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
            _t1960 = value.HasField("int32_value")
        else:
            _t1960 = False
        if _t1960:
            assert value is not None
            return value.int32_value
        else:
            _t1961 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t1962 = value.HasField("int_value")
        else:
            _t1962 = False
        if _t1962:
            assert value is not None
            return value.int_value
        else:
            _t1963 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t1964 = value.HasField("string_value")
        else:
            _t1964 = False
        if _t1964:
            assert value is not None
            return value.string_value
        else:
            _t1965 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t1966 = value.HasField("boolean_value")
        else:
            _t1966 = False
        if _t1966:
            assert value is not None
            return value.boolean_value
        else:
            _t1967 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t1968 = value.HasField("string_value")
        else:
            _t1968 = False
        if _t1968:
            assert value is not None
            return [value.string_value]
        else:
            _t1969 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t1970 = value.HasField("int_value")
        else:
            _t1970 = False
        if _t1970:
            assert value is not None
            return value.int_value
        else:
            _t1971 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t1972 = value.HasField("float_value")
        else:
            _t1972 = False
        if _t1972:
            assert value is not None
            return value.float_value
        else:
            _t1973 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t1974 = value.HasField("string_value")
        else:
            _t1974 = False
        if _t1974:
            assert value is not None
            return value.string_value.encode()
        else:
            _t1975 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t1976 = value.HasField("uint128_value")
        else:
            _t1976 = False
        if _t1976:
            assert value is not None
            return value.uint128_value
        else:
            _t1977 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1978 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t1978
        _t1979 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t1979
        _t1980 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t1980
        _t1981 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t1981
        _t1982 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t1982
        _t1983 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t1983
        _t1984 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t1984
        _t1985 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t1985
        _t1986 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t1986
        _t1987 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t1987
        _t1988 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t1988
        _t1989 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t1989
        _t1990 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t1990

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1991 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t1991
        _t1992 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t1992
        _t1993 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t1993
        _t1994 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t1994
        _t1995 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1995
        _t1996 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t1996
        _t1997 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t1997
        _t1998 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t1998
        _t1999 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t1999
        _t2000 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2000
        _t2001 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2001

    def default_configure(self) -> transactions_pb2.Configure:
        _t2002 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2002
        _t2003 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2003

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
        _t2004 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2004
        _t2005 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2005
        _t2006 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t2006

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2007 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2007
        _t2008 = self._extract_value_string(config.get("compression"), "")
        compression = _t2008
        _t2009 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2009
        _t2010 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2010
        _t2011 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2011
        _t2012 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2012
        _t2013 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2013
        _t2014 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2014

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2015 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t2015

    def construct_export_iceberg_config_from_optional(self, catalog_uri: str, namespace: Sequence[str], table_name: str, catalog_properties: transactions_pb2.IcebergCatalogProperties, schema: str, config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        prefix = ""
        _t2016 = self._extract_value_int64(None, 0)
        target_file_size_bytes = _t2016
        compression = ""
        if config_dict is not None:
            assert config_dict is not None
            config = dict(config_dict)
            _t2017 = self._extract_value_string(config.get("prefix"), "")
            prefix = _t2017
            _t2018 = self._extract_value_int64(config.get("target_file_size_bytes"), 0)
            target_file_size_bytes = _t2018
            _t2019 = self._extract_value_string(config.get("compression"), "")
            compression = _t2019
        _t2020 = transactions_pb2.ExportIcebergConfig(catalog_uri=catalog_uri, namespace=namespace, table_name=table_name, catalog_properties=catalog_properties, schema=schema, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression)
        return _t2020

    def construct_iceberg_catalog_properties_from_optional(self, warehouse: str, config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.IcebergCatalogProperties:
        token = ""
        credential = ""
        if config_dict is not None:
            assert config_dict is not None
            config = dict(config_dict)
            _t2021 = self._extract_value_string(config.get("token"), "")
            token = _t2021
            _t2022 = self._extract_value_string(config.get("credential"), "")
            credential = _t2022
        _t2023 = transactions_pb2.IcebergCatalogProperties(warehouse=warehouse, token=token, credential=credential)
        return _t2023

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start627 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1243 = self.parse_configure()
            _t1242 = _t1243
        else:
            _t1242 = None
        configure621 = _t1242
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1245 = self.parse_sync()
            _t1244 = _t1245
        else:
            _t1244 = None
        sync622 = _t1244
        xs623 = []
        cond624 = self.match_lookahead_literal("(", 0)
        while cond624:
            _t1246 = self.parse_epoch()
            item625 = _t1246
            xs623.append(item625)
            cond624 = self.match_lookahead_literal("(", 0)
        epochs626 = xs623
        self.consume_literal(")")
        _t1247 = self.default_configure()
        _t1248 = transactions_pb2.Transaction(epochs=epochs626, configure=(configure621 if configure621 is not None else _t1247), sync=sync622)
        result628 = _t1248
        self.record_span(span_start627, "Transaction")
        return result628

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start630 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1249 = self.parse_config_dict()
        config_dict629 = _t1249
        self.consume_literal(")")
        _t1250 = self.construct_configure(config_dict629)
        result631 = _t1250
        self.record_span(span_start630, "Configure")
        return result631

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs632 = []
        cond633 = self.match_lookahead_literal(":", 0)
        while cond633:
            _t1251 = self.parse_config_key_value()
            item634 = _t1251
            xs632.append(item634)
            cond633 = self.match_lookahead_literal(":", 0)
        config_key_values635 = xs632
        self.consume_literal("}")
        return config_key_values635

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol636 = self.consume_terminal("SYMBOL")
        _t1252 = self.parse_raw_value()
        raw_value637 = _t1252
        return (symbol636, raw_value637,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start651 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1253 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1254 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1255 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1257 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1258 = 0
                            else:
                                _t1258 = -1
                            _t1257 = _t1258
                        _t1256 = _t1257
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1259 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1260 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1261 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1262 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1263 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1264 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1265 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1266 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1267 = 10
                                                        else:
                                                            _t1267 = -1
                                                        _t1266 = _t1267
                                                    _t1265 = _t1266
                                                _t1264 = _t1265
                                            _t1263 = _t1264
                                        _t1262 = _t1263
                                    _t1261 = _t1262
                                _t1260 = _t1261
                            _t1259 = _t1260
                        _t1256 = _t1259
                    _t1255 = _t1256
                _t1254 = _t1255
            _t1253 = _t1254
        prediction638 = _t1253
        if prediction638 == 12:
            _t1269 = self.parse_boolean_value()
            boolean_value650 = _t1269
            _t1270 = logic_pb2.Value(boolean_value=boolean_value650)
            _t1268 = _t1270
        else:
            if prediction638 == 11:
                self.consume_literal("missing")
                _t1272 = logic_pb2.MissingValue()
                _t1273 = logic_pb2.Value(missing_value=_t1272)
                _t1271 = _t1273
            else:
                if prediction638 == 10:
                    decimal649 = self.consume_terminal("DECIMAL")
                    _t1275 = logic_pb2.Value(decimal_value=decimal649)
                    _t1274 = _t1275
                else:
                    if prediction638 == 9:
                        int128648 = self.consume_terminal("INT128")
                        _t1277 = logic_pb2.Value(int128_value=int128648)
                        _t1276 = _t1277
                    else:
                        if prediction638 == 8:
                            uint128647 = self.consume_terminal("UINT128")
                            _t1279 = logic_pb2.Value(uint128_value=uint128647)
                            _t1278 = _t1279
                        else:
                            if prediction638 == 7:
                                uint32646 = self.consume_terminal("UINT32")
                                _t1281 = logic_pb2.Value(uint32_value=uint32646)
                                _t1280 = _t1281
                            else:
                                if prediction638 == 6:
                                    float645 = self.consume_terminal("FLOAT")
                                    _t1283 = logic_pb2.Value(float_value=float645)
                                    _t1282 = _t1283
                                else:
                                    if prediction638 == 5:
                                        float32644 = self.consume_terminal("FLOAT32")
                                        _t1285 = logic_pb2.Value(float32_value=float32644)
                                        _t1284 = _t1285
                                    else:
                                        if prediction638 == 4:
                                            int643 = self.consume_terminal("INT")
                                            _t1287 = logic_pb2.Value(int_value=int643)
                                            _t1286 = _t1287
                                        else:
                                            if prediction638 == 3:
                                                int32642 = self.consume_terminal("INT32")
                                                _t1289 = logic_pb2.Value(int32_value=int32642)
                                                _t1288 = _t1289
                                            else:
                                                if prediction638 == 2:
                                                    string641 = self.consume_terminal("STRING")
                                                    _t1291 = logic_pb2.Value(string_value=string641)
                                                    _t1290 = _t1291
                                                else:
                                                    if prediction638 == 1:
                                                        _t1293 = self.parse_raw_datetime()
                                                        raw_datetime640 = _t1293
                                                        _t1294 = logic_pb2.Value(datetime_value=raw_datetime640)
                                                        _t1292 = _t1294
                                                    else:
                                                        if prediction638 == 0:
                                                            _t1296 = self.parse_raw_date()
                                                            raw_date639 = _t1296
                                                            _t1297 = logic_pb2.Value(date_value=raw_date639)
                                                            _t1295 = _t1297
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1292 = _t1295
                                                    _t1290 = _t1292
                                                _t1288 = _t1290
                                            _t1286 = _t1288
                                        _t1284 = _t1286
                                    _t1282 = _t1284
                                _t1280 = _t1282
                            _t1278 = _t1280
                        _t1276 = _t1278
                    _t1274 = _t1276
                _t1271 = _t1274
            _t1268 = _t1271
        result652 = _t1268
        self.record_span(span_start651, "Value")
        return result652

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start656 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int653 = self.consume_terminal("INT")
        int_3654 = self.consume_terminal("INT")
        int_4655 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1298 = logic_pb2.DateValue(year=int(int653), month=int(int_3654), day=int(int_4655))
        result657 = _t1298
        self.record_span(span_start656, "DateValue")
        return result657

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start665 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int658 = self.consume_terminal("INT")
        int_3659 = self.consume_terminal("INT")
        int_4660 = self.consume_terminal("INT")
        int_5661 = self.consume_terminal("INT")
        int_6662 = self.consume_terminal("INT")
        int_7663 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1299 = self.consume_terminal("INT")
        else:
            _t1299 = None
        int_8664 = _t1299
        self.consume_literal(")")
        _t1300 = logic_pb2.DateTimeValue(year=int(int658), month=int(int_3659), day=int(int_4660), hour=int(int_5661), minute=int(int_6662), second=int(int_7663), microsecond=int((int_8664 if int_8664 is not None else 0)))
        result666 = _t1300
        self.record_span(span_start665, "DateTimeValue")
        return result666

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1301 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1302 = 1
            else:
                _t1302 = -1
            _t1301 = _t1302
        prediction667 = _t1301
        if prediction667 == 1:
            self.consume_literal("false")
            _t1303 = False
        else:
            if prediction667 == 0:
                self.consume_literal("true")
                _t1304 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1303 = _t1304
        return _t1303

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start672 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs668 = []
        cond669 = self.match_lookahead_literal(":", 0)
        while cond669:
            _t1305 = self.parse_fragment_id()
            item670 = _t1305
            xs668.append(item670)
            cond669 = self.match_lookahead_literal(":", 0)
        fragment_ids671 = xs668
        self.consume_literal(")")
        _t1306 = transactions_pb2.Sync(fragments=fragment_ids671)
        result673 = _t1306
        self.record_span(span_start672, "Sync")
        return result673

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start675 = self.span_start()
        self.consume_literal(":")
        symbol674 = self.consume_terminal("SYMBOL")
        result676 = fragments_pb2.FragmentId(id=symbol674.encode())
        self.record_span(span_start675, "FragmentId")
        return result676

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start679 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1308 = self.parse_epoch_writes()
            _t1307 = _t1308
        else:
            _t1307 = None
        epoch_writes677 = _t1307
        if self.match_lookahead_literal("(", 0):
            _t1310 = self.parse_epoch_reads()
            _t1309 = _t1310
        else:
            _t1309 = None
        epoch_reads678 = _t1309
        self.consume_literal(")")
        _t1311 = transactions_pb2.Epoch(writes=(epoch_writes677 if epoch_writes677 is not None else []), reads=(epoch_reads678 if epoch_reads678 is not None else []))
        result680 = _t1311
        self.record_span(span_start679, "Epoch")
        return result680

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs681 = []
        cond682 = self.match_lookahead_literal("(", 0)
        while cond682:
            _t1312 = self.parse_write()
            item683 = _t1312
            xs681.append(item683)
            cond682 = self.match_lookahead_literal("(", 0)
        writes684 = xs681
        self.consume_literal(")")
        return writes684

    def parse_write(self) -> transactions_pb2.Write:
        span_start690 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1314 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1315 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1316 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1317 = 2
                        else:
                            _t1317 = -1
                        _t1316 = _t1317
                    _t1315 = _t1316
                _t1314 = _t1315
            _t1313 = _t1314
        else:
            _t1313 = -1
        prediction685 = _t1313
        if prediction685 == 3:
            _t1319 = self.parse_snapshot()
            snapshot689 = _t1319
            _t1320 = transactions_pb2.Write(snapshot=snapshot689)
            _t1318 = _t1320
        else:
            if prediction685 == 2:
                _t1322 = self.parse_context()
                context688 = _t1322
                _t1323 = transactions_pb2.Write(context=context688)
                _t1321 = _t1323
            else:
                if prediction685 == 1:
                    _t1325 = self.parse_undefine()
                    undefine687 = _t1325
                    _t1326 = transactions_pb2.Write(undefine=undefine687)
                    _t1324 = _t1326
                else:
                    if prediction685 == 0:
                        _t1328 = self.parse_define()
                        define686 = _t1328
                        _t1329 = transactions_pb2.Write(define=define686)
                        _t1327 = _t1329
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1324 = _t1327
                _t1321 = _t1324
            _t1318 = _t1321
        result691 = _t1318
        self.record_span(span_start690, "Write")
        return result691

    def parse_define(self) -> transactions_pb2.Define:
        span_start693 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1330 = self.parse_fragment()
        fragment692 = _t1330
        self.consume_literal(")")
        _t1331 = transactions_pb2.Define(fragment=fragment692)
        result694 = _t1331
        self.record_span(span_start693, "Define")
        return result694

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start700 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1332 = self.parse_new_fragment_id()
        new_fragment_id695 = _t1332
        xs696 = []
        cond697 = self.match_lookahead_literal("(", 0)
        while cond697:
            _t1333 = self.parse_declaration()
            item698 = _t1333
            xs696.append(item698)
            cond697 = self.match_lookahead_literal("(", 0)
        declarations699 = xs696
        self.consume_literal(")")
        result701 = self.construct_fragment(new_fragment_id695, declarations699)
        self.record_span(span_start700, "Fragment")
        return result701

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start703 = self.span_start()
        _t1334 = self.parse_fragment_id()
        fragment_id702 = _t1334
        self.start_fragment(fragment_id702)
        result704 = fragment_id702
        self.record_span(span_start703, "FragmentId")
        return result704

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start710 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("functional_dependency", 1):
                _t1336 = 2
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1337 = 3
                else:
                    if self.match_lookahead_literal("def", 1):
                        _t1338 = 0
                    else:
                        if self.match_lookahead_literal("csv_data", 1):
                            _t1339 = 3
                        else:
                            if self.match_lookahead_literal("betree_relation", 1):
                                _t1340 = 3
                            else:
                                if self.match_lookahead_literal("algorithm", 1):
                                    _t1341 = 1
                                else:
                                    _t1341 = -1
                                _t1340 = _t1341
                            _t1339 = _t1340
                        _t1338 = _t1339
                    _t1337 = _t1338
                _t1336 = _t1337
            _t1335 = _t1336
        else:
            _t1335 = -1
        prediction705 = _t1335
        if prediction705 == 3:
            _t1343 = self.parse_data()
            data709 = _t1343
            _t1344 = logic_pb2.Declaration(data=data709)
            _t1342 = _t1344
        else:
            if prediction705 == 2:
                _t1346 = self.parse_constraint()
                constraint708 = _t1346
                _t1347 = logic_pb2.Declaration(constraint=constraint708)
                _t1345 = _t1347
            else:
                if prediction705 == 1:
                    _t1349 = self.parse_algorithm()
                    algorithm707 = _t1349
                    _t1350 = logic_pb2.Declaration(algorithm=algorithm707)
                    _t1348 = _t1350
                else:
                    if prediction705 == 0:
                        _t1352 = self.parse_def()
                        def706 = _t1352
                        _t1353 = logic_pb2.Declaration()
                        getattr(_t1353, 'def').CopyFrom(def706)
                        _t1351 = _t1353
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1348 = _t1351
                _t1345 = _t1348
            _t1342 = _t1345
        result711 = _t1342
        self.record_span(span_start710, "Declaration")
        return result711

    def parse_def(self) -> logic_pb2.Def:
        span_start715 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1354 = self.parse_relation_id()
        relation_id712 = _t1354
        _t1355 = self.parse_abstraction()
        abstraction713 = _t1355
        if self.match_lookahead_literal("(", 0):
            _t1357 = self.parse_attrs()
            _t1356 = _t1357
        else:
            _t1356 = None
        attrs714 = _t1356
        self.consume_literal(")")
        _t1358 = logic_pb2.Def(name=relation_id712, body=abstraction713, attrs=(attrs714 if attrs714 is not None else []))
        result716 = _t1358
        self.record_span(span_start715, "Def")
        return result716

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start720 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1359 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1360 = 1
            else:
                _t1360 = -1
            _t1359 = _t1360
        prediction717 = _t1359
        if prediction717 == 1:
            uint128719 = self.consume_terminal("UINT128")
            _t1361 = logic_pb2.RelationId(id_low=uint128719.low, id_high=uint128719.high)
        else:
            if prediction717 == 0:
                self.consume_literal(":")
                symbol718 = self.consume_terminal("SYMBOL")
                _t1362 = self.relation_id_from_string(symbol718)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1361 = _t1362
        result721 = _t1361
        self.record_span(span_start720, "RelationId")
        return result721

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start724 = self.span_start()
        self.consume_literal("(")
        _t1363 = self.parse_bindings()
        bindings722 = _t1363
        _t1364 = self.parse_formula()
        formula723 = _t1364
        self.consume_literal(")")
        _t1365 = logic_pb2.Abstraction(vars=(list(bindings722[0]) + list(bindings722[1] if bindings722[1] is not None else [])), value=formula723)
        result725 = _t1365
        self.record_span(span_start724, "Abstraction")
        return result725

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs726 = []
        cond727 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond727:
            _t1366 = self.parse_binding()
            item728 = _t1366
            xs726.append(item728)
            cond727 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings729 = xs726
        if self.match_lookahead_literal("|", 0):
            _t1368 = self.parse_value_bindings()
            _t1367 = _t1368
        else:
            _t1367 = None
        value_bindings730 = _t1367
        self.consume_literal("]")
        return (bindings729, (value_bindings730 if value_bindings730 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start733 = self.span_start()
        symbol731 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1369 = self.parse_type()
        type732 = _t1369
        _t1370 = logic_pb2.Var(name=symbol731)
        _t1371 = logic_pb2.Binding(var=_t1370, type=type732)
        result734 = _t1371
        self.record_span(span_start733, "Binding")
        return result734

    def parse_type(self) -> logic_pb2.Type:
        span_start750 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1372 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1373 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1374 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1375 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1376 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1377 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1378 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1379 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1380 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1381 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1382 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1383 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1384 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1385 = 9
                                                            else:
                                                                _t1385 = -1
                                                            _t1384 = _t1385
                                                        _t1383 = _t1384
                                                    _t1382 = _t1383
                                                _t1381 = _t1382
                                            _t1380 = _t1381
                                        _t1379 = _t1380
                                    _t1378 = _t1379
                                _t1377 = _t1378
                            _t1376 = _t1377
                        _t1375 = _t1376
                    _t1374 = _t1375
                _t1373 = _t1374
            _t1372 = _t1373
        prediction735 = _t1372
        if prediction735 == 13:
            _t1387 = self.parse_uint32_type()
            uint32_type749 = _t1387
            _t1388 = logic_pb2.Type(uint32_type=uint32_type749)
            _t1386 = _t1388
        else:
            if prediction735 == 12:
                _t1390 = self.parse_float32_type()
                float32_type748 = _t1390
                _t1391 = logic_pb2.Type(float32_type=float32_type748)
                _t1389 = _t1391
            else:
                if prediction735 == 11:
                    _t1393 = self.parse_int32_type()
                    int32_type747 = _t1393
                    _t1394 = logic_pb2.Type(int32_type=int32_type747)
                    _t1392 = _t1394
                else:
                    if prediction735 == 10:
                        _t1396 = self.parse_boolean_type()
                        boolean_type746 = _t1396
                        _t1397 = logic_pb2.Type(boolean_type=boolean_type746)
                        _t1395 = _t1397
                    else:
                        if prediction735 == 9:
                            _t1399 = self.parse_decimal_type()
                            decimal_type745 = _t1399
                            _t1400 = logic_pb2.Type(decimal_type=decimal_type745)
                            _t1398 = _t1400
                        else:
                            if prediction735 == 8:
                                _t1402 = self.parse_missing_type()
                                missing_type744 = _t1402
                                _t1403 = logic_pb2.Type(missing_type=missing_type744)
                                _t1401 = _t1403
                            else:
                                if prediction735 == 7:
                                    _t1405 = self.parse_datetime_type()
                                    datetime_type743 = _t1405
                                    _t1406 = logic_pb2.Type(datetime_type=datetime_type743)
                                    _t1404 = _t1406
                                else:
                                    if prediction735 == 6:
                                        _t1408 = self.parse_date_type()
                                        date_type742 = _t1408
                                        _t1409 = logic_pb2.Type(date_type=date_type742)
                                        _t1407 = _t1409
                                    else:
                                        if prediction735 == 5:
                                            _t1411 = self.parse_int128_type()
                                            int128_type741 = _t1411
                                            _t1412 = logic_pb2.Type(int128_type=int128_type741)
                                            _t1410 = _t1412
                                        else:
                                            if prediction735 == 4:
                                                _t1414 = self.parse_uint128_type()
                                                uint128_type740 = _t1414
                                                _t1415 = logic_pb2.Type(uint128_type=uint128_type740)
                                                _t1413 = _t1415
                                            else:
                                                if prediction735 == 3:
                                                    _t1417 = self.parse_float_type()
                                                    float_type739 = _t1417
                                                    _t1418 = logic_pb2.Type(float_type=float_type739)
                                                    _t1416 = _t1418
                                                else:
                                                    if prediction735 == 2:
                                                        _t1420 = self.parse_int_type()
                                                        int_type738 = _t1420
                                                        _t1421 = logic_pb2.Type(int_type=int_type738)
                                                        _t1419 = _t1421
                                                    else:
                                                        if prediction735 == 1:
                                                            _t1423 = self.parse_string_type()
                                                            string_type737 = _t1423
                                                            _t1424 = logic_pb2.Type(string_type=string_type737)
                                                            _t1422 = _t1424
                                                        else:
                                                            if prediction735 == 0:
                                                                _t1426 = self.parse_unspecified_type()
                                                                unspecified_type736 = _t1426
                                                                _t1427 = logic_pb2.Type(unspecified_type=unspecified_type736)
                                                                _t1425 = _t1427
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t1422 = _t1425
                                                        _t1419 = _t1422
                                                    _t1416 = _t1419
                                                _t1413 = _t1416
                                            _t1410 = _t1413
                                        _t1407 = _t1410
                                    _t1404 = _t1407
                                _t1401 = _t1404
                            _t1398 = _t1401
                        _t1395 = _t1398
                    _t1392 = _t1395
                _t1389 = _t1392
            _t1386 = _t1389
        result751 = _t1386
        self.record_span(span_start750, "Type")
        return result751

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start752 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1428 = logic_pb2.UnspecifiedType()
        result753 = _t1428
        self.record_span(span_start752, "UnspecifiedType")
        return result753

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start754 = self.span_start()
        self.consume_literal("STRING")
        _t1429 = logic_pb2.StringType()
        result755 = _t1429
        self.record_span(span_start754, "StringType")
        return result755

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start756 = self.span_start()
        self.consume_literal("INT")
        _t1430 = logic_pb2.IntType()
        result757 = _t1430
        self.record_span(span_start756, "IntType")
        return result757

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start758 = self.span_start()
        self.consume_literal("FLOAT")
        _t1431 = logic_pb2.FloatType()
        result759 = _t1431
        self.record_span(span_start758, "FloatType")
        return result759

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start760 = self.span_start()
        self.consume_literal("UINT128")
        _t1432 = logic_pb2.UInt128Type()
        result761 = _t1432
        self.record_span(span_start760, "UInt128Type")
        return result761

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start762 = self.span_start()
        self.consume_literal("INT128")
        _t1433 = logic_pb2.Int128Type()
        result763 = _t1433
        self.record_span(span_start762, "Int128Type")
        return result763

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start764 = self.span_start()
        self.consume_literal("DATE")
        _t1434 = logic_pb2.DateType()
        result765 = _t1434
        self.record_span(span_start764, "DateType")
        return result765

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start766 = self.span_start()
        self.consume_literal("DATETIME")
        _t1435 = logic_pb2.DateTimeType()
        result767 = _t1435
        self.record_span(span_start766, "DateTimeType")
        return result767

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start768 = self.span_start()
        self.consume_literal("MISSING")
        _t1436 = logic_pb2.MissingType()
        result769 = _t1436
        self.record_span(span_start768, "MissingType")
        return result769

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start772 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int770 = self.consume_terminal("INT")
        int_3771 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1437 = logic_pb2.DecimalType(precision=int(int770), scale=int(int_3771))
        result773 = _t1437
        self.record_span(span_start772, "DecimalType")
        return result773

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start774 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1438 = logic_pb2.BooleanType()
        result775 = _t1438
        self.record_span(span_start774, "BooleanType")
        return result775

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start776 = self.span_start()
        self.consume_literal("INT32")
        _t1439 = logic_pb2.Int32Type()
        result777 = _t1439
        self.record_span(span_start776, "Int32Type")
        return result777

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start778 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1440 = logic_pb2.Float32Type()
        result779 = _t1440
        self.record_span(span_start778, "Float32Type")
        return result779

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start780 = self.span_start()
        self.consume_literal("UINT32")
        _t1441 = logic_pb2.UInt32Type()
        result781 = _t1441
        self.record_span(span_start780, "UInt32Type")
        return result781

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs782 = []
        cond783 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond783:
            _t1442 = self.parse_binding()
            item784 = _t1442
            xs782.append(item784)
            cond783 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings785 = xs782
        return bindings785

    def parse_formula(self) -> logic_pb2.Formula:
        span_start800 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1444 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1445 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1446 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1447 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1448 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1449 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1450 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1451 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1452 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1453 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1454 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1455 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1456 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1457 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1458 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1459 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1460 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1461 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1462 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1463 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1464 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1465 = 10
                                                                                                else:
                                                                                                    _t1465 = -1
                                                                                                _t1464 = _t1465
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
                                        _t1450 = _t1451
                                    _t1449 = _t1450
                                _t1448 = _t1449
                            _t1447 = _t1448
                        _t1446 = _t1447
                    _t1445 = _t1446
                _t1444 = _t1445
            _t1443 = _t1444
        else:
            _t1443 = -1
        prediction786 = _t1443
        if prediction786 == 12:
            _t1467 = self.parse_cast()
            cast799 = _t1467
            _t1468 = logic_pb2.Formula(cast=cast799)
            _t1466 = _t1468
        else:
            if prediction786 == 11:
                _t1470 = self.parse_rel_atom()
                rel_atom798 = _t1470
                _t1471 = logic_pb2.Formula(rel_atom=rel_atom798)
                _t1469 = _t1471
            else:
                if prediction786 == 10:
                    _t1473 = self.parse_primitive()
                    primitive797 = _t1473
                    _t1474 = logic_pb2.Formula(primitive=primitive797)
                    _t1472 = _t1474
                else:
                    if prediction786 == 9:
                        _t1476 = self.parse_pragma()
                        pragma796 = _t1476
                        _t1477 = logic_pb2.Formula(pragma=pragma796)
                        _t1475 = _t1477
                    else:
                        if prediction786 == 8:
                            _t1479 = self.parse_atom()
                            atom795 = _t1479
                            _t1480 = logic_pb2.Formula(atom=atom795)
                            _t1478 = _t1480
                        else:
                            if prediction786 == 7:
                                _t1482 = self.parse_ffi()
                                ffi794 = _t1482
                                _t1483 = logic_pb2.Formula(ffi=ffi794)
                                _t1481 = _t1483
                            else:
                                if prediction786 == 6:
                                    _t1485 = self.parse_not()
                                    not793 = _t1485
                                    _t1486 = logic_pb2.Formula()
                                    getattr(_t1486, 'not').CopyFrom(not793)
                                    _t1484 = _t1486
                                else:
                                    if prediction786 == 5:
                                        _t1488 = self.parse_disjunction()
                                        disjunction792 = _t1488
                                        _t1489 = logic_pb2.Formula(disjunction=disjunction792)
                                        _t1487 = _t1489
                                    else:
                                        if prediction786 == 4:
                                            _t1491 = self.parse_conjunction()
                                            conjunction791 = _t1491
                                            _t1492 = logic_pb2.Formula(conjunction=conjunction791)
                                            _t1490 = _t1492
                                        else:
                                            if prediction786 == 3:
                                                _t1494 = self.parse_reduce()
                                                reduce790 = _t1494
                                                _t1495 = logic_pb2.Formula(reduce=reduce790)
                                                _t1493 = _t1495
                                            else:
                                                if prediction786 == 2:
                                                    _t1497 = self.parse_exists()
                                                    exists789 = _t1497
                                                    _t1498 = logic_pb2.Formula(exists=exists789)
                                                    _t1496 = _t1498
                                                else:
                                                    if prediction786 == 1:
                                                        _t1500 = self.parse_false()
                                                        false788 = _t1500
                                                        _t1501 = logic_pb2.Formula(disjunction=false788)
                                                        _t1499 = _t1501
                                                    else:
                                                        if prediction786 == 0:
                                                            _t1503 = self.parse_true()
                                                            true787 = _t1503
                                                            _t1504 = logic_pb2.Formula(conjunction=true787)
                                                            _t1502 = _t1504
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
        result801 = _t1466
        self.record_span(span_start800, "Formula")
        return result801

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start802 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1505 = logic_pb2.Conjunction(args=[])
        result803 = _t1505
        self.record_span(span_start802, "Conjunction")
        return result803

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start804 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1506 = logic_pb2.Disjunction(args=[])
        result805 = _t1506
        self.record_span(span_start804, "Disjunction")
        return result805

    def parse_exists(self) -> logic_pb2.Exists:
        span_start808 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1507 = self.parse_bindings()
        bindings806 = _t1507
        _t1508 = self.parse_formula()
        formula807 = _t1508
        self.consume_literal(")")
        _t1509 = logic_pb2.Abstraction(vars=(list(bindings806[0]) + list(bindings806[1] if bindings806[1] is not None else [])), value=formula807)
        _t1510 = logic_pb2.Exists(body=_t1509)
        result809 = _t1510
        self.record_span(span_start808, "Exists")
        return result809

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start813 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1511 = self.parse_abstraction()
        abstraction810 = _t1511
        _t1512 = self.parse_abstraction()
        abstraction_3811 = _t1512
        _t1513 = self.parse_terms()
        terms812 = _t1513
        self.consume_literal(")")
        _t1514 = logic_pb2.Reduce(op=abstraction810, body=abstraction_3811, terms=terms812)
        result814 = _t1514
        self.record_span(span_start813, "Reduce")
        return result814

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs815 = []
        cond816 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond816:
            _t1515 = self.parse_term()
            item817 = _t1515
            xs815.append(item817)
            cond816 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms818 = xs815
        self.consume_literal(")")
        return terms818

    def parse_term(self) -> logic_pb2.Term:
        span_start822 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1516 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1517 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1518 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1519 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1520 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1521 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1522 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1523 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1524 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1525 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1526 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1527 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1528 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1529 = 1
                                                            else:
                                                                _t1529 = -1
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
        prediction819 = _t1516
        if prediction819 == 1:
            _t1531 = self.parse_value()
            value821 = _t1531
            _t1532 = logic_pb2.Term(constant=value821)
            _t1530 = _t1532
        else:
            if prediction819 == 0:
                _t1534 = self.parse_var()
                var820 = _t1534
                _t1535 = logic_pb2.Term(var=var820)
                _t1533 = _t1535
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1530 = _t1533
        result823 = _t1530
        self.record_span(span_start822, "Term")
        return result823

    def parse_var(self) -> logic_pb2.Var:
        span_start825 = self.span_start()
        symbol824 = self.consume_terminal("SYMBOL")
        _t1536 = logic_pb2.Var(name=symbol824)
        result826 = _t1536
        self.record_span(span_start825, "Var")
        return result826

    def parse_value(self) -> logic_pb2.Value:
        span_start840 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1537 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1538 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1539 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1541 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1542 = 0
                            else:
                                _t1542 = -1
                            _t1541 = _t1542
                        _t1540 = _t1541
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1543 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1544 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1545 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1546 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1547 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1548 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1549 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1550 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1551 = 10
                                                        else:
                                                            _t1551 = -1
                                                        _t1550 = _t1551
                                                    _t1549 = _t1550
                                                _t1548 = _t1549
                                            _t1547 = _t1548
                                        _t1546 = _t1547
                                    _t1545 = _t1546
                                _t1544 = _t1545
                            _t1543 = _t1544
                        _t1540 = _t1543
                    _t1539 = _t1540
                _t1538 = _t1539
            _t1537 = _t1538
        prediction827 = _t1537
        if prediction827 == 12:
            _t1553 = self.parse_boolean_value()
            boolean_value839 = _t1553
            _t1554 = logic_pb2.Value(boolean_value=boolean_value839)
            _t1552 = _t1554
        else:
            if prediction827 == 11:
                self.consume_literal("missing")
                _t1556 = logic_pb2.MissingValue()
                _t1557 = logic_pb2.Value(missing_value=_t1556)
                _t1555 = _t1557
            else:
                if prediction827 == 10:
                    formatted_decimal838 = self.consume_terminal("DECIMAL")
                    _t1559 = logic_pb2.Value(decimal_value=formatted_decimal838)
                    _t1558 = _t1559
                else:
                    if prediction827 == 9:
                        formatted_int128837 = self.consume_terminal("INT128")
                        _t1561 = logic_pb2.Value(int128_value=formatted_int128837)
                        _t1560 = _t1561
                    else:
                        if prediction827 == 8:
                            formatted_uint128836 = self.consume_terminal("UINT128")
                            _t1563 = logic_pb2.Value(uint128_value=formatted_uint128836)
                            _t1562 = _t1563
                        else:
                            if prediction827 == 7:
                                formatted_uint32835 = self.consume_terminal("UINT32")
                                _t1565 = logic_pb2.Value(uint32_value=formatted_uint32835)
                                _t1564 = _t1565
                            else:
                                if prediction827 == 6:
                                    formatted_float834 = self.consume_terminal("FLOAT")
                                    _t1567 = logic_pb2.Value(float_value=formatted_float834)
                                    _t1566 = _t1567
                                else:
                                    if prediction827 == 5:
                                        formatted_float32833 = self.consume_terminal("FLOAT32")
                                        _t1569 = logic_pb2.Value(float32_value=formatted_float32833)
                                        _t1568 = _t1569
                                    else:
                                        if prediction827 == 4:
                                            formatted_int832 = self.consume_terminal("INT")
                                            _t1571 = logic_pb2.Value(int_value=formatted_int832)
                                            _t1570 = _t1571
                                        else:
                                            if prediction827 == 3:
                                                formatted_int32831 = self.consume_terminal("INT32")
                                                _t1573 = logic_pb2.Value(int32_value=formatted_int32831)
                                                _t1572 = _t1573
                                            else:
                                                if prediction827 == 2:
                                                    formatted_string830 = self.consume_terminal("STRING")
                                                    _t1575 = logic_pb2.Value(string_value=formatted_string830)
                                                    _t1574 = _t1575
                                                else:
                                                    if prediction827 == 1:
                                                        _t1577 = self.parse_datetime()
                                                        datetime829 = _t1577
                                                        _t1578 = logic_pb2.Value(datetime_value=datetime829)
                                                        _t1576 = _t1578
                                                    else:
                                                        if prediction827 == 0:
                                                            _t1580 = self.parse_date()
                                                            date828 = _t1580
                                                            _t1581 = logic_pb2.Value(date_value=date828)
                                                            _t1579 = _t1581
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1576 = _t1579
                                                    _t1574 = _t1576
                                                _t1572 = _t1574
                                            _t1570 = _t1572
                                        _t1568 = _t1570
                                    _t1566 = _t1568
                                _t1564 = _t1566
                            _t1562 = _t1564
                        _t1560 = _t1562
                    _t1558 = _t1560
                _t1555 = _t1558
            _t1552 = _t1555
        result841 = _t1552
        self.record_span(span_start840, "Value")
        return result841

    def parse_date(self) -> logic_pb2.DateValue:
        span_start845 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int842 = self.consume_terminal("INT")
        formatted_int_3843 = self.consume_terminal("INT")
        formatted_int_4844 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1582 = logic_pb2.DateValue(year=int(formatted_int842), month=int(formatted_int_3843), day=int(formatted_int_4844))
        result846 = _t1582
        self.record_span(span_start845, "DateValue")
        return result846

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start854 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int847 = self.consume_terminal("INT")
        formatted_int_3848 = self.consume_terminal("INT")
        formatted_int_4849 = self.consume_terminal("INT")
        formatted_int_5850 = self.consume_terminal("INT")
        formatted_int_6851 = self.consume_terminal("INT")
        formatted_int_7852 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1583 = self.consume_terminal("INT")
        else:
            _t1583 = None
        formatted_int_8853 = _t1583
        self.consume_literal(")")
        _t1584 = logic_pb2.DateTimeValue(year=int(formatted_int847), month=int(formatted_int_3848), day=int(formatted_int_4849), hour=int(formatted_int_5850), minute=int(formatted_int_6851), second=int(formatted_int_7852), microsecond=int((formatted_int_8853 if formatted_int_8853 is not None else 0)))
        result855 = _t1584
        self.record_span(span_start854, "DateTimeValue")
        return result855

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start860 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs856 = []
        cond857 = self.match_lookahead_literal("(", 0)
        while cond857:
            _t1585 = self.parse_formula()
            item858 = _t1585
            xs856.append(item858)
            cond857 = self.match_lookahead_literal("(", 0)
        formulas859 = xs856
        self.consume_literal(")")
        _t1586 = logic_pb2.Conjunction(args=formulas859)
        result861 = _t1586
        self.record_span(span_start860, "Conjunction")
        return result861

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start866 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs862 = []
        cond863 = self.match_lookahead_literal("(", 0)
        while cond863:
            _t1587 = self.parse_formula()
            item864 = _t1587
            xs862.append(item864)
            cond863 = self.match_lookahead_literal("(", 0)
        formulas865 = xs862
        self.consume_literal(")")
        _t1588 = logic_pb2.Disjunction(args=formulas865)
        result867 = _t1588
        self.record_span(span_start866, "Disjunction")
        return result867

    def parse_not(self) -> logic_pb2.Not:
        span_start869 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1589 = self.parse_formula()
        formula868 = _t1589
        self.consume_literal(")")
        _t1590 = logic_pb2.Not(arg=formula868)
        result870 = _t1590
        self.record_span(span_start869, "Not")
        return result870

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start874 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1591 = self.parse_name()
        name871 = _t1591
        _t1592 = self.parse_ffi_args()
        ffi_args872 = _t1592
        _t1593 = self.parse_terms()
        terms873 = _t1593
        self.consume_literal(")")
        _t1594 = logic_pb2.FFI(name=name871, args=ffi_args872, terms=terms873)
        result875 = _t1594
        self.record_span(span_start874, "FFI")
        return result875

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol876 = self.consume_terminal("SYMBOL")
        return symbol876

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs877 = []
        cond878 = self.match_lookahead_literal("(", 0)
        while cond878:
            _t1595 = self.parse_abstraction()
            item879 = _t1595
            xs877.append(item879)
            cond878 = self.match_lookahead_literal("(", 0)
        abstractions880 = xs877
        self.consume_literal(")")
        return abstractions880

    def parse_atom(self) -> logic_pb2.Atom:
        span_start886 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1596 = self.parse_relation_id()
        relation_id881 = _t1596
        xs882 = []
        cond883 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond883:
            _t1597 = self.parse_term()
            item884 = _t1597
            xs882.append(item884)
            cond883 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms885 = xs882
        self.consume_literal(")")
        _t1598 = logic_pb2.Atom(name=relation_id881, terms=terms885)
        result887 = _t1598
        self.record_span(span_start886, "Atom")
        return result887

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start893 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1599 = self.parse_name()
        name888 = _t1599
        xs889 = []
        cond890 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond890:
            _t1600 = self.parse_term()
            item891 = _t1600
            xs889.append(item891)
            cond890 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms892 = xs889
        self.consume_literal(")")
        _t1601 = logic_pb2.Pragma(name=name888, terms=terms892)
        result894 = _t1601
        self.record_span(span_start893, "Pragma")
        return result894

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start910 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1603 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1604 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1605 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1606 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1607 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1608 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1609 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1610 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1611 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1612 = 7
                                                else:
                                                    _t1612 = -1
                                                _t1611 = _t1612
                                            _t1610 = _t1611
                                        _t1609 = _t1610
                                    _t1608 = _t1609
                                _t1607 = _t1608
                            _t1606 = _t1607
                        _t1605 = _t1606
                    _t1604 = _t1605
                _t1603 = _t1604
            _t1602 = _t1603
        else:
            _t1602 = -1
        prediction895 = _t1602
        if prediction895 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1614 = self.parse_name()
            name905 = _t1614
            xs906 = []
            cond907 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond907:
                _t1615 = self.parse_rel_term()
                item908 = _t1615
                xs906.append(item908)
                cond907 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms909 = xs906
            self.consume_literal(")")
            _t1616 = logic_pb2.Primitive(name=name905, terms=rel_terms909)
            _t1613 = _t1616
        else:
            if prediction895 == 8:
                _t1618 = self.parse_divide()
                divide904 = _t1618
                _t1617 = divide904
            else:
                if prediction895 == 7:
                    _t1620 = self.parse_multiply()
                    multiply903 = _t1620
                    _t1619 = multiply903
                else:
                    if prediction895 == 6:
                        _t1622 = self.parse_minus()
                        minus902 = _t1622
                        _t1621 = minus902
                    else:
                        if prediction895 == 5:
                            _t1624 = self.parse_add()
                            add901 = _t1624
                            _t1623 = add901
                        else:
                            if prediction895 == 4:
                                _t1626 = self.parse_gt_eq()
                                gt_eq900 = _t1626
                                _t1625 = gt_eq900
                            else:
                                if prediction895 == 3:
                                    _t1628 = self.parse_gt()
                                    gt899 = _t1628
                                    _t1627 = gt899
                                else:
                                    if prediction895 == 2:
                                        _t1630 = self.parse_lt_eq()
                                        lt_eq898 = _t1630
                                        _t1629 = lt_eq898
                                    else:
                                        if prediction895 == 1:
                                            _t1632 = self.parse_lt()
                                            lt897 = _t1632
                                            _t1631 = lt897
                                        else:
                                            if prediction895 == 0:
                                                _t1634 = self.parse_eq()
                                                eq896 = _t1634
                                                _t1633 = eq896
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1631 = _t1633
                                        _t1629 = _t1631
                                    _t1627 = _t1629
                                _t1625 = _t1627
                            _t1623 = _t1625
                        _t1621 = _t1623
                    _t1619 = _t1621
                _t1617 = _t1619
            _t1613 = _t1617
        result911 = _t1613
        self.record_span(span_start910, "Primitive")
        return result911

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start914 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1635 = self.parse_term()
        term912 = _t1635
        _t1636 = self.parse_term()
        term_3913 = _t1636
        self.consume_literal(")")
        _t1637 = logic_pb2.RelTerm(term=term912)
        _t1638 = logic_pb2.RelTerm(term=term_3913)
        _t1639 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1637, _t1638])
        result915 = _t1639
        self.record_span(span_start914, "Primitive")
        return result915

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start918 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1640 = self.parse_term()
        term916 = _t1640
        _t1641 = self.parse_term()
        term_3917 = _t1641
        self.consume_literal(")")
        _t1642 = logic_pb2.RelTerm(term=term916)
        _t1643 = logic_pb2.RelTerm(term=term_3917)
        _t1644 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1642, _t1643])
        result919 = _t1644
        self.record_span(span_start918, "Primitive")
        return result919

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start922 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1645 = self.parse_term()
        term920 = _t1645
        _t1646 = self.parse_term()
        term_3921 = _t1646
        self.consume_literal(")")
        _t1647 = logic_pb2.RelTerm(term=term920)
        _t1648 = logic_pb2.RelTerm(term=term_3921)
        _t1649 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1647, _t1648])
        result923 = _t1649
        self.record_span(span_start922, "Primitive")
        return result923

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start926 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1650 = self.parse_term()
        term924 = _t1650
        _t1651 = self.parse_term()
        term_3925 = _t1651
        self.consume_literal(")")
        _t1652 = logic_pb2.RelTerm(term=term924)
        _t1653 = logic_pb2.RelTerm(term=term_3925)
        _t1654 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1652, _t1653])
        result927 = _t1654
        self.record_span(span_start926, "Primitive")
        return result927

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start930 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1655 = self.parse_term()
        term928 = _t1655
        _t1656 = self.parse_term()
        term_3929 = _t1656
        self.consume_literal(")")
        _t1657 = logic_pb2.RelTerm(term=term928)
        _t1658 = logic_pb2.RelTerm(term=term_3929)
        _t1659 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1657, _t1658])
        result931 = _t1659
        self.record_span(span_start930, "Primitive")
        return result931

    def parse_add(self) -> logic_pb2.Primitive:
        span_start935 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1660 = self.parse_term()
        term932 = _t1660
        _t1661 = self.parse_term()
        term_3933 = _t1661
        _t1662 = self.parse_term()
        term_4934 = _t1662
        self.consume_literal(")")
        _t1663 = logic_pb2.RelTerm(term=term932)
        _t1664 = logic_pb2.RelTerm(term=term_3933)
        _t1665 = logic_pb2.RelTerm(term=term_4934)
        _t1666 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1663, _t1664, _t1665])
        result936 = _t1666
        self.record_span(span_start935, "Primitive")
        return result936

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start940 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1667 = self.parse_term()
        term937 = _t1667
        _t1668 = self.parse_term()
        term_3938 = _t1668
        _t1669 = self.parse_term()
        term_4939 = _t1669
        self.consume_literal(")")
        _t1670 = logic_pb2.RelTerm(term=term937)
        _t1671 = logic_pb2.RelTerm(term=term_3938)
        _t1672 = logic_pb2.RelTerm(term=term_4939)
        _t1673 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1670, _t1671, _t1672])
        result941 = _t1673
        self.record_span(span_start940, "Primitive")
        return result941

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start945 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1674 = self.parse_term()
        term942 = _t1674
        _t1675 = self.parse_term()
        term_3943 = _t1675
        _t1676 = self.parse_term()
        term_4944 = _t1676
        self.consume_literal(")")
        _t1677 = logic_pb2.RelTerm(term=term942)
        _t1678 = logic_pb2.RelTerm(term=term_3943)
        _t1679 = logic_pb2.RelTerm(term=term_4944)
        _t1680 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1677, _t1678, _t1679])
        result946 = _t1680
        self.record_span(span_start945, "Primitive")
        return result946

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start950 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1681 = self.parse_term()
        term947 = _t1681
        _t1682 = self.parse_term()
        term_3948 = _t1682
        _t1683 = self.parse_term()
        term_4949 = _t1683
        self.consume_literal(")")
        _t1684 = logic_pb2.RelTerm(term=term947)
        _t1685 = logic_pb2.RelTerm(term=term_3948)
        _t1686 = logic_pb2.RelTerm(term=term_4949)
        _t1687 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1684, _t1685, _t1686])
        result951 = _t1687
        self.record_span(span_start950, "Primitive")
        return result951

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start955 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1688 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1689 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1690 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1691 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1692 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1693 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1694 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1695 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1696 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1697 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1698 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1699 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1700 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1701 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1702 = 1
                                                                else:
                                                                    _t1702 = -1
                                                                _t1701 = _t1702
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
                    _t1690 = _t1691
                _t1689 = _t1690
            _t1688 = _t1689
        prediction952 = _t1688
        if prediction952 == 1:
            _t1704 = self.parse_term()
            term954 = _t1704
            _t1705 = logic_pb2.RelTerm(term=term954)
            _t1703 = _t1705
        else:
            if prediction952 == 0:
                _t1707 = self.parse_specialized_value()
                specialized_value953 = _t1707
                _t1708 = logic_pb2.RelTerm(specialized_value=specialized_value953)
                _t1706 = _t1708
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1703 = _t1706
        result956 = _t1703
        self.record_span(span_start955, "RelTerm")
        return result956

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start958 = self.span_start()
        self.consume_literal("#")
        _t1709 = self.parse_raw_value()
        raw_value957 = _t1709
        result959 = raw_value957
        self.record_span(span_start958, "Value")
        return result959

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start965 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1710 = self.parse_name()
        name960 = _t1710
        xs961 = []
        cond962 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond962:
            _t1711 = self.parse_rel_term()
            item963 = _t1711
            xs961.append(item963)
            cond962 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms964 = xs961
        self.consume_literal(")")
        _t1712 = logic_pb2.RelAtom(name=name960, terms=rel_terms964)
        result966 = _t1712
        self.record_span(span_start965, "RelAtom")
        return result966

    def parse_cast(self) -> logic_pb2.Cast:
        span_start969 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1713 = self.parse_term()
        term967 = _t1713
        _t1714 = self.parse_term()
        term_3968 = _t1714
        self.consume_literal(")")
        _t1715 = logic_pb2.Cast(input=term967, result=term_3968)
        result970 = _t1715
        self.record_span(span_start969, "Cast")
        return result970

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs971 = []
        cond972 = self.match_lookahead_literal("(", 0)
        while cond972:
            _t1716 = self.parse_attribute()
            item973 = _t1716
            xs971.append(item973)
            cond972 = self.match_lookahead_literal("(", 0)
        attributes974 = xs971
        self.consume_literal(")")
        return attributes974

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start980 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1717 = self.parse_name()
        name975 = _t1717
        xs976 = []
        cond977 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond977:
            _t1718 = self.parse_raw_value()
            item978 = _t1718
            xs976.append(item978)
            cond977 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values979 = xs976
        self.consume_literal(")")
        _t1719 = logic_pb2.Attribute(name=name975, args=raw_values979)
        result981 = _t1719
        self.record_span(span_start980, "Attribute")
        return result981

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start987 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs982 = []
        cond983 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond983:
            _t1720 = self.parse_relation_id()
            item984 = _t1720
            xs982.append(item984)
            cond983 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids985 = xs982
        _t1721 = self.parse_script()
        script986 = _t1721
        self.consume_literal(")")
        _t1722 = logic_pb2.Algorithm(body=script986)
        getattr(_t1722, 'global').extend(relation_ids985)
        result988 = _t1722
        self.record_span(span_start987, "Algorithm")
        return result988

    def parse_script(self) -> logic_pb2.Script:
        span_start993 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs989 = []
        cond990 = self.match_lookahead_literal("(", 0)
        while cond990:
            _t1723 = self.parse_construct()
            item991 = _t1723
            xs989.append(item991)
            cond990 = self.match_lookahead_literal("(", 0)
        constructs992 = xs989
        self.consume_literal(")")
        _t1724 = logic_pb2.Script(constructs=constructs992)
        result994 = _t1724
        self.record_span(span_start993, "Script")
        return result994

    def parse_construct(self) -> logic_pb2.Construct:
        span_start998 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1726 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1727 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1728 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1729 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1730 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1731 = 1
                                else:
                                    _t1731 = -1
                                _t1730 = _t1731
                            _t1729 = _t1730
                        _t1728 = _t1729
                    _t1727 = _t1728
                _t1726 = _t1727
            _t1725 = _t1726
        else:
            _t1725 = -1
        prediction995 = _t1725
        if prediction995 == 1:
            _t1733 = self.parse_instruction()
            instruction997 = _t1733
            _t1734 = logic_pb2.Construct(instruction=instruction997)
            _t1732 = _t1734
        else:
            if prediction995 == 0:
                _t1736 = self.parse_loop()
                loop996 = _t1736
                _t1737 = logic_pb2.Construct(loop=loop996)
                _t1735 = _t1737
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1732 = _t1735
        result999 = _t1732
        self.record_span(span_start998, "Construct")
        return result999

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1002 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1738 = self.parse_init()
        init1000 = _t1738
        _t1739 = self.parse_script()
        script1001 = _t1739
        self.consume_literal(")")
        _t1740 = logic_pb2.Loop(init=init1000, body=script1001)
        result1003 = _t1740
        self.record_span(span_start1002, "Loop")
        return result1003

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1004 = []
        cond1005 = self.match_lookahead_literal("(", 0)
        while cond1005:
            _t1741 = self.parse_instruction()
            item1006 = _t1741
            xs1004.append(item1006)
            cond1005 = self.match_lookahead_literal("(", 0)
        instructions1007 = xs1004
        self.consume_literal(")")
        return instructions1007

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1014 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1743 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1744 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1745 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1746 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1747 = 0
                            else:
                                _t1747 = -1
                            _t1746 = _t1747
                        _t1745 = _t1746
                    _t1744 = _t1745
                _t1743 = _t1744
            _t1742 = _t1743
        else:
            _t1742 = -1
        prediction1008 = _t1742
        if prediction1008 == 4:
            _t1749 = self.parse_monus_def()
            monus_def1013 = _t1749
            _t1750 = logic_pb2.Instruction(monus_def=monus_def1013)
            _t1748 = _t1750
        else:
            if prediction1008 == 3:
                _t1752 = self.parse_monoid_def()
                monoid_def1012 = _t1752
                _t1753 = logic_pb2.Instruction(monoid_def=monoid_def1012)
                _t1751 = _t1753
            else:
                if prediction1008 == 2:
                    _t1755 = self.parse_break()
                    break1011 = _t1755
                    _t1756 = logic_pb2.Instruction()
                    getattr(_t1756, 'break').CopyFrom(break1011)
                    _t1754 = _t1756
                else:
                    if prediction1008 == 1:
                        _t1758 = self.parse_upsert()
                        upsert1010 = _t1758
                        _t1759 = logic_pb2.Instruction(upsert=upsert1010)
                        _t1757 = _t1759
                    else:
                        if prediction1008 == 0:
                            _t1761 = self.parse_assign()
                            assign1009 = _t1761
                            _t1762 = logic_pb2.Instruction(assign=assign1009)
                            _t1760 = _t1762
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1757 = _t1760
                    _t1754 = _t1757
                _t1751 = _t1754
            _t1748 = _t1751
        result1015 = _t1748
        self.record_span(span_start1014, "Instruction")
        return result1015

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1019 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1763 = self.parse_relation_id()
        relation_id1016 = _t1763
        _t1764 = self.parse_abstraction()
        abstraction1017 = _t1764
        if self.match_lookahead_literal("(", 0):
            _t1766 = self.parse_attrs()
            _t1765 = _t1766
        else:
            _t1765 = None
        attrs1018 = _t1765
        self.consume_literal(")")
        _t1767 = logic_pb2.Assign(name=relation_id1016, body=abstraction1017, attrs=(attrs1018 if attrs1018 is not None else []))
        result1020 = _t1767
        self.record_span(span_start1019, "Assign")
        return result1020

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1024 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1768 = self.parse_relation_id()
        relation_id1021 = _t1768
        _t1769 = self.parse_abstraction_with_arity()
        abstraction_with_arity1022 = _t1769
        if self.match_lookahead_literal("(", 0):
            _t1771 = self.parse_attrs()
            _t1770 = _t1771
        else:
            _t1770 = None
        attrs1023 = _t1770
        self.consume_literal(")")
        _t1772 = logic_pb2.Upsert(name=relation_id1021, body=abstraction_with_arity1022[0], attrs=(attrs1023 if attrs1023 is not None else []), value_arity=abstraction_with_arity1022[1])
        result1025 = _t1772
        self.record_span(span_start1024, "Upsert")
        return result1025

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1773 = self.parse_bindings()
        bindings1026 = _t1773
        _t1774 = self.parse_formula()
        formula1027 = _t1774
        self.consume_literal(")")
        _t1775 = logic_pb2.Abstraction(vars=(list(bindings1026[0]) + list(bindings1026[1] if bindings1026[1] is not None else [])), value=formula1027)
        return (_t1775, len(bindings1026[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1031 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1776 = self.parse_relation_id()
        relation_id1028 = _t1776
        _t1777 = self.parse_abstraction()
        abstraction1029 = _t1777
        if self.match_lookahead_literal("(", 0):
            _t1779 = self.parse_attrs()
            _t1778 = _t1779
        else:
            _t1778 = None
        attrs1030 = _t1778
        self.consume_literal(")")
        _t1780 = logic_pb2.Break(name=relation_id1028, body=abstraction1029, attrs=(attrs1030 if attrs1030 is not None else []))
        result1032 = _t1780
        self.record_span(span_start1031, "Break")
        return result1032

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1037 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1781 = self.parse_monoid()
        monoid1033 = _t1781
        _t1782 = self.parse_relation_id()
        relation_id1034 = _t1782
        _t1783 = self.parse_abstraction_with_arity()
        abstraction_with_arity1035 = _t1783
        if self.match_lookahead_literal("(", 0):
            _t1785 = self.parse_attrs()
            _t1784 = _t1785
        else:
            _t1784 = None
        attrs1036 = _t1784
        self.consume_literal(")")
        _t1786 = logic_pb2.MonoidDef(monoid=monoid1033, name=relation_id1034, body=abstraction_with_arity1035[0], attrs=(attrs1036 if attrs1036 is not None else []), value_arity=abstraction_with_arity1035[1])
        result1038 = _t1786
        self.record_span(span_start1037, "MonoidDef")
        return result1038

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1044 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1788 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1789 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1790 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1791 = 2
                        else:
                            _t1791 = -1
                        _t1790 = _t1791
                    _t1789 = _t1790
                _t1788 = _t1789
            _t1787 = _t1788
        else:
            _t1787 = -1
        prediction1039 = _t1787
        if prediction1039 == 3:
            _t1793 = self.parse_sum_monoid()
            sum_monoid1043 = _t1793
            _t1794 = logic_pb2.Monoid(sum_monoid=sum_monoid1043)
            _t1792 = _t1794
        else:
            if prediction1039 == 2:
                _t1796 = self.parse_max_monoid()
                max_monoid1042 = _t1796
                _t1797 = logic_pb2.Monoid(max_monoid=max_monoid1042)
                _t1795 = _t1797
            else:
                if prediction1039 == 1:
                    _t1799 = self.parse_min_monoid()
                    min_monoid1041 = _t1799
                    _t1800 = logic_pb2.Monoid(min_monoid=min_monoid1041)
                    _t1798 = _t1800
                else:
                    if prediction1039 == 0:
                        _t1802 = self.parse_or_monoid()
                        or_monoid1040 = _t1802
                        _t1803 = logic_pb2.Monoid(or_monoid=or_monoid1040)
                        _t1801 = _t1803
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1798 = _t1801
                _t1795 = _t1798
            _t1792 = _t1795
        result1045 = _t1792
        self.record_span(span_start1044, "Monoid")
        return result1045

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1046 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1804 = logic_pb2.OrMonoid()
        result1047 = _t1804
        self.record_span(span_start1046, "OrMonoid")
        return result1047

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1049 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1805 = self.parse_type()
        type1048 = _t1805
        self.consume_literal(")")
        _t1806 = logic_pb2.MinMonoid(type=type1048)
        result1050 = _t1806
        self.record_span(span_start1049, "MinMonoid")
        return result1050

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1052 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1807 = self.parse_type()
        type1051 = _t1807
        self.consume_literal(")")
        _t1808 = logic_pb2.MaxMonoid(type=type1051)
        result1053 = _t1808
        self.record_span(span_start1052, "MaxMonoid")
        return result1053

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1055 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1809 = self.parse_type()
        type1054 = _t1809
        self.consume_literal(")")
        _t1810 = logic_pb2.SumMonoid(type=type1054)
        result1056 = _t1810
        self.record_span(span_start1055, "SumMonoid")
        return result1056

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1061 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1811 = self.parse_monoid()
        monoid1057 = _t1811
        _t1812 = self.parse_relation_id()
        relation_id1058 = _t1812
        _t1813 = self.parse_abstraction_with_arity()
        abstraction_with_arity1059 = _t1813
        if self.match_lookahead_literal("(", 0):
            _t1815 = self.parse_attrs()
            _t1814 = _t1815
        else:
            _t1814 = None
        attrs1060 = _t1814
        self.consume_literal(")")
        _t1816 = logic_pb2.MonusDef(monoid=monoid1057, name=relation_id1058, body=abstraction_with_arity1059[0], attrs=(attrs1060 if attrs1060 is not None else []), value_arity=abstraction_with_arity1059[1])
        result1062 = _t1816
        self.record_span(span_start1061, "MonusDef")
        return result1062

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1067 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1817 = self.parse_relation_id()
        relation_id1063 = _t1817
        _t1818 = self.parse_abstraction()
        abstraction1064 = _t1818
        _t1819 = self.parse_functional_dependency_keys()
        functional_dependency_keys1065 = _t1819
        _t1820 = self.parse_functional_dependency_values()
        functional_dependency_values1066 = _t1820
        self.consume_literal(")")
        _t1821 = logic_pb2.FunctionalDependency(guard=abstraction1064, keys=functional_dependency_keys1065, values=functional_dependency_values1066)
        _t1822 = logic_pb2.Constraint(name=relation_id1063, functional_dependency=_t1821)
        result1068 = _t1822
        self.record_span(span_start1067, "Constraint")
        return result1068

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1069 = []
        cond1070 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1070:
            _t1823 = self.parse_var()
            item1071 = _t1823
            xs1069.append(item1071)
            cond1070 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1072 = xs1069
        self.consume_literal(")")
        return vars1072

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1073 = []
        cond1074 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1074:
            _t1824 = self.parse_var()
            item1075 = _t1824
            xs1073.append(item1075)
            cond1074 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1076 = xs1073
        self.consume_literal(")")
        return vars1076

    def parse_data(self) -> logic_pb2.Data:
        span_start1081 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("edb", 1):
                _t1826 = 0
            else:
                if self.match_lookahead_literal("csv_data", 1):
                    _t1827 = 2
                else:
                    if self.match_lookahead_literal("betree_relation", 1):
                        _t1828 = 1
                    else:
                        _t1828 = -1
                    _t1827 = _t1828
                _t1826 = _t1827
            _t1825 = _t1826
        else:
            _t1825 = -1
        prediction1077 = _t1825
        if prediction1077 == 2:
            _t1830 = self.parse_csv_data()
            csv_data1080 = _t1830
            _t1831 = logic_pb2.Data(csv_data=csv_data1080)
            _t1829 = _t1831
        else:
            if prediction1077 == 1:
                _t1833 = self.parse_betree_relation()
                betree_relation1079 = _t1833
                _t1834 = logic_pb2.Data(betree_relation=betree_relation1079)
                _t1832 = _t1834
            else:
                if prediction1077 == 0:
                    _t1836 = self.parse_edb()
                    edb1078 = _t1836
                    _t1837 = logic_pb2.Data(edb=edb1078)
                    _t1835 = _t1837
                else:
                    raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t1832 = _t1835
            _t1829 = _t1832
        result1082 = _t1829
        self.record_span(span_start1081, "Data")
        return result1082

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1086 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1838 = self.parse_relation_id()
        relation_id1083 = _t1838
        _t1839 = self.parse_edb_path()
        edb_path1084 = _t1839
        _t1840 = self.parse_edb_types()
        edb_types1085 = _t1840
        self.consume_literal(")")
        _t1841 = logic_pb2.EDB(target_id=relation_id1083, path=edb_path1084, types=edb_types1085)
        result1087 = _t1841
        self.record_span(span_start1086, "EDB")
        return result1087

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1088 = []
        cond1089 = self.match_lookahead_terminal("STRING", 0)
        while cond1089:
            item1090 = self.consume_terminal("STRING")
            xs1088.append(item1090)
            cond1089 = self.match_lookahead_terminal("STRING", 0)
        strings1091 = xs1088
        self.consume_literal("]")
        return strings1091

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1092 = []
        cond1093 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1093:
            _t1842 = self.parse_type()
            item1094 = _t1842
            xs1092.append(item1094)
            cond1093 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1095 = xs1092
        self.consume_literal("]")
        return types1095

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1098 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1843 = self.parse_relation_id()
        relation_id1096 = _t1843
        _t1844 = self.parse_betree_info()
        betree_info1097 = _t1844
        self.consume_literal(")")
        _t1845 = logic_pb2.BeTreeRelation(name=relation_id1096, relation_info=betree_info1097)
        result1099 = _t1845
        self.record_span(span_start1098, "BeTreeRelation")
        return result1099

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1103 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1846 = self.parse_betree_info_key_types()
        betree_info_key_types1100 = _t1846
        _t1847 = self.parse_betree_info_value_types()
        betree_info_value_types1101 = _t1847
        _t1848 = self.parse_config_dict()
        config_dict1102 = _t1848
        self.consume_literal(")")
        _t1849 = self.construct_betree_info(betree_info_key_types1100, betree_info_value_types1101, config_dict1102)
        result1104 = _t1849
        self.record_span(span_start1103, "BeTreeInfo")
        return result1104

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1105 = []
        cond1106 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1106:
            _t1850 = self.parse_type()
            item1107 = _t1850
            xs1105.append(item1107)
            cond1106 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1108 = xs1105
        self.consume_literal(")")
        return types1108

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1109 = []
        cond1110 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1110:
            _t1851 = self.parse_type()
            item1111 = _t1851
            xs1109.append(item1111)
            cond1110 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1112 = xs1109
        self.consume_literal(")")
        return types1112

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1117 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1852 = self.parse_csvlocator()
        csvlocator1113 = _t1852
        _t1853 = self.parse_csv_config()
        csv_config1114 = _t1853
        _t1854 = self.parse_gnf_columns()
        gnf_columns1115 = _t1854
        _t1855 = self.parse_csv_asof()
        csv_asof1116 = _t1855
        self.consume_literal(")")
        _t1856 = logic_pb2.CSVData(locator=csvlocator1113, config=csv_config1114, columns=gnf_columns1115, asof=csv_asof1116)
        result1118 = _t1856
        self.record_span(span_start1117, "CSVData")
        return result1118

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1121 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1858 = self.parse_csv_locator_paths()
            _t1857 = _t1858
        else:
            _t1857 = None
        csv_locator_paths1119 = _t1857
        if self.match_lookahead_literal("(", 0):
            _t1860 = self.parse_csv_locator_inline_data()
            _t1859 = _t1860
        else:
            _t1859 = None
        csv_locator_inline_data1120 = _t1859
        self.consume_literal(")")
        _t1861 = logic_pb2.CSVLocator(paths=(csv_locator_paths1119 if csv_locator_paths1119 is not None else []), inline_data=(csv_locator_inline_data1120 if csv_locator_inline_data1120 is not None else "").encode())
        result1122 = _t1861
        self.record_span(span_start1121, "CSVLocator")
        return result1122

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1123 = []
        cond1124 = self.match_lookahead_terminal("STRING", 0)
        while cond1124:
            item1125 = self.consume_terminal("STRING")
            xs1123.append(item1125)
            cond1124 = self.match_lookahead_terminal("STRING", 0)
        strings1126 = xs1123
        self.consume_literal(")")
        return strings1126

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1127 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1127

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1129 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1862 = self.parse_config_dict()
        config_dict1128 = _t1862
        self.consume_literal(")")
        _t1863 = self.construct_csv_config(config_dict1128)
        result1130 = _t1863
        self.record_span(span_start1129, "CSVConfig")
        return result1130

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1131 = []
        cond1132 = self.match_lookahead_literal("(", 0)
        while cond1132:
            _t1864 = self.parse_gnf_column()
            item1133 = _t1864
            xs1131.append(item1133)
            cond1132 = self.match_lookahead_literal("(", 0)
        gnf_columns1134 = xs1131
        self.consume_literal(")")
        return gnf_columns1134

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1141 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1865 = self.parse_gnf_column_path()
        gnf_column_path1135 = _t1865
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1867 = self.parse_relation_id()
            _t1866 = _t1867
        else:
            _t1866 = None
        relation_id1136 = _t1866
        self.consume_literal("[")
        xs1137 = []
        cond1138 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1138:
            _t1868 = self.parse_type()
            item1139 = _t1868
            xs1137.append(item1139)
            cond1138 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1140 = xs1137
        self.consume_literal("]")
        self.consume_literal(")")
        _t1869 = logic_pb2.GNFColumn(column_path=gnf_column_path1135, target_id=relation_id1136, types=types1140)
        result1142 = _t1869
        self.record_span(span_start1141, "GNFColumn")
        return result1142

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1870 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1871 = 0
            else:
                _t1871 = -1
            _t1870 = _t1871
        prediction1143 = _t1870
        if prediction1143 == 1:
            self.consume_literal("[")
            xs1145 = []
            cond1146 = self.match_lookahead_terminal("STRING", 0)
            while cond1146:
                item1147 = self.consume_terminal("STRING")
                xs1145.append(item1147)
                cond1146 = self.match_lookahead_terminal("STRING", 0)
            strings1148 = xs1145
            self.consume_literal("]")
            _t1872 = strings1148
        else:
            if prediction1143 == 0:
                string1144 = self.consume_terminal("STRING")
                _t1873 = [string1144]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1872 = _t1873
        return _t1872

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1149 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1149

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1151 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1874 = self.parse_fragment_id()
        fragment_id1150 = _t1874
        self.consume_literal(")")
        _t1875 = transactions_pb2.Undefine(fragment_id=fragment_id1150)
        result1152 = _t1875
        self.record_span(span_start1151, "Undefine")
        return result1152

    def parse_context(self) -> transactions_pb2.Context:
        span_start1157 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1153 = []
        cond1154 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1154:
            _t1876 = self.parse_relation_id()
            item1155 = _t1876
            xs1153.append(item1155)
            cond1154 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1156 = xs1153
        self.consume_literal(")")
        _t1877 = transactions_pb2.Context(relations=relation_ids1156)
        result1158 = _t1877
        self.record_span(span_start1157, "Context")
        return result1158

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1163 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        xs1159 = []
        cond1160 = self.match_lookahead_literal("[", 0)
        while cond1160:
            _t1878 = self.parse_snapshot_mapping()
            item1161 = _t1878
            xs1159.append(item1161)
            cond1160 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1162 = xs1159
        self.consume_literal(")")
        _t1879 = transactions_pb2.Snapshot(mappings=snapshot_mappings1162)
        result1164 = _t1879
        self.record_span(span_start1163, "Snapshot")
        return result1164

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1167 = self.span_start()
        _t1880 = self.parse_edb_path()
        edb_path1165 = _t1880
        _t1881 = self.parse_relation_id()
        relation_id1166 = _t1881
        _t1882 = transactions_pb2.SnapshotMapping(destination_path=edb_path1165, source_relation=relation_id1166)
        result1168 = _t1882
        self.record_span(span_start1167, "SnapshotMapping")
        return result1168

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1169 = []
        cond1170 = self.match_lookahead_literal("(", 0)
        while cond1170:
            _t1883 = self.parse_read()
            item1171 = _t1883
            xs1169.append(item1171)
            cond1170 = self.match_lookahead_literal("(", 0)
        reads1172 = xs1169
        self.consume_literal(")")
        return reads1172

    def parse_read(self) -> transactions_pb2.Read:
        span_start1179 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1885 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1886 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t1887 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t1888 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t1889 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t1890 = 3
                                else:
                                    _t1890 = -1
                                _t1889 = _t1890
                            _t1888 = _t1889
                        _t1887 = _t1888
                    _t1886 = _t1887
                _t1885 = _t1886
            _t1884 = _t1885
        else:
            _t1884 = -1
        prediction1173 = _t1884
        if prediction1173 == 4:
            _t1892 = self.parse_export()
            export1178 = _t1892
            _t1893 = transactions_pb2.Read(export=export1178)
            _t1891 = _t1893
        else:
            if prediction1173 == 3:
                _t1895 = self.parse_abort()
                abort1177 = _t1895
                _t1896 = transactions_pb2.Read(abort=abort1177)
                _t1894 = _t1896
            else:
                if prediction1173 == 2:
                    _t1898 = self.parse_what_if()
                    what_if1176 = _t1898
                    _t1899 = transactions_pb2.Read(what_if=what_if1176)
                    _t1897 = _t1899
                else:
                    if prediction1173 == 1:
                        _t1901 = self.parse_output()
                        output1175 = _t1901
                        _t1902 = transactions_pb2.Read(output=output1175)
                        _t1900 = _t1902
                    else:
                        if prediction1173 == 0:
                            _t1904 = self.parse_demand()
                            demand1174 = _t1904
                            _t1905 = transactions_pb2.Read(demand=demand1174)
                            _t1903 = _t1905
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1900 = _t1903
                    _t1897 = _t1900
                _t1894 = _t1897
            _t1891 = _t1894
        result1180 = _t1891
        self.record_span(span_start1179, "Read")
        return result1180

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1182 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1906 = self.parse_relation_id()
        relation_id1181 = _t1906
        self.consume_literal(")")
        _t1907 = transactions_pb2.Demand(relation_id=relation_id1181)
        result1183 = _t1907
        self.record_span(span_start1182, "Demand")
        return result1183

    def parse_output(self) -> transactions_pb2.Output:
        span_start1186 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t1908 = self.parse_name()
        name1184 = _t1908
        _t1909 = self.parse_relation_id()
        relation_id1185 = _t1909
        self.consume_literal(")")
        _t1910 = transactions_pb2.Output(name=name1184, relation_id=relation_id1185)
        result1187 = _t1910
        self.record_span(span_start1186, "Output")
        return result1187

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1190 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t1911 = self.parse_name()
        name1188 = _t1911
        _t1912 = self.parse_epoch()
        epoch1189 = _t1912
        self.consume_literal(")")
        _t1913 = transactions_pb2.WhatIf(branch=name1188, epoch=epoch1189)
        result1191 = _t1913
        self.record_span(span_start1190, "WhatIf")
        return result1191

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1194 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t1915 = self.parse_name()
            _t1914 = _t1915
        else:
            _t1914 = None
        name1192 = _t1914
        _t1916 = self.parse_relation_id()
        relation_id1193 = _t1916
        self.consume_literal(")")
        _t1917 = transactions_pb2.Abort(name=(name1192 if name1192 is not None else "abort"), relation_id=relation_id1193)
        result1195 = _t1917
        self.record_span(span_start1194, "Abort")
        return result1195

    def parse_export(self) -> transactions_pb2.Export:
        span_start1199 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t1919 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t1920 = 0
                else:
                    _t1920 = -1
                _t1919 = _t1920
            _t1918 = _t1919
        else:
            _t1918 = -1
        prediction1196 = _t1918
        if prediction1196 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t1922 = self.parse_export_iceberg_config()
            export_iceberg_config1198 = _t1922
            self.consume_literal(")")
            _t1923 = transactions_pb2.Export(iceberg_config=export_iceberg_config1198)
            _t1921 = _t1923
        else:
            if prediction1196 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t1925 = self.parse_export_csv_config()
                export_csv_config1197 = _t1925
                self.consume_literal(")")
                _t1926 = transactions_pb2.Export(csv_config=export_csv_config1197)
                _t1924 = _t1926
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1921 = _t1924
        result1200 = _t1921
        self.record_span(span_start1199, "Export")
        return result1200

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1208 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t1928 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t1929 = 1
                else:
                    _t1929 = -1
                _t1928 = _t1929
            _t1927 = _t1928
        else:
            _t1927 = -1
        prediction1201 = _t1927
        if prediction1201 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t1931 = self.parse_export_csv_path()
            export_csv_path1205 = _t1931
            _t1932 = self.parse_export_csv_columns_list()
            export_csv_columns_list1206 = _t1932
            _t1933 = self.parse_config_dict()
            config_dict1207 = _t1933
            self.consume_literal(")")
            _t1934 = self.construct_export_csv_config(export_csv_path1205, export_csv_columns_list1206, config_dict1207)
            _t1930 = _t1934
        else:
            if prediction1201 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t1936 = self.parse_export_csv_path()
                export_csv_path1202 = _t1936
                _t1937 = self.parse_export_csv_source()
                export_csv_source1203 = _t1937
                _t1938 = self.parse_csv_config()
                csv_config1204 = _t1938
                self.consume_literal(")")
                _t1939 = self.construct_export_csv_config_with_source(export_csv_path1202, export_csv_source1203, csv_config1204)
                _t1935 = _t1939
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1930 = _t1935
        result1209 = _t1930
        self.record_span(span_start1208, "ExportCSVConfig")
        return result1209

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1210 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1210

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1217 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t1941 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t1942 = 0
                else:
                    _t1942 = -1
                _t1941 = _t1942
            _t1940 = _t1941
        else:
            _t1940 = -1
        prediction1211 = _t1940
        if prediction1211 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t1944 = self.parse_relation_id()
            relation_id1216 = _t1944
            self.consume_literal(")")
            _t1945 = transactions_pb2.ExportCSVSource(table_def=relation_id1216)
            _t1943 = _t1945
        else:
            if prediction1211 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1212 = []
                cond1213 = self.match_lookahead_literal("(", 0)
                while cond1213:
                    _t1947 = self.parse_export_csv_column()
                    item1214 = _t1947
                    xs1212.append(item1214)
                    cond1213 = self.match_lookahead_literal("(", 0)
                export_csv_columns1215 = xs1212
                self.consume_literal(")")
                _t1948 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1215)
                _t1949 = transactions_pb2.ExportCSVSource(gnf_columns=_t1948)
                _t1946 = _t1949
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1943 = _t1946
        result1218 = _t1943
        self.record_span(span_start1217, "ExportCSVSource")
        return result1218

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1221 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1219 = self.consume_terminal("STRING")
        _t1950 = self.parse_relation_id()
        relation_id1220 = _t1950
        self.consume_literal(")")
        _t1951 = transactions_pb2.ExportCSVColumn(column_name=string1219, column_data=relation_id1220)
        result1222 = _t1951
        self.record_span(span_start1221, "ExportCSVColumn")
        return result1222

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1223 = []
        cond1224 = self.match_lookahead_literal("(", 0)
        while cond1224:
            _t1952 = self.parse_export_csv_column()
            item1225 = _t1952
            xs1223.append(item1225)
            cond1224 = self.match_lookahead_literal("(", 0)
        export_csv_columns1226 = xs1223
        self.consume_literal(")")
        return export_csv_columns1226

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1236 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1227 = self.consume_terminal("STRING")
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1228 = []
        cond1229 = self.match_lookahead_terminal("STRING", 0)
        while cond1229:
            item1230 = self.consume_terminal("STRING")
            xs1228.append(item1230)
            cond1229 = self.match_lookahead_terminal("STRING", 0)
        strings1231 = xs1228
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("table_name")
        string_121232 = self.consume_terminal("STRING")
        self.consume_literal(")")
        _t1953 = self.parse_export_iceberg_catalog_properties()
        export_iceberg_catalog_properties1233 = _t1953
        self.consume_literal("(")
        self.consume_literal("schema")
        string_171234 = self.consume_terminal("STRING")
        self.consume_literal(")")
        if self.match_lookahead_literal("{", 0):
            _t1955 = self.parse_config_dict()
            _t1954 = _t1955
        else:
            _t1954 = None
        config_dict1235 = _t1954
        self.consume_literal(")")
        _t1956 = self.construct_export_iceberg_config_from_optional(string1227, strings1231, string_121232, export_iceberg_catalog_properties1233, string_171234, config_dict1235)
        result1237 = _t1956
        self.record_span(span_start1236, "ExportIcebergConfig")
        return result1237

    def parse_export_iceberg_catalog_properties(self) -> transactions_pb2.IcebergCatalogProperties:
        span_start1240 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("catalog_properties")
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string1238 = self.consume_terminal("STRING")
        self.consume_literal(")")
        if self.match_lookahead_literal("{", 0):
            _t1958 = self.parse_config_dict()
            _t1957 = _t1958
        else:
            _t1957 = None
        config_dict1239 = _t1957
        self.consume_literal(")")
        _t1959 = self.construct_iceberg_catalog_properties_from_optional(string1238, config_dict1239)
        result1241 = _t1959
        self.record_span(span_start1240, "IcebergCatalogProperties")
        return result1241


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
