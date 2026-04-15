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
            _t2081 = value.HasField("int32_value")
        else:
            _t2081 = False
        if _t2081:
            assert value is not None
            return value.int32_value
        else:
            _t2082 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2083 = value.HasField("int_value")
        else:
            _t2083 = False
        if _t2083:
            assert value is not None
            return value.int_value
        else:
            _t2084 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2085 = value.HasField("string_value")
        else:
            _t2085 = False
        if _t2085:
            assert value is not None
            return value.string_value
        else:
            _t2086 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2087 = value.HasField("boolean_value")
        else:
            _t2087 = False
        if _t2087:
            assert value is not None
            return value.boolean_value
        else:
            _t2088 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2089 = value.HasField("string_value")
        else:
            _t2089 = False
        if _t2089:
            assert value is not None
            return [value.string_value]
        else:
            _t2090 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t2091 = value.HasField("int_value")
        else:
            _t2091 = False
        if _t2091:
            assert value is not None
            return value.int_value
        else:
            _t2092 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2093 = value.HasField("float_value")
        else:
            _t2093 = False
        if _t2093:
            assert value is not None
            return value.float_value
        else:
            _t2094 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2095 = value.HasField("string_value")
        else:
            _t2095 = False
        if _t2095:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2096 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2097 = value.HasField("uint128_value")
        else:
            _t2097 = False
        if _t2097:
            assert value is not None
            return value.uint128_value
        else:
            _t2098 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2099 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2099
        _t2100 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2100
        _t2101 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2101
        _t2102 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2102
        _t2103 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2103
        _t2104 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2104
        _t2105 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2105
        _t2106 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2106
        _t2107 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2107
        _t2108 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2108
        _t2109 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t2109
        _t2110 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2110
        _t2111 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t2111

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2112 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2112
        _t2113 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2113
        _t2114 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2114
        _t2115 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2115
        _t2116 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2116
        _t2117 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2117
        _t2118 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2118
        _t2119 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2119
        _t2120 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2120
        _t2121 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2121
        _t2122 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2122

    def default_configure(self) -> transactions_pb2.Configure:
        _t2123 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2123
        _t2124 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2124

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
        _t2125 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2125
        _t2126 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2126
        _t2127 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t2127

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2128 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2128
        _t2129 = self._extract_value_string(config.get("compression"), "")
        compression = _t2129
        _t2130 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2130
        _t2131 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2131
        _t2132 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2132
        _t2133 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2133
        _t2134 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2134
        _t2135 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2135

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2136 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t2136

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2137 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2137

    def construct_iceberg_data(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, columns: Sequence[logic_pb2.GNFColumn], from_snapshot_opt: str | None, to_snapshot_opt: str | None, returns_delta: bool) -> logic_pb2.IcebergData:
        _t2138 = logic_pb2.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(from_snapshot_opt if from_snapshot_opt is not None else ""), to_snapshot=(to_snapshot_opt if to_snapshot_opt is not None else ""), returns_delta=returns_delta)
        return _t2138

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, table_def: logic_pb2.RelationId, table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2139 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2139
        _t2140 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2140
        _t2141 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2141
        table_props = dict(table_property_pairs)
        _t2142 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2142

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start671 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1331 = self.parse_configure()
            _t1330 = _t1331
        else:
            _t1330 = None
        configure665 = _t1330
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1333 = self.parse_sync()
            _t1332 = _t1333
        else:
            _t1332 = None
        sync666 = _t1332
        xs667 = []
        cond668 = self.match_lookahead_literal("(", 0)
        while cond668:
            _t1334 = self.parse_epoch()
            item669 = _t1334
            xs667.append(item669)
            cond668 = self.match_lookahead_literal("(", 0)
        epochs670 = xs667
        self.consume_literal(")")
        _t1335 = self.default_configure()
        _t1336 = transactions_pb2.Transaction(epochs=epochs670, configure=(configure665 if configure665 is not None else _t1335), sync=sync666)
        result672 = _t1336
        self.record_span(span_start671, "Transaction")
        return result672

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start674 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1337 = self.parse_config_dict()
        config_dict673 = _t1337
        self.consume_literal(")")
        _t1338 = self.construct_configure(config_dict673)
        result675 = _t1338
        self.record_span(span_start674, "Configure")
        return result675

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs676 = []
        cond677 = self.match_lookahead_literal(":", 0)
        while cond677:
            _t1339 = self.parse_config_key_value()
            item678 = _t1339
            xs676.append(item678)
            cond677 = self.match_lookahead_literal(":", 0)
        config_key_values679 = xs676
        self.consume_literal("}")
        return config_key_values679

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol680 = self.consume_terminal("SYMBOL")
        _t1340 = self.parse_raw_value()
        raw_value681 = _t1340
        return (symbol680, raw_value681,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start695 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1341 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1342 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1343 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1345 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1346 = 0
                            else:
                                _t1346 = -1
                            _t1345 = _t1346
                        _t1344 = _t1345
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1347 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1348 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1349 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1350 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1351 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1352 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1353 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1354 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1355 = 10
                                                        else:
                                                            _t1355 = -1
                                                        _t1354 = _t1355
                                                    _t1353 = _t1354
                                                _t1352 = _t1353
                                            _t1351 = _t1352
                                        _t1350 = _t1351
                                    _t1349 = _t1350
                                _t1348 = _t1349
                            _t1347 = _t1348
                        _t1344 = _t1347
                    _t1343 = _t1344
                _t1342 = _t1343
            _t1341 = _t1342
        prediction682 = _t1341
        if prediction682 == 12:
            _t1357 = self.parse_boolean_value()
            boolean_value694 = _t1357
            _t1358 = logic_pb2.Value(boolean_value=boolean_value694)
            _t1356 = _t1358
        else:
            if prediction682 == 11:
                self.consume_literal("missing")
                _t1360 = logic_pb2.MissingValue()
                _t1361 = logic_pb2.Value(missing_value=_t1360)
                _t1359 = _t1361
            else:
                if prediction682 == 10:
                    decimal693 = self.consume_terminal("DECIMAL")
                    _t1363 = logic_pb2.Value(decimal_value=decimal693)
                    _t1362 = _t1363
                else:
                    if prediction682 == 9:
                        int128692 = self.consume_terminal("INT128")
                        _t1365 = logic_pb2.Value(int128_value=int128692)
                        _t1364 = _t1365
                    else:
                        if prediction682 == 8:
                            uint128691 = self.consume_terminal("UINT128")
                            _t1367 = logic_pb2.Value(uint128_value=uint128691)
                            _t1366 = _t1367
                        else:
                            if prediction682 == 7:
                                uint32690 = self.consume_terminal("UINT32")
                                _t1369 = logic_pb2.Value(uint32_value=uint32690)
                                _t1368 = _t1369
                            else:
                                if prediction682 == 6:
                                    float689 = self.consume_terminal("FLOAT")
                                    _t1371 = logic_pb2.Value(float_value=float689)
                                    _t1370 = _t1371
                                else:
                                    if prediction682 == 5:
                                        float32688 = self.consume_terminal("FLOAT32")
                                        _t1373 = logic_pb2.Value(float32_value=float32688)
                                        _t1372 = _t1373
                                    else:
                                        if prediction682 == 4:
                                            int687 = self.consume_terminal("INT")
                                            _t1375 = logic_pb2.Value(int_value=int687)
                                            _t1374 = _t1375
                                        else:
                                            if prediction682 == 3:
                                                int32686 = self.consume_terminal("INT32")
                                                _t1377 = logic_pb2.Value(int32_value=int32686)
                                                _t1376 = _t1377
                                            else:
                                                if prediction682 == 2:
                                                    string685 = self.consume_terminal("STRING")
                                                    _t1379 = logic_pb2.Value(string_value=string685)
                                                    _t1378 = _t1379
                                                else:
                                                    if prediction682 == 1:
                                                        _t1381 = self.parse_raw_datetime()
                                                        raw_datetime684 = _t1381
                                                        _t1382 = logic_pb2.Value(datetime_value=raw_datetime684)
                                                        _t1380 = _t1382
                                                    else:
                                                        if prediction682 == 0:
                                                            _t1384 = self.parse_raw_date()
                                                            raw_date683 = _t1384
                                                            _t1385 = logic_pb2.Value(date_value=raw_date683)
                                                            _t1383 = _t1385
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1380 = _t1383
                                                    _t1378 = _t1380
                                                _t1376 = _t1378
                                            _t1374 = _t1376
                                        _t1372 = _t1374
                                    _t1370 = _t1372
                                _t1368 = _t1370
                            _t1366 = _t1368
                        _t1364 = _t1366
                    _t1362 = _t1364
                _t1359 = _t1362
            _t1356 = _t1359
        result696 = _t1356
        self.record_span(span_start695, "Value")
        return result696

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start700 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int697 = self.consume_terminal("INT")
        int_3698 = self.consume_terminal("INT")
        int_4699 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1386 = logic_pb2.DateValue(year=int(int697), month=int(int_3698), day=int(int_4699))
        result701 = _t1386
        self.record_span(span_start700, "DateValue")
        return result701

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start709 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int702 = self.consume_terminal("INT")
        int_3703 = self.consume_terminal("INT")
        int_4704 = self.consume_terminal("INT")
        int_5705 = self.consume_terminal("INT")
        int_6706 = self.consume_terminal("INT")
        int_7707 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1387 = self.consume_terminal("INT")
        else:
            _t1387 = None
        int_8708 = _t1387
        self.consume_literal(")")
        _t1388 = logic_pb2.DateTimeValue(year=int(int702), month=int(int_3703), day=int(int_4704), hour=int(int_5705), minute=int(int_6706), second=int(int_7707), microsecond=int((int_8708 if int_8708 is not None else 0)))
        result710 = _t1388
        self.record_span(span_start709, "DateTimeValue")
        return result710

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1389 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1390 = 1
            else:
                _t1390 = -1
            _t1389 = _t1390
        prediction711 = _t1389
        if prediction711 == 1:
            self.consume_literal("false")
            _t1391 = False
        else:
            if prediction711 == 0:
                self.consume_literal("true")
                _t1392 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1391 = _t1392
        return _t1391

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start716 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs712 = []
        cond713 = self.match_lookahead_literal(":", 0)
        while cond713:
            _t1393 = self.parse_fragment_id()
            item714 = _t1393
            xs712.append(item714)
            cond713 = self.match_lookahead_literal(":", 0)
        fragment_ids715 = xs712
        self.consume_literal(")")
        _t1394 = transactions_pb2.Sync(fragments=fragment_ids715)
        result717 = _t1394
        self.record_span(span_start716, "Sync")
        return result717

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start719 = self.span_start()
        self.consume_literal(":")
        symbol718 = self.consume_terminal("SYMBOL")
        result720 = fragments_pb2.FragmentId(id=symbol718.encode())
        self.record_span(span_start719, "FragmentId")
        return result720

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start723 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1396 = self.parse_epoch_writes()
            _t1395 = _t1396
        else:
            _t1395 = None
        epoch_writes721 = _t1395
        if self.match_lookahead_literal("(", 0):
            _t1398 = self.parse_epoch_reads()
            _t1397 = _t1398
        else:
            _t1397 = None
        epoch_reads722 = _t1397
        self.consume_literal(")")
        _t1399 = transactions_pb2.Epoch(writes=(epoch_writes721 if epoch_writes721 is not None else []), reads=(epoch_reads722 if epoch_reads722 is not None else []))
        result724 = _t1399
        self.record_span(span_start723, "Epoch")
        return result724

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs725 = []
        cond726 = self.match_lookahead_literal("(", 0)
        while cond726:
            _t1400 = self.parse_write()
            item727 = _t1400
            xs725.append(item727)
            cond726 = self.match_lookahead_literal("(", 0)
        writes728 = xs725
        self.consume_literal(")")
        return writes728

    def parse_write(self) -> transactions_pb2.Write:
        span_start734 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1402 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1403 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1404 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1405 = 2
                        else:
                            _t1405 = -1
                        _t1404 = _t1405
                    _t1403 = _t1404
                _t1402 = _t1403
            _t1401 = _t1402
        else:
            _t1401 = -1
        prediction729 = _t1401
        if prediction729 == 3:
            _t1407 = self.parse_snapshot()
            snapshot733 = _t1407
            _t1408 = transactions_pb2.Write(snapshot=snapshot733)
            _t1406 = _t1408
        else:
            if prediction729 == 2:
                _t1410 = self.parse_context()
                context732 = _t1410
                _t1411 = transactions_pb2.Write(context=context732)
                _t1409 = _t1411
            else:
                if prediction729 == 1:
                    _t1413 = self.parse_undefine()
                    undefine731 = _t1413
                    _t1414 = transactions_pb2.Write(undefine=undefine731)
                    _t1412 = _t1414
                else:
                    if prediction729 == 0:
                        _t1416 = self.parse_define()
                        define730 = _t1416
                        _t1417 = transactions_pb2.Write(define=define730)
                        _t1415 = _t1417
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1412 = _t1415
                _t1409 = _t1412
            _t1406 = _t1409
        result735 = _t1406
        self.record_span(span_start734, "Write")
        return result735

    def parse_define(self) -> transactions_pb2.Define:
        span_start737 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1418 = self.parse_fragment()
        fragment736 = _t1418
        self.consume_literal(")")
        _t1419 = transactions_pb2.Define(fragment=fragment736)
        result738 = _t1419
        self.record_span(span_start737, "Define")
        return result738

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start744 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1420 = self.parse_new_fragment_id()
        new_fragment_id739 = _t1420
        xs740 = []
        cond741 = self.match_lookahead_literal("(", 0)
        while cond741:
            _t1421 = self.parse_declaration()
            item742 = _t1421
            xs740.append(item742)
            cond741 = self.match_lookahead_literal("(", 0)
        declarations743 = xs740
        self.consume_literal(")")
        result745 = self.construct_fragment(new_fragment_id739, declarations743)
        self.record_span(span_start744, "Fragment")
        return result745

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start747 = self.span_start()
        _t1422 = self.parse_fragment_id()
        fragment_id746 = _t1422
        self.start_fragment(fragment_id746)
        result748 = fragment_id746
        self.record_span(span_start747, "FragmentId")
        return result748

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start754 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1424 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1425 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1426 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1427 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1428 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1429 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1430 = 1
                                    else:
                                        _t1430 = -1
                                    _t1429 = _t1430
                                _t1428 = _t1429
                            _t1427 = _t1428
                        _t1426 = _t1427
                    _t1425 = _t1426
                _t1424 = _t1425
            _t1423 = _t1424
        else:
            _t1423 = -1
        prediction749 = _t1423
        if prediction749 == 3:
            _t1432 = self.parse_data()
            data753 = _t1432
            _t1433 = logic_pb2.Declaration(data=data753)
            _t1431 = _t1433
        else:
            if prediction749 == 2:
                _t1435 = self.parse_constraint()
                constraint752 = _t1435
                _t1436 = logic_pb2.Declaration(constraint=constraint752)
                _t1434 = _t1436
            else:
                if prediction749 == 1:
                    _t1438 = self.parse_algorithm()
                    algorithm751 = _t1438
                    _t1439 = logic_pb2.Declaration(algorithm=algorithm751)
                    _t1437 = _t1439
                else:
                    if prediction749 == 0:
                        _t1441 = self.parse_def()
                        def750 = _t1441
                        _t1442 = logic_pb2.Declaration()
                        getattr(_t1442, 'def').CopyFrom(def750)
                        _t1440 = _t1442
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1437 = _t1440
                _t1434 = _t1437
            _t1431 = _t1434
        result755 = _t1431
        self.record_span(span_start754, "Declaration")
        return result755

    def parse_def(self) -> logic_pb2.Def:
        span_start759 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1443 = self.parse_relation_id()
        relation_id756 = _t1443
        _t1444 = self.parse_abstraction()
        abstraction757 = _t1444
        if self.match_lookahead_literal("(", 0):
            _t1446 = self.parse_attrs()
            _t1445 = _t1446
        else:
            _t1445 = None
        attrs758 = _t1445
        self.consume_literal(")")
        _t1447 = logic_pb2.Def(name=relation_id756, body=abstraction757, attrs=(attrs758 if attrs758 is not None else []))
        result760 = _t1447
        self.record_span(span_start759, "Def")
        return result760

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start764 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1448 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1449 = 1
            else:
                _t1449 = -1
            _t1448 = _t1449
        prediction761 = _t1448
        if prediction761 == 1:
            uint128763 = self.consume_terminal("UINT128")
            _t1450 = logic_pb2.RelationId(id_low=uint128763.low, id_high=uint128763.high)
        else:
            if prediction761 == 0:
                self.consume_literal(":")
                symbol762 = self.consume_terminal("SYMBOL")
                _t1451 = self.relation_id_from_string(symbol762)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1450 = _t1451
        result765 = _t1450
        self.record_span(span_start764, "RelationId")
        return result765

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start768 = self.span_start()
        self.consume_literal("(")
        _t1452 = self.parse_bindings()
        bindings766 = _t1452
        _t1453 = self.parse_formula()
        formula767 = _t1453
        self.consume_literal(")")
        _t1454 = logic_pb2.Abstraction(vars=(list(bindings766[0]) + list(bindings766[1] if bindings766[1] is not None else [])), value=formula767)
        result769 = _t1454
        self.record_span(span_start768, "Abstraction")
        return result769

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs770 = []
        cond771 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond771:
            _t1455 = self.parse_binding()
            item772 = _t1455
            xs770.append(item772)
            cond771 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings773 = xs770
        if self.match_lookahead_literal("|", 0):
            _t1457 = self.parse_value_bindings()
            _t1456 = _t1457
        else:
            _t1456 = None
        value_bindings774 = _t1456
        self.consume_literal("]")
        return (bindings773, (value_bindings774 if value_bindings774 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start777 = self.span_start()
        symbol775 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1458 = self.parse_type()
        type776 = _t1458
        _t1459 = logic_pb2.Var(name=symbol775)
        _t1460 = logic_pb2.Binding(var=_t1459, type=type776)
        result778 = _t1460
        self.record_span(span_start777, "Binding")
        return result778

    def parse_type(self) -> logic_pb2.Type:
        span_start794 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1461 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1462 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1463 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1464 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1465 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1466 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1467 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1468 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1469 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1470 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1471 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1472 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1473 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1474 = 9
                                                            else:
                                                                _t1474 = -1
                                                            _t1473 = _t1474
                                                        _t1472 = _t1473
                                                    _t1471 = _t1472
                                                _t1470 = _t1471
                                            _t1469 = _t1470
                                        _t1468 = _t1469
                                    _t1467 = _t1468
                                _t1466 = _t1467
                            _t1465 = _t1466
                        _t1464 = _t1465
                    _t1463 = _t1464
                _t1462 = _t1463
            _t1461 = _t1462
        prediction779 = _t1461
        if prediction779 == 13:
            _t1476 = self.parse_uint32_type()
            uint32_type793 = _t1476
            _t1477 = logic_pb2.Type(uint32_type=uint32_type793)
            _t1475 = _t1477
        else:
            if prediction779 == 12:
                _t1479 = self.parse_float32_type()
                float32_type792 = _t1479
                _t1480 = logic_pb2.Type(float32_type=float32_type792)
                _t1478 = _t1480
            else:
                if prediction779 == 11:
                    _t1482 = self.parse_int32_type()
                    int32_type791 = _t1482
                    _t1483 = logic_pb2.Type(int32_type=int32_type791)
                    _t1481 = _t1483
                else:
                    if prediction779 == 10:
                        _t1485 = self.parse_boolean_type()
                        boolean_type790 = _t1485
                        _t1486 = logic_pb2.Type(boolean_type=boolean_type790)
                        _t1484 = _t1486
                    else:
                        if prediction779 == 9:
                            _t1488 = self.parse_decimal_type()
                            decimal_type789 = _t1488
                            _t1489 = logic_pb2.Type(decimal_type=decimal_type789)
                            _t1487 = _t1489
                        else:
                            if prediction779 == 8:
                                _t1491 = self.parse_missing_type()
                                missing_type788 = _t1491
                                _t1492 = logic_pb2.Type(missing_type=missing_type788)
                                _t1490 = _t1492
                            else:
                                if prediction779 == 7:
                                    _t1494 = self.parse_datetime_type()
                                    datetime_type787 = _t1494
                                    _t1495 = logic_pb2.Type(datetime_type=datetime_type787)
                                    _t1493 = _t1495
                                else:
                                    if prediction779 == 6:
                                        _t1497 = self.parse_date_type()
                                        date_type786 = _t1497
                                        _t1498 = logic_pb2.Type(date_type=date_type786)
                                        _t1496 = _t1498
                                    else:
                                        if prediction779 == 5:
                                            _t1500 = self.parse_int128_type()
                                            int128_type785 = _t1500
                                            _t1501 = logic_pb2.Type(int128_type=int128_type785)
                                            _t1499 = _t1501
                                        else:
                                            if prediction779 == 4:
                                                _t1503 = self.parse_uint128_type()
                                                uint128_type784 = _t1503
                                                _t1504 = logic_pb2.Type(uint128_type=uint128_type784)
                                                _t1502 = _t1504
                                            else:
                                                if prediction779 == 3:
                                                    _t1506 = self.parse_float_type()
                                                    float_type783 = _t1506
                                                    _t1507 = logic_pb2.Type(float_type=float_type783)
                                                    _t1505 = _t1507
                                                else:
                                                    if prediction779 == 2:
                                                        _t1509 = self.parse_int_type()
                                                        int_type782 = _t1509
                                                        _t1510 = logic_pb2.Type(int_type=int_type782)
                                                        _t1508 = _t1510
                                                    else:
                                                        if prediction779 == 1:
                                                            _t1512 = self.parse_string_type()
                                                            string_type781 = _t1512
                                                            _t1513 = logic_pb2.Type(string_type=string_type781)
                                                            _t1511 = _t1513
                                                        else:
                                                            if prediction779 == 0:
                                                                _t1515 = self.parse_unspecified_type()
                                                                unspecified_type780 = _t1515
                                                                _t1516 = logic_pb2.Type(unspecified_type=unspecified_type780)
                                                                _t1514 = _t1516
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t1511 = _t1514
                                                        _t1508 = _t1511
                                                    _t1505 = _t1508
                                                _t1502 = _t1505
                                            _t1499 = _t1502
                                        _t1496 = _t1499
                                    _t1493 = _t1496
                                _t1490 = _t1493
                            _t1487 = _t1490
                        _t1484 = _t1487
                    _t1481 = _t1484
                _t1478 = _t1481
            _t1475 = _t1478
        result795 = _t1475
        self.record_span(span_start794, "Type")
        return result795

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start796 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1517 = logic_pb2.UnspecifiedType()
        result797 = _t1517
        self.record_span(span_start796, "UnspecifiedType")
        return result797

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start798 = self.span_start()
        self.consume_literal("STRING")
        _t1518 = logic_pb2.StringType()
        result799 = _t1518
        self.record_span(span_start798, "StringType")
        return result799

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start800 = self.span_start()
        self.consume_literal("INT")
        _t1519 = logic_pb2.IntType()
        result801 = _t1519
        self.record_span(span_start800, "IntType")
        return result801

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start802 = self.span_start()
        self.consume_literal("FLOAT")
        _t1520 = logic_pb2.FloatType()
        result803 = _t1520
        self.record_span(span_start802, "FloatType")
        return result803

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start804 = self.span_start()
        self.consume_literal("UINT128")
        _t1521 = logic_pb2.UInt128Type()
        result805 = _t1521
        self.record_span(span_start804, "UInt128Type")
        return result805

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start806 = self.span_start()
        self.consume_literal("INT128")
        _t1522 = logic_pb2.Int128Type()
        result807 = _t1522
        self.record_span(span_start806, "Int128Type")
        return result807

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start808 = self.span_start()
        self.consume_literal("DATE")
        _t1523 = logic_pb2.DateType()
        result809 = _t1523
        self.record_span(span_start808, "DateType")
        return result809

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start810 = self.span_start()
        self.consume_literal("DATETIME")
        _t1524 = logic_pb2.DateTimeType()
        result811 = _t1524
        self.record_span(span_start810, "DateTimeType")
        return result811

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start812 = self.span_start()
        self.consume_literal("MISSING")
        _t1525 = logic_pb2.MissingType()
        result813 = _t1525
        self.record_span(span_start812, "MissingType")
        return result813

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start816 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int814 = self.consume_terminal("INT")
        int_3815 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1526 = logic_pb2.DecimalType(precision=int(int814), scale=int(int_3815))
        result817 = _t1526
        self.record_span(span_start816, "DecimalType")
        return result817

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start818 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1527 = logic_pb2.BooleanType()
        result819 = _t1527
        self.record_span(span_start818, "BooleanType")
        return result819

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start820 = self.span_start()
        self.consume_literal("INT32")
        _t1528 = logic_pb2.Int32Type()
        result821 = _t1528
        self.record_span(span_start820, "Int32Type")
        return result821

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start822 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1529 = logic_pb2.Float32Type()
        result823 = _t1529
        self.record_span(span_start822, "Float32Type")
        return result823

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start824 = self.span_start()
        self.consume_literal("UINT32")
        _t1530 = logic_pb2.UInt32Type()
        result825 = _t1530
        self.record_span(span_start824, "UInt32Type")
        return result825

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs826 = []
        cond827 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond827:
            _t1531 = self.parse_binding()
            item828 = _t1531
            xs826.append(item828)
            cond827 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings829 = xs826
        return bindings829

    def parse_formula(self) -> logic_pb2.Formula:
        span_start844 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1533 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1534 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1535 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1536 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1537 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1538 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1539 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1540 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1541 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1542 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1543 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1544 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1545 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1546 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1547 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1548 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1549 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1550 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1551 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1552 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1553 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1554 = 10
                                                                                                else:
                                                                                                    _t1554 = -1
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
                        _t1535 = _t1536
                    _t1534 = _t1535
                _t1533 = _t1534
            _t1532 = _t1533
        else:
            _t1532 = -1
        prediction830 = _t1532
        if prediction830 == 12:
            _t1556 = self.parse_cast()
            cast843 = _t1556
            _t1557 = logic_pb2.Formula(cast=cast843)
            _t1555 = _t1557
        else:
            if prediction830 == 11:
                _t1559 = self.parse_rel_atom()
                rel_atom842 = _t1559
                _t1560 = logic_pb2.Formula(rel_atom=rel_atom842)
                _t1558 = _t1560
            else:
                if prediction830 == 10:
                    _t1562 = self.parse_primitive()
                    primitive841 = _t1562
                    _t1563 = logic_pb2.Formula(primitive=primitive841)
                    _t1561 = _t1563
                else:
                    if prediction830 == 9:
                        _t1565 = self.parse_pragma()
                        pragma840 = _t1565
                        _t1566 = logic_pb2.Formula(pragma=pragma840)
                        _t1564 = _t1566
                    else:
                        if prediction830 == 8:
                            _t1568 = self.parse_atom()
                            atom839 = _t1568
                            _t1569 = logic_pb2.Formula(atom=atom839)
                            _t1567 = _t1569
                        else:
                            if prediction830 == 7:
                                _t1571 = self.parse_ffi()
                                ffi838 = _t1571
                                _t1572 = logic_pb2.Formula(ffi=ffi838)
                                _t1570 = _t1572
                            else:
                                if prediction830 == 6:
                                    _t1574 = self.parse_not()
                                    not837 = _t1574
                                    _t1575 = logic_pb2.Formula()
                                    getattr(_t1575, 'not').CopyFrom(not837)
                                    _t1573 = _t1575
                                else:
                                    if prediction830 == 5:
                                        _t1577 = self.parse_disjunction()
                                        disjunction836 = _t1577
                                        _t1578 = logic_pb2.Formula(disjunction=disjunction836)
                                        _t1576 = _t1578
                                    else:
                                        if prediction830 == 4:
                                            _t1580 = self.parse_conjunction()
                                            conjunction835 = _t1580
                                            _t1581 = logic_pb2.Formula(conjunction=conjunction835)
                                            _t1579 = _t1581
                                        else:
                                            if prediction830 == 3:
                                                _t1583 = self.parse_reduce()
                                                reduce834 = _t1583
                                                _t1584 = logic_pb2.Formula(reduce=reduce834)
                                                _t1582 = _t1584
                                            else:
                                                if prediction830 == 2:
                                                    _t1586 = self.parse_exists()
                                                    exists833 = _t1586
                                                    _t1587 = logic_pb2.Formula(exists=exists833)
                                                    _t1585 = _t1587
                                                else:
                                                    if prediction830 == 1:
                                                        _t1589 = self.parse_false()
                                                        false832 = _t1589
                                                        _t1590 = logic_pb2.Formula(disjunction=false832)
                                                        _t1588 = _t1590
                                                    else:
                                                        if prediction830 == 0:
                                                            _t1592 = self.parse_true()
                                                            true831 = _t1592
                                                            _t1593 = logic_pb2.Formula(conjunction=true831)
                                                            _t1591 = _t1593
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
                _t1558 = _t1561
            _t1555 = _t1558
        result845 = _t1555
        self.record_span(span_start844, "Formula")
        return result845

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start846 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1594 = logic_pb2.Conjunction(args=[])
        result847 = _t1594
        self.record_span(span_start846, "Conjunction")
        return result847

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start848 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1595 = logic_pb2.Disjunction(args=[])
        result849 = _t1595
        self.record_span(span_start848, "Disjunction")
        return result849

    def parse_exists(self) -> logic_pb2.Exists:
        span_start852 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1596 = self.parse_bindings()
        bindings850 = _t1596
        _t1597 = self.parse_formula()
        formula851 = _t1597
        self.consume_literal(")")
        _t1598 = logic_pb2.Abstraction(vars=(list(bindings850[0]) + list(bindings850[1] if bindings850[1] is not None else [])), value=formula851)
        _t1599 = logic_pb2.Exists(body=_t1598)
        result853 = _t1599
        self.record_span(span_start852, "Exists")
        return result853

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start857 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1600 = self.parse_abstraction()
        abstraction854 = _t1600
        _t1601 = self.parse_abstraction()
        abstraction_3855 = _t1601
        _t1602 = self.parse_terms()
        terms856 = _t1602
        self.consume_literal(")")
        _t1603 = logic_pb2.Reduce(op=abstraction854, body=abstraction_3855, terms=terms856)
        result858 = _t1603
        self.record_span(span_start857, "Reduce")
        return result858

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs859 = []
        cond860 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond860:
            _t1604 = self.parse_term()
            item861 = _t1604
            xs859.append(item861)
            cond860 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms862 = xs859
        self.consume_literal(")")
        return terms862

    def parse_term(self) -> logic_pb2.Term:
        span_start866 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1605 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1606 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1607 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1608 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1609 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1610 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1611 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1612 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1613 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1614 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1615 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1616 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1617 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1618 = 1
                                                            else:
                                                                _t1618 = -1
                                                            _t1617 = _t1618
                                                        _t1616 = _t1617
                                                    _t1615 = _t1616
                                                _t1614 = _t1615
                                            _t1613 = _t1614
                                        _t1612 = _t1613
                                    _t1611 = _t1612
                                _t1610 = _t1611
                            _t1609 = _t1610
                        _t1608 = _t1609
                    _t1607 = _t1608
                _t1606 = _t1607
            _t1605 = _t1606
        prediction863 = _t1605
        if prediction863 == 1:
            _t1620 = self.parse_value()
            value865 = _t1620
            _t1621 = logic_pb2.Term(constant=value865)
            _t1619 = _t1621
        else:
            if prediction863 == 0:
                _t1623 = self.parse_var()
                var864 = _t1623
                _t1624 = logic_pb2.Term(var=var864)
                _t1622 = _t1624
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1619 = _t1622
        result867 = _t1619
        self.record_span(span_start866, "Term")
        return result867

    def parse_var(self) -> logic_pb2.Var:
        span_start869 = self.span_start()
        symbol868 = self.consume_terminal("SYMBOL")
        _t1625 = logic_pb2.Var(name=symbol868)
        result870 = _t1625
        self.record_span(span_start869, "Var")
        return result870

    def parse_value(self) -> logic_pb2.Value:
        span_start884 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1626 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1627 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1628 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1630 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1631 = 0
                            else:
                                _t1631 = -1
                            _t1630 = _t1631
                        _t1629 = _t1630
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1632 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1633 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1634 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1635 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1636 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1637 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1638 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1639 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
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
                        _t1629 = _t1632
                    _t1628 = _t1629
                _t1627 = _t1628
            _t1626 = _t1627
        prediction871 = _t1626
        if prediction871 == 12:
            _t1642 = self.parse_boolean_value()
            boolean_value883 = _t1642
            _t1643 = logic_pb2.Value(boolean_value=boolean_value883)
            _t1641 = _t1643
        else:
            if prediction871 == 11:
                self.consume_literal("missing")
                _t1645 = logic_pb2.MissingValue()
                _t1646 = logic_pb2.Value(missing_value=_t1645)
                _t1644 = _t1646
            else:
                if prediction871 == 10:
                    formatted_decimal882 = self.consume_terminal("DECIMAL")
                    _t1648 = logic_pb2.Value(decimal_value=formatted_decimal882)
                    _t1647 = _t1648
                else:
                    if prediction871 == 9:
                        formatted_int128881 = self.consume_terminal("INT128")
                        _t1650 = logic_pb2.Value(int128_value=formatted_int128881)
                        _t1649 = _t1650
                    else:
                        if prediction871 == 8:
                            formatted_uint128880 = self.consume_terminal("UINT128")
                            _t1652 = logic_pb2.Value(uint128_value=formatted_uint128880)
                            _t1651 = _t1652
                        else:
                            if prediction871 == 7:
                                formatted_uint32879 = self.consume_terminal("UINT32")
                                _t1654 = logic_pb2.Value(uint32_value=formatted_uint32879)
                                _t1653 = _t1654
                            else:
                                if prediction871 == 6:
                                    formatted_float878 = self.consume_terminal("FLOAT")
                                    _t1656 = logic_pb2.Value(float_value=formatted_float878)
                                    _t1655 = _t1656
                                else:
                                    if prediction871 == 5:
                                        formatted_float32877 = self.consume_terminal("FLOAT32")
                                        _t1658 = logic_pb2.Value(float32_value=formatted_float32877)
                                        _t1657 = _t1658
                                    else:
                                        if prediction871 == 4:
                                            formatted_int876 = self.consume_terminal("INT")
                                            _t1660 = logic_pb2.Value(int_value=formatted_int876)
                                            _t1659 = _t1660
                                        else:
                                            if prediction871 == 3:
                                                formatted_int32875 = self.consume_terminal("INT32")
                                                _t1662 = logic_pb2.Value(int32_value=formatted_int32875)
                                                _t1661 = _t1662
                                            else:
                                                if prediction871 == 2:
                                                    formatted_string874 = self.consume_terminal("STRING")
                                                    _t1664 = logic_pb2.Value(string_value=formatted_string874)
                                                    _t1663 = _t1664
                                                else:
                                                    if prediction871 == 1:
                                                        _t1666 = self.parse_datetime()
                                                        datetime873 = _t1666
                                                        _t1667 = logic_pb2.Value(datetime_value=datetime873)
                                                        _t1665 = _t1667
                                                    else:
                                                        if prediction871 == 0:
                                                            _t1669 = self.parse_date()
                                                            date872 = _t1669
                                                            _t1670 = logic_pb2.Value(date_value=date872)
                                                            _t1668 = _t1670
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1665 = _t1668
                                                    _t1663 = _t1665
                                                _t1661 = _t1663
                                            _t1659 = _t1661
                                        _t1657 = _t1659
                                    _t1655 = _t1657
                                _t1653 = _t1655
                            _t1651 = _t1653
                        _t1649 = _t1651
                    _t1647 = _t1649
                _t1644 = _t1647
            _t1641 = _t1644
        result885 = _t1641
        self.record_span(span_start884, "Value")
        return result885

    def parse_date(self) -> logic_pb2.DateValue:
        span_start889 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int886 = self.consume_terminal("INT")
        formatted_int_3887 = self.consume_terminal("INT")
        formatted_int_4888 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1671 = logic_pb2.DateValue(year=int(formatted_int886), month=int(formatted_int_3887), day=int(formatted_int_4888))
        result890 = _t1671
        self.record_span(span_start889, "DateValue")
        return result890

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start898 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int891 = self.consume_terminal("INT")
        formatted_int_3892 = self.consume_terminal("INT")
        formatted_int_4893 = self.consume_terminal("INT")
        formatted_int_5894 = self.consume_terminal("INT")
        formatted_int_6895 = self.consume_terminal("INT")
        formatted_int_7896 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1672 = self.consume_terminal("INT")
        else:
            _t1672 = None
        formatted_int_8897 = _t1672
        self.consume_literal(")")
        _t1673 = logic_pb2.DateTimeValue(year=int(formatted_int891), month=int(formatted_int_3892), day=int(formatted_int_4893), hour=int(formatted_int_5894), minute=int(formatted_int_6895), second=int(formatted_int_7896), microsecond=int((formatted_int_8897 if formatted_int_8897 is not None else 0)))
        result899 = _t1673
        self.record_span(span_start898, "DateTimeValue")
        return result899

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start904 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs900 = []
        cond901 = self.match_lookahead_literal("(", 0)
        while cond901:
            _t1674 = self.parse_formula()
            item902 = _t1674
            xs900.append(item902)
            cond901 = self.match_lookahead_literal("(", 0)
        formulas903 = xs900
        self.consume_literal(")")
        _t1675 = logic_pb2.Conjunction(args=formulas903)
        result905 = _t1675
        self.record_span(span_start904, "Conjunction")
        return result905

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start910 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs906 = []
        cond907 = self.match_lookahead_literal("(", 0)
        while cond907:
            _t1676 = self.parse_formula()
            item908 = _t1676
            xs906.append(item908)
            cond907 = self.match_lookahead_literal("(", 0)
        formulas909 = xs906
        self.consume_literal(")")
        _t1677 = logic_pb2.Disjunction(args=formulas909)
        result911 = _t1677
        self.record_span(span_start910, "Disjunction")
        return result911

    def parse_not(self) -> logic_pb2.Not:
        span_start913 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1678 = self.parse_formula()
        formula912 = _t1678
        self.consume_literal(")")
        _t1679 = logic_pb2.Not(arg=formula912)
        result914 = _t1679
        self.record_span(span_start913, "Not")
        return result914

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start918 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1680 = self.parse_name()
        name915 = _t1680
        _t1681 = self.parse_ffi_args()
        ffi_args916 = _t1681
        _t1682 = self.parse_terms()
        terms917 = _t1682
        self.consume_literal(")")
        _t1683 = logic_pb2.FFI(name=name915, args=ffi_args916, terms=terms917)
        result919 = _t1683
        self.record_span(span_start918, "FFI")
        return result919

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol920 = self.consume_terminal("SYMBOL")
        return symbol920

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs921 = []
        cond922 = self.match_lookahead_literal("(", 0)
        while cond922:
            _t1684 = self.parse_abstraction()
            item923 = _t1684
            xs921.append(item923)
            cond922 = self.match_lookahead_literal("(", 0)
        abstractions924 = xs921
        self.consume_literal(")")
        return abstractions924

    def parse_atom(self) -> logic_pb2.Atom:
        span_start930 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1685 = self.parse_relation_id()
        relation_id925 = _t1685
        xs926 = []
        cond927 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond927:
            _t1686 = self.parse_term()
            item928 = _t1686
            xs926.append(item928)
            cond927 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms929 = xs926
        self.consume_literal(")")
        _t1687 = logic_pb2.Atom(name=relation_id925, terms=terms929)
        result931 = _t1687
        self.record_span(span_start930, "Atom")
        return result931

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start937 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1688 = self.parse_name()
        name932 = _t1688
        xs933 = []
        cond934 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond934:
            _t1689 = self.parse_term()
            item935 = _t1689
            xs933.append(item935)
            cond934 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms936 = xs933
        self.consume_literal(")")
        _t1690 = logic_pb2.Pragma(name=name932, terms=terms936)
        result938 = _t1690
        self.record_span(span_start937, "Pragma")
        return result938

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start954 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1692 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1693 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1694 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1695 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1696 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1697 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1698 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1699 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1700 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1701 = 7
                                                else:
                                                    _t1701 = -1
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
        else:
            _t1691 = -1
        prediction939 = _t1691
        if prediction939 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1703 = self.parse_name()
            name949 = _t1703
            xs950 = []
            cond951 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond951:
                _t1704 = self.parse_rel_term()
                item952 = _t1704
                xs950.append(item952)
                cond951 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms953 = xs950
            self.consume_literal(")")
            _t1705 = logic_pb2.Primitive(name=name949, terms=rel_terms953)
            _t1702 = _t1705
        else:
            if prediction939 == 8:
                _t1707 = self.parse_divide()
                divide948 = _t1707
                _t1706 = divide948
            else:
                if prediction939 == 7:
                    _t1709 = self.parse_multiply()
                    multiply947 = _t1709
                    _t1708 = multiply947
                else:
                    if prediction939 == 6:
                        _t1711 = self.parse_minus()
                        minus946 = _t1711
                        _t1710 = minus946
                    else:
                        if prediction939 == 5:
                            _t1713 = self.parse_add()
                            add945 = _t1713
                            _t1712 = add945
                        else:
                            if prediction939 == 4:
                                _t1715 = self.parse_gt_eq()
                                gt_eq944 = _t1715
                                _t1714 = gt_eq944
                            else:
                                if prediction939 == 3:
                                    _t1717 = self.parse_gt()
                                    gt943 = _t1717
                                    _t1716 = gt943
                                else:
                                    if prediction939 == 2:
                                        _t1719 = self.parse_lt_eq()
                                        lt_eq942 = _t1719
                                        _t1718 = lt_eq942
                                    else:
                                        if prediction939 == 1:
                                            _t1721 = self.parse_lt()
                                            lt941 = _t1721
                                            _t1720 = lt941
                                        else:
                                            if prediction939 == 0:
                                                _t1723 = self.parse_eq()
                                                eq940 = _t1723
                                                _t1722 = eq940
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1720 = _t1722
                                        _t1718 = _t1720
                                    _t1716 = _t1718
                                _t1714 = _t1716
                            _t1712 = _t1714
                        _t1710 = _t1712
                    _t1708 = _t1710
                _t1706 = _t1708
            _t1702 = _t1706
        result955 = _t1702
        self.record_span(span_start954, "Primitive")
        return result955

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start958 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1724 = self.parse_term()
        term956 = _t1724
        _t1725 = self.parse_term()
        term_3957 = _t1725
        self.consume_literal(")")
        _t1726 = logic_pb2.RelTerm(term=term956)
        _t1727 = logic_pb2.RelTerm(term=term_3957)
        _t1728 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1726, _t1727])
        result959 = _t1728
        self.record_span(span_start958, "Primitive")
        return result959

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start962 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1729 = self.parse_term()
        term960 = _t1729
        _t1730 = self.parse_term()
        term_3961 = _t1730
        self.consume_literal(")")
        _t1731 = logic_pb2.RelTerm(term=term960)
        _t1732 = logic_pb2.RelTerm(term=term_3961)
        _t1733 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1731, _t1732])
        result963 = _t1733
        self.record_span(span_start962, "Primitive")
        return result963

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start966 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1734 = self.parse_term()
        term964 = _t1734
        _t1735 = self.parse_term()
        term_3965 = _t1735
        self.consume_literal(")")
        _t1736 = logic_pb2.RelTerm(term=term964)
        _t1737 = logic_pb2.RelTerm(term=term_3965)
        _t1738 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1736, _t1737])
        result967 = _t1738
        self.record_span(span_start966, "Primitive")
        return result967

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start970 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1739 = self.parse_term()
        term968 = _t1739
        _t1740 = self.parse_term()
        term_3969 = _t1740
        self.consume_literal(")")
        _t1741 = logic_pb2.RelTerm(term=term968)
        _t1742 = logic_pb2.RelTerm(term=term_3969)
        _t1743 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1741, _t1742])
        result971 = _t1743
        self.record_span(span_start970, "Primitive")
        return result971

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start974 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1744 = self.parse_term()
        term972 = _t1744
        _t1745 = self.parse_term()
        term_3973 = _t1745
        self.consume_literal(")")
        _t1746 = logic_pb2.RelTerm(term=term972)
        _t1747 = logic_pb2.RelTerm(term=term_3973)
        _t1748 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1746, _t1747])
        result975 = _t1748
        self.record_span(span_start974, "Primitive")
        return result975

    def parse_add(self) -> logic_pb2.Primitive:
        span_start979 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1749 = self.parse_term()
        term976 = _t1749
        _t1750 = self.parse_term()
        term_3977 = _t1750
        _t1751 = self.parse_term()
        term_4978 = _t1751
        self.consume_literal(")")
        _t1752 = logic_pb2.RelTerm(term=term976)
        _t1753 = logic_pb2.RelTerm(term=term_3977)
        _t1754 = logic_pb2.RelTerm(term=term_4978)
        _t1755 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1752, _t1753, _t1754])
        result980 = _t1755
        self.record_span(span_start979, "Primitive")
        return result980

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start984 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1756 = self.parse_term()
        term981 = _t1756
        _t1757 = self.parse_term()
        term_3982 = _t1757
        _t1758 = self.parse_term()
        term_4983 = _t1758
        self.consume_literal(")")
        _t1759 = logic_pb2.RelTerm(term=term981)
        _t1760 = logic_pb2.RelTerm(term=term_3982)
        _t1761 = logic_pb2.RelTerm(term=term_4983)
        _t1762 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1759, _t1760, _t1761])
        result985 = _t1762
        self.record_span(span_start984, "Primitive")
        return result985

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start989 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1763 = self.parse_term()
        term986 = _t1763
        _t1764 = self.parse_term()
        term_3987 = _t1764
        _t1765 = self.parse_term()
        term_4988 = _t1765
        self.consume_literal(")")
        _t1766 = logic_pb2.RelTerm(term=term986)
        _t1767 = logic_pb2.RelTerm(term=term_3987)
        _t1768 = logic_pb2.RelTerm(term=term_4988)
        _t1769 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1766, _t1767, _t1768])
        result990 = _t1769
        self.record_span(span_start989, "Primitive")
        return result990

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start994 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1770 = self.parse_term()
        term991 = _t1770
        _t1771 = self.parse_term()
        term_3992 = _t1771
        _t1772 = self.parse_term()
        term_4993 = _t1772
        self.consume_literal(")")
        _t1773 = logic_pb2.RelTerm(term=term991)
        _t1774 = logic_pb2.RelTerm(term=term_3992)
        _t1775 = logic_pb2.RelTerm(term=term_4993)
        _t1776 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1773, _t1774, _t1775])
        result995 = _t1776
        self.record_span(span_start994, "Primitive")
        return result995

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start999 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1777 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1778 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1779 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1780 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1781 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1782 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1783 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1784 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1785 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1786 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1787 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1788 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1789 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1790 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1791 = 1
                                                                else:
                                                                    _t1791 = -1
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
                        _t1780 = _t1781
                    _t1779 = _t1780
                _t1778 = _t1779
            _t1777 = _t1778
        prediction996 = _t1777
        if prediction996 == 1:
            _t1793 = self.parse_term()
            term998 = _t1793
            _t1794 = logic_pb2.RelTerm(term=term998)
            _t1792 = _t1794
        else:
            if prediction996 == 0:
                _t1796 = self.parse_specialized_value()
                specialized_value997 = _t1796
                _t1797 = logic_pb2.RelTerm(specialized_value=specialized_value997)
                _t1795 = _t1797
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1792 = _t1795
        result1000 = _t1792
        self.record_span(span_start999, "RelTerm")
        return result1000

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start1002 = self.span_start()
        self.consume_literal("#")
        _t1798 = self.parse_raw_value()
        raw_value1001 = _t1798
        result1003 = raw_value1001
        self.record_span(span_start1002, "Value")
        return result1003

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start1009 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1799 = self.parse_name()
        name1004 = _t1799
        xs1005 = []
        cond1006 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond1006:
            _t1800 = self.parse_rel_term()
            item1007 = _t1800
            xs1005.append(item1007)
            cond1006 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1008 = xs1005
        self.consume_literal(")")
        _t1801 = logic_pb2.RelAtom(name=name1004, terms=rel_terms1008)
        result1010 = _t1801
        self.record_span(span_start1009, "RelAtom")
        return result1010

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1013 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1802 = self.parse_term()
        term1011 = _t1802
        _t1803 = self.parse_term()
        term_31012 = _t1803
        self.consume_literal(")")
        _t1804 = logic_pb2.Cast(input=term1011, result=term_31012)
        result1014 = _t1804
        self.record_span(span_start1013, "Cast")
        return result1014

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1015 = []
        cond1016 = self.match_lookahead_literal("(", 0)
        while cond1016:
            _t1805 = self.parse_attribute()
            item1017 = _t1805
            xs1015.append(item1017)
            cond1016 = self.match_lookahead_literal("(", 0)
        attributes1018 = xs1015
        self.consume_literal(")")
        return attributes1018

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1024 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1806 = self.parse_name()
        name1019 = _t1806
        xs1020 = []
        cond1021 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1021:
            _t1807 = self.parse_raw_value()
            item1022 = _t1807
            xs1020.append(item1022)
            cond1021 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1023 = xs1020
        self.consume_literal(")")
        _t1808 = logic_pb2.Attribute(name=name1019, args=raw_values1023)
        result1025 = _t1808
        self.record_span(span_start1024, "Attribute")
        return result1025

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1032 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1026 = []
        cond1027 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1027:
            _t1809 = self.parse_relation_id()
            item1028 = _t1809
            xs1026.append(item1028)
            cond1027 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1029 = xs1026
        _t1810 = self.parse_script()
        script1030 = _t1810
        if self.match_lookahead_literal("(", 0):
            _t1812 = self.parse_attrs()
            _t1811 = _t1812
        else:
            _t1811 = None
        attrs1031 = _t1811
        self.consume_literal(")")
        _t1813 = logic_pb2.Algorithm(body=script1030, attrs=(attrs1031 if attrs1031 is not None else []))
        getattr(_t1813, 'global').extend(relation_ids1029)
        result1033 = _t1813
        self.record_span(span_start1032, "Algorithm")
        return result1033

    def parse_script(self) -> logic_pb2.Script:
        span_start1038 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1034 = []
        cond1035 = self.match_lookahead_literal("(", 0)
        while cond1035:
            _t1814 = self.parse_construct()
            item1036 = _t1814
            xs1034.append(item1036)
            cond1035 = self.match_lookahead_literal("(", 0)
        constructs1037 = xs1034
        self.consume_literal(")")
        _t1815 = logic_pb2.Script(constructs=constructs1037)
        result1039 = _t1815
        self.record_span(span_start1038, "Script")
        return result1039

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1043 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1817 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1818 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1819 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1820 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1821 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1822 = 1
                                else:
                                    _t1822 = -1
                                _t1821 = _t1822
                            _t1820 = _t1821
                        _t1819 = _t1820
                    _t1818 = _t1819
                _t1817 = _t1818
            _t1816 = _t1817
        else:
            _t1816 = -1
        prediction1040 = _t1816
        if prediction1040 == 1:
            _t1824 = self.parse_instruction()
            instruction1042 = _t1824
            _t1825 = logic_pb2.Construct(instruction=instruction1042)
            _t1823 = _t1825
        else:
            if prediction1040 == 0:
                _t1827 = self.parse_loop()
                loop1041 = _t1827
                _t1828 = logic_pb2.Construct(loop=loop1041)
                _t1826 = _t1828
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1823 = _t1826
        result1044 = _t1823
        self.record_span(span_start1043, "Construct")
        return result1044

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1048 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1829 = self.parse_init()
        init1045 = _t1829
        _t1830 = self.parse_script()
        script1046 = _t1830
        if self.match_lookahead_literal("(", 0):
            _t1832 = self.parse_attrs()
            _t1831 = _t1832
        else:
            _t1831 = None
        attrs1047 = _t1831
        self.consume_literal(")")
        _t1833 = logic_pb2.Loop(init=init1045, body=script1046, attrs=(attrs1047 if attrs1047 is not None else []))
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
        span_start1203 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t1971 = self.parse_iceberg_locator()
        iceberg_locator1197 = _t1971
        _t1972 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1198 = _t1972
        _t1973 = self.parse_gnf_columns()
        gnf_columns1199 = _t1973
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("from_snapshot", 1)):
            _t1975 = self.parse_iceberg_from_snapshot()
            _t1974 = _t1975
        else:
            _t1974 = None
        iceberg_from_snapshot1200 = _t1974
        if self.match_lookahead_literal("(", 0):
            _t1977 = self.parse_iceberg_to_snapshot()
            _t1976 = _t1977
        else:
            _t1976 = None
        iceberg_to_snapshot1201 = _t1976
        _t1978 = self.parse_boolean_value()
        boolean_value1202 = _t1978
        self.consume_literal(")")
        _t1979 = self.construct_iceberg_data(iceberg_locator1197, iceberg_catalog_config1198, gnf_columns1199, iceberg_from_snapshot1200, iceberg_to_snapshot1201, boolean_value1202)
        result1204 = _t1979
        self.record_span(span_start1203, "IcebergData")
        return result1204

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1208 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        _t1980 = self.parse_iceberg_locator_table_name()
        iceberg_locator_table_name1205 = _t1980
        _t1981 = self.parse_iceberg_locator_namespace()
        iceberg_locator_namespace1206 = _t1981
        _t1982 = self.parse_iceberg_locator_warehouse()
        iceberg_locator_warehouse1207 = _t1982
        self.consume_literal(")")
        _t1983 = logic_pb2.IcebergLocator(table_name=iceberg_locator_table_name1205, namespace=iceberg_locator_namespace1206, warehouse=iceberg_locator_warehouse1207)
        result1209 = _t1983
        self.record_span(span_start1208, "IcebergLocator")
        return result1209

    def parse_iceberg_locator_table_name(self) -> str:
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1210 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1210

    def parse_iceberg_locator_namespace(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1211 = []
        cond1212 = self.match_lookahead_terminal("STRING", 0)
        while cond1212:
            item1213 = self.consume_terminal("STRING")
            xs1211.append(item1213)
            cond1212 = self.match_lookahead_terminal("STRING", 0)
        strings1214 = xs1211
        self.consume_literal(")")
        return strings1214

    def parse_iceberg_locator_warehouse(self) -> str:
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string1215 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1215

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1220 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        _t1984 = self.parse_iceberg_catalog_uri()
        iceberg_catalog_uri1216 = _t1984
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t1986 = self.parse_iceberg_catalog_config_scope()
            _t1985 = _t1986
        else:
            _t1985 = None
        iceberg_catalog_config_scope1217 = _t1985
        _t1987 = self.parse_iceberg_properties()
        iceberg_properties1218 = _t1987
        _t1988 = self.parse_iceberg_auth_properties()
        iceberg_auth_properties1219 = _t1988
        self.consume_literal(")")
        _t1989 = self.construct_iceberg_catalog_config(iceberg_catalog_uri1216, iceberg_catalog_config_scope1217, iceberg_properties1218, iceberg_auth_properties1219)
        result1221 = _t1989
        self.record_span(span_start1220, "IcebergCatalogConfig")
        return result1221

    def parse_iceberg_catalog_uri(self) -> str:
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1222 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1222

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1223 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1223

    def parse_iceberg_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1224 = []
        cond1225 = self.match_lookahead_literal("(", 0)
        while cond1225:
            _t1990 = self.parse_iceberg_property_entry()
            item1226 = _t1990
            xs1224.append(item1226)
            cond1225 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1227 = xs1224
        self.consume_literal(")")
        return iceberg_property_entrys1227

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1228 = self.consume_terminal("STRING")
        string_31229 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1228, string_31229,)

    def parse_iceberg_auth_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1230 = []
        cond1231 = self.match_lookahead_literal("(", 0)
        while cond1231:
            _t1991 = self.parse_iceberg_masked_property_entry()
            item1232 = _t1991
            xs1230.append(item1232)
            cond1231 = self.match_lookahead_literal("(", 0)
        iceberg_masked_property_entrys1233 = xs1230
        self.consume_literal(")")
        return iceberg_masked_property_entrys1233

    def parse_iceberg_masked_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1234 = self.consume_terminal("STRING")
        string_31235 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1234, string_31235,)

    def parse_iceberg_from_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("from_snapshot")
        string1236 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1236

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1237 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1237

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1239 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1992 = self.parse_fragment_id()
        fragment_id1238 = _t1992
        self.consume_literal(")")
        _t1993 = transactions_pb2.Undefine(fragment_id=fragment_id1238)
        result1240 = _t1993
        self.record_span(span_start1239, "Undefine")
        return result1240

    def parse_context(self) -> transactions_pb2.Context:
        span_start1245 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1241 = []
        cond1242 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1242:
            _t1994 = self.parse_relation_id()
            item1243 = _t1994
            xs1241.append(item1243)
            cond1242 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1244 = xs1241
        self.consume_literal(")")
        _t1995 = transactions_pb2.Context(relations=relation_ids1244)
        result1246 = _t1995
        self.record_span(span_start1245, "Context")
        return result1246

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1252 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t1996 = self.parse_edb_path()
        edb_path1247 = _t1996
        xs1248 = []
        cond1249 = self.match_lookahead_literal("[", 0)
        while cond1249:
            _t1997 = self.parse_snapshot_mapping()
            item1250 = _t1997
            xs1248.append(item1250)
            cond1249 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1251 = xs1248
        self.consume_literal(")")
        _t1998 = transactions_pb2.Snapshot(prefix=edb_path1247, mappings=snapshot_mappings1251)
        result1253 = _t1998
        self.record_span(span_start1252, "Snapshot")
        return result1253

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1256 = self.span_start()
        _t1999 = self.parse_edb_path()
        edb_path1254 = _t1999
        _t2000 = self.parse_relation_id()
        relation_id1255 = _t2000
        _t2001 = transactions_pb2.SnapshotMapping(destination_path=edb_path1254, source_relation=relation_id1255)
        result1257 = _t2001
        self.record_span(span_start1256, "SnapshotMapping")
        return result1257

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1258 = []
        cond1259 = self.match_lookahead_literal("(", 0)
        while cond1259:
            _t2002 = self.parse_read()
            item1260 = _t2002
            xs1258.append(item1260)
            cond1259 = self.match_lookahead_literal("(", 0)
        reads1261 = xs1258
        self.consume_literal(")")
        return reads1261

    def parse_read(self) -> transactions_pb2.Read:
        span_start1268 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t2004 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t2005 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t2006 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t2007 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t2008 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t2009 = 3
                                else:
                                    _t2009 = -1
                                _t2008 = _t2009
                            _t2007 = _t2008
                        _t2006 = _t2007
                    _t2005 = _t2006
                _t2004 = _t2005
            _t2003 = _t2004
        else:
            _t2003 = -1
        prediction1262 = _t2003
        if prediction1262 == 4:
            _t2011 = self.parse_export()
            export1267 = _t2011
            _t2012 = transactions_pb2.Read(export=export1267)
            _t2010 = _t2012
        else:
            if prediction1262 == 3:
                _t2014 = self.parse_abort()
                abort1266 = _t2014
                _t2015 = transactions_pb2.Read(abort=abort1266)
                _t2013 = _t2015
            else:
                if prediction1262 == 2:
                    _t2017 = self.parse_what_if()
                    what_if1265 = _t2017
                    _t2018 = transactions_pb2.Read(what_if=what_if1265)
                    _t2016 = _t2018
                else:
                    if prediction1262 == 1:
                        _t2020 = self.parse_output()
                        output1264 = _t2020
                        _t2021 = transactions_pb2.Read(output=output1264)
                        _t2019 = _t2021
                    else:
                        if prediction1262 == 0:
                            _t2023 = self.parse_demand()
                            demand1263 = _t2023
                            _t2024 = transactions_pb2.Read(demand=demand1263)
                            _t2022 = _t2024
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t2019 = _t2022
                    _t2016 = _t2019
                _t2013 = _t2016
            _t2010 = _t2013
        result1269 = _t2010
        self.record_span(span_start1268, "Read")
        return result1269

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1271 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t2025 = self.parse_relation_id()
        relation_id1270 = _t2025
        self.consume_literal(")")
        _t2026 = transactions_pb2.Demand(relation_id=relation_id1270)
        result1272 = _t2026
        self.record_span(span_start1271, "Demand")
        return result1272

    def parse_output(self) -> transactions_pb2.Output:
        span_start1275 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2027 = self.parse_name()
        name1273 = _t2027
        _t2028 = self.parse_relation_id()
        relation_id1274 = _t2028
        self.consume_literal(")")
        _t2029 = transactions_pb2.Output(name=name1273, relation_id=relation_id1274)
        result1276 = _t2029
        self.record_span(span_start1275, "Output")
        return result1276

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1279 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2030 = self.parse_name()
        name1277 = _t2030
        _t2031 = self.parse_epoch()
        epoch1278 = _t2031
        self.consume_literal(")")
        _t2032 = transactions_pb2.WhatIf(branch=name1277, epoch=epoch1278)
        result1280 = _t2032
        self.record_span(span_start1279, "WhatIf")
        return result1280

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1283 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2034 = self.parse_name()
            _t2033 = _t2034
        else:
            _t2033 = None
        name1281 = _t2033
        _t2035 = self.parse_relation_id()
        relation_id1282 = _t2035
        self.consume_literal(")")
        _t2036 = transactions_pb2.Abort(name=(name1281 if name1281 is not None else "abort"), relation_id=relation_id1282)
        result1284 = _t2036
        self.record_span(span_start1283, "Abort")
        return result1284

    def parse_export(self) -> transactions_pb2.Export:
        span_start1288 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2038 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2039 = 0
                else:
                    _t2039 = -1
                _t2038 = _t2039
            _t2037 = _t2038
        else:
            _t2037 = -1
        prediction1285 = _t2037
        if prediction1285 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2041 = self.parse_export_iceberg_config()
            export_iceberg_config1287 = _t2041
            self.consume_literal(")")
            _t2042 = transactions_pb2.Export(iceberg_config=export_iceberg_config1287)
            _t2040 = _t2042
        else:
            if prediction1285 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2044 = self.parse_export_csv_config()
                export_csv_config1286 = _t2044
                self.consume_literal(")")
                _t2045 = transactions_pb2.Export(csv_config=export_csv_config1286)
                _t2043 = _t2045
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2040 = _t2043
        result1289 = _t2040
        self.record_span(span_start1288, "Export")
        return result1289

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1297 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2047 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2048 = 1
                else:
                    _t2048 = -1
                _t2047 = _t2048
            _t2046 = _t2047
        else:
            _t2046 = -1
        prediction1290 = _t2046
        if prediction1290 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2050 = self.parse_export_csv_path()
            export_csv_path1294 = _t2050
            _t2051 = self.parse_export_csv_columns_list()
            export_csv_columns_list1295 = _t2051
            _t2052 = self.parse_config_dict()
            config_dict1296 = _t2052
            self.consume_literal(")")
            _t2053 = self.construct_export_csv_config(export_csv_path1294, export_csv_columns_list1295, config_dict1296)
            _t2049 = _t2053
        else:
            if prediction1290 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2055 = self.parse_export_csv_path()
                export_csv_path1291 = _t2055
                _t2056 = self.parse_export_csv_source()
                export_csv_source1292 = _t2056
                _t2057 = self.parse_csv_config()
                csv_config1293 = _t2057
                self.consume_literal(")")
                _t2058 = self.construct_export_csv_config_with_source(export_csv_path1291, export_csv_source1292, csv_config1293)
                _t2054 = _t2058
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2049 = _t2054
        result1298 = _t2049
        self.record_span(span_start1297, "ExportCSVConfig")
        return result1298

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1299 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1299

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1306 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2060 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2061 = 0
                else:
                    _t2061 = -1
                _t2060 = _t2061
            _t2059 = _t2060
        else:
            _t2059 = -1
        prediction1300 = _t2059
        if prediction1300 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2063 = self.parse_relation_id()
            relation_id1305 = _t2063
            self.consume_literal(")")
            _t2064 = transactions_pb2.ExportCSVSource(table_def=relation_id1305)
            _t2062 = _t2064
        else:
            if prediction1300 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1301 = []
                cond1302 = self.match_lookahead_literal("(", 0)
                while cond1302:
                    _t2066 = self.parse_export_csv_column()
                    item1303 = _t2066
                    xs1301.append(item1303)
                    cond1302 = self.match_lookahead_literal("(", 0)
                export_csv_columns1304 = xs1301
                self.consume_literal(")")
                _t2067 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1304)
                _t2068 = transactions_pb2.ExportCSVSource(gnf_columns=_t2067)
                _t2065 = _t2068
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2062 = _t2065
        result1307 = _t2062
        self.record_span(span_start1306, "ExportCSVSource")
        return result1307

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1310 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1308 = self.consume_terminal("STRING")
        _t2069 = self.parse_relation_id()
        relation_id1309 = _t2069
        self.consume_literal(")")
        _t2070 = transactions_pb2.ExportCSVColumn(column_name=string1308, column_data=relation_id1309)
        result1311 = _t2070
        self.record_span(span_start1310, "ExportCSVColumn")
        return result1311

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1312 = []
        cond1313 = self.match_lookahead_literal("(", 0)
        while cond1313:
            _t2071 = self.parse_export_csv_column()
            item1314 = _t2071
            xs1312.append(item1314)
            cond1313 = self.match_lookahead_literal("(", 0)
        export_csv_columns1315 = xs1312
        self.consume_literal(")")
        return export_csv_columns1315

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1321 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2072 = self.parse_iceberg_locator()
        iceberg_locator1316 = _t2072
        _t2073 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1317 = _t2073
        _t2074 = self.parse_export_iceberg_table_def()
        export_iceberg_table_def1318 = _t2074
        _t2075 = self.parse_iceberg_table_properties()
        iceberg_table_properties1319 = _t2075
        if self.match_lookahead_literal("{", 0):
            _t2077 = self.parse_config_dict()
            _t2076 = _t2077
        else:
            _t2076 = None
        config_dict1320 = _t2076
        self.consume_literal(")")
        _t2078 = self.construct_export_iceberg_config_full(iceberg_locator1316, iceberg_catalog_config1317, export_iceberg_table_def1318, iceberg_table_properties1319, config_dict1320)
        result1322 = _t2078
        self.record_span(span_start1321, "ExportIcebergConfig")
        return result1322

    def parse_export_iceberg_table_def(self) -> logic_pb2.RelationId:
        span_start1324 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("table_def")
        _t2079 = self.parse_relation_id()
        relation_id1323 = _t2079
        self.consume_literal(")")
        result1325 = relation_id1323
        self.record_span(span_start1324, "RelationId")
        return result1325

    def parse_iceberg_table_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("table_properties")
        xs1326 = []
        cond1327 = self.match_lookahead_literal("(", 0)
        while cond1327:
            _t2080 = self.parse_iceberg_property_entry()
            item1328 = _t2080
            xs1326.append(item1328)
            cond1327 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1329 = xs1326
        self.consume_literal(")")
        return iceberg_property_entrys1329


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
