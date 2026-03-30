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
            _t2048 = value.HasField("int32_value")
        else:
            _t2048 = False
        if _t2048:
            assert value is not None
            return value.int32_value
        else:
            _t2049 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2050 = value.HasField("int_value")
        else:
            _t2050 = False
        if _t2050:
            assert value is not None
            return value.int_value
        else:
            _t2051 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2052 = value.HasField("string_value")
        else:
            _t2052 = False
        if _t2052:
            assert value is not None
            return value.string_value
        else:
            _t2053 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2054 = value.HasField("boolean_value")
        else:
            _t2054 = False
        if _t2054:
            assert value is not None
            return value.boolean_value
        else:
            _t2055 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2056 = value.HasField("string_value")
        else:
            _t2056 = False
        if _t2056:
            assert value is not None
            return [value.string_value]
        else:
            _t2057 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t2058 = value.HasField("int_value")
        else:
            _t2058 = False
        if _t2058:
            assert value is not None
            return value.int_value
        else:
            _t2059 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2060 = value.HasField("float_value")
        else:
            _t2060 = False
        if _t2060:
            assert value is not None
            return value.float_value
        else:
            _t2061 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2062 = value.HasField("string_value")
        else:
            _t2062 = False
        if _t2062:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2063 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2064 = value.HasField("uint128_value")
        else:
            _t2064 = False
        if _t2064:
            assert value is not None
            return value.uint128_value
        else:
            _t2065 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2066 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2066
        _t2067 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2067
        _t2068 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2068
        _t2069 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2069
        _t2070 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2070
        _t2071 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2071
        _t2072 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2072
        _t2073 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2073
        _t2074 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2074
        _t2075 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2075
        _t2076 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t2076
        _t2077 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2077
        _t2078 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t2078

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2079 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2079
        _t2080 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2080
        _t2081 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2081
        _t2082 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2082
        _t2083 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2083
        _t2084 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2084
        _t2085 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2085
        _t2086 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2086
        _t2087 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2087
        _t2088 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2088
        _t2089 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2089

    def default_configure(self) -> transactions_pb2.Configure:
        _t2090 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2090
        _t2091 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2091

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
        _t2092 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2092
        _t2093 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2093
        _t2094 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t2094

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2095 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2095
        _t2096 = self._extract_value_string(config.get("compression"), "")
        compression = _t2096
        _t2097 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2097
        _t2098 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2098
        _t2099 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2099
        _t2100 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2100
        _t2101 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2101
        _t2102 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2102

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2103 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t2103

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2104 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2104

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, table_def: logic_pb2.RelationId, columns: Sequence[transactions_pb2.ExportIcebergColumn], table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2105 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2105
        _t2106 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2106
        _t2107 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2107
        table_props = dict(table_property_pairs)
        _t2108 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, columns=columns, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2108

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start661 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1311 = self.parse_configure()
            _t1310 = _t1311
        else:
            _t1310 = None
        configure655 = _t1310
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1313 = self.parse_sync()
            _t1312 = _t1313
        else:
            _t1312 = None
        sync656 = _t1312
        xs657 = []
        cond658 = self.match_lookahead_literal("(", 0)
        while cond658:
            _t1314 = self.parse_epoch()
            item659 = _t1314
            xs657.append(item659)
            cond658 = self.match_lookahead_literal("(", 0)
        epochs660 = xs657
        self.consume_literal(")")
        _t1315 = self.default_configure()
        _t1316 = transactions_pb2.Transaction(epochs=epochs660, configure=(configure655 if configure655 is not None else _t1315), sync=sync656)
        result662 = _t1316
        self.record_span(span_start661, "Transaction")
        return result662

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start664 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1317 = self.parse_config_dict()
        config_dict663 = _t1317
        self.consume_literal(")")
        _t1318 = self.construct_configure(config_dict663)
        result665 = _t1318
        self.record_span(span_start664, "Configure")
        return result665

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs666 = []
        cond667 = self.match_lookahead_literal(":", 0)
        while cond667:
            _t1319 = self.parse_config_key_value()
            item668 = _t1319
            xs666.append(item668)
            cond667 = self.match_lookahead_literal(":", 0)
        config_key_values669 = xs666
        self.consume_literal("}")
        return config_key_values669

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol670 = self.consume_terminal("SYMBOL")
        _t1320 = self.parse_raw_value()
        raw_value671 = _t1320
        return (symbol670, raw_value671,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start685 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1321 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1322 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1323 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1325 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1326 = 0
                            else:
                                _t1326 = -1
                            _t1325 = _t1326
                        _t1324 = _t1325
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1327 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1328 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1329 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1330 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1331 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1332 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1333 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1334 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1335 = 10
                                                        else:
                                                            _t1335 = -1
                                                        _t1334 = _t1335
                                                    _t1333 = _t1334
                                                _t1332 = _t1333
                                            _t1331 = _t1332
                                        _t1330 = _t1331
                                    _t1329 = _t1330
                                _t1328 = _t1329
                            _t1327 = _t1328
                        _t1324 = _t1327
                    _t1323 = _t1324
                _t1322 = _t1323
            _t1321 = _t1322
        prediction672 = _t1321
        if prediction672 == 12:
            _t1337 = self.parse_boolean_value()
            boolean_value684 = _t1337
            _t1338 = logic_pb2.Value(boolean_value=boolean_value684)
            _t1336 = _t1338
        else:
            if prediction672 == 11:
                self.consume_literal("missing")
                _t1340 = logic_pb2.MissingValue()
                _t1341 = logic_pb2.Value(missing_value=_t1340)
                _t1339 = _t1341
            else:
                if prediction672 == 10:
                    decimal683 = self.consume_terminal("DECIMAL")
                    _t1343 = logic_pb2.Value(decimal_value=decimal683)
                    _t1342 = _t1343
                else:
                    if prediction672 == 9:
                        int128682 = self.consume_terminal("INT128")
                        _t1345 = logic_pb2.Value(int128_value=int128682)
                        _t1344 = _t1345
                    else:
                        if prediction672 == 8:
                            uint128681 = self.consume_terminal("UINT128")
                            _t1347 = logic_pb2.Value(uint128_value=uint128681)
                            _t1346 = _t1347
                        else:
                            if prediction672 == 7:
                                uint32680 = self.consume_terminal("UINT32")
                                _t1349 = logic_pb2.Value(uint32_value=uint32680)
                                _t1348 = _t1349
                            else:
                                if prediction672 == 6:
                                    float679 = self.consume_terminal("FLOAT")
                                    _t1351 = logic_pb2.Value(float_value=float679)
                                    _t1350 = _t1351
                                else:
                                    if prediction672 == 5:
                                        float32678 = self.consume_terminal("FLOAT32")
                                        _t1353 = logic_pb2.Value(float32_value=float32678)
                                        _t1352 = _t1353
                                    else:
                                        if prediction672 == 4:
                                            int677 = self.consume_terminal("INT")
                                            _t1355 = logic_pb2.Value(int_value=int677)
                                            _t1354 = _t1355
                                        else:
                                            if prediction672 == 3:
                                                int32676 = self.consume_terminal("INT32")
                                                _t1357 = logic_pb2.Value(int32_value=int32676)
                                                _t1356 = _t1357
                                            else:
                                                if prediction672 == 2:
                                                    string675 = self.consume_terminal("STRING")
                                                    _t1359 = logic_pb2.Value(string_value=string675)
                                                    _t1358 = _t1359
                                                else:
                                                    if prediction672 == 1:
                                                        _t1361 = self.parse_raw_datetime()
                                                        raw_datetime674 = _t1361
                                                        _t1362 = logic_pb2.Value(datetime_value=raw_datetime674)
                                                        _t1360 = _t1362
                                                    else:
                                                        if prediction672 == 0:
                                                            _t1364 = self.parse_raw_date()
                                                            raw_date673 = _t1364
                                                            _t1365 = logic_pb2.Value(date_value=raw_date673)
                                                            _t1363 = _t1365
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1360 = _t1363
                                                    _t1358 = _t1360
                                                _t1356 = _t1358
                                            _t1354 = _t1356
                                        _t1352 = _t1354
                                    _t1350 = _t1352
                                _t1348 = _t1350
                            _t1346 = _t1348
                        _t1344 = _t1346
                    _t1342 = _t1344
                _t1339 = _t1342
            _t1336 = _t1339
        result686 = _t1336
        self.record_span(span_start685, "Value")
        return result686

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start690 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int687 = self.consume_terminal("INT")
        int_3688 = self.consume_terminal("INT")
        int_4689 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1366 = logic_pb2.DateValue(year=int(int687), month=int(int_3688), day=int(int_4689))
        result691 = _t1366
        self.record_span(span_start690, "DateValue")
        return result691

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start699 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int692 = self.consume_terminal("INT")
        int_3693 = self.consume_terminal("INT")
        int_4694 = self.consume_terminal("INT")
        int_5695 = self.consume_terminal("INT")
        int_6696 = self.consume_terminal("INT")
        int_7697 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1367 = self.consume_terminal("INT")
        else:
            _t1367 = None
        int_8698 = _t1367
        self.consume_literal(")")
        _t1368 = logic_pb2.DateTimeValue(year=int(int692), month=int(int_3693), day=int(int_4694), hour=int(int_5695), minute=int(int_6696), second=int(int_7697), microsecond=int((int_8698 if int_8698 is not None else 0)))
        result700 = _t1368
        self.record_span(span_start699, "DateTimeValue")
        return result700

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1369 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1370 = 1
            else:
                _t1370 = -1
            _t1369 = _t1370
        prediction701 = _t1369
        if prediction701 == 1:
            self.consume_literal("false")
            _t1371 = False
        else:
            if prediction701 == 0:
                self.consume_literal("true")
                _t1372 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1371 = _t1372
        return _t1371

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start706 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs702 = []
        cond703 = self.match_lookahead_literal(":", 0)
        while cond703:
            _t1373 = self.parse_fragment_id()
            item704 = _t1373
            xs702.append(item704)
            cond703 = self.match_lookahead_literal(":", 0)
        fragment_ids705 = xs702
        self.consume_literal(")")
        _t1374 = transactions_pb2.Sync(fragments=fragment_ids705)
        result707 = _t1374
        self.record_span(span_start706, "Sync")
        return result707

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start709 = self.span_start()
        self.consume_literal(":")
        symbol708 = self.consume_terminal("SYMBOL")
        result710 = fragments_pb2.FragmentId(id=symbol708.encode())
        self.record_span(span_start709, "FragmentId")
        return result710

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start713 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1376 = self.parse_epoch_writes()
            _t1375 = _t1376
        else:
            _t1375 = None
        epoch_writes711 = _t1375
        if self.match_lookahead_literal("(", 0):
            _t1378 = self.parse_epoch_reads()
            _t1377 = _t1378
        else:
            _t1377 = None
        epoch_reads712 = _t1377
        self.consume_literal(")")
        _t1379 = transactions_pb2.Epoch(writes=(epoch_writes711 if epoch_writes711 is not None else []), reads=(epoch_reads712 if epoch_reads712 is not None else []))
        result714 = _t1379
        self.record_span(span_start713, "Epoch")
        return result714

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs715 = []
        cond716 = self.match_lookahead_literal("(", 0)
        while cond716:
            _t1380 = self.parse_write()
            item717 = _t1380
            xs715.append(item717)
            cond716 = self.match_lookahead_literal("(", 0)
        writes718 = xs715
        self.consume_literal(")")
        return writes718

    def parse_write(self) -> transactions_pb2.Write:
        span_start724 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1382 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1383 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1384 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1385 = 2
                        else:
                            _t1385 = -1
                        _t1384 = _t1385
                    _t1383 = _t1384
                _t1382 = _t1383
            _t1381 = _t1382
        else:
            _t1381 = -1
        prediction719 = _t1381
        if prediction719 == 3:
            _t1387 = self.parse_snapshot()
            snapshot723 = _t1387
            _t1388 = transactions_pb2.Write(snapshot=snapshot723)
            _t1386 = _t1388
        else:
            if prediction719 == 2:
                _t1390 = self.parse_context()
                context722 = _t1390
                _t1391 = transactions_pb2.Write(context=context722)
                _t1389 = _t1391
            else:
                if prediction719 == 1:
                    _t1393 = self.parse_undefine()
                    undefine721 = _t1393
                    _t1394 = transactions_pb2.Write(undefine=undefine721)
                    _t1392 = _t1394
                else:
                    if prediction719 == 0:
                        _t1396 = self.parse_define()
                        define720 = _t1396
                        _t1397 = transactions_pb2.Write(define=define720)
                        _t1395 = _t1397
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1392 = _t1395
                _t1389 = _t1392
            _t1386 = _t1389
        result725 = _t1386
        self.record_span(span_start724, "Write")
        return result725

    def parse_define(self) -> transactions_pb2.Define:
        span_start727 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1398 = self.parse_fragment()
        fragment726 = _t1398
        self.consume_literal(")")
        _t1399 = transactions_pb2.Define(fragment=fragment726)
        result728 = _t1399
        self.record_span(span_start727, "Define")
        return result728

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start734 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1400 = self.parse_new_fragment_id()
        new_fragment_id729 = _t1400
        xs730 = []
        cond731 = self.match_lookahead_literal("(", 0)
        while cond731:
            _t1401 = self.parse_declaration()
            item732 = _t1401
            xs730.append(item732)
            cond731 = self.match_lookahead_literal("(", 0)
        declarations733 = xs730
        self.consume_literal(")")
        result735 = self.construct_fragment(new_fragment_id729, declarations733)
        self.record_span(span_start734, "Fragment")
        return result735

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start737 = self.span_start()
        _t1402 = self.parse_fragment_id()
        fragment_id736 = _t1402
        self.start_fragment(fragment_id736)
        result738 = fragment_id736
        self.record_span(span_start737, "FragmentId")
        return result738

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start744 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1404 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1405 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1406 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1407 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1408 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1409 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1410 = 1
                                    else:
                                        _t1410 = -1
                                    _t1409 = _t1410
                                _t1408 = _t1409
                            _t1407 = _t1408
                        _t1406 = _t1407
                    _t1405 = _t1406
                _t1404 = _t1405
            _t1403 = _t1404
        else:
            _t1403 = -1
        prediction739 = _t1403
        if prediction739 == 3:
            _t1412 = self.parse_data()
            data743 = _t1412
            _t1413 = logic_pb2.Declaration(data=data743)
            _t1411 = _t1413
        else:
            if prediction739 == 2:
                _t1415 = self.parse_constraint()
                constraint742 = _t1415
                _t1416 = logic_pb2.Declaration(constraint=constraint742)
                _t1414 = _t1416
            else:
                if prediction739 == 1:
                    _t1418 = self.parse_algorithm()
                    algorithm741 = _t1418
                    _t1419 = logic_pb2.Declaration(algorithm=algorithm741)
                    _t1417 = _t1419
                else:
                    if prediction739 == 0:
                        _t1421 = self.parse_def()
                        def740 = _t1421
                        _t1422 = logic_pb2.Declaration()
                        getattr(_t1422, 'def').CopyFrom(def740)
                        _t1420 = _t1422
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1417 = _t1420
                _t1414 = _t1417
            _t1411 = _t1414
        result745 = _t1411
        self.record_span(span_start744, "Declaration")
        return result745

    def parse_def(self) -> logic_pb2.Def:
        span_start749 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1423 = self.parse_relation_id()
        relation_id746 = _t1423
        _t1424 = self.parse_abstraction()
        abstraction747 = _t1424
        if self.match_lookahead_literal("(", 0):
            _t1426 = self.parse_attrs()
            _t1425 = _t1426
        else:
            _t1425 = None
        attrs748 = _t1425
        self.consume_literal(")")
        _t1427 = logic_pb2.Def(name=relation_id746, body=abstraction747, attrs=(attrs748 if attrs748 is not None else []))
        result750 = _t1427
        self.record_span(span_start749, "Def")
        return result750

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start754 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1428 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1429 = 1
            else:
                _t1429 = -1
            _t1428 = _t1429
        prediction751 = _t1428
        if prediction751 == 1:
            uint128753 = self.consume_terminal("UINT128")
            _t1430 = logic_pb2.RelationId(id_low=uint128753.low, id_high=uint128753.high)
        else:
            if prediction751 == 0:
                self.consume_literal(":")
                symbol752 = self.consume_terminal("SYMBOL")
                _t1431 = self.relation_id_from_string(symbol752)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1430 = _t1431
        result755 = _t1430
        self.record_span(span_start754, "RelationId")
        return result755

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start758 = self.span_start()
        self.consume_literal("(")
        _t1432 = self.parse_bindings()
        bindings756 = _t1432
        _t1433 = self.parse_formula()
        formula757 = _t1433
        self.consume_literal(")")
        _t1434 = logic_pb2.Abstraction(vars=(list(bindings756[0]) + list(bindings756[1] if bindings756[1] is not None else [])), value=formula757)
        result759 = _t1434
        self.record_span(span_start758, "Abstraction")
        return result759

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs760 = []
        cond761 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond761:
            _t1435 = self.parse_binding()
            item762 = _t1435
            xs760.append(item762)
            cond761 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings763 = xs760
        if self.match_lookahead_literal("|", 0):
            _t1437 = self.parse_value_bindings()
            _t1436 = _t1437
        else:
            _t1436 = None
        value_bindings764 = _t1436
        self.consume_literal("]")
        return (bindings763, (value_bindings764 if value_bindings764 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start767 = self.span_start()
        symbol765 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1438 = self.parse_type()
        type766 = _t1438
        _t1439 = logic_pb2.Var(name=symbol765)
        _t1440 = logic_pb2.Binding(var=_t1439, type=type766)
        result768 = _t1440
        self.record_span(span_start767, "Binding")
        return result768

    def parse_type(self) -> logic_pb2.Type:
        span_start784 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1441 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1442 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1443 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1444 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1445 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1446 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1447 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1448 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1449 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1450 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1451 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1452 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1453 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1454 = 9
                                                            else:
                                                                _t1454 = -1
                                                            _t1453 = _t1454
                                                        _t1452 = _t1453
                                                    _t1451 = _t1452
                                                _t1450 = _t1451
                                            _t1449 = _t1450
                                        _t1448 = _t1449
                                    _t1447 = _t1448
                                _t1446 = _t1447
                            _t1445 = _t1446
                        _t1444 = _t1445
                    _t1443 = _t1444
                _t1442 = _t1443
            _t1441 = _t1442
        prediction769 = _t1441
        if prediction769 == 13:
            _t1456 = self.parse_uint32_type()
            uint32_type783 = _t1456
            _t1457 = logic_pb2.Type(uint32_type=uint32_type783)
            _t1455 = _t1457
        else:
            if prediction769 == 12:
                _t1459 = self.parse_float32_type()
                float32_type782 = _t1459
                _t1460 = logic_pb2.Type(float32_type=float32_type782)
                _t1458 = _t1460
            else:
                if prediction769 == 11:
                    _t1462 = self.parse_int32_type()
                    int32_type781 = _t1462
                    _t1463 = logic_pb2.Type(int32_type=int32_type781)
                    _t1461 = _t1463
                else:
                    if prediction769 == 10:
                        _t1465 = self.parse_boolean_type()
                        boolean_type780 = _t1465
                        _t1466 = logic_pb2.Type(boolean_type=boolean_type780)
                        _t1464 = _t1466
                    else:
                        if prediction769 == 9:
                            _t1468 = self.parse_decimal_type()
                            decimal_type779 = _t1468
                            _t1469 = logic_pb2.Type(decimal_type=decimal_type779)
                            _t1467 = _t1469
                        else:
                            if prediction769 == 8:
                                _t1471 = self.parse_missing_type()
                                missing_type778 = _t1471
                                _t1472 = logic_pb2.Type(missing_type=missing_type778)
                                _t1470 = _t1472
                            else:
                                if prediction769 == 7:
                                    _t1474 = self.parse_datetime_type()
                                    datetime_type777 = _t1474
                                    _t1475 = logic_pb2.Type(datetime_type=datetime_type777)
                                    _t1473 = _t1475
                                else:
                                    if prediction769 == 6:
                                        _t1477 = self.parse_date_type()
                                        date_type776 = _t1477
                                        _t1478 = logic_pb2.Type(date_type=date_type776)
                                        _t1476 = _t1478
                                    else:
                                        if prediction769 == 5:
                                            _t1480 = self.parse_int128_type()
                                            int128_type775 = _t1480
                                            _t1481 = logic_pb2.Type(int128_type=int128_type775)
                                            _t1479 = _t1481
                                        else:
                                            if prediction769 == 4:
                                                _t1483 = self.parse_uint128_type()
                                                uint128_type774 = _t1483
                                                _t1484 = logic_pb2.Type(uint128_type=uint128_type774)
                                                _t1482 = _t1484
                                            else:
                                                if prediction769 == 3:
                                                    _t1486 = self.parse_float_type()
                                                    float_type773 = _t1486
                                                    _t1487 = logic_pb2.Type(float_type=float_type773)
                                                    _t1485 = _t1487
                                                else:
                                                    if prediction769 == 2:
                                                        _t1489 = self.parse_int_type()
                                                        int_type772 = _t1489
                                                        _t1490 = logic_pb2.Type(int_type=int_type772)
                                                        _t1488 = _t1490
                                                    else:
                                                        if prediction769 == 1:
                                                            _t1492 = self.parse_string_type()
                                                            string_type771 = _t1492
                                                            _t1493 = logic_pb2.Type(string_type=string_type771)
                                                            _t1491 = _t1493
                                                        else:
                                                            if prediction769 == 0:
                                                                _t1495 = self.parse_unspecified_type()
                                                                unspecified_type770 = _t1495
                                                                _t1496 = logic_pb2.Type(unspecified_type=unspecified_type770)
                                                                _t1494 = _t1496
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
                _t1458 = _t1461
            _t1455 = _t1458
        result785 = _t1455
        self.record_span(span_start784, "Type")
        return result785

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start786 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1497 = logic_pb2.UnspecifiedType()
        result787 = _t1497
        self.record_span(span_start786, "UnspecifiedType")
        return result787

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start788 = self.span_start()
        self.consume_literal("STRING")
        _t1498 = logic_pb2.StringType()
        result789 = _t1498
        self.record_span(span_start788, "StringType")
        return result789

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start790 = self.span_start()
        self.consume_literal("INT")
        _t1499 = logic_pb2.IntType()
        result791 = _t1499
        self.record_span(span_start790, "IntType")
        return result791

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start792 = self.span_start()
        self.consume_literal("FLOAT")
        _t1500 = logic_pb2.FloatType()
        result793 = _t1500
        self.record_span(span_start792, "FloatType")
        return result793

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start794 = self.span_start()
        self.consume_literal("UINT128")
        _t1501 = logic_pb2.UInt128Type()
        result795 = _t1501
        self.record_span(span_start794, "UInt128Type")
        return result795

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start796 = self.span_start()
        self.consume_literal("INT128")
        _t1502 = logic_pb2.Int128Type()
        result797 = _t1502
        self.record_span(span_start796, "Int128Type")
        return result797

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start798 = self.span_start()
        self.consume_literal("DATE")
        _t1503 = logic_pb2.DateType()
        result799 = _t1503
        self.record_span(span_start798, "DateType")
        return result799

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start800 = self.span_start()
        self.consume_literal("DATETIME")
        _t1504 = logic_pb2.DateTimeType()
        result801 = _t1504
        self.record_span(span_start800, "DateTimeType")
        return result801

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start802 = self.span_start()
        self.consume_literal("MISSING")
        _t1505 = logic_pb2.MissingType()
        result803 = _t1505
        self.record_span(span_start802, "MissingType")
        return result803

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start806 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int804 = self.consume_terminal("INT")
        int_3805 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1506 = logic_pb2.DecimalType(precision=int(int804), scale=int(int_3805))
        result807 = _t1506
        self.record_span(span_start806, "DecimalType")
        return result807

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start808 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1507 = logic_pb2.BooleanType()
        result809 = _t1507
        self.record_span(span_start808, "BooleanType")
        return result809

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start810 = self.span_start()
        self.consume_literal("INT32")
        _t1508 = logic_pb2.Int32Type()
        result811 = _t1508
        self.record_span(span_start810, "Int32Type")
        return result811

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start812 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1509 = logic_pb2.Float32Type()
        result813 = _t1509
        self.record_span(span_start812, "Float32Type")
        return result813

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start814 = self.span_start()
        self.consume_literal("UINT32")
        _t1510 = logic_pb2.UInt32Type()
        result815 = _t1510
        self.record_span(span_start814, "UInt32Type")
        return result815

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs816 = []
        cond817 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond817:
            _t1511 = self.parse_binding()
            item818 = _t1511
            xs816.append(item818)
            cond817 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings819 = xs816
        return bindings819

    def parse_formula(self) -> logic_pb2.Formula:
        span_start834 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1513 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1514 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1515 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1516 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1517 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1518 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1519 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1520 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1521 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1522 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1523 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1524 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1525 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1526 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1527 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1528 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1529 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1530 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1531 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1532 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1533 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1534 = 10
                                                                                                else:
                                                                                                    _t1534 = -1
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
                                _t1517 = _t1518
                            _t1516 = _t1517
                        _t1515 = _t1516
                    _t1514 = _t1515
                _t1513 = _t1514
            _t1512 = _t1513
        else:
            _t1512 = -1
        prediction820 = _t1512
        if prediction820 == 12:
            _t1536 = self.parse_cast()
            cast833 = _t1536
            _t1537 = logic_pb2.Formula(cast=cast833)
            _t1535 = _t1537
        else:
            if prediction820 == 11:
                _t1539 = self.parse_rel_atom()
                rel_atom832 = _t1539
                _t1540 = logic_pb2.Formula(rel_atom=rel_atom832)
                _t1538 = _t1540
            else:
                if prediction820 == 10:
                    _t1542 = self.parse_primitive()
                    primitive831 = _t1542
                    _t1543 = logic_pb2.Formula(primitive=primitive831)
                    _t1541 = _t1543
                else:
                    if prediction820 == 9:
                        _t1545 = self.parse_pragma()
                        pragma830 = _t1545
                        _t1546 = logic_pb2.Formula(pragma=pragma830)
                        _t1544 = _t1546
                    else:
                        if prediction820 == 8:
                            _t1548 = self.parse_atom()
                            atom829 = _t1548
                            _t1549 = logic_pb2.Formula(atom=atom829)
                            _t1547 = _t1549
                        else:
                            if prediction820 == 7:
                                _t1551 = self.parse_ffi()
                                ffi828 = _t1551
                                _t1552 = logic_pb2.Formula(ffi=ffi828)
                                _t1550 = _t1552
                            else:
                                if prediction820 == 6:
                                    _t1554 = self.parse_not()
                                    not827 = _t1554
                                    _t1555 = logic_pb2.Formula()
                                    getattr(_t1555, 'not').CopyFrom(not827)
                                    _t1553 = _t1555
                                else:
                                    if prediction820 == 5:
                                        _t1557 = self.parse_disjunction()
                                        disjunction826 = _t1557
                                        _t1558 = logic_pb2.Formula(disjunction=disjunction826)
                                        _t1556 = _t1558
                                    else:
                                        if prediction820 == 4:
                                            _t1560 = self.parse_conjunction()
                                            conjunction825 = _t1560
                                            _t1561 = logic_pb2.Formula(conjunction=conjunction825)
                                            _t1559 = _t1561
                                        else:
                                            if prediction820 == 3:
                                                _t1563 = self.parse_reduce()
                                                reduce824 = _t1563
                                                _t1564 = logic_pb2.Formula(reduce=reduce824)
                                                _t1562 = _t1564
                                            else:
                                                if prediction820 == 2:
                                                    _t1566 = self.parse_exists()
                                                    exists823 = _t1566
                                                    _t1567 = logic_pb2.Formula(exists=exists823)
                                                    _t1565 = _t1567
                                                else:
                                                    if prediction820 == 1:
                                                        _t1569 = self.parse_false()
                                                        false822 = _t1569
                                                        _t1570 = logic_pb2.Formula(disjunction=false822)
                                                        _t1568 = _t1570
                                                    else:
                                                        if prediction820 == 0:
                                                            _t1572 = self.parse_true()
                                                            true821 = _t1572
                                                            _t1573 = logic_pb2.Formula(conjunction=true821)
                                                            _t1571 = _t1573
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
                _t1538 = _t1541
            _t1535 = _t1538
        result835 = _t1535
        self.record_span(span_start834, "Formula")
        return result835

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start836 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1574 = logic_pb2.Conjunction(args=[])
        result837 = _t1574
        self.record_span(span_start836, "Conjunction")
        return result837

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start838 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1575 = logic_pb2.Disjunction(args=[])
        result839 = _t1575
        self.record_span(span_start838, "Disjunction")
        return result839

    def parse_exists(self) -> logic_pb2.Exists:
        span_start842 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1576 = self.parse_bindings()
        bindings840 = _t1576
        _t1577 = self.parse_formula()
        formula841 = _t1577
        self.consume_literal(")")
        _t1578 = logic_pb2.Abstraction(vars=(list(bindings840[0]) + list(bindings840[1] if bindings840[1] is not None else [])), value=formula841)
        _t1579 = logic_pb2.Exists(body=_t1578)
        result843 = _t1579
        self.record_span(span_start842, "Exists")
        return result843

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start847 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1580 = self.parse_abstraction()
        abstraction844 = _t1580
        _t1581 = self.parse_abstraction()
        abstraction_3845 = _t1581
        _t1582 = self.parse_terms()
        terms846 = _t1582
        self.consume_literal(")")
        _t1583 = logic_pb2.Reduce(op=abstraction844, body=abstraction_3845, terms=terms846)
        result848 = _t1583
        self.record_span(span_start847, "Reduce")
        return result848

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs849 = []
        cond850 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond850:
            _t1584 = self.parse_term()
            item851 = _t1584
            xs849.append(item851)
            cond850 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms852 = xs849
        self.consume_literal(")")
        return terms852

    def parse_term(self) -> logic_pb2.Term:
        span_start856 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1585 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1586 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1587 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1588 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1589 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1590 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1591 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1592 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1593 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1594 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1595 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1596 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1597 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1598 = 1
                                                            else:
                                                                _t1598 = -1
                                                            _t1597 = _t1598
                                                        _t1596 = _t1597
                                                    _t1595 = _t1596
                                                _t1594 = _t1595
                                            _t1593 = _t1594
                                        _t1592 = _t1593
                                    _t1591 = _t1592
                                _t1590 = _t1591
                            _t1589 = _t1590
                        _t1588 = _t1589
                    _t1587 = _t1588
                _t1586 = _t1587
            _t1585 = _t1586
        prediction853 = _t1585
        if prediction853 == 1:
            _t1600 = self.parse_value()
            value855 = _t1600
            _t1601 = logic_pb2.Term(constant=value855)
            _t1599 = _t1601
        else:
            if prediction853 == 0:
                _t1603 = self.parse_var()
                var854 = _t1603
                _t1604 = logic_pb2.Term(var=var854)
                _t1602 = _t1604
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1599 = _t1602
        result857 = _t1599
        self.record_span(span_start856, "Term")
        return result857

    def parse_var(self) -> logic_pb2.Var:
        span_start859 = self.span_start()
        symbol858 = self.consume_terminal("SYMBOL")
        _t1605 = logic_pb2.Var(name=symbol858)
        result860 = _t1605
        self.record_span(span_start859, "Var")
        return result860

    def parse_value(self) -> logic_pb2.Value:
        span_start874 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1606 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1607 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1608 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1610 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1611 = 0
                            else:
                                _t1611 = -1
                            _t1610 = _t1611
                        _t1609 = _t1610
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1612 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1613 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1614 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1615 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1616 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1617 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1618 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1619 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1620 = 10
                                                        else:
                                                            _t1620 = -1
                                                        _t1619 = _t1620
                                                    _t1618 = _t1619
                                                _t1617 = _t1618
                                            _t1616 = _t1617
                                        _t1615 = _t1616
                                    _t1614 = _t1615
                                _t1613 = _t1614
                            _t1612 = _t1613
                        _t1609 = _t1612
                    _t1608 = _t1609
                _t1607 = _t1608
            _t1606 = _t1607
        prediction861 = _t1606
        if prediction861 == 12:
            _t1622 = self.parse_boolean_value()
            boolean_value873 = _t1622
            _t1623 = logic_pb2.Value(boolean_value=boolean_value873)
            _t1621 = _t1623
        else:
            if prediction861 == 11:
                self.consume_literal("missing")
                _t1625 = logic_pb2.MissingValue()
                _t1626 = logic_pb2.Value(missing_value=_t1625)
                _t1624 = _t1626
            else:
                if prediction861 == 10:
                    formatted_decimal872 = self.consume_terminal("DECIMAL")
                    _t1628 = logic_pb2.Value(decimal_value=formatted_decimal872)
                    _t1627 = _t1628
                else:
                    if prediction861 == 9:
                        formatted_int128871 = self.consume_terminal("INT128")
                        _t1630 = logic_pb2.Value(int128_value=formatted_int128871)
                        _t1629 = _t1630
                    else:
                        if prediction861 == 8:
                            formatted_uint128870 = self.consume_terminal("UINT128")
                            _t1632 = logic_pb2.Value(uint128_value=formatted_uint128870)
                            _t1631 = _t1632
                        else:
                            if prediction861 == 7:
                                formatted_uint32869 = self.consume_terminal("UINT32")
                                _t1634 = logic_pb2.Value(uint32_value=formatted_uint32869)
                                _t1633 = _t1634
                            else:
                                if prediction861 == 6:
                                    formatted_float868 = self.consume_terminal("FLOAT")
                                    _t1636 = logic_pb2.Value(float_value=formatted_float868)
                                    _t1635 = _t1636
                                else:
                                    if prediction861 == 5:
                                        formatted_float32867 = self.consume_terminal("FLOAT32")
                                        _t1638 = logic_pb2.Value(float32_value=formatted_float32867)
                                        _t1637 = _t1638
                                    else:
                                        if prediction861 == 4:
                                            formatted_int866 = self.consume_terminal("INT")
                                            _t1640 = logic_pb2.Value(int_value=formatted_int866)
                                            _t1639 = _t1640
                                        else:
                                            if prediction861 == 3:
                                                formatted_int32865 = self.consume_terminal("INT32")
                                                _t1642 = logic_pb2.Value(int32_value=formatted_int32865)
                                                _t1641 = _t1642
                                            else:
                                                if prediction861 == 2:
                                                    formatted_string864 = self.consume_terminal("STRING")
                                                    _t1644 = logic_pb2.Value(string_value=formatted_string864)
                                                    _t1643 = _t1644
                                                else:
                                                    if prediction861 == 1:
                                                        _t1646 = self.parse_datetime()
                                                        datetime863 = _t1646
                                                        _t1647 = logic_pb2.Value(datetime_value=datetime863)
                                                        _t1645 = _t1647
                                                    else:
                                                        if prediction861 == 0:
                                                            _t1649 = self.parse_date()
                                                            date862 = _t1649
                                                            _t1650 = logic_pb2.Value(date_value=date862)
                                                            _t1648 = _t1650
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1645 = _t1648
                                                    _t1643 = _t1645
                                                _t1641 = _t1643
                                            _t1639 = _t1641
                                        _t1637 = _t1639
                                    _t1635 = _t1637
                                _t1633 = _t1635
                            _t1631 = _t1633
                        _t1629 = _t1631
                    _t1627 = _t1629
                _t1624 = _t1627
            _t1621 = _t1624
        result875 = _t1621
        self.record_span(span_start874, "Value")
        return result875

    def parse_date(self) -> logic_pb2.DateValue:
        span_start879 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int876 = self.consume_terminal("INT")
        formatted_int_3877 = self.consume_terminal("INT")
        formatted_int_4878 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1651 = logic_pb2.DateValue(year=int(formatted_int876), month=int(formatted_int_3877), day=int(formatted_int_4878))
        result880 = _t1651
        self.record_span(span_start879, "DateValue")
        return result880

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start888 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int881 = self.consume_terminal("INT")
        formatted_int_3882 = self.consume_terminal("INT")
        formatted_int_4883 = self.consume_terminal("INT")
        formatted_int_5884 = self.consume_terminal("INT")
        formatted_int_6885 = self.consume_terminal("INT")
        formatted_int_7886 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1652 = self.consume_terminal("INT")
        else:
            _t1652 = None
        formatted_int_8887 = _t1652
        self.consume_literal(")")
        _t1653 = logic_pb2.DateTimeValue(year=int(formatted_int881), month=int(formatted_int_3882), day=int(formatted_int_4883), hour=int(formatted_int_5884), minute=int(formatted_int_6885), second=int(formatted_int_7886), microsecond=int((formatted_int_8887 if formatted_int_8887 is not None else 0)))
        result889 = _t1653
        self.record_span(span_start888, "DateTimeValue")
        return result889

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start894 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs890 = []
        cond891 = self.match_lookahead_literal("(", 0)
        while cond891:
            _t1654 = self.parse_formula()
            item892 = _t1654
            xs890.append(item892)
            cond891 = self.match_lookahead_literal("(", 0)
        formulas893 = xs890
        self.consume_literal(")")
        _t1655 = logic_pb2.Conjunction(args=formulas893)
        result895 = _t1655
        self.record_span(span_start894, "Conjunction")
        return result895

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start900 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs896 = []
        cond897 = self.match_lookahead_literal("(", 0)
        while cond897:
            _t1656 = self.parse_formula()
            item898 = _t1656
            xs896.append(item898)
            cond897 = self.match_lookahead_literal("(", 0)
        formulas899 = xs896
        self.consume_literal(")")
        _t1657 = logic_pb2.Disjunction(args=formulas899)
        result901 = _t1657
        self.record_span(span_start900, "Disjunction")
        return result901

    def parse_not(self) -> logic_pb2.Not:
        span_start903 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1658 = self.parse_formula()
        formula902 = _t1658
        self.consume_literal(")")
        _t1659 = logic_pb2.Not(arg=formula902)
        result904 = _t1659
        self.record_span(span_start903, "Not")
        return result904

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start908 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1660 = self.parse_name()
        name905 = _t1660
        _t1661 = self.parse_ffi_args()
        ffi_args906 = _t1661
        _t1662 = self.parse_terms()
        terms907 = _t1662
        self.consume_literal(")")
        _t1663 = logic_pb2.FFI(name=name905, args=ffi_args906, terms=terms907)
        result909 = _t1663
        self.record_span(span_start908, "FFI")
        return result909

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol910 = self.consume_terminal("SYMBOL")
        return symbol910

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs911 = []
        cond912 = self.match_lookahead_literal("(", 0)
        while cond912:
            _t1664 = self.parse_abstraction()
            item913 = _t1664
            xs911.append(item913)
            cond912 = self.match_lookahead_literal("(", 0)
        abstractions914 = xs911
        self.consume_literal(")")
        return abstractions914

    def parse_atom(self) -> logic_pb2.Atom:
        span_start920 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1665 = self.parse_relation_id()
        relation_id915 = _t1665
        xs916 = []
        cond917 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond917:
            _t1666 = self.parse_term()
            item918 = _t1666
            xs916.append(item918)
            cond917 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms919 = xs916
        self.consume_literal(")")
        _t1667 = logic_pb2.Atom(name=relation_id915, terms=terms919)
        result921 = _t1667
        self.record_span(span_start920, "Atom")
        return result921

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start927 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1668 = self.parse_name()
        name922 = _t1668
        xs923 = []
        cond924 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond924:
            _t1669 = self.parse_term()
            item925 = _t1669
            xs923.append(item925)
            cond924 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms926 = xs923
        self.consume_literal(")")
        _t1670 = logic_pb2.Pragma(name=name922, terms=terms926)
        result928 = _t1670
        self.record_span(span_start927, "Pragma")
        return result928

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start944 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1672 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1673 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1674 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1675 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1676 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1677 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1678 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1679 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1680 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1681 = 7
                                                else:
                                                    _t1681 = -1
                                                _t1680 = _t1681
                                            _t1679 = _t1680
                                        _t1678 = _t1679
                                    _t1677 = _t1678
                                _t1676 = _t1677
                            _t1675 = _t1676
                        _t1674 = _t1675
                    _t1673 = _t1674
                _t1672 = _t1673
            _t1671 = _t1672
        else:
            _t1671 = -1
        prediction929 = _t1671
        if prediction929 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1683 = self.parse_name()
            name939 = _t1683
            xs940 = []
            cond941 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond941:
                _t1684 = self.parse_rel_term()
                item942 = _t1684
                xs940.append(item942)
                cond941 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms943 = xs940
            self.consume_literal(")")
            _t1685 = logic_pb2.Primitive(name=name939, terms=rel_terms943)
            _t1682 = _t1685
        else:
            if prediction929 == 8:
                _t1687 = self.parse_divide()
                divide938 = _t1687
                _t1686 = divide938
            else:
                if prediction929 == 7:
                    _t1689 = self.parse_multiply()
                    multiply937 = _t1689
                    _t1688 = multiply937
                else:
                    if prediction929 == 6:
                        _t1691 = self.parse_minus()
                        minus936 = _t1691
                        _t1690 = minus936
                    else:
                        if prediction929 == 5:
                            _t1693 = self.parse_add()
                            add935 = _t1693
                            _t1692 = add935
                        else:
                            if prediction929 == 4:
                                _t1695 = self.parse_gt_eq()
                                gt_eq934 = _t1695
                                _t1694 = gt_eq934
                            else:
                                if prediction929 == 3:
                                    _t1697 = self.parse_gt()
                                    gt933 = _t1697
                                    _t1696 = gt933
                                else:
                                    if prediction929 == 2:
                                        _t1699 = self.parse_lt_eq()
                                        lt_eq932 = _t1699
                                        _t1698 = lt_eq932
                                    else:
                                        if prediction929 == 1:
                                            _t1701 = self.parse_lt()
                                            lt931 = _t1701
                                            _t1700 = lt931
                                        else:
                                            if prediction929 == 0:
                                                _t1703 = self.parse_eq()
                                                eq930 = _t1703
                                                _t1702 = eq930
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1700 = _t1702
                                        _t1698 = _t1700
                                    _t1696 = _t1698
                                _t1694 = _t1696
                            _t1692 = _t1694
                        _t1690 = _t1692
                    _t1688 = _t1690
                _t1686 = _t1688
            _t1682 = _t1686
        result945 = _t1682
        self.record_span(span_start944, "Primitive")
        return result945

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start948 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1704 = self.parse_term()
        term946 = _t1704
        _t1705 = self.parse_term()
        term_3947 = _t1705
        self.consume_literal(")")
        _t1706 = logic_pb2.RelTerm(term=term946)
        _t1707 = logic_pb2.RelTerm(term=term_3947)
        _t1708 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1706, _t1707])
        result949 = _t1708
        self.record_span(span_start948, "Primitive")
        return result949

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start952 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1709 = self.parse_term()
        term950 = _t1709
        _t1710 = self.parse_term()
        term_3951 = _t1710
        self.consume_literal(")")
        _t1711 = logic_pb2.RelTerm(term=term950)
        _t1712 = logic_pb2.RelTerm(term=term_3951)
        _t1713 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1711, _t1712])
        result953 = _t1713
        self.record_span(span_start952, "Primitive")
        return result953

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start956 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1714 = self.parse_term()
        term954 = _t1714
        _t1715 = self.parse_term()
        term_3955 = _t1715
        self.consume_literal(")")
        _t1716 = logic_pb2.RelTerm(term=term954)
        _t1717 = logic_pb2.RelTerm(term=term_3955)
        _t1718 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1716, _t1717])
        result957 = _t1718
        self.record_span(span_start956, "Primitive")
        return result957

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start960 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1719 = self.parse_term()
        term958 = _t1719
        _t1720 = self.parse_term()
        term_3959 = _t1720
        self.consume_literal(")")
        _t1721 = logic_pb2.RelTerm(term=term958)
        _t1722 = logic_pb2.RelTerm(term=term_3959)
        _t1723 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1721, _t1722])
        result961 = _t1723
        self.record_span(span_start960, "Primitive")
        return result961

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start964 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1724 = self.parse_term()
        term962 = _t1724
        _t1725 = self.parse_term()
        term_3963 = _t1725
        self.consume_literal(")")
        _t1726 = logic_pb2.RelTerm(term=term962)
        _t1727 = logic_pb2.RelTerm(term=term_3963)
        _t1728 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1726, _t1727])
        result965 = _t1728
        self.record_span(span_start964, "Primitive")
        return result965

    def parse_add(self) -> logic_pb2.Primitive:
        span_start969 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1729 = self.parse_term()
        term966 = _t1729
        _t1730 = self.parse_term()
        term_3967 = _t1730
        _t1731 = self.parse_term()
        term_4968 = _t1731
        self.consume_literal(")")
        _t1732 = logic_pb2.RelTerm(term=term966)
        _t1733 = logic_pb2.RelTerm(term=term_3967)
        _t1734 = logic_pb2.RelTerm(term=term_4968)
        _t1735 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1732, _t1733, _t1734])
        result970 = _t1735
        self.record_span(span_start969, "Primitive")
        return result970

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start974 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1736 = self.parse_term()
        term971 = _t1736
        _t1737 = self.parse_term()
        term_3972 = _t1737
        _t1738 = self.parse_term()
        term_4973 = _t1738
        self.consume_literal(")")
        _t1739 = logic_pb2.RelTerm(term=term971)
        _t1740 = logic_pb2.RelTerm(term=term_3972)
        _t1741 = logic_pb2.RelTerm(term=term_4973)
        _t1742 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1739, _t1740, _t1741])
        result975 = _t1742
        self.record_span(span_start974, "Primitive")
        return result975

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start979 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1743 = self.parse_term()
        term976 = _t1743
        _t1744 = self.parse_term()
        term_3977 = _t1744
        _t1745 = self.parse_term()
        term_4978 = _t1745
        self.consume_literal(")")
        _t1746 = logic_pb2.RelTerm(term=term976)
        _t1747 = logic_pb2.RelTerm(term=term_3977)
        _t1748 = logic_pb2.RelTerm(term=term_4978)
        _t1749 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1746, _t1747, _t1748])
        result980 = _t1749
        self.record_span(span_start979, "Primitive")
        return result980

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start984 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1750 = self.parse_term()
        term981 = _t1750
        _t1751 = self.parse_term()
        term_3982 = _t1751
        _t1752 = self.parse_term()
        term_4983 = _t1752
        self.consume_literal(")")
        _t1753 = logic_pb2.RelTerm(term=term981)
        _t1754 = logic_pb2.RelTerm(term=term_3982)
        _t1755 = logic_pb2.RelTerm(term=term_4983)
        _t1756 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1753, _t1754, _t1755])
        result985 = _t1756
        self.record_span(span_start984, "Primitive")
        return result985

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start989 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1757 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1758 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1759 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1760 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1761 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1762 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1763 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1764 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1765 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1766 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1767 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1768 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1769 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1770 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1771 = 1
                                                                else:
                                                                    _t1771 = -1
                                                                _t1770 = _t1771
                                                            _t1769 = _t1770
                                                        _t1768 = _t1769
                                                    _t1767 = _t1768
                                                _t1766 = _t1767
                                            _t1765 = _t1766
                                        _t1764 = _t1765
                                    _t1763 = _t1764
                                _t1762 = _t1763
                            _t1761 = _t1762
                        _t1760 = _t1761
                    _t1759 = _t1760
                _t1758 = _t1759
            _t1757 = _t1758
        prediction986 = _t1757
        if prediction986 == 1:
            _t1773 = self.parse_term()
            term988 = _t1773
            _t1774 = logic_pb2.RelTerm(term=term988)
            _t1772 = _t1774
        else:
            if prediction986 == 0:
                _t1776 = self.parse_specialized_value()
                specialized_value987 = _t1776
                _t1777 = logic_pb2.RelTerm(specialized_value=specialized_value987)
                _t1775 = _t1777
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1772 = _t1775
        result990 = _t1772
        self.record_span(span_start989, "RelTerm")
        return result990

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start992 = self.span_start()
        self.consume_literal("#")
        _t1778 = self.parse_raw_value()
        raw_value991 = _t1778
        result993 = raw_value991
        self.record_span(span_start992, "Value")
        return result993

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start999 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1779 = self.parse_name()
        name994 = _t1779
        xs995 = []
        cond996 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond996:
            _t1780 = self.parse_rel_term()
            item997 = _t1780
            xs995.append(item997)
            cond996 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms998 = xs995
        self.consume_literal(")")
        _t1781 = logic_pb2.RelAtom(name=name994, terms=rel_terms998)
        result1000 = _t1781
        self.record_span(span_start999, "RelAtom")
        return result1000

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1003 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1782 = self.parse_term()
        term1001 = _t1782
        _t1783 = self.parse_term()
        term_31002 = _t1783
        self.consume_literal(")")
        _t1784 = logic_pb2.Cast(input=term1001, result=term_31002)
        result1004 = _t1784
        self.record_span(span_start1003, "Cast")
        return result1004

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1005 = []
        cond1006 = self.match_lookahead_literal("(", 0)
        while cond1006:
            _t1785 = self.parse_attribute()
            item1007 = _t1785
            xs1005.append(item1007)
            cond1006 = self.match_lookahead_literal("(", 0)
        attributes1008 = xs1005
        self.consume_literal(")")
        return attributes1008

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1014 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1786 = self.parse_name()
        name1009 = _t1786
        xs1010 = []
        cond1011 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1011:
            _t1787 = self.parse_raw_value()
            item1012 = _t1787
            xs1010.append(item1012)
            cond1011 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1013 = xs1010
        self.consume_literal(")")
        _t1788 = logic_pb2.Attribute(name=name1009, args=raw_values1013)
        result1015 = _t1788
        self.record_span(span_start1014, "Attribute")
        return result1015

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1021 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1016 = []
        cond1017 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1017:
            _t1789 = self.parse_relation_id()
            item1018 = _t1789
            xs1016.append(item1018)
            cond1017 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1019 = xs1016
        _t1790 = self.parse_script()
        script1020 = _t1790
        self.consume_literal(")")
        _t1791 = logic_pb2.Algorithm(body=script1020)
        getattr(_t1791, 'global').extend(relation_ids1019)
        result1022 = _t1791
        self.record_span(span_start1021, "Algorithm")
        return result1022

    def parse_script(self) -> logic_pb2.Script:
        span_start1027 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1023 = []
        cond1024 = self.match_lookahead_literal("(", 0)
        while cond1024:
            _t1792 = self.parse_construct()
            item1025 = _t1792
            xs1023.append(item1025)
            cond1024 = self.match_lookahead_literal("(", 0)
        constructs1026 = xs1023
        self.consume_literal(")")
        _t1793 = logic_pb2.Script(constructs=constructs1026)
        result1028 = _t1793
        self.record_span(span_start1027, "Script")
        return result1028

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1032 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1795 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1796 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1797 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1798 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1799 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1800 = 1
                                else:
                                    _t1800 = -1
                                _t1799 = _t1800
                            _t1798 = _t1799
                        _t1797 = _t1798
                    _t1796 = _t1797
                _t1795 = _t1796
            _t1794 = _t1795
        else:
            _t1794 = -1
        prediction1029 = _t1794
        if prediction1029 == 1:
            _t1802 = self.parse_instruction()
            instruction1031 = _t1802
            _t1803 = logic_pb2.Construct(instruction=instruction1031)
            _t1801 = _t1803
        else:
            if prediction1029 == 0:
                _t1805 = self.parse_loop()
                loop1030 = _t1805
                _t1806 = logic_pb2.Construct(loop=loop1030)
                _t1804 = _t1806
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1801 = _t1804
        result1033 = _t1801
        self.record_span(span_start1032, "Construct")
        return result1033

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1036 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1807 = self.parse_init()
        init1034 = _t1807
        _t1808 = self.parse_script()
        script1035 = _t1808
        self.consume_literal(")")
        _t1809 = logic_pb2.Loop(init=init1034, body=script1035)
        result1037 = _t1809
        self.record_span(span_start1036, "Loop")
        return result1037

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1038 = []
        cond1039 = self.match_lookahead_literal("(", 0)
        while cond1039:
            _t1810 = self.parse_instruction()
            item1040 = _t1810
            xs1038.append(item1040)
            cond1039 = self.match_lookahead_literal("(", 0)
        instructions1041 = xs1038
        self.consume_literal(")")
        return instructions1041

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1048 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1812 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1813 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1814 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1815 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1816 = 0
                            else:
                                _t1816 = -1
                            _t1815 = _t1816
                        _t1814 = _t1815
                    _t1813 = _t1814
                _t1812 = _t1813
            _t1811 = _t1812
        else:
            _t1811 = -1
        prediction1042 = _t1811
        if prediction1042 == 4:
            _t1818 = self.parse_monus_def()
            monus_def1047 = _t1818
            _t1819 = logic_pb2.Instruction(monus_def=monus_def1047)
            _t1817 = _t1819
        else:
            if prediction1042 == 3:
                _t1821 = self.parse_monoid_def()
                monoid_def1046 = _t1821
                _t1822 = logic_pb2.Instruction(monoid_def=monoid_def1046)
                _t1820 = _t1822
            else:
                if prediction1042 == 2:
                    _t1824 = self.parse_break()
                    break1045 = _t1824
                    _t1825 = logic_pb2.Instruction()
                    getattr(_t1825, 'break').CopyFrom(break1045)
                    _t1823 = _t1825
                else:
                    if prediction1042 == 1:
                        _t1827 = self.parse_upsert()
                        upsert1044 = _t1827
                        _t1828 = logic_pb2.Instruction(upsert=upsert1044)
                        _t1826 = _t1828
                    else:
                        if prediction1042 == 0:
                            _t1830 = self.parse_assign()
                            assign1043 = _t1830
                            _t1831 = logic_pb2.Instruction(assign=assign1043)
                            _t1829 = _t1831
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1826 = _t1829
                    _t1823 = _t1826
                _t1820 = _t1823
            _t1817 = _t1820
        result1049 = _t1817
        self.record_span(span_start1048, "Instruction")
        return result1049

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1053 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1832 = self.parse_relation_id()
        relation_id1050 = _t1832
        _t1833 = self.parse_abstraction()
        abstraction1051 = _t1833
        if self.match_lookahead_literal("(", 0):
            _t1835 = self.parse_attrs()
            _t1834 = _t1835
        else:
            _t1834 = None
        attrs1052 = _t1834
        self.consume_literal(")")
        _t1836 = logic_pb2.Assign(name=relation_id1050, body=abstraction1051, attrs=(attrs1052 if attrs1052 is not None else []))
        result1054 = _t1836
        self.record_span(span_start1053, "Assign")
        return result1054

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1058 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1837 = self.parse_relation_id()
        relation_id1055 = _t1837
        _t1838 = self.parse_abstraction_with_arity()
        abstraction_with_arity1056 = _t1838
        if self.match_lookahead_literal("(", 0):
            _t1840 = self.parse_attrs()
            _t1839 = _t1840
        else:
            _t1839 = None
        attrs1057 = _t1839
        self.consume_literal(")")
        _t1841 = logic_pb2.Upsert(name=relation_id1055, body=abstraction_with_arity1056[0], attrs=(attrs1057 if attrs1057 is not None else []), value_arity=abstraction_with_arity1056[1])
        result1059 = _t1841
        self.record_span(span_start1058, "Upsert")
        return result1059

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1842 = self.parse_bindings()
        bindings1060 = _t1842
        _t1843 = self.parse_formula()
        formula1061 = _t1843
        self.consume_literal(")")
        _t1844 = logic_pb2.Abstraction(vars=(list(bindings1060[0]) + list(bindings1060[1] if bindings1060[1] is not None else [])), value=formula1061)
        return (_t1844, len(bindings1060[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1065 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1845 = self.parse_relation_id()
        relation_id1062 = _t1845
        _t1846 = self.parse_abstraction()
        abstraction1063 = _t1846
        if self.match_lookahead_literal("(", 0):
            _t1848 = self.parse_attrs()
            _t1847 = _t1848
        else:
            _t1847 = None
        attrs1064 = _t1847
        self.consume_literal(")")
        _t1849 = logic_pb2.Break(name=relation_id1062, body=abstraction1063, attrs=(attrs1064 if attrs1064 is not None else []))
        result1066 = _t1849
        self.record_span(span_start1065, "Break")
        return result1066

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1071 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1850 = self.parse_monoid()
        monoid1067 = _t1850
        _t1851 = self.parse_relation_id()
        relation_id1068 = _t1851
        _t1852 = self.parse_abstraction_with_arity()
        abstraction_with_arity1069 = _t1852
        if self.match_lookahead_literal("(", 0):
            _t1854 = self.parse_attrs()
            _t1853 = _t1854
        else:
            _t1853 = None
        attrs1070 = _t1853
        self.consume_literal(")")
        _t1855 = logic_pb2.MonoidDef(monoid=monoid1067, name=relation_id1068, body=abstraction_with_arity1069[0], attrs=(attrs1070 if attrs1070 is not None else []), value_arity=abstraction_with_arity1069[1])
        result1072 = _t1855
        self.record_span(span_start1071, "MonoidDef")
        return result1072

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1078 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1857 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1858 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1859 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1860 = 2
                        else:
                            _t1860 = -1
                        _t1859 = _t1860
                    _t1858 = _t1859
                _t1857 = _t1858
            _t1856 = _t1857
        else:
            _t1856 = -1
        prediction1073 = _t1856
        if prediction1073 == 3:
            _t1862 = self.parse_sum_monoid()
            sum_monoid1077 = _t1862
            _t1863 = logic_pb2.Monoid(sum_monoid=sum_monoid1077)
            _t1861 = _t1863
        else:
            if prediction1073 == 2:
                _t1865 = self.parse_max_monoid()
                max_monoid1076 = _t1865
                _t1866 = logic_pb2.Monoid(max_monoid=max_monoid1076)
                _t1864 = _t1866
            else:
                if prediction1073 == 1:
                    _t1868 = self.parse_min_monoid()
                    min_monoid1075 = _t1868
                    _t1869 = logic_pb2.Monoid(min_monoid=min_monoid1075)
                    _t1867 = _t1869
                else:
                    if prediction1073 == 0:
                        _t1871 = self.parse_or_monoid()
                        or_monoid1074 = _t1871
                        _t1872 = logic_pb2.Monoid(or_monoid=or_monoid1074)
                        _t1870 = _t1872
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1867 = _t1870
                _t1864 = _t1867
            _t1861 = _t1864
        result1079 = _t1861
        self.record_span(span_start1078, "Monoid")
        return result1079

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1080 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1873 = logic_pb2.OrMonoid()
        result1081 = _t1873
        self.record_span(span_start1080, "OrMonoid")
        return result1081

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1083 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1874 = self.parse_type()
        type1082 = _t1874
        self.consume_literal(")")
        _t1875 = logic_pb2.MinMonoid(type=type1082)
        result1084 = _t1875
        self.record_span(span_start1083, "MinMonoid")
        return result1084

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1086 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1876 = self.parse_type()
        type1085 = _t1876
        self.consume_literal(")")
        _t1877 = logic_pb2.MaxMonoid(type=type1085)
        result1087 = _t1877
        self.record_span(span_start1086, "MaxMonoid")
        return result1087

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1089 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1878 = self.parse_type()
        type1088 = _t1878
        self.consume_literal(")")
        _t1879 = logic_pb2.SumMonoid(type=type1088)
        result1090 = _t1879
        self.record_span(span_start1089, "SumMonoid")
        return result1090

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1095 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1880 = self.parse_monoid()
        monoid1091 = _t1880
        _t1881 = self.parse_relation_id()
        relation_id1092 = _t1881
        _t1882 = self.parse_abstraction_with_arity()
        abstraction_with_arity1093 = _t1882
        if self.match_lookahead_literal("(", 0):
            _t1884 = self.parse_attrs()
            _t1883 = _t1884
        else:
            _t1883 = None
        attrs1094 = _t1883
        self.consume_literal(")")
        _t1885 = logic_pb2.MonusDef(monoid=monoid1091, name=relation_id1092, body=abstraction_with_arity1093[0], attrs=(attrs1094 if attrs1094 is not None else []), value_arity=abstraction_with_arity1093[1])
        result1096 = _t1885
        self.record_span(span_start1095, "MonusDef")
        return result1096

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1101 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1886 = self.parse_relation_id()
        relation_id1097 = _t1886
        _t1887 = self.parse_abstraction()
        abstraction1098 = _t1887
        _t1888 = self.parse_functional_dependency_keys()
        functional_dependency_keys1099 = _t1888
        _t1889 = self.parse_functional_dependency_values()
        functional_dependency_values1100 = _t1889
        self.consume_literal(")")
        _t1890 = logic_pb2.FunctionalDependency(guard=abstraction1098, keys=functional_dependency_keys1099, values=functional_dependency_values1100)
        _t1891 = logic_pb2.Constraint(name=relation_id1097, functional_dependency=_t1890)
        result1102 = _t1891
        self.record_span(span_start1101, "Constraint")
        return result1102

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1103 = []
        cond1104 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1104:
            _t1892 = self.parse_var()
            item1105 = _t1892
            xs1103.append(item1105)
            cond1104 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1106 = xs1103
        self.consume_literal(")")
        return vars1106

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1107 = []
        cond1108 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1108:
            _t1893 = self.parse_var()
            item1109 = _t1893
            xs1107.append(item1109)
            cond1108 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1110 = xs1107
        self.consume_literal(")")
        return vars1110

    def parse_data(self) -> logic_pb2.Data:
        span_start1116 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1895 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1896 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t1897 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t1898 = 1
                        else:
                            _t1898 = -1
                        _t1897 = _t1898
                    _t1896 = _t1897
                _t1895 = _t1896
            _t1894 = _t1895
        else:
            _t1894 = -1
        prediction1111 = _t1894
        if prediction1111 == 3:
            _t1900 = self.parse_iceberg_data()
            iceberg_data1115 = _t1900
            _t1901 = logic_pb2.Data(iceberg_data=iceberg_data1115)
            _t1899 = _t1901
        else:
            if prediction1111 == 2:
                _t1903 = self.parse_csv_data()
                csv_data1114 = _t1903
                _t1904 = logic_pb2.Data(csv_data=csv_data1114)
                _t1902 = _t1904
            else:
                if prediction1111 == 1:
                    _t1906 = self.parse_betree_relation()
                    betree_relation1113 = _t1906
                    _t1907 = logic_pb2.Data(betree_relation=betree_relation1113)
                    _t1905 = _t1907
                else:
                    if prediction1111 == 0:
                        _t1909 = self.parse_edb()
                        edb1112 = _t1909
                        _t1910 = logic_pb2.Data(edb=edb1112)
                        _t1908 = _t1910
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1905 = _t1908
                _t1902 = _t1905
            _t1899 = _t1902
        result1117 = _t1899
        self.record_span(span_start1116, "Data")
        return result1117

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1121 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1911 = self.parse_relation_id()
        relation_id1118 = _t1911
        _t1912 = self.parse_edb_path()
        edb_path1119 = _t1912
        _t1913 = self.parse_edb_types()
        edb_types1120 = _t1913
        self.consume_literal(")")
        _t1914 = logic_pb2.EDB(target_id=relation_id1118, path=edb_path1119, types=edb_types1120)
        result1122 = _t1914
        self.record_span(span_start1121, "EDB")
        return result1122

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1123 = []
        cond1124 = self.match_lookahead_terminal("STRING", 0)
        while cond1124:
            item1125 = self.consume_terminal("STRING")
            xs1123.append(item1125)
            cond1124 = self.match_lookahead_terminal("STRING", 0)
        strings1126 = xs1123
        self.consume_literal("]")
        return strings1126

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1127 = []
        cond1128 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1128:
            _t1915 = self.parse_type()
            item1129 = _t1915
            xs1127.append(item1129)
            cond1128 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1130 = xs1127
        self.consume_literal("]")
        return types1130

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1133 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1916 = self.parse_relation_id()
        relation_id1131 = _t1916
        _t1917 = self.parse_betree_info()
        betree_info1132 = _t1917
        self.consume_literal(")")
        _t1918 = logic_pb2.BeTreeRelation(name=relation_id1131, relation_info=betree_info1132)
        result1134 = _t1918
        self.record_span(span_start1133, "BeTreeRelation")
        return result1134

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1138 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1919 = self.parse_betree_info_key_types()
        betree_info_key_types1135 = _t1919
        _t1920 = self.parse_betree_info_value_types()
        betree_info_value_types1136 = _t1920
        _t1921 = self.parse_config_dict()
        config_dict1137 = _t1921
        self.consume_literal(")")
        _t1922 = self.construct_betree_info(betree_info_key_types1135, betree_info_value_types1136, config_dict1137)
        result1139 = _t1922
        self.record_span(span_start1138, "BeTreeInfo")
        return result1139

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1140 = []
        cond1141 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1141:
            _t1923 = self.parse_type()
            item1142 = _t1923
            xs1140.append(item1142)
            cond1141 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1143 = xs1140
        self.consume_literal(")")
        return types1143

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1144 = []
        cond1145 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1145:
            _t1924 = self.parse_type()
            item1146 = _t1924
            xs1144.append(item1146)
            cond1145 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1147 = xs1144
        self.consume_literal(")")
        return types1147

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1152 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1925 = self.parse_csvlocator()
        csvlocator1148 = _t1925
        _t1926 = self.parse_csv_config()
        csv_config1149 = _t1926
        _t1927 = self.parse_gnf_columns()
        gnf_columns1150 = _t1927
        _t1928 = self.parse_csv_asof()
        csv_asof1151 = _t1928
        self.consume_literal(")")
        _t1929 = logic_pb2.CSVData(locator=csvlocator1148, config=csv_config1149, columns=gnf_columns1150, asof=csv_asof1151)
        result1153 = _t1929
        self.record_span(span_start1152, "CSVData")
        return result1153

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1156 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1931 = self.parse_csv_locator_paths()
            _t1930 = _t1931
        else:
            _t1930 = None
        csv_locator_paths1154 = _t1930
        if self.match_lookahead_literal("(", 0):
            _t1933 = self.parse_csv_locator_inline_data()
            _t1932 = _t1933
        else:
            _t1932 = None
        csv_locator_inline_data1155 = _t1932
        self.consume_literal(")")
        _t1934 = logic_pb2.CSVLocator(paths=(csv_locator_paths1154 if csv_locator_paths1154 is not None else []), inline_data=(csv_locator_inline_data1155 if csv_locator_inline_data1155 is not None else "").encode())
        result1157 = _t1934
        self.record_span(span_start1156, "CSVLocator")
        return result1157

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1158 = []
        cond1159 = self.match_lookahead_terminal("STRING", 0)
        while cond1159:
            item1160 = self.consume_terminal("STRING")
            xs1158.append(item1160)
            cond1159 = self.match_lookahead_terminal("STRING", 0)
        strings1161 = xs1158
        self.consume_literal(")")
        return strings1161

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1162 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1162

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1164 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1935 = self.parse_config_dict()
        config_dict1163 = _t1935
        self.consume_literal(")")
        _t1936 = self.construct_csv_config(config_dict1163)
        result1165 = _t1936
        self.record_span(span_start1164, "CSVConfig")
        return result1165

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1166 = []
        cond1167 = self.match_lookahead_literal("(", 0)
        while cond1167:
            _t1937 = self.parse_gnf_column()
            item1168 = _t1937
            xs1166.append(item1168)
            cond1167 = self.match_lookahead_literal("(", 0)
        gnf_columns1169 = xs1166
        self.consume_literal(")")
        return gnf_columns1169

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1176 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1938 = self.parse_gnf_column_path()
        gnf_column_path1170 = _t1938
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1940 = self.parse_relation_id()
            _t1939 = _t1940
        else:
            _t1939 = None
        relation_id1171 = _t1939
        self.consume_literal("[")
        xs1172 = []
        cond1173 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1173:
            _t1941 = self.parse_type()
            item1174 = _t1941
            xs1172.append(item1174)
            cond1173 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1175 = xs1172
        self.consume_literal("]")
        self.consume_literal(")")
        _t1942 = logic_pb2.GNFColumn(column_path=gnf_column_path1170, target_id=relation_id1171, types=types1175)
        result1177 = _t1942
        self.record_span(span_start1176, "GNFColumn")
        return result1177

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1943 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1944 = 0
            else:
                _t1944 = -1
            _t1943 = _t1944
        prediction1178 = _t1943
        if prediction1178 == 1:
            self.consume_literal("[")
            xs1180 = []
            cond1181 = self.match_lookahead_terminal("STRING", 0)
            while cond1181:
                item1182 = self.consume_terminal("STRING")
                xs1180.append(item1182)
                cond1181 = self.match_lookahead_terminal("STRING", 0)
            strings1183 = xs1180
            self.consume_literal("]")
            _t1945 = strings1183
        else:
            if prediction1178 == 0:
                string1179 = self.consume_terminal("STRING")
                _t1946 = [string1179]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1945 = _t1946
        return _t1945

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1184 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1184

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1189 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t1947 = self.parse_iceberg_locator()
        iceberg_locator1185 = _t1947
        _t1948 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1186 = _t1948
        _t1949 = self.parse_gnf_columns()
        gnf_columns1187 = _t1949
        if self.match_lookahead_literal("(", 0):
            _t1951 = self.parse_iceberg_to_snapshot()
            _t1950 = _t1951
        else:
            _t1950 = None
        iceberg_to_snapshot1188 = _t1950
        self.consume_literal(")")
        _t1952 = logic_pb2.IcebergData(locator=iceberg_locator1185, config=iceberg_catalog_config1186, columns=gnf_columns1187, to_snapshot=(iceberg_to_snapshot1188 if iceberg_to_snapshot1188 is not None else ""))
        result1190 = _t1952
        self.record_span(span_start1189, "IcebergData")
        return result1190

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1197 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1191 = self.consume_terminal("STRING")
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1192 = []
        cond1193 = self.match_lookahead_terminal("STRING", 0)
        while cond1193:
            item1194 = self.consume_terminal("STRING")
            xs1192.append(item1194)
            cond1193 = self.match_lookahead_terminal("STRING", 0)
        strings1195 = xs1192
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string_121196 = self.consume_terminal("STRING")
        self.consume_literal(")")
        self.consume_literal(")")
        _t1953 = logic_pb2.IcebergLocator(table_name=string1191, namespace=strings1195, warehouse=string_121196)
        result1198 = _t1953
        self.record_span(span_start1197, "IcebergLocator")
        return result1198

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1209 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1199 = self.consume_terminal("STRING")
        self.consume_literal(")")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t1955 = self.parse_iceberg_catalog_config_scope()
            _t1954 = _t1955
        else:
            _t1954 = None
        iceberg_catalog_config_scope1200 = _t1954
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1201 = []
        cond1202 = self.match_lookahead_literal("(", 0)
        while cond1202:
            _t1956 = self.parse_iceberg_property_entry()
            item1203 = _t1956
            xs1201.append(item1203)
            cond1202 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1204 = xs1201
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1205 = []
        cond1206 = self.match_lookahead_literal("(", 0)
        while cond1206:
            _t1957 = self.parse_iceberg_property_entry()
            item1207 = _t1957
            xs1205.append(item1207)
            cond1206 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys_131208 = xs1205
        self.consume_literal(")")
        self.consume_literal(")")
        _t1958 = self.construct_iceberg_catalog_config(string1199, iceberg_catalog_config_scope1200, iceberg_property_entrys1204, iceberg_property_entrys_131208)
        result1210 = _t1958
        self.record_span(span_start1209, "IcebergCatalogConfig")
        return result1210

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1211 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1211

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1212 = self.consume_terminal("STRING")
        string_31213 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1212, string_31213,)

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1214 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1214

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1216 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1959 = self.parse_fragment_id()
        fragment_id1215 = _t1959
        self.consume_literal(")")
        _t1960 = transactions_pb2.Undefine(fragment_id=fragment_id1215)
        result1217 = _t1960
        self.record_span(span_start1216, "Undefine")
        return result1217

    def parse_context(self) -> transactions_pb2.Context:
        span_start1222 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1218 = []
        cond1219 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1219:
            _t1961 = self.parse_relation_id()
            item1220 = _t1961
            xs1218.append(item1220)
            cond1219 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1221 = xs1218
        self.consume_literal(")")
        _t1962 = transactions_pb2.Context(relations=relation_ids1221)
        result1223 = _t1962
        self.record_span(span_start1222, "Context")
        return result1223

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1228 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        xs1224 = []
        cond1225 = self.match_lookahead_literal("[", 0)
        while cond1225:
            _t1963 = self.parse_snapshot_mapping()
            item1226 = _t1963
            xs1224.append(item1226)
            cond1225 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1227 = xs1224
        self.consume_literal(")")
        _t1964 = transactions_pb2.Snapshot(mappings=snapshot_mappings1227)
        result1229 = _t1964
        self.record_span(span_start1228, "Snapshot")
        return result1229

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1232 = self.span_start()
        _t1965 = self.parse_edb_path()
        edb_path1230 = _t1965
        _t1966 = self.parse_relation_id()
        relation_id1231 = _t1966
        _t1967 = transactions_pb2.SnapshotMapping(destination_path=edb_path1230, source_relation=relation_id1231)
        result1233 = _t1967
        self.record_span(span_start1232, "SnapshotMapping")
        return result1233

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1234 = []
        cond1235 = self.match_lookahead_literal("(", 0)
        while cond1235:
            _t1968 = self.parse_read()
            item1236 = _t1968
            xs1234.append(item1236)
            cond1235 = self.match_lookahead_literal("(", 0)
        reads1237 = xs1234
        self.consume_literal(")")
        return reads1237

    def parse_read(self) -> transactions_pb2.Read:
        span_start1244 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1970 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1971 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t1972 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t1973 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t1974 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t1975 = 3
                                else:
                                    _t1975 = -1
                                _t1974 = _t1975
                            _t1973 = _t1974
                        _t1972 = _t1973
                    _t1971 = _t1972
                _t1970 = _t1971
            _t1969 = _t1970
        else:
            _t1969 = -1
        prediction1238 = _t1969
        if prediction1238 == 4:
            _t1977 = self.parse_export()
            export1243 = _t1977
            _t1978 = transactions_pb2.Read(export=export1243)
            _t1976 = _t1978
        else:
            if prediction1238 == 3:
                _t1980 = self.parse_abort()
                abort1242 = _t1980
                _t1981 = transactions_pb2.Read(abort=abort1242)
                _t1979 = _t1981
            else:
                if prediction1238 == 2:
                    _t1983 = self.parse_what_if()
                    what_if1241 = _t1983
                    _t1984 = transactions_pb2.Read(what_if=what_if1241)
                    _t1982 = _t1984
                else:
                    if prediction1238 == 1:
                        _t1986 = self.parse_output()
                        output1240 = _t1986
                        _t1987 = transactions_pb2.Read(output=output1240)
                        _t1985 = _t1987
                    else:
                        if prediction1238 == 0:
                            _t1989 = self.parse_demand()
                            demand1239 = _t1989
                            _t1990 = transactions_pb2.Read(demand=demand1239)
                            _t1988 = _t1990
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1985 = _t1988
                    _t1982 = _t1985
                _t1979 = _t1982
            _t1976 = _t1979
        result1245 = _t1976
        self.record_span(span_start1244, "Read")
        return result1245

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1247 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1991 = self.parse_relation_id()
        relation_id1246 = _t1991
        self.consume_literal(")")
        _t1992 = transactions_pb2.Demand(relation_id=relation_id1246)
        result1248 = _t1992
        self.record_span(span_start1247, "Demand")
        return result1248

    def parse_output(self) -> transactions_pb2.Output:
        span_start1251 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t1993 = self.parse_name()
        name1249 = _t1993
        _t1994 = self.parse_relation_id()
        relation_id1250 = _t1994
        self.consume_literal(")")
        _t1995 = transactions_pb2.Output(name=name1249, relation_id=relation_id1250)
        result1252 = _t1995
        self.record_span(span_start1251, "Output")
        return result1252

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1255 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t1996 = self.parse_name()
        name1253 = _t1996
        _t1997 = self.parse_epoch()
        epoch1254 = _t1997
        self.consume_literal(")")
        _t1998 = transactions_pb2.WhatIf(branch=name1253, epoch=epoch1254)
        result1256 = _t1998
        self.record_span(span_start1255, "WhatIf")
        return result1256

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1259 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2000 = self.parse_name()
            _t1999 = _t2000
        else:
            _t1999 = None
        name1257 = _t1999
        _t2001 = self.parse_relation_id()
        relation_id1258 = _t2001
        self.consume_literal(")")
        _t2002 = transactions_pb2.Abort(name=(name1257 if name1257 is not None else "abort"), relation_id=relation_id1258)
        result1260 = _t2002
        self.record_span(span_start1259, "Abort")
        return result1260

    def parse_export(self) -> transactions_pb2.Export:
        span_start1264 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2004 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2005 = 0
                else:
                    _t2005 = -1
                _t2004 = _t2005
            _t2003 = _t2004
        else:
            _t2003 = -1
        prediction1261 = _t2003
        if prediction1261 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2007 = self.parse_export_iceberg_config()
            export_iceberg_config1263 = _t2007
            self.consume_literal(")")
            _t2008 = transactions_pb2.Export(iceberg_config=export_iceberg_config1263)
            _t2006 = _t2008
        else:
            if prediction1261 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2010 = self.parse_export_csv_config()
                export_csv_config1262 = _t2010
                self.consume_literal(")")
                _t2011 = transactions_pb2.Export(csv_config=export_csv_config1262)
                _t2009 = _t2011
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2006 = _t2009
        result1265 = _t2006
        self.record_span(span_start1264, "Export")
        return result1265

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1273 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2013 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2014 = 1
                else:
                    _t2014 = -1
                _t2013 = _t2014
            _t2012 = _t2013
        else:
            _t2012 = -1
        prediction1266 = _t2012
        if prediction1266 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2016 = self.parse_export_csv_path()
            export_csv_path1270 = _t2016
            _t2017 = self.parse_export_csv_columns_list()
            export_csv_columns_list1271 = _t2017
            _t2018 = self.parse_config_dict()
            config_dict1272 = _t2018
            self.consume_literal(")")
            _t2019 = self.construct_export_csv_config(export_csv_path1270, export_csv_columns_list1271, config_dict1272)
            _t2015 = _t2019
        else:
            if prediction1266 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2021 = self.parse_export_csv_path()
                export_csv_path1267 = _t2021
                _t2022 = self.parse_export_csv_source()
                export_csv_source1268 = _t2022
                _t2023 = self.parse_csv_config()
                csv_config1269 = _t2023
                self.consume_literal(")")
                _t2024 = self.construct_export_csv_config_with_source(export_csv_path1267, export_csv_source1268, csv_config1269)
                _t2020 = _t2024
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2015 = _t2020
        result1274 = _t2015
        self.record_span(span_start1273, "ExportCSVConfig")
        return result1274

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1275 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1275

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1282 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2026 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2027 = 0
                else:
                    _t2027 = -1
                _t2026 = _t2027
            _t2025 = _t2026
        else:
            _t2025 = -1
        prediction1276 = _t2025
        if prediction1276 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2029 = self.parse_relation_id()
            relation_id1281 = _t2029
            self.consume_literal(")")
            _t2030 = transactions_pb2.ExportCSVSource(table_def=relation_id1281)
            _t2028 = _t2030
        else:
            if prediction1276 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1277 = []
                cond1278 = self.match_lookahead_literal("(", 0)
                while cond1278:
                    _t2032 = self.parse_export_csv_column()
                    item1279 = _t2032
                    xs1277.append(item1279)
                    cond1278 = self.match_lookahead_literal("(", 0)
                export_csv_columns1280 = xs1277
                self.consume_literal(")")
                _t2033 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1280)
                _t2034 = transactions_pb2.ExportCSVSource(gnf_columns=_t2033)
                _t2031 = _t2034
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2028 = _t2031
        result1283 = _t2028
        self.record_span(span_start1282, "ExportCSVSource")
        return result1283

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1286 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1284 = self.consume_terminal("STRING")
        _t2035 = self.parse_relation_id()
        relation_id1285 = _t2035
        self.consume_literal(")")
        _t2036 = transactions_pb2.ExportCSVColumn(column_name=string1284, column_data=relation_id1285)
        result1287 = _t2036
        self.record_span(span_start1286, "ExportCSVColumn")
        return result1287

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1288 = []
        cond1289 = self.match_lookahead_literal("(", 0)
        while cond1289:
            _t2037 = self.parse_export_csv_column()
            item1290 = _t2037
            xs1288.append(item1290)
            cond1289 = self.match_lookahead_literal("(", 0)
        export_csv_columns1291 = xs1288
        self.consume_literal(")")
        return export_csv_columns1291

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1304 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2038 = self.parse_iceberg_locator()
        iceberg_locator1292 = _t2038
        _t2039 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1293 = _t2039
        self.consume_literal("(")
        self.consume_literal("table_def")
        _t2040 = self.parse_relation_id()
        relation_id1294 = _t2040
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1295 = []
        cond1296 = self.match_lookahead_literal("(", 0)
        while cond1296:
            _t2041 = self.parse_export_iceberg_column()
            item1297 = _t2041
            xs1295.append(item1297)
            cond1296 = self.match_lookahead_literal("(", 0)
        export_iceberg_columns1298 = xs1295
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("table_properties")
        xs1299 = []
        cond1300 = self.match_lookahead_literal("(", 0)
        while cond1300:
            _t2042 = self.parse_iceberg_property_entry()
            item1301 = _t2042
            xs1299.append(item1301)
            cond1300 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1302 = xs1299
        self.consume_literal(")")
        if self.match_lookahead_literal("{", 0):
            _t2044 = self.parse_config_dict()
            _t2043 = _t2044
        else:
            _t2043 = None
        config_dict1303 = _t2043
        self.consume_literal(")")
        _t2045 = self.construct_export_iceberg_config_full(iceberg_locator1292, iceberg_catalog_config1293, relation_id1294, export_iceberg_columns1298, iceberg_property_entrys1302, config_dict1303)
        result1305 = _t2045
        self.record_span(span_start1304, "ExportIcebergConfig")
        return result1305

    def parse_export_iceberg_column(self) -> transactions_pb2.ExportIcebergColumn:
        span_start1308 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_column")
        string1306 = self.consume_terminal("STRING")
        _t2046 = self.parse_boolean_value()
        boolean_value1307 = _t2046
        self.consume_literal(")")
        _t2047 = transactions_pb2.ExportIcebergColumn(name=string1306, nullable=boolean_value1307)
        result1309 = _t2047
        self.record_span(span_start1308, "ExportIcebergColumn")
        return result1309


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
