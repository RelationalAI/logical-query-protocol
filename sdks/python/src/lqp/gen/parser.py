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
    """Source span from start to end location."""

    __slots__ = ("start", "end")

    def __init__(self, start: Location, end: Location):
        self.start = start
        self.end = end

    def __repr__(self) -> str:
        return f"Span({self.start}, {self.end})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Span):
            return NotImplemented
        return self.start == other.start and self.end == other.end

    def __hash__(self) -> int:
        return hash((self.start, self.end))


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
    ("FLOAT", re.compile(r"([-]?\d+\.\d+|inf|nan)"), lambda x: Lexer.scan_float(x)),
    ("INT", re.compile(r"[-]?\d+"), lambda x: Lexer.scan_int(x)),
    ("INT128", re.compile(r"[-]?\d+i128"), lambda x: Lexer.scan_int128(x)),
    ("STRING", re.compile(r'"(?:[^"\\]|\\.)*"'), lambda x: Lexer.scan_string(x)),
    ("SYMBOL", re.compile(r"[a-zA-Z_][a-zA-Z0-9_.-]*"), lambda x: Lexer.scan_symbol(x)),
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
        self.provenance: dict[tuple[int, ...], Span] = {}
        self._path: list[int] = []
        self._line_starts = _compute_line_starts(input_str)

    def _make_location(self, offset: int) -> Location:
        """Convert byte offset to Location with 1-based line/column."""
        line_idx = bisect.bisect_right(self._line_starts, offset) - 1
        col = offset - self._line_starts[line_idx]
        return Location(line_idx + 1, col + 1, offset)

    def push_path(self, n: int) -> None:
        """Push a field number onto the provenance path."""
        self._path.append(n)

    def pop_path(self) -> None:
        """Pop from the provenance path."""
        self._path.pop()

    def span_start(self) -> int:
        """Return the start offset of the current token."""
        return self.lookahead(0).start_pos

    def record_span(self, start_offset: int) -> None:
        """Record a span from start_offset to the previous token's end."""
        if self.pos > 0:
            end_offset = self.tokens[self.pos - 1].end_pos
        else:
            end_offset = start_offset
        span = Span(self._make_location(start_offset), self._make_location(end_offset))
        self.provenance[tuple(self._path)] = span

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
        id_low = int(hashlib.sha256(name.encode()).hexdigest()[:16], 16)
        id_high = 0
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
            _t1835 = value.HasField("int_value")
        else:
            _t1835 = False
        if _t1835:
            assert value is not None
            return int(value.int_value)
        else:
            _t1836 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t1837 = value.HasField("int_value")
        else:
            _t1837 = False
        if _t1837:
            assert value is not None
            return value.int_value
        else:
            _t1838 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t1839 = value.HasField("string_value")
        else:
            _t1839 = False
        if _t1839:
            assert value is not None
            return value.string_value
        else:
            _t1840 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t1841 = value.HasField("boolean_value")
        else:
            _t1841 = False
        if _t1841:
            assert value is not None
            return value.boolean_value
        else:
            _t1842 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t1843 = value.HasField("string_value")
        else:
            _t1843 = False
        if _t1843:
            assert value is not None
            return [value.string_value]
        else:
            _t1844 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t1845 = value.HasField("int_value")
        else:
            _t1845 = False
        if _t1845:
            assert value is not None
            return value.int_value
        else:
            _t1846 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t1847 = value.HasField("float_value")
        else:
            _t1847 = False
        if _t1847:
            assert value is not None
            return value.float_value
        else:
            _t1848 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t1849 = value.HasField("string_value")
        else:
            _t1849 = False
        if _t1849:
            assert value is not None
            return value.string_value.encode()
        else:
            _t1850 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t1851 = value.HasField("uint128_value")
        else:
            _t1851 = False
        if _t1851:
            assert value is not None
            return value.uint128_value
        else:
            _t1852 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1853 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t1853
        _t1854 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t1854
        _t1855 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t1855
        _t1856 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t1856
        _t1857 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t1857
        _t1858 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t1858
        _t1859 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t1859
        _t1860 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t1860
        _t1861 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t1861
        _t1862 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t1862
        _t1863 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t1863
        _t1864 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t1864

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1865 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t1865
        _t1866 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t1866
        _t1867 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t1867
        _t1868 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t1868
        _t1869 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1869
        _t1870 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t1870
        _t1871 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t1871
        _t1872 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t1872
        _t1873 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t1873
        _t1874 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1874
        _t1875 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1875

    def default_configure(self) -> transactions_pb2.Configure:
        _t1876 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1876
        _t1877 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1877

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
        _t1878 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1878
        _t1879 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t1879
        _t1880 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1880

    def export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1881 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t1881
        _t1882 = self._extract_value_string(config.get("compression"), "")
        compression = _t1882
        _t1883 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t1883
        _t1884 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t1884
        _t1885 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t1885
        _t1886 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t1886
        _t1887 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t1887
        _t1888 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1888

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start602 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        self.push_path(2)
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1237 = self.parse_configure()
            _t1236 = _t1237
        else:
            _t1236 = None
        configure592 = _t1236
        self.pop_path()
        self.push_path(3)
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1239 = self.parse_sync()
            _t1238 = _t1239
        else:
            _t1238 = None
        sync593 = _t1238
        self.pop_path()
        self.push_path(1)
        xs598 = []
        cond599 = self.match_lookahead_literal("(", 0)
        idx600 = 0
        while cond599:
            self.push_path(idx600)
            _t1240 = self.parse_epoch()
            item601 = _t1240
            self.pop_path()
            xs598.append(item601)
            idx600 = (idx600 + 1)
            cond599 = self.match_lookahead_literal("(", 0)
        epochs597 = xs598
        self.pop_path()
        self.consume_literal(")")
        _t1241 = self.default_configure()
        _t1242 = transactions_pb2.Transaction(epochs=epochs597, configure=(configure592 if configure592 is not None else _t1241), sync=sync593)
        result603 = _t1242
        self.record_span(span_start602)
        return result603

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start605 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1243 = self.parse_config_dict()
        config_dict604 = _t1243
        self.consume_literal(")")
        _t1244 = self.construct_configure(config_dict604)
        result606 = _t1244
        self.record_span(span_start605)
        return result606

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        span_start611 = self.span_start()
        self.consume_literal("{")
        xs607 = []
        cond608 = self.match_lookahead_literal(":", 0)
        while cond608:
            _t1245 = self.parse_config_key_value()
            item609 = _t1245
            xs607.append(item609)
            cond608 = self.match_lookahead_literal(":", 0)
        config_key_values610 = xs607
        self.consume_literal("}")
        result612 = config_key_values610
        self.record_span(span_start611)
        return result612

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        span_start615 = self.span_start()
        self.consume_literal(":")
        symbol613 = self.consume_terminal("SYMBOL")
        _t1246 = self.parse_value()
        value614 = _t1246
        result616 = (symbol613, value614,)
        self.record_span(span_start615)
        return result616

    def parse_value(self) -> logic_pb2.Value:
        span_start627 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1247 = 9
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1248 = 8
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1249 = 9
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1251 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1252 = 0
                            else:
                                _t1252 = -1
                            _t1251 = _t1252
                        _t1250 = _t1251
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t1253 = 5
                        else:
                            if self.match_lookahead_terminal("STRING", 0):
                                _t1254 = 2
                            else:
                                if self.match_lookahead_terminal("INT128", 0):
                                    _t1255 = 6
                                else:
                                    if self.match_lookahead_terminal("INT", 0):
                                        _t1256 = 3
                                    else:
                                        if self.match_lookahead_terminal("FLOAT", 0):
                                            _t1257 = 4
                                        else:
                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                _t1258 = 7
                                            else:
                                                _t1258 = -1
                                            _t1257 = _t1258
                                        _t1256 = _t1257
                                    _t1255 = _t1256
                                _t1254 = _t1255
                            _t1253 = _t1254
                        _t1250 = _t1253
                    _t1249 = _t1250
                _t1248 = _t1249
            _t1247 = _t1248
        prediction617 = _t1247
        if prediction617 == 9:
            _t1260 = self.parse_boolean_value()
            boolean_value626 = _t1260
            _t1261 = logic_pb2.Value(boolean_value=boolean_value626)
            _t1259 = _t1261
        else:
            if prediction617 == 8:
                self.consume_literal("missing")
                _t1263 = logic_pb2.MissingValue()
                _t1264 = logic_pb2.Value(missing_value=_t1263)
                _t1262 = _t1264
            else:
                if prediction617 == 7:
                    decimal625 = self.consume_terminal("DECIMAL")
                    _t1266 = logic_pb2.Value(decimal_value=decimal625)
                    _t1265 = _t1266
                else:
                    if prediction617 == 6:
                        int128624 = self.consume_terminal("INT128")
                        _t1268 = logic_pb2.Value(int128_value=int128624)
                        _t1267 = _t1268
                    else:
                        if prediction617 == 5:
                            uint128623 = self.consume_terminal("UINT128")
                            _t1270 = logic_pb2.Value(uint128_value=uint128623)
                            _t1269 = _t1270
                        else:
                            if prediction617 == 4:
                                float622 = self.consume_terminal("FLOAT")
                                _t1272 = logic_pb2.Value(float_value=float622)
                                _t1271 = _t1272
                            else:
                                if prediction617 == 3:
                                    int621 = self.consume_terminal("INT")
                                    _t1274 = logic_pb2.Value(int_value=int621)
                                    _t1273 = _t1274
                                else:
                                    if prediction617 == 2:
                                        string620 = self.consume_terminal("STRING")
                                        _t1276 = logic_pb2.Value(string_value=string620)
                                        _t1275 = _t1276
                                    else:
                                        if prediction617 == 1:
                                            _t1278 = self.parse_datetime()
                                            datetime619 = _t1278
                                            _t1279 = logic_pb2.Value(datetime_value=datetime619)
                                            _t1277 = _t1279
                                        else:
                                            if prediction617 == 0:
                                                _t1281 = self.parse_date()
                                                date618 = _t1281
                                                _t1282 = logic_pb2.Value(date_value=date618)
                                                _t1280 = _t1282
                                            else:
                                                raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1277 = _t1280
                                        _t1275 = _t1277
                                    _t1273 = _t1275
                                _t1271 = _t1273
                            _t1269 = _t1271
                        _t1267 = _t1269
                    _t1265 = _t1267
                _t1262 = _t1265
            _t1259 = _t1262
        result628 = _t1259
        self.record_span(span_start627)
        return result628

    def parse_date(self) -> logic_pb2.DateValue:
        span_start632 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        self.push_path(1)
        int629 = self.consume_terminal("INT")
        self.pop_path()
        self.push_path(2)
        int_3630 = self.consume_terminal("INT")
        self.pop_path()
        self.push_path(3)
        int_4631 = self.consume_terminal("INT")
        self.pop_path()
        self.consume_literal(")")
        _t1283 = logic_pb2.DateValue(year=int(int629), month=int(int_3630), day=int(int_4631))
        result633 = _t1283
        self.record_span(span_start632)
        return result633

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start641 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        self.push_path(1)
        int634 = self.consume_terminal("INT")
        self.pop_path()
        self.push_path(2)
        int_3635 = self.consume_terminal("INT")
        self.pop_path()
        self.push_path(3)
        int_4636 = self.consume_terminal("INT")
        self.pop_path()
        self.push_path(4)
        int_5637 = self.consume_terminal("INT")
        self.pop_path()
        self.push_path(5)
        int_6638 = self.consume_terminal("INT")
        self.pop_path()
        self.push_path(6)
        int_7639 = self.consume_terminal("INT")
        self.pop_path()
        self.push_path(7)
        if self.match_lookahead_terminal("INT", 0):
            _t1284 = self.consume_terminal("INT")
        else:
            _t1284 = None
        int_8640 = _t1284
        self.pop_path()
        self.consume_literal(")")
        _t1285 = logic_pb2.DateTimeValue(year=int(int634), month=int(int_3635), day=int(int_4636), hour=int(int_5637), minute=int(int_6638), second=int(int_7639), microsecond=int((int_8640 if int_8640 is not None else 0)))
        result642 = _t1285
        self.record_span(span_start641)
        return result642

    def parse_boolean_value(self) -> bool:
        span_start644 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1286 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1287 = 1
            else:
                _t1287 = -1
            _t1286 = _t1287
        prediction643 = _t1286
        if prediction643 == 1:
            self.consume_literal("false")
            _t1288 = False
        else:
            if prediction643 == 0:
                self.consume_literal("true")
                _t1289 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1288 = _t1289
        result645 = _t1288
        self.record_span(span_start644)
        return result645

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start654 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        self.push_path(1)
        xs650 = []
        cond651 = self.match_lookahead_literal(":", 0)
        idx652 = 0
        while cond651:
            self.push_path(idx652)
            _t1290 = self.parse_fragment_id()
            item653 = _t1290
            self.pop_path()
            xs650.append(item653)
            idx652 = (idx652 + 1)
            cond651 = self.match_lookahead_literal(":", 0)
        fragment_ids649 = xs650
        self.pop_path()
        self.consume_literal(")")
        _t1291 = transactions_pb2.Sync(fragments=fragment_ids649)
        result655 = _t1291
        self.record_span(span_start654)
        return result655

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start657 = self.span_start()
        self.consume_literal(":")
        symbol656 = self.consume_terminal("SYMBOL")
        result658 = fragments_pb2.FragmentId(id=symbol656.encode())
        self.record_span(span_start657)
        return result658

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start661 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        self.push_path(1)
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1293 = self.parse_epoch_writes()
            _t1292 = _t1293
        else:
            _t1292 = None
        epoch_writes659 = _t1292
        self.pop_path()
        self.push_path(2)
        if self.match_lookahead_literal("(", 0):
            _t1295 = self.parse_epoch_reads()
            _t1294 = _t1295
        else:
            _t1294 = None
        epoch_reads660 = _t1294
        self.pop_path()
        self.consume_literal(")")
        _t1296 = transactions_pb2.Epoch(writes=(epoch_writes659 if epoch_writes659 is not None else []), reads=(epoch_reads660 if epoch_reads660 is not None else []))
        result662 = _t1296
        self.record_span(span_start661)
        return result662

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        span_start667 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("writes")
        xs663 = []
        cond664 = self.match_lookahead_literal("(", 0)
        while cond664:
            _t1297 = self.parse_write()
            item665 = _t1297
            xs663.append(item665)
            cond664 = self.match_lookahead_literal("(", 0)
        writes666 = xs663
        self.consume_literal(")")
        result668 = writes666
        self.record_span(span_start667)
        return result668

    def parse_write(self) -> transactions_pb2.Write:
        span_start674 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1299 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1300 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1301 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1302 = 2
                        else:
                            _t1302 = -1
                        _t1301 = _t1302
                    _t1300 = _t1301
                _t1299 = _t1300
            _t1298 = _t1299
        else:
            _t1298 = -1
        prediction669 = _t1298
        if prediction669 == 3:
            _t1304 = self.parse_snapshot()
            snapshot673 = _t1304
            _t1305 = transactions_pb2.Write(snapshot=snapshot673)
            _t1303 = _t1305
        else:
            if prediction669 == 2:
                _t1307 = self.parse_context()
                context672 = _t1307
                _t1308 = transactions_pb2.Write(context=context672)
                _t1306 = _t1308
            else:
                if prediction669 == 1:
                    _t1310 = self.parse_undefine()
                    undefine671 = _t1310
                    _t1311 = transactions_pb2.Write(undefine=undefine671)
                    _t1309 = _t1311
                else:
                    if prediction669 == 0:
                        _t1313 = self.parse_define()
                        define670 = _t1313
                        _t1314 = transactions_pb2.Write(define=define670)
                        _t1312 = _t1314
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1309 = _t1312
                _t1306 = _t1309
            _t1303 = _t1306
        result675 = _t1303
        self.record_span(span_start674)
        return result675

    def parse_define(self) -> transactions_pb2.Define:
        span_start677 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        self.push_path(1)
        _t1315 = self.parse_fragment()
        fragment676 = _t1315
        self.pop_path()
        self.consume_literal(")")
        _t1316 = transactions_pb2.Define(fragment=fragment676)
        result678 = _t1316
        self.record_span(span_start677)
        return result678

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start684 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1317 = self.parse_new_fragment_id()
        new_fragment_id679 = _t1317
        xs680 = []
        cond681 = self.match_lookahead_literal("(", 0)
        while cond681:
            _t1318 = self.parse_declaration()
            item682 = _t1318
            xs680.append(item682)
            cond681 = self.match_lookahead_literal("(", 0)
        declarations683 = xs680
        self.consume_literal(")")
        result685 = self.construct_fragment(new_fragment_id679, declarations683)
        self.record_span(span_start684)
        return result685

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start687 = self.span_start()
        _t1319 = self.parse_fragment_id()
        fragment_id686 = _t1319
        self.start_fragment(fragment_id686)
        result688 = fragment_id686
        self.record_span(span_start687)
        return result688

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start694 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("rel_edb", 1):
                _t1321 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1322 = 2
                else:
                    if self.match_lookahead_literal("def", 1):
                        _t1323 = 0
                    else:
                        if self.match_lookahead_literal("csv_data", 1):
                            _t1324 = 3
                        else:
                            if self.match_lookahead_literal("betree_relation", 1):
                                _t1325 = 3
                            else:
                                if self.match_lookahead_literal("algorithm", 1):
                                    _t1326 = 1
                                else:
                                    _t1326 = -1
                                _t1325 = _t1326
                            _t1324 = _t1325
                        _t1323 = _t1324
                    _t1322 = _t1323
                _t1321 = _t1322
            _t1320 = _t1321
        else:
            _t1320 = -1
        prediction689 = _t1320
        if prediction689 == 3:
            _t1328 = self.parse_data()
            data693 = _t1328
            _t1329 = logic_pb2.Declaration(data=data693)
            _t1327 = _t1329
        else:
            if prediction689 == 2:
                _t1331 = self.parse_constraint()
                constraint692 = _t1331
                _t1332 = logic_pb2.Declaration(constraint=constraint692)
                _t1330 = _t1332
            else:
                if prediction689 == 1:
                    _t1334 = self.parse_algorithm()
                    algorithm691 = _t1334
                    _t1335 = logic_pb2.Declaration(algorithm=algorithm691)
                    _t1333 = _t1335
                else:
                    if prediction689 == 0:
                        _t1337 = self.parse_def()
                        def690 = _t1337
                        _t1338 = logic_pb2.Declaration()
                        getattr(_t1338, 'def').CopyFrom(def690)
                        _t1336 = _t1338
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1333 = _t1336
                _t1330 = _t1333
            _t1327 = _t1330
        result695 = _t1327
        self.record_span(span_start694)
        return result695

    def parse_def(self) -> logic_pb2.Def:
        span_start699 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        self.push_path(1)
        _t1339 = self.parse_relation_id()
        relation_id696 = _t1339
        self.pop_path()
        self.push_path(2)
        _t1340 = self.parse_abstraction()
        abstraction697 = _t1340
        self.pop_path()
        self.push_path(3)
        if self.match_lookahead_literal("(", 0):
            _t1342 = self.parse_attrs()
            _t1341 = _t1342
        else:
            _t1341 = None
        attrs698 = _t1341
        self.pop_path()
        self.consume_literal(")")
        _t1343 = logic_pb2.Def(name=relation_id696, body=abstraction697, attrs=(attrs698 if attrs698 is not None else []))
        result700 = _t1343
        self.record_span(span_start699)
        return result700

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start704 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1344 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1345 = 1
            else:
                _t1345 = -1
            _t1344 = _t1345
        prediction701 = _t1344
        if prediction701 == 1:
            uint128703 = self.consume_terminal("UINT128")
            _t1346 = logic_pb2.RelationId(id_low=uint128703.low, id_high=uint128703.high)
        else:
            if prediction701 == 0:
                self.consume_literal(":")
                symbol702 = self.consume_terminal("SYMBOL")
                _t1347 = self.relation_id_from_string(symbol702)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1346 = _t1347
        result705 = _t1346
        self.record_span(span_start704)
        return result705

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start708 = self.span_start()
        self.consume_literal("(")
        _t1348 = self.parse_bindings()
        bindings706 = _t1348
        self.push_path(2)
        _t1349 = self.parse_formula()
        formula707 = _t1349
        self.pop_path()
        self.consume_literal(")")
        _t1350 = logic_pb2.Abstraction(vars=(list(bindings706[0]) + list(bindings706[1] if bindings706[1] is not None else [])), value=formula707)
        result709 = _t1350
        self.record_span(span_start708)
        return result709

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        span_start715 = self.span_start()
        self.consume_literal("[")
        xs710 = []
        cond711 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond711:
            _t1351 = self.parse_binding()
            item712 = _t1351
            xs710.append(item712)
            cond711 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings713 = xs710
        if self.match_lookahead_literal("|", 0):
            _t1353 = self.parse_value_bindings()
            _t1352 = _t1353
        else:
            _t1352 = None
        value_bindings714 = _t1352
        self.consume_literal("]")
        result716 = (bindings713, (value_bindings714 if value_bindings714 is not None else []),)
        self.record_span(span_start715)
        return result716

    def parse_binding(self) -> logic_pb2.Binding:
        span_start719 = self.span_start()
        symbol717 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        self.push_path(2)
        _t1354 = self.parse_type()
        type718 = _t1354
        self.pop_path()
        _t1355 = logic_pb2.Var(name=symbol717)
        _t1356 = logic_pb2.Binding(var=_t1355, type=type718)
        result720 = _t1356
        self.record_span(span_start719)
        return result720

    def parse_type(self) -> logic_pb2.Type:
        span_start733 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1357 = 0
        else:
            if self.match_lookahead_literal("UINT128", 0):
                _t1358 = 4
            else:
                if self.match_lookahead_literal("STRING", 0):
                    _t1359 = 1
                else:
                    if self.match_lookahead_literal("MISSING", 0):
                        _t1360 = 8
                    else:
                        if self.match_lookahead_literal("INT128", 0):
                            _t1361 = 5
                        else:
                            if self.match_lookahead_literal("INT", 0):
                                _t1362 = 2
                            else:
                                if self.match_lookahead_literal("FLOAT", 0):
                                    _t1363 = 3
                                else:
                                    if self.match_lookahead_literal("DATETIME", 0):
                                        _t1364 = 7
                                    else:
                                        if self.match_lookahead_literal("DATE", 0):
                                            _t1365 = 6
                                        else:
                                            if self.match_lookahead_literal("BOOLEAN", 0):
                                                _t1366 = 10
                                            else:
                                                if self.match_lookahead_literal("(", 0):
                                                    _t1367 = 9
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
                _t1358 = _t1359
            _t1357 = _t1358
        prediction721 = _t1357
        if prediction721 == 10:
            _t1369 = self.parse_boolean_type()
            boolean_type732 = _t1369
            _t1370 = logic_pb2.Type(boolean_type=boolean_type732)
            _t1368 = _t1370
        else:
            if prediction721 == 9:
                _t1372 = self.parse_decimal_type()
                decimal_type731 = _t1372
                _t1373 = logic_pb2.Type(decimal_type=decimal_type731)
                _t1371 = _t1373
            else:
                if prediction721 == 8:
                    _t1375 = self.parse_missing_type()
                    missing_type730 = _t1375
                    _t1376 = logic_pb2.Type(missing_type=missing_type730)
                    _t1374 = _t1376
                else:
                    if prediction721 == 7:
                        _t1378 = self.parse_datetime_type()
                        datetime_type729 = _t1378
                        _t1379 = logic_pb2.Type(datetime_type=datetime_type729)
                        _t1377 = _t1379
                    else:
                        if prediction721 == 6:
                            _t1381 = self.parse_date_type()
                            date_type728 = _t1381
                            _t1382 = logic_pb2.Type(date_type=date_type728)
                            _t1380 = _t1382
                        else:
                            if prediction721 == 5:
                                _t1384 = self.parse_int128_type()
                                int128_type727 = _t1384
                                _t1385 = logic_pb2.Type(int128_type=int128_type727)
                                _t1383 = _t1385
                            else:
                                if prediction721 == 4:
                                    _t1387 = self.parse_uint128_type()
                                    uint128_type726 = _t1387
                                    _t1388 = logic_pb2.Type(uint128_type=uint128_type726)
                                    _t1386 = _t1388
                                else:
                                    if prediction721 == 3:
                                        _t1390 = self.parse_float_type()
                                        float_type725 = _t1390
                                        _t1391 = logic_pb2.Type(float_type=float_type725)
                                        _t1389 = _t1391
                                    else:
                                        if prediction721 == 2:
                                            _t1393 = self.parse_int_type()
                                            int_type724 = _t1393
                                            _t1394 = logic_pb2.Type(int_type=int_type724)
                                            _t1392 = _t1394
                                        else:
                                            if prediction721 == 1:
                                                _t1396 = self.parse_string_type()
                                                string_type723 = _t1396
                                                _t1397 = logic_pb2.Type(string_type=string_type723)
                                                _t1395 = _t1397
                                            else:
                                                if prediction721 == 0:
                                                    _t1399 = self.parse_unspecified_type()
                                                    unspecified_type722 = _t1399
                                                    _t1400 = logic_pb2.Type(unspecified_type=unspecified_type722)
                                                    _t1398 = _t1400
                                                else:
                                                    raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t1395 = _t1398
                                            _t1392 = _t1395
                                        _t1389 = _t1392
                                    _t1386 = _t1389
                                _t1383 = _t1386
                            _t1380 = _t1383
                        _t1377 = _t1380
                    _t1374 = _t1377
                _t1371 = _t1374
            _t1368 = _t1371
        result734 = _t1368
        self.record_span(span_start733)
        return result734

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start735 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1401 = logic_pb2.UnspecifiedType()
        result736 = _t1401
        self.record_span(span_start735)
        return result736

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start737 = self.span_start()
        self.consume_literal("STRING")
        _t1402 = logic_pb2.StringType()
        result738 = _t1402
        self.record_span(span_start737)
        return result738

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start739 = self.span_start()
        self.consume_literal("INT")
        _t1403 = logic_pb2.IntType()
        result740 = _t1403
        self.record_span(span_start739)
        return result740

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start741 = self.span_start()
        self.consume_literal("FLOAT")
        _t1404 = logic_pb2.FloatType()
        result742 = _t1404
        self.record_span(span_start741)
        return result742

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start743 = self.span_start()
        self.consume_literal("UINT128")
        _t1405 = logic_pb2.UInt128Type()
        result744 = _t1405
        self.record_span(span_start743)
        return result744

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start745 = self.span_start()
        self.consume_literal("INT128")
        _t1406 = logic_pb2.Int128Type()
        result746 = _t1406
        self.record_span(span_start745)
        return result746

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start747 = self.span_start()
        self.consume_literal("DATE")
        _t1407 = logic_pb2.DateType()
        result748 = _t1407
        self.record_span(span_start747)
        return result748

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start749 = self.span_start()
        self.consume_literal("DATETIME")
        _t1408 = logic_pb2.DateTimeType()
        result750 = _t1408
        self.record_span(span_start749)
        return result750

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start751 = self.span_start()
        self.consume_literal("MISSING")
        _t1409 = logic_pb2.MissingType()
        result752 = _t1409
        self.record_span(span_start751)
        return result752

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start755 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        self.push_path(1)
        int753 = self.consume_terminal("INT")
        self.pop_path()
        self.push_path(2)
        int_3754 = self.consume_terminal("INT")
        self.pop_path()
        self.consume_literal(")")
        _t1410 = logic_pb2.DecimalType(precision=int(int753), scale=int(int_3754))
        result756 = _t1410
        self.record_span(span_start755)
        return result756

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start757 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1411 = logic_pb2.BooleanType()
        result758 = _t1411
        self.record_span(span_start757)
        return result758

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        span_start763 = self.span_start()
        self.consume_literal("|")
        xs759 = []
        cond760 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond760:
            _t1412 = self.parse_binding()
            item761 = _t1412
            xs759.append(item761)
            cond760 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings762 = xs759
        result764 = bindings762
        self.record_span(span_start763)
        return result764

    def parse_formula(self) -> logic_pb2.Formula:
        span_start779 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1414 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1415 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1416 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1417 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1418 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1419 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1420 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1421 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1422 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1423 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1424 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1425 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1426 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1427 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1428 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1429 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1430 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1431 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1432 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1433 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1434 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1435 = 10
                                                                                                else:
                                                                                                    _t1435 = -1
                                                                                                _t1434 = _t1435
                                                                                            _t1433 = _t1434
                                                                                        _t1432 = _t1433
                                                                                    _t1431 = _t1432
                                                                                _t1430 = _t1431
                                                                            _t1429 = _t1430
                                                                        _t1428 = _t1429
                                                                    _t1427 = _t1428
                                                                _t1426 = _t1427
                                                            _t1425 = _t1426
                                                        _t1424 = _t1425
                                                    _t1423 = _t1424
                                                _t1422 = _t1423
                                            _t1421 = _t1422
                                        _t1420 = _t1421
                                    _t1419 = _t1420
                                _t1418 = _t1419
                            _t1417 = _t1418
                        _t1416 = _t1417
                    _t1415 = _t1416
                _t1414 = _t1415
            _t1413 = _t1414
        else:
            _t1413 = -1
        prediction765 = _t1413
        if prediction765 == 12:
            _t1437 = self.parse_cast()
            cast778 = _t1437
            _t1438 = logic_pb2.Formula(cast=cast778)
            _t1436 = _t1438
        else:
            if prediction765 == 11:
                _t1440 = self.parse_rel_atom()
                rel_atom777 = _t1440
                _t1441 = logic_pb2.Formula(rel_atom=rel_atom777)
                _t1439 = _t1441
            else:
                if prediction765 == 10:
                    _t1443 = self.parse_primitive()
                    primitive776 = _t1443
                    _t1444 = logic_pb2.Formula(primitive=primitive776)
                    _t1442 = _t1444
                else:
                    if prediction765 == 9:
                        _t1446 = self.parse_pragma()
                        pragma775 = _t1446
                        _t1447 = logic_pb2.Formula(pragma=pragma775)
                        _t1445 = _t1447
                    else:
                        if prediction765 == 8:
                            _t1449 = self.parse_atom()
                            atom774 = _t1449
                            _t1450 = logic_pb2.Formula(atom=atom774)
                            _t1448 = _t1450
                        else:
                            if prediction765 == 7:
                                _t1452 = self.parse_ffi()
                                ffi773 = _t1452
                                _t1453 = logic_pb2.Formula(ffi=ffi773)
                                _t1451 = _t1453
                            else:
                                if prediction765 == 6:
                                    _t1455 = self.parse_not()
                                    not772 = _t1455
                                    _t1456 = logic_pb2.Formula()
                                    getattr(_t1456, 'not').CopyFrom(not772)
                                    _t1454 = _t1456
                                else:
                                    if prediction765 == 5:
                                        _t1458 = self.parse_disjunction()
                                        disjunction771 = _t1458
                                        _t1459 = logic_pb2.Formula(disjunction=disjunction771)
                                        _t1457 = _t1459
                                    else:
                                        if prediction765 == 4:
                                            _t1461 = self.parse_conjunction()
                                            conjunction770 = _t1461
                                            _t1462 = logic_pb2.Formula(conjunction=conjunction770)
                                            _t1460 = _t1462
                                        else:
                                            if prediction765 == 3:
                                                _t1464 = self.parse_reduce()
                                                reduce769 = _t1464
                                                _t1465 = logic_pb2.Formula(reduce=reduce769)
                                                _t1463 = _t1465
                                            else:
                                                if prediction765 == 2:
                                                    _t1467 = self.parse_exists()
                                                    exists768 = _t1467
                                                    _t1468 = logic_pb2.Formula(exists=exists768)
                                                    _t1466 = _t1468
                                                else:
                                                    if prediction765 == 1:
                                                        _t1470 = self.parse_false()
                                                        false767 = _t1470
                                                        _t1471 = logic_pb2.Formula(disjunction=false767)
                                                        _t1469 = _t1471
                                                    else:
                                                        if prediction765 == 0:
                                                            _t1473 = self.parse_true()
                                                            true766 = _t1473
                                                            _t1474 = logic_pb2.Formula(conjunction=true766)
                                                            _t1472 = _t1474
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1469 = _t1472
                                                    _t1466 = _t1469
                                                _t1463 = _t1466
                                            _t1460 = _t1463
                                        _t1457 = _t1460
                                    _t1454 = _t1457
                                _t1451 = _t1454
                            _t1448 = _t1451
                        _t1445 = _t1448
                    _t1442 = _t1445
                _t1439 = _t1442
            _t1436 = _t1439
        result780 = _t1436
        self.record_span(span_start779)
        return result780

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start781 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1475 = logic_pb2.Conjunction(args=[])
        result782 = _t1475
        self.record_span(span_start781)
        return result782

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start783 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1476 = logic_pb2.Disjunction(args=[])
        result784 = _t1476
        self.record_span(span_start783)
        return result784

    def parse_exists(self) -> logic_pb2.Exists:
        span_start787 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1477 = self.parse_bindings()
        bindings785 = _t1477
        _t1478 = self.parse_formula()
        formula786 = _t1478
        self.consume_literal(")")
        _t1479 = logic_pb2.Abstraction(vars=(list(bindings785[0]) + list(bindings785[1] if bindings785[1] is not None else [])), value=formula786)
        _t1480 = logic_pb2.Exists(body=_t1479)
        result788 = _t1480
        self.record_span(span_start787)
        return result788

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start792 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        self.push_path(1)
        _t1481 = self.parse_abstraction()
        abstraction789 = _t1481
        self.pop_path()
        self.push_path(2)
        _t1482 = self.parse_abstraction()
        abstraction_3790 = _t1482
        self.pop_path()
        self.push_path(3)
        _t1483 = self.parse_terms()
        terms791 = _t1483
        self.pop_path()
        self.consume_literal(")")
        _t1484 = logic_pb2.Reduce(op=abstraction789, body=abstraction_3790, terms=terms791)
        result793 = _t1484
        self.record_span(span_start792)
        return result793

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        span_start798 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("terms")
        xs794 = []
        cond795 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond795:
            _t1485 = self.parse_term()
            item796 = _t1485
            xs794.append(item796)
            cond795 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms797 = xs794
        self.consume_literal(")")
        result799 = terms797
        self.record_span(span_start798)
        return result799

    def parse_term(self) -> logic_pb2.Term:
        span_start803 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1486 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1487 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1488 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1489 = 1
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t1490 = 1
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1491 = 0
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1492 = 1
                                else:
                                    if self.match_lookahead_terminal("INT128", 0):
                                        _t1493 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT", 0):
                                            _t1494 = 1
                                        else:
                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                _t1495 = 1
                                            else:
                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                    _t1496 = 1
                                                else:
                                                    _t1496 = -1
                                                _t1495 = _t1496
                                            _t1494 = _t1495
                                        _t1493 = _t1494
                                    _t1492 = _t1493
                                _t1491 = _t1492
                            _t1490 = _t1491
                        _t1489 = _t1490
                    _t1488 = _t1489
                _t1487 = _t1488
            _t1486 = _t1487
        prediction800 = _t1486
        if prediction800 == 1:
            _t1498 = self.parse_constant()
            constant802 = _t1498
            _t1499 = logic_pb2.Term(constant=constant802)
            _t1497 = _t1499
        else:
            if prediction800 == 0:
                _t1501 = self.parse_var()
                var801 = _t1501
                _t1502 = logic_pb2.Term(var=var801)
                _t1500 = _t1502
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1497 = _t1500
        result804 = _t1497
        self.record_span(span_start803)
        return result804

    def parse_var(self) -> logic_pb2.Var:
        span_start806 = self.span_start()
        symbol805 = self.consume_terminal("SYMBOL")
        _t1503 = logic_pb2.Var(name=symbol805)
        result807 = _t1503
        self.record_span(span_start806)
        return result807

    def parse_constant(self) -> logic_pb2.Value:
        span_start809 = self.span_start()
        _t1504 = self.parse_value()
        value808 = _t1504
        result810 = value808
        self.record_span(span_start809)
        return result810

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start819 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        self.push_path(1)
        xs815 = []
        cond816 = self.match_lookahead_literal("(", 0)
        idx817 = 0
        while cond816:
            self.push_path(idx817)
            _t1505 = self.parse_formula()
            item818 = _t1505
            self.pop_path()
            xs815.append(item818)
            idx817 = (idx817 + 1)
            cond816 = self.match_lookahead_literal("(", 0)
        formulas814 = xs815
        self.pop_path()
        self.consume_literal(")")
        _t1506 = logic_pb2.Conjunction(args=formulas814)
        result820 = _t1506
        self.record_span(span_start819)
        return result820

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start829 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.push_path(1)
        xs825 = []
        cond826 = self.match_lookahead_literal("(", 0)
        idx827 = 0
        while cond826:
            self.push_path(idx827)
            _t1507 = self.parse_formula()
            item828 = _t1507
            self.pop_path()
            xs825.append(item828)
            idx827 = (idx827 + 1)
            cond826 = self.match_lookahead_literal("(", 0)
        formulas824 = xs825
        self.pop_path()
        self.consume_literal(")")
        _t1508 = logic_pb2.Disjunction(args=formulas824)
        result830 = _t1508
        self.record_span(span_start829)
        return result830

    def parse_not(self) -> logic_pb2.Not:
        span_start832 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        self.push_path(1)
        _t1509 = self.parse_formula()
        formula831 = _t1509
        self.pop_path()
        self.consume_literal(")")
        _t1510 = logic_pb2.Not(arg=formula831)
        result833 = _t1510
        self.record_span(span_start832)
        return result833

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start837 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        self.push_path(1)
        _t1511 = self.parse_name()
        name834 = _t1511
        self.pop_path()
        self.push_path(2)
        _t1512 = self.parse_ffi_args()
        ffi_args835 = _t1512
        self.pop_path()
        self.push_path(3)
        _t1513 = self.parse_terms()
        terms836 = _t1513
        self.pop_path()
        self.consume_literal(")")
        _t1514 = logic_pb2.FFI(name=name834, args=ffi_args835, terms=terms836)
        result838 = _t1514
        self.record_span(span_start837)
        return result838

    def parse_name(self) -> str:
        span_start840 = self.span_start()
        self.consume_literal(":")
        symbol839 = self.consume_terminal("SYMBOL")
        result841 = symbol839
        self.record_span(span_start840)
        return result841

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        span_start846 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("args")
        xs842 = []
        cond843 = self.match_lookahead_literal("(", 0)
        while cond843:
            _t1515 = self.parse_abstraction()
            item844 = _t1515
            xs842.append(item844)
            cond843 = self.match_lookahead_literal("(", 0)
        abstractions845 = xs842
        self.consume_literal(")")
        result847 = abstractions845
        self.record_span(span_start846)
        return result847

    def parse_atom(self) -> logic_pb2.Atom:
        span_start857 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        self.push_path(1)
        _t1516 = self.parse_relation_id()
        relation_id848 = _t1516
        self.pop_path()
        self.push_path(2)
        xs853 = []
        cond854 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        idx855 = 0
        while cond854:
            self.push_path(idx855)
            _t1517 = self.parse_term()
            item856 = _t1517
            self.pop_path()
            xs853.append(item856)
            idx855 = (idx855 + 1)
            cond854 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms852 = xs853
        self.pop_path()
        self.consume_literal(")")
        _t1518 = logic_pb2.Atom(name=relation_id848, terms=terms852)
        result858 = _t1518
        self.record_span(span_start857)
        return result858

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start868 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        self.push_path(1)
        _t1519 = self.parse_name()
        name859 = _t1519
        self.pop_path()
        self.push_path(2)
        xs864 = []
        cond865 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        idx866 = 0
        while cond865:
            self.push_path(idx866)
            _t1520 = self.parse_term()
            item867 = _t1520
            self.pop_path()
            xs864.append(item867)
            idx866 = (idx866 + 1)
            cond865 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms863 = xs864
        self.pop_path()
        self.consume_literal(")")
        _t1521 = logic_pb2.Pragma(name=name859, terms=terms863)
        result869 = _t1521
        self.record_span(span_start868)
        return result869

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start889 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1523 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1524 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1525 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1526 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1527 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1528 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1529 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1530 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1531 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1532 = 7
                                                else:
                                                    _t1532 = -1
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
        prediction870 = _t1522
        if prediction870 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            self.push_path(1)
            _t1534 = self.parse_name()
            name880 = _t1534
            self.pop_path()
            self.push_path(2)
            xs885 = []
            cond886 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            idx887 = 0
            while cond886:
                self.push_path(idx887)
                _t1535 = self.parse_rel_term()
                item888 = _t1535
                self.pop_path()
                xs885.append(item888)
                idx887 = (idx887 + 1)
                cond886 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            rel_terms884 = xs885
            self.pop_path()
            self.consume_literal(")")
            _t1536 = logic_pb2.Primitive(name=name880, terms=rel_terms884)
            _t1533 = _t1536
        else:
            if prediction870 == 8:
                _t1538 = self.parse_divide()
                divide879 = _t1538
                _t1537 = divide879
            else:
                if prediction870 == 7:
                    _t1540 = self.parse_multiply()
                    multiply878 = _t1540
                    _t1539 = multiply878
                else:
                    if prediction870 == 6:
                        _t1542 = self.parse_minus()
                        minus877 = _t1542
                        _t1541 = minus877
                    else:
                        if prediction870 == 5:
                            _t1544 = self.parse_add()
                            add876 = _t1544
                            _t1543 = add876
                        else:
                            if prediction870 == 4:
                                _t1546 = self.parse_gt_eq()
                                gt_eq875 = _t1546
                                _t1545 = gt_eq875
                            else:
                                if prediction870 == 3:
                                    _t1548 = self.parse_gt()
                                    gt874 = _t1548
                                    _t1547 = gt874
                                else:
                                    if prediction870 == 2:
                                        _t1550 = self.parse_lt_eq()
                                        lt_eq873 = _t1550
                                        _t1549 = lt_eq873
                                    else:
                                        if prediction870 == 1:
                                            _t1552 = self.parse_lt()
                                            lt872 = _t1552
                                            _t1551 = lt872
                                        else:
                                            if prediction870 == 0:
                                                _t1554 = self.parse_eq()
                                                eq871 = _t1554
                                                _t1553 = eq871
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1551 = _t1553
                                        _t1549 = _t1551
                                    _t1547 = _t1549
                                _t1545 = _t1547
                            _t1543 = _t1545
                        _t1541 = _t1543
                    _t1539 = _t1541
                _t1537 = _t1539
            _t1533 = _t1537
        result890 = _t1533
        self.record_span(span_start889)
        return result890

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start893 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1555 = self.parse_term()
        term891 = _t1555
        _t1556 = self.parse_term()
        term_3892 = _t1556
        self.consume_literal(")")
        _t1557 = logic_pb2.RelTerm(term=term891)
        _t1558 = logic_pb2.RelTerm(term=term_3892)
        _t1559 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1557, _t1558])
        result894 = _t1559
        self.record_span(span_start893)
        return result894

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start897 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1560 = self.parse_term()
        term895 = _t1560
        _t1561 = self.parse_term()
        term_3896 = _t1561
        self.consume_literal(")")
        _t1562 = logic_pb2.RelTerm(term=term895)
        _t1563 = logic_pb2.RelTerm(term=term_3896)
        _t1564 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1562, _t1563])
        result898 = _t1564
        self.record_span(span_start897)
        return result898

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start901 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1565 = self.parse_term()
        term899 = _t1565
        _t1566 = self.parse_term()
        term_3900 = _t1566
        self.consume_literal(")")
        _t1567 = logic_pb2.RelTerm(term=term899)
        _t1568 = logic_pb2.RelTerm(term=term_3900)
        _t1569 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1567, _t1568])
        result902 = _t1569
        self.record_span(span_start901)
        return result902

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start905 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1570 = self.parse_term()
        term903 = _t1570
        _t1571 = self.parse_term()
        term_3904 = _t1571
        self.consume_literal(")")
        _t1572 = logic_pb2.RelTerm(term=term903)
        _t1573 = logic_pb2.RelTerm(term=term_3904)
        _t1574 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1572, _t1573])
        result906 = _t1574
        self.record_span(span_start905)
        return result906

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start909 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1575 = self.parse_term()
        term907 = _t1575
        _t1576 = self.parse_term()
        term_3908 = _t1576
        self.consume_literal(")")
        _t1577 = logic_pb2.RelTerm(term=term907)
        _t1578 = logic_pb2.RelTerm(term=term_3908)
        _t1579 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1577, _t1578])
        result910 = _t1579
        self.record_span(span_start909)
        return result910

    def parse_add(self) -> logic_pb2.Primitive:
        span_start914 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1580 = self.parse_term()
        term911 = _t1580
        _t1581 = self.parse_term()
        term_3912 = _t1581
        _t1582 = self.parse_term()
        term_4913 = _t1582
        self.consume_literal(")")
        _t1583 = logic_pb2.RelTerm(term=term911)
        _t1584 = logic_pb2.RelTerm(term=term_3912)
        _t1585 = logic_pb2.RelTerm(term=term_4913)
        _t1586 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1583, _t1584, _t1585])
        result915 = _t1586
        self.record_span(span_start914)
        return result915

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start919 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1587 = self.parse_term()
        term916 = _t1587
        _t1588 = self.parse_term()
        term_3917 = _t1588
        _t1589 = self.parse_term()
        term_4918 = _t1589
        self.consume_literal(")")
        _t1590 = logic_pb2.RelTerm(term=term916)
        _t1591 = logic_pb2.RelTerm(term=term_3917)
        _t1592 = logic_pb2.RelTerm(term=term_4918)
        _t1593 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1590, _t1591, _t1592])
        result920 = _t1593
        self.record_span(span_start919)
        return result920

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start924 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1594 = self.parse_term()
        term921 = _t1594
        _t1595 = self.parse_term()
        term_3922 = _t1595
        _t1596 = self.parse_term()
        term_4923 = _t1596
        self.consume_literal(")")
        _t1597 = logic_pb2.RelTerm(term=term921)
        _t1598 = logic_pb2.RelTerm(term=term_3922)
        _t1599 = logic_pb2.RelTerm(term=term_4923)
        _t1600 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1597, _t1598, _t1599])
        result925 = _t1600
        self.record_span(span_start924)
        return result925

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start929 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1601 = self.parse_term()
        term926 = _t1601
        _t1602 = self.parse_term()
        term_3927 = _t1602
        _t1603 = self.parse_term()
        term_4928 = _t1603
        self.consume_literal(")")
        _t1604 = logic_pb2.RelTerm(term=term926)
        _t1605 = logic_pb2.RelTerm(term=term_3927)
        _t1606 = logic_pb2.RelTerm(term=term_4928)
        _t1607 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1604, _t1605, _t1606])
        result930 = _t1607
        self.record_span(span_start929)
        return result930

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start934 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1608 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1609 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1610 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1611 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1612 = 0
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1613 = 1
                            else:
                                if self.match_lookahead_terminal("SYMBOL", 0):
                                    _t1614 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1615 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1616 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1617 = 1
                                            else:
                                                if self.match_lookahead_terminal("FLOAT", 0):
                                                    _t1618 = 1
                                                else:
                                                    if self.match_lookahead_terminal("DECIMAL", 0):
                                                        _t1619 = 1
                                                    else:
                                                        _t1619 = -1
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
            _t1608 = _t1609
        prediction931 = _t1608
        if prediction931 == 1:
            _t1621 = self.parse_term()
            term933 = _t1621
            _t1622 = logic_pb2.RelTerm(term=term933)
            _t1620 = _t1622
        else:
            if prediction931 == 0:
                _t1624 = self.parse_specialized_value()
                specialized_value932 = _t1624
                _t1625 = logic_pb2.RelTerm(specialized_value=specialized_value932)
                _t1623 = _t1625
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1620 = _t1623
        result935 = _t1620
        self.record_span(span_start934)
        return result935

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start937 = self.span_start()
        self.consume_literal("#")
        _t1626 = self.parse_value()
        value936 = _t1626
        result938 = value936
        self.record_span(span_start937)
        return result938

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start948 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        self.push_path(3)
        _t1627 = self.parse_name()
        name939 = _t1627
        self.pop_path()
        self.push_path(2)
        xs944 = []
        cond945 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        idx946 = 0
        while cond945:
            self.push_path(idx946)
            _t1628 = self.parse_rel_term()
            item947 = _t1628
            self.pop_path()
            xs944.append(item947)
            idx946 = (idx946 + 1)
            cond945 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        rel_terms943 = xs944
        self.pop_path()
        self.consume_literal(")")
        _t1629 = logic_pb2.RelAtom(name=name939, terms=rel_terms943)
        result949 = _t1629
        self.record_span(span_start948)
        return result949

    def parse_cast(self) -> logic_pb2.Cast:
        span_start952 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        self.push_path(2)
        _t1630 = self.parse_term()
        term950 = _t1630
        self.pop_path()
        self.push_path(3)
        _t1631 = self.parse_term()
        term_3951 = _t1631
        self.pop_path()
        self.consume_literal(")")
        _t1632 = logic_pb2.Cast(input=term950, result=term_3951)
        result953 = _t1632
        self.record_span(span_start952)
        return result953

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        span_start958 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs954 = []
        cond955 = self.match_lookahead_literal("(", 0)
        while cond955:
            _t1633 = self.parse_attribute()
            item956 = _t1633
            xs954.append(item956)
            cond955 = self.match_lookahead_literal("(", 0)
        attributes957 = xs954
        self.consume_literal(")")
        result959 = attributes957
        self.record_span(span_start958)
        return result959

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start969 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        self.push_path(1)
        _t1634 = self.parse_name()
        name960 = _t1634
        self.pop_path()
        self.push_path(2)
        xs965 = []
        cond966 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        idx967 = 0
        while cond966:
            self.push_path(idx967)
            _t1635 = self.parse_value()
            item968 = _t1635
            self.pop_path()
            xs965.append(item968)
            idx967 = (idx967 + 1)
            cond966 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        values964 = xs965
        self.pop_path()
        self.consume_literal(")")
        _t1636 = logic_pb2.Attribute(name=name960, args=values964)
        result970 = _t1636
        self.record_span(span_start969)
        return result970

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start980 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        self.push_path(1)
        xs975 = []
        cond976 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        idx977 = 0
        while cond976:
            self.push_path(idx977)
            _t1637 = self.parse_relation_id()
            item978 = _t1637
            self.pop_path()
            xs975.append(item978)
            idx977 = (idx977 + 1)
            cond976 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids974 = xs975
        self.pop_path()
        self.push_path(2)
        _t1638 = self.parse_script()
        script979 = _t1638
        self.pop_path()
        self.consume_literal(")")
        _t1639 = logic_pb2.Algorithm(body=script979)
        getattr(_t1639, 'global').extend(relation_ids974)
        result981 = _t1639
        self.record_span(span_start980)
        return result981

    def parse_script(self) -> logic_pb2.Script:
        span_start990 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        self.push_path(1)
        xs986 = []
        cond987 = self.match_lookahead_literal("(", 0)
        idx988 = 0
        while cond987:
            self.push_path(idx988)
            _t1640 = self.parse_construct()
            item989 = _t1640
            self.pop_path()
            xs986.append(item989)
            idx988 = (idx988 + 1)
            cond987 = self.match_lookahead_literal("(", 0)
        constructs985 = xs986
        self.pop_path()
        self.consume_literal(")")
        _t1641 = logic_pb2.Script(constructs=constructs985)
        result991 = _t1641
        self.record_span(span_start990)
        return result991

    def parse_construct(self) -> logic_pb2.Construct:
        span_start995 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1643 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1644 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1645 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1646 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1647 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1648 = 1
                                else:
                                    _t1648 = -1
                                _t1647 = _t1648
                            _t1646 = _t1647
                        _t1645 = _t1646
                    _t1644 = _t1645
                _t1643 = _t1644
            _t1642 = _t1643
        else:
            _t1642 = -1
        prediction992 = _t1642
        if prediction992 == 1:
            _t1650 = self.parse_instruction()
            instruction994 = _t1650
            _t1651 = logic_pb2.Construct(instruction=instruction994)
            _t1649 = _t1651
        else:
            if prediction992 == 0:
                _t1653 = self.parse_loop()
                loop993 = _t1653
                _t1654 = logic_pb2.Construct(loop=loop993)
                _t1652 = _t1654
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1649 = _t1652
        result996 = _t1649
        self.record_span(span_start995)
        return result996

    def parse_loop(self) -> logic_pb2.Loop:
        span_start999 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        self.push_path(1)
        _t1655 = self.parse_init()
        init997 = _t1655
        self.pop_path()
        self.push_path(2)
        _t1656 = self.parse_script()
        script998 = _t1656
        self.pop_path()
        self.consume_literal(")")
        _t1657 = logic_pb2.Loop(init=init997, body=script998)
        result1000 = _t1657
        self.record_span(span_start999)
        return result1000

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        span_start1005 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("init")
        xs1001 = []
        cond1002 = self.match_lookahead_literal("(", 0)
        while cond1002:
            _t1658 = self.parse_instruction()
            item1003 = _t1658
            xs1001.append(item1003)
            cond1002 = self.match_lookahead_literal("(", 0)
        instructions1004 = xs1001
        self.consume_literal(")")
        result1006 = instructions1004
        self.record_span(span_start1005)
        return result1006

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1013 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1660 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1661 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1662 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1663 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1664 = 0
                            else:
                                _t1664 = -1
                            _t1663 = _t1664
                        _t1662 = _t1663
                    _t1661 = _t1662
                _t1660 = _t1661
            _t1659 = _t1660
        else:
            _t1659 = -1
        prediction1007 = _t1659
        if prediction1007 == 4:
            _t1666 = self.parse_monus_def()
            monus_def1012 = _t1666
            _t1667 = logic_pb2.Instruction(monus_def=monus_def1012)
            _t1665 = _t1667
        else:
            if prediction1007 == 3:
                _t1669 = self.parse_monoid_def()
                monoid_def1011 = _t1669
                _t1670 = logic_pb2.Instruction(monoid_def=monoid_def1011)
                _t1668 = _t1670
            else:
                if prediction1007 == 2:
                    _t1672 = self.parse_break()
                    break1010 = _t1672
                    _t1673 = logic_pb2.Instruction()
                    getattr(_t1673, 'break').CopyFrom(break1010)
                    _t1671 = _t1673
                else:
                    if prediction1007 == 1:
                        _t1675 = self.parse_upsert()
                        upsert1009 = _t1675
                        _t1676 = logic_pb2.Instruction(upsert=upsert1009)
                        _t1674 = _t1676
                    else:
                        if prediction1007 == 0:
                            _t1678 = self.parse_assign()
                            assign1008 = _t1678
                            _t1679 = logic_pb2.Instruction(assign=assign1008)
                            _t1677 = _t1679
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1674 = _t1677
                    _t1671 = _t1674
                _t1668 = _t1671
            _t1665 = _t1668
        result1014 = _t1665
        self.record_span(span_start1013)
        return result1014

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1018 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        self.push_path(1)
        _t1680 = self.parse_relation_id()
        relation_id1015 = _t1680
        self.pop_path()
        self.push_path(2)
        _t1681 = self.parse_abstraction()
        abstraction1016 = _t1681
        self.pop_path()
        self.push_path(3)
        if self.match_lookahead_literal("(", 0):
            _t1683 = self.parse_attrs()
            _t1682 = _t1683
        else:
            _t1682 = None
        attrs1017 = _t1682
        self.pop_path()
        self.consume_literal(")")
        _t1684 = logic_pb2.Assign(name=relation_id1015, body=abstraction1016, attrs=(attrs1017 if attrs1017 is not None else []))
        result1019 = _t1684
        self.record_span(span_start1018)
        return result1019

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1023 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        self.push_path(1)
        _t1685 = self.parse_relation_id()
        relation_id1020 = _t1685
        self.pop_path()
        _t1686 = self.parse_abstraction_with_arity()
        abstraction_with_arity1021 = _t1686
        self.push_path(3)
        if self.match_lookahead_literal("(", 0):
            _t1688 = self.parse_attrs()
            _t1687 = _t1688
        else:
            _t1687 = None
        attrs1022 = _t1687
        self.pop_path()
        self.consume_literal(")")
        _t1689 = logic_pb2.Upsert(name=relation_id1020, body=abstraction_with_arity1021[0], attrs=(attrs1022 if attrs1022 is not None else []), value_arity=abstraction_with_arity1021[1])
        result1024 = _t1689
        self.record_span(span_start1023)
        return result1024

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        span_start1027 = self.span_start()
        self.consume_literal("(")
        _t1690 = self.parse_bindings()
        bindings1025 = _t1690
        _t1691 = self.parse_formula()
        formula1026 = _t1691
        self.consume_literal(")")
        _t1692 = logic_pb2.Abstraction(vars=(list(bindings1025[0]) + list(bindings1025[1] if bindings1025[1] is not None else [])), value=formula1026)
        result1028 = (_t1692, len(bindings1025[1]),)
        self.record_span(span_start1027)
        return result1028

    def parse_break(self) -> logic_pb2.Break:
        span_start1032 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        self.push_path(1)
        _t1693 = self.parse_relation_id()
        relation_id1029 = _t1693
        self.pop_path()
        self.push_path(2)
        _t1694 = self.parse_abstraction()
        abstraction1030 = _t1694
        self.pop_path()
        self.push_path(3)
        if self.match_lookahead_literal("(", 0):
            _t1696 = self.parse_attrs()
            _t1695 = _t1696
        else:
            _t1695 = None
        attrs1031 = _t1695
        self.pop_path()
        self.consume_literal(")")
        _t1697 = logic_pb2.Break(name=relation_id1029, body=abstraction1030, attrs=(attrs1031 if attrs1031 is not None else []))
        result1033 = _t1697
        self.record_span(span_start1032)
        return result1033

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1038 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        self.push_path(1)
        _t1698 = self.parse_monoid()
        monoid1034 = _t1698
        self.pop_path()
        self.push_path(2)
        _t1699 = self.parse_relation_id()
        relation_id1035 = _t1699
        self.pop_path()
        _t1700 = self.parse_abstraction_with_arity()
        abstraction_with_arity1036 = _t1700
        self.push_path(4)
        if self.match_lookahead_literal("(", 0):
            _t1702 = self.parse_attrs()
            _t1701 = _t1702
        else:
            _t1701 = None
        attrs1037 = _t1701
        self.pop_path()
        self.consume_literal(")")
        _t1703 = logic_pb2.MonoidDef(monoid=monoid1034, name=relation_id1035, body=abstraction_with_arity1036[0], attrs=(attrs1037 if attrs1037 is not None else []), value_arity=abstraction_with_arity1036[1])
        result1039 = _t1703
        self.record_span(span_start1038)
        return result1039

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1045 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1705 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1706 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1707 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1708 = 2
                        else:
                            _t1708 = -1
                        _t1707 = _t1708
                    _t1706 = _t1707
                _t1705 = _t1706
            _t1704 = _t1705
        else:
            _t1704 = -1
        prediction1040 = _t1704
        if prediction1040 == 3:
            _t1710 = self.parse_sum_monoid()
            sum_monoid1044 = _t1710
            _t1711 = logic_pb2.Monoid(sum_monoid=sum_monoid1044)
            _t1709 = _t1711
        else:
            if prediction1040 == 2:
                _t1713 = self.parse_max_monoid()
                max_monoid1043 = _t1713
                _t1714 = logic_pb2.Monoid(max_monoid=max_monoid1043)
                _t1712 = _t1714
            else:
                if prediction1040 == 1:
                    _t1716 = self.parse_min_monoid()
                    min_monoid1042 = _t1716
                    _t1717 = logic_pb2.Monoid(min_monoid=min_monoid1042)
                    _t1715 = _t1717
                else:
                    if prediction1040 == 0:
                        _t1719 = self.parse_or_monoid()
                        or_monoid1041 = _t1719
                        _t1720 = logic_pb2.Monoid(or_monoid=or_monoid1041)
                        _t1718 = _t1720
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1715 = _t1718
                _t1712 = _t1715
            _t1709 = _t1712
        result1046 = _t1709
        self.record_span(span_start1045)
        return result1046

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1047 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1721 = logic_pb2.OrMonoid()
        result1048 = _t1721
        self.record_span(span_start1047)
        return result1048

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1050 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        self.push_path(1)
        _t1722 = self.parse_type()
        type1049 = _t1722
        self.pop_path()
        self.consume_literal(")")
        _t1723 = logic_pb2.MinMonoid(type=type1049)
        result1051 = _t1723
        self.record_span(span_start1050)
        return result1051

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1053 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        self.push_path(1)
        _t1724 = self.parse_type()
        type1052 = _t1724
        self.pop_path()
        self.consume_literal(")")
        _t1725 = logic_pb2.MaxMonoid(type=type1052)
        result1054 = _t1725
        self.record_span(span_start1053)
        return result1054

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1056 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        self.push_path(1)
        _t1726 = self.parse_type()
        type1055 = _t1726
        self.pop_path()
        self.consume_literal(")")
        _t1727 = logic_pb2.SumMonoid(type=type1055)
        result1057 = _t1727
        self.record_span(span_start1056)
        return result1057

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1062 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        self.push_path(1)
        _t1728 = self.parse_monoid()
        monoid1058 = _t1728
        self.pop_path()
        self.push_path(2)
        _t1729 = self.parse_relation_id()
        relation_id1059 = _t1729
        self.pop_path()
        _t1730 = self.parse_abstraction_with_arity()
        abstraction_with_arity1060 = _t1730
        self.push_path(4)
        if self.match_lookahead_literal("(", 0):
            _t1732 = self.parse_attrs()
            _t1731 = _t1732
        else:
            _t1731 = None
        attrs1061 = _t1731
        self.pop_path()
        self.consume_literal(")")
        _t1733 = logic_pb2.MonusDef(monoid=monoid1058, name=relation_id1059, body=abstraction_with_arity1060[0], attrs=(attrs1061 if attrs1061 is not None else []), value_arity=abstraction_with_arity1060[1])
        result1063 = _t1733
        self.record_span(span_start1062)
        return result1063

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1068 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        self.push_path(2)
        _t1734 = self.parse_relation_id()
        relation_id1064 = _t1734
        self.pop_path()
        _t1735 = self.parse_abstraction()
        abstraction1065 = _t1735
        _t1736 = self.parse_functional_dependency_keys()
        functional_dependency_keys1066 = _t1736
        _t1737 = self.parse_functional_dependency_values()
        functional_dependency_values1067 = _t1737
        self.consume_literal(")")
        _t1738 = logic_pb2.FunctionalDependency(guard=abstraction1065, keys=functional_dependency_keys1066, values=functional_dependency_values1067)
        _t1739 = logic_pb2.Constraint(name=relation_id1064, functional_dependency=_t1738)
        result1069 = _t1739
        self.record_span(span_start1068)
        return result1069

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        span_start1074 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1070 = []
        cond1071 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1071:
            _t1740 = self.parse_var()
            item1072 = _t1740
            xs1070.append(item1072)
            cond1071 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1073 = xs1070
        self.consume_literal(")")
        result1075 = vars1073
        self.record_span(span_start1074)
        return result1075

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        span_start1080 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("values")
        xs1076 = []
        cond1077 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1077:
            _t1741 = self.parse_var()
            item1078 = _t1741
            xs1076.append(item1078)
            cond1077 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1079 = xs1076
        self.consume_literal(")")
        result1081 = vars1079
        self.record_span(span_start1080)
        return result1081

    def parse_data(self) -> logic_pb2.Data:
        span_start1086 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("rel_edb", 1):
                _t1743 = 0
            else:
                if self.match_lookahead_literal("csv_data", 1):
                    _t1744 = 2
                else:
                    if self.match_lookahead_literal("betree_relation", 1):
                        _t1745 = 1
                    else:
                        _t1745 = -1
                    _t1744 = _t1745
                _t1743 = _t1744
            _t1742 = _t1743
        else:
            _t1742 = -1
        prediction1082 = _t1742
        if prediction1082 == 2:
            _t1747 = self.parse_csv_data()
            csv_data1085 = _t1747
            _t1748 = logic_pb2.Data(csv_data=csv_data1085)
            _t1746 = _t1748
        else:
            if prediction1082 == 1:
                _t1750 = self.parse_betree_relation()
                betree_relation1084 = _t1750
                _t1751 = logic_pb2.Data(betree_relation=betree_relation1084)
                _t1749 = _t1751
            else:
                if prediction1082 == 0:
                    _t1753 = self.parse_rel_edb()
                    rel_edb1083 = _t1753
                    _t1754 = logic_pb2.Data(rel_edb=rel_edb1083)
                    _t1752 = _t1754
                else:
                    raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t1749 = _t1752
            _t1746 = _t1749
        result1087 = _t1746
        self.record_span(span_start1086)
        return result1087

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        span_start1091 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("rel_edb")
        self.push_path(1)
        _t1755 = self.parse_relation_id()
        relation_id1088 = _t1755
        self.pop_path()
        self.push_path(2)
        _t1756 = self.parse_rel_edb_path()
        rel_edb_path1089 = _t1756
        self.pop_path()
        self.push_path(3)
        _t1757 = self.parse_rel_edb_types()
        rel_edb_types1090 = _t1757
        self.pop_path()
        self.consume_literal(")")
        _t1758 = logic_pb2.RelEDB(target_id=relation_id1088, path=rel_edb_path1089, types=rel_edb_types1090)
        result1092 = _t1758
        self.record_span(span_start1091)
        return result1092

    def parse_rel_edb_path(self) -> Sequence[str]:
        span_start1097 = self.span_start()
        self.consume_literal("[")
        xs1093 = []
        cond1094 = self.match_lookahead_terminal("STRING", 0)
        while cond1094:
            item1095 = self.consume_terminal("STRING")
            xs1093.append(item1095)
            cond1094 = self.match_lookahead_terminal("STRING", 0)
        strings1096 = xs1093
        self.consume_literal("]")
        result1098 = strings1096
        self.record_span(span_start1097)
        return result1098

    def parse_rel_edb_types(self) -> Sequence[logic_pb2.Type]:
        span_start1103 = self.span_start()
        self.consume_literal("[")
        xs1099 = []
        cond1100 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1100:
            _t1759 = self.parse_type()
            item1101 = _t1759
            xs1099.append(item1101)
            cond1100 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1102 = xs1099
        self.consume_literal("]")
        result1104 = types1102
        self.record_span(span_start1103)
        return result1104

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1107 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        self.push_path(1)
        _t1760 = self.parse_relation_id()
        relation_id1105 = _t1760
        self.pop_path()
        self.push_path(2)
        _t1761 = self.parse_betree_info()
        betree_info1106 = _t1761
        self.pop_path()
        self.consume_literal(")")
        _t1762 = logic_pb2.BeTreeRelation(name=relation_id1105, relation_info=betree_info1106)
        result1108 = _t1762
        self.record_span(span_start1107)
        return result1108

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1112 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1763 = self.parse_betree_info_key_types()
        betree_info_key_types1109 = _t1763
        _t1764 = self.parse_betree_info_value_types()
        betree_info_value_types1110 = _t1764
        _t1765 = self.parse_config_dict()
        config_dict1111 = _t1765
        self.consume_literal(")")
        _t1766 = self.construct_betree_info(betree_info_key_types1109, betree_info_value_types1110, config_dict1111)
        result1113 = _t1766
        self.record_span(span_start1112)
        return result1113

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        span_start1118 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1114 = []
        cond1115 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1115:
            _t1767 = self.parse_type()
            item1116 = _t1767
            xs1114.append(item1116)
            cond1115 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1117 = xs1114
        self.consume_literal(")")
        result1119 = types1117
        self.record_span(span_start1118)
        return result1119

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        span_start1124 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1120 = []
        cond1121 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1121:
            _t1768 = self.parse_type()
            item1122 = _t1768
            xs1120.append(item1122)
            cond1121 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1123 = xs1120
        self.consume_literal(")")
        result1125 = types1123
        self.record_span(span_start1124)
        return result1125

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1130 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        self.push_path(1)
        _t1769 = self.parse_csvlocator()
        csvlocator1126 = _t1769
        self.pop_path()
        self.push_path(2)
        _t1770 = self.parse_csv_config()
        csv_config1127 = _t1770
        self.pop_path()
        self.push_path(3)
        _t1771 = self.parse_csv_columns()
        csv_columns1128 = _t1771
        self.pop_path()
        self.push_path(4)
        _t1772 = self.parse_csv_asof()
        csv_asof1129 = _t1772
        self.pop_path()
        self.consume_literal(")")
        _t1773 = logic_pb2.CSVData(locator=csvlocator1126, config=csv_config1127, columns=csv_columns1128, asof=csv_asof1129)
        result1131 = _t1773
        self.record_span(span_start1130)
        return result1131

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1134 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        self.push_path(1)
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1775 = self.parse_csv_locator_paths()
            _t1774 = _t1775
        else:
            _t1774 = None
        csv_locator_paths1132 = _t1774
        self.pop_path()
        self.push_path(2)
        if self.match_lookahead_literal("(", 0):
            _t1777 = self.parse_csv_locator_inline_data()
            _t1776 = _t1777
        else:
            _t1776 = None
        csv_locator_inline_data1133 = _t1776
        self.pop_path()
        self.consume_literal(")")
        _t1778 = logic_pb2.CSVLocator(paths=(csv_locator_paths1132 if csv_locator_paths1132 is not None else []), inline_data=(csv_locator_inline_data1133 if csv_locator_inline_data1133 is not None else "").encode())
        result1135 = _t1778
        self.record_span(span_start1134)
        return result1135

    def parse_csv_locator_paths(self) -> Sequence[str]:
        span_start1140 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1136 = []
        cond1137 = self.match_lookahead_terminal("STRING", 0)
        while cond1137:
            item1138 = self.consume_terminal("STRING")
            xs1136.append(item1138)
            cond1137 = self.match_lookahead_terminal("STRING", 0)
        strings1139 = xs1136
        self.consume_literal(")")
        result1141 = strings1139
        self.record_span(span_start1140)
        return result1141

    def parse_csv_locator_inline_data(self) -> str:
        span_start1143 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1142 = self.consume_terminal("STRING")
        self.consume_literal(")")
        result1144 = string1142
        self.record_span(span_start1143)
        return result1144

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1146 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1779 = self.parse_config_dict()
        config_dict1145 = _t1779
        self.consume_literal(")")
        _t1780 = self.construct_csv_config(config_dict1145)
        result1147 = _t1780
        self.record_span(span_start1146)
        return result1147

    def parse_csv_columns(self) -> Sequence[logic_pb2.CSVColumn]:
        span_start1152 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1148 = []
        cond1149 = self.match_lookahead_literal("(", 0)
        while cond1149:
            _t1781 = self.parse_csv_column()
            item1150 = _t1781
            xs1148.append(item1150)
            cond1149 = self.match_lookahead_literal("(", 0)
        csv_columns1151 = xs1148
        self.consume_literal(")")
        result1153 = csv_columns1151
        self.record_span(span_start1152)
        return result1153

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        span_start1164 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        self.push_path(1)
        string1154 = self.consume_terminal("STRING")
        self.pop_path()
        self.push_path(2)
        _t1782 = self.parse_relation_id()
        relation_id1155 = _t1782
        self.pop_path()
        self.consume_literal("[")
        self.push_path(3)
        xs1160 = []
        cond1161 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        idx1162 = 0
        while cond1161:
            self.push_path(idx1162)
            _t1783 = self.parse_type()
            item1163 = _t1783
            self.pop_path()
            xs1160.append(item1163)
            idx1162 = (idx1162 + 1)
            cond1161 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1159 = xs1160
        self.pop_path()
        self.consume_literal("]")
        self.consume_literal(")")
        _t1784 = logic_pb2.CSVColumn(column_name=string1154, target_id=relation_id1155, types=types1159)
        result1165 = _t1784
        self.record_span(span_start1164)
        return result1165

    def parse_csv_asof(self) -> str:
        span_start1167 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("asof")
        string1166 = self.consume_terminal("STRING")
        self.consume_literal(")")
        result1168 = string1166
        self.record_span(span_start1167)
        return result1168

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1170 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        self.push_path(1)
        _t1785 = self.parse_fragment_id()
        fragment_id1169 = _t1785
        self.pop_path()
        self.consume_literal(")")
        _t1786 = transactions_pb2.Undefine(fragment_id=fragment_id1169)
        result1171 = _t1786
        self.record_span(span_start1170)
        return result1171

    def parse_context(self) -> transactions_pb2.Context:
        span_start1180 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        self.push_path(1)
        xs1176 = []
        cond1177 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        idx1178 = 0
        while cond1177:
            self.push_path(idx1178)
            _t1787 = self.parse_relation_id()
            item1179 = _t1787
            self.pop_path()
            xs1176.append(item1179)
            idx1178 = (idx1178 + 1)
            cond1177 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1175 = xs1176
        self.pop_path()
        self.consume_literal(")")
        _t1788 = transactions_pb2.Context(relations=relation_ids1175)
        result1181 = _t1788
        self.record_span(span_start1180)
        return result1181

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1184 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        self.push_path(1)
        _t1789 = self.parse_rel_edb_path()
        rel_edb_path1182 = _t1789
        self.pop_path()
        self.push_path(2)
        _t1790 = self.parse_relation_id()
        relation_id1183 = _t1790
        self.pop_path()
        self.consume_literal(")")
        _t1791 = transactions_pb2.Snapshot(destination_path=rel_edb_path1182, source_relation=relation_id1183)
        result1185 = _t1791
        self.record_span(span_start1184)
        return result1185

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        span_start1190 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1186 = []
        cond1187 = self.match_lookahead_literal("(", 0)
        while cond1187:
            _t1792 = self.parse_read()
            item1188 = _t1792
            xs1186.append(item1188)
            cond1187 = self.match_lookahead_literal("(", 0)
        reads1189 = xs1186
        self.consume_literal(")")
        result1191 = reads1189
        self.record_span(span_start1190)
        return result1191

    def parse_read(self) -> transactions_pb2.Read:
        span_start1198 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1794 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1795 = 1
                else:
                    if self.match_lookahead_literal("export", 1):
                        _t1796 = 4
                    else:
                        if self.match_lookahead_literal("demand", 1):
                            _t1797 = 0
                        else:
                            if self.match_lookahead_literal("abort", 1):
                                _t1798 = 3
                            else:
                                _t1798 = -1
                            _t1797 = _t1798
                        _t1796 = _t1797
                    _t1795 = _t1796
                _t1794 = _t1795
            _t1793 = _t1794
        else:
            _t1793 = -1
        prediction1192 = _t1793
        if prediction1192 == 4:
            _t1800 = self.parse_export()
            export1197 = _t1800
            _t1801 = transactions_pb2.Read(export=export1197)
            _t1799 = _t1801
        else:
            if prediction1192 == 3:
                _t1803 = self.parse_abort()
                abort1196 = _t1803
                _t1804 = transactions_pb2.Read(abort=abort1196)
                _t1802 = _t1804
            else:
                if prediction1192 == 2:
                    _t1806 = self.parse_what_if()
                    what_if1195 = _t1806
                    _t1807 = transactions_pb2.Read(what_if=what_if1195)
                    _t1805 = _t1807
                else:
                    if prediction1192 == 1:
                        _t1809 = self.parse_output()
                        output1194 = _t1809
                        _t1810 = transactions_pb2.Read(output=output1194)
                        _t1808 = _t1810
                    else:
                        if prediction1192 == 0:
                            _t1812 = self.parse_demand()
                            demand1193 = _t1812
                            _t1813 = transactions_pb2.Read(demand=demand1193)
                            _t1811 = _t1813
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1808 = _t1811
                    _t1805 = _t1808
                _t1802 = _t1805
            _t1799 = _t1802
        result1199 = _t1799
        self.record_span(span_start1198)
        return result1199

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1201 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        self.push_path(1)
        _t1814 = self.parse_relation_id()
        relation_id1200 = _t1814
        self.pop_path()
        self.consume_literal(")")
        _t1815 = transactions_pb2.Demand(relation_id=relation_id1200)
        result1202 = _t1815
        self.record_span(span_start1201)
        return result1202

    def parse_output(self) -> transactions_pb2.Output:
        span_start1205 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        self.push_path(1)
        _t1816 = self.parse_name()
        name1203 = _t1816
        self.pop_path()
        self.push_path(2)
        _t1817 = self.parse_relation_id()
        relation_id1204 = _t1817
        self.pop_path()
        self.consume_literal(")")
        _t1818 = transactions_pb2.Output(name=name1203, relation_id=relation_id1204)
        result1206 = _t1818
        self.record_span(span_start1205)
        return result1206

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1209 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        self.push_path(1)
        _t1819 = self.parse_name()
        name1207 = _t1819
        self.pop_path()
        self.push_path(2)
        _t1820 = self.parse_epoch()
        epoch1208 = _t1820
        self.pop_path()
        self.consume_literal(")")
        _t1821 = transactions_pb2.WhatIf(branch=name1207, epoch=epoch1208)
        result1210 = _t1821
        self.record_span(span_start1209)
        return result1210

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1213 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        self.push_path(1)
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t1823 = self.parse_name()
            _t1822 = _t1823
        else:
            _t1822 = None
        name1211 = _t1822
        self.pop_path()
        self.push_path(2)
        _t1824 = self.parse_relation_id()
        relation_id1212 = _t1824
        self.pop_path()
        self.consume_literal(")")
        _t1825 = transactions_pb2.Abort(name=(name1211 if name1211 is not None else "abort"), relation_id=relation_id1212)
        result1214 = _t1825
        self.record_span(span_start1213)
        return result1214

    def parse_export(self) -> transactions_pb2.Export:
        span_start1216 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export")
        self.push_path(1)
        _t1826 = self.parse_export_csv_config()
        export_csv_config1215 = _t1826
        self.pop_path()
        self.consume_literal(")")
        _t1827 = transactions_pb2.Export(csv_config=export_csv_config1215)
        result1217 = _t1827
        self.record_span(span_start1216)
        return result1217

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1221 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_csv_config")
        _t1828 = self.parse_export_csv_path()
        export_csv_path1218 = _t1828
        _t1829 = self.parse_export_csv_columns()
        export_csv_columns1219 = _t1829
        _t1830 = self.parse_config_dict()
        config_dict1220 = _t1830
        self.consume_literal(")")
        _t1831 = self.export_csv_config(export_csv_path1218, export_csv_columns1219, config_dict1220)
        result1222 = _t1831
        self.record_span(span_start1221)
        return result1222

    def parse_export_csv_path(self) -> str:
        span_start1224 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("path")
        string1223 = self.consume_terminal("STRING")
        self.consume_literal(")")
        result1225 = string1223
        self.record_span(span_start1224)
        return result1225

    def parse_export_csv_columns(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        span_start1230 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1226 = []
        cond1227 = self.match_lookahead_literal("(", 0)
        while cond1227:
            _t1832 = self.parse_export_csv_column()
            item1228 = _t1832
            xs1226.append(item1228)
            cond1227 = self.match_lookahead_literal("(", 0)
        export_csv_columns1229 = xs1226
        self.consume_literal(")")
        result1231 = export_csv_columns1229
        self.record_span(span_start1230)
        return result1231

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1234 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        self.push_path(1)
        string1232 = self.consume_terminal("STRING")
        self.pop_path()
        self.push_path(2)
        _t1833 = self.parse_relation_id()
        relation_id1233 = _t1833
        self.pop_path()
        self.consume_literal(")")
        _t1834 = transactions_pb2.ExportCSVColumn(column_name=string1232, column_data=relation_id1233)
        result1235 = _t1834
        self.record_span(span_start1234)
        return result1235


def parse(input_str: str) -> tuple[Any, dict[tuple[int, ...], Span]]:
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
