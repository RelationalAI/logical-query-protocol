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
            _t2057 = value.HasField("int32_value")
        else:
            _t2057 = False
        if _t2057:
            assert value is not None
            return value.int32_value
        else:
            _t2058 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2059 = value.HasField("int_value")
        else:
            _t2059 = False
        if _t2059:
            assert value is not None
            return value.int_value
        else:
            _t2060 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2061 = value.HasField("string_value")
        else:
            _t2061 = False
        if _t2061:
            assert value is not None
            return value.string_value
        else:
            _t2062 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2063 = value.HasField("boolean_value")
        else:
            _t2063 = False
        if _t2063:
            assert value is not None
            return value.boolean_value
        else:
            _t2064 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2065 = value.HasField("string_value")
        else:
            _t2065 = False
        if _t2065:
            assert value is not None
            return [value.string_value]
        else:
            _t2066 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t2067 = value.HasField("int_value")
        else:
            _t2067 = False
        if _t2067:
            assert value is not None
            return value.int_value
        else:
            _t2068 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2069 = value.HasField("float_value")
        else:
            _t2069 = False
        if _t2069:
            assert value is not None
            return value.float_value
        else:
            _t2070 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2071 = value.HasField("string_value")
        else:
            _t2071 = False
        if _t2071:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2072 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2073 = value.HasField("uint128_value")
        else:
            _t2073 = False
        if _t2073:
            assert value is not None
            return value.uint128_value
        else:
            _t2074 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2075 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2075
        _t2076 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2076
        _t2077 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2077
        _t2078 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2078
        _t2079 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2079
        _t2080 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2080
        _t2081 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2081
        _t2082 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2082
        _t2083 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2083
        _t2084 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2084
        _t2085 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t2085
        _t2086 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2086
        _t2087 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t2087

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2088 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2088
        _t2089 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2089
        _t2090 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2090
        _t2091 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2091
        _t2092 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2092
        _t2093 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2093
        _t2094 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2094
        _t2095 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2095
        _t2096 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2096
        _t2097 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2097
        _t2098 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2098

    def default_configure(self) -> transactions_pb2.Configure:
        _t2099 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2099
        _t2100 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2100

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
        _t2101 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2101
        _t2102 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2102
        _t2103 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t2103

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2104 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2104
        _t2105 = self._extract_value_string(config.get("compression"), "")
        compression = _t2105
        _t2106 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2106
        _t2107 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2107
        _t2108 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2108
        _t2109 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2109
        _t2110 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2110
        _t2111 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2111

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2112 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t2112

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2113 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2113

    def construct_iceberg_locator(self, table_name: str, namespace: Sequence[str], warehouse: str, from_snapshot_opt: str | None, to_snapshot_opt: str | None) -> logic_pb2.IcebergLocator:
        _t2114 = logic_pb2.IcebergLocator(table_name=table_name, namespace=namespace, warehouse=warehouse, from_snapshot=(from_snapshot_opt if from_snapshot_opt is not None else ""), to_snapshot=(to_snapshot_opt if to_snapshot_opt is not None else ""))
        return _t2114

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, table_def: logic_pb2.RelationId, columns: Sequence[transactions_pb2.ExportGNFColumn], table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2115 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2115
        _t2116 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2116
        _t2117 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2117
        table_props = dict(table_property_pairs)
        _t2118 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, columns=columns, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2118

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start664 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1317 = self.parse_configure()
            _t1316 = _t1317
        else:
            _t1316 = None
        configure658 = _t1316
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1319 = self.parse_sync()
            _t1318 = _t1319
        else:
            _t1318 = None
        sync659 = _t1318
        xs660 = []
        cond661 = self.match_lookahead_literal("(", 0)
        while cond661:
            _t1320 = self.parse_epoch()
            item662 = _t1320
            xs660.append(item662)
            cond661 = self.match_lookahead_literal("(", 0)
        epochs663 = xs660
        self.consume_literal(")")
        _t1321 = self.default_configure()
        _t1322 = transactions_pb2.Transaction(epochs=epochs663, configure=(configure658 if configure658 is not None else _t1321), sync=sync659)
        result665 = _t1322
        self.record_span(span_start664, "Transaction")
        return result665

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start667 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1323 = self.parse_config_dict()
        config_dict666 = _t1323
        self.consume_literal(")")
        _t1324 = self.construct_configure(config_dict666)
        result668 = _t1324
        self.record_span(span_start667, "Configure")
        return result668

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs669 = []
        cond670 = self.match_lookahead_literal(":", 0)
        while cond670:
            _t1325 = self.parse_config_key_value()
            item671 = _t1325
            xs669.append(item671)
            cond670 = self.match_lookahead_literal(":", 0)
        config_key_values672 = xs669
        self.consume_literal("}")
        return config_key_values672

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol673 = self.consume_terminal("SYMBOL")
        _t1326 = self.parse_raw_value()
        raw_value674 = _t1326
        return (symbol673, raw_value674,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start688 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1327 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1328 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1329 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1331 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1332 = 0
                            else:
                                _t1332 = -1
                            _t1331 = _t1332
                        _t1330 = _t1331
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1333 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1334 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1335 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1336 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1337 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1338 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1339 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1340 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1341 = 10
                                                        else:
                                                            _t1341 = -1
                                                        _t1340 = _t1341
                                                    _t1339 = _t1340
                                                _t1338 = _t1339
                                            _t1337 = _t1338
                                        _t1336 = _t1337
                                    _t1335 = _t1336
                                _t1334 = _t1335
                            _t1333 = _t1334
                        _t1330 = _t1333
                    _t1329 = _t1330
                _t1328 = _t1329
            _t1327 = _t1328
        prediction675 = _t1327
        if prediction675 == 12:
            _t1343 = self.parse_boolean_value()
            boolean_value687 = _t1343
            _t1344 = logic_pb2.Value(boolean_value=boolean_value687)
            _t1342 = _t1344
        else:
            if prediction675 == 11:
                self.consume_literal("missing")
                _t1346 = logic_pb2.MissingValue()
                _t1347 = logic_pb2.Value(missing_value=_t1346)
                _t1345 = _t1347
            else:
                if prediction675 == 10:
                    decimal686 = self.consume_terminal("DECIMAL")
                    _t1349 = logic_pb2.Value(decimal_value=decimal686)
                    _t1348 = _t1349
                else:
                    if prediction675 == 9:
                        int128685 = self.consume_terminal("INT128")
                        _t1351 = logic_pb2.Value(int128_value=int128685)
                        _t1350 = _t1351
                    else:
                        if prediction675 == 8:
                            uint128684 = self.consume_terminal("UINT128")
                            _t1353 = logic_pb2.Value(uint128_value=uint128684)
                            _t1352 = _t1353
                        else:
                            if prediction675 == 7:
                                uint32683 = self.consume_terminal("UINT32")
                                _t1355 = logic_pb2.Value(uint32_value=uint32683)
                                _t1354 = _t1355
                            else:
                                if prediction675 == 6:
                                    float682 = self.consume_terminal("FLOAT")
                                    _t1357 = logic_pb2.Value(float_value=float682)
                                    _t1356 = _t1357
                                else:
                                    if prediction675 == 5:
                                        float32681 = self.consume_terminal("FLOAT32")
                                        _t1359 = logic_pb2.Value(float32_value=float32681)
                                        _t1358 = _t1359
                                    else:
                                        if prediction675 == 4:
                                            int680 = self.consume_terminal("INT")
                                            _t1361 = logic_pb2.Value(int_value=int680)
                                            _t1360 = _t1361
                                        else:
                                            if prediction675 == 3:
                                                int32679 = self.consume_terminal("INT32")
                                                _t1363 = logic_pb2.Value(int32_value=int32679)
                                                _t1362 = _t1363
                                            else:
                                                if prediction675 == 2:
                                                    string678 = self.consume_terminal("STRING")
                                                    _t1365 = logic_pb2.Value(string_value=string678)
                                                    _t1364 = _t1365
                                                else:
                                                    if prediction675 == 1:
                                                        _t1367 = self.parse_raw_datetime()
                                                        raw_datetime677 = _t1367
                                                        _t1368 = logic_pb2.Value(datetime_value=raw_datetime677)
                                                        _t1366 = _t1368
                                                    else:
                                                        if prediction675 == 0:
                                                            _t1370 = self.parse_raw_date()
                                                            raw_date676 = _t1370
                                                            _t1371 = logic_pb2.Value(date_value=raw_date676)
                                                            _t1369 = _t1371
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1366 = _t1369
                                                    _t1364 = _t1366
                                                _t1362 = _t1364
                                            _t1360 = _t1362
                                        _t1358 = _t1360
                                    _t1356 = _t1358
                                _t1354 = _t1356
                            _t1352 = _t1354
                        _t1350 = _t1352
                    _t1348 = _t1350
                _t1345 = _t1348
            _t1342 = _t1345
        result689 = _t1342
        self.record_span(span_start688, "Value")
        return result689

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start693 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int690 = self.consume_terminal("INT")
        int_3691 = self.consume_terminal("INT")
        int_4692 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1372 = logic_pb2.DateValue(year=int(int690), month=int(int_3691), day=int(int_4692))
        result694 = _t1372
        self.record_span(span_start693, "DateValue")
        return result694

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start702 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int695 = self.consume_terminal("INT")
        int_3696 = self.consume_terminal("INT")
        int_4697 = self.consume_terminal("INT")
        int_5698 = self.consume_terminal("INT")
        int_6699 = self.consume_terminal("INT")
        int_7700 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1373 = self.consume_terminal("INT")
        else:
            _t1373 = None
        int_8701 = _t1373
        self.consume_literal(")")
        _t1374 = logic_pb2.DateTimeValue(year=int(int695), month=int(int_3696), day=int(int_4697), hour=int(int_5698), minute=int(int_6699), second=int(int_7700), microsecond=int((int_8701 if int_8701 is not None else 0)))
        result703 = _t1374
        self.record_span(span_start702, "DateTimeValue")
        return result703

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1375 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1376 = 1
            else:
                _t1376 = -1
            _t1375 = _t1376
        prediction704 = _t1375
        if prediction704 == 1:
            self.consume_literal("false")
            _t1377 = False
        else:
            if prediction704 == 0:
                self.consume_literal("true")
                _t1378 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1377 = _t1378
        return _t1377

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start709 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs705 = []
        cond706 = self.match_lookahead_literal(":", 0)
        while cond706:
            _t1379 = self.parse_fragment_id()
            item707 = _t1379
            xs705.append(item707)
            cond706 = self.match_lookahead_literal(":", 0)
        fragment_ids708 = xs705
        self.consume_literal(")")
        _t1380 = transactions_pb2.Sync(fragments=fragment_ids708)
        result710 = _t1380
        self.record_span(span_start709, "Sync")
        return result710

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start712 = self.span_start()
        self.consume_literal(":")
        symbol711 = self.consume_terminal("SYMBOL")
        result713 = fragments_pb2.FragmentId(id=symbol711.encode())
        self.record_span(span_start712, "FragmentId")
        return result713

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start716 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1382 = self.parse_epoch_writes()
            _t1381 = _t1382
        else:
            _t1381 = None
        epoch_writes714 = _t1381
        if self.match_lookahead_literal("(", 0):
            _t1384 = self.parse_epoch_reads()
            _t1383 = _t1384
        else:
            _t1383 = None
        epoch_reads715 = _t1383
        self.consume_literal(")")
        _t1385 = transactions_pb2.Epoch(writes=(epoch_writes714 if epoch_writes714 is not None else []), reads=(epoch_reads715 if epoch_reads715 is not None else []))
        result717 = _t1385
        self.record_span(span_start716, "Epoch")
        return result717

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs718 = []
        cond719 = self.match_lookahead_literal("(", 0)
        while cond719:
            _t1386 = self.parse_write()
            item720 = _t1386
            xs718.append(item720)
            cond719 = self.match_lookahead_literal("(", 0)
        writes721 = xs718
        self.consume_literal(")")
        return writes721

    def parse_write(self) -> transactions_pb2.Write:
        span_start727 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1388 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1389 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1390 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1391 = 2
                        else:
                            _t1391 = -1
                        _t1390 = _t1391
                    _t1389 = _t1390
                _t1388 = _t1389
            _t1387 = _t1388
        else:
            _t1387 = -1
        prediction722 = _t1387
        if prediction722 == 3:
            _t1393 = self.parse_snapshot()
            snapshot726 = _t1393
            _t1394 = transactions_pb2.Write(snapshot=snapshot726)
            _t1392 = _t1394
        else:
            if prediction722 == 2:
                _t1396 = self.parse_context()
                context725 = _t1396
                _t1397 = transactions_pb2.Write(context=context725)
                _t1395 = _t1397
            else:
                if prediction722 == 1:
                    _t1399 = self.parse_undefine()
                    undefine724 = _t1399
                    _t1400 = transactions_pb2.Write(undefine=undefine724)
                    _t1398 = _t1400
                else:
                    if prediction722 == 0:
                        _t1402 = self.parse_define()
                        define723 = _t1402
                        _t1403 = transactions_pb2.Write(define=define723)
                        _t1401 = _t1403
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1398 = _t1401
                _t1395 = _t1398
            _t1392 = _t1395
        result728 = _t1392
        self.record_span(span_start727, "Write")
        return result728

    def parse_define(self) -> transactions_pb2.Define:
        span_start730 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1404 = self.parse_fragment()
        fragment729 = _t1404
        self.consume_literal(")")
        _t1405 = transactions_pb2.Define(fragment=fragment729)
        result731 = _t1405
        self.record_span(span_start730, "Define")
        return result731

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start737 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1406 = self.parse_new_fragment_id()
        new_fragment_id732 = _t1406
        xs733 = []
        cond734 = self.match_lookahead_literal("(", 0)
        while cond734:
            _t1407 = self.parse_declaration()
            item735 = _t1407
            xs733.append(item735)
            cond734 = self.match_lookahead_literal("(", 0)
        declarations736 = xs733
        self.consume_literal(")")
        result738 = self.construct_fragment(new_fragment_id732, declarations736)
        self.record_span(span_start737, "Fragment")
        return result738

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start740 = self.span_start()
        _t1408 = self.parse_fragment_id()
        fragment_id739 = _t1408
        self.start_fragment(fragment_id739)
        result741 = fragment_id739
        self.record_span(span_start740, "FragmentId")
        return result741

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start747 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1410 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1411 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1412 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1413 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1414 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1415 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1416 = 1
                                    else:
                                        _t1416 = -1
                                    _t1415 = _t1416
                                _t1414 = _t1415
                            _t1413 = _t1414
                        _t1412 = _t1413
                    _t1411 = _t1412
                _t1410 = _t1411
            _t1409 = _t1410
        else:
            _t1409 = -1
        prediction742 = _t1409
        if prediction742 == 3:
            _t1418 = self.parse_data()
            data746 = _t1418
            _t1419 = logic_pb2.Declaration(data=data746)
            _t1417 = _t1419
        else:
            if prediction742 == 2:
                _t1421 = self.parse_constraint()
                constraint745 = _t1421
                _t1422 = logic_pb2.Declaration(constraint=constraint745)
                _t1420 = _t1422
            else:
                if prediction742 == 1:
                    _t1424 = self.parse_algorithm()
                    algorithm744 = _t1424
                    _t1425 = logic_pb2.Declaration(algorithm=algorithm744)
                    _t1423 = _t1425
                else:
                    if prediction742 == 0:
                        _t1427 = self.parse_def()
                        def743 = _t1427
                        _t1428 = logic_pb2.Declaration()
                        getattr(_t1428, 'def').CopyFrom(def743)
                        _t1426 = _t1428
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1423 = _t1426
                _t1420 = _t1423
            _t1417 = _t1420
        result748 = _t1417
        self.record_span(span_start747, "Declaration")
        return result748

    def parse_def(self) -> logic_pb2.Def:
        span_start752 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1429 = self.parse_relation_id()
        relation_id749 = _t1429
        _t1430 = self.parse_abstraction()
        abstraction750 = _t1430
        if self.match_lookahead_literal("(", 0):
            _t1432 = self.parse_attrs()
            _t1431 = _t1432
        else:
            _t1431 = None
        attrs751 = _t1431
        self.consume_literal(")")
        _t1433 = logic_pb2.Def(name=relation_id749, body=abstraction750, attrs=(attrs751 if attrs751 is not None else []))
        result753 = _t1433
        self.record_span(span_start752, "Def")
        return result753

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start757 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1434 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1435 = 1
            else:
                _t1435 = -1
            _t1434 = _t1435
        prediction754 = _t1434
        if prediction754 == 1:
            uint128756 = self.consume_terminal("UINT128")
            _t1436 = logic_pb2.RelationId(id_low=uint128756.low, id_high=uint128756.high)
        else:
            if prediction754 == 0:
                self.consume_literal(":")
                symbol755 = self.consume_terminal("SYMBOL")
                _t1437 = self.relation_id_from_string(symbol755)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1436 = _t1437
        result758 = _t1436
        self.record_span(span_start757, "RelationId")
        return result758

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start761 = self.span_start()
        self.consume_literal("(")
        _t1438 = self.parse_bindings()
        bindings759 = _t1438
        _t1439 = self.parse_formula()
        formula760 = _t1439
        self.consume_literal(")")
        _t1440 = logic_pb2.Abstraction(vars=(list(bindings759[0]) + list(bindings759[1] if bindings759[1] is not None else [])), value=formula760)
        result762 = _t1440
        self.record_span(span_start761, "Abstraction")
        return result762

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs763 = []
        cond764 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond764:
            _t1441 = self.parse_binding()
            item765 = _t1441
            xs763.append(item765)
            cond764 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings766 = xs763
        if self.match_lookahead_literal("|", 0):
            _t1443 = self.parse_value_bindings()
            _t1442 = _t1443
        else:
            _t1442 = None
        value_bindings767 = _t1442
        self.consume_literal("]")
        return (bindings766, (value_bindings767 if value_bindings767 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start770 = self.span_start()
        symbol768 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1444 = self.parse_type()
        type769 = _t1444
        _t1445 = logic_pb2.Var(name=symbol768)
        _t1446 = logic_pb2.Binding(var=_t1445, type=type769)
        result771 = _t1446
        self.record_span(span_start770, "Binding")
        return result771

    def parse_type(self) -> logic_pb2.Type:
        span_start787 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1447 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1448 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1449 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1450 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1451 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1452 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1453 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1454 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1455 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1456 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1457 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1458 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1459 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1460 = 9
                                                            else:
                                                                _t1460 = -1
                                                            _t1459 = _t1460
                                                        _t1458 = _t1459
                                                    _t1457 = _t1458
                                                _t1456 = _t1457
                                            _t1455 = _t1456
                                        _t1454 = _t1455
                                    _t1453 = _t1454
                                _t1452 = _t1453
                            _t1451 = _t1452
                        _t1450 = _t1451
                    _t1449 = _t1450
                _t1448 = _t1449
            _t1447 = _t1448
        prediction772 = _t1447
        if prediction772 == 13:
            _t1462 = self.parse_uint32_type()
            uint32_type786 = _t1462
            _t1463 = logic_pb2.Type(uint32_type=uint32_type786)
            _t1461 = _t1463
        else:
            if prediction772 == 12:
                _t1465 = self.parse_float32_type()
                float32_type785 = _t1465
                _t1466 = logic_pb2.Type(float32_type=float32_type785)
                _t1464 = _t1466
            else:
                if prediction772 == 11:
                    _t1468 = self.parse_int32_type()
                    int32_type784 = _t1468
                    _t1469 = logic_pb2.Type(int32_type=int32_type784)
                    _t1467 = _t1469
                else:
                    if prediction772 == 10:
                        _t1471 = self.parse_boolean_type()
                        boolean_type783 = _t1471
                        _t1472 = logic_pb2.Type(boolean_type=boolean_type783)
                        _t1470 = _t1472
                    else:
                        if prediction772 == 9:
                            _t1474 = self.parse_decimal_type()
                            decimal_type782 = _t1474
                            _t1475 = logic_pb2.Type(decimal_type=decimal_type782)
                            _t1473 = _t1475
                        else:
                            if prediction772 == 8:
                                _t1477 = self.parse_missing_type()
                                missing_type781 = _t1477
                                _t1478 = logic_pb2.Type(missing_type=missing_type781)
                                _t1476 = _t1478
                            else:
                                if prediction772 == 7:
                                    _t1480 = self.parse_datetime_type()
                                    datetime_type780 = _t1480
                                    _t1481 = logic_pb2.Type(datetime_type=datetime_type780)
                                    _t1479 = _t1481
                                else:
                                    if prediction772 == 6:
                                        _t1483 = self.parse_date_type()
                                        date_type779 = _t1483
                                        _t1484 = logic_pb2.Type(date_type=date_type779)
                                        _t1482 = _t1484
                                    else:
                                        if prediction772 == 5:
                                            _t1486 = self.parse_int128_type()
                                            int128_type778 = _t1486
                                            _t1487 = logic_pb2.Type(int128_type=int128_type778)
                                            _t1485 = _t1487
                                        else:
                                            if prediction772 == 4:
                                                _t1489 = self.parse_uint128_type()
                                                uint128_type777 = _t1489
                                                _t1490 = logic_pb2.Type(uint128_type=uint128_type777)
                                                _t1488 = _t1490
                                            else:
                                                if prediction772 == 3:
                                                    _t1492 = self.parse_float_type()
                                                    float_type776 = _t1492
                                                    _t1493 = logic_pb2.Type(float_type=float_type776)
                                                    _t1491 = _t1493
                                                else:
                                                    if prediction772 == 2:
                                                        _t1495 = self.parse_int_type()
                                                        int_type775 = _t1495
                                                        _t1496 = logic_pb2.Type(int_type=int_type775)
                                                        _t1494 = _t1496
                                                    else:
                                                        if prediction772 == 1:
                                                            _t1498 = self.parse_string_type()
                                                            string_type774 = _t1498
                                                            _t1499 = logic_pb2.Type(string_type=string_type774)
                                                            _t1497 = _t1499
                                                        else:
                                                            if prediction772 == 0:
                                                                _t1501 = self.parse_unspecified_type()
                                                                unspecified_type773 = _t1501
                                                                _t1502 = logic_pb2.Type(unspecified_type=unspecified_type773)
                                                                _t1500 = _t1502
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t1497 = _t1500
                                                        _t1494 = _t1497
                                                    _t1491 = _t1494
                                                _t1488 = _t1491
                                            _t1485 = _t1488
                                        _t1482 = _t1485
                                    _t1479 = _t1482
                                _t1476 = _t1479
                            _t1473 = _t1476
                        _t1470 = _t1473
                    _t1467 = _t1470
                _t1464 = _t1467
            _t1461 = _t1464
        result788 = _t1461
        self.record_span(span_start787, "Type")
        return result788

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start789 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1503 = logic_pb2.UnspecifiedType()
        result790 = _t1503
        self.record_span(span_start789, "UnspecifiedType")
        return result790

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start791 = self.span_start()
        self.consume_literal("STRING")
        _t1504 = logic_pb2.StringType()
        result792 = _t1504
        self.record_span(span_start791, "StringType")
        return result792

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start793 = self.span_start()
        self.consume_literal("INT")
        _t1505 = logic_pb2.IntType()
        result794 = _t1505
        self.record_span(span_start793, "IntType")
        return result794

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start795 = self.span_start()
        self.consume_literal("FLOAT")
        _t1506 = logic_pb2.FloatType()
        result796 = _t1506
        self.record_span(span_start795, "FloatType")
        return result796

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start797 = self.span_start()
        self.consume_literal("UINT128")
        _t1507 = logic_pb2.UInt128Type()
        result798 = _t1507
        self.record_span(span_start797, "UInt128Type")
        return result798

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start799 = self.span_start()
        self.consume_literal("INT128")
        _t1508 = logic_pb2.Int128Type()
        result800 = _t1508
        self.record_span(span_start799, "Int128Type")
        return result800

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start801 = self.span_start()
        self.consume_literal("DATE")
        _t1509 = logic_pb2.DateType()
        result802 = _t1509
        self.record_span(span_start801, "DateType")
        return result802

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start803 = self.span_start()
        self.consume_literal("DATETIME")
        _t1510 = logic_pb2.DateTimeType()
        result804 = _t1510
        self.record_span(span_start803, "DateTimeType")
        return result804

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start805 = self.span_start()
        self.consume_literal("MISSING")
        _t1511 = logic_pb2.MissingType()
        result806 = _t1511
        self.record_span(span_start805, "MissingType")
        return result806

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start809 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int807 = self.consume_terminal("INT")
        int_3808 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1512 = logic_pb2.DecimalType(precision=int(int807), scale=int(int_3808))
        result810 = _t1512
        self.record_span(span_start809, "DecimalType")
        return result810

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start811 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1513 = logic_pb2.BooleanType()
        result812 = _t1513
        self.record_span(span_start811, "BooleanType")
        return result812

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start813 = self.span_start()
        self.consume_literal("INT32")
        _t1514 = logic_pb2.Int32Type()
        result814 = _t1514
        self.record_span(span_start813, "Int32Type")
        return result814

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start815 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1515 = logic_pb2.Float32Type()
        result816 = _t1515
        self.record_span(span_start815, "Float32Type")
        return result816

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start817 = self.span_start()
        self.consume_literal("UINT32")
        _t1516 = logic_pb2.UInt32Type()
        result818 = _t1516
        self.record_span(span_start817, "UInt32Type")
        return result818

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs819 = []
        cond820 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond820:
            _t1517 = self.parse_binding()
            item821 = _t1517
            xs819.append(item821)
            cond820 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings822 = xs819
        return bindings822

    def parse_formula(self) -> logic_pb2.Formula:
        span_start837 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1519 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1520 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1521 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1522 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1523 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1524 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1525 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1526 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1527 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1528 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1529 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1530 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1531 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1532 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1533 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1534 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1535 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1536 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1537 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1538 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1539 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1540 = 10
                                                                                                else:
                                                                                                    _t1540 = -1
                                                                                                _t1539 = _t1540
                                                                                            _t1538 = _t1539
                                                                                        _t1537 = _t1538
                                                                                    _t1536 = _t1537
                                                                                _t1535 = _t1536
                                                                            _t1534 = _t1535
                                                                        _t1533 = _t1534
                                                                    _t1532 = _t1533
                                                                _t1531 = _t1532
                                                            _t1530 = _t1531
                                                        _t1529 = _t1530
                                                    _t1528 = _t1529
                                                _t1527 = _t1528
                                            _t1526 = _t1527
                                        _t1525 = _t1526
                                    _t1524 = _t1525
                                _t1523 = _t1524
                            _t1522 = _t1523
                        _t1521 = _t1522
                    _t1520 = _t1521
                _t1519 = _t1520
            _t1518 = _t1519
        else:
            _t1518 = -1
        prediction823 = _t1518
        if prediction823 == 12:
            _t1542 = self.parse_cast()
            cast836 = _t1542
            _t1543 = logic_pb2.Formula(cast=cast836)
            _t1541 = _t1543
        else:
            if prediction823 == 11:
                _t1545 = self.parse_rel_atom()
                rel_atom835 = _t1545
                _t1546 = logic_pb2.Formula(rel_atom=rel_atom835)
                _t1544 = _t1546
            else:
                if prediction823 == 10:
                    _t1548 = self.parse_primitive()
                    primitive834 = _t1548
                    _t1549 = logic_pb2.Formula(primitive=primitive834)
                    _t1547 = _t1549
                else:
                    if prediction823 == 9:
                        _t1551 = self.parse_pragma()
                        pragma833 = _t1551
                        _t1552 = logic_pb2.Formula(pragma=pragma833)
                        _t1550 = _t1552
                    else:
                        if prediction823 == 8:
                            _t1554 = self.parse_atom()
                            atom832 = _t1554
                            _t1555 = logic_pb2.Formula(atom=atom832)
                            _t1553 = _t1555
                        else:
                            if prediction823 == 7:
                                _t1557 = self.parse_ffi()
                                ffi831 = _t1557
                                _t1558 = logic_pb2.Formula(ffi=ffi831)
                                _t1556 = _t1558
                            else:
                                if prediction823 == 6:
                                    _t1560 = self.parse_not()
                                    not830 = _t1560
                                    _t1561 = logic_pb2.Formula()
                                    getattr(_t1561, 'not').CopyFrom(not830)
                                    _t1559 = _t1561
                                else:
                                    if prediction823 == 5:
                                        _t1563 = self.parse_disjunction()
                                        disjunction829 = _t1563
                                        _t1564 = logic_pb2.Formula(disjunction=disjunction829)
                                        _t1562 = _t1564
                                    else:
                                        if prediction823 == 4:
                                            _t1566 = self.parse_conjunction()
                                            conjunction828 = _t1566
                                            _t1567 = logic_pb2.Formula(conjunction=conjunction828)
                                            _t1565 = _t1567
                                        else:
                                            if prediction823 == 3:
                                                _t1569 = self.parse_reduce()
                                                reduce827 = _t1569
                                                _t1570 = logic_pb2.Formula(reduce=reduce827)
                                                _t1568 = _t1570
                                            else:
                                                if prediction823 == 2:
                                                    _t1572 = self.parse_exists()
                                                    exists826 = _t1572
                                                    _t1573 = logic_pb2.Formula(exists=exists826)
                                                    _t1571 = _t1573
                                                else:
                                                    if prediction823 == 1:
                                                        _t1575 = self.parse_false()
                                                        false825 = _t1575
                                                        _t1576 = logic_pb2.Formula(disjunction=false825)
                                                        _t1574 = _t1576
                                                    else:
                                                        if prediction823 == 0:
                                                            _t1578 = self.parse_true()
                                                            true824 = _t1578
                                                            _t1579 = logic_pb2.Formula(conjunction=true824)
                                                            _t1577 = _t1579
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1574 = _t1577
                                                    _t1571 = _t1574
                                                _t1568 = _t1571
                                            _t1565 = _t1568
                                        _t1562 = _t1565
                                    _t1559 = _t1562
                                _t1556 = _t1559
                            _t1553 = _t1556
                        _t1550 = _t1553
                    _t1547 = _t1550
                _t1544 = _t1547
            _t1541 = _t1544
        result838 = _t1541
        self.record_span(span_start837, "Formula")
        return result838

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start839 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1580 = logic_pb2.Conjunction(args=[])
        result840 = _t1580
        self.record_span(span_start839, "Conjunction")
        return result840

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start841 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1581 = logic_pb2.Disjunction(args=[])
        result842 = _t1581
        self.record_span(span_start841, "Disjunction")
        return result842

    def parse_exists(self) -> logic_pb2.Exists:
        span_start845 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1582 = self.parse_bindings()
        bindings843 = _t1582
        _t1583 = self.parse_formula()
        formula844 = _t1583
        self.consume_literal(")")
        _t1584 = logic_pb2.Abstraction(vars=(list(bindings843[0]) + list(bindings843[1] if bindings843[1] is not None else [])), value=formula844)
        _t1585 = logic_pb2.Exists(body=_t1584)
        result846 = _t1585
        self.record_span(span_start845, "Exists")
        return result846

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start850 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1586 = self.parse_abstraction()
        abstraction847 = _t1586
        _t1587 = self.parse_abstraction()
        abstraction_3848 = _t1587
        _t1588 = self.parse_terms()
        terms849 = _t1588
        self.consume_literal(")")
        _t1589 = logic_pb2.Reduce(op=abstraction847, body=abstraction_3848, terms=terms849)
        result851 = _t1589
        self.record_span(span_start850, "Reduce")
        return result851

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs852 = []
        cond853 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond853:
            _t1590 = self.parse_term()
            item854 = _t1590
            xs852.append(item854)
            cond853 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms855 = xs852
        self.consume_literal(")")
        return terms855

    def parse_term(self) -> logic_pb2.Term:
        span_start859 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1591 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1592 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1593 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1594 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1595 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1596 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1597 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1598 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1599 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1600 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1601 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1602 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1603 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1604 = 1
                                                            else:
                                                                _t1604 = -1
                                                            _t1603 = _t1604
                                                        _t1602 = _t1603
                                                    _t1601 = _t1602
                                                _t1600 = _t1601
                                            _t1599 = _t1600
                                        _t1598 = _t1599
                                    _t1597 = _t1598
                                _t1596 = _t1597
                            _t1595 = _t1596
                        _t1594 = _t1595
                    _t1593 = _t1594
                _t1592 = _t1593
            _t1591 = _t1592
        prediction856 = _t1591
        if prediction856 == 1:
            _t1606 = self.parse_value()
            value858 = _t1606
            _t1607 = logic_pb2.Term(constant=value858)
            _t1605 = _t1607
        else:
            if prediction856 == 0:
                _t1609 = self.parse_var()
                var857 = _t1609
                _t1610 = logic_pb2.Term(var=var857)
                _t1608 = _t1610
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1605 = _t1608
        result860 = _t1605
        self.record_span(span_start859, "Term")
        return result860

    def parse_var(self) -> logic_pb2.Var:
        span_start862 = self.span_start()
        symbol861 = self.consume_terminal("SYMBOL")
        _t1611 = logic_pb2.Var(name=symbol861)
        result863 = _t1611
        self.record_span(span_start862, "Var")
        return result863

    def parse_value(self) -> logic_pb2.Value:
        span_start877 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1612 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1613 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1614 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1616 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1617 = 0
                            else:
                                _t1617 = -1
                            _t1616 = _t1617
                        _t1615 = _t1616
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1618 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1619 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1620 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1621 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1622 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1623 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1624 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1625 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1626 = 10
                                                        else:
                                                            _t1626 = -1
                                                        _t1625 = _t1626
                                                    _t1624 = _t1625
                                                _t1623 = _t1624
                                            _t1622 = _t1623
                                        _t1621 = _t1622
                                    _t1620 = _t1621
                                _t1619 = _t1620
                            _t1618 = _t1619
                        _t1615 = _t1618
                    _t1614 = _t1615
                _t1613 = _t1614
            _t1612 = _t1613
        prediction864 = _t1612
        if prediction864 == 12:
            _t1628 = self.parse_boolean_value()
            boolean_value876 = _t1628
            _t1629 = logic_pb2.Value(boolean_value=boolean_value876)
            _t1627 = _t1629
        else:
            if prediction864 == 11:
                self.consume_literal("missing")
                _t1631 = logic_pb2.MissingValue()
                _t1632 = logic_pb2.Value(missing_value=_t1631)
                _t1630 = _t1632
            else:
                if prediction864 == 10:
                    formatted_decimal875 = self.consume_terminal("DECIMAL")
                    _t1634 = logic_pb2.Value(decimal_value=formatted_decimal875)
                    _t1633 = _t1634
                else:
                    if prediction864 == 9:
                        formatted_int128874 = self.consume_terminal("INT128")
                        _t1636 = logic_pb2.Value(int128_value=formatted_int128874)
                        _t1635 = _t1636
                    else:
                        if prediction864 == 8:
                            formatted_uint128873 = self.consume_terminal("UINT128")
                            _t1638 = logic_pb2.Value(uint128_value=formatted_uint128873)
                            _t1637 = _t1638
                        else:
                            if prediction864 == 7:
                                formatted_uint32872 = self.consume_terminal("UINT32")
                                _t1640 = logic_pb2.Value(uint32_value=formatted_uint32872)
                                _t1639 = _t1640
                            else:
                                if prediction864 == 6:
                                    formatted_float871 = self.consume_terminal("FLOAT")
                                    _t1642 = logic_pb2.Value(float_value=formatted_float871)
                                    _t1641 = _t1642
                                else:
                                    if prediction864 == 5:
                                        formatted_float32870 = self.consume_terminal("FLOAT32")
                                        _t1644 = logic_pb2.Value(float32_value=formatted_float32870)
                                        _t1643 = _t1644
                                    else:
                                        if prediction864 == 4:
                                            formatted_int869 = self.consume_terminal("INT")
                                            _t1646 = logic_pb2.Value(int_value=formatted_int869)
                                            _t1645 = _t1646
                                        else:
                                            if prediction864 == 3:
                                                formatted_int32868 = self.consume_terminal("INT32")
                                                _t1648 = logic_pb2.Value(int32_value=formatted_int32868)
                                                _t1647 = _t1648
                                            else:
                                                if prediction864 == 2:
                                                    formatted_string867 = self.consume_terminal("STRING")
                                                    _t1650 = logic_pb2.Value(string_value=formatted_string867)
                                                    _t1649 = _t1650
                                                else:
                                                    if prediction864 == 1:
                                                        _t1652 = self.parse_datetime()
                                                        datetime866 = _t1652
                                                        _t1653 = logic_pb2.Value(datetime_value=datetime866)
                                                        _t1651 = _t1653
                                                    else:
                                                        if prediction864 == 0:
                                                            _t1655 = self.parse_date()
                                                            date865 = _t1655
                                                            _t1656 = logic_pb2.Value(date_value=date865)
                                                            _t1654 = _t1656
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1651 = _t1654
                                                    _t1649 = _t1651
                                                _t1647 = _t1649
                                            _t1645 = _t1647
                                        _t1643 = _t1645
                                    _t1641 = _t1643
                                _t1639 = _t1641
                            _t1637 = _t1639
                        _t1635 = _t1637
                    _t1633 = _t1635
                _t1630 = _t1633
            _t1627 = _t1630
        result878 = _t1627
        self.record_span(span_start877, "Value")
        return result878

    def parse_date(self) -> logic_pb2.DateValue:
        span_start882 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int879 = self.consume_terminal("INT")
        formatted_int_3880 = self.consume_terminal("INT")
        formatted_int_4881 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1657 = logic_pb2.DateValue(year=int(formatted_int879), month=int(formatted_int_3880), day=int(formatted_int_4881))
        result883 = _t1657
        self.record_span(span_start882, "DateValue")
        return result883

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start891 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int884 = self.consume_terminal("INT")
        formatted_int_3885 = self.consume_terminal("INT")
        formatted_int_4886 = self.consume_terminal("INT")
        formatted_int_5887 = self.consume_terminal("INT")
        formatted_int_6888 = self.consume_terminal("INT")
        formatted_int_7889 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1658 = self.consume_terminal("INT")
        else:
            _t1658 = None
        formatted_int_8890 = _t1658
        self.consume_literal(")")
        _t1659 = logic_pb2.DateTimeValue(year=int(formatted_int884), month=int(formatted_int_3885), day=int(formatted_int_4886), hour=int(formatted_int_5887), minute=int(formatted_int_6888), second=int(formatted_int_7889), microsecond=int((formatted_int_8890 if formatted_int_8890 is not None else 0)))
        result892 = _t1659
        self.record_span(span_start891, "DateTimeValue")
        return result892

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start897 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs893 = []
        cond894 = self.match_lookahead_literal("(", 0)
        while cond894:
            _t1660 = self.parse_formula()
            item895 = _t1660
            xs893.append(item895)
            cond894 = self.match_lookahead_literal("(", 0)
        formulas896 = xs893
        self.consume_literal(")")
        _t1661 = logic_pb2.Conjunction(args=formulas896)
        result898 = _t1661
        self.record_span(span_start897, "Conjunction")
        return result898

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start903 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs899 = []
        cond900 = self.match_lookahead_literal("(", 0)
        while cond900:
            _t1662 = self.parse_formula()
            item901 = _t1662
            xs899.append(item901)
            cond900 = self.match_lookahead_literal("(", 0)
        formulas902 = xs899
        self.consume_literal(")")
        _t1663 = logic_pb2.Disjunction(args=formulas902)
        result904 = _t1663
        self.record_span(span_start903, "Disjunction")
        return result904

    def parse_not(self) -> logic_pb2.Not:
        span_start906 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1664 = self.parse_formula()
        formula905 = _t1664
        self.consume_literal(")")
        _t1665 = logic_pb2.Not(arg=formula905)
        result907 = _t1665
        self.record_span(span_start906, "Not")
        return result907

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start911 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1666 = self.parse_name()
        name908 = _t1666
        _t1667 = self.parse_ffi_args()
        ffi_args909 = _t1667
        _t1668 = self.parse_terms()
        terms910 = _t1668
        self.consume_literal(")")
        _t1669 = logic_pb2.FFI(name=name908, args=ffi_args909, terms=terms910)
        result912 = _t1669
        self.record_span(span_start911, "FFI")
        return result912

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol913 = self.consume_terminal("SYMBOL")
        return symbol913

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs914 = []
        cond915 = self.match_lookahead_literal("(", 0)
        while cond915:
            _t1670 = self.parse_abstraction()
            item916 = _t1670
            xs914.append(item916)
            cond915 = self.match_lookahead_literal("(", 0)
        abstractions917 = xs914
        self.consume_literal(")")
        return abstractions917

    def parse_atom(self) -> logic_pb2.Atom:
        span_start923 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1671 = self.parse_relation_id()
        relation_id918 = _t1671
        xs919 = []
        cond920 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond920:
            _t1672 = self.parse_term()
            item921 = _t1672
            xs919.append(item921)
            cond920 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms922 = xs919
        self.consume_literal(")")
        _t1673 = logic_pb2.Atom(name=relation_id918, terms=terms922)
        result924 = _t1673
        self.record_span(span_start923, "Atom")
        return result924

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start930 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1674 = self.parse_name()
        name925 = _t1674
        xs926 = []
        cond927 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond927:
            _t1675 = self.parse_term()
            item928 = _t1675
            xs926.append(item928)
            cond927 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms929 = xs926
        self.consume_literal(")")
        _t1676 = logic_pb2.Pragma(name=name925, terms=terms929)
        result931 = _t1676
        self.record_span(span_start930, "Pragma")
        return result931

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start947 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1678 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1679 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1680 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1681 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1682 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1683 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1684 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1685 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1686 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1687 = 7
                                                else:
                                                    _t1687 = -1
                                                _t1686 = _t1687
                                            _t1685 = _t1686
                                        _t1684 = _t1685
                                    _t1683 = _t1684
                                _t1682 = _t1683
                            _t1681 = _t1682
                        _t1680 = _t1681
                    _t1679 = _t1680
                _t1678 = _t1679
            _t1677 = _t1678
        else:
            _t1677 = -1
        prediction932 = _t1677
        if prediction932 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1689 = self.parse_name()
            name942 = _t1689
            xs943 = []
            cond944 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond944:
                _t1690 = self.parse_rel_term()
                item945 = _t1690
                xs943.append(item945)
                cond944 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms946 = xs943
            self.consume_literal(")")
            _t1691 = logic_pb2.Primitive(name=name942, terms=rel_terms946)
            _t1688 = _t1691
        else:
            if prediction932 == 8:
                _t1693 = self.parse_divide()
                divide941 = _t1693
                _t1692 = divide941
            else:
                if prediction932 == 7:
                    _t1695 = self.parse_multiply()
                    multiply940 = _t1695
                    _t1694 = multiply940
                else:
                    if prediction932 == 6:
                        _t1697 = self.parse_minus()
                        minus939 = _t1697
                        _t1696 = minus939
                    else:
                        if prediction932 == 5:
                            _t1699 = self.parse_add()
                            add938 = _t1699
                            _t1698 = add938
                        else:
                            if prediction932 == 4:
                                _t1701 = self.parse_gt_eq()
                                gt_eq937 = _t1701
                                _t1700 = gt_eq937
                            else:
                                if prediction932 == 3:
                                    _t1703 = self.parse_gt()
                                    gt936 = _t1703
                                    _t1702 = gt936
                                else:
                                    if prediction932 == 2:
                                        _t1705 = self.parse_lt_eq()
                                        lt_eq935 = _t1705
                                        _t1704 = lt_eq935
                                    else:
                                        if prediction932 == 1:
                                            _t1707 = self.parse_lt()
                                            lt934 = _t1707
                                            _t1706 = lt934
                                        else:
                                            if prediction932 == 0:
                                                _t1709 = self.parse_eq()
                                                eq933 = _t1709
                                                _t1708 = eq933
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1706 = _t1708
                                        _t1704 = _t1706
                                    _t1702 = _t1704
                                _t1700 = _t1702
                            _t1698 = _t1700
                        _t1696 = _t1698
                    _t1694 = _t1696
                _t1692 = _t1694
            _t1688 = _t1692
        result948 = _t1688
        self.record_span(span_start947, "Primitive")
        return result948

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start951 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1710 = self.parse_term()
        term949 = _t1710
        _t1711 = self.parse_term()
        term_3950 = _t1711
        self.consume_literal(")")
        _t1712 = logic_pb2.RelTerm(term=term949)
        _t1713 = logic_pb2.RelTerm(term=term_3950)
        _t1714 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1712, _t1713])
        result952 = _t1714
        self.record_span(span_start951, "Primitive")
        return result952

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start955 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1715 = self.parse_term()
        term953 = _t1715
        _t1716 = self.parse_term()
        term_3954 = _t1716
        self.consume_literal(")")
        _t1717 = logic_pb2.RelTerm(term=term953)
        _t1718 = logic_pb2.RelTerm(term=term_3954)
        _t1719 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1717, _t1718])
        result956 = _t1719
        self.record_span(span_start955, "Primitive")
        return result956

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start959 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1720 = self.parse_term()
        term957 = _t1720
        _t1721 = self.parse_term()
        term_3958 = _t1721
        self.consume_literal(")")
        _t1722 = logic_pb2.RelTerm(term=term957)
        _t1723 = logic_pb2.RelTerm(term=term_3958)
        _t1724 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1722, _t1723])
        result960 = _t1724
        self.record_span(span_start959, "Primitive")
        return result960

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start963 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1725 = self.parse_term()
        term961 = _t1725
        _t1726 = self.parse_term()
        term_3962 = _t1726
        self.consume_literal(")")
        _t1727 = logic_pb2.RelTerm(term=term961)
        _t1728 = logic_pb2.RelTerm(term=term_3962)
        _t1729 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1727, _t1728])
        result964 = _t1729
        self.record_span(span_start963, "Primitive")
        return result964

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start967 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1730 = self.parse_term()
        term965 = _t1730
        _t1731 = self.parse_term()
        term_3966 = _t1731
        self.consume_literal(")")
        _t1732 = logic_pb2.RelTerm(term=term965)
        _t1733 = logic_pb2.RelTerm(term=term_3966)
        _t1734 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1732, _t1733])
        result968 = _t1734
        self.record_span(span_start967, "Primitive")
        return result968

    def parse_add(self) -> logic_pb2.Primitive:
        span_start972 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1735 = self.parse_term()
        term969 = _t1735
        _t1736 = self.parse_term()
        term_3970 = _t1736
        _t1737 = self.parse_term()
        term_4971 = _t1737
        self.consume_literal(")")
        _t1738 = logic_pb2.RelTerm(term=term969)
        _t1739 = logic_pb2.RelTerm(term=term_3970)
        _t1740 = logic_pb2.RelTerm(term=term_4971)
        _t1741 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1738, _t1739, _t1740])
        result973 = _t1741
        self.record_span(span_start972, "Primitive")
        return result973

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start977 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1742 = self.parse_term()
        term974 = _t1742
        _t1743 = self.parse_term()
        term_3975 = _t1743
        _t1744 = self.parse_term()
        term_4976 = _t1744
        self.consume_literal(")")
        _t1745 = logic_pb2.RelTerm(term=term974)
        _t1746 = logic_pb2.RelTerm(term=term_3975)
        _t1747 = logic_pb2.RelTerm(term=term_4976)
        _t1748 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1745, _t1746, _t1747])
        result978 = _t1748
        self.record_span(span_start977, "Primitive")
        return result978

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start982 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1749 = self.parse_term()
        term979 = _t1749
        _t1750 = self.parse_term()
        term_3980 = _t1750
        _t1751 = self.parse_term()
        term_4981 = _t1751
        self.consume_literal(")")
        _t1752 = logic_pb2.RelTerm(term=term979)
        _t1753 = logic_pb2.RelTerm(term=term_3980)
        _t1754 = logic_pb2.RelTerm(term=term_4981)
        _t1755 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1752, _t1753, _t1754])
        result983 = _t1755
        self.record_span(span_start982, "Primitive")
        return result983

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start987 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1756 = self.parse_term()
        term984 = _t1756
        _t1757 = self.parse_term()
        term_3985 = _t1757
        _t1758 = self.parse_term()
        term_4986 = _t1758
        self.consume_literal(")")
        _t1759 = logic_pb2.RelTerm(term=term984)
        _t1760 = logic_pb2.RelTerm(term=term_3985)
        _t1761 = logic_pb2.RelTerm(term=term_4986)
        _t1762 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1759, _t1760, _t1761])
        result988 = _t1762
        self.record_span(span_start987, "Primitive")
        return result988

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start992 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1763 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1764 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1765 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1766 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1767 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1768 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1769 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1770 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1771 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1772 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1773 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1774 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1775 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1776 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1777 = 1
                                                                else:
                                                                    _t1777 = -1
                                                                _t1776 = _t1777
                                                            _t1775 = _t1776
                                                        _t1774 = _t1775
                                                    _t1773 = _t1774
                                                _t1772 = _t1773
                                            _t1771 = _t1772
                                        _t1770 = _t1771
                                    _t1769 = _t1770
                                _t1768 = _t1769
                            _t1767 = _t1768
                        _t1766 = _t1767
                    _t1765 = _t1766
                _t1764 = _t1765
            _t1763 = _t1764
        prediction989 = _t1763
        if prediction989 == 1:
            _t1779 = self.parse_term()
            term991 = _t1779
            _t1780 = logic_pb2.RelTerm(term=term991)
            _t1778 = _t1780
        else:
            if prediction989 == 0:
                _t1782 = self.parse_specialized_value()
                specialized_value990 = _t1782
                _t1783 = logic_pb2.RelTerm(specialized_value=specialized_value990)
                _t1781 = _t1783
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1778 = _t1781
        result993 = _t1778
        self.record_span(span_start992, "RelTerm")
        return result993

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start995 = self.span_start()
        self.consume_literal("#")
        _t1784 = self.parse_raw_value()
        raw_value994 = _t1784
        result996 = raw_value994
        self.record_span(span_start995, "Value")
        return result996

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start1002 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1785 = self.parse_name()
        name997 = _t1785
        xs998 = []
        cond999 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond999:
            _t1786 = self.parse_rel_term()
            item1000 = _t1786
            xs998.append(item1000)
            cond999 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1001 = xs998
        self.consume_literal(")")
        _t1787 = logic_pb2.RelAtom(name=name997, terms=rel_terms1001)
        result1003 = _t1787
        self.record_span(span_start1002, "RelAtom")
        return result1003

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1006 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1788 = self.parse_term()
        term1004 = _t1788
        _t1789 = self.parse_term()
        term_31005 = _t1789
        self.consume_literal(")")
        _t1790 = logic_pb2.Cast(input=term1004, result=term_31005)
        result1007 = _t1790
        self.record_span(span_start1006, "Cast")
        return result1007

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1008 = []
        cond1009 = self.match_lookahead_literal("(", 0)
        while cond1009:
            _t1791 = self.parse_attribute()
            item1010 = _t1791
            xs1008.append(item1010)
            cond1009 = self.match_lookahead_literal("(", 0)
        attributes1011 = xs1008
        self.consume_literal(")")
        return attributes1011

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1017 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1792 = self.parse_name()
        name1012 = _t1792
        xs1013 = []
        cond1014 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1014:
            _t1793 = self.parse_raw_value()
            item1015 = _t1793
            xs1013.append(item1015)
            cond1014 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1016 = xs1013
        self.consume_literal(")")
        _t1794 = logic_pb2.Attribute(name=name1012, args=raw_values1016)
        result1018 = _t1794
        self.record_span(span_start1017, "Attribute")
        return result1018

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1024 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1019 = []
        cond1020 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1020:
            _t1795 = self.parse_relation_id()
            item1021 = _t1795
            xs1019.append(item1021)
            cond1020 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1022 = xs1019
        _t1796 = self.parse_script()
        script1023 = _t1796
        self.consume_literal(")")
        _t1797 = logic_pb2.Algorithm(body=script1023)
        getattr(_t1797, 'global').extend(relation_ids1022)
        result1025 = _t1797
        self.record_span(span_start1024, "Algorithm")
        return result1025

    def parse_script(self) -> logic_pb2.Script:
        span_start1030 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1026 = []
        cond1027 = self.match_lookahead_literal("(", 0)
        while cond1027:
            _t1798 = self.parse_construct()
            item1028 = _t1798
            xs1026.append(item1028)
            cond1027 = self.match_lookahead_literal("(", 0)
        constructs1029 = xs1026
        self.consume_literal(")")
        _t1799 = logic_pb2.Script(constructs=constructs1029)
        result1031 = _t1799
        self.record_span(span_start1030, "Script")
        return result1031

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1035 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1801 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1802 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1803 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1804 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1805 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1806 = 1
                                else:
                                    _t1806 = -1
                                _t1805 = _t1806
                            _t1804 = _t1805
                        _t1803 = _t1804
                    _t1802 = _t1803
                _t1801 = _t1802
            _t1800 = _t1801
        else:
            _t1800 = -1
        prediction1032 = _t1800
        if prediction1032 == 1:
            _t1808 = self.parse_instruction()
            instruction1034 = _t1808
            _t1809 = logic_pb2.Construct(instruction=instruction1034)
            _t1807 = _t1809
        else:
            if prediction1032 == 0:
                _t1811 = self.parse_loop()
                loop1033 = _t1811
                _t1812 = logic_pb2.Construct(loop=loop1033)
                _t1810 = _t1812
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1807 = _t1810
        result1036 = _t1807
        self.record_span(span_start1035, "Construct")
        return result1036

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1039 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1813 = self.parse_init()
        init1037 = _t1813
        _t1814 = self.parse_script()
        script1038 = _t1814
        self.consume_literal(")")
        _t1815 = logic_pb2.Loop(init=init1037, body=script1038)
        result1040 = _t1815
        self.record_span(span_start1039, "Loop")
        return result1040

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1041 = []
        cond1042 = self.match_lookahead_literal("(", 0)
        while cond1042:
            _t1816 = self.parse_instruction()
            item1043 = _t1816
            xs1041.append(item1043)
            cond1042 = self.match_lookahead_literal("(", 0)
        instructions1044 = xs1041
        self.consume_literal(")")
        return instructions1044

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1051 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1818 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1819 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1820 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1821 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1822 = 0
                            else:
                                _t1822 = -1
                            _t1821 = _t1822
                        _t1820 = _t1821
                    _t1819 = _t1820
                _t1818 = _t1819
            _t1817 = _t1818
        else:
            _t1817 = -1
        prediction1045 = _t1817
        if prediction1045 == 4:
            _t1824 = self.parse_monus_def()
            monus_def1050 = _t1824
            _t1825 = logic_pb2.Instruction(monus_def=monus_def1050)
            _t1823 = _t1825
        else:
            if prediction1045 == 3:
                _t1827 = self.parse_monoid_def()
                monoid_def1049 = _t1827
                _t1828 = logic_pb2.Instruction(monoid_def=monoid_def1049)
                _t1826 = _t1828
            else:
                if prediction1045 == 2:
                    _t1830 = self.parse_break()
                    break1048 = _t1830
                    _t1831 = logic_pb2.Instruction()
                    getattr(_t1831, 'break').CopyFrom(break1048)
                    _t1829 = _t1831
                else:
                    if prediction1045 == 1:
                        _t1833 = self.parse_upsert()
                        upsert1047 = _t1833
                        _t1834 = logic_pb2.Instruction(upsert=upsert1047)
                        _t1832 = _t1834
                    else:
                        if prediction1045 == 0:
                            _t1836 = self.parse_assign()
                            assign1046 = _t1836
                            _t1837 = logic_pb2.Instruction(assign=assign1046)
                            _t1835 = _t1837
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1832 = _t1835
                    _t1829 = _t1832
                _t1826 = _t1829
            _t1823 = _t1826
        result1052 = _t1823
        self.record_span(span_start1051, "Instruction")
        return result1052

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1056 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1838 = self.parse_relation_id()
        relation_id1053 = _t1838
        _t1839 = self.parse_abstraction()
        abstraction1054 = _t1839
        if self.match_lookahead_literal("(", 0):
            _t1841 = self.parse_attrs()
            _t1840 = _t1841
        else:
            _t1840 = None
        attrs1055 = _t1840
        self.consume_literal(")")
        _t1842 = logic_pb2.Assign(name=relation_id1053, body=abstraction1054, attrs=(attrs1055 if attrs1055 is not None else []))
        result1057 = _t1842
        self.record_span(span_start1056, "Assign")
        return result1057

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1061 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1843 = self.parse_relation_id()
        relation_id1058 = _t1843
        _t1844 = self.parse_abstraction_with_arity()
        abstraction_with_arity1059 = _t1844
        if self.match_lookahead_literal("(", 0):
            _t1846 = self.parse_attrs()
            _t1845 = _t1846
        else:
            _t1845 = None
        attrs1060 = _t1845
        self.consume_literal(")")
        _t1847 = logic_pb2.Upsert(name=relation_id1058, body=abstraction_with_arity1059[0], attrs=(attrs1060 if attrs1060 is not None else []), value_arity=abstraction_with_arity1059[1])
        result1062 = _t1847
        self.record_span(span_start1061, "Upsert")
        return result1062

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1848 = self.parse_bindings()
        bindings1063 = _t1848
        _t1849 = self.parse_formula()
        formula1064 = _t1849
        self.consume_literal(")")
        _t1850 = logic_pb2.Abstraction(vars=(list(bindings1063[0]) + list(bindings1063[1] if bindings1063[1] is not None else [])), value=formula1064)
        return (_t1850, len(bindings1063[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1068 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1851 = self.parse_relation_id()
        relation_id1065 = _t1851
        _t1852 = self.parse_abstraction()
        abstraction1066 = _t1852
        if self.match_lookahead_literal("(", 0):
            _t1854 = self.parse_attrs()
            _t1853 = _t1854
        else:
            _t1853 = None
        attrs1067 = _t1853
        self.consume_literal(")")
        _t1855 = logic_pb2.Break(name=relation_id1065, body=abstraction1066, attrs=(attrs1067 if attrs1067 is not None else []))
        result1069 = _t1855
        self.record_span(span_start1068, "Break")
        return result1069

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1074 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1856 = self.parse_monoid()
        monoid1070 = _t1856
        _t1857 = self.parse_relation_id()
        relation_id1071 = _t1857
        _t1858 = self.parse_abstraction_with_arity()
        abstraction_with_arity1072 = _t1858
        if self.match_lookahead_literal("(", 0):
            _t1860 = self.parse_attrs()
            _t1859 = _t1860
        else:
            _t1859 = None
        attrs1073 = _t1859
        self.consume_literal(")")
        _t1861 = logic_pb2.MonoidDef(monoid=monoid1070, name=relation_id1071, body=abstraction_with_arity1072[0], attrs=(attrs1073 if attrs1073 is not None else []), value_arity=abstraction_with_arity1072[1])
        result1075 = _t1861
        self.record_span(span_start1074, "MonoidDef")
        return result1075

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1081 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1863 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1864 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1865 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1866 = 2
                        else:
                            _t1866 = -1
                        _t1865 = _t1866
                    _t1864 = _t1865
                _t1863 = _t1864
            _t1862 = _t1863
        else:
            _t1862 = -1
        prediction1076 = _t1862
        if prediction1076 == 3:
            _t1868 = self.parse_sum_monoid()
            sum_monoid1080 = _t1868
            _t1869 = logic_pb2.Monoid(sum_monoid=sum_monoid1080)
            _t1867 = _t1869
        else:
            if prediction1076 == 2:
                _t1871 = self.parse_max_monoid()
                max_monoid1079 = _t1871
                _t1872 = logic_pb2.Monoid(max_monoid=max_monoid1079)
                _t1870 = _t1872
            else:
                if prediction1076 == 1:
                    _t1874 = self.parse_min_monoid()
                    min_monoid1078 = _t1874
                    _t1875 = logic_pb2.Monoid(min_monoid=min_monoid1078)
                    _t1873 = _t1875
                else:
                    if prediction1076 == 0:
                        _t1877 = self.parse_or_monoid()
                        or_monoid1077 = _t1877
                        _t1878 = logic_pb2.Monoid(or_monoid=or_monoid1077)
                        _t1876 = _t1878
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1873 = _t1876
                _t1870 = _t1873
            _t1867 = _t1870
        result1082 = _t1867
        self.record_span(span_start1081, "Monoid")
        return result1082

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1083 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1879 = logic_pb2.OrMonoid()
        result1084 = _t1879
        self.record_span(span_start1083, "OrMonoid")
        return result1084

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1086 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1880 = self.parse_type()
        type1085 = _t1880
        self.consume_literal(")")
        _t1881 = logic_pb2.MinMonoid(type=type1085)
        result1087 = _t1881
        self.record_span(span_start1086, "MinMonoid")
        return result1087

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1089 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1882 = self.parse_type()
        type1088 = _t1882
        self.consume_literal(")")
        _t1883 = logic_pb2.MaxMonoid(type=type1088)
        result1090 = _t1883
        self.record_span(span_start1089, "MaxMonoid")
        return result1090

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1092 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1884 = self.parse_type()
        type1091 = _t1884
        self.consume_literal(")")
        _t1885 = logic_pb2.SumMonoid(type=type1091)
        result1093 = _t1885
        self.record_span(span_start1092, "SumMonoid")
        return result1093

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1098 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1886 = self.parse_monoid()
        monoid1094 = _t1886
        _t1887 = self.parse_relation_id()
        relation_id1095 = _t1887
        _t1888 = self.parse_abstraction_with_arity()
        abstraction_with_arity1096 = _t1888
        if self.match_lookahead_literal("(", 0):
            _t1890 = self.parse_attrs()
            _t1889 = _t1890
        else:
            _t1889 = None
        attrs1097 = _t1889
        self.consume_literal(")")
        _t1891 = logic_pb2.MonusDef(monoid=monoid1094, name=relation_id1095, body=abstraction_with_arity1096[0], attrs=(attrs1097 if attrs1097 is not None else []), value_arity=abstraction_with_arity1096[1])
        result1099 = _t1891
        self.record_span(span_start1098, "MonusDef")
        return result1099

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1104 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1892 = self.parse_relation_id()
        relation_id1100 = _t1892
        _t1893 = self.parse_abstraction()
        abstraction1101 = _t1893
        _t1894 = self.parse_functional_dependency_keys()
        functional_dependency_keys1102 = _t1894
        _t1895 = self.parse_functional_dependency_values()
        functional_dependency_values1103 = _t1895
        self.consume_literal(")")
        _t1896 = logic_pb2.FunctionalDependency(guard=abstraction1101, keys=functional_dependency_keys1102, values=functional_dependency_values1103)
        _t1897 = logic_pb2.Constraint(name=relation_id1100, functional_dependency=_t1896)
        result1105 = _t1897
        self.record_span(span_start1104, "Constraint")
        return result1105

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1106 = []
        cond1107 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1107:
            _t1898 = self.parse_var()
            item1108 = _t1898
            xs1106.append(item1108)
            cond1107 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1109 = xs1106
        self.consume_literal(")")
        return vars1109

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1110 = []
        cond1111 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1111:
            _t1899 = self.parse_var()
            item1112 = _t1899
            xs1110.append(item1112)
            cond1111 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1113 = xs1110
        self.consume_literal(")")
        return vars1113

    def parse_data(self) -> logic_pb2.Data:
        span_start1119 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1901 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1902 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t1903 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t1904 = 1
                        else:
                            _t1904 = -1
                        _t1903 = _t1904
                    _t1902 = _t1903
                _t1901 = _t1902
            _t1900 = _t1901
        else:
            _t1900 = -1
        prediction1114 = _t1900
        if prediction1114 == 3:
            _t1906 = self.parse_iceberg_data()
            iceberg_data1118 = _t1906
            _t1907 = logic_pb2.Data(iceberg_data=iceberg_data1118)
            _t1905 = _t1907
        else:
            if prediction1114 == 2:
                _t1909 = self.parse_csv_data()
                csv_data1117 = _t1909
                _t1910 = logic_pb2.Data(csv_data=csv_data1117)
                _t1908 = _t1910
            else:
                if prediction1114 == 1:
                    _t1912 = self.parse_betree_relation()
                    betree_relation1116 = _t1912
                    _t1913 = logic_pb2.Data(betree_relation=betree_relation1116)
                    _t1911 = _t1913
                else:
                    if prediction1114 == 0:
                        _t1915 = self.parse_edb()
                        edb1115 = _t1915
                        _t1916 = logic_pb2.Data(edb=edb1115)
                        _t1914 = _t1916
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1911 = _t1914
                _t1908 = _t1911
            _t1905 = _t1908
        result1120 = _t1905
        self.record_span(span_start1119, "Data")
        return result1120

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1124 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1917 = self.parse_relation_id()
        relation_id1121 = _t1917
        _t1918 = self.parse_edb_path()
        edb_path1122 = _t1918
        _t1919 = self.parse_edb_types()
        edb_types1123 = _t1919
        self.consume_literal(")")
        _t1920 = logic_pb2.EDB(target_id=relation_id1121, path=edb_path1122, types=edb_types1123)
        result1125 = _t1920
        self.record_span(span_start1124, "EDB")
        return result1125

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1126 = []
        cond1127 = self.match_lookahead_terminal("STRING", 0)
        while cond1127:
            item1128 = self.consume_terminal("STRING")
            xs1126.append(item1128)
            cond1127 = self.match_lookahead_terminal("STRING", 0)
        strings1129 = xs1126
        self.consume_literal("]")
        return strings1129

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1130 = []
        cond1131 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1131:
            _t1921 = self.parse_type()
            item1132 = _t1921
            xs1130.append(item1132)
            cond1131 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1133 = xs1130
        self.consume_literal("]")
        return types1133

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1136 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1922 = self.parse_relation_id()
        relation_id1134 = _t1922
        _t1923 = self.parse_betree_info()
        betree_info1135 = _t1923
        self.consume_literal(")")
        _t1924 = logic_pb2.BeTreeRelation(name=relation_id1134, relation_info=betree_info1135)
        result1137 = _t1924
        self.record_span(span_start1136, "BeTreeRelation")
        return result1137

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1141 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1925 = self.parse_betree_info_key_types()
        betree_info_key_types1138 = _t1925
        _t1926 = self.parse_betree_info_value_types()
        betree_info_value_types1139 = _t1926
        _t1927 = self.parse_config_dict()
        config_dict1140 = _t1927
        self.consume_literal(")")
        _t1928 = self.construct_betree_info(betree_info_key_types1138, betree_info_value_types1139, config_dict1140)
        result1142 = _t1928
        self.record_span(span_start1141, "BeTreeInfo")
        return result1142

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1143 = []
        cond1144 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1144:
            _t1929 = self.parse_type()
            item1145 = _t1929
            xs1143.append(item1145)
            cond1144 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1146 = xs1143
        self.consume_literal(")")
        return types1146

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1147 = []
        cond1148 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1148:
            _t1930 = self.parse_type()
            item1149 = _t1930
            xs1147.append(item1149)
            cond1148 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1150 = xs1147
        self.consume_literal(")")
        return types1150

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1155 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1931 = self.parse_csvlocator()
        csvlocator1151 = _t1931
        _t1932 = self.parse_csv_config()
        csv_config1152 = _t1932
        _t1933 = self.parse_gnf_columns()
        gnf_columns1153 = _t1933
        _t1934 = self.parse_csv_asof()
        csv_asof1154 = _t1934
        self.consume_literal(")")
        _t1935 = logic_pb2.CSVData(locator=csvlocator1151, config=csv_config1152, columns=gnf_columns1153, asof=csv_asof1154)
        result1156 = _t1935
        self.record_span(span_start1155, "CSVData")
        return result1156

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1159 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1937 = self.parse_csv_locator_paths()
            _t1936 = _t1937
        else:
            _t1936 = None
        csv_locator_paths1157 = _t1936
        if self.match_lookahead_literal("(", 0):
            _t1939 = self.parse_csv_locator_inline_data()
            _t1938 = _t1939
        else:
            _t1938 = None
        csv_locator_inline_data1158 = _t1938
        self.consume_literal(")")
        _t1940 = logic_pb2.CSVLocator(paths=(csv_locator_paths1157 if csv_locator_paths1157 is not None else []), inline_data=(csv_locator_inline_data1158 if csv_locator_inline_data1158 is not None else "").encode())
        result1160 = _t1940
        self.record_span(span_start1159, "CSVLocator")
        return result1160

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1161 = []
        cond1162 = self.match_lookahead_terminal("STRING", 0)
        while cond1162:
            item1163 = self.consume_terminal("STRING")
            xs1161.append(item1163)
            cond1162 = self.match_lookahead_terminal("STRING", 0)
        strings1164 = xs1161
        self.consume_literal(")")
        return strings1164

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1165 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1165

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1167 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1941 = self.parse_config_dict()
        config_dict1166 = _t1941
        self.consume_literal(")")
        _t1942 = self.construct_csv_config(config_dict1166)
        result1168 = _t1942
        self.record_span(span_start1167, "CSVConfig")
        return result1168

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1169 = []
        cond1170 = self.match_lookahead_literal("(", 0)
        while cond1170:
            _t1943 = self.parse_gnf_column()
            item1171 = _t1943
            xs1169.append(item1171)
            cond1170 = self.match_lookahead_literal("(", 0)
        gnf_columns1172 = xs1169
        self.consume_literal(")")
        return gnf_columns1172

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1179 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1944 = self.parse_gnf_column_path()
        gnf_column_path1173 = _t1944
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1946 = self.parse_relation_id()
            _t1945 = _t1946
        else:
            _t1945 = None
        relation_id1174 = _t1945
        self.consume_literal("[")
        xs1175 = []
        cond1176 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1176:
            _t1947 = self.parse_type()
            item1177 = _t1947
            xs1175.append(item1177)
            cond1176 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1178 = xs1175
        self.consume_literal("]")
        self.consume_literal(")")
        _t1948 = logic_pb2.GNFColumn(column_path=gnf_column_path1173, target_id=relation_id1174, types=types1178)
        result1180 = _t1948
        self.record_span(span_start1179, "GNFColumn")
        return result1180

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1949 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1950 = 0
            else:
                _t1950 = -1
            _t1949 = _t1950
        prediction1181 = _t1949
        if prediction1181 == 1:
            self.consume_literal("[")
            xs1183 = []
            cond1184 = self.match_lookahead_terminal("STRING", 0)
            while cond1184:
                item1185 = self.consume_terminal("STRING")
                xs1183.append(item1185)
                cond1184 = self.match_lookahead_terminal("STRING", 0)
            strings1186 = xs1183
            self.consume_literal("]")
            _t1951 = strings1186
        else:
            if prediction1181 == 0:
                string1182 = self.consume_terminal("STRING")
                _t1952 = [string1182]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1951 = _t1952
        return _t1951

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1187 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1187

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1192 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t1953 = self.parse_iceberg_locator()
        iceberg_locator1188 = _t1953
        _t1954 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1189 = _t1954
        _t1955 = self.parse_gnf_columns()
        gnf_columns1190 = _t1955
        _t1956 = self.parse_boolean_value()
        boolean_value1191 = _t1956
        self.consume_literal(")")
        _t1957 = logic_pb2.IcebergData(locator=iceberg_locator1188, config=iceberg_catalog_config1189, columns=gnf_columns1190, returns_delta=boolean_value1191)
        result1193 = _t1957
        self.record_span(span_start1192, "IcebergData")
        return result1193

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1202 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1194 = self.consume_terminal("STRING")
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1195 = []
        cond1196 = self.match_lookahead_terminal("STRING", 0)
        while cond1196:
            item1197 = self.consume_terminal("STRING")
            xs1195.append(item1197)
            cond1196 = self.match_lookahead_terminal("STRING", 0)
        strings1198 = xs1195
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string_121199 = self.consume_terminal("STRING")
        self.consume_literal(")")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("from_snapshot", 1)):
            _t1959 = self.parse_iceberg_from_snapshot()
            _t1958 = _t1959
        else:
            _t1958 = None
        iceberg_from_snapshot1200 = _t1958
        if self.match_lookahead_literal("(", 0):
            _t1961 = self.parse_iceberg_to_snapshot()
            _t1960 = _t1961
        else:
            _t1960 = None
        iceberg_to_snapshot1201 = _t1960
        self.consume_literal(")")
        _t1962 = self.construct_iceberg_locator(string1194, strings1198, string_121199, iceberg_from_snapshot1200, iceberg_to_snapshot1201)
        result1203 = _t1962
        self.record_span(span_start1202, "IcebergLocator")
        return result1203

    def parse_iceberg_from_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("from_snapshot")
        string1204 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1204

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1205 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1205

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1216 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1206 = self.consume_terminal("STRING")
        self.consume_literal(")")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t1964 = self.parse_iceberg_catalog_config_scope()
            _t1963 = _t1964
        else:
            _t1963 = None
        iceberg_catalog_config_scope1207 = _t1963
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1208 = []
        cond1209 = self.match_lookahead_literal("(", 0)
        while cond1209:
            _t1965 = self.parse_iceberg_property_entry()
            item1210 = _t1965
            xs1208.append(item1210)
            cond1209 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1211 = xs1208
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1212 = []
        cond1213 = self.match_lookahead_literal("(", 0)
        while cond1213:
            _t1966 = self.parse_iceberg_property_entry()
            item1214 = _t1966
            xs1212.append(item1214)
            cond1213 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys_131215 = xs1212
        self.consume_literal(")")
        self.consume_literal(")")
        _t1967 = self.construct_iceberg_catalog_config(string1206, iceberg_catalog_config_scope1207, iceberg_property_entrys1211, iceberg_property_entrys_131215)
        result1217 = _t1967
        self.record_span(span_start1216, "IcebergCatalogConfig")
        return result1217

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1218 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1218

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1219 = self.consume_terminal("STRING")
        string_31220 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1219, string_31220,)

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1222 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1968 = self.parse_fragment_id()
        fragment_id1221 = _t1968
        self.consume_literal(")")
        _t1969 = transactions_pb2.Undefine(fragment_id=fragment_id1221)
        result1223 = _t1969
        self.record_span(span_start1222, "Undefine")
        return result1223

    def parse_context(self) -> transactions_pb2.Context:
        span_start1228 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1224 = []
        cond1225 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1225:
            _t1970 = self.parse_relation_id()
            item1226 = _t1970
            xs1224.append(item1226)
            cond1225 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1227 = xs1224
        self.consume_literal(")")
        _t1971 = transactions_pb2.Context(relations=relation_ids1227)
        result1229 = _t1971
        self.record_span(span_start1228, "Context")
        return result1229

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1234 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        xs1230 = []
        cond1231 = self.match_lookahead_literal("[", 0)
        while cond1231:
            _t1972 = self.parse_snapshot_mapping()
            item1232 = _t1972
            xs1230.append(item1232)
            cond1231 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1233 = xs1230
        self.consume_literal(")")
        _t1973 = transactions_pb2.Snapshot(mappings=snapshot_mappings1233)
        result1235 = _t1973
        self.record_span(span_start1234, "Snapshot")
        return result1235

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1238 = self.span_start()
        _t1974 = self.parse_edb_path()
        edb_path1236 = _t1974
        _t1975 = self.parse_relation_id()
        relation_id1237 = _t1975
        _t1976 = transactions_pb2.SnapshotMapping(destination_path=edb_path1236, source_relation=relation_id1237)
        result1239 = _t1976
        self.record_span(span_start1238, "SnapshotMapping")
        return result1239

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1240 = []
        cond1241 = self.match_lookahead_literal("(", 0)
        while cond1241:
            _t1977 = self.parse_read()
            item1242 = _t1977
            xs1240.append(item1242)
            cond1241 = self.match_lookahead_literal("(", 0)
        reads1243 = xs1240
        self.consume_literal(")")
        return reads1243

    def parse_read(self) -> transactions_pb2.Read:
        span_start1250 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1979 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1980 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t1981 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t1982 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t1983 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t1984 = 3
                                else:
                                    _t1984 = -1
                                _t1983 = _t1984
                            _t1982 = _t1983
                        _t1981 = _t1982
                    _t1980 = _t1981
                _t1979 = _t1980
            _t1978 = _t1979
        else:
            _t1978 = -1
        prediction1244 = _t1978
        if prediction1244 == 4:
            _t1986 = self.parse_export()
            export1249 = _t1986
            _t1987 = transactions_pb2.Read(export=export1249)
            _t1985 = _t1987
        else:
            if prediction1244 == 3:
                _t1989 = self.parse_abort()
                abort1248 = _t1989
                _t1990 = transactions_pb2.Read(abort=abort1248)
                _t1988 = _t1990
            else:
                if prediction1244 == 2:
                    _t1992 = self.parse_what_if()
                    what_if1247 = _t1992
                    _t1993 = transactions_pb2.Read(what_if=what_if1247)
                    _t1991 = _t1993
                else:
                    if prediction1244 == 1:
                        _t1995 = self.parse_output()
                        output1246 = _t1995
                        _t1996 = transactions_pb2.Read(output=output1246)
                        _t1994 = _t1996
                    else:
                        if prediction1244 == 0:
                            _t1998 = self.parse_demand()
                            demand1245 = _t1998
                            _t1999 = transactions_pb2.Read(demand=demand1245)
                            _t1997 = _t1999
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1994 = _t1997
                    _t1991 = _t1994
                _t1988 = _t1991
            _t1985 = _t1988
        result1251 = _t1985
        self.record_span(span_start1250, "Read")
        return result1251

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1253 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t2000 = self.parse_relation_id()
        relation_id1252 = _t2000
        self.consume_literal(")")
        _t2001 = transactions_pb2.Demand(relation_id=relation_id1252)
        result1254 = _t2001
        self.record_span(span_start1253, "Demand")
        return result1254

    def parse_output(self) -> transactions_pb2.Output:
        span_start1257 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2002 = self.parse_name()
        name1255 = _t2002
        _t2003 = self.parse_relation_id()
        relation_id1256 = _t2003
        self.consume_literal(")")
        _t2004 = transactions_pb2.Output(name=name1255, relation_id=relation_id1256)
        result1258 = _t2004
        self.record_span(span_start1257, "Output")
        return result1258

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1261 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2005 = self.parse_name()
        name1259 = _t2005
        _t2006 = self.parse_epoch()
        epoch1260 = _t2006
        self.consume_literal(")")
        _t2007 = transactions_pb2.WhatIf(branch=name1259, epoch=epoch1260)
        result1262 = _t2007
        self.record_span(span_start1261, "WhatIf")
        return result1262

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1265 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2009 = self.parse_name()
            _t2008 = _t2009
        else:
            _t2008 = None
        name1263 = _t2008
        _t2010 = self.parse_relation_id()
        relation_id1264 = _t2010
        self.consume_literal(")")
        _t2011 = transactions_pb2.Abort(name=(name1263 if name1263 is not None else "abort"), relation_id=relation_id1264)
        result1266 = _t2011
        self.record_span(span_start1265, "Abort")
        return result1266

    def parse_export(self) -> transactions_pb2.Export:
        span_start1270 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2013 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2014 = 0
                else:
                    _t2014 = -1
                _t2013 = _t2014
            _t2012 = _t2013
        else:
            _t2012 = -1
        prediction1267 = _t2012
        if prediction1267 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2016 = self.parse_export_iceberg_config()
            export_iceberg_config1269 = _t2016
            self.consume_literal(")")
            _t2017 = transactions_pb2.Export(iceberg_config=export_iceberg_config1269)
            _t2015 = _t2017
        else:
            if prediction1267 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2019 = self.parse_export_csv_config()
                export_csv_config1268 = _t2019
                self.consume_literal(")")
                _t2020 = transactions_pb2.Export(csv_config=export_csv_config1268)
                _t2018 = _t2020
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2015 = _t2018
        result1271 = _t2015
        self.record_span(span_start1270, "Export")
        return result1271

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1279 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2022 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2023 = 1
                else:
                    _t2023 = -1
                _t2022 = _t2023
            _t2021 = _t2022
        else:
            _t2021 = -1
        prediction1272 = _t2021
        if prediction1272 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2025 = self.parse_export_csv_path()
            export_csv_path1276 = _t2025
            _t2026 = self.parse_export_csv_columns_list()
            export_csv_columns_list1277 = _t2026
            _t2027 = self.parse_config_dict()
            config_dict1278 = _t2027
            self.consume_literal(")")
            _t2028 = self.construct_export_csv_config(export_csv_path1276, export_csv_columns_list1277, config_dict1278)
            _t2024 = _t2028
        else:
            if prediction1272 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2030 = self.parse_export_csv_path()
                export_csv_path1273 = _t2030
                _t2031 = self.parse_export_csv_source()
                export_csv_source1274 = _t2031
                _t2032 = self.parse_csv_config()
                csv_config1275 = _t2032
                self.consume_literal(")")
                _t2033 = self.construct_export_csv_config_with_source(export_csv_path1273, export_csv_source1274, csv_config1275)
                _t2029 = _t2033
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2024 = _t2029
        result1280 = _t2024
        self.record_span(span_start1279, "ExportCSVConfig")
        return result1280

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1281 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1281

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1288 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2035 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2036 = 0
                else:
                    _t2036 = -1
                _t2035 = _t2036
            _t2034 = _t2035
        else:
            _t2034 = -1
        prediction1282 = _t2034
        if prediction1282 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2038 = self.parse_relation_id()
            relation_id1287 = _t2038
            self.consume_literal(")")
            _t2039 = transactions_pb2.ExportCSVSource(table_def=relation_id1287)
            _t2037 = _t2039
        else:
            if prediction1282 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1283 = []
                cond1284 = self.match_lookahead_literal("(", 0)
                while cond1284:
                    _t2041 = self.parse_export_csv_column()
                    item1285 = _t2041
                    xs1283.append(item1285)
                    cond1284 = self.match_lookahead_literal("(", 0)
                export_csv_columns1286 = xs1283
                self.consume_literal(")")
                _t2042 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1286)
                _t2043 = transactions_pb2.ExportCSVSource(gnf_columns=_t2042)
                _t2040 = _t2043
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2037 = _t2040
        result1289 = _t2037
        self.record_span(span_start1288, "ExportCSVSource")
        return result1289

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1292 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1290 = self.consume_terminal("STRING")
        _t2044 = self.parse_relation_id()
        relation_id1291 = _t2044
        self.consume_literal(")")
        _t2045 = transactions_pb2.ExportCSVColumn(column_name=string1290, column_data=relation_id1291)
        result1293 = _t2045
        self.record_span(span_start1292, "ExportCSVColumn")
        return result1293

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1294 = []
        cond1295 = self.match_lookahead_literal("(", 0)
        while cond1295:
            _t2046 = self.parse_export_csv_column()
            item1296 = _t2046
            xs1294.append(item1296)
            cond1295 = self.match_lookahead_literal("(", 0)
        export_csv_columns1297 = xs1294
        self.consume_literal(")")
        return export_csv_columns1297

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1310 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2047 = self.parse_iceberg_locator()
        iceberg_locator1298 = _t2047
        _t2048 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1299 = _t2048
        self.consume_literal("(")
        self.consume_literal("table_def")
        _t2049 = self.parse_relation_id()
        relation_id1300 = _t2049
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1301 = []
        cond1302 = self.match_lookahead_literal("(", 0)
        while cond1302:
            _t2050 = self.parse_export_gnf_column()
            item1303 = _t2050
            xs1301.append(item1303)
            cond1302 = self.match_lookahead_literal("(", 0)
        export_gnf_columns1304 = xs1301
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("table_properties")
        xs1305 = []
        cond1306 = self.match_lookahead_literal("(", 0)
        while cond1306:
            _t2051 = self.parse_iceberg_property_entry()
            item1307 = _t2051
            xs1305.append(item1307)
            cond1306 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1308 = xs1305
        self.consume_literal(")")
        if self.match_lookahead_literal("{", 0):
            _t2053 = self.parse_config_dict()
            _t2052 = _t2053
        else:
            _t2052 = None
        config_dict1309 = _t2052
        self.consume_literal(")")
        _t2054 = self.construct_export_iceberg_config_full(iceberg_locator1298, iceberg_catalog_config1299, relation_id1300, export_gnf_columns1304, iceberg_property_entrys1308, config_dict1309)
        result1311 = _t2054
        self.record_span(span_start1310, "ExportIcebergConfig")
        return result1311

    def parse_export_gnf_column(self) -> transactions_pb2.ExportGNFColumn:
        span_start1314 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("gnf_column")
        string1312 = self.consume_terminal("STRING")
        _t2055 = self.parse_boolean_value()
        boolean_value1313 = _t2055
        self.consume_literal(")")
        _t2056 = transactions_pb2.ExportGNFColumn(name=string1312, nullable=boolean_value1313)
        result1315 = _t2056
        self.record_span(span_start1314, "ExportGNFColumn")
        return result1315


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
