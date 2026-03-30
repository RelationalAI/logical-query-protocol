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
            _t2061 = value.HasField("int32_value")
        else:
            _t2061 = False
        if _t2061:
            assert value is not None
            return value.int32_value
        else:
            _t2062 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2063 = value.HasField("int_value")
        else:
            _t2063 = False
        if _t2063:
            assert value is not None
            return value.int_value
        else:
            _t2064 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2065 = value.HasField("string_value")
        else:
            _t2065 = False
        if _t2065:
            assert value is not None
            return value.string_value
        else:
            _t2066 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2067 = value.HasField("boolean_value")
        else:
            _t2067 = False
        if _t2067:
            assert value is not None
            return value.boolean_value
        else:
            _t2068 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2069 = value.HasField("string_value")
        else:
            _t2069 = False
        if _t2069:
            assert value is not None
            return [value.string_value]
        else:
            _t2070 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t2071 = value.HasField("int_value")
        else:
            _t2071 = False
        if _t2071:
            assert value is not None
            return value.int_value
        else:
            _t2072 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2073 = value.HasField("float_value")
        else:
            _t2073 = False
        if _t2073:
            assert value is not None
            return value.float_value
        else:
            _t2074 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2075 = value.HasField("string_value")
        else:
            _t2075 = False
        if _t2075:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2076 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2077 = value.HasField("uint128_value")
        else:
            _t2077 = False
        if _t2077:
            assert value is not None
            return value.uint128_value
        else:
            _t2078 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2079 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2079
        _t2080 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2080
        _t2081 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2081
        _t2082 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2082
        _t2083 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2083
        _t2084 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2084
        _t2085 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2085
        _t2086 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2086
        _t2087 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2087
        _t2088 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2088
        _t2089 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t2089
        _t2090 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2090
        _t2091 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t2091

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2092 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2092
        _t2093 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2093
        _t2094 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2094
        _t2095 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2095
        _t2096 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2096
        _t2097 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2097
        _t2098 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2098
        _t2099 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2099
        _t2100 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2100
        _t2101 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2101
        _t2102 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2102

    def default_configure(self) -> transactions_pb2.Configure:
        _t2103 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2103
        _t2104 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2104

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
        _t2105 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2105
        _t2106 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2106
        _t2107 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t2107

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2108 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2108
        _t2109 = self._extract_value_string(config.get("compression"), "")
        compression = _t2109
        _t2110 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2110
        _t2111 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2111
        _t2112 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2112
        _t2113 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2113
        _t2114 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2114
        _t2115 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2115

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2116 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t2116

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2117 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2117

    def construct_iceberg_locator(self, table_name: str, namespace: Sequence[str], warehouse: str, from_snapshot_opt: str | None, to_snapshot_opt: str | None) -> logic_pb2.IcebergLocator:
        _t2118 = logic_pb2.IcebergLocator(table_name=table_name, namespace=namespace, warehouse=warehouse, from_snapshot=(from_snapshot_opt if from_snapshot_opt is not None else ""), to_snapshot=(to_snapshot_opt if to_snapshot_opt is not None else ""))
        return _t2118

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, table_def: logic_pb2.RelationId, columns: Sequence[transactions_pb2.ExportGNFColumn], table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2119 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2119
        _t2120 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2120
        _t2121 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2121
        table_props = dict(table_property_pairs)
        _t2122 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, columns=columns, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2122

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start666 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1321 = self.parse_configure()
            _t1320 = _t1321
        else:
            _t1320 = None
        configure660 = _t1320
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1323 = self.parse_sync()
            _t1322 = _t1323
        else:
            _t1322 = None
        sync661 = _t1322
        xs662 = []
        cond663 = self.match_lookahead_literal("(", 0)
        while cond663:
            _t1324 = self.parse_epoch()
            item664 = _t1324
            xs662.append(item664)
            cond663 = self.match_lookahead_literal("(", 0)
        epochs665 = xs662
        self.consume_literal(")")
        _t1325 = self.default_configure()
        _t1326 = transactions_pb2.Transaction(epochs=epochs665, configure=(configure660 if configure660 is not None else _t1325), sync=sync661)
        result667 = _t1326
        self.record_span(span_start666, "Transaction")
        return result667

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start669 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1327 = self.parse_config_dict()
        config_dict668 = _t1327
        self.consume_literal(")")
        _t1328 = self.construct_configure(config_dict668)
        result670 = _t1328
        self.record_span(span_start669, "Configure")
        return result670

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs671 = []
        cond672 = self.match_lookahead_literal(":", 0)
        while cond672:
            _t1329 = self.parse_config_key_value()
            item673 = _t1329
            xs671.append(item673)
            cond672 = self.match_lookahead_literal(":", 0)
        config_key_values674 = xs671
        self.consume_literal("}")
        return config_key_values674

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol675 = self.consume_terminal("SYMBOL")
        _t1330 = self.parse_raw_value()
        raw_value676 = _t1330
        return (symbol675, raw_value676,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start690 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1331 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1332 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1333 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1335 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1336 = 0
                            else:
                                _t1336 = -1
                            _t1335 = _t1336
                        _t1334 = _t1335
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1337 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1338 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1339 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1340 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1341 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1342 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1343 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1344 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1345 = 10
                                                        else:
                                                            _t1345 = -1
                                                        _t1344 = _t1345
                                                    _t1343 = _t1344
                                                _t1342 = _t1343
                                            _t1341 = _t1342
                                        _t1340 = _t1341
                                    _t1339 = _t1340
                                _t1338 = _t1339
                            _t1337 = _t1338
                        _t1334 = _t1337
                    _t1333 = _t1334
                _t1332 = _t1333
            _t1331 = _t1332
        prediction677 = _t1331
        if prediction677 == 12:
            _t1347 = self.parse_boolean_value()
            boolean_value689 = _t1347
            _t1348 = logic_pb2.Value(boolean_value=boolean_value689)
            _t1346 = _t1348
        else:
            if prediction677 == 11:
                self.consume_literal("missing")
                _t1350 = logic_pb2.MissingValue()
                _t1351 = logic_pb2.Value(missing_value=_t1350)
                _t1349 = _t1351
            else:
                if prediction677 == 10:
                    decimal688 = self.consume_terminal("DECIMAL")
                    _t1353 = logic_pb2.Value(decimal_value=decimal688)
                    _t1352 = _t1353
                else:
                    if prediction677 == 9:
                        int128687 = self.consume_terminal("INT128")
                        _t1355 = logic_pb2.Value(int128_value=int128687)
                        _t1354 = _t1355
                    else:
                        if prediction677 == 8:
                            uint128686 = self.consume_terminal("UINT128")
                            _t1357 = logic_pb2.Value(uint128_value=uint128686)
                            _t1356 = _t1357
                        else:
                            if prediction677 == 7:
                                uint32685 = self.consume_terminal("UINT32")
                                _t1359 = logic_pb2.Value(uint32_value=uint32685)
                                _t1358 = _t1359
                            else:
                                if prediction677 == 6:
                                    float684 = self.consume_terminal("FLOAT")
                                    _t1361 = logic_pb2.Value(float_value=float684)
                                    _t1360 = _t1361
                                else:
                                    if prediction677 == 5:
                                        float32683 = self.consume_terminal("FLOAT32")
                                        _t1363 = logic_pb2.Value(float32_value=float32683)
                                        _t1362 = _t1363
                                    else:
                                        if prediction677 == 4:
                                            int682 = self.consume_terminal("INT")
                                            _t1365 = logic_pb2.Value(int_value=int682)
                                            _t1364 = _t1365
                                        else:
                                            if prediction677 == 3:
                                                int32681 = self.consume_terminal("INT32")
                                                _t1367 = logic_pb2.Value(int32_value=int32681)
                                                _t1366 = _t1367
                                            else:
                                                if prediction677 == 2:
                                                    string680 = self.consume_terminal("STRING")
                                                    _t1369 = logic_pb2.Value(string_value=string680)
                                                    _t1368 = _t1369
                                                else:
                                                    if prediction677 == 1:
                                                        _t1371 = self.parse_raw_datetime()
                                                        raw_datetime679 = _t1371
                                                        _t1372 = logic_pb2.Value(datetime_value=raw_datetime679)
                                                        _t1370 = _t1372
                                                    else:
                                                        if prediction677 == 0:
                                                            _t1374 = self.parse_raw_date()
                                                            raw_date678 = _t1374
                                                            _t1375 = logic_pb2.Value(date_value=raw_date678)
                                                            _t1373 = _t1375
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1370 = _t1373
                                                    _t1368 = _t1370
                                                _t1366 = _t1368
                                            _t1364 = _t1366
                                        _t1362 = _t1364
                                    _t1360 = _t1362
                                _t1358 = _t1360
                            _t1356 = _t1358
                        _t1354 = _t1356
                    _t1352 = _t1354
                _t1349 = _t1352
            _t1346 = _t1349
        result691 = _t1346
        self.record_span(span_start690, "Value")
        return result691

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start695 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int692 = self.consume_terminal("INT")
        int_3693 = self.consume_terminal("INT")
        int_4694 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1376 = logic_pb2.DateValue(year=int(int692), month=int(int_3693), day=int(int_4694))
        result696 = _t1376
        self.record_span(span_start695, "DateValue")
        return result696

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start704 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int697 = self.consume_terminal("INT")
        int_3698 = self.consume_terminal("INT")
        int_4699 = self.consume_terminal("INT")
        int_5700 = self.consume_terminal("INT")
        int_6701 = self.consume_terminal("INT")
        int_7702 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1377 = self.consume_terminal("INT")
        else:
            _t1377 = None
        int_8703 = _t1377
        self.consume_literal(")")
        _t1378 = logic_pb2.DateTimeValue(year=int(int697), month=int(int_3698), day=int(int_4699), hour=int(int_5700), minute=int(int_6701), second=int(int_7702), microsecond=int((int_8703 if int_8703 is not None else 0)))
        result705 = _t1378
        self.record_span(span_start704, "DateTimeValue")
        return result705

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1379 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1380 = 1
            else:
                _t1380 = -1
            _t1379 = _t1380
        prediction706 = _t1379
        if prediction706 == 1:
            self.consume_literal("false")
            _t1381 = False
        else:
            if prediction706 == 0:
                self.consume_literal("true")
                _t1382 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1381 = _t1382
        return _t1381

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start711 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs707 = []
        cond708 = self.match_lookahead_literal(":", 0)
        while cond708:
            _t1383 = self.parse_fragment_id()
            item709 = _t1383
            xs707.append(item709)
            cond708 = self.match_lookahead_literal(":", 0)
        fragment_ids710 = xs707
        self.consume_literal(")")
        _t1384 = transactions_pb2.Sync(fragments=fragment_ids710)
        result712 = _t1384
        self.record_span(span_start711, "Sync")
        return result712

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start714 = self.span_start()
        self.consume_literal(":")
        symbol713 = self.consume_terminal("SYMBOL")
        result715 = fragments_pb2.FragmentId(id=symbol713.encode())
        self.record_span(span_start714, "FragmentId")
        return result715

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start718 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1386 = self.parse_epoch_writes()
            _t1385 = _t1386
        else:
            _t1385 = None
        epoch_writes716 = _t1385
        if self.match_lookahead_literal("(", 0):
            _t1388 = self.parse_epoch_reads()
            _t1387 = _t1388
        else:
            _t1387 = None
        epoch_reads717 = _t1387
        self.consume_literal(")")
        _t1389 = transactions_pb2.Epoch(writes=(epoch_writes716 if epoch_writes716 is not None else []), reads=(epoch_reads717 if epoch_reads717 is not None else []))
        result719 = _t1389
        self.record_span(span_start718, "Epoch")
        return result719

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs720 = []
        cond721 = self.match_lookahead_literal("(", 0)
        while cond721:
            _t1390 = self.parse_write()
            item722 = _t1390
            xs720.append(item722)
            cond721 = self.match_lookahead_literal("(", 0)
        writes723 = xs720
        self.consume_literal(")")
        return writes723

    def parse_write(self) -> transactions_pb2.Write:
        span_start729 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1392 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1393 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1394 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1395 = 2
                        else:
                            _t1395 = -1
                        _t1394 = _t1395
                    _t1393 = _t1394
                _t1392 = _t1393
            _t1391 = _t1392
        else:
            _t1391 = -1
        prediction724 = _t1391
        if prediction724 == 3:
            _t1397 = self.parse_snapshot()
            snapshot728 = _t1397
            _t1398 = transactions_pb2.Write(snapshot=snapshot728)
            _t1396 = _t1398
        else:
            if prediction724 == 2:
                _t1400 = self.parse_context()
                context727 = _t1400
                _t1401 = transactions_pb2.Write(context=context727)
                _t1399 = _t1401
            else:
                if prediction724 == 1:
                    _t1403 = self.parse_undefine()
                    undefine726 = _t1403
                    _t1404 = transactions_pb2.Write(undefine=undefine726)
                    _t1402 = _t1404
                else:
                    if prediction724 == 0:
                        _t1406 = self.parse_define()
                        define725 = _t1406
                        _t1407 = transactions_pb2.Write(define=define725)
                        _t1405 = _t1407
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1402 = _t1405
                _t1399 = _t1402
            _t1396 = _t1399
        result730 = _t1396
        self.record_span(span_start729, "Write")
        return result730

    def parse_define(self) -> transactions_pb2.Define:
        span_start732 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1408 = self.parse_fragment()
        fragment731 = _t1408
        self.consume_literal(")")
        _t1409 = transactions_pb2.Define(fragment=fragment731)
        result733 = _t1409
        self.record_span(span_start732, "Define")
        return result733

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start739 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1410 = self.parse_new_fragment_id()
        new_fragment_id734 = _t1410
        xs735 = []
        cond736 = self.match_lookahead_literal("(", 0)
        while cond736:
            _t1411 = self.parse_declaration()
            item737 = _t1411
            xs735.append(item737)
            cond736 = self.match_lookahead_literal("(", 0)
        declarations738 = xs735
        self.consume_literal(")")
        result740 = self.construct_fragment(new_fragment_id734, declarations738)
        self.record_span(span_start739, "Fragment")
        return result740

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start742 = self.span_start()
        _t1412 = self.parse_fragment_id()
        fragment_id741 = _t1412
        self.start_fragment(fragment_id741)
        result743 = fragment_id741
        self.record_span(span_start742, "FragmentId")
        return result743

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start749 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1414 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1415 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1416 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1417 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1418 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1419 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1420 = 1
                                    else:
                                        _t1420 = -1
                                    _t1419 = _t1420
                                _t1418 = _t1419
                            _t1417 = _t1418
                        _t1416 = _t1417
                    _t1415 = _t1416
                _t1414 = _t1415
            _t1413 = _t1414
        else:
            _t1413 = -1
        prediction744 = _t1413
        if prediction744 == 3:
            _t1422 = self.parse_data()
            data748 = _t1422
            _t1423 = logic_pb2.Declaration(data=data748)
            _t1421 = _t1423
        else:
            if prediction744 == 2:
                _t1425 = self.parse_constraint()
                constraint747 = _t1425
                _t1426 = logic_pb2.Declaration(constraint=constraint747)
                _t1424 = _t1426
            else:
                if prediction744 == 1:
                    _t1428 = self.parse_algorithm()
                    algorithm746 = _t1428
                    _t1429 = logic_pb2.Declaration(algorithm=algorithm746)
                    _t1427 = _t1429
                else:
                    if prediction744 == 0:
                        _t1431 = self.parse_def()
                        def745 = _t1431
                        _t1432 = logic_pb2.Declaration()
                        getattr(_t1432, 'def').CopyFrom(def745)
                        _t1430 = _t1432
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1427 = _t1430
                _t1424 = _t1427
            _t1421 = _t1424
        result750 = _t1421
        self.record_span(span_start749, "Declaration")
        return result750

    def parse_def(self) -> logic_pb2.Def:
        span_start754 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1433 = self.parse_relation_id()
        relation_id751 = _t1433
        _t1434 = self.parse_abstraction()
        abstraction752 = _t1434
        if self.match_lookahead_literal("(", 0):
            _t1436 = self.parse_attrs()
            _t1435 = _t1436
        else:
            _t1435 = None
        attrs753 = _t1435
        self.consume_literal(")")
        _t1437 = logic_pb2.Def(name=relation_id751, body=abstraction752, attrs=(attrs753 if attrs753 is not None else []))
        result755 = _t1437
        self.record_span(span_start754, "Def")
        return result755

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start759 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1438 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1439 = 1
            else:
                _t1439 = -1
            _t1438 = _t1439
        prediction756 = _t1438
        if prediction756 == 1:
            uint128758 = self.consume_terminal("UINT128")
            _t1440 = logic_pb2.RelationId(id_low=uint128758.low, id_high=uint128758.high)
        else:
            if prediction756 == 0:
                self.consume_literal(":")
                symbol757 = self.consume_terminal("SYMBOL")
                _t1441 = self.relation_id_from_string(symbol757)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1440 = _t1441
        result760 = _t1440
        self.record_span(span_start759, "RelationId")
        return result760

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start763 = self.span_start()
        self.consume_literal("(")
        _t1442 = self.parse_bindings()
        bindings761 = _t1442
        _t1443 = self.parse_formula()
        formula762 = _t1443
        self.consume_literal(")")
        _t1444 = logic_pb2.Abstraction(vars=(list(bindings761[0]) + list(bindings761[1] if bindings761[1] is not None else [])), value=formula762)
        result764 = _t1444
        self.record_span(span_start763, "Abstraction")
        return result764

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs765 = []
        cond766 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond766:
            _t1445 = self.parse_binding()
            item767 = _t1445
            xs765.append(item767)
            cond766 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings768 = xs765
        if self.match_lookahead_literal("|", 0):
            _t1447 = self.parse_value_bindings()
            _t1446 = _t1447
        else:
            _t1446 = None
        value_bindings769 = _t1446
        self.consume_literal("]")
        return (bindings768, (value_bindings769 if value_bindings769 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start772 = self.span_start()
        symbol770 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1448 = self.parse_type()
        type771 = _t1448
        _t1449 = logic_pb2.Var(name=symbol770)
        _t1450 = logic_pb2.Binding(var=_t1449, type=type771)
        result773 = _t1450
        self.record_span(span_start772, "Binding")
        return result773

    def parse_type(self) -> logic_pb2.Type:
        span_start789 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1451 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1452 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1453 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1454 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1455 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1456 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1457 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1458 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1459 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1460 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1461 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1462 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1463 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1464 = 9
                                                            else:
                                                                _t1464 = -1
                                                            _t1463 = _t1464
                                                        _t1462 = _t1463
                                                    _t1461 = _t1462
                                                _t1460 = _t1461
                                            _t1459 = _t1460
                                        _t1458 = _t1459
                                    _t1457 = _t1458
                                _t1456 = _t1457
                            _t1455 = _t1456
                        _t1454 = _t1455
                    _t1453 = _t1454
                _t1452 = _t1453
            _t1451 = _t1452
        prediction774 = _t1451
        if prediction774 == 13:
            _t1466 = self.parse_uint32_type()
            uint32_type788 = _t1466
            _t1467 = logic_pb2.Type(uint32_type=uint32_type788)
            _t1465 = _t1467
        else:
            if prediction774 == 12:
                _t1469 = self.parse_float32_type()
                float32_type787 = _t1469
                _t1470 = logic_pb2.Type(float32_type=float32_type787)
                _t1468 = _t1470
            else:
                if prediction774 == 11:
                    _t1472 = self.parse_int32_type()
                    int32_type786 = _t1472
                    _t1473 = logic_pb2.Type(int32_type=int32_type786)
                    _t1471 = _t1473
                else:
                    if prediction774 == 10:
                        _t1475 = self.parse_boolean_type()
                        boolean_type785 = _t1475
                        _t1476 = logic_pb2.Type(boolean_type=boolean_type785)
                        _t1474 = _t1476
                    else:
                        if prediction774 == 9:
                            _t1478 = self.parse_decimal_type()
                            decimal_type784 = _t1478
                            _t1479 = logic_pb2.Type(decimal_type=decimal_type784)
                            _t1477 = _t1479
                        else:
                            if prediction774 == 8:
                                _t1481 = self.parse_missing_type()
                                missing_type783 = _t1481
                                _t1482 = logic_pb2.Type(missing_type=missing_type783)
                                _t1480 = _t1482
                            else:
                                if prediction774 == 7:
                                    _t1484 = self.parse_datetime_type()
                                    datetime_type782 = _t1484
                                    _t1485 = logic_pb2.Type(datetime_type=datetime_type782)
                                    _t1483 = _t1485
                                else:
                                    if prediction774 == 6:
                                        _t1487 = self.parse_date_type()
                                        date_type781 = _t1487
                                        _t1488 = logic_pb2.Type(date_type=date_type781)
                                        _t1486 = _t1488
                                    else:
                                        if prediction774 == 5:
                                            _t1490 = self.parse_int128_type()
                                            int128_type780 = _t1490
                                            _t1491 = logic_pb2.Type(int128_type=int128_type780)
                                            _t1489 = _t1491
                                        else:
                                            if prediction774 == 4:
                                                _t1493 = self.parse_uint128_type()
                                                uint128_type779 = _t1493
                                                _t1494 = logic_pb2.Type(uint128_type=uint128_type779)
                                                _t1492 = _t1494
                                            else:
                                                if prediction774 == 3:
                                                    _t1496 = self.parse_float_type()
                                                    float_type778 = _t1496
                                                    _t1497 = logic_pb2.Type(float_type=float_type778)
                                                    _t1495 = _t1497
                                                else:
                                                    if prediction774 == 2:
                                                        _t1499 = self.parse_int_type()
                                                        int_type777 = _t1499
                                                        _t1500 = logic_pb2.Type(int_type=int_type777)
                                                        _t1498 = _t1500
                                                    else:
                                                        if prediction774 == 1:
                                                            _t1502 = self.parse_string_type()
                                                            string_type776 = _t1502
                                                            _t1503 = logic_pb2.Type(string_type=string_type776)
                                                            _t1501 = _t1503
                                                        else:
                                                            if prediction774 == 0:
                                                                _t1505 = self.parse_unspecified_type()
                                                                unspecified_type775 = _t1505
                                                                _t1506 = logic_pb2.Type(unspecified_type=unspecified_type775)
                                                                _t1504 = _t1506
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t1501 = _t1504
                                                        _t1498 = _t1501
                                                    _t1495 = _t1498
                                                _t1492 = _t1495
                                            _t1489 = _t1492
                                        _t1486 = _t1489
                                    _t1483 = _t1486
                                _t1480 = _t1483
                            _t1477 = _t1480
                        _t1474 = _t1477
                    _t1471 = _t1474
                _t1468 = _t1471
            _t1465 = _t1468
        result790 = _t1465
        self.record_span(span_start789, "Type")
        return result790

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start791 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1507 = logic_pb2.UnspecifiedType()
        result792 = _t1507
        self.record_span(span_start791, "UnspecifiedType")
        return result792

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start793 = self.span_start()
        self.consume_literal("STRING")
        _t1508 = logic_pb2.StringType()
        result794 = _t1508
        self.record_span(span_start793, "StringType")
        return result794

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start795 = self.span_start()
        self.consume_literal("INT")
        _t1509 = logic_pb2.IntType()
        result796 = _t1509
        self.record_span(span_start795, "IntType")
        return result796

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start797 = self.span_start()
        self.consume_literal("FLOAT")
        _t1510 = logic_pb2.FloatType()
        result798 = _t1510
        self.record_span(span_start797, "FloatType")
        return result798

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start799 = self.span_start()
        self.consume_literal("UINT128")
        _t1511 = logic_pb2.UInt128Type()
        result800 = _t1511
        self.record_span(span_start799, "UInt128Type")
        return result800

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start801 = self.span_start()
        self.consume_literal("INT128")
        _t1512 = logic_pb2.Int128Type()
        result802 = _t1512
        self.record_span(span_start801, "Int128Type")
        return result802

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start803 = self.span_start()
        self.consume_literal("DATE")
        _t1513 = logic_pb2.DateType()
        result804 = _t1513
        self.record_span(span_start803, "DateType")
        return result804

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start805 = self.span_start()
        self.consume_literal("DATETIME")
        _t1514 = logic_pb2.DateTimeType()
        result806 = _t1514
        self.record_span(span_start805, "DateTimeType")
        return result806

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start807 = self.span_start()
        self.consume_literal("MISSING")
        _t1515 = logic_pb2.MissingType()
        result808 = _t1515
        self.record_span(span_start807, "MissingType")
        return result808

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start811 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int809 = self.consume_terminal("INT")
        int_3810 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1516 = logic_pb2.DecimalType(precision=int(int809), scale=int(int_3810))
        result812 = _t1516
        self.record_span(span_start811, "DecimalType")
        return result812

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start813 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1517 = logic_pb2.BooleanType()
        result814 = _t1517
        self.record_span(span_start813, "BooleanType")
        return result814

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start815 = self.span_start()
        self.consume_literal("INT32")
        _t1518 = logic_pb2.Int32Type()
        result816 = _t1518
        self.record_span(span_start815, "Int32Type")
        return result816

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start817 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1519 = logic_pb2.Float32Type()
        result818 = _t1519
        self.record_span(span_start817, "Float32Type")
        return result818

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start819 = self.span_start()
        self.consume_literal("UINT32")
        _t1520 = logic_pb2.UInt32Type()
        result820 = _t1520
        self.record_span(span_start819, "UInt32Type")
        return result820

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs821 = []
        cond822 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond822:
            _t1521 = self.parse_binding()
            item823 = _t1521
            xs821.append(item823)
            cond822 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings824 = xs821
        return bindings824

    def parse_formula(self) -> logic_pb2.Formula:
        span_start839 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1523 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1524 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1525 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1526 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1527 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1528 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1529 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1530 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1531 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1532 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1533 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1534 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1535 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1536 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1537 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1538 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1539 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1540 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1541 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1542 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1543 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1544 = 10
                                                                                                else:
                                                                                                    _t1544 = -1
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
        else:
            _t1522 = -1
        prediction825 = _t1522
        if prediction825 == 12:
            _t1546 = self.parse_cast()
            cast838 = _t1546
            _t1547 = logic_pb2.Formula(cast=cast838)
            _t1545 = _t1547
        else:
            if prediction825 == 11:
                _t1549 = self.parse_rel_atom()
                rel_atom837 = _t1549
                _t1550 = logic_pb2.Formula(rel_atom=rel_atom837)
                _t1548 = _t1550
            else:
                if prediction825 == 10:
                    _t1552 = self.parse_primitive()
                    primitive836 = _t1552
                    _t1553 = logic_pb2.Formula(primitive=primitive836)
                    _t1551 = _t1553
                else:
                    if prediction825 == 9:
                        _t1555 = self.parse_pragma()
                        pragma835 = _t1555
                        _t1556 = logic_pb2.Formula(pragma=pragma835)
                        _t1554 = _t1556
                    else:
                        if prediction825 == 8:
                            _t1558 = self.parse_atom()
                            atom834 = _t1558
                            _t1559 = logic_pb2.Formula(atom=atom834)
                            _t1557 = _t1559
                        else:
                            if prediction825 == 7:
                                _t1561 = self.parse_ffi()
                                ffi833 = _t1561
                                _t1562 = logic_pb2.Formula(ffi=ffi833)
                                _t1560 = _t1562
                            else:
                                if prediction825 == 6:
                                    _t1564 = self.parse_not()
                                    not832 = _t1564
                                    _t1565 = logic_pb2.Formula()
                                    getattr(_t1565, 'not').CopyFrom(not832)
                                    _t1563 = _t1565
                                else:
                                    if prediction825 == 5:
                                        _t1567 = self.parse_disjunction()
                                        disjunction831 = _t1567
                                        _t1568 = logic_pb2.Formula(disjunction=disjunction831)
                                        _t1566 = _t1568
                                    else:
                                        if prediction825 == 4:
                                            _t1570 = self.parse_conjunction()
                                            conjunction830 = _t1570
                                            _t1571 = logic_pb2.Formula(conjunction=conjunction830)
                                            _t1569 = _t1571
                                        else:
                                            if prediction825 == 3:
                                                _t1573 = self.parse_reduce()
                                                reduce829 = _t1573
                                                _t1574 = logic_pb2.Formula(reduce=reduce829)
                                                _t1572 = _t1574
                                            else:
                                                if prediction825 == 2:
                                                    _t1576 = self.parse_exists()
                                                    exists828 = _t1576
                                                    _t1577 = logic_pb2.Formula(exists=exists828)
                                                    _t1575 = _t1577
                                                else:
                                                    if prediction825 == 1:
                                                        _t1579 = self.parse_false()
                                                        false827 = _t1579
                                                        _t1580 = logic_pb2.Formula(disjunction=false827)
                                                        _t1578 = _t1580
                                                    else:
                                                        if prediction825 == 0:
                                                            _t1582 = self.parse_true()
                                                            true826 = _t1582
                                                            _t1583 = logic_pb2.Formula(conjunction=true826)
                                                            _t1581 = _t1583
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1578 = _t1581
                                                    _t1575 = _t1578
                                                _t1572 = _t1575
                                            _t1569 = _t1572
                                        _t1566 = _t1569
                                    _t1563 = _t1566
                                _t1560 = _t1563
                            _t1557 = _t1560
                        _t1554 = _t1557
                    _t1551 = _t1554
                _t1548 = _t1551
            _t1545 = _t1548
        result840 = _t1545
        self.record_span(span_start839, "Formula")
        return result840

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start841 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1584 = logic_pb2.Conjunction(args=[])
        result842 = _t1584
        self.record_span(span_start841, "Conjunction")
        return result842

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start843 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1585 = logic_pb2.Disjunction(args=[])
        result844 = _t1585
        self.record_span(span_start843, "Disjunction")
        return result844

    def parse_exists(self) -> logic_pb2.Exists:
        span_start847 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1586 = self.parse_bindings()
        bindings845 = _t1586
        _t1587 = self.parse_formula()
        formula846 = _t1587
        self.consume_literal(")")
        _t1588 = logic_pb2.Abstraction(vars=(list(bindings845[0]) + list(bindings845[1] if bindings845[1] is not None else [])), value=formula846)
        _t1589 = logic_pb2.Exists(body=_t1588)
        result848 = _t1589
        self.record_span(span_start847, "Exists")
        return result848

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start852 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1590 = self.parse_abstraction()
        abstraction849 = _t1590
        _t1591 = self.parse_abstraction()
        abstraction_3850 = _t1591
        _t1592 = self.parse_terms()
        terms851 = _t1592
        self.consume_literal(")")
        _t1593 = logic_pb2.Reduce(op=abstraction849, body=abstraction_3850, terms=terms851)
        result853 = _t1593
        self.record_span(span_start852, "Reduce")
        return result853

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs854 = []
        cond855 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond855:
            _t1594 = self.parse_term()
            item856 = _t1594
            xs854.append(item856)
            cond855 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms857 = xs854
        self.consume_literal(")")
        return terms857

    def parse_term(self) -> logic_pb2.Term:
        span_start861 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1595 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1596 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1597 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1598 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1599 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1600 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1601 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1602 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1603 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1604 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1605 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1606 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1607 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1608 = 1
                                                            else:
                                                                _t1608 = -1
                                                            _t1607 = _t1608
                                                        _t1606 = _t1607
                                                    _t1605 = _t1606
                                                _t1604 = _t1605
                                            _t1603 = _t1604
                                        _t1602 = _t1603
                                    _t1601 = _t1602
                                _t1600 = _t1601
                            _t1599 = _t1600
                        _t1598 = _t1599
                    _t1597 = _t1598
                _t1596 = _t1597
            _t1595 = _t1596
        prediction858 = _t1595
        if prediction858 == 1:
            _t1610 = self.parse_value()
            value860 = _t1610
            _t1611 = logic_pb2.Term(constant=value860)
            _t1609 = _t1611
        else:
            if prediction858 == 0:
                _t1613 = self.parse_var()
                var859 = _t1613
                _t1614 = logic_pb2.Term(var=var859)
                _t1612 = _t1614
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1609 = _t1612
        result862 = _t1609
        self.record_span(span_start861, "Term")
        return result862

    def parse_var(self) -> logic_pb2.Var:
        span_start864 = self.span_start()
        symbol863 = self.consume_terminal("SYMBOL")
        _t1615 = logic_pb2.Var(name=symbol863)
        result865 = _t1615
        self.record_span(span_start864, "Var")
        return result865

    def parse_value(self) -> logic_pb2.Value:
        span_start879 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1616 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1617 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1618 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1620 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1621 = 0
                            else:
                                _t1621 = -1
                            _t1620 = _t1621
                        _t1619 = _t1620
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1622 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1623 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1624 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1625 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1626 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1627 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1628 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1629 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1630 = 10
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
                        _t1619 = _t1622
                    _t1618 = _t1619
                _t1617 = _t1618
            _t1616 = _t1617
        prediction866 = _t1616
        if prediction866 == 12:
            _t1632 = self.parse_boolean_value()
            boolean_value878 = _t1632
            _t1633 = logic_pb2.Value(boolean_value=boolean_value878)
            _t1631 = _t1633
        else:
            if prediction866 == 11:
                self.consume_literal("missing")
                _t1635 = logic_pb2.MissingValue()
                _t1636 = logic_pb2.Value(missing_value=_t1635)
                _t1634 = _t1636
            else:
                if prediction866 == 10:
                    formatted_decimal877 = self.consume_terminal("DECIMAL")
                    _t1638 = logic_pb2.Value(decimal_value=formatted_decimal877)
                    _t1637 = _t1638
                else:
                    if prediction866 == 9:
                        formatted_int128876 = self.consume_terminal("INT128")
                        _t1640 = logic_pb2.Value(int128_value=formatted_int128876)
                        _t1639 = _t1640
                    else:
                        if prediction866 == 8:
                            formatted_uint128875 = self.consume_terminal("UINT128")
                            _t1642 = logic_pb2.Value(uint128_value=formatted_uint128875)
                            _t1641 = _t1642
                        else:
                            if prediction866 == 7:
                                formatted_uint32874 = self.consume_terminal("UINT32")
                                _t1644 = logic_pb2.Value(uint32_value=formatted_uint32874)
                                _t1643 = _t1644
                            else:
                                if prediction866 == 6:
                                    formatted_float873 = self.consume_terminal("FLOAT")
                                    _t1646 = logic_pb2.Value(float_value=formatted_float873)
                                    _t1645 = _t1646
                                else:
                                    if prediction866 == 5:
                                        formatted_float32872 = self.consume_terminal("FLOAT32")
                                        _t1648 = logic_pb2.Value(float32_value=formatted_float32872)
                                        _t1647 = _t1648
                                    else:
                                        if prediction866 == 4:
                                            formatted_int871 = self.consume_terminal("INT")
                                            _t1650 = logic_pb2.Value(int_value=formatted_int871)
                                            _t1649 = _t1650
                                        else:
                                            if prediction866 == 3:
                                                formatted_int32870 = self.consume_terminal("INT32")
                                                _t1652 = logic_pb2.Value(int32_value=formatted_int32870)
                                                _t1651 = _t1652
                                            else:
                                                if prediction866 == 2:
                                                    formatted_string869 = self.consume_terminal("STRING")
                                                    _t1654 = logic_pb2.Value(string_value=formatted_string869)
                                                    _t1653 = _t1654
                                                else:
                                                    if prediction866 == 1:
                                                        _t1656 = self.parse_datetime()
                                                        datetime868 = _t1656
                                                        _t1657 = logic_pb2.Value(datetime_value=datetime868)
                                                        _t1655 = _t1657
                                                    else:
                                                        if prediction866 == 0:
                                                            _t1659 = self.parse_date()
                                                            date867 = _t1659
                                                            _t1660 = logic_pb2.Value(date_value=date867)
                                                            _t1658 = _t1660
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1655 = _t1658
                                                    _t1653 = _t1655
                                                _t1651 = _t1653
                                            _t1649 = _t1651
                                        _t1647 = _t1649
                                    _t1645 = _t1647
                                _t1643 = _t1645
                            _t1641 = _t1643
                        _t1639 = _t1641
                    _t1637 = _t1639
                _t1634 = _t1637
            _t1631 = _t1634
        result880 = _t1631
        self.record_span(span_start879, "Value")
        return result880

    def parse_date(self) -> logic_pb2.DateValue:
        span_start884 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int881 = self.consume_terminal("INT")
        formatted_int_3882 = self.consume_terminal("INT")
        formatted_int_4883 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1661 = logic_pb2.DateValue(year=int(formatted_int881), month=int(formatted_int_3882), day=int(formatted_int_4883))
        result885 = _t1661
        self.record_span(span_start884, "DateValue")
        return result885

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start893 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int886 = self.consume_terminal("INT")
        formatted_int_3887 = self.consume_terminal("INT")
        formatted_int_4888 = self.consume_terminal("INT")
        formatted_int_5889 = self.consume_terminal("INT")
        formatted_int_6890 = self.consume_terminal("INT")
        formatted_int_7891 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1662 = self.consume_terminal("INT")
        else:
            _t1662 = None
        formatted_int_8892 = _t1662
        self.consume_literal(")")
        _t1663 = logic_pb2.DateTimeValue(year=int(formatted_int886), month=int(formatted_int_3887), day=int(formatted_int_4888), hour=int(formatted_int_5889), minute=int(formatted_int_6890), second=int(formatted_int_7891), microsecond=int((formatted_int_8892 if formatted_int_8892 is not None else 0)))
        result894 = _t1663
        self.record_span(span_start893, "DateTimeValue")
        return result894

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start899 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs895 = []
        cond896 = self.match_lookahead_literal("(", 0)
        while cond896:
            _t1664 = self.parse_formula()
            item897 = _t1664
            xs895.append(item897)
            cond896 = self.match_lookahead_literal("(", 0)
        formulas898 = xs895
        self.consume_literal(")")
        _t1665 = logic_pb2.Conjunction(args=formulas898)
        result900 = _t1665
        self.record_span(span_start899, "Conjunction")
        return result900

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start905 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs901 = []
        cond902 = self.match_lookahead_literal("(", 0)
        while cond902:
            _t1666 = self.parse_formula()
            item903 = _t1666
            xs901.append(item903)
            cond902 = self.match_lookahead_literal("(", 0)
        formulas904 = xs901
        self.consume_literal(")")
        _t1667 = logic_pb2.Disjunction(args=formulas904)
        result906 = _t1667
        self.record_span(span_start905, "Disjunction")
        return result906

    def parse_not(self) -> logic_pb2.Not:
        span_start908 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1668 = self.parse_formula()
        formula907 = _t1668
        self.consume_literal(")")
        _t1669 = logic_pb2.Not(arg=formula907)
        result909 = _t1669
        self.record_span(span_start908, "Not")
        return result909

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start913 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1670 = self.parse_name()
        name910 = _t1670
        _t1671 = self.parse_ffi_args()
        ffi_args911 = _t1671
        _t1672 = self.parse_terms()
        terms912 = _t1672
        self.consume_literal(")")
        _t1673 = logic_pb2.FFI(name=name910, args=ffi_args911, terms=terms912)
        result914 = _t1673
        self.record_span(span_start913, "FFI")
        return result914

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol915 = self.consume_terminal("SYMBOL")
        return symbol915

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs916 = []
        cond917 = self.match_lookahead_literal("(", 0)
        while cond917:
            _t1674 = self.parse_abstraction()
            item918 = _t1674
            xs916.append(item918)
            cond917 = self.match_lookahead_literal("(", 0)
        abstractions919 = xs916
        self.consume_literal(")")
        return abstractions919

    def parse_atom(self) -> logic_pb2.Atom:
        span_start925 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1675 = self.parse_relation_id()
        relation_id920 = _t1675
        xs921 = []
        cond922 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond922:
            _t1676 = self.parse_term()
            item923 = _t1676
            xs921.append(item923)
            cond922 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms924 = xs921
        self.consume_literal(")")
        _t1677 = logic_pb2.Atom(name=relation_id920, terms=terms924)
        result926 = _t1677
        self.record_span(span_start925, "Atom")
        return result926

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start932 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1678 = self.parse_name()
        name927 = _t1678
        xs928 = []
        cond929 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond929:
            _t1679 = self.parse_term()
            item930 = _t1679
            xs928.append(item930)
            cond929 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms931 = xs928
        self.consume_literal(")")
        _t1680 = logic_pb2.Pragma(name=name927, terms=terms931)
        result933 = _t1680
        self.record_span(span_start932, "Pragma")
        return result933

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start949 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1682 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1683 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1684 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1685 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1686 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1687 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1688 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1689 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1690 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1691 = 7
                                                else:
                                                    _t1691 = -1
                                                _t1690 = _t1691
                                            _t1689 = _t1690
                                        _t1688 = _t1689
                                    _t1687 = _t1688
                                _t1686 = _t1687
                            _t1685 = _t1686
                        _t1684 = _t1685
                    _t1683 = _t1684
                _t1682 = _t1683
            _t1681 = _t1682
        else:
            _t1681 = -1
        prediction934 = _t1681
        if prediction934 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1693 = self.parse_name()
            name944 = _t1693
            xs945 = []
            cond946 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond946:
                _t1694 = self.parse_rel_term()
                item947 = _t1694
                xs945.append(item947)
                cond946 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms948 = xs945
            self.consume_literal(")")
            _t1695 = logic_pb2.Primitive(name=name944, terms=rel_terms948)
            _t1692 = _t1695
        else:
            if prediction934 == 8:
                _t1697 = self.parse_divide()
                divide943 = _t1697
                _t1696 = divide943
            else:
                if prediction934 == 7:
                    _t1699 = self.parse_multiply()
                    multiply942 = _t1699
                    _t1698 = multiply942
                else:
                    if prediction934 == 6:
                        _t1701 = self.parse_minus()
                        minus941 = _t1701
                        _t1700 = minus941
                    else:
                        if prediction934 == 5:
                            _t1703 = self.parse_add()
                            add940 = _t1703
                            _t1702 = add940
                        else:
                            if prediction934 == 4:
                                _t1705 = self.parse_gt_eq()
                                gt_eq939 = _t1705
                                _t1704 = gt_eq939
                            else:
                                if prediction934 == 3:
                                    _t1707 = self.parse_gt()
                                    gt938 = _t1707
                                    _t1706 = gt938
                                else:
                                    if prediction934 == 2:
                                        _t1709 = self.parse_lt_eq()
                                        lt_eq937 = _t1709
                                        _t1708 = lt_eq937
                                    else:
                                        if prediction934 == 1:
                                            _t1711 = self.parse_lt()
                                            lt936 = _t1711
                                            _t1710 = lt936
                                        else:
                                            if prediction934 == 0:
                                                _t1713 = self.parse_eq()
                                                eq935 = _t1713
                                                _t1712 = eq935
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1710 = _t1712
                                        _t1708 = _t1710
                                    _t1706 = _t1708
                                _t1704 = _t1706
                            _t1702 = _t1704
                        _t1700 = _t1702
                    _t1698 = _t1700
                _t1696 = _t1698
            _t1692 = _t1696
        result950 = _t1692
        self.record_span(span_start949, "Primitive")
        return result950

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start953 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1714 = self.parse_term()
        term951 = _t1714
        _t1715 = self.parse_term()
        term_3952 = _t1715
        self.consume_literal(")")
        _t1716 = logic_pb2.RelTerm(term=term951)
        _t1717 = logic_pb2.RelTerm(term=term_3952)
        _t1718 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1716, _t1717])
        result954 = _t1718
        self.record_span(span_start953, "Primitive")
        return result954

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start957 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1719 = self.parse_term()
        term955 = _t1719
        _t1720 = self.parse_term()
        term_3956 = _t1720
        self.consume_literal(")")
        _t1721 = logic_pb2.RelTerm(term=term955)
        _t1722 = logic_pb2.RelTerm(term=term_3956)
        _t1723 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1721, _t1722])
        result958 = _t1723
        self.record_span(span_start957, "Primitive")
        return result958

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start961 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1724 = self.parse_term()
        term959 = _t1724
        _t1725 = self.parse_term()
        term_3960 = _t1725
        self.consume_literal(")")
        _t1726 = logic_pb2.RelTerm(term=term959)
        _t1727 = logic_pb2.RelTerm(term=term_3960)
        _t1728 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1726, _t1727])
        result962 = _t1728
        self.record_span(span_start961, "Primitive")
        return result962

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start965 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1729 = self.parse_term()
        term963 = _t1729
        _t1730 = self.parse_term()
        term_3964 = _t1730
        self.consume_literal(")")
        _t1731 = logic_pb2.RelTerm(term=term963)
        _t1732 = logic_pb2.RelTerm(term=term_3964)
        _t1733 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1731, _t1732])
        result966 = _t1733
        self.record_span(span_start965, "Primitive")
        return result966

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start969 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1734 = self.parse_term()
        term967 = _t1734
        _t1735 = self.parse_term()
        term_3968 = _t1735
        self.consume_literal(")")
        _t1736 = logic_pb2.RelTerm(term=term967)
        _t1737 = logic_pb2.RelTerm(term=term_3968)
        _t1738 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1736, _t1737])
        result970 = _t1738
        self.record_span(span_start969, "Primitive")
        return result970

    def parse_add(self) -> logic_pb2.Primitive:
        span_start974 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1739 = self.parse_term()
        term971 = _t1739
        _t1740 = self.parse_term()
        term_3972 = _t1740
        _t1741 = self.parse_term()
        term_4973 = _t1741
        self.consume_literal(")")
        _t1742 = logic_pb2.RelTerm(term=term971)
        _t1743 = logic_pb2.RelTerm(term=term_3972)
        _t1744 = logic_pb2.RelTerm(term=term_4973)
        _t1745 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1742, _t1743, _t1744])
        result975 = _t1745
        self.record_span(span_start974, "Primitive")
        return result975

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start979 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1746 = self.parse_term()
        term976 = _t1746
        _t1747 = self.parse_term()
        term_3977 = _t1747
        _t1748 = self.parse_term()
        term_4978 = _t1748
        self.consume_literal(")")
        _t1749 = logic_pb2.RelTerm(term=term976)
        _t1750 = logic_pb2.RelTerm(term=term_3977)
        _t1751 = logic_pb2.RelTerm(term=term_4978)
        _t1752 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1749, _t1750, _t1751])
        result980 = _t1752
        self.record_span(span_start979, "Primitive")
        return result980

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start984 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1753 = self.parse_term()
        term981 = _t1753
        _t1754 = self.parse_term()
        term_3982 = _t1754
        _t1755 = self.parse_term()
        term_4983 = _t1755
        self.consume_literal(")")
        _t1756 = logic_pb2.RelTerm(term=term981)
        _t1757 = logic_pb2.RelTerm(term=term_3982)
        _t1758 = logic_pb2.RelTerm(term=term_4983)
        _t1759 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1756, _t1757, _t1758])
        result985 = _t1759
        self.record_span(span_start984, "Primitive")
        return result985

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start989 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1760 = self.parse_term()
        term986 = _t1760
        _t1761 = self.parse_term()
        term_3987 = _t1761
        _t1762 = self.parse_term()
        term_4988 = _t1762
        self.consume_literal(")")
        _t1763 = logic_pb2.RelTerm(term=term986)
        _t1764 = logic_pb2.RelTerm(term=term_3987)
        _t1765 = logic_pb2.RelTerm(term=term_4988)
        _t1766 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1763, _t1764, _t1765])
        result990 = _t1766
        self.record_span(span_start989, "Primitive")
        return result990

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start994 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1767 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1768 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1769 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1770 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1771 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1772 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1773 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1774 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1775 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1776 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1777 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1778 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1779 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1780 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1781 = 1
                                                                else:
                                                                    _t1781 = -1
                                                                _t1780 = _t1781
                                                            _t1779 = _t1780
                                                        _t1778 = _t1779
                                                    _t1777 = _t1778
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
        prediction991 = _t1767
        if prediction991 == 1:
            _t1783 = self.parse_term()
            term993 = _t1783
            _t1784 = logic_pb2.RelTerm(term=term993)
            _t1782 = _t1784
        else:
            if prediction991 == 0:
                _t1786 = self.parse_specialized_value()
                specialized_value992 = _t1786
                _t1787 = logic_pb2.RelTerm(specialized_value=specialized_value992)
                _t1785 = _t1787
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1782 = _t1785
        result995 = _t1782
        self.record_span(span_start994, "RelTerm")
        return result995

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start997 = self.span_start()
        self.consume_literal("#")
        _t1788 = self.parse_raw_value()
        raw_value996 = _t1788
        result998 = raw_value996
        self.record_span(span_start997, "Value")
        return result998

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start1004 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1789 = self.parse_name()
        name999 = _t1789
        xs1000 = []
        cond1001 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond1001:
            _t1790 = self.parse_rel_term()
            item1002 = _t1790
            xs1000.append(item1002)
            cond1001 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1003 = xs1000
        self.consume_literal(")")
        _t1791 = logic_pb2.RelAtom(name=name999, terms=rel_terms1003)
        result1005 = _t1791
        self.record_span(span_start1004, "RelAtom")
        return result1005

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1008 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1792 = self.parse_term()
        term1006 = _t1792
        _t1793 = self.parse_term()
        term_31007 = _t1793
        self.consume_literal(")")
        _t1794 = logic_pb2.Cast(input=term1006, result=term_31007)
        result1009 = _t1794
        self.record_span(span_start1008, "Cast")
        return result1009

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1010 = []
        cond1011 = self.match_lookahead_literal("(", 0)
        while cond1011:
            _t1795 = self.parse_attribute()
            item1012 = _t1795
            xs1010.append(item1012)
            cond1011 = self.match_lookahead_literal("(", 0)
        attributes1013 = xs1010
        self.consume_literal(")")
        return attributes1013

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1019 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1796 = self.parse_name()
        name1014 = _t1796
        xs1015 = []
        cond1016 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1016:
            _t1797 = self.parse_raw_value()
            item1017 = _t1797
            xs1015.append(item1017)
            cond1016 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1018 = xs1015
        self.consume_literal(")")
        _t1798 = logic_pb2.Attribute(name=name1014, args=raw_values1018)
        result1020 = _t1798
        self.record_span(span_start1019, "Attribute")
        return result1020

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1026 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1021 = []
        cond1022 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1022:
            _t1799 = self.parse_relation_id()
            item1023 = _t1799
            xs1021.append(item1023)
            cond1022 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1024 = xs1021
        _t1800 = self.parse_script()
        script1025 = _t1800
        self.consume_literal(")")
        _t1801 = logic_pb2.Algorithm(body=script1025)
        getattr(_t1801, 'global').extend(relation_ids1024)
        result1027 = _t1801
        self.record_span(span_start1026, "Algorithm")
        return result1027

    def parse_script(self) -> logic_pb2.Script:
        span_start1032 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1028 = []
        cond1029 = self.match_lookahead_literal("(", 0)
        while cond1029:
            _t1802 = self.parse_construct()
            item1030 = _t1802
            xs1028.append(item1030)
            cond1029 = self.match_lookahead_literal("(", 0)
        constructs1031 = xs1028
        self.consume_literal(")")
        _t1803 = logic_pb2.Script(constructs=constructs1031)
        result1033 = _t1803
        self.record_span(span_start1032, "Script")
        return result1033

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1037 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1805 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1806 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1807 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1808 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1809 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1810 = 1
                                else:
                                    _t1810 = -1
                                _t1809 = _t1810
                            _t1808 = _t1809
                        _t1807 = _t1808
                    _t1806 = _t1807
                _t1805 = _t1806
            _t1804 = _t1805
        else:
            _t1804 = -1
        prediction1034 = _t1804
        if prediction1034 == 1:
            _t1812 = self.parse_instruction()
            instruction1036 = _t1812
            _t1813 = logic_pb2.Construct(instruction=instruction1036)
            _t1811 = _t1813
        else:
            if prediction1034 == 0:
                _t1815 = self.parse_loop()
                loop1035 = _t1815
                _t1816 = logic_pb2.Construct(loop=loop1035)
                _t1814 = _t1816
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1811 = _t1814
        result1038 = _t1811
        self.record_span(span_start1037, "Construct")
        return result1038

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1041 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1817 = self.parse_init()
        init1039 = _t1817
        _t1818 = self.parse_script()
        script1040 = _t1818
        self.consume_literal(")")
        _t1819 = logic_pb2.Loop(init=init1039, body=script1040)
        result1042 = _t1819
        self.record_span(span_start1041, "Loop")
        return result1042

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1043 = []
        cond1044 = self.match_lookahead_literal("(", 0)
        while cond1044:
            _t1820 = self.parse_instruction()
            item1045 = _t1820
            xs1043.append(item1045)
            cond1044 = self.match_lookahead_literal("(", 0)
        instructions1046 = xs1043
        self.consume_literal(")")
        return instructions1046

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1053 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1822 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1823 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1824 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1825 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1826 = 0
                            else:
                                _t1826 = -1
                            _t1825 = _t1826
                        _t1824 = _t1825
                    _t1823 = _t1824
                _t1822 = _t1823
            _t1821 = _t1822
        else:
            _t1821 = -1
        prediction1047 = _t1821
        if prediction1047 == 4:
            _t1828 = self.parse_monus_def()
            monus_def1052 = _t1828
            _t1829 = logic_pb2.Instruction(monus_def=monus_def1052)
            _t1827 = _t1829
        else:
            if prediction1047 == 3:
                _t1831 = self.parse_monoid_def()
                monoid_def1051 = _t1831
                _t1832 = logic_pb2.Instruction(monoid_def=monoid_def1051)
                _t1830 = _t1832
            else:
                if prediction1047 == 2:
                    _t1834 = self.parse_break()
                    break1050 = _t1834
                    _t1835 = logic_pb2.Instruction()
                    getattr(_t1835, 'break').CopyFrom(break1050)
                    _t1833 = _t1835
                else:
                    if prediction1047 == 1:
                        _t1837 = self.parse_upsert()
                        upsert1049 = _t1837
                        _t1838 = logic_pb2.Instruction(upsert=upsert1049)
                        _t1836 = _t1838
                    else:
                        if prediction1047 == 0:
                            _t1840 = self.parse_assign()
                            assign1048 = _t1840
                            _t1841 = logic_pb2.Instruction(assign=assign1048)
                            _t1839 = _t1841
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1836 = _t1839
                    _t1833 = _t1836
                _t1830 = _t1833
            _t1827 = _t1830
        result1054 = _t1827
        self.record_span(span_start1053, "Instruction")
        return result1054

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1058 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1842 = self.parse_relation_id()
        relation_id1055 = _t1842
        _t1843 = self.parse_abstraction()
        abstraction1056 = _t1843
        if self.match_lookahead_literal("(", 0):
            _t1845 = self.parse_attrs()
            _t1844 = _t1845
        else:
            _t1844 = None
        attrs1057 = _t1844
        self.consume_literal(")")
        _t1846 = logic_pb2.Assign(name=relation_id1055, body=abstraction1056, attrs=(attrs1057 if attrs1057 is not None else []))
        result1059 = _t1846
        self.record_span(span_start1058, "Assign")
        return result1059

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1063 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1847 = self.parse_relation_id()
        relation_id1060 = _t1847
        _t1848 = self.parse_abstraction_with_arity()
        abstraction_with_arity1061 = _t1848
        if self.match_lookahead_literal("(", 0):
            _t1850 = self.parse_attrs()
            _t1849 = _t1850
        else:
            _t1849 = None
        attrs1062 = _t1849
        self.consume_literal(")")
        _t1851 = logic_pb2.Upsert(name=relation_id1060, body=abstraction_with_arity1061[0], attrs=(attrs1062 if attrs1062 is not None else []), value_arity=abstraction_with_arity1061[1])
        result1064 = _t1851
        self.record_span(span_start1063, "Upsert")
        return result1064

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1852 = self.parse_bindings()
        bindings1065 = _t1852
        _t1853 = self.parse_formula()
        formula1066 = _t1853
        self.consume_literal(")")
        _t1854 = logic_pb2.Abstraction(vars=(list(bindings1065[0]) + list(bindings1065[1] if bindings1065[1] is not None else [])), value=formula1066)
        return (_t1854, len(bindings1065[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1070 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1855 = self.parse_relation_id()
        relation_id1067 = _t1855
        _t1856 = self.parse_abstraction()
        abstraction1068 = _t1856
        if self.match_lookahead_literal("(", 0):
            _t1858 = self.parse_attrs()
            _t1857 = _t1858
        else:
            _t1857 = None
        attrs1069 = _t1857
        self.consume_literal(")")
        _t1859 = logic_pb2.Break(name=relation_id1067, body=abstraction1068, attrs=(attrs1069 if attrs1069 is not None else []))
        result1071 = _t1859
        self.record_span(span_start1070, "Break")
        return result1071

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1076 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1860 = self.parse_monoid()
        monoid1072 = _t1860
        _t1861 = self.parse_relation_id()
        relation_id1073 = _t1861
        _t1862 = self.parse_abstraction_with_arity()
        abstraction_with_arity1074 = _t1862
        if self.match_lookahead_literal("(", 0):
            _t1864 = self.parse_attrs()
            _t1863 = _t1864
        else:
            _t1863 = None
        attrs1075 = _t1863
        self.consume_literal(")")
        _t1865 = logic_pb2.MonoidDef(monoid=monoid1072, name=relation_id1073, body=abstraction_with_arity1074[0], attrs=(attrs1075 if attrs1075 is not None else []), value_arity=abstraction_with_arity1074[1])
        result1077 = _t1865
        self.record_span(span_start1076, "MonoidDef")
        return result1077

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1083 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1867 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1868 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1869 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1870 = 2
                        else:
                            _t1870 = -1
                        _t1869 = _t1870
                    _t1868 = _t1869
                _t1867 = _t1868
            _t1866 = _t1867
        else:
            _t1866 = -1
        prediction1078 = _t1866
        if prediction1078 == 3:
            _t1872 = self.parse_sum_monoid()
            sum_monoid1082 = _t1872
            _t1873 = logic_pb2.Monoid(sum_monoid=sum_monoid1082)
            _t1871 = _t1873
        else:
            if prediction1078 == 2:
                _t1875 = self.parse_max_monoid()
                max_monoid1081 = _t1875
                _t1876 = logic_pb2.Monoid(max_monoid=max_monoid1081)
                _t1874 = _t1876
            else:
                if prediction1078 == 1:
                    _t1878 = self.parse_min_monoid()
                    min_monoid1080 = _t1878
                    _t1879 = logic_pb2.Monoid(min_monoid=min_monoid1080)
                    _t1877 = _t1879
                else:
                    if prediction1078 == 0:
                        _t1881 = self.parse_or_monoid()
                        or_monoid1079 = _t1881
                        _t1882 = logic_pb2.Monoid(or_monoid=or_monoid1079)
                        _t1880 = _t1882
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1877 = _t1880
                _t1874 = _t1877
            _t1871 = _t1874
        result1084 = _t1871
        self.record_span(span_start1083, "Monoid")
        return result1084

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1085 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1883 = logic_pb2.OrMonoid()
        result1086 = _t1883
        self.record_span(span_start1085, "OrMonoid")
        return result1086

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1088 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1884 = self.parse_type()
        type1087 = _t1884
        self.consume_literal(")")
        _t1885 = logic_pb2.MinMonoid(type=type1087)
        result1089 = _t1885
        self.record_span(span_start1088, "MinMonoid")
        return result1089

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1091 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1886 = self.parse_type()
        type1090 = _t1886
        self.consume_literal(")")
        _t1887 = logic_pb2.MaxMonoid(type=type1090)
        result1092 = _t1887
        self.record_span(span_start1091, "MaxMonoid")
        return result1092

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1094 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1888 = self.parse_type()
        type1093 = _t1888
        self.consume_literal(")")
        _t1889 = logic_pb2.SumMonoid(type=type1093)
        result1095 = _t1889
        self.record_span(span_start1094, "SumMonoid")
        return result1095

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1100 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1890 = self.parse_monoid()
        monoid1096 = _t1890
        _t1891 = self.parse_relation_id()
        relation_id1097 = _t1891
        _t1892 = self.parse_abstraction_with_arity()
        abstraction_with_arity1098 = _t1892
        if self.match_lookahead_literal("(", 0):
            _t1894 = self.parse_attrs()
            _t1893 = _t1894
        else:
            _t1893 = None
        attrs1099 = _t1893
        self.consume_literal(")")
        _t1895 = logic_pb2.MonusDef(monoid=monoid1096, name=relation_id1097, body=abstraction_with_arity1098[0], attrs=(attrs1099 if attrs1099 is not None else []), value_arity=abstraction_with_arity1098[1])
        result1101 = _t1895
        self.record_span(span_start1100, "MonusDef")
        return result1101

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1106 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1896 = self.parse_relation_id()
        relation_id1102 = _t1896
        _t1897 = self.parse_abstraction()
        abstraction1103 = _t1897
        _t1898 = self.parse_functional_dependency_keys()
        functional_dependency_keys1104 = _t1898
        _t1899 = self.parse_functional_dependency_values()
        functional_dependency_values1105 = _t1899
        self.consume_literal(")")
        _t1900 = logic_pb2.FunctionalDependency(guard=abstraction1103, keys=functional_dependency_keys1104, values=functional_dependency_values1105)
        _t1901 = logic_pb2.Constraint(name=relation_id1102, functional_dependency=_t1900)
        result1107 = _t1901
        self.record_span(span_start1106, "Constraint")
        return result1107

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1108 = []
        cond1109 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1109:
            _t1902 = self.parse_var()
            item1110 = _t1902
            xs1108.append(item1110)
            cond1109 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1111 = xs1108
        self.consume_literal(")")
        return vars1111

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1112 = []
        cond1113 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1113:
            _t1903 = self.parse_var()
            item1114 = _t1903
            xs1112.append(item1114)
            cond1113 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1115 = xs1112
        self.consume_literal(")")
        return vars1115

    def parse_data(self) -> logic_pb2.Data:
        span_start1121 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1905 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1906 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t1907 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t1908 = 1
                        else:
                            _t1908 = -1
                        _t1907 = _t1908
                    _t1906 = _t1907
                _t1905 = _t1906
            _t1904 = _t1905
        else:
            _t1904 = -1
        prediction1116 = _t1904
        if prediction1116 == 3:
            _t1910 = self.parse_iceberg_data()
            iceberg_data1120 = _t1910
            _t1911 = logic_pb2.Data(iceberg_data=iceberg_data1120)
            _t1909 = _t1911
        else:
            if prediction1116 == 2:
                _t1913 = self.parse_csv_data()
                csv_data1119 = _t1913
                _t1914 = logic_pb2.Data(csv_data=csv_data1119)
                _t1912 = _t1914
            else:
                if prediction1116 == 1:
                    _t1916 = self.parse_betree_relation()
                    betree_relation1118 = _t1916
                    _t1917 = logic_pb2.Data(betree_relation=betree_relation1118)
                    _t1915 = _t1917
                else:
                    if prediction1116 == 0:
                        _t1919 = self.parse_edb()
                        edb1117 = _t1919
                        _t1920 = logic_pb2.Data(edb=edb1117)
                        _t1918 = _t1920
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1915 = _t1918
                _t1912 = _t1915
            _t1909 = _t1912
        result1122 = _t1909
        self.record_span(span_start1121, "Data")
        return result1122

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1126 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1921 = self.parse_relation_id()
        relation_id1123 = _t1921
        _t1922 = self.parse_edb_path()
        edb_path1124 = _t1922
        _t1923 = self.parse_edb_types()
        edb_types1125 = _t1923
        self.consume_literal(")")
        _t1924 = logic_pb2.EDB(target_id=relation_id1123, path=edb_path1124, types=edb_types1125)
        result1127 = _t1924
        self.record_span(span_start1126, "EDB")
        return result1127

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1128 = []
        cond1129 = self.match_lookahead_terminal("STRING", 0)
        while cond1129:
            item1130 = self.consume_terminal("STRING")
            xs1128.append(item1130)
            cond1129 = self.match_lookahead_terminal("STRING", 0)
        strings1131 = xs1128
        self.consume_literal("]")
        return strings1131

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1132 = []
        cond1133 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1133:
            _t1925 = self.parse_type()
            item1134 = _t1925
            xs1132.append(item1134)
            cond1133 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1135 = xs1132
        self.consume_literal("]")
        return types1135

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1138 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1926 = self.parse_relation_id()
        relation_id1136 = _t1926
        _t1927 = self.parse_betree_info()
        betree_info1137 = _t1927
        self.consume_literal(")")
        _t1928 = logic_pb2.BeTreeRelation(name=relation_id1136, relation_info=betree_info1137)
        result1139 = _t1928
        self.record_span(span_start1138, "BeTreeRelation")
        return result1139

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1143 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1929 = self.parse_betree_info_key_types()
        betree_info_key_types1140 = _t1929
        _t1930 = self.parse_betree_info_value_types()
        betree_info_value_types1141 = _t1930
        _t1931 = self.parse_config_dict()
        config_dict1142 = _t1931
        self.consume_literal(")")
        _t1932 = self.construct_betree_info(betree_info_key_types1140, betree_info_value_types1141, config_dict1142)
        result1144 = _t1932
        self.record_span(span_start1143, "BeTreeInfo")
        return result1144

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1145 = []
        cond1146 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1146:
            _t1933 = self.parse_type()
            item1147 = _t1933
            xs1145.append(item1147)
            cond1146 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1148 = xs1145
        self.consume_literal(")")
        return types1148

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1149 = []
        cond1150 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1150:
            _t1934 = self.parse_type()
            item1151 = _t1934
            xs1149.append(item1151)
            cond1150 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1152 = xs1149
        self.consume_literal(")")
        return types1152

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1157 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1935 = self.parse_csvlocator()
        csvlocator1153 = _t1935
        _t1936 = self.parse_csv_config()
        csv_config1154 = _t1936
        _t1937 = self.parse_gnf_columns()
        gnf_columns1155 = _t1937
        _t1938 = self.parse_csv_asof()
        csv_asof1156 = _t1938
        self.consume_literal(")")
        _t1939 = logic_pb2.CSVData(locator=csvlocator1153, config=csv_config1154, columns=gnf_columns1155, asof=csv_asof1156)
        result1158 = _t1939
        self.record_span(span_start1157, "CSVData")
        return result1158

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1161 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1941 = self.parse_csv_locator_paths()
            _t1940 = _t1941
        else:
            _t1940 = None
        csv_locator_paths1159 = _t1940
        if self.match_lookahead_literal("(", 0):
            _t1943 = self.parse_csv_locator_inline_data()
            _t1942 = _t1943
        else:
            _t1942 = None
        csv_locator_inline_data1160 = _t1942
        self.consume_literal(")")
        _t1944 = logic_pb2.CSVLocator(paths=(csv_locator_paths1159 if csv_locator_paths1159 is not None else []), inline_data=(csv_locator_inline_data1160 if csv_locator_inline_data1160 is not None else "").encode())
        result1162 = _t1944
        self.record_span(span_start1161, "CSVLocator")
        return result1162

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1163 = []
        cond1164 = self.match_lookahead_terminal("STRING", 0)
        while cond1164:
            item1165 = self.consume_terminal("STRING")
            xs1163.append(item1165)
            cond1164 = self.match_lookahead_terminal("STRING", 0)
        strings1166 = xs1163
        self.consume_literal(")")
        return strings1166

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1167 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1167

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1169 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1945 = self.parse_config_dict()
        config_dict1168 = _t1945
        self.consume_literal(")")
        _t1946 = self.construct_csv_config(config_dict1168)
        result1170 = _t1946
        self.record_span(span_start1169, "CSVConfig")
        return result1170

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1171 = []
        cond1172 = self.match_lookahead_literal("(", 0)
        while cond1172:
            _t1947 = self.parse_gnf_column()
            item1173 = _t1947
            xs1171.append(item1173)
            cond1172 = self.match_lookahead_literal("(", 0)
        gnf_columns1174 = xs1171
        self.consume_literal(")")
        return gnf_columns1174

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1181 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1948 = self.parse_gnf_column_path()
        gnf_column_path1175 = _t1948
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1950 = self.parse_relation_id()
            _t1949 = _t1950
        else:
            _t1949 = None
        relation_id1176 = _t1949
        self.consume_literal("[")
        xs1177 = []
        cond1178 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1178:
            _t1951 = self.parse_type()
            item1179 = _t1951
            xs1177.append(item1179)
            cond1178 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1180 = xs1177
        self.consume_literal("]")
        self.consume_literal(")")
        _t1952 = logic_pb2.GNFColumn(column_path=gnf_column_path1175, target_id=relation_id1176, types=types1180)
        result1182 = _t1952
        self.record_span(span_start1181, "GNFColumn")
        return result1182

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1953 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1954 = 0
            else:
                _t1954 = -1
            _t1953 = _t1954
        prediction1183 = _t1953
        if prediction1183 == 1:
            self.consume_literal("[")
            xs1185 = []
            cond1186 = self.match_lookahead_terminal("STRING", 0)
            while cond1186:
                item1187 = self.consume_terminal("STRING")
                xs1185.append(item1187)
                cond1186 = self.match_lookahead_terminal("STRING", 0)
            strings1188 = xs1185
            self.consume_literal("]")
            _t1955 = strings1188
        else:
            if prediction1183 == 0:
                string1184 = self.consume_terminal("STRING")
                _t1956 = [string1184]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1955 = _t1956
        return _t1955

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1189 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1189

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1194 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t1957 = self.parse_iceberg_locator()
        iceberg_locator1190 = _t1957
        _t1958 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1191 = _t1958
        _t1959 = self.parse_gnf_columns()
        gnf_columns1192 = _t1959
        _t1960 = self.parse_boolean_value()
        boolean_value1193 = _t1960
        self.consume_literal(")")
        _t1961 = logic_pb2.IcebergData(locator=iceberg_locator1190, config=iceberg_catalog_config1191, columns=gnf_columns1192, returns_delta=boolean_value1193)
        result1195 = _t1961
        self.record_span(span_start1194, "IcebergData")
        return result1195

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1204 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1196 = self.consume_terminal("STRING")
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1197 = []
        cond1198 = self.match_lookahead_terminal("STRING", 0)
        while cond1198:
            item1199 = self.consume_terminal("STRING")
            xs1197.append(item1199)
            cond1198 = self.match_lookahead_terminal("STRING", 0)
        strings1200 = xs1197
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string_121201 = self.consume_terminal("STRING")
        self.consume_literal(")")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("from_snapshot", 1)):
            _t1963 = self.parse_iceberg_from_snapshot()
            _t1962 = _t1963
        else:
            _t1962 = None
        iceberg_from_snapshot1202 = _t1962
        if self.match_lookahead_literal("(", 0):
            _t1965 = self.parse_iceberg_to_snapshot()
            _t1964 = _t1965
        else:
            _t1964 = None
        iceberg_to_snapshot1203 = _t1964
        self.consume_literal(")")
        _t1966 = self.construct_iceberg_locator(string1196, strings1200, string_121201, iceberg_from_snapshot1202, iceberg_to_snapshot1203)
        result1205 = _t1966
        self.record_span(span_start1204, "IcebergLocator")
        return result1205

    def parse_iceberg_from_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("from_snapshot")
        string1206 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1206

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1207 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1207

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1218 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1208 = self.consume_terminal("STRING")
        self.consume_literal(")")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t1968 = self.parse_iceberg_catalog_config_scope()
            _t1967 = _t1968
        else:
            _t1967 = None
        iceberg_catalog_config_scope1209 = _t1967
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1210 = []
        cond1211 = self.match_lookahead_literal("(", 0)
        while cond1211:
            _t1969 = self.parse_iceberg_property_entry()
            item1212 = _t1969
            xs1210.append(item1212)
            cond1211 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1213 = xs1210
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1214 = []
        cond1215 = self.match_lookahead_literal("(", 0)
        while cond1215:
            _t1970 = self.parse_iceberg_masked_property_entry()
            item1216 = _t1970
            xs1214.append(item1216)
            cond1215 = self.match_lookahead_literal("(", 0)
        iceberg_masked_property_entrys1217 = xs1214
        self.consume_literal(")")
        self.consume_literal(")")
        _t1971 = self.construct_iceberg_catalog_config(string1208, iceberg_catalog_config_scope1209, iceberg_property_entrys1213, iceberg_masked_property_entrys1217)
        result1219 = _t1971
        self.record_span(span_start1218, "IcebergCatalogConfig")
        return result1219

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1220 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1220

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1221 = self.consume_terminal("STRING")
        string_31222 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1221, string_31222,)

    def parse_iceberg_masked_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1223 = self.consume_terminal("STRING")
        string_31224 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1223, string_31224,)

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1226 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1972 = self.parse_fragment_id()
        fragment_id1225 = _t1972
        self.consume_literal(")")
        _t1973 = transactions_pb2.Undefine(fragment_id=fragment_id1225)
        result1227 = _t1973
        self.record_span(span_start1226, "Undefine")
        return result1227

    def parse_context(self) -> transactions_pb2.Context:
        span_start1232 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1228 = []
        cond1229 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1229:
            _t1974 = self.parse_relation_id()
            item1230 = _t1974
            xs1228.append(item1230)
            cond1229 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1231 = xs1228
        self.consume_literal(")")
        _t1975 = transactions_pb2.Context(relations=relation_ids1231)
        result1233 = _t1975
        self.record_span(span_start1232, "Context")
        return result1233

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1238 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        xs1234 = []
        cond1235 = self.match_lookahead_literal("[", 0)
        while cond1235:
            _t1976 = self.parse_snapshot_mapping()
            item1236 = _t1976
            xs1234.append(item1236)
            cond1235 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1237 = xs1234
        self.consume_literal(")")
        _t1977 = transactions_pb2.Snapshot(mappings=snapshot_mappings1237)
        result1239 = _t1977
        self.record_span(span_start1238, "Snapshot")
        return result1239

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1242 = self.span_start()
        _t1978 = self.parse_edb_path()
        edb_path1240 = _t1978
        _t1979 = self.parse_relation_id()
        relation_id1241 = _t1979
        _t1980 = transactions_pb2.SnapshotMapping(destination_path=edb_path1240, source_relation=relation_id1241)
        result1243 = _t1980
        self.record_span(span_start1242, "SnapshotMapping")
        return result1243

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1244 = []
        cond1245 = self.match_lookahead_literal("(", 0)
        while cond1245:
            _t1981 = self.parse_read()
            item1246 = _t1981
            xs1244.append(item1246)
            cond1245 = self.match_lookahead_literal("(", 0)
        reads1247 = xs1244
        self.consume_literal(")")
        return reads1247

    def parse_read(self) -> transactions_pb2.Read:
        span_start1254 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1983 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1984 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t1985 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t1986 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t1987 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t1988 = 3
                                else:
                                    _t1988 = -1
                                _t1987 = _t1988
                            _t1986 = _t1987
                        _t1985 = _t1986
                    _t1984 = _t1985
                _t1983 = _t1984
            _t1982 = _t1983
        else:
            _t1982 = -1
        prediction1248 = _t1982
        if prediction1248 == 4:
            _t1990 = self.parse_export()
            export1253 = _t1990
            _t1991 = transactions_pb2.Read(export=export1253)
            _t1989 = _t1991
        else:
            if prediction1248 == 3:
                _t1993 = self.parse_abort()
                abort1252 = _t1993
                _t1994 = transactions_pb2.Read(abort=abort1252)
                _t1992 = _t1994
            else:
                if prediction1248 == 2:
                    _t1996 = self.parse_what_if()
                    what_if1251 = _t1996
                    _t1997 = transactions_pb2.Read(what_if=what_if1251)
                    _t1995 = _t1997
                else:
                    if prediction1248 == 1:
                        _t1999 = self.parse_output()
                        output1250 = _t1999
                        _t2000 = transactions_pb2.Read(output=output1250)
                        _t1998 = _t2000
                    else:
                        if prediction1248 == 0:
                            _t2002 = self.parse_demand()
                            demand1249 = _t2002
                            _t2003 = transactions_pb2.Read(demand=demand1249)
                            _t2001 = _t2003
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1998 = _t2001
                    _t1995 = _t1998
                _t1992 = _t1995
            _t1989 = _t1992
        result1255 = _t1989
        self.record_span(span_start1254, "Read")
        return result1255

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1257 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t2004 = self.parse_relation_id()
        relation_id1256 = _t2004
        self.consume_literal(")")
        _t2005 = transactions_pb2.Demand(relation_id=relation_id1256)
        result1258 = _t2005
        self.record_span(span_start1257, "Demand")
        return result1258

    def parse_output(self) -> transactions_pb2.Output:
        span_start1261 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2006 = self.parse_name()
        name1259 = _t2006
        _t2007 = self.parse_relation_id()
        relation_id1260 = _t2007
        self.consume_literal(")")
        _t2008 = transactions_pb2.Output(name=name1259, relation_id=relation_id1260)
        result1262 = _t2008
        self.record_span(span_start1261, "Output")
        return result1262

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1265 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2009 = self.parse_name()
        name1263 = _t2009
        _t2010 = self.parse_epoch()
        epoch1264 = _t2010
        self.consume_literal(")")
        _t2011 = transactions_pb2.WhatIf(branch=name1263, epoch=epoch1264)
        result1266 = _t2011
        self.record_span(span_start1265, "WhatIf")
        return result1266

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1269 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2013 = self.parse_name()
            _t2012 = _t2013
        else:
            _t2012 = None
        name1267 = _t2012
        _t2014 = self.parse_relation_id()
        relation_id1268 = _t2014
        self.consume_literal(")")
        _t2015 = transactions_pb2.Abort(name=(name1267 if name1267 is not None else "abort"), relation_id=relation_id1268)
        result1270 = _t2015
        self.record_span(span_start1269, "Abort")
        return result1270

    def parse_export(self) -> transactions_pb2.Export:
        span_start1274 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2017 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2018 = 0
                else:
                    _t2018 = -1
                _t2017 = _t2018
            _t2016 = _t2017
        else:
            _t2016 = -1
        prediction1271 = _t2016
        if prediction1271 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2020 = self.parse_export_iceberg_config()
            export_iceberg_config1273 = _t2020
            self.consume_literal(")")
            _t2021 = transactions_pb2.Export(iceberg_config=export_iceberg_config1273)
            _t2019 = _t2021
        else:
            if prediction1271 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2023 = self.parse_export_csv_config()
                export_csv_config1272 = _t2023
                self.consume_literal(")")
                _t2024 = transactions_pb2.Export(csv_config=export_csv_config1272)
                _t2022 = _t2024
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2019 = _t2022
        result1275 = _t2019
        self.record_span(span_start1274, "Export")
        return result1275

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1283 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2026 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2027 = 1
                else:
                    _t2027 = -1
                _t2026 = _t2027
            _t2025 = _t2026
        else:
            _t2025 = -1
        prediction1276 = _t2025
        if prediction1276 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2029 = self.parse_export_csv_path()
            export_csv_path1280 = _t2029
            _t2030 = self.parse_export_csv_columns_list()
            export_csv_columns_list1281 = _t2030
            _t2031 = self.parse_config_dict()
            config_dict1282 = _t2031
            self.consume_literal(")")
            _t2032 = self.construct_export_csv_config(export_csv_path1280, export_csv_columns_list1281, config_dict1282)
            _t2028 = _t2032
        else:
            if prediction1276 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2034 = self.parse_export_csv_path()
                export_csv_path1277 = _t2034
                _t2035 = self.parse_export_csv_source()
                export_csv_source1278 = _t2035
                _t2036 = self.parse_csv_config()
                csv_config1279 = _t2036
                self.consume_literal(")")
                _t2037 = self.construct_export_csv_config_with_source(export_csv_path1277, export_csv_source1278, csv_config1279)
                _t2033 = _t2037
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2028 = _t2033
        result1284 = _t2028
        self.record_span(span_start1283, "ExportCSVConfig")
        return result1284

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1285 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1285

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1292 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2039 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2040 = 0
                else:
                    _t2040 = -1
                _t2039 = _t2040
            _t2038 = _t2039
        else:
            _t2038 = -1
        prediction1286 = _t2038
        if prediction1286 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2042 = self.parse_relation_id()
            relation_id1291 = _t2042
            self.consume_literal(")")
            _t2043 = transactions_pb2.ExportCSVSource(table_def=relation_id1291)
            _t2041 = _t2043
        else:
            if prediction1286 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1287 = []
                cond1288 = self.match_lookahead_literal("(", 0)
                while cond1288:
                    _t2045 = self.parse_export_csv_column()
                    item1289 = _t2045
                    xs1287.append(item1289)
                    cond1288 = self.match_lookahead_literal("(", 0)
                export_csv_columns1290 = xs1287
                self.consume_literal(")")
                _t2046 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1290)
                _t2047 = transactions_pb2.ExportCSVSource(gnf_columns=_t2046)
                _t2044 = _t2047
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2041 = _t2044
        result1293 = _t2041
        self.record_span(span_start1292, "ExportCSVSource")
        return result1293

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1296 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1294 = self.consume_terminal("STRING")
        _t2048 = self.parse_relation_id()
        relation_id1295 = _t2048
        self.consume_literal(")")
        _t2049 = transactions_pb2.ExportCSVColumn(column_name=string1294, column_data=relation_id1295)
        result1297 = _t2049
        self.record_span(span_start1296, "ExportCSVColumn")
        return result1297

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1298 = []
        cond1299 = self.match_lookahead_literal("(", 0)
        while cond1299:
            _t2050 = self.parse_export_csv_column()
            item1300 = _t2050
            xs1298.append(item1300)
            cond1299 = self.match_lookahead_literal("(", 0)
        export_csv_columns1301 = xs1298
        self.consume_literal(")")
        return export_csv_columns1301

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1314 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2051 = self.parse_iceberg_locator()
        iceberg_locator1302 = _t2051
        _t2052 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1303 = _t2052
        self.consume_literal("(")
        self.consume_literal("table_def")
        _t2053 = self.parse_relation_id()
        relation_id1304 = _t2053
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1305 = []
        cond1306 = self.match_lookahead_literal("(", 0)
        while cond1306:
            _t2054 = self.parse_export_gnf_column()
            item1307 = _t2054
            xs1305.append(item1307)
            cond1306 = self.match_lookahead_literal("(", 0)
        export_gnf_columns1308 = xs1305
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("table_properties")
        xs1309 = []
        cond1310 = self.match_lookahead_literal("(", 0)
        while cond1310:
            _t2055 = self.parse_iceberg_property_entry()
            item1311 = _t2055
            xs1309.append(item1311)
            cond1310 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1312 = xs1309
        self.consume_literal(")")
        if self.match_lookahead_literal("{", 0):
            _t2057 = self.parse_config_dict()
            _t2056 = _t2057
        else:
            _t2056 = None
        config_dict1313 = _t2056
        self.consume_literal(")")
        _t2058 = self.construct_export_iceberg_config_full(iceberg_locator1302, iceberg_catalog_config1303, relation_id1304, export_gnf_columns1308, iceberg_property_entrys1312, config_dict1313)
        result1315 = _t2058
        self.record_span(span_start1314, "ExportIcebergConfig")
        return result1315

    def parse_export_gnf_column(self) -> transactions_pb2.ExportGNFColumn:
        span_start1318 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("gnf_column")
        string1316 = self.consume_terminal("STRING")
        _t2059 = self.parse_boolean_value()
        boolean_value1317 = _t2059
        self.consume_literal(")")
        _t2060 = transactions_pb2.ExportGNFColumn(name=string1316, nullable=boolean_value1317)
        result1319 = _t2060
        self.record_span(span_start1318, "ExportGNFColumn")
        return result1319


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
