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
            _t2051 = value.HasField("int32_value")
        else:
            _t2051 = False
        if _t2051:
            assert value is not None
            return value.int32_value
        else:
            _t2052 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2053 = value.HasField("int_value")
        else:
            _t2053 = False
        if _t2053:
            assert value is not None
            return value.int_value
        else:
            _t2054 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2055 = value.HasField("string_value")
        else:
            _t2055 = False
        if _t2055:
            assert value is not None
            return value.string_value
        else:
            _t2056 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2057 = value.HasField("boolean_value")
        else:
            _t2057 = False
        if _t2057:
            assert value is not None
            return value.boolean_value
        else:
            _t2058 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2059 = value.HasField("string_value")
        else:
            _t2059 = False
        if _t2059:
            assert value is not None
            return [value.string_value]
        else:
            _t2060 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
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
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2063 = value.HasField("float_value")
        else:
            _t2063 = False
        if _t2063:
            assert value is not None
            return value.float_value
        else:
            _t2064 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2065 = value.HasField("string_value")
        else:
            _t2065 = False
        if _t2065:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2066 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2067 = value.HasField("uint128_value")
        else:
            _t2067 = False
        if _t2067:
            assert value is not None
            return value.uint128_value
        else:
            _t2068 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2069 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2069
        _t2070 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2070
        _t2071 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2071
        _t2072 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2072
        _t2073 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2073
        _t2074 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2074
        _t2075 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2075
        _t2076 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2076
        _t2077 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2077
        _t2078 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2078
        _t2079 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t2079
        _t2080 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2080
        _t2081 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t2081

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2082 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2082
        _t2083 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2083
        _t2084 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2084
        _t2085 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2085
        _t2086 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2086
        _t2087 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2087
        _t2088 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2088
        _t2089 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2089
        _t2090 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2090
        _t2091 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2091
        _t2092 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2092

    def default_configure(self) -> transactions_pb2.Configure:
        _t2093 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2093
        _t2094 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2094

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
        _t2095 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2095
        _t2096 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2096
        _t2097 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t2097

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2098 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2098
        _t2099 = self._extract_value_string(config.get("compression"), "")
        compression = _t2099
        _t2100 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2100
        _t2101 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2101
        _t2102 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2102
        _t2103 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2103
        _t2104 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2104
        _t2105 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2105

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2106 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t2106

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2107 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2107

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, columns: Sequence[transactions_pb2.ExportIcebergColumn], create_table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2108 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2108
        _t2109 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2109
        _t2110 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2110
        create_table_props = dict(create_table_property_pairs)
        _t2111 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, columns=columns, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, create_table_properties=create_table_props)
        return _t2111

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start662 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1313 = self.parse_configure()
            _t1312 = _t1313
        else:
            _t1312 = None
        configure656 = _t1312
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1315 = self.parse_sync()
            _t1314 = _t1315
        else:
            _t1314 = None
        sync657 = _t1314
        xs658 = []
        cond659 = self.match_lookahead_literal("(", 0)
        while cond659:
            _t1316 = self.parse_epoch()
            item660 = _t1316
            xs658.append(item660)
            cond659 = self.match_lookahead_literal("(", 0)
        epochs661 = xs658
        self.consume_literal(")")
        _t1317 = self.default_configure()
        _t1318 = transactions_pb2.Transaction(epochs=epochs661, configure=(configure656 if configure656 is not None else _t1317), sync=sync657)
        result663 = _t1318
        self.record_span(span_start662, "Transaction")
        return result663

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start665 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1319 = self.parse_config_dict()
        config_dict664 = _t1319
        self.consume_literal(")")
        _t1320 = self.construct_configure(config_dict664)
        result666 = _t1320
        self.record_span(span_start665, "Configure")
        return result666

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs667 = []
        cond668 = self.match_lookahead_literal(":", 0)
        while cond668:
            _t1321 = self.parse_config_key_value()
            item669 = _t1321
            xs667.append(item669)
            cond668 = self.match_lookahead_literal(":", 0)
        config_key_values670 = xs667
        self.consume_literal("}")
        return config_key_values670

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol671 = self.consume_terminal("SYMBOL")
        _t1322 = self.parse_raw_value()
        raw_value672 = _t1322
        return (symbol671, raw_value672,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start686 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1323 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1324 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1325 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1327 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1328 = 0
                            else:
                                _t1328 = -1
                            _t1327 = _t1328
                        _t1326 = _t1327
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1329 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1330 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1331 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1332 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1333 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1334 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1335 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1336 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1337 = 10
                                                        else:
                                                            _t1337 = -1
                                                        _t1336 = _t1337
                                                    _t1335 = _t1336
                                                _t1334 = _t1335
                                            _t1333 = _t1334
                                        _t1332 = _t1333
                                    _t1331 = _t1332
                                _t1330 = _t1331
                            _t1329 = _t1330
                        _t1326 = _t1329
                    _t1325 = _t1326
                _t1324 = _t1325
            _t1323 = _t1324
        prediction673 = _t1323
        if prediction673 == 12:
            _t1339 = self.parse_boolean_value()
            boolean_value685 = _t1339
            _t1340 = logic_pb2.Value(boolean_value=boolean_value685)
            _t1338 = _t1340
        else:
            if prediction673 == 11:
                self.consume_literal("missing")
                _t1342 = logic_pb2.MissingValue()
                _t1343 = logic_pb2.Value(missing_value=_t1342)
                _t1341 = _t1343
            else:
                if prediction673 == 10:
                    decimal684 = self.consume_terminal("DECIMAL")
                    _t1345 = logic_pb2.Value(decimal_value=decimal684)
                    _t1344 = _t1345
                else:
                    if prediction673 == 9:
                        int128683 = self.consume_terminal("INT128")
                        _t1347 = logic_pb2.Value(int128_value=int128683)
                        _t1346 = _t1347
                    else:
                        if prediction673 == 8:
                            uint128682 = self.consume_terminal("UINT128")
                            _t1349 = logic_pb2.Value(uint128_value=uint128682)
                            _t1348 = _t1349
                        else:
                            if prediction673 == 7:
                                uint32681 = self.consume_terminal("UINT32")
                                _t1351 = logic_pb2.Value(uint32_value=uint32681)
                                _t1350 = _t1351
                            else:
                                if prediction673 == 6:
                                    float680 = self.consume_terminal("FLOAT")
                                    _t1353 = logic_pb2.Value(float_value=float680)
                                    _t1352 = _t1353
                                else:
                                    if prediction673 == 5:
                                        float32679 = self.consume_terminal("FLOAT32")
                                        _t1355 = logic_pb2.Value(float32_value=float32679)
                                        _t1354 = _t1355
                                    else:
                                        if prediction673 == 4:
                                            int678 = self.consume_terminal("INT")
                                            _t1357 = logic_pb2.Value(int_value=int678)
                                            _t1356 = _t1357
                                        else:
                                            if prediction673 == 3:
                                                int32677 = self.consume_terminal("INT32")
                                                _t1359 = logic_pb2.Value(int32_value=int32677)
                                                _t1358 = _t1359
                                            else:
                                                if prediction673 == 2:
                                                    string676 = self.consume_terminal("STRING")
                                                    _t1361 = logic_pb2.Value(string_value=string676)
                                                    _t1360 = _t1361
                                                else:
                                                    if prediction673 == 1:
                                                        _t1363 = self.parse_raw_datetime()
                                                        raw_datetime675 = _t1363
                                                        _t1364 = logic_pb2.Value(datetime_value=raw_datetime675)
                                                        _t1362 = _t1364
                                                    else:
                                                        if prediction673 == 0:
                                                            _t1366 = self.parse_raw_date()
                                                            raw_date674 = _t1366
                                                            _t1367 = logic_pb2.Value(date_value=raw_date674)
                                                            _t1365 = _t1367
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1362 = _t1365
                                                    _t1360 = _t1362
                                                _t1358 = _t1360
                                            _t1356 = _t1358
                                        _t1354 = _t1356
                                    _t1352 = _t1354
                                _t1350 = _t1352
                            _t1348 = _t1350
                        _t1346 = _t1348
                    _t1344 = _t1346
                _t1341 = _t1344
            _t1338 = _t1341
        result687 = _t1338
        self.record_span(span_start686, "Value")
        return result687

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start691 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int688 = self.consume_terminal("INT")
        int_3689 = self.consume_terminal("INT")
        int_4690 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1368 = logic_pb2.DateValue(year=int(int688), month=int(int_3689), day=int(int_4690))
        result692 = _t1368
        self.record_span(span_start691, "DateValue")
        return result692

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start700 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int693 = self.consume_terminal("INT")
        int_3694 = self.consume_terminal("INT")
        int_4695 = self.consume_terminal("INT")
        int_5696 = self.consume_terminal("INT")
        int_6697 = self.consume_terminal("INT")
        int_7698 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1369 = self.consume_terminal("INT")
        else:
            _t1369 = None
        int_8699 = _t1369
        self.consume_literal(")")
        _t1370 = logic_pb2.DateTimeValue(year=int(int693), month=int(int_3694), day=int(int_4695), hour=int(int_5696), minute=int(int_6697), second=int(int_7698), microsecond=int((int_8699 if int_8699 is not None else 0)))
        result701 = _t1370
        self.record_span(span_start700, "DateTimeValue")
        return result701

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1371 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1372 = 1
            else:
                _t1372 = -1
            _t1371 = _t1372
        prediction702 = _t1371
        if prediction702 == 1:
            self.consume_literal("false")
            _t1373 = False
        else:
            if prediction702 == 0:
                self.consume_literal("true")
                _t1374 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1373 = _t1374
        return _t1373

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start707 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs703 = []
        cond704 = self.match_lookahead_literal(":", 0)
        while cond704:
            _t1375 = self.parse_fragment_id()
            item705 = _t1375
            xs703.append(item705)
            cond704 = self.match_lookahead_literal(":", 0)
        fragment_ids706 = xs703
        self.consume_literal(")")
        _t1376 = transactions_pb2.Sync(fragments=fragment_ids706)
        result708 = _t1376
        self.record_span(span_start707, "Sync")
        return result708

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start710 = self.span_start()
        self.consume_literal(":")
        symbol709 = self.consume_terminal("SYMBOL")
        result711 = fragments_pb2.FragmentId(id=symbol709.encode())
        self.record_span(span_start710, "FragmentId")
        return result711

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start714 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1378 = self.parse_epoch_writes()
            _t1377 = _t1378
        else:
            _t1377 = None
        epoch_writes712 = _t1377
        if self.match_lookahead_literal("(", 0):
            _t1380 = self.parse_epoch_reads()
            _t1379 = _t1380
        else:
            _t1379 = None
        epoch_reads713 = _t1379
        self.consume_literal(")")
        _t1381 = transactions_pb2.Epoch(writes=(epoch_writes712 if epoch_writes712 is not None else []), reads=(epoch_reads713 if epoch_reads713 is not None else []))
        result715 = _t1381
        self.record_span(span_start714, "Epoch")
        return result715

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs716 = []
        cond717 = self.match_lookahead_literal("(", 0)
        while cond717:
            _t1382 = self.parse_write()
            item718 = _t1382
            xs716.append(item718)
            cond717 = self.match_lookahead_literal("(", 0)
        writes719 = xs716
        self.consume_literal(")")
        return writes719

    def parse_write(self) -> transactions_pb2.Write:
        span_start725 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1384 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1385 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1386 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1387 = 2
                        else:
                            _t1387 = -1
                        _t1386 = _t1387
                    _t1385 = _t1386
                _t1384 = _t1385
            _t1383 = _t1384
        else:
            _t1383 = -1
        prediction720 = _t1383
        if prediction720 == 3:
            _t1389 = self.parse_snapshot()
            snapshot724 = _t1389
            _t1390 = transactions_pb2.Write(snapshot=snapshot724)
            _t1388 = _t1390
        else:
            if prediction720 == 2:
                _t1392 = self.parse_context()
                context723 = _t1392
                _t1393 = transactions_pb2.Write(context=context723)
                _t1391 = _t1393
            else:
                if prediction720 == 1:
                    _t1395 = self.parse_undefine()
                    undefine722 = _t1395
                    _t1396 = transactions_pb2.Write(undefine=undefine722)
                    _t1394 = _t1396
                else:
                    if prediction720 == 0:
                        _t1398 = self.parse_define()
                        define721 = _t1398
                        _t1399 = transactions_pb2.Write(define=define721)
                        _t1397 = _t1399
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1394 = _t1397
                _t1391 = _t1394
            _t1388 = _t1391
        result726 = _t1388
        self.record_span(span_start725, "Write")
        return result726

    def parse_define(self) -> transactions_pb2.Define:
        span_start728 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1400 = self.parse_fragment()
        fragment727 = _t1400
        self.consume_literal(")")
        _t1401 = transactions_pb2.Define(fragment=fragment727)
        result729 = _t1401
        self.record_span(span_start728, "Define")
        return result729

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start735 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1402 = self.parse_new_fragment_id()
        new_fragment_id730 = _t1402
        xs731 = []
        cond732 = self.match_lookahead_literal("(", 0)
        while cond732:
            _t1403 = self.parse_declaration()
            item733 = _t1403
            xs731.append(item733)
            cond732 = self.match_lookahead_literal("(", 0)
        declarations734 = xs731
        self.consume_literal(")")
        result736 = self.construct_fragment(new_fragment_id730, declarations734)
        self.record_span(span_start735, "Fragment")
        return result736

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start738 = self.span_start()
        _t1404 = self.parse_fragment_id()
        fragment_id737 = _t1404
        self.start_fragment(fragment_id737)
        result739 = fragment_id737
        self.record_span(span_start738, "FragmentId")
        return result739

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start745 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1406 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1407 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1408 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1409 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1410 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1411 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1412 = 1
                                    else:
                                        _t1412 = -1
                                    _t1411 = _t1412
                                _t1410 = _t1411
                            _t1409 = _t1410
                        _t1408 = _t1409
                    _t1407 = _t1408
                _t1406 = _t1407
            _t1405 = _t1406
        else:
            _t1405 = -1
        prediction740 = _t1405
        if prediction740 == 3:
            _t1414 = self.parse_data()
            data744 = _t1414
            _t1415 = logic_pb2.Declaration(data=data744)
            _t1413 = _t1415
        else:
            if prediction740 == 2:
                _t1417 = self.parse_constraint()
                constraint743 = _t1417
                _t1418 = logic_pb2.Declaration(constraint=constraint743)
                _t1416 = _t1418
            else:
                if prediction740 == 1:
                    _t1420 = self.parse_algorithm()
                    algorithm742 = _t1420
                    _t1421 = logic_pb2.Declaration(algorithm=algorithm742)
                    _t1419 = _t1421
                else:
                    if prediction740 == 0:
                        _t1423 = self.parse_def()
                        def741 = _t1423
                        _t1424 = logic_pb2.Declaration()
                        getattr(_t1424, 'def').CopyFrom(def741)
                        _t1422 = _t1424
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1419 = _t1422
                _t1416 = _t1419
            _t1413 = _t1416
        result746 = _t1413
        self.record_span(span_start745, "Declaration")
        return result746

    def parse_def(self) -> logic_pb2.Def:
        span_start750 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1425 = self.parse_relation_id()
        relation_id747 = _t1425
        _t1426 = self.parse_abstraction()
        abstraction748 = _t1426
        if self.match_lookahead_literal("(", 0):
            _t1428 = self.parse_attrs()
            _t1427 = _t1428
        else:
            _t1427 = None
        attrs749 = _t1427
        self.consume_literal(")")
        _t1429 = logic_pb2.Def(name=relation_id747, body=abstraction748, attrs=(attrs749 if attrs749 is not None else []))
        result751 = _t1429
        self.record_span(span_start750, "Def")
        return result751

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start755 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1430 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1431 = 1
            else:
                _t1431 = -1
            _t1430 = _t1431
        prediction752 = _t1430
        if prediction752 == 1:
            uint128754 = self.consume_terminal("UINT128")
            _t1432 = logic_pb2.RelationId(id_low=uint128754.low, id_high=uint128754.high)
        else:
            if prediction752 == 0:
                self.consume_literal(":")
                symbol753 = self.consume_terminal("SYMBOL")
                _t1433 = self.relation_id_from_string(symbol753)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1432 = _t1433
        result756 = _t1432
        self.record_span(span_start755, "RelationId")
        return result756

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start759 = self.span_start()
        self.consume_literal("(")
        _t1434 = self.parse_bindings()
        bindings757 = _t1434
        _t1435 = self.parse_formula()
        formula758 = _t1435
        self.consume_literal(")")
        _t1436 = logic_pb2.Abstraction(vars=(list(bindings757[0]) + list(bindings757[1] if bindings757[1] is not None else [])), value=formula758)
        result760 = _t1436
        self.record_span(span_start759, "Abstraction")
        return result760

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs761 = []
        cond762 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond762:
            _t1437 = self.parse_binding()
            item763 = _t1437
            xs761.append(item763)
            cond762 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings764 = xs761
        if self.match_lookahead_literal("|", 0):
            _t1439 = self.parse_value_bindings()
            _t1438 = _t1439
        else:
            _t1438 = None
        value_bindings765 = _t1438
        self.consume_literal("]")
        return (bindings764, (value_bindings765 if value_bindings765 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start768 = self.span_start()
        symbol766 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1440 = self.parse_type()
        type767 = _t1440
        _t1441 = logic_pb2.Var(name=symbol766)
        _t1442 = logic_pb2.Binding(var=_t1441, type=type767)
        result769 = _t1442
        self.record_span(span_start768, "Binding")
        return result769

    def parse_type(self) -> logic_pb2.Type:
        span_start785 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1443 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1444 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1445 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1446 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1447 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1448 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1449 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1450 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1451 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1452 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1453 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1454 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1455 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1456 = 9
                                                            else:
                                                                _t1456 = -1
                                                            _t1455 = _t1456
                                                        _t1454 = _t1455
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
        prediction770 = _t1443
        if prediction770 == 13:
            _t1458 = self.parse_uint32_type()
            uint32_type784 = _t1458
            _t1459 = logic_pb2.Type(uint32_type=uint32_type784)
            _t1457 = _t1459
        else:
            if prediction770 == 12:
                _t1461 = self.parse_float32_type()
                float32_type783 = _t1461
                _t1462 = logic_pb2.Type(float32_type=float32_type783)
                _t1460 = _t1462
            else:
                if prediction770 == 11:
                    _t1464 = self.parse_int32_type()
                    int32_type782 = _t1464
                    _t1465 = logic_pb2.Type(int32_type=int32_type782)
                    _t1463 = _t1465
                else:
                    if prediction770 == 10:
                        _t1467 = self.parse_boolean_type()
                        boolean_type781 = _t1467
                        _t1468 = logic_pb2.Type(boolean_type=boolean_type781)
                        _t1466 = _t1468
                    else:
                        if prediction770 == 9:
                            _t1470 = self.parse_decimal_type()
                            decimal_type780 = _t1470
                            _t1471 = logic_pb2.Type(decimal_type=decimal_type780)
                            _t1469 = _t1471
                        else:
                            if prediction770 == 8:
                                _t1473 = self.parse_missing_type()
                                missing_type779 = _t1473
                                _t1474 = logic_pb2.Type(missing_type=missing_type779)
                                _t1472 = _t1474
                            else:
                                if prediction770 == 7:
                                    _t1476 = self.parse_datetime_type()
                                    datetime_type778 = _t1476
                                    _t1477 = logic_pb2.Type(datetime_type=datetime_type778)
                                    _t1475 = _t1477
                                else:
                                    if prediction770 == 6:
                                        _t1479 = self.parse_date_type()
                                        date_type777 = _t1479
                                        _t1480 = logic_pb2.Type(date_type=date_type777)
                                        _t1478 = _t1480
                                    else:
                                        if prediction770 == 5:
                                            _t1482 = self.parse_int128_type()
                                            int128_type776 = _t1482
                                            _t1483 = logic_pb2.Type(int128_type=int128_type776)
                                            _t1481 = _t1483
                                        else:
                                            if prediction770 == 4:
                                                _t1485 = self.parse_uint128_type()
                                                uint128_type775 = _t1485
                                                _t1486 = logic_pb2.Type(uint128_type=uint128_type775)
                                                _t1484 = _t1486
                                            else:
                                                if prediction770 == 3:
                                                    _t1488 = self.parse_float_type()
                                                    float_type774 = _t1488
                                                    _t1489 = logic_pb2.Type(float_type=float_type774)
                                                    _t1487 = _t1489
                                                else:
                                                    if prediction770 == 2:
                                                        _t1491 = self.parse_int_type()
                                                        int_type773 = _t1491
                                                        _t1492 = logic_pb2.Type(int_type=int_type773)
                                                        _t1490 = _t1492
                                                    else:
                                                        if prediction770 == 1:
                                                            _t1494 = self.parse_string_type()
                                                            string_type772 = _t1494
                                                            _t1495 = logic_pb2.Type(string_type=string_type772)
                                                            _t1493 = _t1495
                                                        else:
                                                            if prediction770 == 0:
                                                                _t1497 = self.parse_unspecified_type()
                                                                unspecified_type771 = _t1497
                                                                _t1498 = logic_pb2.Type(unspecified_type=unspecified_type771)
                                                                _t1496 = _t1498
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
                _t1460 = _t1463
            _t1457 = _t1460
        result786 = _t1457
        self.record_span(span_start785, "Type")
        return result786

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start787 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1499 = logic_pb2.UnspecifiedType()
        result788 = _t1499
        self.record_span(span_start787, "UnspecifiedType")
        return result788

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start789 = self.span_start()
        self.consume_literal("STRING")
        _t1500 = logic_pb2.StringType()
        result790 = _t1500
        self.record_span(span_start789, "StringType")
        return result790

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start791 = self.span_start()
        self.consume_literal("INT")
        _t1501 = logic_pb2.IntType()
        result792 = _t1501
        self.record_span(span_start791, "IntType")
        return result792

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start793 = self.span_start()
        self.consume_literal("FLOAT")
        _t1502 = logic_pb2.FloatType()
        result794 = _t1502
        self.record_span(span_start793, "FloatType")
        return result794

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start795 = self.span_start()
        self.consume_literal("UINT128")
        _t1503 = logic_pb2.UInt128Type()
        result796 = _t1503
        self.record_span(span_start795, "UInt128Type")
        return result796

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start797 = self.span_start()
        self.consume_literal("INT128")
        _t1504 = logic_pb2.Int128Type()
        result798 = _t1504
        self.record_span(span_start797, "Int128Type")
        return result798

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start799 = self.span_start()
        self.consume_literal("DATE")
        _t1505 = logic_pb2.DateType()
        result800 = _t1505
        self.record_span(span_start799, "DateType")
        return result800

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start801 = self.span_start()
        self.consume_literal("DATETIME")
        _t1506 = logic_pb2.DateTimeType()
        result802 = _t1506
        self.record_span(span_start801, "DateTimeType")
        return result802

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start803 = self.span_start()
        self.consume_literal("MISSING")
        _t1507 = logic_pb2.MissingType()
        result804 = _t1507
        self.record_span(span_start803, "MissingType")
        return result804

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start807 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int805 = self.consume_terminal("INT")
        int_3806 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1508 = logic_pb2.DecimalType(precision=int(int805), scale=int(int_3806))
        result808 = _t1508
        self.record_span(span_start807, "DecimalType")
        return result808

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start809 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1509 = logic_pb2.BooleanType()
        result810 = _t1509
        self.record_span(span_start809, "BooleanType")
        return result810

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start811 = self.span_start()
        self.consume_literal("INT32")
        _t1510 = logic_pb2.Int32Type()
        result812 = _t1510
        self.record_span(span_start811, "Int32Type")
        return result812

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start813 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1511 = logic_pb2.Float32Type()
        result814 = _t1511
        self.record_span(span_start813, "Float32Type")
        return result814

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start815 = self.span_start()
        self.consume_literal("UINT32")
        _t1512 = logic_pb2.UInt32Type()
        result816 = _t1512
        self.record_span(span_start815, "UInt32Type")
        return result816

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs817 = []
        cond818 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond818:
            _t1513 = self.parse_binding()
            item819 = _t1513
            xs817.append(item819)
            cond818 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings820 = xs817
        return bindings820

    def parse_formula(self) -> logic_pb2.Formula:
        span_start835 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1515 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1516 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1517 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1518 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1519 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1520 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1521 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1522 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1523 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1524 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1525 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1526 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1527 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1528 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1529 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1530 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1531 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1532 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1533 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1534 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1535 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1536 = 10
                                                                                                else:
                                                                                                    _t1536 = -1
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
                        _t1517 = _t1518
                    _t1516 = _t1517
                _t1515 = _t1516
            _t1514 = _t1515
        else:
            _t1514 = -1
        prediction821 = _t1514
        if prediction821 == 12:
            _t1538 = self.parse_cast()
            cast834 = _t1538
            _t1539 = logic_pb2.Formula(cast=cast834)
            _t1537 = _t1539
        else:
            if prediction821 == 11:
                _t1541 = self.parse_rel_atom()
                rel_atom833 = _t1541
                _t1542 = logic_pb2.Formula(rel_atom=rel_atom833)
                _t1540 = _t1542
            else:
                if prediction821 == 10:
                    _t1544 = self.parse_primitive()
                    primitive832 = _t1544
                    _t1545 = logic_pb2.Formula(primitive=primitive832)
                    _t1543 = _t1545
                else:
                    if prediction821 == 9:
                        _t1547 = self.parse_pragma()
                        pragma831 = _t1547
                        _t1548 = logic_pb2.Formula(pragma=pragma831)
                        _t1546 = _t1548
                    else:
                        if prediction821 == 8:
                            _t1550 = self.parse_atom()
                            atom830 = _t1550
                            _t1551 = logic_pb2.Formula(atom=atom830)
                            _t1549 = _t1551
                        else:
                            if prediction821 == 7:
                                _t1553 = self.parse_ffi()
                                ffi829 = _t1553
                                _t1554 = logic_pb2.Formula(ffi=ffi829)
                                _t1552 = _t1554
                            else:
                                if prediction821 == 6:
                                    _t1556 = self.parse_not()
                                    not828 = _t1556
                                    _t1557 = logic_pb2.Formula()
                                    getattr(_t1557, 'not').CopyFrom(not828)
                                    _t1555 = _t1557
                                else:
                                    if prediction821 == 5:
                                        _t1559 = self.parse_disjunction()
                                        disjunction827 = _t1559
                                        _t1560 = logic_pb2.Formula(disjunction=disjunction827)
                                        _t1558 = _t1560
                                    else:
                                        if prediction821 == 4:
                                            _t1562 = self.parse_conjunction()
                                            conjunction826 = _t1562
                                            _t1563 = logic_pb2.Formula(conjunction=conjunction826)
                                            _t1561 = _t1563
                                        else:
                                            if prediction821 == 3:
                                                _t1565 = self.parse_reduce()
                                                reduce825 = _t1565
                                                _t1566 = logic_pb2.Formula(reduce=reduce825)
                                                _t1564 = _t1566
                                            else:
                                                if prediction821 == 2:
                                                    _t1568 = self.parse_exists()
                                                    exists824 = _t1568
                                                    _t1569 = logic_pb2.Formula(exists=exists824)
                                                    _t1567 = _t1569
                                                else:
                                                    if prediction821 == 1:
                                                        _t1571 = self.parse_false()
                                                        false823 = _t1571
                                                        _t1572 = logic_pb2.Formula(disjunction=false823)
                                                        _t1570 = _t1572
                                                    else:
                                                        if prediction821 == 0:
                                                            _t1574 = self.parse_true()
                                                            true822 = _t1574
                                                            _t1575 = logic_pb2.Formula(conjunction=true822)
                                                            _t1573 = _t1575
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
                _t1540 = _t1543
            _t1537 = _t1540
        result836 = _t1537
        self.record_span(span_start835, "Formula")
        return result836

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start837 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1576 = logic_pb2.Conjunction(args=[])
        result838 = _t1576
        self.record_span(span_start837, "Conjunction")
        return result838

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start839 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1577 = logic_pb2.Disjunction(args=[])
        result840 = _t1577
        self.record_span(span_start839, "Disjunction")
        return result840

    def parse_exists(self) -> logic_pb2.Exists:
        span_start843 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1578 = self.parse_bindings()
        bindings841 = _t1578
        _t1579 = self.parse_formula()
        formula842 = _t1579
        self.consume_literal(")")
        _t1580 = logic_pb2.Abstraction(vars=(list(bindings841[0]) + list(bindings841[1] if bindings841[1] is not None else [])), value=formula842)
        _t1581 = logic_pb2.Exists(body=_t1580)
        result844 = _t1581
        self.record_span(span_start843, "Exists")
        return result844

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start848 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1582 = self.parse_abstraction()
        abstraction845 = _t1582
        _t1583 = self.parse_abstraction()
        abstraction_3846 = _t1583
        _t1584 = self.parse_terms()
        terms847 = _t1584
        self.consume_literal(")")
        _t1585 = logic_pb2.Reduce(op=abstraction845, body=abstraction_3846, terms=terms847)
        result849 = _t1585
        self.record_span(span_start848, "Reduce")
        return result849

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs850 = []
        cond851 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond851:
            _t1586 = self.parse_term()
            item852 = _t1586
            xs850.append(item852)
            cond851 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms853 = xs850
        self.consume_literal(")")
        return terms853

    def parse_term(self) -> logic_pb2.Term:
        span_start857 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1587 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1588 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1589 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1590 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1591 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1592 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1593 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1594 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1595 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1596 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1597 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1598 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1599 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1600 = 1
                                                            else:
                                                                _t1600 = -1
                                                            _t1599 = _t1600
                                                        _t1598 = _t1599
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
        prediction854 = _t1587
        if prediction854 == 1:
            _t1602 = self.parse_value()
            value856 = _t1602
            _t1603 = logic_pb2.Term(constant=value856)
            _t1601 = _t1603
        else:
            if prediction854 == 0:
                _t1605 = self.parse_var()
                var855 = _t1605
                _t1606 = logic_pb2.Term(var=var855)
                _t1604 = _t1606
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1601 = _t1604
        result858 = _t1601
        self.record_span(span_start857, "Term")
        return result858

    def parse_var(self) -> logic_pb2.Var:
        span_start860 = self.span_start()
        symbol859 = self.consume_terminal("SYMBOL")
        _t1607 = logic_pb2.Var(name=symbol859)
        result861 = _t1607
        self.record_span(span_start860, "Var")
        return result861

    def parse_value(self) -> logic_pb2.Value:
        span_start875 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1608 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1609 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1610 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1612 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1613 = 0
                            else:
                                _t1613 = -1
                            _t1612 = _t1613
                        _t1611 = _t1612
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1614 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1615 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1616 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1617 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1618 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1619 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1620 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1621 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1622 = 10
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
                        _t1611 = _t1614
                    _t1610 = _t1611
                _t1609 = _t1610
            _t1608 = _t1609
        prediction862 = _t1608
        if prediction862 == 12:
            _t1624 = self.parse_boolean_value()
            boolean_value874 = _t1624
            _t1625 = logic_pb2.Value(boolean_value=boolean_value874)
            _t1623 = _t1625
        else:
            if prediction862 == 11:
                self.consume_literal("missing")
                _t1627 = logic_pb2.MissingValue()
                _t1628 = logic_pb2.Value(missing_value=_t1627)
                _t1626 = _t1628
            else:
                if prediction862 == 10:
                    formatted_decimal873 = self.consume_terminal("DECIMAL")
                    _t1630 = logic_pb2.Value(decimal_value=formatted_decimal873)
                    _t1629 = _t1630
                else:
                    if prediction862 == 9:
                        formatted_int128872 = self.consume_terminal("INT128")
                        _t1632 = logic_pb2.Value(int128_value=formatted_int128872)
                        _t1631 = _t1632
                    else:
                        if prediction862 == 8:
                            formatted_uint128871 = self.consume_terminal("UINT128")
                            _t1634 = logic_pb2.Value(uint128_value=formatted_uint128871)
                            _t1633 = _t1634
                        else:
                            if prediction862 == 7:
                                formatted_uint32870 = self.consume_terminal("UINT32")
                                _t1636 = logic_pb2.Value(uint32_value=formatted_uint32870)
                                _t1635 = _t1636
                            else:
                                if prediction862 == 6:
                                    formatted_float869 = self.consume_terminal("FLOAT")
                                    _t1638 = logic_pb2.Value(float_value=formatted_float869)
                                    _t1637 = _t1638
                                else:
                                    if prediction862 == 5:
                                        formatted_float32868 = self.consume_terminal("FLOAT32")
                                        _t1640 = logic_pb2.Value(float32_value=formatted_float32868)
                                        _t1639 = _t1640
                                    else:
                                        if prediction862 == 4:
                                            formatted_int867 = self.consume_terminal("INT")
                                            _t1642 = logic_pb2.Value(int_value=formatted_int867)
                                            _t1641 = _t1642
                                        else:
                                            if prediction862 == 3:
                                                formatted_int32866 = self.consume_terminal("INT32")
                                                _t1644 = logic_pb2.Value(int32_value=formatted_int32866)
                                                _t1643 = _t1644
                                            else:
                                                if prediction862 == 2:
                                                    formatted_string865 = self.consume_terminal("STRING")
                                                    _t1646 = logic_pb2.Value(string_value=formatted_string865)
                                                    _t1645 = _t1646
                                                else:
                                                    if prediction862 == 1:
                                                        _t1648 = self.parse_datetime()
                                                        datetime864 = _t1648
                                                        _t1649 = logic_pb2.Value(datetime_value=datetime864)
                                                        _t1647 = _t1649
                                                    else:
                                                        if prediction862 == 0:
                                                            _t1651 = self.parse_date()
                                                            date863 = _t1651
                                                            _t1652 = logic_pb2.Value(date_value=date863)
                                                            _t1650 = _t1652
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1647 = _t1650
                                                    _t1645 = _t1647
                                                _t1643 = _t1645
                                            _t1641 = _t1643
                                        _t1639 = _t1641
                                    _t1637 = _t1639
                                _t1635 = _t1637
                            _t1633 = _t1635
                        _t1631 = _t1633
                    _t1629 = _t1631
                _t1626 = _t1629
            _t1623 = _t1626
        result876 = _t1623
        self.record_span(span_start875, "Value")
        return result876

    def parse_date(self) -> logic_pb2.DateValue:
        span_start880 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int877 = self.consume_terminal("INT")
        formatted_int_3878 = self.consume_terminal("INT")
        formatted_int_4879 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1653 = logic_pb2.DateValue(year=int(formatted_int877), month=int(formatted_int_3878), day=int(formatted_int_4879))
        result881 = _t1653
        self.record_span(span_start880, "DateValue")
        return result881

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start889 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int882 = self.consume_terminal("INT")
        formatted_int_3883 = self.consume_terminal("INT")
        formatted_int_4884 = self.consume_terminal("INT")
        formatted_int_5885 = self.consume_terminal("INT")
        formatted_int_6886 = self.consume_terminal("INT")
        formatted_int_7887 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1654 = self.consume_terminal("INT")
        else:
            _t1654 = None
        formatted_int_8888 = _t1654
        self.consume_literal(")")
        _t1655 = logic_pb2.DateTimeValue(year=int(formatted_int882), month=int(formatted_int_3883), day=int(formatted_int_4884), hour=int(formatted_int_5885), minute=int(formatted_int_6886), second=int(formatted_int_7887), microsecond=int((formatted_int_8888 if formatted_int_8888 is not None else 0)))
        result890 = _t1655
        self.record_span(span_start889, "DateTimeValue")
        return result890

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start895 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs891 = []
        cond892 = self.match_lookahead_literal("(", 0)
        while cond892:
            _t1656 = self.parse_formula()
            item893 = _t1656
            xs891.append(item893)
            cond892 = self.match_lookahead_literal("(", 0)
        formulas894 = xs891
        self.consume_literal(")")
        _t1657 = logic_pb2.Conjunction(args=formulas894)
        result896 = _t1657
        self.record_span(span_start895, "Conjunction")
        return result896

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start901 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs897 = []
        cond898 = self.match_lookahead_literal("(", 0)
        while cond898:
            _t1658 = self.parse_formula()
            item899 = _t1658
            xs897.append(item899)
            cond898 = self.match_lookahead_literal("(", 0)
        formulas900 = xs897
        self.consume_literal(")")
        _t1659 = logic_pb2.Disjunction(args=formulas900)
        result902 = _t1659
        self.record_span(span_start901, "Disjunction")
        return result902

    def parse_not(self) -> logic_pb2.Not:
        span_start904 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1660 = self.parse_formula()
        formula903 = _t1660
        self.consume_literal(")")
        _t1661 = logic_pb2.Not(arg=formula903)
        result905 = _t1661
        self.record_span(span_start904, "Not")
        return result905

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start909 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1662 = self.parse_name()
        name906 = _t1662
        _t1663 = self.parse_ffi_args()
        ffi_args907 = _t1663
        _t1664 = self.parse_terms()
        terms908 = _t1664
        self.consume_literal(")")
        _t1665 = logic_pb2.FFI(name=name906, args=ffi_args907, terms=terms908)
        result910 = _t1665
        self.record_span(span_start909, "FFI")
        return result910

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol911 = self.consume_terminal("SYMBOL")
        return symbol911

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs912 = []
        cond913 = self.match_lookahead_literal("(", 0)
        while cond913:
            _t1666 = self.parse_abstraction()
            item914 = _t1666
            xs912.append(item914)
            cond913 = self.match_lookahead_literal("(", 0)
        abstractions915 = xs912
        self.consume_literal(")")
        return abstractions915

    def parse_atom(self) -> logic_pb2.Atom:
        span_start921 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1667 = self.parse_relation_id()
        relation_id916 = _t1667
        xs917 = []
        cond918 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond918:
            _t1668 = self.parse_term()
            item919 = _t1668
            xs917.append(item919)
            cond918 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms920 = xs917
        self.consume_literal(")")
        _t1669 = logic_pb2.Atom(name=relation_id916, terms=terms920)
        result922 = _t1669
        self.record_span(span_start921, "Atom")
        return result922

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start928 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1670 = self.parse_name()
        name923 = _t1670
        xs924 = []
        cond925 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond925:
            _t1671 = self.parse_term()
            item926 = _t1671
            xs924.append(item926)
            cond925 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms927 = xs924
        self.consume_literal(")")
        _t1672 = logic_pb2.Pragma(name=name923, terms=terms927)
        result929 = _t1672
        self.record_span(span_start928, "Pragma")
        return result929

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start945 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1674 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1675 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1676 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1677 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1678 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1679 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1680 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1681 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1682 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1683 = 7
                                                else:
                                                    _t1683 = -1
                                                _t1682 = _t1683
                                            _t1681 = _t1682
                                        _t1680 = _t1681
                                    _t1679 = _t1680
                                _t1678 = _t1679
                            _t1677 = _t1678
                        _t1676 = _t1677
                    _t1675 = _t1676
                _t1674 = _t1675
            _t1673 = _t1674
        else:
            _t1673 = -1
        prediction930 = _t1673
        if prediction930 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1685 = self.parse_name()
            name940 = _t1685
            xs941 = []
            cond942 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond942:
                _t1686 = self.parse_rel_term()
                item943 = _t1686
                xs941.append(item943)
                cond942 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms944 = xs941
            self.consume_literal(")")
            _t1687 = logic_pb2.Primitive(name=name940, terms=rel_terms944)
            _t1684 = _t1687
        else:
            if prediction930 == 8:
                _t1689 = self.parse_divide()
                divide939 = _t1689
                _t1688 = divide939
            else:
                if prediction930 == 7:
                    _t1691 = self.parse_multiply()
                    multiply938 = _t1691
                    _t1690 = multiply938
                else:
                    if prediction930 == 6:
                        _t1693 = self.parse_minus()
                        minus937 = _t1693
                        _t1692 = minus937
                    else:
                        if prediction930 == 5:
                            _t1695 = self.parse_add()
                            add936 = _t1695
                            _t1694 = add936
                        else:
                            if prediction930 == 4:
                                _t1697 = self.parse_gt_eq()
                                gt_eq935 = _t1697
                                _t1696 = gt_eq935
                            else:
                                if prediction930 == 3:
                                    _t1699 = self.parse_gt()
                                    gt934 = _t1699
                                    _t1698 = gt934
                                else:
                                    if prediction930 == 2:
                                        _t1701 = self.parse_lt_eq()
                                        lt_eq933 = _t1701
                                        _t1700 = lt_eq933
                                    else:
                                        if prediction930 == 1:
                                            _t1703 = self.parse_lt()
                                            lt932 = _t1703
                                            _t1702 = lt932
                                        else:
                                            if prediction930 == 0:
                                                _t1705 = self.parse_eq()
                                                eq931 = _t1705
                                                _t1704 = eq931
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1702 = _t1704
                                        _t1700 = _t1702
                                    _t1698 = _t1700
                                _t1696 = _t1698
                            _t1694 = _t1696
                        _t1692 = _t1694
                    _t1690 = _t1692
                _t1688 = _t1690
            _t1684 = _t1688
        result946 = _t1684
        self.record_span(span_start945, "Primitive")
        return result946

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start949 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1706 = self.parse_term()
        term947 = _t1706
        _t1707 = self.parse_term()
        term_3948 = _t1707
        self.consume_literal(")")
        _t1708 = logic_pb2.RelTerm(term=term947)
        _t1709 = logic_pb2.RelTerm(term=term_3948)
        _t1710 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1708, _t1709])
        result950 = _t1710
        self.record_span(span_start949, "Primitive")
        return result950

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start953 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1711 = self.parse_term()
        term951 = _t1711
        _t1712 = self.parse_term()
        term_3952 = _t1712
        self.consume_literal(")")
        _t1713 = logic_pb2.RelTerm(term=term951)
        _t1714 = logic_pb2.RelTerm(term=term_3952)
        _t1715 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1713, _t1714])
        result954 = _t1715
        self.record_span(span_start953, "Primitive")
        return result954

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start957 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1716 = self.parse_term()
        term955 = _t1716
        _t1717 = self.parse_term()
        term_3956 = _t1717
        self.consume_literal(")")
        _t1718 = logic_pb2.RelTerm(term=term955)
        _t1719 = logic_pb2.RelTerm(term=term_3956)
        _t1720 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1718, _t1719])
        result958 = _t1720
        self.record_span(span_start957, "Primitive")
        return result958

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start961 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1721 = self.parse_term()
        term959 = _t1721
        _t1722 = self.parse_term()
        term_3960 = _t1722
        self.consume_literal(")")
        _t1723 = logic_pb2.RelTerm(term=term959)
        _t1724 = logic_pb2.RelTerm(term=term_3960)
        _t1725 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1723, _t1724])
        result962 = _t1725
        self.record_span(span_start961, "Primitive")
        return result962

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start965 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1726 = self.parse_term()
        term963 = _t1726
        _t1727 = self.parse_term()
        term_3964 = _t1727
        self.consume_literal(")")
        _t1728 = logic_pb2.RelTerm(term=term963)
        _t1729 = logic_pb2.RelTerm(term=term_3964)
        _t1730 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1728, _t1729])
        result966 = _t1730
        self.record_span(span_start965, "Primitive")
        return result966

    def parse_add(self) -> logic_pb2.Primitive:
        span_start970 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1731 = self.parse_term()
        term967 = _t1731
        _t1732 = self.parse_term()
        term_3968 = _t1732
        _t1733 = self.parse_term()
        term_4969 = _t1733
        self.consume_literal(")")
        _t1734 = logic_pb2.RelTerm(term=term967)
        _t1735 = logic_pb2.RelTerm(term=term_3968)
        _t1736 = logic_pb2.RelTerm(term=term_4969)
        _t1737 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1734, _t1735, _t1736])
        result971 = _t1737
        self.record_span(span_start970, "Primitive")
        return result971

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start975 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1738 = self.parse_term()
        term972 = _t1738
        _t1739 = self.parse_term()
        term_3973 = _t1739
        _t1740 = self.parse_term()
        term_4974 = _t1740
        self.consume_literal(")")
        _t1741 = logic_pb2.RelTerm(term=term972)
        _t1742 = logic_pb2.RelTerm(term=term_3973)
        _t1743 = logic_pb2.RelTerm(term=term_4974)
        _t1744 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1741, _t1742, _t1743])
        result976 = _t1744
        self.record_span(span_start975, "Primitive")
        return result976

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start980 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1745 = self.parse_term()
        term977 = _t1745
        _t1746 = self.parse_term()
        term_3978 = _t1746
        _t1747 = self.parse_term()
        term_4979 = _t1747
        self.consume_literal(")")
        _t1748 = logic_pb2.RelTerm(term=term977)
        _t1749 = logic_pb2.RelTerm(term=term_3978)
        _t1750 = logic_pb2.RelTerm(term=term_4979)
        _t1751 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1748, _t1749, _t1750])
        result981 = _t1751
        self.record_span(span_start980, "Primitive")
        return result981

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start985 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1752 = self.parse_term()
        term982 = _t1752
        _t1753 = self.parse_term()
        term_3983 = _t1753
        _t1754 = self.parse_term()
        term_4984 = _t1754
        self.consume_literal(")")
        _t1755 = logic_pb2.RelTerm(term=term982)
        _t1756 = logic_pb2.RelTerm(term=term_3983)
        _t1757 = logic_pb2.RelTerm(term=term_4984)
        _t1758 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1755, _t1756, _t1757])
        result986 = _t1758
        self.record_span(span_start985, "Primitive")
        return result986

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start990 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1759 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1760 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1761 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1762 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1763 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1764 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1765 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1766 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1767 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1768 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1769 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1770 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1771 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1772 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1773 = 1
                                                                else:
                                                                    _t1773 = -1
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
                        _t1762 = _t1763
                    _t1761 = _t1762
                _t1760 = _t1761
            _t1759 = _t1760
        prediction987 = _t1759
        if prediction987 == 1:
            _t1775 = self.parse_term()
            term989 = _t1775
            _t1776 = logic_pb2.RelTerm(term=term989)
            _t1774 = _t1776
        else:
            if prediction987 == 0:
                _t1778 = self.parse_specialized_value()
                specialized_value988 = _t1778
                _t1779 = logic_pb2.RelTerm(specialized_value=specialized_value988)
                _t1777 = _t1779
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1774 = _t1777
        result991 = _t1774
        self.record_span(span_start990, "RelTerm")
        return result991

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start993 = self.span_start()
        self.consume_literal("#")
        _t1780 = self.parse_raw_value()
        raw_value992 = _t1780
        result994 = raw_value992
        self.record_span(span_start993, "Value")
        return result994

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start1000 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1781 = self.parse_name()
        name995 = _t1781
        xs996 = []
        cond997 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond997:
            _t1782 = self.parse_rel_term()
            item998 = _t1782
            xs996.append(item998)
            cond997 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms999 = xs996
        self.consume_literal(")")
        _t1783 = logic_pb2.RelAtom(name=name995, terms=rel_terms999)
        result1001 = _t1783
        self.record_span(span_start1000, "RelAtom")
        return result1001

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1004 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1784 = self.parse_term()
        term1002 = _t1784
        _t1785 = self.parse_term()
        term_31003 = _t1785
        self.consume_literal(")")
        _t1786 = logic_pb2.Cast(input=term1002, result=term_31003)
        result1005 = _t1786
        self.record_span(span_start1004, "Cast")
        return result1005

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1006 = []
        cond1007 = self.match_lookahead_literal("(", 0)
        while cond1007:
            _t1787 = self.parse_attribute()
            item1008 = _t1787
            xs1006.append(item1008)
            cond1007 = self.match_lookahead_literal("(", 0)
        attributes1009 = xs1006
        self.consume_literal(")")
        return attributes1009

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1015 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1788 = self.parse_name()
        name1010 = _t1788
        xs1011 = []
        cond1012 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1012:
            _t1789 = self.parse_raw_value()
            item1013 = _t1789
            xs1011.append(item1013)
            cond1012 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1014 = xs1011
        self.consume_literal(")")
        _t1790 = logic_pb2.Attribute(name=name1010, args=raw_values1014)
        result1016 = _t1790
        self.record_span(span_start1015, "Attribute")
        return result1016

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1022 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1017 = []
        cond1018 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1018:
            _t1791 = self.parse_relation_id()
            item1019 = _t1791
            xs1017.append(item1019)
            cond1018 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1020 = xs1017
        _t1792 = self.parse_script()
        script1021 = _t1792
        self.consume_literal(")")
        _t1793 = logic_pb2.Algorithm(body=script1021)
        getattr(_t1793, 'global').extend(relation_ids1020)
        result1023 = _t1793
        self.record_span(span_start1022, "Algorithm")
        return result1023

    def parse_script(self) -> logic_pb2.Script:
        span_start1028 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1024 = []
        cond1025 = self.match_lookahead_literal("(", 0)
        while cond1025:
            _t1794 = self.parse_construct()
            item1026 = _t1794
            xs1024.append(item1026)
            cond1025 = self.match_lookahead_literal("(", 0)
        constructs1027 = xs1024
        self.consume_literal(")")
        _t1795 = logic_pb2.Script(constructs=constructs1027)
        result1029 = _t1795
        self.record_span(span_start1028, "Script")
        return result1029

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1033 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1797 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1798 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1799 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1800 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1801 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1802 = 1
                                else:
                                    _t1802 = -1
                                _t1801 = _t1802
                            _t1800 = _t1801
                        _t1799 = _t1800
                    _t1798 = _t1799
                _t1797 = _t1798
            _t1796 = _t1797
        else:
            _t1796 = -1
        prediction1030 = _t1796
        if prediction1030 == 1:
            _t1804 = self.parse_instruction()
            instruction1032 = _t1804
            _t1805 = logic_pb2.Construct(instruction=instruction1032)
            _t1803 = _t1805
        else:
            if prediction1030 == 0:
                _t1807 = self.parse_loop()
                loop1031 = _t1807
                _t1808 = logic_pb2.Construct(loop=loop1031)
                _t1806 = _t1808
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1803 = _t1806
        result1034 = _t1803
        self.record_span(span_start1033, "Construct")
        return result1034

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1037 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1809 = self.parse_init()
        init1035 = _t1809
        _t1810 = self.parse_script()
        script1036 = _t1810
        self.consume_literal(")")
        _t1811 = logic_pb2.Loop(init=init1035, body=script1036)
        result1038 = _t1811
        self.record_span(span_start1037, "Loop")
        return result1038

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1039 = []
        cond1040 = self.match_lookahead_literal("(", 0)
        while cond1040:
            _t1812 = self.parse_instruction()
            item1041 = _t1812
            xs1039.append(item1041)
            cond1040 = self.match_lookahead_literal("(", 0)
        instructions1042 = xs1039
        self.consume_literal(")")
        return instructions1042

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1049 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1814 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1815 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1816 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1817 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1818 = 0
                            else:
                                _t1818 = -1
                            _t1817 = _t1818
                        _t1816 = _t1817
                    _t1815 = _t1816
                _t1814 = _t1815
            _t1813 = _t1814
        else:
            _t1813 = -1
        prediction1043 = _t1813
        if prediction1043 == 4:
            _t1820 = self.parse_monus_def()
            monus_def1048 = _t1820
            _t1821 = logic_pb2.Instruction(monus_def=monus_def1048)
            _t1819 = _t1821
        else:
            if prediction1043 == 3:
                _t1823 = self.parse_monoid_def()
                monoid_def1047 = _t1823
                _t1824 = logic_pb2.Instruction(monoid_def=monoid_def1047)
                _t1822 = _t1824
            else:
                if prediction1043 == 2:
                    _t1826 = self.parse_break()
                    break1046 = _t1826
                    _t1827 = logic_pb2.Instruction()
                    getattr(_t1827, 'break').CopyFrom(break1046)
                    _t1825 = _t1827
                else:
                    if prediction1043 == 1:
                        _t1829 = self.parse_upsert()
                        upsert1045 = _t1829
                        _t1830 = logic_pb2.Instruction(upsert=upsert1045)
                        _t1828 = _t1830
                    else:
                        if prediction1043 == 0:
                            _t1832 = self.parse_assign()
                            assign1044 = _t1832
                            _t1833 = logic_pb2.Instruction(assign=assign1044)
                            _t1831 = _t1833
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1828 = _t1831
                    _t1825 = _t1828
                _t1822 = _t1825
            _t1819 = _t1822
        result1050 = _t1819
        self.record_span(span_start1049, "Instruction")
        return result1050

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1054 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1834 = self.parse_relation_id()
        relation_id1051 = _t1834
        _t1835 = self.parse_abstraction()
        abstraction1052 = _t1835
        if self.match_lookahead_literal("(", 0):
            _t1837 = self.parse_attrs()
            _t1836 = _t1837
        else:
            _t1836 = None
        attrs1053 = _t1836
        self.consume_literal(")")
        _t1838 = logic_pb2.Assign(name=relation_id1051, body=abstraction1052, attrs=(attrs1053 if attrs1053 is not None else []))
        result1055 = _t1838
        self.record_span(span_start1054, "Assign")
        return result1055

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1059 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1839 = self.parse_relation_id()
        relation_id1056 = _t1839
        _t1840 = self.parse_abstraction_with_arity()
        abstraction_with_arity1057 = _t1840
        if self.match_lookahead_literal("(", 0):
            _t1842 = self.parse_attrs()
            _t1841 = _t1842
        else:
            _t1841 = None
        attrs1058 = _t1841
        self.consume_literal(")")
        _t1843 = logic_pb2.Upsert(name=relation_id1056, body=abstraction_with_arity1057[0], attrs=(attrs1058 if attrs1058 is not None else []), value_arity=abstraction_with_arity1057[1])
        result1060 = _t1843
        self.record_span(span_start1059, "Upsert")
        return result1060

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1844 = self.parse_bindings()
        bindings1061 = _t1844
        _t1845 = self.parse_formula()
        formula1062 = _t1845
        self.consume_literal(")")
        _t1846 = logic_pb2.Abstraction(vars=(list(bindings1061[0]) + list(bindings1061[1] if bindings1061[1] is not None else [])), value=formula1062)
        return (_t1846, len(bindings1061[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1066 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1847 = self.parse_relation_id()
        relation_id1063 = _t1847
        _t1848 = self.parse_abstraction()
        abstraction1064 = _t1848
        if self.match_lookahead_literal("(", 0):
            _t1850 = self.parse_attrs()
            _t1849 = _t1850
        else:
            _t1849 = None
        attrs1065 = _t1849
        self.consume_literal(")")
        _t1851 = logic_pb2.Break(name=relation_id1063, body=abstraction1064, attrs=(attrs1065 if attrs1065 is not None else []))
        result1067 = _t1851
        self.record_span(span_start1066, "Break")
        return result1067

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1072 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1852 = self.parse_monoid()
        monoid1068 = _t1852
        _t1853 = self.parse_relation_id()
        relation_id1069 = _t1853
        _t1854 = self.parse_abstraction_with_arity()
        abstraction_with_arity1070 = _t1854
        if self.match_lookahead_literal("(", 0):
            _t1856 = self.parse_attrs()
            _t1855 = _t1856
        else:
            _t1855 = None
        attrs1071 = _t1855
        self.consume_literal(")")
        _t1857 = logic_pb2.MonoidDef(monoid=monoid1068, name=relation_id1069, body=abstraction_with_arity1070[0], attrs=(attrs1071 if attrs1071 is not None else []), value_arity=abstraction_with_arity1070[1])
        result1073 = _t1857
        self.record_span(span_start1072, "MonoidDef")
        return result1073

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1079 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1859 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1860 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1861 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1862 = 2
                        else:
                            _t1862 = -1
                        _t1861 = _t1862
                    _t1860 = _t1861
                _t1859 = _t1860
            _t1858 = _t1859
        else:
            _t1858 = -1
        prediction1074 = _t1858
        if prediction1074 == 3:
            _t1864 = self.parse_sum_monoid()
            sum_monoid1078 = _t1864
            _t1865 = logic_pb2.Monoid(sum_monoid=sum_monoid1078)
            _t1863 = _t1865
        else:
            if prediction1074 == 2:
                _t1867 = self.parse_max_monoid()
                max_monoid1077 = _t1867
                _t1868 = logic_pb2.Monoid(max_monoid=max_monoid1077)
                _t1866 = _t1868
            else:
                if prediction1074 == 1:
                    _t1870 = self.parse_min_monoid()
                    min_monoid1076 = _t1870
                    _t1871 = logic_pb2.Monoid(min_monoid=min_monoid1076)
                    _t1869 = _t1871
                else:
                    if prediction1074 == 0:
                        _t1873 = self.parse_or_monoid()
                        or_monoid1075 = _t1873
                        _t1874 = logic_pb2.Monoid(or_monoid=or_monoid1075)
                        _t1872 = _t1874
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1869 = _t1872
                _t1866 = _t1869
            _t1863 = _t1866
        result1080 = _t1863
        self.record_span(span_start1079, "Monoid")
        return result1080

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1081 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1875 = logic_pb2.OrMonoid()
        result1082 = _t1875
        self.record_span(span_start1081, "OrMonoid")
        return result1082

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1084 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1876 = self.parse_type()
        type1083 = _t1876
        self.consume_literal(")")
        _t1877 = logic_pb2.MinMonoid(type=type1083)
        result1085 = _t1877
        self.record_span(span_start1084, "MinMonoid")
        return result1085

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1087 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1878 = self.parse_type()
        type1086 = _t1878
        self.consume_literal(")")
        _t1879 = logic_pb2.MaxMonoid(type=type1086)
        result1088 = _t1879
        self.record_span(span_start1087, "MaxMonoid")
        return result1088

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1090 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1880 = self.parse_type()
        type1089 = _t1880
        self.consume_literal(")")
        _t1881 = logic_pb2.SumMonoid(type=type1089)
        result1091 = _t1881
        self.record_span(span_start1090, "SumMonoid")
        return result1091

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1096 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1882 = self.parse_monoid()
        monoid1092 = _t1882
        _t1883 = self.parse_relation_id()
        relation_id1093 = _t1883
        _t1884 = self.parse_abstraction_with_arity()
        abstraction_with_arity1094 = _t1884
        if self.match_lookahead_literal("(", 0):
            _t1886 = self.parse_attrs()
            _t1885 = _t1886
        else:
            _t1885 = None
        attrs1095 = _t1885
        self.consume_literal(")")
        _t1887 = logic_pb2.MonusDef(monoid=monoid1092, name=relation_id1093, body=abstraction_with_arity1094[0], attrs=(attrs1095 if attrs1095 is not None else []), value_arity=abstraction_with_arity1094[1])
        result1097 = _t1887
        self.record_span(span_start1096, "MonusDef")
        return result1097

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1102 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1888 = self.parse_relation_id()
        relation_id1098 = _t1888
        _t1889 = self.parse_abstraction()
        abstraction1099 = _t1889
        _t1890 = self.parse_functional_dependency_keys()
        functional_dependency_keys1100 = _t1890
        _t1891 = self.parse_functional_dependency_values()
        functional_dependency_values1101 = _t1891
        self.consume_literal(")")
        _t1892 = logic_pb2.FunctionalDependency(guard=abstraction1099, keys=functional_dependency_keys1100, values=functional_dependency_values1101)
        _t1893 = logic_pb2.Constraint(name=relation_id1098, functional_dependency=_t1892)
        result1103 = _t1893
        self.record_span(span_start1102, "Constraint")
        return result1103

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1104 = []
        cond1105 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1105:
            _t1894 = self.parse_var()
            item1106 = _t1894
            xs1104.append(item1106)
            cond1105 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1107 = xs1104
        self.consume_literal(")")
        return vars1107

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1108 = []
        cond1109 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1109:
            _t1895 = self.parse_var()
            item1110 = _t1895
            xs1108.append(item1110)
            cond1109 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1111 = xs1108
        self.consume_literal(")")
        return vars1111

    def parse_data(self) -> logic_pb2.Data:
        span_start1117 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1897 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1898 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t1899 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t1900 = 1
                        else:
                            _t1900 = -1
                        _t1899 = _t1900
                    _t1898 = _t1899
                _t1897 = _t1898
            _t1896 = _t1897
        else:
            _t1896 = -1
        prediction1112 = _t1896
        if prediction1112 == 3:
            _t1902 = self.parse_iceberg_data()
            iceberg_data1116 = _t1902
            _t1903 = logic_pb2.Data(iceberg_data=iceberg_data1116)
            _t1901 = _t1903
        else:
            if prediction1112 == 2:
                _t1905 = self.parse_csv_data()
                csv_data1115 = _t1905
                _t1906 = logic_pb2.Data(csv_data=csv_data1115)
                _t1904 = _t1906
            else:
                if prediction1112 == 1:
                    _t1908 = self.parse_betree_relation()
                    betree_relation1114 = _t1908
                    _t1909 = logic_pb2.Data(betree_relation=betree_relation1114)
                    _t1907 = _t1909
                else:
                    if prediction1112 == 0:
                        _t1911 = self.parse_edb()
                        edb1113 = _t1911
                        _t1912 = logic_pb2.Data(edb=edb1113)
                        _t1910 = _t1912
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1907 = _t1910
                _t1904 = _t1907
            _t1901 = _t1904
        result1118 = _t1901
        self.record_span(span_start1117, "Data")
        return result1118

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1122 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1913 = self.parse_relation_id()
        relation_id1119 = _t1913
        _t1914 = self.parse_edb_path()
        edb_path1120 = _t1914
        _t1915 = self.parse_edb_types()
        edb_types1121 = _t1915
        self.consume_literal(")")
        _t1916 = logic_pb2.EDB(target_id=relation_id1119, path=edb_path1120, types=edb_types1121)
        result1123 = _t1916
        self.record_span(span_start1122, "EDB")
        return result1123

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1124 = []
        cond1125 = self.match_lookahead_terminal("STRING", 0)
        while cond1125:
            item1126 = self.consume_terminal("STRING")
            xs1124.append(item1126)
            cond1125 = self.match_lookahead_terminal("STRING", 0)
        strings1127 = xs1124
        self.consume_literal("]")
        return strings1127

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1128 = []
        cond1129 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1129:
            _t1917 = self.parse_type()
            item1130 = _t1917
            xs1128.append(item1130)
            cond1129 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1131 = xs1128
        self.consume_literal("]")
        return types1131

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1134 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1918 = self.parse_relation_id()
        relation_id1132 = _t1918
        _t1919 = self.parse_betree_info()
        betree_info1133 = _t1919
        self.consume_literal(")")
        _t1920 = logic_pb2.BeTreeRelation(name=relation_id1132, relation_info=betree_info1133)
        result1135 = _t1920
        self.record_span(span_start1134, "BeTreeRelation")
        return result1135

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1139 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1921 = self.parse_betree_info_key_types()
        betree_info_key_types1136 = _t1921
        _t1922 = self.parse_betree_info_value_types()
        betree_info_value_types1137 = _t1922
        _t1923 = self.parse_config_dict()
        config_dict1138 = _t1923
        self.consume_literal(")")
        _t1924 = self.construct_betree_info(betree_info_key_types1136, betree_info_value_types1137, config_dict1138)
        result1140 = _t1924
        self.record_span(span_start1139, "BeTreeInfo")
        return result1140

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1141 = []
        cond1142 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1142:
            _t1925 = self.parse_type()
            item1143 = _t1925
            xs1141.append(item1143)
            cond1142 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1144 = xs1141
        self.consume_literal(")")
        return types1144

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1145 = []
        cond1146 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1146:
            _t1926 = self.parse_type()
            item1147 = _t1926
            xs1145.append(item1147)
            cond1146 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1148 = xs1145
        self.consume_literal(")")
        return types1148

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1153 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1927 = self.parse_csvlocator()
        csvlocator1149 = _t1927
        _t1928 = self.parse_csv_config()
        csv_config1150 = _t1928
        _t1929 = self.parse_gnf_columns()
        gnf_columns1151 = _t1929
        _t1930 = self.parse_csv_asof()
        csv_asof1152 = _t1930
        self.consume_literal(")")
        _t1931 = logic_pb2.CSVData(locator=csvlocator1149, config=csv_config1150, columns=gnf_columns1151, asof=csv_asof1152)
        result1154 = _t1931
        self.record_span(span_start1153, "CSVData")
        return result1154

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1157 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1933 = self.parse_csv_locator_paths()
            _t1932 = _t1933
        else:
            _t1932 = None
        csv_locator_paths1155 = _t1932
        if self.match_lookahead_literal("(", 0):
            _t1935 = self.parse_csv_locator_inline_data()
            _t1934 = _t1935
        else:
            _t1934 = None
        csv_locator_inline_data1156 = _t1934
        self.consume_literal(")")
        _t1936 = logic_pb2.CSVLocator(paths=(csv_locator_paths1155 if csv_locator_paths1155 is not None else []), inline_data=(csv_locator_inline_data1156 if csv_locator_inline_data1156 is not None else "").encode())
        result1158 = _t1936
        self.record_span(span_start1157, "CSVLocator")
        return result1158

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1159 = []
        cond1160 = self.match_lookahead_terminal("STRING", 0)
        while cond1160:
            item1161 = self.consume_terminal("STRING")
            xs1159.append(item1161)
            cond1160 = self.match_lookahead_terminal("STRING", 0)
        strings1162 = xs1159
        self.consume_literal(")")
        return strings1162

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1163 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1163

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1165 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1937 = self.parse_config_dict()
        config_dict1164 = _t1937
        self.consume_literal(")")
        _t1938 = self.construct_csv_config(config_dict1164)
        result1166 = _t1938
        self.record_span(span_start1165, "CSVConfig")
        return result1166

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1167 = []
        cond1168 = self.match_lookahead_literal("(", 0)
        while cond1168:
            _t1939 = self.parse_gnf_column()
            item1169 = _t1939
            xs1167.append(item1169)
            cond1168 = self.match_lookahead_literal("(", 0)
        gnf_columns1170 = xs1167
        self.consume_literal(")")
        return gnf_columns1170

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1177 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1940 = self.parse_gnf_column_path()
        gnf_column_path1171 = _t1940
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1942 = self.parse_relation_id()
            _t1941 = _t1942
        else:
            _t1941 = None
        relation_id1172 = _t1941
        self.consume_literal("[")
        xs1173 = []
        cond1174 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1174:
            _t1943 = self.parse_type()
            item1175 = _t1943
            xs1173.append(item1175)
            cond1174 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1176 = xs1173
        self.consume_literal("]")
        self.consume_literal(")")
        _t1944 = logic_pb2.GNFColumn(column_path=gnf_column_path1171, target_id=relation_id1172, types=types1176)
        result1178 = _t1944
        self.record_span(span_start1177, "GNFColumn")
        return result1178

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1945 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1946 = 0
            else:
                _t1946 = -1
            _t1945 = _t1946
        prediction1179 = _t1945
        if prediction1179 == 1:
            self.consume_literal("[")
            xs1181 = []
            cond1182 = self.match_lookahead_terminal("STRING", 0)
            while cond1182:
                item1183 = self.consume_terminal("STRING")
                xs1181.append(item1183)
                cond1182 = self.match_lookahead_terminal("STRING", 0)
            strings1184 = xs1181
            self.consume_literal("]")
            _t1947 = strings1184
        else:
            if prediction1179 == 0:
                string1180 = self.consume_terminal("STRING")
                _t1948 = [string1180]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1947 = _t1948
        return _t1947

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1185 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1185

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1190 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t1949 = self.parse_iceberg_locator()
        iceberg_locator1186 = _t1949
        _t1950 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1187 = _t1950
        _t1951 = self.parse_gnf_columns()
        gnf_columns1188 = _t1951
        if self.match_lookahead_literal("(", 0):
            _t1953 = self.parse_iceberg_to_snapshot()
            _t1952 = _t1953
        else:
            _t1952 = None
        iceberg_to_snapshot1189 = _t1952
        self.consume_literal(")")
        _t1954 = logic_pb2.IcebergData(locator=iceberg_locator1186, config=iceberg_catalog_config1187, columns=gnf_columns1188, to_snapshot=(iceberg_to_snapshot1189 if iceberg_to_snapshot1189 is not None else ""))
        result1191 = _t1954
        self.record_span(span_start1190, "IcebergData")
        return result1191

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1198 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1192 = self.consume_terminal("STRING")
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1193 = []
        cond1194 = self.match_lookahead_terminal("STRING", 0)
        while cond1194:
            item1195 = self.consume_terminal("STRING")
            xs1193.append(item1195)
            cond1194 = self.match_lookahead_terminal("STRING", 0)
        strings1196 = xs1193
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string_121197 = self.consume_terminal("STRING")
        self.consume_literal(")")
        self.consume_literal(")")
        _t1955 = logic_pb2.IcebergLocator(table_name=string1192, namespace=strings1196, warehouse=string_121197)
        result1199 = _t1955
        self.record_span(span_start1198, "IcebergLocator")
        return result1199

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1210 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1200 = self.consume_terminal("STRING")
        self.consume_literal(")")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t1957 = self.parse_iceberg_catalog_config_scope()
            _t1956 = _t1957
        else:
            _t1956 = None
        iceberg_catalog_config_scope1201 = _t1956
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1202 = []
        cond1203 = self.match_lookahead_literal("(", 0)
        while cond1203:
            _t1958 = self.parse_iceberg_property_entry()
            item1204 = _t1958
            xs1202.append(item1204)
            cond1203 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1205 = xs1202
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1206 = []
        cond1207 = self.match_lookahead_literal("(", 0)
        while cond1207:
            _t1959 = self.parse_iceberg_property_entry()
            item1208 = _t1959
            xs1206.append(item1208)
            cond1207 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys_131209 = xs1206
        self.consume_literal(")")
        self.consume_literal(")")
        _t1960 = self.construct_iceberg_catalog_config(string1200, iceberg_catalog_config_scope1201, iceberg_property_entrys1205, iceberg_property_entrys_131209)
        result1211 = _t1960
        self.record_span(span_start1210, "IcebergCatalogConfig")
        return result1211

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1212 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1212

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1213 = self.consume_terminal("STRING")
        string_31214 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1213, string_31214,)

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1215 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1215

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1217 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1961 = self.parse_fragment_id()
        fragment_id1216 = _t1961
        self.consume_literal(")")
        _t1962 = transactions_pb2.Undefine(fragment_id=fragment_id1216)
        result1218 = _t1962
        self.record_span(span_start1217, "Undefine")
        return result1218

    def parse_context(self) -> transactions_pb2.Context:
        span_start1223 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1219 = []
        cond1220 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1220:
            _t1963 = self.parse_relation_id()
            item1221 = _t1963
            xs1219.append(item1221)
            cond1220 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1222 = xs1219
        self.consume_literal(")")
        _t1964 = transactions_pb2.Context(relations=relation_ids1222)
        result1224 = _t1964
        self.record_span(span_start1223, "Context")
        return result1224

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1229 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        xs1225 = []
        cond1226 = self.match_lookahead_literal("[", 0)
        while cond1226:
            _t1965 = self.parse_snapshot_mapping()
            item1227 = _t1965
            xs1225.append(item1227)
            cond1226 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1228 = xs1225
        self.consume_literal(")")
        _t1966 = transactions_pb2.Snapshot(mappings=snapshot_mappings1228)
        result1230 = _t1966
        self.record_span(span_start1229, "Snapshot")
        return result1230

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1233 = self.span_start()
        _t1967 = self.parse_edb_path()
        edb_path1231 = _t1967
        _t1968 = self.parse_relation_id()
        relation_id1232 = _t1968
        _t1969 = transactions_pb2.SnapshotMapping(destination_path=edb_path1231, source_relation=relation_id1232)
        result1234 = _t1969
        self.record_span(span_start1233, "SnapshotMapping")
        return result1234

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1235 = []
        cond1236 = self.match_lookahead_literal("(", 0)
        while cond1236:
            _t1970 = self.parse_read()
            item1237 = _t1970
            xs1235.append(item1237)
            cond1236 = self.match_lookahead_literal("(", 0)
        reads1238 = xs1235
        self.consume_literal(")")
        return reads1238

    def parse_read(self) -> transactions_pb2.Read:
        span_start1245 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1972 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1973 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t1974 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t1975 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t1976 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t1977 = 3
                                else:
                                    _t1977 = -1
                                _t1976 = _t1977
                            _t1975 = _t1976
                        _t1974 = _t1975
                    _t1973 = _t1974
                _t1972 = _t1973
            _t1971 = _t1972
        else:
            _t1971 = -1
        prediction1239 = _t1971
        if prediction1239 == 4:
            _t1979 = self.parse_export()
            export1244 = _t1979
            _t1980 = transactions_pb2.Read(export=export1244)
            _t1978 = _t1980
        else:
            if prediction1239 == 3:
                _t1982 = self.parse_abort()
                abort1243 = _t1982
                _t1983 = transactions_pb2.Read(abort=abort1243)
                _t1981 = _t1983
            else:
                if prediction1239 == 2:
                    _t1985 = self.parse_what_if()
                    what_if1242 = _t1985
                    _t1986 = transactions_pb2.Read(what_if=what_if1242)
                    _t1984 = _t1986
                else:
                    if prediction1239 == 1:
                        _t1988 = self.parse_output()
                        output1241 = _t1988
                        _t1989 = transactions_pb2.Read(output=output1241)
                        _t1987 = _t1989
                    else:
                        if prediction1239 == 0:
                            _t1991 = self.parse_demand()
                            demand1240 = _t1991
                            _t1992 = transactions_pb2.Read(demand=demand1240)
                            _t1990 = _t1992
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1987 = _t1990
                    _t1984 = _t1987
                _t1981 = _t1984
            _t1978 = _t1981
        result1246 = _t1978
        self.record_span(span_start1245, "Read")
        return result1246

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1248 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1993 = self.parse_relation_id()
        relation_id1247 = _t1993
        self.consume_literal(")")
        _t1994 = transactions_pb2.Demand(relation_id=relation_id1247)
        result1249 = _t1994
        self.record_span(span_start1248, "Demand")
        return result1249

    def parse_output(self) -> transactions_pb2.Output:
        span_start1252 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t1995 = self.parse_name()
        name1250 = _t1995
        _t1996 = self.parse_relation_id()
        relation_id1251 = _t1996
        self.consume_literal(")")
        _t1997 = transactions_pb2.Output(name=name1250, relation_id=relation_id1251)
        result1253 = _t1997
        self.record_span(span_start1252, "Output")
        return result1253

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1256 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t1998 = self.parse_name()
        name1254 = _t1998
        _t1999 = self.parse_epoch()
        epoch1255 = _t1999
        self.consume_literal(")")
        _t2000 = transactions_pb2.WhatIf(branch=name1254, epoch=epoch1255)
        result1257 = _t2000
        self.record_span(span_start1256, "WhatIf")
        return result1257

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1260 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2002 = self.parse_name()
            _t2001 = _t2002
        else:
            _t2001 = None
        name1258 = _t2001
        _t2003 = self.parse_relation_id()
        relation_id1259 = _t2003
        self.consume_literal(")")
        _t2004 = transactions_pb2.Abort(name=(name1258 if name1258 is not None else "abort"), relation_id=relation_id1259)
        result1261 = _t2004
        self.record_span(span_start1260, "Abort")
        return result1261

    def parse_export(self) -> transactions_pb2.Export:
        span_start1265 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2006 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2007 = 0
                else:
                    _t2007 = -1
                _t2006 = _t2007
            _t2005 = _t2006
        else:
            _t2005 = -1
        prediction1262 = _t2005
        if prediction1262 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2009 = self.parse_export_iceberg_config()
            export_iceberg_config1264 = _t2009
            self.consume_literal(")")
            _t2010 = transactions_pb2.Export(iceberg_config=export_iceberg_config1264)
            _t2008 = _t2010
        else:
            if prediction1262 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2012 = self.parse_export_csv_config()
                export_csv_config1263 = _t2012
                self.consume_literal(")")
                _t2013 = transactions_pb2.Export(csv_config=export_csv_config1263)
                _t2011 = _t2013
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2008 = _t2011
        result1266 = _t2008
        self.record_span(span_start1265, "Export")
        return result1266

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1274 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2015 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2016 = 1
                else:
                    _t2016 = -1
                _t2015 = _t2016
            _t2014 = _t2015
        else:
            _t2014 = -1
        prediction1267 = _t2014
        if prediction1267 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2018 = self.parse_export_csv_path()
            export_csv_path1271 = _t2018
            _t2019 = self.parse_export_csv_columns_list()
            export_csv_columns_list1272 = _t2019
            _t2020 = self.parse_config_dict()
            config_dict1273 = _t2020
            self.consume_literal(")")
            _t2021 = self.construct_export_csv_config(export_csv_path1271, export_csv_columns_list1272, config_dict1273)
            _t2017 = _t2021
        else:
            if prediction1267 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2023 = self.parse_export_csv_path()
                export_csv_path1268 = _t2023
                _t2024 = self.parse_export_csv_source()
                export_csv_source1269 = _t2024
                _t2025 = self.parse_csv_config()
                csv_config1270 = _t2025
                self.consume_literal(")")
                _t2026 = self.construct_export_csv_config_with_source(export_csv_path1268, export_csv_source1269, csv_config1270)
                _t2022 = _t2026
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2017 = _t2022
        result1275 = _t2017
        self.record_span(span_start1274, "ExportCSVConfig")
        return result1275

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1276 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1276

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1283 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2028 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2029 = 0
                else:
                    _t2029 = -1
                _t2028 = _t2029
            _t2027 = _t2028
        else:
            _t2027 = -1
        prediction1277 = _t2027
        if prediction1277 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2031 = self.parse_relation_id()
            relation_id1282 = _t2031
            self.consume_literal(")")
            _t2032 = transactions_pb2.ExportCSVSource(table_def=relation_id1282)
            _t2030 = _t2032
        else:
            if prediction1277 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1278 = []
                cond1279 = self.match_lookahead_literal("(", 0)
                while cond1279:
                    _t2034 = self.parse_export_csv_column()
                    item1280 = _t2034
                    xs1278.append(item1280)
                    cond1279 = self.match_lookahead_literal("(", 0)
                export_csv_columns1281 = xs1278
                self.consume_literal(")")
                _t2035 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1281)
                _t2036 = transactions_pb2.ExportCSVSource(gnf_columns=_t2035)
                _t2033 = _t2036
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2030 = _t2033
        result1284 = _t2030
        self.record_span(span_start1283, "ExportCSVSource")
        return result1284

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1287 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1285 = self.consume_terminal("STRING")
        _t2037 = self.parse_relation_id()
        relation_id1286 = _t2037
        self.consume_literal(")")
        _t2038 = transactions_pb2.ExportCSVColumn(column_name=string1285, column_data=relation_id1286)
        result1288 = _t2038
        self.record_span(span_start1287, "ExportCSVColumn")
        return result1288

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1289 = []
        cond1290 = self.match_lookahead_literal("(", 0)
        while cond1290:
            _t2039 = self.parse_export_csv_column()
            item1291 = _t2039
            xs1289.append(item1291)
            cond1290 = self.match_lookahead_literal("(", 0)
        export_csv_columns1292 = xs1289
        self.consume_literal(")")
        return export_csv_columns1292

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1304 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2040 = self.parse_iceberg_locator()
        iceberg_locator1293 = _t2040
        _t2041 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1294 = _t2041
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1295 = []
        cond1296 = self.match_lookahead_literal("(", 0)
        while cond1296:
            _t2042 = self.parse_iceberg_export_column()
            item1297 = _t2042
            xs1295.append(item1297)
            cond1296 = self.match_lookahead_literal("(", 0)
        iceberg_export_columns1298 = xs1295
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("create_table_properties")
        xs1299 = []
        cond1300 = self.match_lookahead_literal("(", 0)
        while cond1300:
            _t2043 = self.parse_iceberg_property_entry()
            item1301 = _t2043
            xs1299.append(item1301)
            cond1300 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1302 = xs1299
        self.consume_literal(")")
        if self.match_lookahead_literal("{", 0):
            _t2045 = self.parse_config_dict()
            _t2044 = _t2045
        else:
            _t2044 = None
        config_dict1303 = _t2044
        self.consume_literal(")")
        _t2046 = self.construct_export_iceberg_config_full(iceberg_locator1293, iceberg_catalog_config1294, iceberg_export_columns1298, iceberg_property_entrys1302, config_dict1303)
        result1305 = _t2046
        self.record_span(span_start1304, "ExportIcebergConfig")
        return result1305

    def parse_iceberg_export_column(self) -> transactions_pb2.ExportIcebergColumn:
        span_start1310 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_column")
        string1306 = self.consume_terminal("STRING")
        _t2047 = self.parse_relation_id()
        relation_id1307 = _t2047
        _t2048 = self.parse_type()
        type1308 = _t2048
        _t2049 = self.parse_boolean_value()
        boolean_value1309 = _t2049
        self.consume_literal(")")
        _t2050 = transactions_pb2.ExportIcebergColumn(name=string1306, column_data=relation_id1307, type=type1308, nullable=boolean_value1309)
        result1311 = _t2050
        self.record_span(span_start1310, "ExportIcebergColumn")
        return result1311


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
