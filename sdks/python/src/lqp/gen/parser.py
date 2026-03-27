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
            _t2059 = value.HasField("int32_value")
        else:
            _t2059 = False
        if _t2059:
            assert value is not None
            return value.int32_value
        else:
            _t2060 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2061 = value.HasField("int_value")
        else:
            _t2061 = False
        if _t2061:
            assert value is not None
            return value.int_value
        else:
            _t2062 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2063 = value.HasField("string_value")
        else:
            _t2063 = False
        if _t2063:
            assert value is not None
            return value.string_value
        else:
            _t2064 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2065 = value.HasField("boolean_value")
        else:
            _t2065 = False
        if _t2065:
            assert value is not None
            return value.boolean_value
        else:
            _t2066 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2067 = value.HasField("string_value")
        else:
            _t2067 = False
        if _t2067:
            assert value is not None
            return [value.string_value]
        else:
            _t2068 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t2069 = value.HasField("int_value")
        else:
            _t2069 = False
        if _t2069:
            assert value is not None
            return value.int_value
        else:
            _t2070 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2071 = value.HasField("float_value")
        else:
            _t2071 = False
        if _t2071:
            assert value is not None
            return value.float_value
        else:
            _t2072 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2073 = value.HasField("string_value")
        else:
            _t2073 = False
        if _t2073:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2074 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2075 = value.HasField("uint128_value")
        else:
            _t2075 = False
        if _t2075:
            assert value is not None
            return value.uint128_value
        else:
            _t2076 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2077 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2077
        _t2078 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2078
        _t2079 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2079
        _t2080 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2080
        _t2081 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2081
        _t2082 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2082
        _t2083 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2083
        _t2084 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2084
        _t2085 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2085
        _t2086 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2086
        _t2087 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t2087
        _t2088 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2088
        _t2089 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t2089

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2090 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2090
        _t2091 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2091
        _t2092 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2092
        _t2093 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2093
        _t2094 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2094
        _t2095 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2095
        _t2096 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2096
        _t2097 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2097
        _t2098 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2098
        _t2099 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2099
        _t2100 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2100

    def default_configure(self) -> transactions_pb2.Configure:
        _t2101 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2101
        _t2102 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2102

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
        _t2103 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2103
        _t2104 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2104
        _t2105 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t2105

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2106 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2106
        _t2107 = self._extract_value_string(config.get("compression"), "")
        compression = _t2107
        _t2108 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2108
        _t2109 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2109
        _t2110 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2110
        _t2111 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2111
        _t2112 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2112
        _t2113 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2113

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2114 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t2114

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2115 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2115

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, columns: transactions_pb2.ExportIcebergColumns, table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2116 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2116
        _t2117 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2117
        _t2118 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2118
        table_props = dict(table_property_pairs)
        _t2119 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, columns=columns, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2119

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start665 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1319 = self.parse_configure()
            _t1318 = _t1319
        else:
            _t1318 = None
        configure659 = _t1318
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1321 = self.parse_sync()
            _t1320 = _t1321
        else:
            _t1320 = None
        sync660 = _t1320
        xs661 = []
        cond662 = self.match_lookahead_literal("(", 0)
        while cond662:
            _t1322 = self.parse_epoch()
            item663 = _t1322
            xs661.append(item663)
            cond662 = self.match_lookahead_literal("(", 0)
        epochs664 = xs661
        self.consume_literal(")")
        _t1323 = self.default_configure()
        _t1324 = transactions_pb2.Transaction(epochs=epochs664, configure=(configure659 if configure659 is not None else _t1323), sync=sync660)
        result666 = _t1324
        self.record_span(span_start665, "Transaction")
        return result666

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start668 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1325 = self.parse_config_dict()
        config_dict667 = _t1325
        self.consume_literal(")")
        _t1326 = self.construct_configure(config_dict667)
        result669 = _t1326
        self.record_span(span_start668, "Configure")
        return result669

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs670 = []
        cond671 = self.match_lookahead_literal(":", 0)
        while cond671:
            _t1327 = self.parse_config_key_value()
            item672 = _t1327
            xs670.append(item672)
            cond671 = self.match_lookahead_literal(":", 0)
        config_key_values673 = xs670
        self.consume_literal("}")
        return config_key_values673

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol674 = self.consume_terminal("SYMBOL")
        _t1328 = self.parse_raw_value()
        raw_value675 = _t1328
        return (symbol674, raw_value675,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start689 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1329 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1330 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1331 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1333 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1334 = 0
                            else:
                                _t1334 = -1
                            _t1333 = _t1334
                        _t1332 = _t1333
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1335 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1336 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1337 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1338 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1339 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1340 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1341 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1342 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1343 = 10
                                                        else:
                                                            _t1343 = -1
                                                        _t1342 = _t1343
                                                    _t1341 = _t1342
                                                _t1340 = _t1341
                                            _t1339 = _t1340
                                        _t1338 = _t1339
                                    _t1337 = _t1338
                                _t1336 = _t1337
                            _t1335 = _t1336
                        _t1332 = _t1335
                    _t1331 = _t1332
                _t1330 = _t1331
            _t1329 = _t1330
        prediction676 = _t1329
        if prediction676 == 12:
            _t1345 = self.parse_boolean_value()
            boolean_value688 = _t1345
            _t1346 = logic_pb2.Value(boolean_value=boolean_value688)
            _t1344 = _t1346
        else:
            if prediction676 == 11:
                self.consume_literal("missing")
                _t1348 = logic_pb2.MissingValue()
                _t1349 = logic_pb2.Value(missing_value=_t1348)
                _t1347 = _t1349
            else:
                if prediction676 == 10:
                    decimal687 = self.consume_terminal("DECIMAL")
                    _t1351 = logic_pb2.Value(decimal_value=decimal687)
                    _t1350 = _t1351
                else:
                    if prediction676 == 9:
                        int128686 = self.consume_terminal("INT128")
                        _t1353 = logic_pb2.Value(int128_value=int128686)
                        _t1352 = _t1353
                    else:
                        if prediction676 == 8:
                            uint128685 = self.consume_terminal("UINT128")
                            _t1355 = logic_pb2.Value(uint128_value=uint128685)
                            _t1354 = _t1355
                        else:
                            if prediction676 == 7:
                                uint32684 = self.consume_terminal("UINT32")
                                _t1357 = logic_pb2.Value(uint32_value=uint32684)
                                _t1356 = _t1357
                            else:
                                if prediction676 == 6:
                                    float683 = self.consume_terminal("FLOAT")
                                    _t1359 = logic_pb2.Value(float_value=float683)
                                    _t1358 = _t1359
                                else:
                                    if prediction676 == 5:
                                        float32682 = self.consume_terminal("FLOAT32")
                                        _t1361 = logic_pb2.Value(float32_value=float32682)
                                        _t1360 = _t1361
                                    else:
                                        if prediction676 == 4:
                                            int681 = self.consume_terminal("INT")
                                            _t1363 = logic_pb2.Value(int_value=int681)
                                            _t1362 = _t1363
                                        else:
                                            if prediction676 == 3:
                                                int32680 = self.consume_terminal("INT32")
                                                _t1365 = logic_pb2.Value(int32_value=int32680)
                                                _t1364 = _t1365
                                            else:
                                                if prediction676 == 2:
                                                    string679 = self.consume_terminal("STRING")
                                                    _t1367 = logic_pb2.Value(string_value=string679)
                                                    _t1366 = _t1367
                                                else:
                                                    if prediction676 == 1:
                                                        _t1369 = self.parse_raw_datetime()
                                                        raw_datetime678 = _t1369
                                                        _t1370 = logic_pb2.Value(datetime_value=raw_datetime678)
                                                        _t1368 = _t1370
                                                    else:
                                                        if prediction676 == 0:
                                                            _t1372 = self.parse_raw_date()
                                                            raw_date677 = _t1372
                                                            _t1373 = logic_pb2.Value(date_value=raw_date677)
                                                            _t1371 = _t1373
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1368 = _t1371
                                                    _t1366 = _t1368
                                                _t1364 = _t1366
                                            _t1362 = _t1364
                                        _t1360 = _t1362
                                    _t1358 = _t1360
                                _t1356 = _t1358
                            _t1354 = _t1356
                        _t1352 = _t1354
                    _t1350 = _t1352
                _t1347 = _t1350
            _t1344 = _t1347
        result690 = _t1344
        self.record_span(span_start689, "Value")
        return result690

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start694 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int691 = self.consume_terminal("INT")
        int_3692 = self.consume_terminal("INT")
        int_4693 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1374 = logic_pb2.DateValue(year=int(int691), month=int(int_3692), day=int(int_4693))
        result695 = _t1374
        self.record_span(span_start694, "DateValue")
        return result695

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start703 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int696 = self.consume_terminal("INT")
        int_3697 = self.consume_terminal("INT")
        int_4698 = self.consume_terminal("INT")
        int_5699 = self.consume_terminal("INT")
        int_6700 = self.consume_terminal("INT")
        int_7701 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1375 = self.consume_terminal("INT")
        else:
            _t1375 = None
        int_8702 = _t1375
        self.consume_literal(")")
        _t1376 = logic_pb2.DateTimeValue(year=int(int696), month=int(int_3697), day=int(int_4698), hour=int(int_5699), minute=int(int_6700), second=int(int_7701), microsecond=int((int_8702 if int_8702 is not None else 0)))
        result704 = _t1376
        self.record_span(span_start703, "DateTimeValue")
        return result704

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1377 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1378 = 1
            else:
                _t1378 = -1
            _t1377 = _t1378
        prediction705 = _t1377
        if prediction705 == 1:
            self.consume_literal("false")
            _t1379 = False
        else:
            if prediction705 == 0:
                self.consume_literal("true")
                _t1380 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1379 = _t1380
        return _t1379

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start710 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs706 = []
        cond707 = self.match_lookahead_literal(":", 0)
        while cond707:
            _t1381 = self.parse_fragment_id()
            item708 = _t1381
            xs706.append(item708)
            cond707 = self.match_lookahead_literal(":", 0)
        fragment_ids709 = xs706
        self.consume_literal(")")
        _t1382 = transactions_pb2.Sync(fragments=fragment_ids709)
        result711 = _t1382
        self.record_span(span_start710, "Sync")
        return result711

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start713 = self.span_start()
        self.consume_literal(":")
        symbol712 = self.consume_terminal("SYMBOL")
        result714 = fragments_pb2.FragmentId(id=symbol712.encode())
        self.record_span(span_start713, "FragmentId")
        return result714

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start717 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1384 = self.parse_epoch_writes()
            _t1383 = _t1384
        else:
            _t1383 = None
        epoch_writes715 = _t1383
        if self.match_lookahead_literal("(", 0):
            _t1386 = self.parse_epoch_reads()
            _t1385 = _t1386
        else:
            _t1385 = None
        epoch_reads716 = _t1385
        self.consume_literal(")")
        _t1387 = transactions_pb2.Epoch(writes=(epoch_writes715 if epoch_writes715 is not None else []), reads=(epoch_reads716 if epoch_reads716 is not None else []))
        result718 = _t1387
        self.record_span(span_start717, "Epoch")
        return result718

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs719 = []
        cond720 = self.match_lookahead_literal("(", 0)
        while cond720:
            _t1388 = self.parse_write()
            item721 = _t1388
            xs719.append(item721)
            cond720 = self.match_lookahead_literal("(", 0)
        writes722 = xs719
        self.consume_literal(")")
        return writes722

    def parse_write(self) -> transactions_pb2.Write:
        span_start728 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1390 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1391 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1392 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1393 = 2
                        else:
                            _t1393 = -1
                        _t1392 = _t1393
                    _t1391 = _t1392
                _t1390 = _t1391
            _t1389 = _t1390
        else:
            _t1389 = -1
        prediction723 = _t1389
        if prediction723 == 3:
            _t1395 = self.parse_snapshot()
            snapshot727 = _t1395
            _t1396 = transactions_pb2.Write(snapshot=snapshot727)
            _t1394 = _t1396
        else:
            if prediction723 == 2:
                _t1398 = self.parse_context()
                context726 = _t1398
                _t1399 = transactions_pb2.Write(context=context726)
                _t1397 = _t1399
            else:
                if prediction723 == 1:
                    _t1401 = self.parse_undefine()
                    undefine725 = _t1401
                    _t1402 = transactions_pb2.Write(undefine=undefine725)
                    _t1400 = _t1402
                else:
                    if prediction723 == 0:
                        _t1404 = self.parse_define()
                        define724 = _t1404
                        _t1405 = transactions_pb2.Write(define=define724)
                        _t1403 = _t1405
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1400 = _t1403
                _t1397 = _t1400
            _t1394 = _t1397
        result729 = _t1394
        self.record_span(span_start728, "Write")
        return result729

    def parse_define(self) -> transactions_pb2.Define:
        span_start731 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1406 = self.parse_fragment()
        fragment730 = _t1406
        self.consume_literal(")")
        _t1407 = transactions_pb2.Define(fragment=fragment730)
        result732 = _t1407
        self.record_span(span_start731, "Define")
        return result732

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start738 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1408 = self.parse_new_fragment_id()
        new_fragment_id733 = _t1408
        xs734 = []
        cond735 = self.match_lookahead_literal("(", 0)
        while cond735:
            _t1409 = self.parse_declaration()
            item736 = _t1409
            xs734.append(item736)
            cond735 = self.match_lookahead_literal("(", 0)
        declarations737 = xs734
        self.consume_literal(")")
        result739 = self.construct_fragment(new_fragment_id733, declarations737)
        self.record_span(span_start738, "Fragment")
        return result739

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start741 = self.span_start()
        _t1410 = self.parse_fragment_id()
        fragment_id740 = _t1410
        self.start_fragment(fragment_id740)
        result742 = fragment_id740
        self.record_span(span_start741, "FragmentId")
        return result742

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start748 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1412 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1413 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1414 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1415 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1416 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1417 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1418 = 1
                                    else:
                                        _t1418 = -1
                                    _t1417 = _t1418
                                _t1416 = _t1417
                            _t1415 = _t1416
                        _t1414 = _t1415
                    _t1413 = _t1414
                _t1412 = _t1413
            _t1411 = _t1412
        else:
            _t1411 = -1
        prediction743 = _t1411
        if prediction743 == 3:
            _t1420 = self.parse_data()
            data747 = _t1420
            _t1421 = logic_pb2.Declaration(data=data747)
            _t1419 = _t1421
        else:
            if prediction743 == 2:
                _t1423 = self.parse_constraint()
                constraint746 = _t1423
                _t1424 = logic_pb2.Declaration(constraint=constraint746)
                _t1422 = _t1424
            else:
                if prediction743 == 1:
                    _t1426 = self.parse_algorithm()
                    algorithm745 = _t1426
                    _t1427 = logic_pb2.Declaration(algorithm=algorithm745)
                    _t1425 = _t1427
                else:
                    if prediction743 == 0:
                        _t1429 = self.parse_def()
                        def744 = _t1429
                        _t1430 = logic_pb2.Declaration()
                        getattr(_t1430, 'def').CopyFrom(def744)
                        _t1428 = _t1430
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1425 = _t1428
                _t1422 = _t1425
            _t1419 = _t1422
        result749 = _t1419
        self.record_span(span_start748, "Declaration")
        return result749

    def parse_def(self) -> logic_pb2.Def:
        span_start753 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1431 = self.parse_relation_id()
        relation_id750 = _t1431
        _t1432 = self.parse_abstraction()
        abstraction751 = _t1432
        if self.match_lookahead_literal("(", 0):
            _t1434 = self.parse_attrs()
            _t1433 = _t1434
        else:
            _t1433 = None
        attrs752 = _t1433
        self.consume_literal(")")
        _t1435 = logic_pb2.Def(name=relation_id750, body=abstraction751, attrs=(attrs752 if attrs752 is not None else []))
        result754 = _t1435
        self.record_span(span_start753, "Def")
        return result754

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start758 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1436 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1437 = 1
            else:
                _t1437 = -1
            _t1436 = _t1437
        prediction755 = _t1436
        if prediction755 == 1:
            uint128757 = self.consume_terminal("UINT128")
            _t1438 = logic_pb2.RelationId(id_low=uint128757.low, id_high=uint128757.high)
        else:
            if prediction755 == 0:
                self.consume_literal(":")
                symbol756 = self.consume_terminal("SYMBOL")
                _t1439 = self.relation_id_from_string(symbol756)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1438 = _t1439
        result759 = _t1438
        self.record_span(span_start758, "RelationId")
        return result759

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start762 = self.span_start()
        self.consume_literal("(")
        _t1440 = self.parse_bindings()
        bindings760 = _t1440
        _t1441 = self.parse_formula()
        formula761 = _t1441
        self.consume_literal(")")
        _t1442 = logic_pb2.Abstraction(vars=(list(bindings760[0]) + list(bindings760[1] if bindings760[1] is not None else [])), value=formula761)
        result763 = _t1442
        self.record_span(span_start762, "Abstraction")
        return result763

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs764 = []
        cond765 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond765:
            _t1443 = self.parse_binding()
            item766 = _t1443
            xs764.append(item766)
            cond765 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings767 = xs764
        if self.match_lookahead_literal("|", 0):
            _t1445 = self.parse_value_bindings()
            _t1444 = _t1445
        else:
            _t1444 = None
        value_bindings768 = _t1444
        self.consume_literal("]")
        return (bindings767, (value_bindings768 if value_bindings768 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start771 = self.span_start()
        symbol769 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1446 = self.parse_type()
        type770 = _t1446
        _t1447 = logic_pb2.Var(name=symbol769)
        _t1448 = logic_pb2.Binding(var=_t1447, type=type770)
        result772 = _t1448
        self.record_span(span_start771, "Binding")
        return result772

    def parse_type(self) -> logic_pb2.Type:
        span_start788 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1449 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1450 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1451 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1452 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1453 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1454 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1455 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1456 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1457 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1458 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1459 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1460 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1461 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1462 = 9
                                                            else:
                                                                _t1462 = -1
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
                _t1450 = _t1451
            _t1449 = _t1450
        prediction773 = _t1449
        if prediction773 == 13:
            _t1464 = self.parse_uint32_type()
            uint32_type787 = _t1464
            _t1465 = logic_pb2.Type(uint32_type=uint32_type787)
            _t1463 = _t1465
        else:
            if prediction773 == 12:
                _t1467 = self.parse_float32_type()
                float32_type786 = _t1467
                _t1468 = logic_pb2.Type(float32_type=float32_type786)
                _t1466 = _t1468
            else:
                if prediction773 == 11:
                    _t1470 = self.parse_int32_type()
                    int32_type785 = _t1470
                    _t1471 = logic_pb2.Type(int32_type=int32_type785)
                    _t1469 = _t1471
                else:
                    if prediction773 == 10:
                        _t1473 = self.parse_boolean_type()
                        boolean_type784 = _t1473
                        _t1474 = logic_pb2.Type(boolean_type=boolean_type784)
                        _t1472 = _t1474
                    else:
                        if prediction773 == 9:
                            _t1476 = self.parse_decimal_type()
                            decimal_type783 = _t1476
                            _t1477 = logic_pb2.Type(decimal_type=decimal_type783)
                            _t1475 = _t1477
                        else:
                            if prediction773 == 8:
                                _t1479 = self.parse_missing_type()
                                missing_type782 = _t1479
                                _t1480 = logic_pb2.Type(missing_type=missing_type782)
                                _t1478 = _t1480
                            else:
                                if prediction773 == 7:
                                    _t1482 = self.parse_datetime_type()
                                    datetime_type781 = _t1482
                                    _t1483 = logic_pb2.Type(datetime_type=datetime_type781)
                                    _t1481 = _t1483
                                else:
                                    if prediction773 == 6:
                                        _t1485 = self.parse_date_type()
                                        date_type780 = _t1485
                                        _t1486 = logic_pb2.Type(date_type=date_type780)
                                        _t1484 = _t1486
                                    else:
                                        if prediction773 == 5:
                                            _t1488 = self.parse_int128_type()
                                            int128_type779 = _t1488
                                            _t1489 = logic_pb2.Type(int128_type=int128_type779)
                                            _t1487 = _t1489
                                        else:
                                            if prediction773 == 4:
                                                _t1491 = self.parse_uint128_type()
                                                uint128_type778 = _t1491
                                                _t1492 = logic_pb2.Type(uint128_type=uint128_type778)
                                                _t1490 = _t1492
                                            else:
                                                if prediction773 == 3:
                                                    _t1494 = self.parse_float_type()
                                                    float_type777 = _t1494
                                                    _t1495 = logic_pb2.Type(float_type=float_type777)
                                                    _t1493 = _t1495
                                                else:
                                                    if prediction773 == 2:
                                                        _t1497 = self.parse_int_type()
                                                        int_type776 = _t1497
                                                        _t1498 = logic_pb2.Type(int_type=int_type776)
                                                        _t1496 = _t1498
                                                    else:
                                                        if prediction773 == 1:
                                                            _t1500 = self.parse_string_type()
                                                            string_type775 = _t1500
                                                            _t1501 = logic_pb2.Type(string_type=string_type775)
                                                            _t1499 = _t1501
                                                        else:
                                                            if prediction773 == 0:
                                                                _t1503 = self.parse_unspecified_type()
                                                                unspecified_type774 = _t1503
                                                                _t1504 = logic_pb2.Type(unspecified_type=unspecified_type774)
                                                                _t1502 = _t1504
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t1499 = _t1502
                                                        _t1496 = _t1499
                                                    _t1493 = _t1496
                                                _t1490 = _t1493
                                            _t1487 = _t1490
                                        _t1484 = _t1487
                                    _t1481 = _t1484
                                _t1478 = _t1481
                            _t1475 = _t1478
                        _t1472 = _t1475
                    _t1469 = _t1472
                _t1466 = _t1469
            _t1463 = _t1466
        result789 = _t1463
        self.record_span(span_start788, "Type")
        return result789

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start790 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1505 = logic_pb2.UnspecifiedType()
        result791 = _t1505
        self.record_span(span_start790, "UnspecifiedType")
        return result791

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start792 = self.span_start()
        self.consume_literal("STRING")
        _t1506 = logic_pb2.StringType()
        result793 = _t1506
        self.record_span(span_start792, "StringType")
        return result793

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start794 = self.span_start()
        self.consume_literal("INT")
        _t1507 = logic_pb2.IntType()
        result795 = _t1507
        self.record_span(span_start794, "IntType")
        return result795

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start796 = self.span_start()
        self.consume_literal("FLOAT")
        _t1508 = logic_pb2.FloatType()
        result797 = _t1508
        self.record_span(span_start796, "FloatType")
        return result797

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start798 = self.span_start()
        self.consume_literal("UINT128")
        _t1509 = logic_pb2.UInt128Type()
        result799 = _t1509
        self.record_span(span_start798, "UInt128Type")
        return result799

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start800 = self.span_start()
        self.consume_literal("INT128")
        _t1510 = logic_pb2.Int128Type()
        result801 = _t1510
        self.record_span(span_start800, "Int128Type")
        return result801

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start802 = self.span_start()
        self.consume_literal("DATE")
        _t1511 = logic_pb2.DateType()
        result803 = _t1511
        self.record_span(span_start802, "DateType")
        return result803

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start804 = self.span_start()
        self.consume_literal("DATETIME")
        _t1512 = logic_pb2.DateTimeType()
        result805 = _t1512
        self.record_span(span_start804, "DateTimeType")
        return result805

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start806 = self.span_start()
        self.consume_literal("MISSING")
        _t1513 = logic_pb2.MissingType()
        result807 = _t1513
        self.record_span(span_start806, "MissingType")
        return result807

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start810 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int808 = self.consume_terminal("INT")
        int_3809 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1514 = logic_pb2.DecimalType(precision=int(int808), scale=int(int_3809))
        result811 = _t1514
        self.record_span(span_start810, "DecimalType")
        return result811

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start812 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1515 = logic_pb2.BooleanType()
        result813 = _t1515
        self.record_span(span_start812, "BooleanType")
        return result813

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start814 = self.span_start()
        self.consume_literal("INT32")
        _t1516 = logic_pb2.Int32Type()
        result815 = _t1516
        self.record_span(span_start814, "Int32Type")
        return result815

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start816 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1517 = logic_pb2.Float32Type()
        result817 = _t1517
        self.record_span(span_start816, "Float32Type")
        return result817

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start818 = self.span_start()
        self.consume_literal("UINT32")
        _t1518 = logic_pb2.UInt32Type()
        result819 = _t1518
        self.record_span(span_start818, "UInt32Type")
        return result819

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs820 = []
        cond821 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond821:
            _t1519 = self.parse_binding()
            item822 = _t1519
            xs820.append(item822)
            cond821 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings823 = xs820
        return bindings823

    def parse_formula(self) -> logic_pb2.Formula:
        span_start838 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1521 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1522 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1523 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1524 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1525 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1526 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1527 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1528 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1529 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1530 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1531 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1532 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1533 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1534 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1535 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1536 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1537 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1538 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1539 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1540 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1541 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1542 = 10
                                                                                                else:
                                                                                                    _t1542 = -1
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
                _t1521 = _t1522
            _t1520 = _t1521
        else:
            _t1520 = -1
        prediction824 = _t1520
        if prediction824 == 12:
            _t1544 = self.parse_cast()
            cast837 = _t1544
            _t1545 = logic_pb2.Formula(cast=cast837)
            _t1543 = _t1545
        else:
            if prediction824 == 11:
                _t1547 = self.parse_rel_atom()
                rel_atom836 = _t1547
                _t1548 = logic_pb2.Formula(rel_atom=rel_atom836)
                _t1546 = _t1548
            else:
                if prediction824 == 10:
                    _t1550 = self.parse_primitive()
                    primitive835 = _t1550
                    _t1551 = logic_pb2.Formula(primitive=primitive835)
                    _t1549 = _t1551
                else:
                    if prediction824 == 9:
                        _t1553 = self.parse_pragma()
                        pragma834 = _t1553
                        _t1554 = logic_pb2.Formula(pragma=pragma834)
                        _t1552 = _t1554
                    else:
                        if prediction824 == 8:
                            _t1556 = self.parse_atom()
                            atom833 = _t1556
                            _t1557 = logic_pb2.Formula(atom=atom833)
                            _t1555 = _t1557
                        else:
                            if prediction824 == 7:
                                _t1559 = self.parse_ffi()
                                ffi832 = _t1559
                                _t1560 = logic_pb2.Formula(ffi=ffi832)
                                _t1558 = _t1560
                            else:
                                if prediction824 == 6:
                                    _t1562 = self.parse_not()
                                    not831 = _t1562
                                    _t1563 = logic_pb2.Formula()
                                    getattr(_t1563, 'not').CopyFrom(not831)
                                    _t1561 = _t1563
                                else:
                                    if prediction824 == 5:
                                        _t1565 = self.parse_disjunction()
                                        disjunction830 = _t1565
                                        _t1566 = logic_pb2.Formula(disjunction=disjunction830)
                                        _t1564 = _t1566
                                    else:
                                        if prediction824 == 4:
                                            _t1568 = self.parse_conjunction()
                                            conjunction829 = _t1568
                                            _t1569 = logic_pb2.Formula(conjunction=conjunction829)
                                            _t1567 = _t1569
                                        else:
                                            if prediction824 == 3:
                                                _t1571 = self.parse_reduce()
                                                reduce828 = _t1571
                                                _t1572 = logic_pb2.Formula(reduce=reduce828)
                                                _t1570 = _t1572
                                            else:
                                                if prediction824 == 2:
                                                    _t1574 = self.parse_exists()
                                                    exists827 = _t1574
                                                    _t1575 = logic_pb2.Formula(exists=exists827)
                                                    _t1573 = _t1575
                                                else:
                                                    if prediction824 == 1:
                                                        _t1577 = self.parse_false()
                                                        false826 = _t1577
                                                        _t1578 = logic_pb2.Formula(disjunction=false826)
                                                        _t1576 = _t1578
                                                    else:
                                                        if prediction824 == 0:
                                                            _t1580 = self.parse_true()
                                                            true825 = _t1580
                                                            _t1581 = logic_pb2.Formula(conjunction=true825)
                                                            _t1579 = _t1581
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1576 = _t1579
                                                    _t1573 = _t1576
                                                _t1570 = _t1573
                                            _t1567 = _t1570
                                        _t1564 = _t1567
                                    _t1561 = _t1564
                                _t1558 = _t1561
                            _t1555 = _t1558
                        _t1552 = _t1555
                    _t1549 = _t1552
                _t1546 = _t1549
            _t1543 = _t1546
        result839 = _t1543
        self.record_span(span_start838, "Formula")
        return result839

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start840 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1582 = logic_pb2.Conjunction(args=[])
        result841 = _t1582
        self.record_span(span_start840, "Conjunction")
        return result841

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start842 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1583 = logic_pb2.Disjunction(args=[])
        result843 = _t1583
        self.record_span(span_start842, "Disjunction")
        return result843

    def parse_exists(self) -> logic_pb2.Exists:
        span_start846 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1584 = self.parse_bindings()
        bindings844 = _t1584
        _t1585 = self.parse_formula()
        formula845 = _t1585
        self.consume_literal(")")
        _t1586 = logic_pb2.Abstraction(vars=(list(bindings844[0]) + list(bindings844[1] if bindings844[1] is not None else [])), value=formula845)
        _t1587 = logic_pb2.Exists(body=_t1586)
        result847 = _t1587
        self.record_span(span_start846, "Exists")
        return result847

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start851 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1588 = self.parse_abstraction()
        abstraction848 = _t1588
        _t1589 = self.parse_abstraction()
        abstraction_3849 = _t1589
        _t1590 = self.parse_terms()
        terms850 = _t1590
        self.consume_literal(")")
        _t1591 = logic_pb2.Reduce(op=abstraction848, body=abstraction_3849, terms=terms850)
        result852 = _t1591
        self.record_span(span_start851, "Reduce")
        return result852

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs853 = []
        cond854 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond854:
            _t1592 = self.parse_term()
            item855 = _t1592
            xs853.append(item855)
            cond854 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms856 = xs853
        self.consume_literal(")")
        return terms856

    def parse_term(self) -> logic_pb2.Term:
        span_start860 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1593 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1594 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1595 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1596 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1597 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1598 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1599 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1600 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1601 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1602 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1603 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1604 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1605 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1606 = 1
                                                            else:
                                                                _t1606 = -1
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
                _t1594 = _t1595
            _t1593 = _t1594
        prediction857 = _t1593
        if prediction857 == 1:
            _t1608 = self.parse_value()
            value859 = _t1608
            _t1609 = logic_pb2.Term(constant=value859)
            _t1607 = _t1609
        else:
            if prediction857 == 0:
                _t1611 = self.parse_var()
                var858 = _t1611
                _t1612 = logic_pb2.Term(var=var858)
                _t1610 = _t1612
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1607 = _t1610
        result861 = _t1607
        self.record_span(span_start860, "Term")
        return result861

    def parse_var(self) -> logic_pb2.Var:
        span_start863 = self.span_start()
        symbol862 = self.consume_terminal("SYMBOL")
        _t1613 = logic_pb2.Var(name=symbol862)
        result864 = _t1613
        self.record_span(span_start863, "Var")
        return result864

    def parse_value(self) -> logic_pb2.Value:
        span_start878 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1614 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1615 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1616 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1618 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1619 = 0
                            else:
                                _t1619 = -1
                            _t1618 = _t1619
                        _t1617 = _t1618
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1620 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1621 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1622 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1623 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1624 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1625 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1626 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1627 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1628 = 10
                                                        else:
                                                            _t1628 = -1
                                                        _t1627 = _t1628
                                                    _t1626 = _t1627
                                                _t1625 = _t1626
                                            _t1624 = _t1625
                                        _t1623 = _t1624
                                    _t1622 = _t1623
                                _t1621 = _t1622
                            _t1620 = _t1621
                        _t1617 = _t1620
                    _t1616 = _t1617
                _t1615 = _t1616
            _t1614 = _t1615
        prediction865 = _t1614
        if prediction865 == 12:
            _t1630 = self.parse_boolean_value()
            boolean_value877 = _t1630
            _t1631 = logic_pb2.Value(boolean_value=boolean_value877)
            _t1629 = _t1631
        else:
            if prediction865 == 11:
                self.consume_literal("missing")
                _t1633 = logic_pb2.MissingValue()
                _t1634 = logic_pb2.Value(missing_value=_t1633)
                _t1632 = _t1634
            else:
                if prediction865 == 10:
                    formatted_decimal876 = self.consume_terminal("DECIMAL")
                    _t1636 = logic_pb2.Value(decimal_value=formatted_decimal876)
                    _t1635 = _t1636
                else:
                    if prediction865 == 9:
                        formatted_int128875 = self.consume_terminal("INT128")
                        _t1638 = logic_pb2.Value(int128_value=formatted_int128875)
                        _t1637 = _t1638
                    else:
                        if prediction865 == 8:
                            formatted_uint128874 = self.consume_terminal("UINT128")
                            _t1640 = logic_pb2.Value(uint128_value=formatted_uint128874)
                            _t1639 = _t1640
                        else:
                            if prediction865 == 7:
                                formatted_uint32873 = self.consume_terminal("UINT32")
                                _t1642 = logic_pb2.Value(uint32_value=formatted_uint32873)
                                _t1641 = _t1642
                            else:
                                if prediction865 == 6:
                                    formatted_float872 = self.consume_terminal("FLOAT")
                                    _t1644 = logic_pb2.Value(float_value=formatted_float872)
                                    _t1643 = _t1644
                                else:
                                    if prediction865 == 5:
                                        formatted_float32871 = self.consume_terminal("FLOAT32")
                                        _t1646 = logic_pb2.Value(float32_value=formatted_float32871)
                                        _t1645 = _t1646
                                    else:
                                        if prediction865 == 4:
                                            formatted_int870 = self.consume_terminal("INT")
                                            _t1648 = logic_pb2.Value(int_value=formatted_int870)
                                            _t1647 = _t1648
                                        else:
                                            if prediction865 == 3:
                                                formatted_int32869 = self.consume_terminal("INT32")
                                                _t1650 = logic_pb2.Value(int32_value=formatted_int32869)
                                                _t1649 = _t1650
                                            else:
                                                if prediction865 == 2:
                                                    formatted_string868 = self.consume_terminal("STRING")
                                                    _t1652 = logic_pb2.Value(string_value=formatted_string868)
                                                    _t1651 = _t1652
                                                else:
                                                    if prediction865 == 1:
                                                        _t1654 = self.parse_datetime()
                                                        datetime867 = _t1654
                                                        _t1655 = logic_pb2.Value(datetime_value=datetime867)
                                                        _t1653 = _t1655
                                                    else:
                                                        if prediction865 == 0:
                                                            _t1657 = self.parse_date()
                                                            date866 = _t1657
                                                            _t1658 = logic_pb2.Value(date_value=date866)
                                                            _t1656 = _t1658
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1653 = _t1656
                                                    _t1651 = _t1653
                                                _t1649 = _t1651
                                            _t1647 = _t1649
                                        _t1645 = _t1647
                                    _t1643 = _t1645
                                _t1641 = _t1643
                            _t1639 = _t1641
                        _t1637 = _t1639
                    _t1635 = _t1637
                _t1632 = _t1635
            _t1629 = _t1632
        result879 = _t1629
        self.record_span(span_start878, "Value")
        return result879

    def parse_date(self) -> logic_pb2.DateValue:
        span_start883 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int880 = self.consume_terminal("INT")
        formatted_int_3881 = self.consume_terminal("INT")
        formatted_int_4882 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1659 = logic_pb2.DateValue(year=int(formatted_int880), month=int(formatted_int_3881), day=int(formatted_int_4882))
        result884 = _t1659
        self.record_span(span_start883, "DateValue")
        return result884

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start892 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int885 = self.consume_terminal("INT")
        formatted_int_3886 = self.consume_terminal("INT")
        formatted_int_4887 = self.consume_terminal("INT")
        formatted_int_5888 = self.consume_terminal("INT")
        formatted_int_6889 = self.consume_terminal("INT")
        formatted_int_7890 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1660 = self.consume_terminal("INT")
        else:
            _t1660 = None
        formatted_int_8891 = _t1660
        self.consume_literal(")")
        _t1661 = logic_pb2.DateTimeValue(year=int(formatted_int885), month=int(formatted_int_3886), day=int(formatted_int_4887), hour=int(formatted_int_5888), minute=int(formatted_int_6889), second=int(formatted_int_7890), microsecond=int((formatted_int_8891 if formatted_int_8891 is not None else 0)))
        result893 = _t1661
        self.record_span(span_start892, "DateTimeValue")
        return result893

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start898 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs894 = []
        cond895 = self.match_lookahead_literal("(", 0)
        while cond895:
            _t1662 = self.parse_formula()
            item896 = _t1662
            xs894.append(item896)
            cond895 = self.match_lookahead_literal("(", 0)
        formulas897 = xs894
        self.consume_literal(")")
        _t1663 = logic_pb2.Conjunction(args=formulas897)
        result899 = _t1663
        self.record_span(span_start898, "Conjunction")
        return result899

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start904 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs900 = []
        cond901 = self.match_lookahead_literal("(", 0)
        while cond901:
            _t1664 = self.parse_formula()
            item902 = _t1664
            xs900.append(item902)
            cond901 = self.match_lookahead_literal("(", 0)
        formulas903 = xs900
        self.consume_literal(")")
        _t1665 = logic_pb2.Disjunction(args=formulas903)
        result905 = _t1665
        self.record_span(span_start904, "Disjunction")
        return result905

    def parse_not(self) -> logic_pb2.Not:
        span_start907 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1666 = self.parse_formula()
        formula906 = _t1666
        self.consume_literal(")")
        _t1667 = logic_pb2.Not(arg=formula906)
        result908 = _t1667
        self.record_span(span_start907, "Not")
        return result908

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start912 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1668 = self.parse_name()
        name909 = _t1668
        _t1669 = self.parse_ffi_args()
        ffi_args910 = _t1669
        _t1670 = self.parse_terms()
        terms911 = _t1670
        self.consume_literal(")")
        _t1671 = logic_pb2.FFI(name=name909, args=ffi_args910, terms=terms911)
        result913 = _t1671
        self.record_span(span_start912, "FFI")
        return result913

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol914 = self.consume_terminal("SYMBOL")
        return symbol914

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs915 = []
        cond916 = self.match_lookahead_literal("(", 0)
        while cond916:
            _t1672 = self.parse_abstraction()
            item917 = _t1672
            xs915.append(item917)
            cond916 = self.match_lookahead_literal("(", 0)
        abstractions918 = xs915
        self.consume_literal(")")
        return abstractions918

    def parse_atom(self) -> logic_pb2.Atom:
        span_start924 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1673 = self.parse_relation_id()
        relation_id919 = _t1673
        xs920 = []
        cond921 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond921:
            _t1674 = self.parse_term()
            item922 = _t1674
            xs920.append(item922)
            cond921 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms923 = xs920
        self.consume_literal(")")
        _t1675 = logic_pb2.Atom(name=relation_id919, terms=terms923)
        result925 = _t1675
        self.record_span(span_start924, "Atom")
        return result925

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start931 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1676 = self.parse_name()
        name926 = _t1676
        xs927 = []
        cond928 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond928:
            _t1677 = self.parse_term()
            item929 = _t1677
            xs927.append(item929)
            cond928 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms930 = xs927
        self.consume_literal(")")
        _t1678 = logic_pb2.Pragma(name=name926, terms=terms930)
        result932 = _t1678
        self.record_span(span_start931, "Pragma")
        return result932

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start948 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1680 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1681 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1682 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1683 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1684 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1685 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1686 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1687 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1688 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1689 = 7
                                                else:
                                                    _t1689 = -1
                                                _t1688 = _t1689
                                            _t1687 = _t1688
                                        _t1686 = _t1687
                                    _t1685 = _t1686
                                _t1684 = _t1685
                            _t1683 = _t1684
                        _t1682 = _t1683
                    _t1681 = _t1682
                _t1680 = _t1681
            _t1679 = _t1680
        else:
            _t1679 = -1
        prediction933 = _t1679
        if prediction933 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1691 = self.parse_name()
            name943 = _t1691
            xs944 = []
            cond945 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond945:
                _t1692 = self.parse_rel_term()
                item946 = _t1692
                xs944.append(item946)
                cond945 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms947 = xs944
            self.consume_literal(")")
            _t1693 = logic_pb2.Primitive(name=name943, terms=rel_terms947)
            _t1690 = _t1693
        else:
            if prediction933 == 8:
                _t1695 = self.parse_divide()
                divide942 = _t1695
                _t1694 = divide942
            else:
                if prediction933 == 7:
                    _t1697 = self.parse_multiply()
                    multiply941 = _t1697
                    _t1696 = multiply941
                else:
                    if prediction933 == 6:
                        _t1699 = self.parse_minus()
                        minus940 = _t1699
                        _t1698 = minus940
                    else:
                        if prediction933 == 5:
                            _t1701 = self.parse_add()
                            add939 = _t1701
                            _t1700 = add939
                        else:
                            if prediction933 == 4:
                                _t1703 = self.parse_gt_eq()
                                gt_eq938 = _t1703
                                _t1702 = gt_eq938
                            else:
                                if prediction933 == 3:
                                    _t1705 = self.parse_gt()
                                    gt937 = _t1705
                                    _t1704 = gt937
                                else:
                                    if prediction933 == 2:
                                        _t1707 = self.parse_lt_eq()
                                        lt_eq936 = _t1707
                                        _t1706 = lt_eq936
                                    else:
                                        if prediction933 == 1:
                                            _t1709 = self.parse_lt()
                                            lt935 = _t1709
                                            _t1708 = lt935
                                        else:
                                            if prediction933 == 0:
                                                _t1711 = self.parse_eq()
                                                eq934 = _t1711
                                                _t1710 = eq934
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1708 = _t1710
                                        _t1706 = _t1708
                                    _t1704 = _t1706
                                _t1702 = _t1704
                            _t1700 = _t1702
                        _t1698 = _t1700
                    _t1696 = _t1698
                _t1694 = _t1696
            _t1690 = _t1694
        result949 = _t1690
        self.record_span(span_start948, "Primitive")
        return result949

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start952 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1712 = self.parse_term()
        term950 = _t1712
        _t1713 = self.parse_term()
        term_3951 = _t1713
        self.consume_literal(")")
        _t1714 = logic_pb2.RelTerm(term=term950)
        _t1715 = logic_pb2.RelTerm(term=term_3951)
        _t1716 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1714, _t1715])
        result953 = _t1716
        self.record_span(span_start952, "Primitive")
        return result953

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start956 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1717 = self.parse_term()
        term954 = _t1717
        _t1718 = self.parse_term()
        term_3955 = _t1718
        self.consume_literal(")")
        _t1719 = logic_pb2.RelTerm(term=term954)
        _t1720 = logic_pb2.RelTerm(term=term_3955)
        _t1721 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1719, _t1720])
        result957 = _t1721
        self.record_span(span_start956, "Primitive")
        return result957

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start960 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1722 = self.parse_term()
        term958 = _t1722
        _t1723 = self.parse_term()
        term_3959 = _t1723
        self.consume_literal(")")
        _t1724 = logic_pb2.RelTerm(term=term958)
        _t1725 = logic_pb2.RelTerm(term=term_3959)
        _t1726 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1724, _t1725])
        result961 = _t1726
        self.record_span(span_start960, "Primitive")
        return result961

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start964 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1727 = self.parse_term()
        term962 = _t1727
        _t1728 = self.parse_term()
        term_3963 = _t1728
        self.consume_literal(")")
        _t1729 = logic_pb2.RelTerm(term=term962)
        _t1730 = logic_pb2.RelTerm(term=term_3963)
        _t1731 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1729, _t1730])
        result965 = _t1731
        self.record_span(span_start964, "Primitive")
        return result965

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start968 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1732 = self.parse_term()
        term966 = _t1732
        _t1733 = self.parse_term()
        term_3967 = _t1733
        self.consume_literal(")")
        _t1734 = logic_pb2.RelTerm(term=term966)
        _t1735 = logic_pb2.RelTerm(term=term_3967)
        _t1736 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1734, _t1735])
        result969 = _t1736
        self.record_span(span_start968, "Primitive")
        return result969

    def parse_add(self) -> logic_pb2.Primitive:
        span_start973 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1737 = self.parse_term()
        term970 = _t1737
        _t1738 = self.parse_term()
        term_3971 = _t1738
        _t1739 = self.parse_term()
        term_4972 = _t1739
        self.consume_literal(")")
        _t1740 = logic_pb2.RelTerm(term=term970)
        _t1741 = logic_pb2.RelTerm(term=term_3971)
        _t1742 = logic_pb2.RelTerm(term=term_4972)
        _t1743 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1740, _t1741, _t1742])
        result974 = _t1743
        self.record_span(span_start973, "Primitive")
        return result974

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start978 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1744 = self.parse_term()
        term975 = _t1744
        _t1745 = self.parse_term()
        term_3976 = _t1745
        _t1746 = self.parse_term()
        term_4977 = _t1746
        self.consume_literal(")")
        _t1747 = logic_pb2.RelTerm(term=term975)
        _t1748 = logic_pb2.RelTerm(term=term_3976)
        _t1749 = logic_pb2.RelTerm(term=term_4977)
        _t1750 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1747, _t1748, _t1749])
        result979 = _t1750
        self.record_span(span_start978, "Primitive")
        return result979

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start983 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1751 = self.parse_term()
        term980 = _t1751
        _t1752 = self.parse_term()
        term_3981 = _t1752
        _t1753 = self.parse_term()
        term_4982 = _t1753
        self.consume_literal(")")
        _t1754 = logic_pb2.RelTerm(term=term980)
        _t1755 = logic_pb2.RelTerm(term=term_3981)
        _t1756 = logic_pb2.RelTerm(term=term_4982)
        _t1757 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1754, _t1755, _t1756])
        result984 = _t1757
        self.record_span(span_start983, "Primitive")
        return result984

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start988 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1758 = self.parse_term()
        term985 = _t1758
        _t1759 = self.parse_term()
        term_3986 = _t1759
        _t1760 = self.parse_term()
        term_4987 = _t1760
        self.consume_literal(")")
        _t1761 = logic_pb2.RelTerm(term=term985)
        _t1762 = logic_pb2.RelTerm(term=term_3986)
        _t1763 = logic_pb2.RelTerm(term=term_4987)
        _t1764 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1761, _t1762, _t1763])
        result989 = _t1764
        self.record_span(span_start988, "Primitive")
        return result989

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start993 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1765 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1766 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1767 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1768 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1769 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1770 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1771 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1772 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1773 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1774 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1775 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1776 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1777 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1778 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1779 = 1
                                                                else:
                                                                    _t1779 = -1
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
                _t1766 = _t1767
            _t1765 = _t1766
        prediction990 = _t1765
        if prediction990 == 1:
            _t1781 = self.parse_term()
            term992 = _t1781
            _t1782 = logic_pb2.RelTerm(term=term992)
            _t1780 = _t1782
        else:
            if prediction990 == 0:
                _t1784 = self.parse_specialized_value()
                specialized_value991 = _t1784
                _t1785 = logic_pb2.RelTerm(specialized_value=specialized_value991)
                _t1783 = _t1785
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1780 = _t1783
        result994 = _t1780
        self.record_span(span_start993, "RelTerm")
        return result994

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start996 = self.span_start()
        self.consume_literal("#")
        _t1786 = self.parse_raw_value()
        raw_value995 = _t1786
        result997 = raw_value995
        self.record_span(span_start996, "Value")
        return result997

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start1003 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1787 = self.parse_name()
        name998 = _t1787
        xs999 = []
        cond1000 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond1000:
            _t1788 = self.parse_rel_term()
            item1001 = _t1788
            xs999.append(item1001)
            cond1000 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1002 = xs999
        self.consume_literal(")")
        _t1789 = logic_pb2.RelAtom(name=name998, terms=rel_terms1002)
        result1004 = _t1789
        self.record_span(span_start1003, "RelAtom")
        return result1004

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1007 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1790 = self.parse_term()
        term1005 = _t1790
        _t1791 = self.parse_term()
        term_31006 = _t1791
        self.consume_literal(")")
        _t1792 = logic_pb2.Cast(input=term1005, result=term_31006)
        result1008 = _t1792
        self.record_span(span_start1007, "Cast")
        return result1008

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1009 = []
        cond1010 = self.match_lookahead_literal("(", 0)
        while cond1010:
            _t1793 = self.parse_attribute()
            item1011 = _t1793
            xs1009.append(item1011)
            cond1010 = self.match_lookahead_literal("(", 0)
        attributes1012 = xs1009
        self.consume_literal(")")
        return attributes1012

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1018 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1794 = self.parse_name()
        name1013 = _t1794
        xs1014 = []
        cond1015 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1015:
            _t1795 = self.parse_raw_value()
            item1016 = _t1795
            xs1014.append(item1016)
            cond1015 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1017 = xs1014
        self.consume_literal(")")
        _t1796 = logic_pb2.Attribute(name=name1013, args=raw_values1017)
        result1019 = _t1796
        self.record_span(span_start1018, "Attribute")
        return result1019

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1025 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1020 = []
        cond1021 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1021:
            _t1797 = self.parse_relation_id()
            item1022 = _t1797
            xs1020.append(item1022)
            cond1021 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1023 = xs1020
        _t1798 = self.parse_script()
        script1024 = _t1798
        self.consume_literal(")")
        _t1799 = logic_pb2.Algorithm(body=script1024)
        getattr(_t1799, 'global').extend(relation_ids1023)
        result1026 = _t1799
        self.record_span(span_start1025, "Algorithm")
        return result1026

    def parse_script(self) -> logic_pb2.Script:
        span_start1031 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1027 = []
        cond1028 = self.match_lookahead_literal("(", 0)
        while cond1028:
            _t1800 = self.parse_construct()
            item1029 = _t1800
            xs1027.append(item1029)
            cond1028 = self.match_lookahead_literal("(", 0)
        constructs1030 = xs1027
        self.consume_literal(")")
        _t1801 = logic_pb2.Script(constructs=constructs1030)
        result1032 = _t1801
        self.record_span(span_start1031, "Script")
        return result1032

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1036 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1803 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1804 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1805 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1806 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1807 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1808 = 1
                                else:
                                    _t1808 = -1
                                _t1807 = _t1808
                            _t1806 = _t1807
                        _t1805 = _t1806
                    _t1804 = _t1805
                _t1803 = _t1804
            _t1802 = _t1803
        else:
            _t1802 = -1
        prediction1033 = _t1802
        if prediction1033 == 1:
            _t1810 = self.parse_instruction()
            instruction1035 = _t1810
            _t1811 = logic_pb2.Construct(instruction=instruction1035)
            _t1809 = _t1811
        else:
            if prediction1033 == 0:
                _t1813 = self.parse_loop()
                loop1034 = _t1813
                _t1814 = logic_pb2.Construct(loop=loop1034)
                _t1812 = _t1814
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1809 = _t1812
        result1037 = _t1809
        self.record_span(span_start1036, "Construct")
        return result1037

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1040 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1815 = self.parse_init()
        init1038 = _t1815
        _t1816 = self.parse_script()
        script1039 = _t1816
        self.consume_literal(")")
        _t1817 = logic_pb2.Loop(init=init1038, body=script1039)
        result1041 = _t1817
        self.record_span(span_start1040, "Loop")
        return result1041

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1042 = []
        cond1043 = self.match_lookahead_literal("(", 0)
        while cond1043:
            _t1818 = self.parse_instruction()
            item1044 = _t1818
            xs1042.append(item1044)
            cond1043 = self.match_lookahead_literal("(", 0)
        instructions1045 = xs1042
        self.consume_literal(")")
        return instructions1045

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1052 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1820 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1821 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1822 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1823 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1824 = 0
                            else:
                                _t1824 = -1
                            _t1823 = _t1824
                        _t1822 = _t1823
                    _t1821 = _t1822
                _t1820 = _t1821
            _t1819 = _t1820
        else:
            _t1819 = -1
        prediction1046 = _t1819
        if prediction1046 == 4:
            _t1826 = self.parse_monus_def()
            monus_def1051 = _t1826
            _t1827 = logic_pb2.Instruction(monus_def=monus_def1051)
            _t1825 = _t1827
        else:
            if prediction1046 == 3:
                _t1829 = self.parse_monoid_def()
                monoid_def1050 = _t1829
                _t1830 = logic_pb2.Instruction(monoid_def=monoid_def1050)
                _t1828 = _t1830
            else:
                if prediction1046 == 2:
                    _t1832 = self.parse_break()
                    break1049 = _t1832
                    _t1833 = logic_pb2.Instruction()
                    getattr(_t1833, 'break').CopyFrom(break1049)
                    _t1831 = _t1833
                else:
                    if prediction1046 == 1:
                        _t1835 = self.parse_upsert()
                        upsert1048 = _t1835
                        _t1836 = logic_pb2.Instruction(upsert=upsert1048)
                        _t1834 = _t1836
                    else:
                        if prediction1046 == 0:
                            _t1838 = self.parse_assign()
                            assign1047 = _t1838
                            _t1839 = logic_pb2.Instruction(assign=assign1047)
                            _t1837 = _t1839
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1834 = _t1837
                    _t1831 = _t1834
                _t1828 = _t1831
            _t1825 = _t1828
        result1053 = _t1825
        self.record_span(span_start1052, "Instruction")
        return result1053

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1057 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1840 = self.parse_relation_id()
        relation_id1054 = _t1840
        _t1841 = self.parse_abstraction()
        abstraction1055 = _t1841
        if self.match_lookahead_literal("(", 0):
            _t1843 = self.parse_attrs()
            _t1842 = _t1843
        else:
            _t1842 = None
        attrs1056 = _t1842
        self.consume_literal(")")
        _t1844 = logic_pb2.Assign(name=relation_id1054, body=abstraction1055, attrs=(attrs1056 if attrs1056 is not None else []))
        result1058 = _t1844
        self.record_span(span_start1057, "Assign")
        return result1058

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1062 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1845 = self.parse_relation_id()
        relation_id1059 = _t1845
        _t1846 = self.parse_abstraction_with_arity()
        abstraction_with_arity1060 = _t1846
        if self.match_lookahead_literal("(", 0):
            _t1848 = self.parse_attrs()
            _t1847 = _t1848
        else:
            _t1847 = None
        attrs1061 = _t1847
        self.consume_literal(")")
        _t1849 = logic_pb2.Upsert(name=relation_id1059, body=abstraction_with_arity1060[0], attrs=(attrs1061 if attrs1061 is not None else []), value_arity=abstraction_with_arity1060[1])
        result1063 = _t1849
        self.record_span(span_start1062, "Upsert")
        return result1063

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1850 = self.parse_bindings()
        bindings1064 = _t1850
        _t1851 = self.parse_formula()
        formula1065 = _t1851
        self.consume_literal(")")
        _t1852 = logic_pb2.Abstraction(vars=(list(bindings1064[0]) + list(bindings1064[1] if bindings1064[1] is not None else [])), value=formula1065)
        return (_t1852, len(bindings1064[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1069 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1853 = self.parse_relation_id()
        relation_id1066 = _t1853
        _t1854 = self.parse_abstraction()
        abstraction1067 = _t1854
        if self.match_lookahead_literal("(", 0):
            _t1856 = self.parse_attrs()
            _t1855 = _t1856
        else:
            _t1855 = None
        attrs1068 = _t1855
        self.consume_literal(")")
        _t1857 = logic_pb2.Break(name=relation_id1066, body=abstraction1067, attrs=(attrs1068 if attrs1068 is not None else []))
        result1070 = _t1857
        self.record_span(span_start1069, "Break")
        return result1070

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1075 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1858 = self.parse_monoid()
        monoid1071 = _t1858
        _t1859 = self.parse_relation_id()
        relation_id1072 = _t1859
        _t1860 = self.parse_abstraction_with_arity()
        abstraction_with_arity1073 = _t1860
        if self.match_lookahead_literal("(", 0):
            _t1862 = self.parse_attrs()
            _t1861 = _t1862
        else:
            _t1861 = None
        attrs1074 = _t1861
        self.consume_literal(")")
        _t1863 = logic_pb2.MonoidDef(monoid=monoid1071, name=relation_id1072, body=abstraction_with_arity1073[0], attrs=(attrs1074 if attrs1074 is not None else []), value_arity=abstraction_with_arity1073[1])
        result1076 = _t1863
        self.record_span(span_start1075, "MonoidDef")
        return result1076

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1082 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1865 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1866 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1867 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1868 = 2
                        else:
                            _t1868 = -1
                        _t1867 = _t1868
                    _t1866 = _t1867
                _t1865 = _t1866
            _t1864 = _t1865
        else:
            _t1864 = -1
        prediction1077 = _t1864
        if prediction1077 == 3:
            _t1870 = self.parse_sum_monoid()
            sum_monoid1081 = _t1870
            _t1871 = logic_pb2.Monoid(sum_monoid=sum_monoid1081)
            _t1869 = _t1871
        else:
            if prediction1077 == 2:
                _t1873 = self.parse_max_monoid()
                max_monoid1080 = _t1873
                _t1874 = logic_pb2.Monoid(max_monoid=max_monoid1080)
                _t1872 = _t1874
            else:
                if prediction1077 == 1:
                    _t1876 = self.parse_min_monoid()
                    min_monoid1079 = _t1876
                    _t1877 = logic_pb2.Monoid(min_monoid=min_monoid1079)
                    _t1875 = _t1877
                else:
                    if prediction1077 == 0:
                        _t1879 = self.parse_or_monoid()
                        or_monoid1078 = _t1879
                        _t1880 = logic_pb2.Monoid(or_monoid=or_monoid1078)
                        _t1878 = _t1880
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1875 = _t1878
                _t1872 = _t1875
            _t1869 = _t1872
        result1083 = _t1869
        self.record_span(span_start1082, "Monoid")
        return result1083

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1084 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1881 = logic_pb2.OrMonoid()
        result1085 = _t1881
        self.record_span(span_start1084, "OrMonoid")
        return result1085

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1087 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1882 = self.parse_type()
        type1086 = _t1882
        self.consume_literal(")")
        _t1883 = logic_pb2.MinMonoid(type=type1086)
        result1088 = _t1883
        self.record_span(span_start1087, "MinMonoid")
        return result1088

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1090 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1884 = self.parse_type()
        type1089 = _t1884
        self.consume_literal(")")
        _t1885 = logic_pb2.MaxMonoid(type=type1089)
        result1091 = _t1885
        self.record_span(span_start1090, "MaxMonoid")
        return result1091

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1093 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1886 = self.parse_type()
        type1092 = _t1886
        self.consume_literal(")")
        _t1887 = logic_pb2.SumMonoid(type=type1092)
        result1094 = _t1887
        self.record_span(span_start1093, "SumMonoid")
        return result1094

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1099 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1888 = self.parse_monoid()
        monoid1095 = _t1888
        _t1889 = self.parse_relation_id()
        relation_id1096 = _t1889
        _t1890 = self.parse_abstraction_with_arity()
        abstraction_with_arity1097 = _t1890
        if self.match_lookahead_literal("(", 0):
            _t1892 = self.parse_attrs()
            _t1891 = _t1892
        else:
            _t1891 = None
        attrs1098 = _t1891
        self.consume_literal(")")
        _t1893 = logic_pb2.MonusDef(monoid=monoid1095, name=relation_id1096, body=abstraction_with_arity1097[0], attrs=(attrs1098 if attrs1098 is not None else []), value_arity=abstraction_with_arity1097[1])
        result1100 = _t1893
        self.record_span(span_start1099, "MonusDef")
        return result1100

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1105 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1894 = self.parse_relation_id()
        relation_id1101 = _t1894
        _t1895 = self.parse_abstraction()
        abstraction1102 = _t1895
        _t1896 = self.parse_functional_dependency_keys()
        functional_dependency_keys1103 = _t1896
        _t1897 = self.parse_functional_dependency_values()
        functional_dependency_values1104 = _t1897
        self.consume_literal(")")
        _t1898 = logic_pb2.FunctionalDependency(guard=abstraction1102, keys=functional_dependency_keys1103, values=functional_dependency_values1104)
        _t1899 = logic_pb2.Constraint(name=relation_id1101, functional_dependency=_t1898)
        result1106 = _t1899
        self.record_span(span_start1105, "Constraint")
        return result1106

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1107 = []
        cond1108 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1108:
            _t1900 = self.parse_var()
            item1109 = _t1900
            xs1107.append(item1109)
            cond1108 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1110 = xs1107
        self.consume_literal(")")
        return vars1110

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1111 = []
        cond1112 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1112:
            _t1901 = self.parse_var()
            item1113 = _t1901
            xs1111.append(item1113)
            cond1112 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1114 = xs1111
        self.consume_literal(")")
        return vars1114

    def parse_data(self) -> logic_pb2.Data:
        span_start1120 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1903 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1904 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t1905 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t1906 = 1
                        else:
                            _t1906 = -1
                        _t1905 = _t1906
                    _t1904 = _t1905
                _t1903 = _t1904
            _t1902 = _t1903
        else:
            _t1902 = -1
        prediction1115 = _t1902
        if prediction1115 == 3:
            _t1908 = self.parse_iceberg_data()
            iceberg_data1119 = _t1908
            _t1909 = logic_pb2.Data(iceberg_data=iceberg_data1119)
            _t1907 = _t1909
        else:
            if prediction1115 == 2:
                _t1911 = self.parse_csv_data()
                csv_data1118 = _t1911
                _t1912 = logic_pb2.Data(csv_data=csv_data1118)
                _t1910 = _t1912
            else:
                if prediction1115 == 1:
                    _t1914 = self.parse_betree_relation()
                    betree_relation1117 = _t1914
                    _t1915 = logic_pb2.Data(betree_relation=betree_relation1117)
                    _t1913 = _t1915
                else:
                    if prediction1115 == 0:
                        _t1917 = self.parse_edb()
                        edb1116 = _t1917
                        _t1918 = logic_pb2.Data(edb=edb1116)
                        _t1916 = _t1918
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1913 = _t1916
                _t1910 = _t1913
            _t1907 = _t1910
        result1121 = _t1907
        self.record_span(span_start1120, "Data")
        return result1121

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1125 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1919 = self.parse_relation_id()
        relation_id1122 = _t1919
        _t1920 = self.parse_edb_path()
        edb_path1123 = _t1920
        _t1921 = self.parse_edb_types()
        edb_types1124 = _t1921
        self.consume_literal(")")
        _t1922 = logic_pb2.EDB(target_id=relation_id1122, path=edb_path1123, types=edb_types1124)
        result1126 = _t1922
        self.record_span(span_start1125, "EDB")
        return result1126

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1127 = []
        cond1128 = self.match_lookahead_terminal("STRING", 0)
        while cond1128:
            item1129 = self.consume_terminal("STRING")
            xs1127.append(item1129)
            cond1128 = self.match_lookahead_terminal("STRING", 0)
        strings1130 = xs1127
        self.consume_literal("]")
        return strings1130

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1131 = []
        cond1132 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1132:
            _t1923 = self.parse_type()
            item1133 = _t1923
            xs1131.append(item1133)
            cond1132 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1134 = xs1131
        self.consume_literal("]")
        return types1134

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1137 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1924 = self.parse_relation_id()
        relation_id1135 = _t1924
        _t1925 = self.parse_betree_info()
        betree_info1136 = _t1925
        self.consume_literal(")")
        _t1926 = logic_pb2.BeTreeRelation(name=relation_id1135, relation_info=betree_info1136)
        result1138 = _t1926
        self.record_span(span_start1137, "BeTreeRelation")
        return result1138

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1142 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1927 = self.parse_betree_info_key_types()
        betree_info_key_types1139 = _t1927
        _t1928 = self.parse_betree_info_value_types()
        betree_info_value_types1140 = _t1928
        _t1929 = self.parse_config_dict()
        config_dict1141 = _t1929
        self.consume_literal(")")
        _t1930 = self.construct_betree_info(betree_info_key_types1139, betree_info_value_types1140, config_dict1141)
        result1143 = _t1930
        self.record_span(span_start1142, "BeTreeInfo")
        return result1143

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1144 = []
        cond1145 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1145:
            _t1931 = self.parse_type()
            item1146 = _t1931
            xs1144.append(item1146)
            cond1145 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1147 = xs1144
        self.consume_literal(")")
        return types1147

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1148 = []
        cond1149 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1149:
            _t1932 = self.parse_type()
            item1150 = _t1932
            xs1148.append(item1150)
            cond1149 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1151 = xs1148
        self.consume_literal(")")
        return types1151

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1156 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1933 = self.parse_csvlocator()
        csvlocator1152 = _t1933
        _t1934 = self.parse_csv_config()
        csv_config1153 = _t1934
        _t1935 = self.parse_gnf_columns()
        gnf_columns1154 = _t1935
        _t1936 = self.parse_csv_asof()
        csv_asof1155 = _t1936
        self.consume_literal(")")
        _t1937 = logic_pb2.CSVData(locator=csvlocator1152, config=csv_config1153, columns=gnf_columns1154, asof=csv_asof1155)
        result1157 = _t1937
        self.record_span(span_start1156, "CSVData")
        return result1157

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1160 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1939 = self.parse_csv_locator_paths()
            _t1938 = _t1939
        else:
            _t1938 = None
        csv_locator_paths1158 = _t1938
        if self.match_lookahead_literal("(", 0):
            _t1941 = self.parse_csv_locator_inline_data()
            _t1940 = _t1941
        else:
            _t1940 = None
        csv_locator_inline_data1159 = _t1940
        self.consume_literal(")")
        _t1942 = logic_pb2.CSVLocator(paths=(csv_locator_paths1158 if csv_locator_paths1158 is not None else []), inline_data=(csv_locator_inline_data1159 if csv_locator_inline_data1159 is not None else "").encode())
        result1161 = _t1942
        self.record_span(span_start1160, "CSVLocator")
        return result1161

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1162 = []
        cond1163 = self.match_lookahead_terminal("STRING", 0)
        while cond1163:
            item1164 = self.consume_terminal("STRING")
            xs1162.append(item1164)
            cond1163 = self.match_lookahead_terminal("STRING", 0)
        strings1165 = xs1162
        self.consume_literal(")")
        return strings1165

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1166 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1166

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1168 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1943 = self.parse_config_dict()
        config_dict1167 = _t1943
        self.consume_literal(")")
        _t1944 = self.construct_csv_config(config_dict1167)
        result1169 = _t1944
        self.record_span(span_start1168, "CSVConfig")
        return result1169

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1170 = []
        cond1171 = self.match_lookahead_literal("(", 0)
        while cond1171:
            _t1945 = self.parse_gnf_column()
            item1172 = _t1945
            xs1170.append(item1172)
            cond1171 = self.match_lookahead_literal("(", 0)
        gnf_columns1173 = xs1170
        self.consume_literal(")")
        return gnf_columns1173

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1180 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1946 = self.parse_gnf_column_path()
        gnf_column_path1174 = _t1946
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1948 = self.parse_relation_id()
            _t1947 = _t1948
        else:
            _t1947 = None
        relation_id1175 = _t1947
        self.consume_literal("[")
        xs1176 = []
        cond1177 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1177:
            _t1949 = self.parse_type()
            item1178 = _t1949
            xs1176.append(item1178)
            cond1177 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1179 = xs1176
        self.consume_literal("]")
        self.consume_literal(")")
        _t1950 = logic_pb2.GNFColumn(column_path=gnf_column_path1174, target_id=relation_id1175, types=types1179)
        result1181 = _t1950
        self.record_span(span_start1180, "GNFColumn")
        return result1181

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1951 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1952 = 0
            else:
                _t1952 = -1
            _t1951 = _t1952
        prediction1182 = _t1951
        if prediction1182 == 1:
            self.consume_literal("[")
            xs1184 = []
            cond1185 = self.match_lookahead_terminal("STRING", 0)
            while cond1185:
                item1186 = self.consume_terminal("STRING")
                xs1184.append(item1186)
                cond1185 = self.match_lookahead_terminal("STRING", 0)
            strings1187 = xs1184
            self.consume_literal("]")
            _t1953 = strings1187
        else:
            if prediction1182 == 0:
                string1183 = self.consume_terminal("STRING")
                _t1954 = [string1183]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1953 = _t1954
        return _t1953

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1188 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1188

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1193 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t1955 = self.parse_iceberg_locator()
        iceberg_locator1189 = _t1955
        _t1956 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1190 = _t1956
        _t1957 = self.parse_gnf_columns()
        gnf_columns1191 = _t1957
        if self.match_lookahead_literal("(", 0):
            _t1959 = self.parse_iceberg_to_snapshot()
            _t1958 = _t1959
        else:
            _t1958 = None
        iceberg_to_snapshot1192 = _t1958
        self.consume_literal(")")
        _t1960 = logic_pb2.IcebergData(locator=iceberg_locator1189, config=iceberg_catalog_config1190, columns=gnf_columns1191, to_snapshot=(iceberg_to_snapshot1192 if iceberg_to_snapshot1192 is not None else ""))
        result1194 = _t1960
        self.record_span(span_start1193, "IcebergData")
        return result1194

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1201 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1195 = self.consume_terminal("STRING")
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1196 = []
        cond1197 = self.match_lookahead_terminal("STRING", 0)
        while cond1197:
            item1198 = self.consume_terminal("STRING")
            xs1196.append(item1198)
            cond1197 = self.match_lookahead_terminal("STRING", 0)
        strings1199 = xs1196
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string_121200 = self.consume_terminal("STRING")
        self.consume_literal(")")
        self.consume_literal(")")
        _t1961 = logic_pb2.IcebergLocator(table_name=string1195, namespace=strings1199, warehouse=string_121200)
        result1202 = _t1961
        self.record_span(span_start1201, "IcebergLocator")
        return result1202

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1213 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1203 = self.consume_terminal("STRING")
        self.consume_literal(")")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t1963 = self.parse_iceberg_catalog_config_scope()
            _t1962 = _t1963
        else:
            _t1962 = None
        iceberg_catalog_config_scope1204 = _t1962
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1205 = []
        cond1206 = self.match_lookahead_literal("(", 0)
        while cond1206:
            _t1964 = self.parse_iceberg_property_entry()
            item1207 = _t1964
            xs1205.append(item1207)
            cond1206 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1208 = xs1205
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1209 = []
        cond1210 = self.match_lookahead_literal("(", 0)
        while cond1210:
            _t1965 = self.parse_iceberg_property_entry()
            item1211 = _t1965
            xs1209.append(item1211)
            cond1210 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys_131212 = xs1209
        self.consume_literal(")")
        self.consume_literal(")")
        _t1966 = self.construct_iceberg_catalog_config(string1203, iceberg_catalog_config_scope1204, iceberg_property_entrys1208, iceberg_property_entrys_131212)
        result1214 = _t1966
        self.record_span(span_start1213, "IcebergCatalogConfig")
        return result1214

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1215 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1215

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1216 = self.consume_terminal("STRING")
        string_31217 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1216, string_31217,)

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1218 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1218

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1220 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1967 = self.parse_fragment_id()
        fragment_id1219 = _t1967
        self.consume_literal(")")
        _t1968 = transactions_pb2.Undefine(fragment_id=fragment_id1219)
        result1221 = _t1968
        self.record_span(span_start1220, "Undefine")
        return result1221

    def parse_context(self) -> transactions_pb2.Context:
        span_start1226 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1222 = []
        cond1223 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1223:
            _t1969 = self.parse_relation_id()
            item1224 = _t1969
            xs1222.append(item1224)
            cond1223 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1225 = xs1222
        self.consume_literal(")")
        _t1970 = transactions_pb2.Context(relations=relation_ids1225)
        result1227 = _t1970
        self.record_span(span_start1226, "Context")
        return result1227

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1232 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        xs1228 = []
        cond1229 = self.match_lookahead_literal("[", 0)
        while cond1229:
            _t1971 = self.parse_snapshot_mapping()
            item1230 = _t1971
            xs1228.append(item1230)
            cond1229 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1231 = xs1228
        self.consume_literal(")")
        _t1972 = transactions_pb2.Snapshot(mappings=snapshot_mappings1231)
        result1233 = _t1972
        self.record_span(span_start1232, "Snapshot")
        return result1233

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1236 = self.span_start()
        _t1973 = self.parse_edb_path()
        edb_path1234 = _t1973
        _t1974 = self.parse_relation_id()
        relation_id1235 = _t1974
        _t1975 = transactions_pb2.SnapshotMapping(destination_path=edb_path1234, source_relation=relation_id1235)
        result1237 = _t1975
        self.record_span(span_start1236, "SnapshotMapping")
        return result1237

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1238 = []
        cond1239 = self.match_lookahead_literal("(", 0)
        while cond1239:
            _t1976 = self.parse_read()
            item1240 = _t1976
            xs1238.append(item1240)
            cond1239 = self.match_lookahead_literal("(", 0)
        reads1241 = xs1238
        self.consume_literal(")")
        return reads1241

    def parse_read(self) -> transactions_pb2.Read:
        span_start1248 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1978 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1979 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t1980 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t1981 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t1982 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t1983 = 3
                                else:
                                    _t1983 = -1
                                _t1982 = _t1983
                            _t1981 = _t1982
                        _t1980 = _t1981
                    _t1979 = _t1980
                _t1978 = _t1979
            _t1977 = _t1978
        else:
            _t1977 = -1
        prediction1242 = _t1977
        if prediction1242 == 4:
            _t1985 = self.parse_export()
            export1247 = _t1985
            _t1986 = transactions_pb2.Read(export=export1247)
            _t1984 = _t1986
        else:
            if prediction1242 == 3:
                _t1988 = self.parse_abort()
                abort1246 = _t1988
                _t1989 = transactions_pb2.Read(abort=abort1246)
                _t1987 = _t1989
            else:
                if prediction1242 == 2:
                    _t1991 = self.parse_what_if()
                    what_if1245 = _t1991
                    _t1992 = transactions_pb2.Read(what_if=what_if1245)
                    _t1990 = _t1992
                else:
                    if prediction1242 == 1:
                        _t1994 = self.parse_output()
                        output1244 = _t1994
                        _t1995 = transactions_pb2.Read(output=output1244)
                        _t1993 = _t1995
                    else:
                        if prediction1242 == 0:
                            _t1997 = self.parse_demand()
                            demand1243 = _t1997
                            _t1998 = transactions_pb2.Read(demand=demand1243)
                            _t1996 = _t1998
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1993 = _t1996
                    _t1990 = _t1993
                _t1987 = _t1990
            _t1984 = _t1987
        result1249 = _t1984
        self.record_span(span_start1248, "Read")
        return result1249

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1251 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1999 = self.parse_relation_id()
        relation_id1250 = _t1999
        self.consume_literal(")")
        _t2000 = transactions_pb2.Demand(relation_id=relation_id1250)
        result1252 = _t2000
        self.record_span(span_start1251, "Demand")
        return result1252

    def parse_output(self) -> transactions_pb2.Output:
        span_start1255 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2001 = self.parse_name()
        name1253 = _t2001
        _t2002 = self.parse_relation_id()
        relation_id1254 = _t2002
        self.consume_literal(")")
        _t2003 = transactions_pb2.Output(name=name1253, relation_id=relation_id1254)
        result1256 = _t2003
        self.record_span(span_start1255, "Output")
        return result1256

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1259 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2004 = self.parse_name()
        name1257 = _t2004
        _t2005 = self.parse_epoch()
        epoch1258 = _t2005
        self.consume_literal(")")
        _t2006 = transactions_pb2.WhatIf(branch=name1257, epoch=epoch1258)
        result1260 = _t2006
        self.record_span(span_start1259, "WhatIf")
        return result1260

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1263 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2008 = self.parse_name()
            _t2007 = _t2008
        else:
            _t2007 = None
        name1261 = _t2007
        _t2009 = self.parse_relation_id()
        relation_id1262 = _t2009
        self.consume_literal(")")
        _t2010 = transactions_pb2.Abort(name=(name1261 if name1261 is not None else "abort"), relation_id=relation_id1262)
        result1264 = _t2010
        self.record_span(span_start1263, "Abort")
        return result1264

    def parse_export(self) -> transactions_pb2.Export:
        span_start1268 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2012 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2013 = 0
                else:
                    _t2013 = -1
                _t2012 = _t2013
            _t2011 = _t2012
        else:
            _t2011 = -1
        prediction1265 = _t2011
        if prediction1265 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2015 = self.parse_export_iceberg_config()
            export_iceberg_config1267 = _t2015
            self.consume_literal(")")
            _t2016 = transactions_pb2.Export(iceberg_config=export_iceberg_config1267)
            _t2014 = _t2016
        else:
            if prediction1265 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2018 = self.parse_export_csv_config()
                export_csv_config1266 = _t2018
                self.consume_literal(")")
                _t2019 = transactions_pb2.Export(csv_config=export_csv_config1266)
                _t2017 = _t2019
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2014 = _t2017
        result1269 = _t2014
        self.record_span(span_start1268, "Export")
        return result1269

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1277 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2021 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2022 = 1
                else:
                    _t2022 = -1
                _t2021 = _t2022
            _t2020 = _t2021
        else:
            _t2020 = -1
        prediction1270 = _t2020
        if prediction1270 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2024 = self.parse_export_csv_path()
            export_csv_path1274 = _t2024
            _t2025 = self.parse_export_csv_columns_list()
            export_csv_columns_list1275 = _t2025
            _t2026 = self.parse_config_dict()
            config_dict1276 = _t2026
            self.consume_literal(")")
            _t2027 = self.construct_export_csv_config(export_csv_path1274, export_csv_columns_list1275, config_dict1276)
            _t2023 = _t2027
        else:
            if prediction1270 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2029 = self.parse_export_csv_path()
                export_csv_path1271 = _t2029
                _t2030 = self.parse_export_csv_source()
                export_csv_source1272 = _t2030
                _t2031 = self.parse_csv_config()
                csv_config1273 = _t2031
                self.consume_literal(")")
                _t2032 = self.construct_export_csv_config_with_source(export_csv_path1271, export_csv_source1272, csv_config1273)
                _t2028 = _t2032
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2023 = _t2028
        result1278 = _t2023
        self.record_span(span_start1277, "ExportCSVConfig")
        return result1278

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1279 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1279

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1286 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2034 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2035 = 0
                else:
                    _t2035 = -1
                _t2034 = _t2035
            _t2033 = _t2034
        else:
            _t2033 = -1
        prediction1280 = _t2033
        if prediction1280 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2037 = self.parse_relation_id()
            relation_id1285 = _t2037
            self.consume_literal(")")
            _t2038 = transactions_pb2.ExportCSVSource(table_def=relation_id1285)
            _t2036 = _t2038
        else:
            if prediction1280 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1281 = []
                cond1282 = self.match_lookahead_literal("(", 0)
                while cond1282:
                    _t2040 = self.parse_export_csv_column()
                    item1283 = _t2040
                    xs1281.append(item1283)
                    cond1282 = self.match_lookahead_literal("(", 0)
                export_csv_columns1284 = xs1281
                self.consume_literal(")")
                _t2041 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1284)
                _t2042 = transactions_pb2.ExportCSVSource(gnf_columns=_t2041)
                _t2039 = _t2042
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2036 = _t2039
        result1287 = _t2036
        self.record_span(span_start1286, "ExportCSVSource")
        return result1287

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1290 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1288 = self.consume_terminal("STRING")
        _t2043 = self.parse_relation_id()
        relation_id1289 = _t2043
        self.consume_literal(")")
        _t2044 = transactions_pb2.ExportCSVColumn(column_name=string1288, column_data=relation_id1289)
        result1291 = _t2044
        self.record_span(span_start1290, "ExportCSVColumn")
        return result1291

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1292 = []
        cond1293 = self.match_lookahead_literal("(", 0)
        while cond1293:
            _t2045 = self.parse_export_csv_column()
            item1294 = _t2045
            xs1292.append(item1294)
            cond1293 = self.match_lookahead_literal("(", 0)
        export_csv_columns1295 = xs1292
        self.consume_literal(")")
        return export_csv_columns1295

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1304 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2046 = self.parse_iceberg_locator()
        iceberg_locator1296 = _t2046
        _t2047 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1297 = _t2047
        _t2048 = self.parse_export_iceberg_columns()
        export_iceberg_columns1298 = _t2048
        self.consume_literal("(")
        self.consume_literal("table_properties")
        xs1299 = []
        cond1300 = self.match_lookahead_literal("(", 0)
        while cond1300:
            _t2049 = self.parse_iceberg_property_entry()
            item1301 = _t2049
            xs1299.append(item1301)
            cond1300 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1302 = xs1299
        self.consume_literal(")")
        if self.match_lookahead_literal("{", 0):
            _t2051 = self.parse_config_dict()
            _t2050 = _t2051
        else:
            _t2050 = None
        config_dict1303 = _t2050
        self.consume_literal(")")
        _t2052 = self.construct_export_iceberg_config_full(iceberg_locator1296, iceberg_catalog_config1297, export_iceberg_columns1298, iceberg_property_entrys1302, config_dict1303)
        result1305 = _t2052
        self.record_span(span_start1304, "ExportIcebergConfig")
        return result1305

    def parse_export_iceberg_columns(self) -> transactions_pb2.ExportIcebergColumns:
        span_start1311 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("columns")
        self.consume_literal("(")
        self.consume_literal("source_table_def")
        _t2053 = self.parse_relation_id()
        relation_id1306 = _t2053
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("target_columns")
        xs1307 = []
        cond1308 = self.match_lookahead_literal("(", 0)
        while cond1308:
            _t2054 = self.parse_export_iceberg_column()
            item1309 = _t2054
            xs1307.append(item1309)
            cond1308 = self.match_lookahead_literal("(", 0)
        export_iceberg_columns1310 = xs1307
        self.consume_literal(")")
        self.consume_literal(")")
        _t2055 = transactions_pb2.ExportIcebergColumns(source_table_def=relation_id1306, target_columns=export_iceberg_columns1310)
        result1312 = _t2055
        self.record_span(span_start1311, "ExportIcebergColumns")
        return result1312

    def parse_export_iceberg_column(self) -> transactions_pb2.ExportIcebergColumn:
        span_start1316 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_column")
        string1313 = self.consume_terminal("STRING")
        _t2056 = self.parse_type()
        type1314 = _t2056
        _t2057 = self.parse_boolean_value()
        boolean_value1315 = _t2057
        self.consume_literal(")")
        _t2058 = transactions_pb2.ExportIcebergColumn(name=string1313, type=type1314, nullable=boolean_value1315)
        result1317 = _t2058
        self.record_span(span_start1316, "ExportIcebergColumn")
        return result1317


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
