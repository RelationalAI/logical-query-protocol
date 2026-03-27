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
        re.compile(r"[a-zA-Z_][a-zA-Z0-9_./#-]*"),
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
            _t2085 = value.HasField("int32_value")
        else:
            _t2085 = False
        if _t2085:
            assert value is not None
            return value.int32_value
        else:
            _t2086 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2087 = value.HasField("int_value")
        else:
            _t2087 = False
        if _t2087:
            assert value is not None
            return value.int_value
        else:
            _t2088 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2089 = value.HasField("string_value")
        else:
            _t2089 = False
        if _t2089:
            assert value is not None
            return value.string_value
        else:
            _t2090 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2091 = value.HasField("boolean_value")
        else:
            _t2091 = False
        if _t2091:
            assert value is not None
            return value.boolean_value
        else:
            _t2092 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2093 = value.HasField("string_value")
        else:
            _t2093 = False
        if _t2093:
            assert value is not None
            return [value.string_value]
        else:
            _t2094 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t2095 = value.HasField("int_value")
        else:
            _t2095 = False
        if _t2095:
            assert value is not None
            return value.int_value
        else:
            _t2096 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2097 = value.HasField("float_value")
        else:
            _t2097 = False
        if _t2097:
            assert value is not None
            return value.float_value
        else:
            _t2098 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2099 = value.HasField("string_value")
        else:
            _t2099 = False
        if _t2099:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2100 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2101 = value.HasField("uint128_value")
        else:
            _t2101 = False
        if _t2101:
            assert value is not None
            return value.uint128_value
        else:
            _t2102 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2103 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2103
        _t2104 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2104
        _t2105 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2105
        _t2106 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2106
        _t2107 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2107
        _t2108 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2108
        _t2109 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2109
        _t2110 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2110
        _t2111 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2111
        _t2112 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2112
        _t2113 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t2113
        _t2114 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2114
        _t2115 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t2115

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2116 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2116
        _t2117 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2117
        _t2118 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2118
        _t2119 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2119
        _t2120 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2120
        _t2121 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2121
        _t2122 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2122
        _t2123 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2123
        _t2124 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2124
        _t2125 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2125
        _t2126 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2126

    def default_configure(self) -> transactions_pb2.Configure:
        _t2127 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2127
        _t2128 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2128

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
        _t2129 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2129
        _t2130 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2130
        _t2131 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t2131

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2132 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2132
        _t2133 = self._extract_value_string(config.get("compression"), "")
        compression = _t2133
        _t2134 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2134
        _t2135 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2135
        _t2136 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2136
        _t2137 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2137
        _t2138 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2138
        _t2139 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2139

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2140 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t2140

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2141 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2141

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, columns: transactions_pb2.ExportIcebergColumns, table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2142 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2142
        _t2143 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2143
        _t2144 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2144
        table_props = dict(table_property_pairs)
        _t2145 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, columns=columns, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2145

    def merge_export_iceberg_columns(self, source: transactions_pb2.ExportIcebergColumns, target_columns: Sequence[transactions_pb2.ExportIcebergColumn]) -> transactions_pb2.ExportIcebergColumns:
        if source.HasField("source_gnf_defs"):
            _t2147 = transactions_pb2.ExportIcebergGnfDefs(defs=source.source_gnf_defs.defs)
            _t2148 = transactions_pb2.ExportIcebergColumns(source_gnf_defs=_t2147, target_columns=target_columns)
            return _t2148
        else:
            _t2146 = None
        _t2149 = transactions_pb2.ExportIcebergColumns(source_table_def=source.source_table_def, target_columns=target_columns)
        return _t2149

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start673 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1335 = self.parse_configure()
            _t1334 = _t1335
        else:
            _t1334 = None
        configure667 = _t1334
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1337 = self.parse_sync()
            _t1336 = _t1337
        else:
            _t1336 = None
        sync668 = _t1336
        xs669 = []
        cond670 = self.match_lookahead_literal("(", 0)
        while cond670:
            _t1338 = self.parse_epoch()
            item671 = _t1338
            xs669.append(item671)
            cond670 = self.match_lookahead_literal("(", 0)
        epochs672 = xs669
        self.consume_literal(")")
        _t1339 = self.default_configure()
        _t1340 = transactions_pb2.Transaction(epochs=epochs672, configure=(configure667 if configure667 is not None else _t1339), sync=sync668)
        result674 = _t1340
        self.record_span(span_start673, "Transaction")
        return result674

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start676 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1341 = self.parse_config_dict()
        config_dict675 = _t1341
        self.consume_literal(")")
        _t1342 = self.construct_configure(config_dict675)
        result677 = _t1342
        self.record_span(span_start676, "Configure")
        return result677

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs678 = []
        cond679 = self.match_lookahead_literal(":", 0)
        while cond679:
            _t1343 = self.parse_config_key_value()
            item680 = _t1343
            xs678.append(item680)
            cond679 = self.match_lookahead_literal(":", 0)
        config_key_values681 = xs678
        self.consume_literal("}")
        return config_key_values681

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol682 = self.consume_terminal("SYMBOL")
        _t1344 = self.parse_raw_value()
        raw_value683 = _t1344
        return (symbol682, raw_value683,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start697 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1345 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1346 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1347 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1349 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1350 = 0
                            else:
                                _t1350 = -1
                            _t1349 = _t1350
                        _t1348 = _t1349
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1351 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1352 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1353 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1354 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1355 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1356 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1357 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1358 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1359 = 10
                                                        else:
                                                            _t1359 = -1
                                                        _t1358 = _t1359
                                                    _t1357 = _t1358
                                                _t1356 = _t1357
                                            _t1355 = _t1356
                                        _t1354 = _t1355
                                    _t1353 = _t1354
                                _t1352 = _t1353
                            _t1351 = _t1352
                        _t1348 = _t1351
                    _t1347 = _t1348
                _t1346 = _t1347
            _t1345 = _t1346
        prediction684 = _t1345
        if prediction684 == 12:
            _t1361 = self.parse_boolean_value()
            boolean_value696 = _t1361
            _t1362 = logic_pb2.Value(boolean_value=boolean_value696)
            _t1360 = _t1362
        else:
            if prediction684 == 11:
                self.consume_literal("missing")
                _t1364 = logic_pb2.MissingValue()
                _t1365 = logic_pb2.Value(missing_value=_t1364)
                _t1363 = _t1365
            else:
                if prediction684 == 10:
                    decimal695 = self.consume_terminal("DECIMAL")
                    _t1367 = logic_pb2.Value(decimal_value=decimal695)
                    _t1366 = _t1367
                else:
                    if prediction684 == 9:
                        int128694 = self.consume_terminal("INT128")
                        _t1369 = logic_pb2.Value(int128_value=int128694)
                        _t1368 = _t1369
                    else:
                        if prediction684 == 8:
                            uint128693 = self.consume_terminal("UINT128")
                            _t1371 = logic_pb2.Value(uint128_value=uint128693)
                            _t1370 = _t1371
                        else:
                            if prediction684 == 7:
                                uint32692 = self.consume_terminal("UINT32")
                                _t1373 = logic_pb2.Value(uint32_value=uint32692)
                                _t1372 = _t1373
                            else:
                                if prediction684 == 6:
                                    float691 = self.consume_terminal("FLOAT")
                                    _t1375 = logic_pb2.Value(float_value=float691)
                                    _t1374 = _t1375
                                else:
                                    if prediction684 == 5:
                                        float32690 = self.consume_terminal("FLOAT32")
                                        _t1377 = logic_pb2.Value(float32_value=float32690)
                                        _t1376 = _t1377
                                    else:
                                        if prediction684 == 4:
                                            int689 = self.consume_terminal("INT")
                                            _t1379 = logic_pb2.Value(int_value=int689)
                                            _t1378 = _t1379
                                        else:
                                            if prediction684 == 3:
                                                int32688 = self.consume_terminal("INT32")
                                                _t1381 = logic_pb2.Value(int32_value=int32688)
                                                _t1380 = _t1381
                                            else:
                                                if prediction684 == 2:
                                                    string687 = self.consume_terminal("STRING")
                                                    _t1383 = logic_pb2.Value(string_value=string687)
                                                    _t1382 = _t1383
                                                else:
                                                    if prediction684 == 1:
                                                        _t1385 = self.parse_raw_datetime()
                                                        raw_datetime686 = _t1385
                                                        _t1386 = logic_pb2.Value(datetime_value=raw_datetime686)
                                                        _t1384 = _t1386
                                                    else:
                                                        if prediction684 == 0:
                                                            _t1388 = self.parse_raw_date()
                                                            raw_date685 = _t1388
                                                            _t1389 = logic_pb2.Value(date_value=raw_date685)
                                                            _t1387 = _t1389
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1384 = _t1387
                                                    _t1382 = _t1384
                                                _t1380 = _t1382
                                            _t1378 = _t1380
                                        _t1376 = _t1378
                                    _t1374 = _t1376
                                _t1372 = _t1374
                            _t1370 = _t1372
                        _t1368 = _t1370
                    _t1366 = _t1368
                _t1363 = _t1366
            _t1360 = _t1363
        result698 = _t1360
        self.record_span(span_start697, "Value")
        return result698

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start702 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int699 = self.consume_terminal("INT")
        int_3700 = self.consume_terminal("INT")
        int_4701 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1390 = logic_pb2.DateValue(year=int(int699), month=int(int_3700), day=int(int_4701))
        result703 = _t1390
        self.record_span(span_start702, "DateValue")
        return result703

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start711 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int704 = self.consume_terminal("INT")
        int_3705 = self.consume_terminal("INT")
        int_4706 = self.consume_terminal("INT")
        int_5707 = self.consume_terminal("INT")
        int_6708 = self.consume_terminal("INT")
        int_7709 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1391 = self.consume_terminal("INT")
        else:
            _t1391 = None
        int_8710 = _t1391
        self.consume_literal(")")
        _t1392 = logic_pb2.DateTimeValue(year=int(int704), month=int(int_3705), day=int(int_4706), hour=int(int_5707), minute=int(int_6708), second=int(int_7709), microsecond=int((int_8710 if int_8710 is not None else 0)))
        result712 = _t1392
        self.record_span(span_start711, "DateTimeValue")
        return result712

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1393 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1394 = 1
            else:
                _t1394 = -1
            _t1393 = _t1394
        prediction713 = _t1393
        if prediction713 == 1:
            self.consume_literal("false")
            _t1395 = False
        else:
            if prediction713 == 0:
                self.consume_literal("true")
                _t1396 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1395 = _t1396
        return _t1395

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start718 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs714 = []
        cond715 = self.match_lookahead_literal(":", 0)
        while cond715:
            _t1397 = self.parse_fragment_id()
            item716 = _t1397
            xs714.append(item716)
            cond715 = self.match_lookahead_literal(":", 0)
        fragment_ids717 = xs714
        self.consume_literal(")")
        _t1398 = transactions_pb2.Sync(fragments=fragment_ids717)
        result719 = _t1398
        self.record_span(span_start718, "Sync")
        return result719

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start721 = self.span_start()
        self.consume_literal(":")
        symbol720 = self.consume_terminal("SYMBOL")
        result722 = fragments_pb2.FragmentId(id=symbol720.encode())
        self.record_span(span_start721, "FragmentId")
        return result722

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start725 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1400 = self.parse_epoch_writes()
            _t1399 = _t1400
        else:
            _t1399 = None
        epoch_writes723 = _t1399
        if self.match_lookahead_literal("(", 0):
            _t1402 = self.parse_epoch_reads()
            _t1401 = _t1402
        else:
            _t1401 = None
        epoch_reads724 = _t1401
        self.consume_literal(")")
        _t1403 = transactions_pb2.Epoch(writes=(epoch_writes723 if epoch_writes723 is not None else []), reads=(epoch_reads724 if epoch_reads724 is not None else []))
        result726 = _t1403
        self.record_span(span_start725, "Epoch")
        return result726

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs727 = []
        cond728 = self.match_lookahead_literal("(", 0)
        while cond728:
            _t1404 = self.parse_write()
            item729 = _t1404
            xs727.append(item729)
            cond728 = self.match_lookahead_literal("(", 0)
        writes730 = xs727
        self.consume_literal(")")
        return writes730

    def parse_write(self) -> transactions_pb2.Write:
        span_start736 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1406 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1407 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1408 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1409 = 2
                        else:
                            _t1409 = -1
                        _t1408 = _t1409
                    _t1407 = _t1408
                _t1406 = _t1407
            _t1405 = _t1406
        else:
            _t1405 = -1
        prediction731 = _t1405
        if prediction731 == 3:
            _t1411 = self.parse_snapshot()
            snapshot735 = _t1411
            _t1412 = transactions_pb2.Write(snapshot=snapshot735)
            _t1410 = _t1412
        else:
            if prediction731 == 2:
                _t1414 = self.parse_context()
                context734 = _t1414
                _t1415 = transactions_pb2.Write(context=context734)
                _t1413 = _t1415
            else:
                if prediction731 == 1:
                    _t1417 = self.parse_undefine()
                    undefine733 = _t1417
                    _t1418 = transactions_pb2.Write(undefine=undefine733)
                    _t1416 = _t1418
                else:
                    if prediction731 == 0:
                        _t1420 = self.parse_define()
                        define732 = _t1420
                        _t1421 = transactions_pb2.Write(define=define732)
                        _t1419 = _t1421
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1416 = _t1419
                _t1413 = _t1416
            _t1410 = _t1413
        result737 = _t1410
        self.record_span(span_start736, "Write")
        return result737

    def parse_define(self) -> transactions_pb2.Define:
        span_start739 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1422 = self.parse_fragment()
        fragment738 = _t1422
        self.consume_literal(")")
        _t1423 = transactions_pb2.Define(fragment=fragment738)
        result740 = _t1423
        self.record_span(span_start739, "Define")
        return result740

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start746 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1424 = self.parse_new_fragment_id()
        new_fragment_id741 = _t1424
        xs742 = []
        cond743 = self.match_lookahead_literal("(", 0)
        while cond743:
            _t1425 = self.parse_declaration()
            item744 = _t1425
            xs742.append(item744)
            cond743 = self.match_lookahead_literal("(", 0)
        declarations745 = xs742
        self.consume_literal(")")
        result747 = self.construct_fragment(new_fragment_id741, declarations745)
        self.record_span(span_start746, "Fragment")
        return result747

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start749 = self.span_start()
        _t1426 = self.parse_fragment_id()
        fragment_id748 = _t1426
        self.start_fragment(fragment_id748)
        result750 = fragment_id748
        self.record_span(span_start749, "FragmentId")
        return result750

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start756 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1428 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1429 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1430 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1431 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1432 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1433 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1434 = 1
                                    else:
                                        _t1434 = -1
                                    _t1433 = _t1434
                                _t1432 = _t1433
                            _t1431 = _t1432
                        _t1430 = _t1431
                    _t1429 = _t1430
                _t1428 = _t1429
            _t1427 = _t1428
        else:
            _t1427 = -1
        prediction751 = _t1427
        if prediction751 == 3:
            _t1436 = self.parse_data()
            data755 = _t1436
            _t1437 = logic_pb2.Declaration(data=data755)
            _t1435 = _t1437
        else:
            if prediction751 == 2:
                _t1439 = self.parse_constraint()
                constraint754 = _t1439
                _t1440 = logic_pb2.Declaration(constraint=constraint754)
                _t1438 = _t1440
            else:
                if prediction751 == 1:
                    _t1442 = self.parse_algorithm()
                    algorithm753 = _t1442
                    _t1443 = logic_pb2.Declaration(algorithm=algorithm753)
                    _t1441 = _t1443
                else:
                    if prediction751 == 0:
                        _t1445 = self.parse_def()
                        def752 = _t1445
                        _t1446 = logic_pb2.Declaration()
                        getattr(_t1446, 'def').CopyFrom(def752)
                        _t1444 = _t1446
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1441 = _t1444
                _t1438 = _t1441
            _t1435 = _t1438
        result757 = _t1435
        self.record_span(span_start756, "Declaration")
        return result757

    def parse_def(self) -> logic_pb2.Def:
        span_start761 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1447 = self.parse_relation_id()
        relation_id758 = _t1447
        _t1448 = self.parse_abstraction()
        abstraction759 = _t1448
        if self.match_lookahead_literal("(", 0):
            _t1450 = self.parse_attrs()
            _t1449 = _t1450
        else:
            _t1449 = None
        attrs760 = _t1449
        self.consume_literal(")")
        _t1451 = logic_pb2.Def(name=relation_id758, body=abstraction759, attrs=(attrs760 if attrs760 is not None else []))
        result762 = _t1451
        self.record_span(span_start761, "Def")
        return result762

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start766 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1452 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1453 = 1
            else:
                _t1453 = -1
            _t1452 = _t1453
        prediction763 = _t1452
        if prediction763 == 1:
            uint128765 = self.consume_terminal("UINT128")
            _t1454 = logic_pb2.RelationId(id_low=uint128765.low, id_high=uint128765.high)
        else:
            if prediction763 == 0:
                self.consume_literal(":")
                symbol764 = self.consume_terminal("SYMBOL")
                _t1455 = self.relation_id_from_string(symbol764)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1454 = _t1455
        result767 = _t1454
        self.record_span(span_start766, "RelationId")
        return result767

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start770 = self.span_start()
        self.consume_literal("(")
        _t1456 = self.parse_bindings()
        bindings768 = _t1456
        _t1457 = self.parse_formula()
        formula769 = _t1457
        self.consume_literal(")")
        _t1458 = logic_pb2.Abstraction(vars=(list(bindings768[0]) + list(bindings768[1] if bindings768[1] is not None else [])), value=formula769)
        result771 = _t1458
        self.record_span(span_start770, "Abstraction")
        return result771

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs772 = []
        cond773 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond773:
            _t1459 = self.parse_binding()
            item774 = _t1459
            xs772.append(item774)
            cond773 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings775 = xs772
        if self.match_lookahead_literal("|", 0):
            _t1461 = self.parse_value_bindings()
            _t1460 = _t1461
        else:
            _t1460 = None
        value_bindings776 = _t1460
        self.consume_literal("]")
        return (bindings775, (value_bindings776 if value_bindings776 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start779 = self.span_start()
        symbol777 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1462 = self.parse_type()
        type778 = _t1462
        _t1463 = logic_pb2.Var(name=symbol777)
        _t1464 = logic_pb2.Binding(var=_t1463, type=type778)
        result780 = _t1464
        self.record_span(span_start779, "Binding")
        return result780

    def parse_type(self) -> logic_pb2.Type:
        span_start796 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1465 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1466 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1467 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1468 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1469 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1470 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1471 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1472 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1473 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1474 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1475 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1476 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1477 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1478 = 9
                                                            else:
                                                                _t1478 = -1
                                                            _t1477 = _t1478
                                                        _t1476 = _t1477
                                                    _t1475 = _t1476
                                                _t1474 = _t1475
                                            _t1473 = _t1474
                                        _t1472 = _t1473
                                    _t1471 = _t1472
                                _t1470 = _t1471
                            _t1469 = _t1470
                        _t1468 = _t1469
                    _t1467 = _t1468
                _t1466 = _t1467
            _t1465 = _t1466
        prediction781 = _t1465
        if prediction781 == 13:
            _t1480 = self.parse_uint32_type()
            uint32_type795 = _t1480
            _t1481 = logic_pb2.Type(uint32_type=uint32_type795)
            _t1479 = _t1481
        else:
            if prediction781 == 12:
                _t1483 = self.parse_float32_type()
                float32_type794 = _t1483
                _t1484 = logic_pb2.Type(float32_type=float32_type794)
                _t1482 = _t1484
            else:
                if prediction781 == 11:
                    _t1486 = self.parse_int32_type()
                    int32_type793 = _t1486
                    _t1487 = logic_pb2.Type(int32_type=int32_type793)
                    _t1485 = _t1487
                else:
                    if prediction781 == 10:
                        _t1489 = self.parse_boolean_type()
                        boolean_type792 = _t1489
                        _t1490 = logic_pb2.Type(boolean_type=boolean_type792)
                        _t1488 = _t1490
                    else:
                        if prediction781 == 9:
                            _t1492 = self.parse_decimal_type()
                            decimal_type791 = _t1492
                            _t1493 = logic_pb2.Type(decimal_type=decimal_type791)
                            _t1491 = _t1493
                        else:
                            if prediction781 == 8:
                                _t1495 = self.parse_missing_type()
                                missing_type790 = _t1495
                                _t1496 = logic_pb2.Type(missing_type=missing_type790)
                                _t1494 = _t1496
                            else:
                                if prediction781 == 7:
                                    _t1498 = self.parse_datetime_type()
                                    datetime_type789 = _t1498
                                    _t1499 = logic_pb2.Type(datetime_type=datetime_type789)
                                    _t1497 = _t1499
                                else:
                                    if prediction781 == 6:
                                        _t1501 = self.parse_date_type()
                                        date_type788 = _t1501
                                        _t1502 = logic_pb2.Type(date_type=date_type788)
                                        _t1500 = _t1502
                                    else:
                                        if prediction781 == 5:
                                            _t1504 = self.parse_int128_type()
                                            int128_type787 = _t1504
                                            _t1505 = logic_pb2.Type(int128_type=int128_type787)
                                            _t1503 = _t1505
                                        else:
                                            if prediction781 == 4:
                                                _t1507 = self.parse_uint128_type()
                                                uint128_type786 = _t1507
                                                _t1508 = logic_pb2.Type(uint128_type=uint128_type786)
                                                _t1506 = _t1508
                                            else:
                                                if prediction781 == 3:
                                                    _t1510 = self.parse_float_type()
                                                    float_type785 = _t1510
                                                    _t1511 = logic_pb2.Type(float_type=float_type785)
                                                    _t1509 = _t1511
                                                else:
                                                    if prediction781 == 2:
                                                        _t1513 = self.parse_int_type()
                                                        int_type784 = _t1513
                                                        _t1514 = logic_pb2.Type(int_type=int_type784)
                                                        _t1512 = _t1514
                                                    else:
                                                        if prediction781 == 1:
                                                            _t1516 = self.parse_string_type()
                                                            string_type783 = _t1516
                                                            _t1517 = logic_pb2.Type(string_type=string_type783)
                                                            _t1515 = _t1517
                                                        else:
                                                            if prediction781 == 0:
                                                                _t1519 = self.parse_unspecified_type()
                                                                unspecified_type782 = _t1519
                                                                _t1520 = logic_pb2.Type(unspecified_type=unspecified_type782)
                                                                _t1518 = _t1520
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t1515 = _t1518
                                                        _t1512 = _t1515
                                                    _t1509 = _t1512
                                                _t1506 = _t1509
                                            _t1503 = _t1506
                                        _t1500 = _t1503
                                    _t1497 = _t1500
                                _t1494 = _t1497
                            _t1491 = _t1494
                        _t1488 = _t1491
                    _t1485 = _t1488
                _t1482 = _t1485
            _t1479 = _t1482
        result797 = _t1479
        self.record_span(span_start796, "Type")
        return result797

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start798 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1521 = logic_pb2.UnspecifiedType()
        result799 = _t1521
        self.record_span(span_start798, "UnspecifiedType")
        return result799

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start800 = self.span_start()
        self.consume_literal("STRING")
        _t1522 = logic_pb2.StringType()
        result801 = _t1522
        self.record_span(span_start800, "StringType")
        return result801

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start802 = self.span_start()
        self.consume_literal("INT")
        _t1523 = logic_pb2.IntType()
        result803 = _t1523
        self.record_span(span_start802, "IntType")
        return result803

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start804 = self.span_start()
        self.consume_literal("FLOAT")
        _t1524 = logic_pb2.FloatType()
        result805 = _t1524
        self.record_span(span_start804, "FloatType")
        return result805

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start806 = self.span_start()
        self.consume_literal("UINT128")
        _t1525 = logic_pb2.UInt128Type()
        result807 = _t1525
        self.record_span(span_start806, "UInt128Type")
        return result807

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start808 = self.span_start()
        self.consume_literal("INT128")
        _t1526 = logic_pb2.Int128Type()
        result809 = _t1526
        self.record_span(span_start808, "Int128Type")
        return result809

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start810 = self.span_start()
        self.consume_literal("DATE")
        _t1527 = logic_pb2.DateType()
        result811 = _t1527
        self.record_span(span_start810, "DateType")
        return result811

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start812 = self.span_start()
        self.consume_literal("DATETIME")
        _t1528 = logic_pb2.DateTimeType()
        result813 = _t1528
        self.record_span(span_start812, "DateTimeType")
        return result813

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start814 = self.span_start()
        self.consume_literal("MISSING")
        _t1529 = logic_pb2.MissingType()
        result815 = _t1529
        self.record_span(span_start814, "MissingType")
        return result815

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start818 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int816 = self.consume_terminal("INT")
        int_3817 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1530 = logic_pb2.DecimalType(precision=int(int816), scale=int(int_3817))
        result819 = _t1530
        self.record_span(span_start818, "DecimalType")
        return result819

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start820 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1531 = logic_pb2.BooleanType()
        result821 = _t1531
        self.record_span(span_start820, "BooleanType")
        return result821

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start822 = self.span_start()
        self.consume_literal("INT32")
        _t1532 = logic_pb2.Int32Type()
        result823 = _t1532
        self.record_span(span_start822, "Int32Type")
        return result823

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start824 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1533 = logic_pb2.Float32Type()
        result825 = _t1533
        self.record_span(span_start824, "Float32Type")
        return result825

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start826 = self.span_start()
        self.consume_literal("UINT32")
        _t1534 = logic_pb2.UInt32Type()
        result827 = _t1534
        self.record_span(span_start826, "UInt32Type")
        return result827

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs828 = []
        cond829 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond829:
            _t1535 = self.parse_binding()
            item830 = _t1535
            xs828.append(item830)
            cond829 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings831 = xs828
        return bindings831

    def parse_formula(self) -> logic_pb2.Formula:
        span_start846 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1537 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1538 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1539 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1540 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1541 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1542 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1543 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1544 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1545 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1546 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1547 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1548 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1549 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1550 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1551 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1552 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1553 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1554 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1555 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1556 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1557 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1558 = 10
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
                                            _t1544 = _t1545
                                        _t1543 = _t1544
                                    _t1542 = _t1543
                                _t1541 = _t1542
                            _t1540 = _t1541
                        _t1539 = _t1540
                    _t1538 = _t1539
                _t1537 = _t1538
            _t1536 = _t1537
        else:
            _t1536 = -1
        prediction832 = _t1536
        if prediction832 == 12:
            _t1560 = self.parse_cast()
            cast845 = _t1560
            _t1561 = logic_pb2.Formula(cast=cast845)
            _t1559 = _t1561
        else:
            if prediction832 == 11:
                _t1563 = self.parse_rel_atom()
                rel_atom844 = _t1563
                _t1564 = logic_pb2.Formula(rel_atom=rel_atom844)
                _t1562 = _t1564
            else:
                if prediction832 == 10:
                    _t1566 = self.parse_primitive()
                    primitive843 = _t1566
                    _t1567 = logic_pb2.Formula(primitive=primitive843)
                    _t1565 = _t1567
                else:
                    if prediction832 == 9:
                        _t1569 = self.parse_pragma()
                        pragma842 = _t1569
                        _t1570 = logic_pb2.Formula(pragma=pragma842)
                        _t1568 = _t1570
                    else:
                        if prediction832 == 8:
                            _t1572 = self.parse_atom()
                            atom841 = _t1572
                            _t1573 = logic_pb2.Formula(atom=atom841)
                            _t1571 = _t1573
                        else:
                            if prediction832 == 7:
                                _t1575 = self.parse_ffi()
                                ffi840 = _t1575
                                _t1576 = logic_pb2.Formula(ffi=ffi840)
                                _t1574 = _t1576
                            else:
                                if prediction832 == 6:
                                    _t1578 = self.parse_not()
                                    not839 = _t1578
                                    _t1579 = logic_pb2.Formula()
                                    getattr(_t1579, 'not').CopyFrom(not839)
                                    _t1577 = _t1579
                                else:
                                    if prediction832 == 5:
                                        _t1581 = self.parse_disjunction()
                                        disjunction838 = _t1581
                                        _t1582 = logic_pb2.Formula(disjunction=disjunction838)
                                        _t1580 = _t1582
                                    else:
                                        if prediction832 == 4:
                                            _t1584 = self.parse_conjunction()
                                            conjunction837 = _t1584
                                            _t1585 = logic_pb2.Formula(conjunction=conjunction837)
                                            _t1583 = _t1585
                                        else:
                                            if prediction832 == 3:
                                                _t1587 = self.parse_reduce()
                                                reduce836 = _t1587
                                                _t1588 = logic_pb2.Formula(reduce=reduce836)
                                                _t1586 = _t1588
                                            else:
                                                if prediction832 == 2:
                                                    _t1590 = self.parse_exists()
                                                    exists835 = _t1590
                                                    _t1591 = logic_pb2.Formula(exists=exists835)
                                                    _t1589 = _t1591
                                                else:
                                                    if prediction832 == 1:
                                                        _t1593 = self.parse_false()
                                                        false834 = _t1593
                                                        _t1594 = logic_pb2.Formula(disjunction=false834)
                                                        _t1592 = _t1594
                                                    else:
                                                        if prediction832 == 0:
                                                            _t1596 = self.parse_true()
                                                            true833 = _t1596
                                                            _t1597 = logic_pb2.Formula(conjunction=true833)
                                                            _t1595 = _t1597
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
        result847 = _t1559
        self.record_span(span_start846, "Formula")
        return result847

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start848 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1598 = logic_pb2.Conjunction(args=[])
        result849 = _t1598
        self.record_span(span_start848, "Conjunction")
        return result849

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start850 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1599 = logic_pb2.Disjunction(args=[])
        result851 = _t1599
        self.record_span(span_start850, "Disjunction")
        return result851

    def parse_exists(self) -> logic_pb2.Exists:
        span_start854 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1600 = self.parse_bindings()
        bindings852 = _t1600
        _t1601 = self.parse_formula()
        formula853 = _t1601
        self.consume_literal(")")
        _t1602 = logic_pb2.Abstraction(vars=(list(bindings852[0]) + list(bindings852[1] if bindings852[1] is not None else [])), value=formula853)
        _t1603 = logic_pb2.Exists(body=_t1602)
        result855 = _t1603
        self.record_span(span_start854, "Exists")
        return result855

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start859 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1604 = self.parse_abstraction()
        abstraction856 = _t1604
        _t1605 = self.parse_abstraction()
        abstraction_3857 = _t1605
        _t1606 = self.parse_terms()
        terms858 = _t1606
        self.consume_literal(")")
        _t1607 = logic_pb2.Reduce(op=abstraction856, body=abstraction_3857, terms=terms858)
        result860 = _t1607
        self.record_span(span_start859, "Reduce")
        return result860

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs861 = []
        cond862 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond862:
            _t1608 = self.parse_term()
            item863 = _t1608
            xs861.append(item863)
            cond862 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms864 = xs861
        self.consume_literal(")")
        return terms864

    def parse_term(self) -> logic_pb2.Term:
        span_start868 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1609 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1610 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1611 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1612 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1613 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1614 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1615 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1616 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1617 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1618 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1619 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1620 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1621 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1622 = 1
                                                            else:
                                                                _t1622 = -1
                                                            _t1621 = _t1622
                                                        _t1620 = _t1621
                                                    _t1619 = _t1620
                                                _t1618 = _t1619
                                            _t1617 = _t1618
                                        _t1616 = _t1617
                                    _t1615 = _t1616
                                _t1614 = _t1615
                            _t1613 = _t1614
                        _t1612 = _t1613
                    _t1611 = _t1612
                _t1610 = _t1611
            _t1609 = _t1610
        prediction865 = _t1609
        if prediction865 == 1:
            _t1624 = self.parse_value()
            value867 = _t1624
            _t1625 = logic_pb2.Term(constant=value867)
            _t1623 = _t1625
        else:
            if prediction865 == 0:
                _t1627 = self.parse_var()
                var866 = _t1627
                _t1628 = logic_pb2.Term(var=var866)
                _t1626 = _t1628
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1623 = _t1626
        result869 = _t1623
        self.record_span(span_start868, "Term")
        return result869

    def parse_var(self) -> logic_pb2.Var:
        span_start871 = self.span_start()
        symbol870 = self.consume_terminal("SYMBOL")
        _t1629 = logic_pb2.Var(name=symbol870)
        result872 = _t1629
        self.record_span(span_start871, "Var")
        return result872

    def parse_value(self) -> logic_pb2.Value:
        span_start886 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1630 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1631 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1632 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1634 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1635 = 0
                            else:
                                _t1635 = -1
                            _t1634 = _t1635
                        _t1633 = _t1634
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1636 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1637 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1638 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1639 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1640 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1641 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1642 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1643 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1644 = 10
                                                        else:
                                                            _t1644 = -1
                                                        _t1643 = _t1644
                                                    _t1642 = _t1643
                                                _t1641 = _t1642
                                            _t1640 = _t1641
                                        _t1639 = _t1640
                                    _t1638 = _t1639
                                _t1637 = _t1638
                            _t1636 = _t1637
                        _t1633 = _t1636
                    _t1632 = _t1633
                _t1631 = _t1632
            _t1630 = _t1631
        prediction873 = _t1630
        if prediction873 == 12:
            _t1646 = self.parse_boolean_value()
            boolean_value885 = _t1646
            _t1647 = logic_pb2.Value(boolean_value=boolean_value885)
            _t1645 = _t1647
        else:
            if prediction873 == 11:
                self.consume_literal("missing")
                _t1649 = logic_pb2.MissingValue()
                _t1650 = logic_pb2.Value(missing_value=_t1649)
                _t1648 = _t1650
            else:
                if prediction873 == 10:
                    formatted_decimal884 = self.consume_terminal("DECIMAL")
                    _t1652 = logic_pb2.Value(decimal_value=formatted_decimal884)
                    _t1651 = _t1652
                else:
                    if prediction873 == 9:
                        formatted_int128883 = self.consume_terminal("INT128")
                        _t1654 = logic_pb2.Value(int128_value=formatted_int128883)
                        _t1653 = _t1654
                    else:
                        if prediction873 == 8:
                            formatted_uint128882 = self.consume_terminal("UINT128")
                            _t1656 = logic_pb2.Value(uint128_value=formatted_uint128882)
                            _t1655 = _t1656
                        else:
                            if prediction873 == 7:
                                formatted_uint32881 = self.consume_terminal("UINT32")
                                _t1658 = logic_pb2.Value(uint32_value=formatted_uint32881)
                                _t1657 = _t1658
                            else:
                                if prediction873 == 6:
                                    formatted_float880 = self.consume_terminal("FLOAT")
                                    _t1660 = logic_pb2.Value(float_value=formatted_float880)
                                    _t1659 = _t1660
                                else:
                                    if prediction873 == 5:
                                        formatted_float32879 = self.consume_terminal("FLOAT32")
                                        _t1662 = logic_pb2.Value(float32_value=formatted_float32879)
                                        _t1661 = _t1662
                                    else:
                                        if prediction873 == 4:
                                            formatted_int878 = self.consume_terminal("INT")
                                            _t1664 = logic_pb2.Value(int_value=formatted_int878)
                                            _t1663 = _t1664
                                        else:
                                            if prediction873 == 3:
                                                formatted_int32877 = self.consume_terminal("INT32")
                                                _t1666 = logic_pb2.Value(int32_value=formatted_int32877)
                                                _t1665 = _t1666
                                            else:
                                                if prediction873 == 2:
                                                    formatted_string876 = self.consume_terminal("STRING")
                                                    _t1668 = logic_pb2.Value(string_value=formatted_string876)
                                                    _t1667 = _t1668
                                                else:
                                                    if prediction873 == 1:
                                                        _t1670 = self.parse_datetime()
                                                        datetime875 = _t1670
                                                        _t1671 = logic_pb2.Value(datetime_value=datetime875)
                                                        _t1669 = _t1671
                                                    else:
                                                        if prediction873 == 0:
                                                            _t1673 = self.parse_date()
                                                            date874 = _t1673
                                                            _t1674 = logic_pb2.Value(date_value=date874)
                                                            _t1672 = _t1674
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1669 = _t1672
                                                    _t1667 = _t1669
                                                _t1665 = _t1667
                                            _t1663 = _t1665
                                        _t1661 = _t1663
                                    _t1659 = _t1661
                                _t1657 = _t1659
                            _t1655 = _t1657
                        _t1653 = _t1655
                    _t1651 = _t1653
                _t1648 = _t1651
            _t1645 = _t1648
        result887 = _t1645
        self.record_span(span_start886, "Value")
        return result887

    def parse_date(self) -> logic_pb2.DateValue:
        span_start891 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int888 = self.consume_terminal("INT")
        formatted_int_3889 = self.consume_terminal("INT")
        formatted_int_4890 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1675 = logic_pb2.DateValue(year=int(formatted_int888), month=int(formatted_int_3889), day=int(formatted_int_4890))
        result892 = _t1675
        self.record_span(span_start891, "DateValue")
        return result892

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start900 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int893 = self.consume_terminal("INT")
        formatted_int_3894 = self.consume_terminal("INT")
        formatted_int_4895 = self.consume_terminal("INT")
        formatted_int_5896 = self.consume_terminal("INT")
        formatted_int_6897 = self.consume_terminal("INT")
        formatted_int_7898 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1676 = self.consume_terminal("INT")
        else:
            _t1676 = None
        formatted_int_8899 = _t1676
        self.consume_literal(")")
        _t1677 = logic_pb2.DateTimeValue(year=int(formatted_int893), month=int(formatted_int_3894), day=int(formatted_int_4895), hour=int(formatted_int_5896), minute=int(formatted_int_6897), second=int(formatted_int_7898), microsecond=int((formatted_int_8899 if formatted_int_8899 is not None else 0)))
        result901 = _t1677
        self.record_span(span_start900, "DateTimeValue")
        return result901

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start906 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs902 = []
        cond903 = self.match_lookahead_literal("(", 0)
        while cond903:
            _t1678 = self.parse_formula()
            item904 = _t1678
            xs902.append(item904)
            cond903 = self.match_lookahead_literal("(", 0)
        formulas905 = xs902
        self.consume_literal(")")
        _t1679 = logic_pb2.Conjunction(args=formulas905)
        result907 = _t1679
        self.record_span(span_start906, "Conjunction")
        return result907

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start912 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs908 = []
        cond909 = self.match_lookahead_literal("(", 0)
        while cond909:
            _t1680 = self.parse_formula()
            item910 = _t1680
            xs908.append(item910)
            cond909 = self.match_lookahead_literal("(", 0)
        formulas911 = xs908
        self.consume_literal(")")
        _t1681 = logic_pb2.Disjunction(args=formulas911)
        result913 = _t1681
        self.record_span(span_start912, "Disjunction")
        return result913

    def parse_not(self) -> logic_pb2.Not:
        span_start915 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1682 = self.parse_formula()
        formula914 = _t1682
        self.consume_literal(")")
        _t1683 = logic_pb2.Not(arg=formula914)
        result916 = _t1683
        self.record_span(span_start915, "Not")
        return result916

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start920 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1684 = self.parse_name()
        name917 = _t1684
        _t1685 = self.parse_ffi_args()
        ffi_args918 = _t1685
        _t1686 = self.parse_terms()
        terms919 = _t1686
        self.consume_literal(")")
        _t1687 = logic_pb2.FFI(name=name917, args=ffi_args918, terms=terms919)
        result921 = _t1687
        self.record_span(span_start920, "FFI")
        return result921

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol922 = self.consume_terminal("SYMBOL")
        return symbol922

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs923 = []
        cond924 = self.match_lookahead_literal("(", 0)
        while cond924:
            _t1688 = self.parse_abstraction()
            item925 = _t1688
            xs923.append(item925)
            cond924 = self.match_lookahead_literal("(", 0)
        abstractions926 = xs923
        self.consume_literal(")")
        return abstractions926

    def parse_atom(self) -> logic_pb2.Atom:
        span_start932 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1689 = self.parse_relation_id()
        relation_id927 = _t1689
        xs928 = []
        cond929 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond929:
            _t1690 = self.parse_term()
            item930 = _t1690
            xs928.append(item930)
            cond929 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms931 = xs928
        self.consume_literal(")")
        _t1691 = logic_pb2.Atom(name=relation_id927, terms=terms931)
        result933 = _t1691
        self.record_span(span_start932, "Atom")
        return result933

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start939 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1692 = self.parse_name()
        name934 = _t1692
        xs935 = []
        cond936 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond936:
            _t1693 = self.parse_term()
            item937 = _t1693
            xs935.append(item937)
            cond936 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms938 = xs935
        self.consume_literal(")")
        _t1694 = logic_pb2.Pragma(name=name934, terms=terms938)
        result940 = _t1694
        self.record_span(span_start939, "Pragma")
        return result940

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start956 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1696 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1697 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1698 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1699 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1700 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1701 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1702 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1703 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1704 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1705 = 7
                                                else:
                                                    _t1705 = -1
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
        else:
            _t1695 = -1
        prediction941 = _t1695
        if prediction941 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1707 = self.parse_name()
            name951 = _t1707
            xs952 = []
            cond953 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond953:
                _t1708 = self.parse_rel_term()
                item954 = _t1708
                xs952.append(item954)
                cond953 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms955 = xs952
            self.consume_literal(")")
            _t1709 = logic_pb2.Primitive(name=name951, terms=rel_terms955)
            _t1706 = _t1709
        else:
            if prediction941 == 8:
                _t1711 = self.parse_divide()
                divide950 = _t1711
                _t1710 = divide950
            else:
                if prediction941 == 7:
                    _t1713 = self.parse_multiply()
                    multiply949 = _t1713
                    _t1712 = multiply949
                else:
                    if prediction941 == 6:
                        _t1715 = self.parse_minus()
                        minus948 = _t1715
                        _t1714 = minus948
                    else:
                        if prediction941 == 5:
                            _t1717 = self.parse_add()
                            add947 = _t1717
                            _t1716 = add947
                        else:
                            if prediction941 == 4:
                                _t1719 = self.parse_gt_eq()
                                gt_eq946 = _t1719
                                _t1718 = gt_eq946
                            else:
                                if prediction941 == 3:
                                    _t1721 = self.parse_gt()
                                    gt945 = _t1721
                                    _t1720 = gt945
                                else:
                                    if prediction941 == 2:
                                        _t1723 = self.parse_lt_eq()
                                        lt_eq944 = _t1723
                                        _t1722 = lt_eq944
                                    else:
                                        if prediction941 == 1:
                                            _t1725 = self.parse_lt()
                                            lt943 = _t1725
                                            _t1724 = lt943
                                        else:
                                            if prediction941 == 0:
                                                _t1727 = self.parse_eq()
                                                eq942 = _t1727
                                                _t1726 = eq942
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1724 = _t1726
                                        _t1722 = _t1724
                                    _t1720 = _t1722
                                _t1718 = _t1720
                            _t1716 = _t1718
                        _t1714 = _t1716
                    _t1712 = _t1714
                _t1710 = _t1712
            _t1706 = _t1710
        result957 = _t1706
        self.record_span(span_start956, "Primitive")
        return result957

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start960 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1728 = self.parse_term()
        term958 = _t1728
        _t1729 = self.parse_term()
        term_3959 = _t1729
        self.consume_literal(")")
        _t1730 = logic_pb2.RelTerm(term=term958)
        _t1731 = logic_pb2.RelTerm(term=term_3959)
        _t1732 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1730, _t1731])
        result961 = _t1732
        self.record_span(span_start960, "Primitive")
        return result961

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start964 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1733 = self.parse_term()
        term962 = _t1733
        _t1734 = self.parse_term()
        term_3963 = _t1734
        self.consume_literal(")")
        _t1735 = logic_pb2.RelTerm(term=term962)
        _t1736 = logic_pb2.RelTerm(term=term_3963)
        _t1737 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1735, _t1736])
        result965 = _t1737
        self.record_span(span_start964, "Primitive")
        return result965

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start968 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1738 = self.parse_term()
        term966 = _t1738
        _t1739 = self.parse_term()
        term_3967 = _t1739
        self.consume_literal(")")
        _t1740 = logic_pb2.RelTerm(term=term966)
        _t1741 = logic_pb2.RelTerm(term=term_3967)
        _t1742 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1740, _t1741])
        result969 = _t1742
        self.record_span(span_start968, "Primitive")
        return result969

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start972 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1743 = self.parse_term()
        term970 = _t1743
        _t1744 = self.parse_term()
        term_3971 = _t1744
        self.consume_literal(")")
        _t1745 = logic_pb2.RelTerm(term=term970)
        _t1746 = logic_pb2.RelTerm(term=term_3971)
        _t1747 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1745, _t1746])
        result973 = _t1747
        self.record_span(span_start972, "Primitive")
        return result973

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start976 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1748 = self.parse_term()
        term974 = _t1748
        _t1749 = self.parse_term()
        term_3975 = _t1749
        self.consume_literal(")")
        _t1750 = logic_pb2.RelTerm(term=term974)
        _t1751 = logic_pb2.RelTerm(term=term_3975)
        _t1752 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1750, _t1751])
        result977 = _t1752
        self.record_span(span_start976, "Primitive")
        return result977

    def parse_add(self) -> logic_pb2.Primitive:
        span_start981 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1753 = self.parse_term()
        term978 = _t1753
        _t1754 = self.parse_term()
        term_3979 = _t1754
        _t1755 = self.parse_term()
        term_4980 = _t1755
        self.consume_literal(")")
        _t1756 = logic_pb2.RelTerm(term=term978)
        _t1757 = logic_pb2.RelTerm(term=term_3979)
        _t1758 = logic_pb2.RelTerm(term=term_4980)
        _t1759 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1756, _t1757, _t1758])
        result982 = _t1759
        self.record_span(span_start981, "Primitive")
        return result982

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start986 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1760 = self.parse_term()
        term983 = _t1760
        _t1761 = self.parse_term()
        term_3984 = _t1761
        _t1762 = self.parse_term()
        term_4985 = _t1762
        self.consume_literal(")")
        _t1763 = logic_pb2.RelTerm(term=term983)
        _t1764 = logic_pb2.RelTerm(term=term_3984)
        _t1765 = logic_pb2.RelTerm(term=term_4985)
        _t1766 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1763, _t1764, _t1765])
        result987 = _t1766
        self.record_span(span_start986, "Primitive")
        return result987

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start991 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1767 = self.parse_term()
        term988 = _t1767
        _t1768 = self.parse_term()
        term_3989 = _t1768
        _t1769 = self.parse_term()
        term_4990 = _t1769
        self.consume_literal(")")
        _t1770 = logic_pb2.RelTerm(term=term988)
        _t1771 = logic_pb2.RelTerm(term=term_3989)
        _t1772 = logic_pb2.RelTerm(term=term_4990)
        _t1773 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1770, _t1771, _t1772])
        result992 = _t1773
        self.record_span(span_start991, "Primitive")
        return result992

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start996 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1774 = self.parse_term()
        term993 = _t1774
        _t1775 = self.parse_term()
        term_3994 = _t1775
        _t1776 = self.parse_term()
        term_4995 = _t1776
        self.consume_literal(")")
        _t1777 = logic_pb2.RelTerm(term=term993)
        _t1778 = logic_pb2.RelTerm(term=term_3994)
        _t1779 = logic_pb2.RelTerm(term=term_4995)
        _t1780 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1777, _t1778, _t1779])
        result997 = _t1780
        self.record_span(span_start996, "Primitive")
        return result997

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start1001 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1781 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1782 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1783 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1784 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1785 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1786 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1787 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1788 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1789 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1790 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1791 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1792 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1793 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1794 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1795 = 1
                                                                else:
                                                                    _t1795 = -1
                                                                _t1794 = _t1795
                                                            _t1793 = _t1794
                                                        _t1792 = _t1793
                                                    _t1791 = _t1792
                                                _t1790 = _t1791
                                            _t1789 = _t1790
                                        _t1788 = _t1789
                                    _t1787 = _t1788
                                _t1786 = _t1787
                            _t1785 = _t1786
                        _t1784 = _t1785
                    _t1783 = _t1784
                _t1782 = _t1783
            _t1781 = _t1782
        prediction998 = _t1781
        if prediction998 == 1:
            _t1797 = self.parse_term()
            term1000 = _t1797
            _t1798 = logic_pb2.RelTerm(term=term1000)
            _t1796 = _t1798
        else:
            if prediction998 == 0:
                _t1800 = self.parse_specialized_value()
                specialized_value999 = _t1800
                _t1801 = logic_pb2.RelTerm(specialized_value=specialized_value999)
                _t1799 = _t1801
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1796 = _t1799
        result1002 = _t1796
        self.record_span(span_start1001, "RelTerm")
        return result1002

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start1004 = self.span_start()
        self.consume_literal("#")
        _t1802 = self.parse_raw_value()
        raw_value1003 = _t1802
        result1005 = raw_value1003
        self.record_span(span_start1004, "Value")
        return result1005

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start1011 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1803 = self.parse_name()
        name1006 = _t1803
        xs1007 = []
        cond1008 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond1008:
            _t1804 = self.parse_rel_term()
            item1009 = _t1804
            xs1007.append(item1009)
            cond1008 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1010 = xs1007
        self.consume_literal(")")
        _t1805 = logic_pb2.RelAtom(name=name1006, terms=rel_terms1010)
        result1012 = _t1805
        self.record_span(span_start1011, "RelAtom")
        return result1012

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1015 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1806 = self.parse_term()
        term1013 = _t1806
        _t1807 = self.parse_term()
        term_31014 = _t1807
        self.consume_literal(")")
        _t1808 = logic_pb2.Cast(input=term1013, result=term_31014)
        result1016 = _t1808
        self.record_span(span_start1015, "Cast")
        return result1016

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1017 = []
        cond1018 = self.match_lookahead_literal("(", 0)
        while cond1018:
            _t1809 = self.parse_attribute()
            item1019 = _t1809
            xs1017.append(item1019)
            cond1018 = self.match_lookahead_literal("(", 0)
        attributes1020 = xs1017
        self.consume_literal(")")
        return attributes1020

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1026 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1810 = self.parse_name()
        name1021 = _t1810
        xs1022 = []
        cond1023 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1023:
            _t1811 = self.parse_raw_value()
            item1024 = _t1811
            xs1022.append(item1024)
            cond1023 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1025 = xs1022
        self.consume_literal(")")
        _t1812 = logic_pb2.Attribute(name=name1021, args=raw_values1025)
        result1027 = _t1812
        self.record_span(span_start1026, "Attribute")
        return result1027

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1033 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1028 = []
        cond1029 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1029:
            _t1813 = self.parse_relation_id()
            item1030 = _t1813
            xs1028.append(item1030)
            cond1029 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1031 = xs1028
        _t1814 = self.parse_script()
        script1032 = _t1814
        self.consume_literal(")")
        _t1815 = logic_pb2.Algorithm(body=script1032)
        getattr(_t1815, 'global').extend(relation_ids1031)
        result1034 = _t1815
        self.record_span(span_start1033, "Algorithm")
        return result1034

    def parse_script(self) -> logic_pb2.Script:
        span_start1039 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1035 = []
        cond1036 = self.match_lookahead_literal("(", 0)
        while cond1036:
            _t1816 = self.parse_construct()
            item1037 = _t1816
            xs1035.append(item1037)
            cond1036 = self.match_lookahead_literal("(", 0)
        constructs1038 = xs1035
        self.consume_literal(")")
        _t1817 = logic_pb2.Script(constructs=constructs1038)
        result1040 = _t1817
        self.record_span(span_start1039, "Script")
        return result1040

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1044 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1819 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1820 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1821 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1822 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1823 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1824 = 1
                                else:
                                    _t1824 = -1
                                _t1823 = _t1824
                            _t1822 = _t1823
                        _t1821 = _t1822
                    _t1820 = _t1821
                _t1819 = _t1820
            _t1818 = _t1819
        else:
            _t1818 = -1
        prediction1041 = _t1818
        if prediction1041 == 1:
            _t1826 = self.parse_instruction()
            instruction1043 = _t1826
            _t1827 = logic_pb2.Construct(instruction=instruction1043)
            _t1825 = _t1827
        else:
            if prediction1041 == 0:
                _t1829 = self.parse_loop()
                loop1042 = _t1829
                _t1830 = logic_pb2.Construct(loop=loop1042)
                _t1828 = _t1830
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1825 = _t1828
        result1045 = _t1825
        self.record_span(span_start1044, "Construct")
        return result1045

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1048 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1831 = self.parse_init()
        init1046 = _t1831
        _t1832 = self.parse_script()
        script1047 = _t1832
        self.consume_literal(")")
        _t1833 = logic_pb2.Loop(init=init1046, body=script1047)
        result1049 = _t1833
        self.record_span(span_start1048, "Loop")
        return result1049

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1050 = []
        cond1051 = self.match_lookahead_literal("(", 0)
        while cond1051:
            _t1834 = self.parse_instruction()
            item1052 = _t1834
            xs1050.append(item1052)
            cond1051 = self.match_lookahead_literal("(", 0)
        instructions1053 = xs1050
        self.consume_literal(")")
        return instructions1053

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1060 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1836 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1837 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1838 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1839 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1840 = 0
                            else:
                                _t1840 = -1
                            _t1839 = _t1840
                        _t1838 = _t1839
                    _t1837 = _t1838
                _t1836 = _t1837
            _t1835 = _t1836
        else:
            _t1835 = -1
        prediction1054 = _t1835
        if prediction1054 == 4:
            _t1842 = self.parse_monus_def()
            monus_def1059 = _t1842
            _t1843 = logic_pb2.Instruction(monus_def=monus_def1059)
            _t1841 = _t1843
        else:
            if prediction1054 == 3:
                _t1845 = self.parse_monoid_def()
                monoid_def1058 = _t1845
                _t1846 = logic_pb2.Instruction(monoid_def=monoid_def1058)
                _t1844 = _t1846
            else:
                if prediction1054 == 2:
                    _t1848 = self.parse_break()
                    break1057 = _t1848
                    _t1849 = logic_pb2.Instruction()
                    getattr(_t1849, 'break').CopyFrom(break1057)
                    _t1847 = _t1849
                else:
                    if prediction1054 == 1:
                        _t1851 = self.parse_upsert()
                        upsert1056 = _t1851
                        _t1852 = logic_pb2.Instruction(upsert=upsert1056)
                        _t1850 = _t1852
                    else:
                        if prediction1054 == 0:
                            _t1854 = self.parse_assign()
                            assign1055 = _t1854
                            _t1855 = logic_pb2.Instruction(assign=assign1055)
                            _t1853 = _t1855
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1850 = _t1853
                    _t1847 = _t1850
                _t1844 = _t1847
            _t1841 = _t1844
        result1061 = _t1841
        self.record_span(span_start1060, "Instruction")
        return result1061

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1065 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1856 = self.parse_relation_id()
        relation_id1062 = _t1856
        _t1857 = self.parse_abstraction()
        abstraction1063 = _t1857
        if self.match_lookahead_literal("(", 0):
            _t1859 = self.parse_attrs()
            _t1858 = _t1859
        else:
            _t1858 = None
        attrs1064 = _t1858
        self.consume_literal(")")
        _t1860 = logic_pb2.Assign(name=relation_id1062, body=abstraction1063, attrs=(attrs1064 if attrs1064 is not None else []))
        result1066 = _t1860
        self.record_span(span_start1065, "Assign")
        return result1066

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1070 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1861 = self.parse_relation_id()
        relation_id1067 = _t1861
        _t1862 = self.parse_abstraction_with_arity()
        abstraction_with_arity1068 = _t1862
        if self.match_lookahead_literal("(", 0):
            _t1864 = self.parse_attrs()
            _t1863 = _t1864
        else:
            _t1863 = None
        attrs1069 = _t1863
        self.consume_literal(")")
        _t1865 = logic_pb2.Upsert(name=relation_id1067, body=abstraction_with_arity1068[0], attrs=(attrs1069 if attrs1069 is not None else []), value_arity=abstraction_with_arity1068[1])
        result1071 = _t1865
        self.record_span(span_start1070, "Upsert")
        return result1071

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1866 = self.parse_bindings()
        bindings1072 = _t1866
        _t1867 = self.parse_formula()
        formula1073 = _t1867
        self.consume_literal(")")
        _t1868 = logic_pb2.Abstraction(vars=(list(bindings1072[0]) + list(bindings1072[1] if bindings1072[1] is not None else [])), value=formula1073)
        return (_t1868, len(bindings1072[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1077 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1869 = self.parse_relation_id()
        relation_id1074 = _t1869
        _t1870 = self.parse_abstraction()
        abstraction1075 = _t1870
        if self.match_lookahead_literal("(", 0):
            _t1872 = self.parse_attrs()
            _t1871 = _t1872
        else:
            _t1871 = None
        attrs1076 = _t1871
        self.consume_literal(")")
        _t1873 = logic_pb2.Break(name=relation_id1074, body=abstraction1075, attrs=(attrs1076 if attrs1076 is not None else []))
        result1078 = _t1873
        self.record_span(span_start1077, "Break")
        return result1078

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1083 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1874 = self.parse_monoid()
        monoid1079 = _t1874
        _t1875 = self.parse_relation_id()
        relation_id1080 = _t1875
        _t1876 = self.parse_abstraction_with_arity()
        abstraction_with_arity1081 = _t1876
        if self.match_lookahead_literal("(", 0):
            _t1878 = self.parse_attrs()
            _t1877 = _t1878
        else:
            _t1877 = None
        attrs1082 = _t1877
        self.consume_literal(")")
        _t1879 = logic_pb2.MonoidDef(monoid=monoid1079, name=relation_id1080, body=abstraction_with_arity1081[0], attrs=(attrs1082 if attrs1082 is not None else []), value_arity=abstraction_with_arity1081[1])
        result1084 = _t1879
        self.record_span(span_start1083, "MonoidDef")
        return result1084

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1090 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1881 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1882 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1883 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1884 = 2
                        else:
                            _t1884 = -1
                        _t1883 = _t1884
                    _t1882 = _t1883
                _t1881 = _t1882
            _t1880 = _t1881
        else:
            _t1880 = -1
        prediction1085 = _t1880
        if prediction1085 == 3:
            _t1886 = self.parse_sum_monoid()
            sum_monoid1089 = _t1886
            _t1887 = logic_pb2.Monoid(sum_monoid=sum_monoid1089)
            _t1885 = _t1887
        else:
            if prediction1085 == 2:
                _t1889 = self.parse_max_monoid()
                max_monoid1088 = _t1889
                _t1890 = logic_pb2.Monoid(max_monoid=max_monoid1088)
                _t1888 = _t1890
            else:
                if prediction1085 == 1:
                    _t1892 = self.parse_min_monoid()
                    min_monoid1087 = _t1892
                    _t1893 = logic_pb2.Monoid(min_monoid=min_monoid1087)
                    _t1891 = _t1893
                else:
                    if prediction1085 == 0:
                        _t1895 = self.parse_or_monoid()
                        or_monoid1086 = _t1895
                        _t1896 = logic_pb2.Monoid(or_monoid=or_monoid1086)
                        _t1894 = _t1896
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1891 = _t1894
                _t1888 = _t1891
            _t1885 = _t1888
        result1091 = _t1885
        self.record_span(span_start1090, "Monoid")
        return result1091

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1092 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1897 = logic_pb2.OrMonoid()
        result1093 = _t1897
        self.record_span(span_start1092, "OrMonoid")
        return result1093

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1095 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1898 = self.parse_type()
        type1094 = _t1898
        self.consume_literal(")")
        _t1899 = logic_pb2.MinMonoid(type=type1094)
        result1096 = _t1899
        self.record_span(span_start1095, "MinMonoid")
        return result1096

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1098 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1900 = self.parse_type()
        type1097 = _t1900
        self.consume_literal(")")
        _t1901 = logic_pb2.MaxMonoid(type=type1097)
        result1099 = _t1901
        self.record_span(span_start1098, "MaxMonoid")
        return result1099

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1101 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1902 = self.parse_type()
        type1100 = _t1902
        self.consume_literal(")")
        _t1903 = logic_pb2.SumMonoid(type=type1100)
        result1102 = _t1903
        self.record_span(span_start1101, "SumMonoid")
        return result1102

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1107 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1904 = self.parse_monoid()
        monoid1103 = _t1904
        _t1905 = self.parse_relation_id()
        relation_id1104 = _t1905
        _t1906 = self.parse_abstraction_with_arity()
        abstraction_with_arity1105 = _t1906
        if self.match_lookahead_literal("(", 0):
            _t1908 = self.parse_attrs()
            _t1907 = _t1908
        else:
            _t1907 = None
        attrs1106 = _t1907
        self.consume_literal(")")
        _t1909 = logic_pb2.MonusDef(monoid=monoid1103, name=relation_id1104, body=abstraction_with_arity1105[0], attrs=(attrs1106 if attrs1106 is not None else []), value_arity=abstraction_with_arity1105[1])
        result1108 = _t1909
        self.record_span(span_start1107, "MonusDef")
        return result1108

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1113 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1910 = self.parse_relation_id()
        relation_id1109 = _t1910
        _t1911 = self.parse_abstraction()
        abstraction1110 = _t1911
        _t1912 = self.parse_functional_dependency_keys()
        functional_dependency_keys1111 = _t1912
        _t1913 = self.parse_functional_dependency_values()
        functional_dependency_values1112 = _t1913
        self.consume_literal(")")
        _t1914 = logic_pb2.FunctionalDependency(guard=abstraction1110, keys=functional_dependency_keys1111, values=functional_dependency_values1112)
        _t1915 = logic_pb2.Constraint(name=relation_id1109, functional_dependency=_t1914)
        result1114 = _t1915
        self.record_span(span_start1113, "Constraint")
        return result1114

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1115 = []
        cond1116 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1116:
            _t1916 = self.parse_var()
            item1117 = _t1916
            xs1115.append(item1117)
            cond1116 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1118 = xs1115
        self.consume_literal(")")
        return vars1118

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1119 = []
        cond1120 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1120:
            _t1917 = self.parse_var()
            item1121 = _t1917
            xs1119.append(item1121)
            cond1120 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1122 = xs1119
        self.consume_literal(")")
        return vars1122

    def parse_data(self) -> logic_pb2.Data:
        span_start1128 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1919 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1920 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t1921 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t1922 = 1
                        else:
                            _t1922 = -1
                        _t1921 = _t1922
                    _t1920 = _t1921
                _t1919 = _t1920
            _t1918 = _t1919
        else:
            _t1918 = -1
        prediction1123 = _t1918
        if prediction1123 == 3:
            _t1924 = self.parse_iceberg_data()
            iceberg_data1127 = _t1924
            _t1925 = logic_pb2.Data(iceberg_data=iceberg_data1127)
            _t1923 = _t1925
        else:
            if prediction1123 == 2:
                _t1927 = self.parse_csv_data()
                csv_data1126 = _t1927
                _t1928 = logic_pb2.Data(csv_data=csv_data1126)
                _t1926 = _t1928
            else:
                if prediction1123 == 1:
                    _t1930 = self.parse_betree_relation()
                    betree_relation1125 = _t1930
                    _t1931 = logic_pb2.Data(betree_relation=betree_relation1125)
                    _t1929 = _t1931
                else:
                    if prediction1123 == 0:
                        _t1933 = self.parse_edb()
                        edb1124 = _t1933
                        _t1934 = logic_pb2.Data(edb=edb1124)
                        _t1932 = _t1934
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1929 = _t1932
                _t1926 = _t1929
            _t1923 = _t1926
        result1129 = _t1923
        self.record_span(span_start1128, "Data")
        return result1129

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1133 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1935 = self.parse_relation_id()
        relation_id1130 = _t1935
        _t1936 = self.parse_edb_path()
        edb_path1131 = _t1936
        _t1937 = self.parse_edb_types()
        edb_types1132 = _t1937
        self.consume_literal(")")
        _t1938 = logic_pb2.EDB(target_id=relation_id1130, path=edb_path1131, types=edb_types1132)
        result1134 = _t1938
        self.record_span(span_start1133, "EDB")
        return result1134

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1135 = []
        cond1136 = self.match_lookahead_terminal("STRING", 0)
        while cond1136:
            item1137 = self.consume_terminal("STRING")
            xs1135.append(item1137)
            cond1136 = self.match_lookahead_terminal("STRING", 0)
        strings1138 = xs1135
        self.consume_literal("]")
        return strings1138

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1139 = []
        cond1140 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1140:
            _t1939 = self.parse_type()
            item1141 = _t1939
            xs1139.append(item1141)
            cond1140 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1142 = xs1139
        self.consume_literal("]")
        return types1142

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1145 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1940 = self.parse_relation_id()
        relation_id1143 = _t1940
        _t1941 = self.parse_betree_info()
        betree_info1144 = _t1941
        self.consume_literal(")")
        _t1942 = logic_pb2.BeTreeRelation(name=relation_id1143, relation_info=betree_info1144)
        result1146 = _t1942
        self.record_span(span_start1145, "BeTreeRelation")
        return result1146

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1150 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1943 = self.parse_betree_info_key_types()
        betree_info_key_types1147 = _t1943
        _t1944 = self.parse_betree_info_value_types()
        betree_info_value_types1148 = _t1944
        _t1945 = self.parse_config_dict()
        config_dict1149 = _t1945
        self.consume_literal(")")
        _t1946 = self.construct_betree_info(betree_info_key_types1147, betree_info_value_types1148, config_dict1149)
        result1151 = _t1946
        self.record_span(span_start1150, "BeTreeInfo")
        return result1151

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1152 = []
        cond1153 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1153:
            _t1947 = self.parse_type()
            item1154 = _t1947
            xs1152.append(item1154)
            cond1153 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1155 = xs1152
        self.consume_literal(")")
        return types1155

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1156 = []
        cond1157 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1157:
            _t1948 = self.parse_type()
            item1158 = _t1948
            xs1156.append(item1158)
            cond1157 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1159 = xs1156
        self.consume_literal(")")
        return types1159

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1164 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1949 = self.parse_csvlocator()
        csvlocator1160 = _t1949
        _t1950 = self.parse_csv_config()
        csv_config1161 = _t1950
        _t1951 = self.parse_gnf_columns()
        gnf_columns1162 = _t1951
        _t1952 = self.parse_csv_asof()
        csv_asof1163 = _t1952
        self.consume_literal(")")
        _t1953 = logic_pb2.CSVData(locator=csvlocator1160, config=csv_config1161, columns=gnf_columns1162, asof=csv_asof1163)
        result1165 = _t1953
        self.record_span(span_start1164, "CSVData")
        return result1165

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1168 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1955 = self.parse_csv_locator_paths()
            _t1954 = _t1955
        else:
            _t1954 = None
        csv_locator_paths1166 = _t1954
        if self.match_lookahead_literal("(", 0):
            _t1957 = self.parse_csv_locator_inline_data()
            _t1956 = _t1957
        else:
            _t1956 = None
        csv_locator_inline_data1167 = _t1956
        self.consume_literal(")")
        _t1958 = logic_pb2.CSVLocator(paths=(csv_locator_paths1166 if csv_locator_paths1166 is not None else []), inline_data=(csv_locator_inline_data1167 if csv_locator_inline_data1167 is not None else "").encode())
        result1169 = _t1958
        self.record_span(span_start1168, "CSVLocator")
        return result1169

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1170 = []
        cond1171 = self.match_lookahead_terminal("STRING", 0)
        while cond1171:
            item1172 = self.consume_terminal("STRING")
            xs1170.append(item1172)
            cond1171 = self.match_lookahead_terminal("STRING", 0)
        strings1173 = xs1170
        self.consume_literal(")")
        return strings1173

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1174 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1174

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1176 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1959 = self.parse_config_dict()
        config_dict1175 = _t1959
        self.consume_literal(")")
        _t1960 = self.construct_csv_config(config_dict1175)
        result1177 = _t1960
        self.record_span(span_start1176, "CSVConfig")
        return result1177

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1178 = []
        cond1179 = self.match_lookahead_literal("(", 0)
        while cond1179:
            _t1961 = self.parse_gnf_column()
            item1180 = _t1961
            xs1178.append(item1180)
            cond1179 = self.match_lookahead_literal("(", 0)
        gnf_columns1181 = xs1178
        self.consume_literal(")")
        return gnf_columns1181

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1188 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1962 = self.parse_gnf_column_path()
        gnf_column_path1182 = _t1962
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1964 = self.parse_relation_id()
            _t1963 = _t1964
        else:
            _t1963 = None
        relation_id1183 = _t1963
        self.consume_literal("[")
        xs1184 = []
        cond1185 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1185:
            _t1965 = self.parse_type()
            item1186 = _t1965
            xs1184.append(item1186)
            cond1185 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1187 = xs1184
        self.consume_literal("]")
        self.consume_literal(")")
        _t1966 = logic_pb2.GNFColumn(column_path=gnf_column_path1182, target_id=relation_id1183, types=types1187)
        result1189 = _t1966
        self.record_span(span_start1188, "GNFColumn")
        return result1189

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1967 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1968 = 0
            else:
                _t1968 = -1
            _t1967 = _t1968
        prediction1190 = _t1967
        if prediction1190 == 1:
            self.consume_literal("[")
            xs1192 = []
            cond1193 = self.match_lookahead_terminal("STRING", 0)
            while cond1193:
                item1194 = self.consume_terminal("STRING")
                xs1192.append(item1194)
                cond1193 = self.match_lookahead_terminal("STRING", 0)
            strings1195 = xs1192
            self.consume_literal("]")
            _t1969 = strings1195
        else:
            if prediction1190 == 0:
                string1191 = self.consume_terminal("STRING")
                _t1970 = [string1191]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1969 = _t1970
        return _t1969

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1196 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1196

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1201 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t1971 = self.parse_iceberg_locator()
        iceberg_locator1197 = _t1971
        _t1972 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1198 = _t1972
        _t1973 = self.parse_gnf_columns()
        gnf_columns1199 = _t1973
        if self.match_lookahead_literal("(", 0):
            _t1975 = self.parse_iceberg_to_snapshot()
            _t1974 = _t1975
        else:
            _t1974 = None
        iceberg_to_snapshot1200 = _t1974
        self.consume_literal(")")
        _t1976 = logic_pb2.IcebergData(locator=iceberg_locator1197, config=iceberg_catalog_config1198, columns=gnf_columns1199, to_snapshot=(iceberg_to_snapshot1200 if iceberg_to_snapshot1200 is not None else ""))
        result1202 = _t1976
        self.record_span(span_start1201, "IcebergData")
        return result1202

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1209 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1203 = self.consume_terminal("STRING")
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1204 = []
        cond1205 = self.match_lookahead_terminal("STRING", 0)
        while cond1205:
            item1206 = self.consume_terminal("STRING")
            xs1204.append(item1206)
            cond1205 = self.match_lookahead_terminal("STRING", 0)
        strings1207 = xs1204
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string_121208 = self.consume_terminal("STRING")
        self.consume_literal(")")
        self.consume_literal(")")
        _t1977 = logic_pb2.IcebergLocator(table_name=string1203, namespace=strings1207, warehouse=string_121208)
        result1210 = _t1977
        self.record_span(span_start1209, "IcebergLocator")
        return result1210

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1221 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1211 = self.consume_terminal("STRING")
        self.consume_literal(")")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t1979 = self.parse_iceberg_catalog_config_scope()
            _t1978 = _t1979
        else:
            _t1978 = None
        iceberg_catalog_config_scope1212 = _t1978
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1213 = []
        cond1214 = self.match_lookahead_literal("(", 0)
        while cond1214:
            _t1980 = self.parse_iceberg_property_entry()
            item1215 = _t1980
            xs1213.append(item1215)
            cond1214 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1216 = xs1213
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1217 = []
        cond1218 = self.match_lookahead_literal("(", 0)
        while cond1218:
            _t1981 = self.parse_iceberg_property_entry()
            item1219 = _t1981
            xs1217.append(item1219)
            cond1218 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys_131220 = xs1217
        self.consume_literal(")")
        self.consume_literal(")")
        _t1982 = self.construct_iceberg_catalog_config(string1211, iceberg_catalog_config_scope1212, iceberg_property_entrys1216, iceberg_property_entrys_131220)
        result1222 = _t1982
        self.record_span(span_start1221, "IcebergCatalogConfig")
        return result1222

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1223 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1223

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1224 = self.consume_terminal("STRING")
        string_31225 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1224, string_31225,)

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1226 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1226

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1228 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1983 = self.parse_fragment_id()
        fragment_id1227 = _t1983
        self.consume_literal(")")
        _t1984 = transactions_pb2.Undefine(fragment_id=fragment_id1227)
        result1229 = _t1984
        self.record_span(span_start1228, "Undefine")
        return result1229

    def parse_context(self) -> transactions_pb2.Context:
        span_start1234 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1230 = []
        cond1231 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1231:
            _t1985 = self.parse_relation_id()
            item1232 = _t1985
            xs1230.append(item1232)
            cond1231 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1233 = xs1230
        self.consume_literal(")")
        _t1986 = transactions_pb2.Context(relations=relation_ids1233)
        result1235 = _t1986
        self.record_span(span_start1234, "Context")
        return result1235

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1240 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        xs1236 = []
        cond1237 = self.match_lookahead_literal("[", 0)
        while cond1237:
            _t1987 = self.parse_snapshot_mapping()
            item1238 = _t1987
            xs1236.append(item1238)
            cond1237 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1239 = xs1236
        self.consume_literal(")")
        _t1988 = transactions_pb2.Snapshot(mappings=snapshot_mappings1239)
        result1241 = _t1988
        self.record_span(span_start1240, "Snapshot")
        return result1241

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1244 = self.span_start()
        _t1989 = self.parse_edb_path()
        edb_path1242 = _t1989
        _t1990 = self.parse_relation_id()
        relation_id1243 = _t1990
        _t1991 = transactions_pb2.SnapshotMapping(destination_path=edb_path1242, source_relation=relation_id1243)
        result1245 = _t1991
        self.record_span(span_start1244, "SnapshotMapping")
        return result1245

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1246 = []
        cond1247 = self.match_lookahead_literal("(", 0)
        while cond1247:
            _t1992 = self.parse_read()
            item1248 = _t1992
            xs1246.append(item1248)
            cond1247 = self.match_lookahead_literal("(", 0)
        reads1249 = xs1246
        self.consume_literal(")")
        return reads1249

    def parse_read(self) -> transactions_pb2.Read:
        span_start1256 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1994 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1995 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t1996 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t1997 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t1998 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t1999 = 3
                                else:
                                    _t1999 = -1
                                _t1998 = _t1999
                            _t1997 = _t1998
                        _t1996 = _t1997
                    _t1995 = _t1996
                _t1994 = _t1995
            _t1993 = _t1994
        else:
            _t1993 = -1
        prediction1250 = _t1993
        if prediction1250 == 4:
            _t2001 = self.parse_export()
            export1255 = _t2001
            _t2002 = transactions_pb2.Read(export=export1255)
            _t2000 = _t2002
        else:
            if prediction1250 == 3:
                _t2004 = self.parse_abort()
                abort1254 = _t2004
                _t2005 = transactions_pb2.Read(abort=abort1254)
                _t2003 = _t2005
            else:
                if prediction1250 == 2:
                    _t2007 = self.parse_what_if()
                    what_if1253 = _t2007
                    _t2008 = transactions_pb2.Read(what_if=what_if1253)
                    _t2006 = _t2008
                else:
                    if prediction1250 == 1:
                        _t2010 = self.parse_output()
                        output1252 = _t2010
                        _t2011 = transactions_pb2.Read(output=output1252)
                        _t2009 = _t2011
                    else:
                        if prediction1250 == 0:
                            _t2013 = self.parse_demand()
                            demand1251 = _t2013
                            _t2014 = transactions_pb2.Read(demand=demand1251)
                            _t2012 = _t2014
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t2009 = _t2012
                    _t2006 = _t2009
                _t2003 = _t2006
            _t2000 = _t2003
        result1257 = _t2000
        self.record_span(span_start1256, "Read")
        return result1257

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1259 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t2015 = self.parse_relation_id()
        relation_id1258 = _t2015
        self.consume_literal(")")
        _t2016 = transactions_pb2.Demand(relation_id=relation_id1258)
        result1260 = _t2016
        self.record_span(span_start1259, "Demand")
        return result1260

    def parse_output(self) -> transactions_pb2.Output:
        span_start1263 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2017 = self.parse_name()
        name1261 = _t2017
        _t2018 = self.parse_relation_id()
        relation_id1262 = _t2018
        self.consume_literal(")")
        _t2019 = transactions_pb2.Output(name=name1261, relation_id=relation_id1262)
        result1264 = _t2019
        self.record_span(span_start1263, "Output")
        return result1264

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1267 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2020 = self.parse_name()
        name1265 = _t2020
        _t2021 = self.parse_epoch()
        epoch1266 = _t2021
        self.consume_literal(")")
        _t2022 = transactions_pb2.WhatIf(branch=name1265, epoch=epoch1266)
        result1268 = _t2022
        self.record_span(span_start1267, "WhatIf")
        return result1268

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1271 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2024 = self.parse_name()
            _t2023 = _t2024
        else:
            _t2023 = None
        name1269 = _t2023
        _t2025 = self.parse_relation_id()
        relation_id1270 = _t2025
        self.consume_literal(")")
        _t2026 = transactions_pb2.Abort(name=(name1269 if name1269 is not None else "abort"), relation_id=relation_id1270)
        result1272 = _t2026
        self.record_span(span_start1271, "Abort")
        return result1272

    def parse_export(self) -> transactions_pb2.Export:
        span_start1276 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2028 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2029 = 0
                else:
                    _t2029 = -1
                _t2028 = _t2029
            _t2027 = _t2028
        else:
            _t2027 = -1
        prediction1273 = _t2027
        if prediction1273 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2031 = self.parse_export_iceberg_config()
            export_iceberg_config1275 = _t2031
            self.consume_literal(")")
            _t2032 = transactions_pb2.Export(iceberg_config=export_iceberg_config1275)
            _t2030 = _t2032
        else:
            if prediction1273 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2034 = self.parse_export_csv_config()
                export_csv_config1274 = _t2034
                self.consume_literal(")")
                _t2035 = transactions_pb2.Export(csv_config=export_csv_config1274)
                _t2033 = _t2035
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2030 = _t2033
        result1277 = _t2030
        self.record_span(span_start1276, "Export")
        return result1277

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1285 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2037 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2038 = 1
                else:
                    _t2038 = -1
                _t2037 = _t2038
            _t2036 = _t2037
        else:
            _t2036 = -1
        prediction1278 = _t2036
        if prediction1278 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2040 = self.parse_export_csv_path()
            export_csv_path1282 = _t2040
            _t2041 = self.parse_export_csv_columns_list()
            export_csv_columns_list1283 = _t2041
            _t2042 = self.parse_config_dict()
            config_dict1284 = _t2042
            self.consume_literal(")")
            _t2043 = self.construct_export_csv_config(export_csv_path1282, export_csv_columns_list1283, config_dict1284)
            _t2039 = _t2043
        else:
            if prediction1278 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2045 = self.parse_export_csv_path()
                export_csv_path1279 = _t2045
                _t2046 = self.parse_export_csv_source()
                export_csv_source1280 = _t2046
                _t2047 = self.parse_csv_config()
                csv_config1281 = _t2047
                self.consume_literal(")")
                _t2048 = self.construct_export_csv_config_with_source(export_csv_path1279, export_csv_source1280, csv_config1281)
                _t2044 = _t2048
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2039 = _t2044
        result1286 = _t2039
        self.record_span(span_start1285, "ExportCSVConfig")
        return result1286

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1287 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1287

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1294 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2050 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2051 = 0
                else:
                    _t2051 = -1
                _t2050 = _t2051
            _t2049 = _t2050
        else:
            _t2049 = -1
        prediction1288 = _t2049
        if prediction1288 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2053 = self.parse_relation_id()
            relation_id1293 = _t2053
            self.consume_literal(")")
            _t2054 = transactions_pb2.ExportCSVSource(table_def=relation_id1293)
            _t2052 = _t2054
        else:
            if prediction1288 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1289 = []
                cond1290 = self.match_lookahead_literal("(", 0)
                while cond1290:
                    _t2056 = self.parse_export_csv_column()
                    item1291 = _t2056
                    xs1289.append(item1291)
                    cond1290 = self.match_lookahead_literal("(", 0)
                export_csv_columns1292 = xs1289
                self.consume_literal(")")
                _t2057 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1292)
                _t2058 = transactions_pb2.ExportCSVSource(gnf_columns=_t2057)
                _t2055 = _t2058
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2052 = _t2055
        result1295 = _t2052
        self.record_span(span_start1294, "ExportCSVSource")
        return result1295

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1298 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1296 = self.consume_terminal("STRING")
        _t2059 = self.parse_relation_id()
        relation_id1297 = _t2059
        self.consume_literal(")")
        _t2060 = transactions_pb2.ExportCSVColumn(column_name=string1296, column_data=relation_id1297)
        result1299 = _t2060
        self.record_span(span_start1298, "ExportCSVColumn")
        return result1299

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1300 = []
        cond1301 = self.match_lookahead_literal("(", 0)
        while cond1301:
            _t2061 = self.parse_export_csv_column()
            item1302 = _t2061
            xs1300.append(item1302)
            cond1301 = self.match_lookahead_literal("(", 0)
        export_csv_columns1303 = xs1300
        self.consume_literal(")")
        return export_csv_columns1303

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1312 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2062 = self.parse_iceberg_locator()
        iceberg_locator1304 = _t2062
        _t2063 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1305 = _t2063
        _t2064 = self.parse_export_iceberg_columns()
        export_iceberg_columns1306 = _t2064
        self.consume_literal("(")
        self.consume_literal("table_properties")
        xs1307 = []
        cond1308 = self.match_lookahead_literal("(", 0)
        while cond1308:
            _t2065 = self.parse_iceberg_property_entry()
            item1309 = _t2065
            xs1307.append(item1309)
            cond1308 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1310 = xs1307
        self.consume_literal(")")
        if self.match_lookahead_literal("{", 0):
            _t2067 = self.parse_config_dict()
            _t2066 = _t2067
        else:
            _t2066 = None
        config_dict1311 = _t2066
        self.consume_literal(")")
        _t2068 = self.construct_export_iceberg_config_full(iceberg_locator1304, iceberg_catalog_config1305, export_iceberg_columns1306, iceberg_property_entrys1310, config_dict1311)
        result1313 = _t2068
        self.record_span(span_start1312, "ExportIcebergConfig")
        return result1313

    def parse_export_iceberg_columns(self) -> transactions_pb2.ExportIcebergColumns:
        span_start1319 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("columns")
        _t2069 = self.parse_export_iceberg_column_source()
        export_iceberg_column_source1314 = _t2069
        self.consume_literal("(")
        self.consume_literal("target_columns")
        xs1315 = []
        cond1316 = self.match_lookahead_literal("(", 0)
        while cond1316:
            _t2070 = self.parse_export_iceberg_column()
            item1317 = _t2070
            xs1315.append(item1317)
            cond1316 = self.match_lookahead_literal("(", 0)
        export_iceberg_columns1318 = xs1315
        self.consume_literal(")")
        self.consume_literal(")")
        _t2071 = self.merge_export_iceberg_columns(export_iceberg_column_source1314, export_iceberg_columns1318)
        result1320 = _t2071
        self.record_span(span_start1319, "ExportIcebergColumns")
        return result1320

    def parse_export_iceberg_column_source(self) -> transactions_pb2.ExportIcebergColumns:
        span_start1327 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("source_table_def", 1):
                _t2073 = 1
            else:
                if self.match_lookahead_literal("source_gnf_defs", 1):
                    _t2074 = 0
                else:
                    _t2074 = -1
                _t2073 = _t2074
            _t2072 = _t2073
        else:
            _t2072 = -1
        prediction1321 = _t2072
        if prediction1321 == 1:
            self.consume_literal("(")
            self.consume_literal("source_table_def")
            _t2076 = self.parse_relation_id()
            relation_id1326 = _t2076
            self.consume_literal(")")
            _t2077 = transactions_pb2.ExportIcebergColumns(source_table_def=relation_id1326, target_columns=[])
            _t2075 = _t2077
        else:
            if prediction1321 == 0:
                self.consume_literal("(")
                self.consume_literal("source_gnf_defs")
                xs1322 = []
                cond1323 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
                while cond1323:
                    _t2079 = self.parse_relation_id()
                    item1324 = _t2079
                    xs1322.append(item1324)
                    cond1323 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
                relation_ids1325 = xs1322
                self.consume_literal(")")
                _t2080 = transactions_pb2.ExportIcebergGnfDefs(defs=relation_ids1325)
                _t2081 = transactions_pb2.ExportIcebergColumns(source_gnf_defs=_t2080, target_columns=[])
                _t2078 = _t2081
            else:
                raise ParseError("Unexpected token in export_iceberg_column_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2075 = _t2078
        result1328 = _t2075
        self.record_span(span_start1327, "ExportIcebergColumns")
        return result1328

    def parse_export_iceberg_column(self) -> transactions_pb2.ExportIcebergColumn:
        span_start1332 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_column")
        string1329 = self.consume_terminal("STRING")
        _t2082 = self.parse_type()
        type1330 = _t2082
        _t2083 = self.parse_boolean_value()
        boolean_value1331 = _t2083
        self.consume_literal(")")
        _t2084 = transactions_pb2.ExportIcebergColumn(name=string1329, type=type1330, nullable=boolean_value1331)
        result1333 = _t2084
        self.record_span(span_start1332, "ExportIcebergColumn")
        return result1333


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
