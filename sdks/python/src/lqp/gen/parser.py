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
            _t1683 = value.HasField("int_value")
        else:
            _t1683 = False
        if _t1683:
            assert value is not None
            return int(value.int_value)
        else:
            _t1684 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t1685 = value.HasField("int_value")
        else:
            _t1685 = False
        if _t1685:
            assert value is not None
            return value.int_value
        else:
            _t1686 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t1687 = value.HasField("string_value")
        else:
            _t1687 = False
        if _t1687:
            assert value is not None
            return value.string_value
        else:
            _t1688 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t1689 = value.HasField("boolean_value")
        else:
            _t1689 = False
        if _t1689:
            assert value is not None
            return value.boolean_value
        else:
            _t1690 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t1691 = value.HasField("string_value")
        else:
            _t1691 = False
        if _t1691:
            assert value is not None
            return [value.string_value]
        else:
            _t1692 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t1693 = value.HasField("int_value")
        else:
            _t1693 = False
        if _t1693:
            assert value is not None
            return value.int_value
        else:
            _t1694 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t1695 = value.HasField("float_value")
        else:
            _t1695 = False
        if _t1695:
            assert value is not None
            return value.float_value
        else:
            _t1696 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t1697 = value.HasField("string_value")
        else:
            _t1697 = False
        if _t1697:
            assert value is not None
            return value.string_value.encode()
        else:
            _t1698 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t1699 = value.HasField("uint128_value")
        else:
            _t1699 = False
        if _t1699:
            assert value is not None
            return value.uint128_value
        else:
            _t1700 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1701 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t1701
        _t1702 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t1702
        _t1703 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t1703
        _t1704 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t1704
        _t1705 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t1705
        _t1706 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t1706
        _t1707 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t1707
        _t1708 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t1708
        _t1709 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t1709
        _t1710 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t1710
        _t1711 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t1711
        _t1712 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t1712

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1713 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t1713
        _t1714 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t1714
        _t1715 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t1715
        _t1716 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t1716
        _t1717 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1717
        _t1718 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t1718
        _t1719 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t1719
        _t1720 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t1720
        _t1721 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t1721
        _t1722 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1722
        _t1723 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1723

    def default_configure(self) -> transactions_pb2.Configure:
        _t1724 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1724
        _t1725 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1725

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
        _t1726 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1726
        _t1727 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t1727
        _t1728 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1728

    def export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1729 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t1729
        _t1730 = self._extract_value_string(config.get("compression"), "")
        compression = _t1730
        _t1731 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t1731
        _t1732 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t1732
        _t1733 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t1733
        _t1734 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t1734
        _t1735 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t1735
        _t1736 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1736

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start548 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1085 = self.parse_configure()
            _t1084 = _t1085
        else:
            _t1084 = None
        configure542 = _t1084
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1087 = self.parse_sync()
            _t1086 = _t1087
        else:
            _t1086 = None
        sync543 = _t1086
        xs544 = []
        cond545 = self.match_lookahead_literal("(", 0)
        while cond545:
            _t1088 = self.parse_epoch()
            item546 = _t1088
            xs544.append(item546)
            cond545 = self.match_lookahead_literal("(", 0)
        epochs547 = xs544
        self.consume_literal(")")
        _t1089 = self.default_configure()
        _t1090 = transactions_pb2.Transaction(epochs=epochs547, configure=(configure542 if configure542 is not None else _t1089), sync=sync543)
        result549 = _t1090
        self.record_span(span_start548, "Transaction")
        return result549

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start551 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1091 = self.parse_config_dict()
        config_dict550 = _t1091
        self.consume_literal(")")
        _t1092 = self.construct_configure(config_dict550)
        result552 = _t1092
        self.record_span(span_start551, "Configure")
        return result552

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs553 = []
        cond554 = self.match_lookahead_literal(":", 0)
        while cond554:
            _t1093 = self.parse_config_key_value()
            item555 = _t1093
            xs553.append(item555)
            cond554 = self.match_lookahead_literal(":", 0)
        config_key_values556 = xs553
        self.consume_literal("}")
        return config_key_values556

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol557 = self.consume_terminal("SYMBOL")
        _t1094 = self.parse_value()
        value558 = _t1094
        return (symbol557, value558,)

    def parse_value(self) -> logic_pb2.Value:
        span_start569 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1095 = 9
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1096 = 8
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1097 = 9
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1099 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1100 = 0
                            else:
                                _t1100 = -1
                            _t1099 = _t1100
                        _t1098 = _t1099
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t1101 = 5
                        else:
                            if self.match_lookahead_terminal("STRING", 0):
                                _t1102 = 2
                            else:
                                if self.match_lookahead_terminal("INT128", 0):
                                    _t1103 = 6
                                else:
                                    if self.match_lookahead_terminal("INT", 0):
                                        _t1104 = 3
                                    else:
                                        if self.match_lookahead_terminal("FLOAT", 0):
                                            _t1105 = 4
                                        else:
                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                _t1106 = 7
                                            else:
                                                _t1106 = -1
                                            _t1105 = _t1106
                                        _t1104 = _t1105
                                    _t1103 = _t1104
                                _t1102 = _t1103
                            _t1101 = _t1102
                        _t1098 = _t1101
                    _t1097 = _t1098
                _t1096 = _t1097
            _t1095 = _t1096
        prediction559 = _t1095
        if prediction559 == 9:
            _t1108 = self.parse_boolean_value()
            boolean_value568 = _t1108
            _t1109 = logic_pb2.Value(boolean_value=boolean_value568)
            _t1107 = _t1109
        else:
            if prediction559 == 8:
                self.consume_literal("missing")
                _t1111 = logic_pb2.MissingValue()
                _t1112 = logic_pb2.Value(missing_value=_t1111)
                _t1110 = _t1112
            else:
                if prediction559 == 7:
                    decimal567 = self.consume_terminal("DECIMAL")
                    _t1114 = logic_pb2.Value(decimal_value=decimal567)
                    _t1113 = _t1114
                else:
                    if prediction559 == 6:
                        int128566 = self.consume_terminal("INT128")
                        _t1116 = logic_pb2.Value(int128_value=int128566)
                        _t1115 = _t1116
                    else:
                        if prediction559 == 5:
                            uint128565 = self.consume_terminal("UINT128")
                            _t1118 = logic_pb2.Value(uint128_value=uint128565)
                            _t1117 = _t1118
                        else:
                            if prediction559 == 4:
                                float564 = self.consume_terminal("FLOAT")
                                _t1120 = logic_pb2.Value(float_value=float564)
                                _t1119 = _t1120
                            else:
                                if prediction559 == 3:
                                    int563 = self.consume_terminal("INT")
                                    _t1122 = logic_pb2.Value(int_value=int563)
                                    _t1121 = _t1122
                                else:
                                    if prediction559 == 2:
                                        string562 = self.consume_terminal("STRING")
                                        _t1124 = logic_pb2.Value(string_value=string562)
                                        _t1123 = _t1124
                                    else:
                                        if prediction559 == 1:
                                            _t1126 = self.parse_datetime()
                                            datetime561 = _t1126
                                            _t1127 = logic_pb2.Value(datetime_value=datetime561)
                                            _t1125 = _t1127
                                        else:
                                            if prediction559 == 0:
                                                _t1129 = self.parse_date()
                                                date560 = _t1129
                                                _t1130 = logic_pb2.Value(date_value=date560)
                                                _t1128 = _t1130
                                            else:
                                                raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1125 = _t1128
                                        _t1123 = _t1125
                                    _t1121 = _t1123
                                _t1119 = _t1121
                            _t1117 = _t1119
                        _t1115 = _t1117
                    _t1113 = _t1115
                _t1110 = _t1113
            _t1107 = _t1110
        result570 = _t1107
        self.record_span(span_start569, "Value")
        return result570

    def parse_date(self) -> logic_pb2.DateValue:
        span_start574 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int571 = self.consume_terminal("INT")
        int_3572 = self.consume_terminal("INT")
        int_4573 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1131 = logic_pb2.DateValue(year=int(int571), month=int(int_3572), day=int(int_4573))
        result575 = _t1131
        self.record_span(span_start574, "DateValue")
        return result575

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start583 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int576 = self.consume_terminal("INT")
        int_3577 = self.consume_terminal("INT")
        int_4578 = self.consume_terminal("INT")
        int_5579 = self.consume_terminal("INT")
        int_6580 = self.consume_terminal("INT")
        int_7581 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1132 = self.consume_terminal("INT")
        else:
            _t1132 = None
        int_8582 = _t1132
        self.consume_literal(")")
        _t1133 = logic_pb2.DateTimeValue(year=int(int576), month=int(int_3577), day=int(int_4578), hour=int(int_5579), minute=int(int_6580), second=int(int_7581), microsecond=int((int_8582 if int_8582 is not None else 0)))
        result584 = _t1133
        self.record_span(span_start583, "DateTimeValue")
        return result584

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1134 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1135 = 1
            else:
                _t1135 = -1
            _t1134 = _t1135
        prediction585 = _t1134
        if prediction585 == 1:
            self.consume_literal("false")
            _t1136 = False
        else:
            if prediction585 == 0:
                self.consume_literal("true")
                _t1137 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1136 = _t1137
        return _t1136

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start590 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs586 = []
        cond587 = self.match_lookahead_literal(":", 0)
        while cond587:
            _t1138 = self.parse_fragment_id()
            item588 = _t1138
            xs586.append(item588)
            cond587 = self.match_lookahead_literal(":", 0)
        fragment_ids589 = xs586
        self.consume_literal(")")
        _t1139 = transactions_pb2.Sync(fragments=fragment_ids589)
        result591 = _t1139
        self.record_span(span_start590, "Sync")
        return result591

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start593 = self.span_start()
        self.consume_literal(":")
        symbol592 = self.consume_terminal("SYMBOL")
        result594 = fragments_pb2.FragmentId(id=symbol592.encode())
        self.record_span(span_start593, "FragmentId")
        return result594

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start597 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1141 = self.parse_epoch_writes()
            _t1140 = _t1141
        else:
            _t1140 = None
        epoch_writes595 = _t1140
        if self.match_lookahead_literal("(", 0):
            _t1143 = self.parse_epoch_reads()
            _t1142 = _t1143
        else:
            _t1142 = None
        epoch_reads596 = _t1142
        self.consume_literal(")")
        _t1144 = transactions_pb2.Epoch(writes=(epoch_writes595 if epoch_writes595 is not None else []), reads=(epoch_reads596 if epoch_reads596 is not None else []))
        result598 = _t1144
        self.record_span(span_start597, "Epoch")
        return result598

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs599 = []
        cond600 = self.match_lookahead_literal("(", 0)
        while cond600:
            _t1145 = self.parse_write()
            item601 = _t1145
            xs599.append(item601)
            cond600 = self.match_lookahead_literal("(", 0)
        writes602 = xs599
        self.consume_literal(")")
        return writes602

    def parse_write(self) -> transactions_pb2.Write:
        span_start608 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1147 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1148 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1149 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1150 = 2
                        else:
                            _t1150 = -1
                        _t1149 = _t1150
                    _t1148 = _t1149
                _t1147 = _t1148
            _t1146 = _t1147
        else:
            _t1146 = -1
        prediction603 = _t1146
        if prediction603 == 3:
            _t1152 = self.parse_snapshot()
            snapshot607 = _t1152
            _t1153 = transactions_pb2.Write(snapshot=snapshot607)
            _t1151 = _t1153
        else:
            if prediction603 == 2:
                _t1155 = self.parse_context()
                context606 = _t1155
                _t1156 = transactions_pb2.Write(context=context606)
                _t1154 = _t1156
            else:
                if prediction603 == 1:
                    _t1158 = self.parse_undefine()
                    undefine605 = _t1158
                    _t1159 = transactions_pb2.Write(undefine=undefine605)
                    _t1157 = _t1159
                else:
                    if prediction603 == 0:
                        _t1161 = self.parse_define()
                        define604 = _t1161
                        _t1162 = transactions_pb2.Write(define=define604)
                        _t1160 = _t1162
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1157 = _t1160
                _t1154 = _t1157
            _t1151 = _t1154
        result609 = _t1151
        self.record_span(span_start608, "Write")
        return result609

    def parse_define(self) -> transactions_pb2.Define:
        span_start611 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1163 = self.parse_fragment()
        fragment610 = _t1163
        self.consume_literal(")")
        _t1164 = transactions_pb2.Define(fragment=fragment610)
        result612 = _t1164
        self.record_span(span_start611, "Define")
        return result612

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start618 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1165 = self.parse_new_fragment_id()
        new_fragment_id613 = _t1165
        xs614 = []
        cond615 = self.match_lookahead_literal("(", 0)
        while cond615:
            _t1166 = self.parse_declaration()
            item616 = _t1166
            xs614.append(item616)
            cond615 = self.match_lookahead_literal("(", 0)
        declarations617 = xs614
        self.consume_literal(")")
        result619 = self.construct_fragment(new_fragment_id613, declarations617)
        self.record_span(span_start618, "Fragment")
        return result619

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start621 = self.span_start()
        _t1167 = self.parse_fragment_id()
        fragment_id620 = _t1167
        self.start_fragment(fragment_id620)
        result622 = fragment_id620
        self.record_span(span_start621, "FragmentId")
        return result622

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start628 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("rel_edb", 1):
                _t1169 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1170 = 2
                else:
                    if self.match_lookahead_literal("def", 1):
                        _t1171 = 0
                    else:
                        if self.match_lookahead_literal("csv_data", 1):
                            _t1172 = 3
                        else:
                            if self.match_lookahead_literal("betree_relation", 1):
                                _t1173 = 3
                            else:
                                if self.match_lookahead_literal("algorithm", 1):
                                    _t1174 = 1
                                else:
                                    _t1174 = -1
                                _t1173 = _t1174
                            _t1172 = _t1173
                        _t1171 = _t1172
                    _t1170 = _t1171
                _t1169 = _t1170
            _t1168 = _t1169
        else:
            _t1168 = -1
        prediction623 = _t1168
        if prediction623 == 3:
            _t1176 = self.parse_data()
            data627 = _t1176
            _t1177 = logic_pb2.Declaration(data=data627)
            _t1175 = _t1177
        else:
            if prediction623 == 2:
                _t1179 = self.parse_constraint()
                constraint626 = _t1179
                _t1180 = logic_pb2.Declaration(constraint=constraint626)
                _t1178 = _t1180
            else:
                if prediction623 == 1:
                    _t1182 = self.parse_algorithm()
                    algorithm625 = _t1182
                    _t1183 = logic_pb2.Declaration(algorithm=algorithm625)
                    _t1181 = _t1183
                else:
                    if prediction623 == 0:
                        _t1185 = self.parse_def()
                        def624 = _t1185
                        _t1186 = logic_pb2.Declaration()
                        getattr(_t1186, 'def').CopyFrom(def624)
                        _t1184 = _t1186
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1181 = _t1184
                _t1178 = _t1181
            _t1175 = _t1178
        result629 = _t1175
        self.record_span(span_start628, "Declaration")
        return result629

    def parse_def(self) -> logic_pb2.Def:
        span_start633 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1187 = self.parse_relation_id()
        relation_id630 = _t1187
        _t1188 = self.parse_abstraction()
        abstraction631 = _t1188
        if self.match_lookahead_literal("(", 0):
            _t1190 = self.parse_attrs()
            _t1189 = _t1190
        else:
            _t1189 = None
        attrs632 = _t1189
        self.consume_literal(")")
        _t1191 = logic_pb2.Def(name=relation_id630, body=abstraction631, attrs=(attrs632 if attrs632 is not None else []))
        result634 = _t1191
        self.record_span(span_start633, "Def")
        return result634

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start638 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1192 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1193 = 1
            else:
                _t1193 = -1
            _t1192 = _t1193
        prediction635 = _t1192
        if prediction635 == 1:
            uint128637 = self.consume_terminal("UINT128")
            _t1194 = logic_pb2.RelationId(id_low=uint128637.low, id_high=uint128637.high)
        else:
            if prediction635 == 0:
                self.consume_literal(":")
                symbol636 = self.consume_terminal("SYMBOL")
                _t1195 = self.relation_id_from_string(symbol636)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1194 = _t1195
        result639 = _t1194
        self.record_span(span_start638, "RelationId")
        return result639

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start642 = self.span_start()
        self.consume_literal("(")
        _t1196 = self.parse_bindings()
        bindings640 = _t1196
        _t1197 = self.parse_formula()
        formula641 = _t1197
        self.consume_literal(")")
        _t1198 = logic_pb2.Abstraction(vars=(list(bindings640[0]) + list(bindings640[1] if bindings640[1] is not None else [])), value=formula641)
        result643 = _t1198
        self.record_span(span_start642, "Abstraction")
        return result643

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs644 = []
        cond645 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond645:
            _t1199 = self.parse_binding()
            item646 = _t1199
            xs644.append(item646)
            cond645 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings647 = xs644
        if self.match_lookahead_literal("|", 0):
            _t1201 = self.parse_value_bindings()
            _t1200 = _t1201
        else:
            _t1200 = None
        value_bindings648 = _t1200
        self.consume_literal("]")
        return (bindings647, (value_bindings648 if value_bindings648 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start651 = self.span_start()
        symbol649 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1202 = self.parse_type()
        type650 = _t1202
        _t1203 = logic_pb2.Var(name=symbol649)
        _t1204 = logic_pb2.Binding(var=_t1203, type=type650)
        result652 = _t1204
        self.record_span(span_start651, "Binding")
        return result652

    def parse_type(self) -> logic_pb2.Type:
        span_start665 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1205 = 0
        else:
            if self.match_lookahead_literal("UINT128", 0):
                _t1206 = 4
            else:
                if self.match_lookahead_literal("STRING", 0):
                    _t1207 = 1
                else:
                    if self.match_lookahead_literal("MISSING", 0):
                        _t1208 = 8
                    else:
                        if self.match_lookahead_literal("INT128", 0):
                            _t1209 = 5
                        else:
                            if self.match_lookahead_literal("INT", 0):
                                _t1210 = 2
                            else:
                                if self.match_lookahead_literal("FLOAT", 0):
                                    _t1211 = 3
                                else:
                                    if self.match_lookahead_literal("DATETIME", 0):
                                        _t1212 = 7
                                    else:
                                        if self.match_lookahead_literal("DATE", 0):
                                            _t1213 = 6
                                        else:
                                            if self.match_lookahead_literal("BOOLEAN", 0):
                                                _t1214 = 10
                                            else:
                                                if self.match_lookahead_literal("(", 0):
                                                    _t1215 = 9
                                                else:
                                                    _t1215 = -1
                                                _t1214 = _t1215
                                            _t1213 = _t1214
                                        _t1212 = _t1213
                                    _t1211 = _t1212
                                _t1210 = _t1211
                            _t1209 = _t1210
                        _t1208 = _t1209
                    _t1207 = _t1208
                _t1206 = _t1207
            _t1205 = _t1206
        prediction653 = _t1205
        if prediction653 == 10:
            _t1217 = self.parse_boolean_type()
            boolean_type664 = _t1217
            _t1218 = logic_pb2.Type(boolean_type=boolean_type664)
            _t1216 = _t1218
        else:
            if prediction653 == 9:
                _t1220 = self.parse_decimal_type()
                decimal_type663 = _t1220
                _t1221 = logic_pb2.Type(decimal_type=decimal_type663)
                _t1219 = _t1221
            else:
                if prediction653 == 8:
                    _t1223 = self.parse_missing_type()
                    missing_type662 = _t1223
                    _t1224 = logic_pb2.Type(missing_type=missing_type662)
                    _t1222 = _t1224
                else:
                    if prediction653 == 7:
                        _t1226 = self.parse_datetime_type()
                        datetime_type661 = _t1226
                        _t1227 = logic_pb2.Type(datetime_type=datetime_type661)
                        _t1225 = _t1227
                    else:
                        if prediction653 == 6:
                            _t1229 = self.parse_date_type()
                            date_type660 = _t1229
                            _t1230 = logic_pb2.Type(date_type=date_type660)
                            _t1228 = _t1230
                        else:
                            if prediction653 == 5:
                                _t1232 = self.parse_int128_type()
                                int128_type659 = _t1232
                                _t1233 = logic_pb2.Type(int128_type=int128_type659)
                                _t1231 = _t1233
                            else:
                                if prediction653 == 4:
                                    _t1235 = self.parse_uint128_type()
                                    uint128_type658 = _t1235
                                    _t1236 = logic_pb2.Type(uint128_type=uint128_type658)
                                    _t1234 = _t1236
                                else:
                                    if prediction653 == 3:
                                        _t1238 = self.parse_float_type()
                                        float_type657 = _t1238
                                        _t1239 = logic_pb2.Type(float_type=float_type657)
                                        _t1237 = _t1239
                                    else:
                                        if prediction653 == 2:
                                            _t1241 = self.parse_int_type()
                                            int_type656 = _t1241
                                            _t1242 = logic_pb2.Type(int_type=int_type656)
                                            _t1240 = _t1242
                                        else:
                                            if prediction653 == 1:
                                                _t1244 = self.parse_string_type()
                                                string_type655 = _t1244
                                                _t1245 = logic_pb2.Type(string_type=string_type655)
                                                _t1243 = _t1245
                                            else:
                                                if prediction653 == 0:
                                                    _t1247 = self.parse_unspecified_type()
                                                    unspecified_type654 = _t1247
                                                    _t1248 = logic_pb2.Type(unspecified_type=unspecified_type654)
                                                    _t1246 = _t1248
                                                else:
                                                    raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t1243 = _t1246
                                            _t1240 = _t1243
                                        _t1237 = _t1240
                                    _t1234 = _t1237
                                _t1231 = _t1234
                            _t1228 = _t1231
                        _t1225 = _t1228
                    _t1222 = _t1225
                _t1219 = _t1222
            _t1216 = _t1219
        result666 = _t1216
        self.record_span(span_start665, "Type")
        return result666

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start667 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1249 = logic_pb2.UnspecifiedType()
        result668 = _t1249
        self.record_span(span_start667, "UnspecifiedType")
        return result668

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start669 = self.span_start()
        self.consume_literal("STRING")
        _t1250 = logic_pb2.StringType()
        result670 = _t1250
        self.record_span(span_start669, "StringType")
        return result670

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start671 = self.span_start()
        self.consume_literal("INT")
        _t1251 = logic_pb2.IntType()
        result672 = _t1251
        self.record_span(span_start671, "IntType")
        return result672

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start673 = self.span_start()
        self.consume_literal("FLOAT")
        _t1252 = logic_pb2.FloatType()
        result674 = _t1252
        self.record_span(span_start673, "FloatType")
        return result674

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start675 = self.span_start()
        self.consume_literal("UINT128")
        _t1253 = logic_pb2.UInt128Type()
        result676 = _t1253
        self.record_span(span_start675, "UInt128Type")
        return result676

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start677 = self.span_start()
        self.consume_literal("INT128")
        _t1254 = logic_pb2.Int128Type()
        result678 = _t1254
        self.record_span(span_start677, "Int128Type")
        return result678

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start679 = self.span_start()
        self.consume_literal("DATE")
        _t1255 = logic_pb2.DateType()
        result680 = _t1255
        self.record_span(span_start679, "DateType")
        return result680

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start681 = self.span_start()
        self.consume_literal("DATETIME")
        _t1256 = logic_pb2.DateTimeType()
        result682 = _t1256
        self.record_span(span_start681, "DateTimeType")
        return result682

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start683 = self.span_start()
        self.consume_literal("MISSING")
        _t1257 = logic_pb2.MissingType()
        result684 = _t1257
        self.record_span(span_start683, "MissingType")
        return result684

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start687 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int685 = self.consume_terminal("INT")
        int_3686 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1258 = logic_pb2.DecimalType(precision=int(int685), scale=int(int_3686))
        result688 = _t1258
        self.record_span(span_start687, "DecimalType")
        return result688

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start689 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1259 = logic_pb2.BooleanType()
        result690 = _t1259
        self.record_span(span_start689, "BooleanType")
        return result690

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs691 = []
        cond692 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond692:
            _t1260 = self.parse_binding()
            item693 = _t1260
            xs691.append(item693)
            cond692 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings694 = xs691
        return bindings694

    def parse_formula(self) -> logic_pb2.Formula:
        span_start709 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1262 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1263 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1264 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1265 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1266 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1267 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1268 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1269 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1270 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1271 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1272 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1273 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1274 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1275 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1276 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1277 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1278 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1279 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1280 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1281 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1282 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1283 = 10
                                                                                                else:
                                                                                                    _t1283 = -1
                                                                                                _t1282 = _t1283
                                                                                            _t1281 = _t1282
                                                                                        _t1280 = _t1281
                                                                                    _t1279 = _t1280
                                                                                _t1278 = _t1279
                                                                            _t1277 = _t1278
                                                                        _t1276 = _t1277
                                                                    _t1275 = _t1276
                                                                _t1274 = _t1275
                                                            _t1273 = _t1274
                                                        _t1272 = _t1273
                                                    _t1271 = _t1272
                                                _t1270 = _t1271
                                            _t1269 = _t1270
                                        _t1268 = _t1269
                                    _t1267 = _t1268
                                _t1266 = _t1267
                            _t1265 = _t1266
                        _t1264 = _t1265
                    _t1263 = _t1264
                _t1262 = _t1263
            _t1261 = _t1262
        else:
            _t1261 = -1
        prediction695 = _t1261
        if prediction695 == 12:
            _t1285 = self.parse_cast()
            cast708 = _t1285
            _t1286 = logic_pb2.Formula(cast=cast708)
            _t1284 = _t1286
        else:
            if prediction695 == 11:
                _t1288 = self.parse_rel_atom()
                rel_atom707 = _t1288
                _t1289 = logic_pb2.Formula(rel_atom=rel_atom707)
                _t1287 = _t1289
            else:
                if prediction695 == 10:
                    _t1291 = self.parse_primitive()
                    primitive706 = _t1291
                    _t1292 = logic_pb2.Formula(primitive=primitive706)
                    _t1290 = _t1292
                else:
                    if prediction695 == 9:
                        _t1294 = self.parse_pragma()
                        pragma705 = _t1294
                        _t1295 = logic_pb2.Formula(pragma=pragma705)
                        _t1293 = _t1295
                    else:
                        if prediction695 == 8:
                            _t1297 = self.parse_atom()
                            atom704 = _t1297
                            _t1298 = logic_pb2.Formula(atom=atom704)
                            _t1296 = _t1298
                        else:
                            if prediction695 == 7:
                                _t1300 = self.parse_ffi()
                                ffi703 = _t1300
                                _t1301 = logic_pb2.Formula(ffi=ffi703)
                                _t1299 = _t1301
                            else:
                                if prediction695 == 6:
                                    _t1303 = self.parse_not()
                                    not702 = _t1303
                                    _t1304 = logic_pb2.Formula()
                                    getattr(_t1304, 'not').CopyFrom(not702)
                                    _t1302 = _t1304
                                else:
                                    if prediction695 == 5:
                                        _t1306 = self.parse_disjunction()
                                        disjunction701 = _t1306
                                        _t1307 = logic_pb2.Formula(disjunction=disjunction701)
                                        _t1305 = _t1307
                                    else:
                                        if prediction695 == 4:
                                            _t1309 = self.parse_conjunction()
                                            conjunction700 = _t1309
                                            _t1310 = logic_pb2.Formula(conjunction=conjunction700)
                                            _t1308 = _t1310
                                        else:
                                            if prediction695 == 3:
                                                _t1312 = self.parse_reduce()
                                                reduce699 = _t1312
                                                _t1313 = logic_pb2.Formula(reduce=reduce699)
                                                _t1311 = _t1313
                                            else:
                                                if prediction695 == 2:
                                                    _t1315 = self.parse_exists()
                                                    exists698 = _t1315
                                                    _t1316 = logic_pb2.Formula(exists=exists698)
                                                    _t1314 = _t1316
                                                else:
                                                    if prediction695 == 1:
                                                        _t1318 = self.parse_false()
                                                        false697 = _t1318
                                                        _t1319 = logic_pb2.Formula(disjunction=false697)
                                                        _t1317 = _t1319
                                                    else:
                                                        if prediction695 == 0:
                                                            _t1321 = self.parse_true()
                                                            true696 = _t1321
                                                            _t1322 = logic_pb2.Formula(conjunction=true696)
                                                            _t1320 = _t1322
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1317 = _t1320
                                                    _t1314 = _t1317
                                                _t1311 = _t1314
                                            _t1308 = _t1311
                                        _t1305 = _t1308
                                    _t1302 = _t1305
                                _t1299 = _t1302
                            _t1296 = _t1299
                        _t1293 = _t1296
                    _t1290 = _t1293
                _t1287 = _t1290
            _t1284 = _t1287
        result710 = _t1284
        self.record_span(span_start709, "Formula")
        return result710

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start711 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1323 = logic_pb2.Conjunction(args=[])
        result712 = _t1323
        self.record_span(span_start711, "Conjunction")
        return result712

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start713 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1324 = logic_pb2.Disjunction(args=[])
        result714 = _t1324
        self.record_span(span_start713, "Disjunction")
        return result714

    def parse_exists(self) -> logic_pb2.Exists:
        span_start717 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1325 = self.parse_bindings()
        bindings715 = _t1325
        _t1326 = self.parse_formula()
        formula716 = _t1326
        self.consume_literal(")")
        _t1327 = logic_pb2.Abstraction(vars=(list(bindings715[0]) + list(bindings715[1] if bindings715[1] is not None else [])), value=formula716)
        _t1328 = logic_pb2.Exists(body=_t1327)
        result718 = _t1328
        self.record_span(span_start717, "Exists")
        return result718

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start722 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1329 = self.parse_abstraction()
        abstraction719 = _t1329
        _t1330 = self.parse_abstraction()
        abstraction_3720 = _t1330
        _t1331 = self.parse_terms()
        terms721 = _t1331
        self.consume_literal(")")
        _t1332 = logic_pb2.Reduce(op=abstraction719, body=abstraction_3720, terms=terms721)
        result723 = _t1332
        self.record_span(span_start722, "Reduce")
        return result723

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs724 = []
        cond725 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond725:
            _t1333 = self.parse_term()
            item726 = _t1333
            xs724.append(item726)
            cond725 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms727 = xs724
        self.consume_literal(")")
        return terms727

    def parse_term(self) -> logic_pb2.Term:
        span_start731 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1334 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1335 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1336 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1337 = 1
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t1338 = 1
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1339 = 0
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1340 = 1
                                else:
                                    if self.match_lookahead_terminal("INT128", 0):
                                        _t1341 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT", 0):
                                            _t1342 = 1
                                        else:
                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                _t1343 = 1
                                            else:
                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                    _t1344 = 1
                                                else:
                                                    _t1344 = -1
                                                _t1343 = _t1344
                                            _t1342 = _t1343
                                        _t1341 = _t1342
                                    _t1340 = _t1341
                                _t1339 = _t1340
                            _t1338 = _t1339
                        _t1337 = _t1338
                    _t1336 = _t1337
                _t1335 = _t1336
            _t1334 = _t1335
        prediction728 = _t1334
        if prediction728 == 1:
            _t1346 = self.parse_constant()
            constant730 = _t1346
            _t1347 = logic_pb2.Term(constant=constant730)
            _t1345 = _t1347
        else:
            if prediction728 == 0:
                _t1349 = self.parse_var()
                var729 = _t1349
                _t1350 = logic_pb2.Term(var=var729)
                _t1348 = _t1350
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1345 = _t1348
        result732 = _t1345
        self.record_span(span_start731, "Term")
        return result732

    def parse_var(self) -> logic_pb2.Var:
        span_start734 = self.span_start()
        symbol733 = self.consume_terminal("SYMBOL")
        _t1351 = logic_pb2.Var(name=symbol733)
        result735 = _t1351
        self.record_span(span_start734, "Var")
        return result735

    def parse_constant(self) -> logic_pb2.Value:
        span_start737 = self.span_start()
        _t1352 = self.parse_value()
        value736 = _t1352
        result738 = value736
        self.record_span(span_start737, "Value")
        return result738

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start743 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs739 = []
        cond740 = self.match_lookahead_literal("(", 0)
        while cond740:
            _t1353 = self.parse_formula()
            item741 = _t1353
            xs739.append(item741)
            cond740 = self.match_lookahead_literal("(", 0)
        formulas742 = xs739
        self.consume_literal(")")
        _t1354 = logic_pb2.Conjunction(args=formulas742)
        result744 = _t1354
        self.record_span(span_start743, "Conjunction")
        return result744

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start749 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs745 = []
        cond746 = self.match_lookahead_literal("(", 0)
        while cond746:
            _t1355 = self.parse_formula()
            item747 = _t1355
            xs745.append(item747)
            cond746 = self.match_lookahead_literal("(", 0)
        formulas748 = xs745
        self.consume_literal(")")
        _t1356 = logic_pb2.Disjunction(args=formulas748)
        result750 = _t1356
        self.record_span(span_start749, "Disjunction")
        return result750

    def parse_not(self) -> logic_pb2.Not:
        span_start752 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1357 = self.parse_formula()
        formula751 = _t1357
        self.consume_literal(")")
        _t1358 = logic_pb2.Not(arg=formula751)
        result753 = _t1358
        self.record_span(span_start752, "Not")
        return result753

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start757 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1359 = self.parse_name()
        name754 = _t1359
        _t1360 = self.parse_ffi_args()
        ffi_args755 = _t1360
        _t1361 = self.parse_terms()
        terms756 = _t1361
        self.consume_literal(")")
        _t1362 = logic_pb2.FFI(name=name754, args=ffi_args755, terms=terms756)
        result758 = _t1362
        self.record_span(span_start757, "FFI")
        return result758

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol759 = self.consume_terminal("SYMBOL")
        return symbol759

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs760 = []
        cond761 = self.match_lookahead_literal("(", 0)
        while cond761:
            _t1363 = self.parse_abstraction()
            item762 = _t1363
            xs760.append(item762)
            cond761 = self.match_lookahead_literal("(", 0)
        abstractions763 = xs760
        self.consume_literal(")")
        return abstractions763

    def parse_atom(self) -> logic_pb2.Atom:
        span_start769 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1364 = self.parse_relation_id()
        relation_id764 = _t1364
        xs765 = []
        cond766 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond766:
            _t1365 = self.parse_term()
            item767 = _t1365
            xs765.append(item767)
            cond766 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms768 = xs765
        self.consume_literal(")")
        _t1366 = logic_pb2.Atom(name=relation_id764, terms=terms768)
        result770 = _t1366
        self.record_span(span_start769, "Atom")
        return result770

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start776 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1367 = self.parse_name()
        name771 = _t1367
        xs772 = []
        cond773 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond773:
            _t1368 = self.parse_term()
            item774 = _t1368
            xs772.append(item774)
            cond773 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms775 = xs772
        self.consume_literal(")")
        _t1369 = logic_pb2.Pragma(name=name771, terms=terms775)
        result777 = _t1369
        self.record_span(span_start776, "Pragma")
        return result777

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start793 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1371 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1372 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1373 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1374 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1375 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1376 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1377 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1378 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1379 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1380 = 7
                                                else:
                                                    _t1380 = -1
                                                _t1379 = _t1380
                                            _t1378 = _t1379
                                        _t1377 = _t1378
                                    _t1376 = _t1377
                                _t1375 = _t1376
                            _t1374 = _t1375
                        _t1373 = _t1374
                    _t1372 = _t1373
                _t1371 = _t1372
            _t1370 = _t1371
        else:
            _t1370 = -1
        prediction778 = _t1370
        if prediction778 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1382 = self.parse_name()
            name788 = _t1382
            xs789 = []
            cond790 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            while cond790:
                _t1383 = self.parse_rel_term()
                item791 = _t1383
                xs789.append(item791)
                cond790 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            rel_terms792 = xs789
            self.consume_literal(")")
            _t1384 = logic_pb2.Primitive(name=name788, terms=rel_terms792)
            _t1381 = _t1384
        else:
            if prediction778 == 8:
                _t1386 = self.parse_divide()
                divide787 = _t1386
                _t1385 = divide787
            else:
                if prediction778 == 7:
                    _t1388 = self.parse_multiply()
                    multiply786 = _t1388
                    _t1387 = multiply786
                else:
                    if prediction778 == 6:
                        _t1390 = self.parse_minus()
                        minus785 = _t1390
                        _t1389 = minus785
                    else:
                        if prediction778 == 5:
                            _t1392 = self.parse_add()
                            add784 = _t1392
                            _t1391 = add784
                        else:
                            if prediction778 == 4:
                                _t1394 = self.parse_gt_eq()
                                gt_eq783 = _t1394
                                _t1393 = gt_eq783
                            else:
                                if prediction778 == 3:
                                    _t1396 = self.parse_gt()
                                    gt782 = _t1396
                                    _t1395 = gt782
                                else:
                                    if prediction778 == 2:
                                        _t1398 = self.parse_lt_eq()
                                        lt_eq781 = _t1398
                                        _t1397 = lt_eq781
                                    else:
                                        if prediction778 == 1:
                                            _t1400 = self.parse_lt()
                                            lt780 = _t1400
                                            _t1399 = lt780
                                        else:
                                            if prediction778 == 0:
                                                _t1402 = self.parse_eq()
                                                eq779 = _t1402
                                                _t1401 = eq779
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1399 = _t1401
                                        _t1397 = _t1399
                                    _t1395 = _t1397
                                _t1393 = _t1395
                            _t1391 = _t1393
                        _t1389 = _t1391
                    _t1387 = _t1389
                _t1385 = _t1387
            _t1381 = _t1385
        result794 = _t1381
        self.record_span(span_start793, "Primitive")
        return result794

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start797 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1403 = self.parse_term()
        term795 = _t1403
        _t1404 = self.parse_term()
        term_3796 = _t1404
        self.consume_literal(")")
        _t1405 = logic_pb2.RelTerm(term=term795)
        _t1406 = logic_pb2.RelTerm(term=term_3796)
        _t1407 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1405, _t1406])
        result798 = _t1407
        self.record_span(span_start797, "Primitive")
        return result798

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start801 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1408 = self.parse_term()
        term799 = _t1408
        _t1409 = self.parse_term()
        term_3800 = _t1409
        self.consume_literal(")")
        _t1410 = logic_pb2.RelTerm(term=term799)
        _t1411 = logic_pb2.RelTerm(term=term_3800)
        _t1412 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1410, _t1411])
        result802 = _t1412
        self.record_span(span_start801, "Primitive")
        return result802

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start805 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1413 = self.parse_term()
        term803 = _t1413
        _t1414 = self.parse_term()
        term_3804 = _t1414
        self.consume_literal(")")
        _t1415 = logic_pb2.RelTerm(term=term803)
        _t1416 = logic_pb2.RelTerm(term=term_3804)
        _t1417 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1415, _t1416])
        result806 = _t1417
        self.record_span(span_start805, "Primitive")
        return result806

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start809 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1418 = self.parse_term()
        term807 = _t1418
        _t1419 = self.parse_term()
        term_3808 = _t1419
        self.consume_literal(")")
        _t1420 = logic_pb2.RelTerm(term=term807)
        _t1421 = logic_pb2.RelTerm(term=term_3808)
        _t1422 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1420, _t1421])
        result810 = _t1422
        self.record_span(span_start809, "Primitive")
        return result810

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start813 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1423 = self.parse_term()
        term811 = _t1423
        _t1424 = self.parse_term()
        term_3812 = _t1424
        self.consume_literal(")")
        _t1425 = logic_pb2.RelTerm(term=term811)
        _t1426 = logic_pb2.RelTerm(term=term_3812)
        _t1427 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1425, _t1426])
        result814 = _t1427
        self.record_span(span_start813, "Primitive")
        return result814

    def parse_add(self) -> logic_pb2.Primitive:
        span_start818 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1428 = self.parse_term()
        term815 = _t1428
        _t1429 = self.parse_term()
        term_3816 = _t1429
        _t1430 = self.parse_term()
        term_4817 = _t1430
        self.consume_literal(")")
        _t1431 = logic_pb2.RelTerm(term=term815)
        _t1432 = logic_pb2.RelTerm(term=term_3816)
        _t1433 = logic_pb2.RelTerm(term=term_4817)
        _t1434 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1431, _t1432, _t1433])
        result819 = _t1434
        self.record_span(span_start818, "Primitive")
        return result819

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start823 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1435 = self.parse_term()
        term820 = _t1435
        _t1436 = self.parse_term()
        term_3821 = _t1436
        _t1437 = self.parse_term()
        term_4822 = _t1437
        self.consume_literal(")")
        _t1438 = logic_pb2.RelTerm(term=term820)
        _t1439 = logic_pb2.RelTerm(term=term_3821)
        _t1440 = logic_pb2.RelTerm(term=term_4822)
        _t1441 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1438, _t1439, _t1440])
        result824 = _t1441
        self.record_span(span_start823, "Primitive")
        return result824

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start828 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1442 = self.parse_term()
        term825 = _t1442
        _t1443 = self.parse_term()
        term_3826 = _t1443
        _t1444 = self.parse_term()
        term_4827 = _t1444
        self.consume_literal(")")
        _t1445 = logic_pb2.RelTerm(term=term825)
        _t1446 = logic_pb2.RelTerm(term=term_3826)
        _t1447 = logic_pb2.RelTerm(term=term_4827)
        _t1448 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1445, _t1446, _t1447])
        result829 = _t1448
        self.record_span(span_start828, "Primitive")
        return result829

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start833 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1449 = self.parse_term()
        term830 = _t1449
        _t1450 = self.parse_term()
        term_3831 = _t1450
        _t1451 = self.parse_term()
        term_4832 = _t1451
        self.consume_literal(")")
        _t1452 = logic_pb2.RelTerm(term=term830)
        _t1453 = logic_pb2.RelTerm(term=term_3831)
        _t1454 = logic_pb2.RelTerm(term=term_4832)
        _t1455 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1452, _t1453, _t1454])
        result834 = _t1455
        self.record_span(span_start833, "Primitive")
        return result834

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start838 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1456 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1457 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1458 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1459 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1460 = 0
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1461 = 1
                            else:
                                if self.match_lookahead_terminal("SYMBOL", 0):
                                    _t1462 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1463 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1464 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1465 = 1
                                            else:
                                                if self.match_lookahead_terminal("FLOAT", 0):
                                                    _t1466 = 1
                                                else:
                                                    if self.match_lookahead_terminal("DECIMAL", 0):
                                                        _t1467 = 1
                                                    else:
                                                        _t1467 = -1
                                                    _t1466 = _t1467
                                                _t1465 = _t1466
                                            _t1464 = _t1465
                                        _t1463 = _t1464
                                    _t1462 = _t1463
                                _t1461 = _t1462
                            _t1460 = _t1461
                        _t1459 = _t1460
                    _t1458 = _t1459
                _t1457 = _t1458
            _t1456 = _t1457
        prediction835 = _t1456
        if prediction835 == 1:
            _t1469 = self.parse_term()
            term837 = _t1469
            _t1470 = logic_pb2.RelTerm(term=term837)
            _t1468 = _t1470
        else:
            if prediction835 == 0:
                _t1472 = self.parse_specialized_value()
                specialized_value836 = _t1472
                _t1473 = logic_pb2.RelTerm(specialized_value=specialized_value836)
                _t1471 = _t1473
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1468 = _t1471
        result839 = _t1468
        self.record_span(span_start838, "RelTerm")
        return result839

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start841 = self.span_start()
        self.consume_literal("#")
        _t1474 = self.parse_value()
        value840 = _t1474
        result842 = value840
        self.record_span(span_start841, "Value")
        return result842

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start848 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1475 = self.parse_name()
        name843 = _t1475
        xs844 = []
        cond845 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond845:
            _t1476 = self.parse_rel_term()
            item846 = _t1476
            xs844.append(item846)
            cond845 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        rel_terms847 = xs844
        self.consume_literal(")")
        _t1477 = logic_pb2.RelAtom(name=name843, terms=rel_terms847)
        result849 = _t1477
        self.record_span(span_start848, "RelAtom")
        return result849

    def parse_cast(self) -> logic_pb2.Cast:
        span_start852 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1478 = self.parse_term()
        term850 = _t1478
        _t1479 = self.parse_term()
        term_3851 = _t1479
        self.consume_literal(")")
        _t1480 = logic_pb2.Cast(input=term850, result=term_3851)
        result853 = _t1480
        self.record_span(span_start852, "Cast")
        return result853

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs854 = []
        cond855 = self.match_lookahead_literal("(", 0)
        while cond855:
            _t1481 = self.parse_attribute()
            item856 = _t1481
            xs854.append(item856)
            cond855 = self.match_lookahead_literal("(", 0)
        attributes857 = xs854
        self.consume_literal(")")
        return attributes857

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start863 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1482 = self.parse_name()
        name858 = _t1482
        xs859 = []
        cond860 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond860:
            _t1483 = self.parse_value()
            item861 = _t1483
            xs859.append(item861)
            cond860 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        values862 = xs859
        self.consume_literal(")")
        _t1484 = logic_pb2.Attribute(name=name858, args=values862)
        result864 = _t1484
        self.record_span(span_start863, "Attribute")
        return result864

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start870 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs865 = []
        cond866 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond866:
            _t1485 = self.parse_relation_id()
            item867 = _t1485
            xs865.append(item867)
            cond866 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids868 = xs865
        _t1486 = self.parse_script()
        script869 = _t1486
        self.consume_literal(")")
        _t1487 = logic_pb2.Algorithm(body=script869)
        getattr(_t1487, 'global').extend(relation_ids868)
        result871 = _t1487
        self.record_span(span_start870, "Algorithm")
        return result871

    def parse_script(self) -> logic_pb2.Script:
        span_start876 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs872 = []
        cond873 = self.match_lookahead_literal("(", 0)
        while cond873:
            _t1488 = self.parse_construct()
            item874 = _t1488
            xs872.append(item874)
            cond873 = self.match_lookahead_literal("(", 0)
        constructs875 = xs872
        self.consume_literal(")")
        _t1489 = logic_pb2.Script(constructs=constructs875)
        result877 = _t1489
        self.record_span(span_start876, "Script")
        return result877

    def parse_construct(self) -> logic_pb2.Construct:
        span_start881 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1491 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1492 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1493 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1494 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1495 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1496 = 1
                                else:
                                    _t1496 = -1
                                _t1495 = _t1496
                            _t1494 = _t1495
                        _t1493 = _t1494
                    _t1492 = _t1493
                _t1491 = _t1492
            _t1490 = _t1491
        else:
            _t1490 = -1
        prediction878 = _t1490
        if prediction878 == 1:
            _t1498 = self.parse_instruction()
            instruction880 = _t1498
            _t1499 = logic_pb2.Construct(instruction=instruction880)
            _t1497 = _t1499
        else:
            if prediction878 == 0:
                _t1501 = self.parse_loop()
                loop879 = _t1501
                _t1502 = logic_pb2.Construct(loop=loop879)
                _t1500 = _t1502
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1497 = _t1500
        result882 = _t1497
        self.record_span(span_start881, "Construct")
        return result882

    def parse_loop(self) -> logic_pb2.Loop:
        span_start885 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1503 = self.parse_init()
        init883 = _t1503
        _t1504 = self.parse_script()
        script884 = _t1504
        self.consume_literal(")")
        _t1505 = logic_pb2.Loop(init=init883, body=script884)
        result886 = _t1505
        self.record_span(span_start885, "Loop")
        return result886

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs887 = []
        cond888 = self.match_lookahead_literal("(", 0)
        while cond888:
            _t1506 = self.parse_instruction()
            item889 = _t1506
            xs887.append(item889)
            cond888 = self.match_lookahead_literal("(", 0)
        instructions890 = xs887
        self.consume_literal(")")
        return instructions890

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start897 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1508 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1509 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1510 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1511 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1512 = 0
                            else:
                                _t1512 = -1
                            _t1511 = _t1512
                        _t1510 = _t1511
                    _t1509 = _t1510
                _t1508 = _t1509
            _t1507 = _t1508
        else:
            _t1507 = -1
        prediction891 = _t1507
        if prediction891 == 4:
            _t1514 = self.parse_monus_def()
            monus_def896 = _t1514
            _t1515 = logic_pb2.Instruction(monus_def=monus_def896)
            _t1513 = _t1515
        else:
            if prediction891 == 3:
                _t1517 = self.parse_monoid_def()
                monoid_def895 = _t1517
                _t1518 = logic_pb2.Instruction(monoid_def=monoid_def895)
                _t1516 = _t1518
            else:
                if prediction891 == 2:
                    _t1520 = self.parse_break()
                    break894 = _t1520
                    _t1521 = logic_pb2.Instruction()
                    getattr(_t1521, 'break').CopyFrom(break894)
                    _t1519 = _t1521
                else:
                    if prediction891 == 1:
                        _t1523 = self.parse_upsert()
                        upsert893 = _t1523
                        _t1524 = logic_pb2.Instruction(upsert=upsert893)
                        _t1522 = _t1524
                    else:
                        if prediction891 == 0:
                            _t1526 = self.parse_assign()
                            assign892 = _t1526
                            _t1527 = logic_pb2.Instruction(assign=assign892)
                            _t1525 = _t1527
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1522 = _t1525
                    _t1519 = _t1522
                _t1516 = _t1519
            _t1513 = _t1516
        result898 = _t1513
        self.record_span(span_start897, "Instruction")
        return result898

    def parse_assign(self) -> logic_pb2.Assign:
        span_start902 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1528 = self.parse_relation_id()
        relation_id899 = _t1528
        _t1529 = self.parse_abstraction()
        abstraction900 = _t1529
        if self.match_lookahead_literal("(", 0):
            _t1531 = self.parse_attrs()
            _t1530 = _t1531
        else:
            _t1530 = None
        attrs901 = _t1530
        self.consume_literal(")")
        _t1532 = logic_pb2.Assign(name=relation_id899, body=abstraction900, attrs=(attrs901 if attrs901 is not None else []))
        result903 = _t1532
        self.record_span(span_start902, "Assign")
        return result903

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start907 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1533 = self.parse_relation_id()
        relation_id904 = _t1533
        _t1534 = self.parse_abstraction_with_arity()
        abstraction_with_arity905 = _t1534
        if self.match_lookahead_literal("(", 0):
            _t1536 = self.parse_attrs()
            _t1535 = _t1536
        else:
            _t1535 = None
        attrs906 = _t1535
        self.consume_literal(")")
        _t1537 = logic_pb2.Upsert(name=relation_id904, body=abstraction_with_arity905[0], attrs=(attrs906 if attrs906 is not None else []), value_arity=abstraction_with_arity905[1])
        result908 = _t1537
        self.record_span(span_start907, "Upsert")
        return result908

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1538 = self.parse_bindings()
        bindings909 = _t1538
        _t1539 = self.parse_formula()
        formula910 = _t1539
        self.consume_literal(")")
        _t1540 = logic_pb2.Abstraction(vars=(list(bindings909[0]) + list(bindings909[1] if bindings909[1] is not None else [])), value=formula910)
        return (_t1540, len(bindings909[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start914 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1541 = self.parse_relation_id()
        relation_id911 = _t1541
        _t1542 = self.parse_abstraction()
        abstraction912 = _t1542
        if self.match_lookahead_literal("(", 0):
            _t1544 = self.parse_attrs()
            _t1543 = _t1544
        else:
            _t1543 = None
        attrs913 = _t1543
        self.consume_literal(")")
        _t1545 = logic_pb2.Break(name=relation_id911, body=abstraction912, attrs=(attrs913 if attrs913 is not None else []))
        result915 = _t1545
        self.record_span(span_start914, "Break")
        return result915

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start920 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1546 = self.parse_monoid()
        monoid916 = _t1546
        _t1547 = self.parse_relation_id()
        relation_id917 = _t1547
        _t1548 = self.parse_abstraction_with_arity()
        abstraction_with_arity918 = _t1548
        if self.match_lookahead_literal("(", 0):
            _t1550 = self.parse_attrs()
            _t1549 = _t1550
        else:
            _t1549 = None
        attrs919 = _t1549
        self.consume_literal(")")
        _t1551 = logic_pb2.MonoidDef(monoid=monoid916, name=relation_id917, body=abstraction_with_arity918[0], attrs=(attrs919 if attrs919 is not None else []), value_arity=abstraction_with_arity918[1])
        result921 = _t1551
        self.record_span(span_start920, "MonoidDef")
        return result921

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start927 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1553 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1554 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1555 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1556 = 2
                        else:
                            _t1556 = -1
                        _t1555 = _t1556
                    _t1554 = _t1555
                _t1553 = _t1554
            _t1552 = _t1553
        else:
            _t1552 = -1
        prediction922 = _t1552
        if prediction922 == 3:
            _t1558 = self.parse_sum_monoid()
            sum_monoid926 = _t1558
            _t1559 = logic_pb2.Monoid(sum_monoid=sum_monoid926)
            _t1557 = _t1559
        else:
            if prediction922 == 2:
                _t1561 = self.parse_max_monoid()
                max_monoid925 = _t1561
                _t1562 = logic_pb2.Monoid(max_monoid=max_monoid925)
                _t1560 = _t1562
            else:
                if prediction922 == 1:
                    _t1564 = self.parse_min_monoid()
                    min_monoid924 = _t1564
                    _t1565 = logic_pb2.Monoid(min_monoid=min_monoid924)
                    _t1563 = _t1565
                else:
                    if prediction922 == 0:
                        _t1567 = self.parse_or_monoid()
                        or_monoid923 = _t1567
                        _t1568 = logic_pb2.Monoid(or_monoid=or_monoid923)
                        _t1566 = _t1568
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1563 = _t1566
                _t1560 = _t1563
            _t1557 = _t1560
        result928 = _t1557
        self.record_span(span_start927, "Monoid")
        return result928

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start929 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1569 = logic_pb2.OrMonoid()
        result930 = _t1569
        self.record_span(span_start929, "OrMonoid")
        return result930

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start932 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1570 = self.parse_type()
        type931 = _t1570
        self.consume_literal(")")
        _t1571 = logic_pb2.MinMonoid(type=type931)
        result933 = _t1571
        self.record_span(span_start932, "MinMonoid")
        return result933

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start935 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1572 = self.parse_type()
        type934 = _t1572
        self.consume_literal(")")
        _t1573 = logic_pb2.MaxMonoid(type=type934)
        result936 = _t1573
        self.record_span(span_start935, "MaxMonoid")
        return result936

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start938 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1574 = self.parse_type()
        type937 = _t1574
        self.consume_literal(")")
        _t1575 = logic_pb2.SumMonoid(type=type937)
        result939 = _t1575
        self.record_span(span_start938, "SumMonoid")
        return result939

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start944 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1576 = self.parse_monoid()
        monoid940 = _t1576
        _t1577 = self.parse_relation_id()
        relation_id941 = _t1577
        _t1578 = self.parse_abstraction_with_arity()
        abstraction_with_arity942 = _t1578
        if self.match_lookahead_literal("(", 0):
            _t1580 = self.parse_attrs()
            _t1579 = _t1580
        else:
            _t1579 = None
        attrs943 = _t1579
        self.consume_literal(")")
        _t1581 = logic_pb2.MonusDef(monoid=monoid940, name=relation_id941, body=abstraction_with_arity942[0], attrs=(attrs943 if attrs943 is not None else []), value_arity=abstraction_with_arity942[1])
        result945 = _t1581
        self.record_span(span_start944, "MonusDef")
        return result945

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start950 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1582 = self.parse_relation_id()
        relation_id946 = _t1582
        _t1583 = self.parse_abstraction()
        abstraction947 = _t1583
        _t1584 = self.parse_functional_dependency_keys()
        functional_dependency_keys948 = _t1584
        _t1585 = self.parse_functional_dependency_values()
        functional_dependency_values949 = _t1585
        self.consume_literal(")")
        _t1586 = logic_pb2.FunctionalDependency(guard=abstraction947, keys=functional_dependency_keys948, values=functional_dependency_values949)
        _t1587 = logic_pb2.Constraint(name=relation_id946, functional_dependency=_t1586)
        result951 = _t1587
        self.record_span(span_start950, "Constraint")
        return result951

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs952 = []
        cond953 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond953:
            _t1588 = self.parse_var()
            item954 = _t1588
            xs952.append(item954)
            cond953 = self.match_lookahead_terminal("SYMBOL", 0)
        vars955 = xs952
        self.consume_literal(")")
        return vars955

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs956 = []
        cond957 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond957:
            _t1589 = self.parse_var()
            item958 = _t1589
            xs956.append(item958)
            cond957 = self.match_lookahead_terminal("SYMBOL", 0)
        vars959 = xs956
        self.consume_literal(")")
        return vars959

    def parse_data(self) -> logic_pb2.Data:
        span_start964 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("rel_edb", 1):
                _t1591 = 0
            else:
                if self.match_lookahead_literal("csv_data", 1):
                    _t1592 = 2
                else:
                    if self.match_lookahead_literal("betree_relation", 1):
                        _t1593 = 1
                    else:
                        _t1593 = -1
                    _t1592 = _t1593
                _t1591 = _t1592
            _t1590 = _t1591
        else:
            _t1590 = -1
        prediction960 = _t1590
        if prediction960 == 2:
            _t1595 = self.parse_csv_data()
            csv_data963 = _t1595
            _t1596 = logic_pb2.Data(csv_data=csv_data963)
            _t1594 = _t1596
        else:
            if prediction960 == 1:
                _t1598 = self.parse_betree_relation()
                betree_relation962 = _t1598
                _t1599 = logic_pb2.Data(betree_relation=betree_relation962)
                _t1597 = _t1599
            else:
                if prediction960 == 0:
                    _t1601 = self.parse_rel_edb()
                    rel_edb961 = _t1601
                    _t1602 = logic_pb2.Data(rel_edb=rel_edb961)
                    _t1600 = _t1602
                else:
                    raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t1597 = _t1600
            _t1594 = _t1597
        result965 = _t1594
        self.record_span(span_start964, "Data")
        return result965

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        span_start969 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("rel_edb")
        _t1603 = self.parse_relation_id()
        relation_id966 = _t1603
        _t1604 = self.parse_rel_edb_path()
        rel_edb_path967 = _t1604
        _t1605 = self.parse_rel_edb_types()
        rel_edb_types968 = _t1605
        self.consume_literal(")")
        _t1606 = logic_pb2.RelEDB(target_id=relation_id966, path=rel_edb_path967, types=rel_edb_types968)
        result970 = _t1606
        self.record_span(span_start969, "RelEDB")
        return result970

    def parse_rel_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs971 = []
        cond972 = self.match_lookahead_terminal("STRING", 0)
        while cond972:
            item973 = self.consume_terminal("STRING")
            xs971.append(item973)
            cond972 = self.match_lookahead_terminal("STRING", 0)
        strings974 = xs971
        self.consume_literal("]")
        return strings974

    def parse_rel_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs975 = []
        cond976 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond976:
            _t1607 = self.parse_type()
            item977 = _t1607
            xs975.append(item977)
            cond976 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types978 = xs975
        self.consume_literal("]")
        return types978

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start981 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1608 = self.parse_relation_id()
        relation_id979 = _t1608
        _t1609 = self.parse_betree_info()
        betree_info980 = _t1609
        self.consume_literal(")")
        _t1610 = logic_pb2.BeTreeRelation(name=relation_id979, relation_info=betree_info980)
        result982 = _t1610
        self.record_span(span_start981, "BeTreeRelation")
        return result982

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start986 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1611 = self.parse_betree_info_key_types()
        betree_info_key_types983 = _t1611
        _t1612 = self.parse_betree_info_value_types()
        betree_info_value_types984 = _t1612
        _t1613 = self.parse_config_dict()
        config_dict985 = _t1613
        self.consume_literal(")")
        _t1614 = self.construct_betree_info(betree_info_key_types983, betree_info_value_types984, config_dict985)
        result987 = _t1614
        self.record_span(span_start986, "BeTreeInfo")
        return result987

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs988 = []
        cond989 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond989:
            _t1615 = self.parse_type()
            item990 = _t1615
            xs988.append(item990)
            cond989 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types991 = xs988
        self.consume_literal(")")
        return types991

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs992 = []
        cond993 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond993:
            _t1616 = self.parse_type()
            item994 = _t1616
            xs992.append(item994)
            cond993 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types995 = xs992
        self.consume_literal(")")
        return types995

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1000 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1617 = self.parse_csvlocator()
        csvlocator996 = _t1617
        _t1618 = self.parse_csv_config()
        csv_config997 = _t1618
        _t1619 = self.parse_csv_columns()
        csv_columns998 = _t1619
        _t1620 = self.parse_csv_asof()
        csv_asof999 = _t1620
        self.consume_literal(")")
        _t1621 = logic_pb2.CSVData(locator=csvlocator996, config=csv_config997, columns=csv_columns998, asof=csv_asof999)
        result1001 = _t1621
        self.record_span(span_start1000, "CSVData")
        return result1001

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1004 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1623 = self.parse_csv_locator_paths()
            _t1622 = _t1623
        else:
            _t1622 = None
        csv_locator_paths1002 = _t1622
        if self.match_lookahead_literal("(", 0):
            _t1625 = self.parse_csv_locator_inline_data()
            _t1624 = _t1625
        else:
            _t1624 = None
        csv_locator_inline_data1003 = _t1624
        self.consume_literal(")")
        _t1626 = logic_pb2.CSVLocator(paths=(csv_locator_paths1002 if csv_locator_paths1002 is not None else []), inline_data=(csv_locator_inline_data1003 if csv_locator_inline_data1003 is not None else "").encode())
        result1005 = _t1626
        self.record_span(span_start1004, "CSVLocator")
        return result1005

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1006 = []
        cond1007 = self.match_lookahead_terminal("STRING", 0)
        while cond1007:
            item1008 = self.consume_terminal("STRING")
            xs1006.append(item1008)
            cond1007 = self.match_lookahead_terminal("STRING", 0)
        strings1009 = xs1006
        self.consume_literal(")")
        return strings1009

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1010 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1010

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1012 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1627 = self.parse_config_dict()
        config_dict1011 = _t1627
        self.consume_literal(")")
        _t1628 = self.construct_csv_config(config_dict1011)
        result1013 = _t1628
        self.record_span(span_start1012, "CSVConfig")
        return result1013

    def parse_csv_columns(self) -> Sequence[logic_pb2.CSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1014 = []
        cond1015 = self.match_lookahead_literal("(", 0)
        while cond1015:
            _t1629 = self.parse_csv_column()
            item1016 = _t1629
            xs1014.append(item1016)
            cond1015 = self.match_lookahead_literal("(", 0)
        csv_columns1017 = xs1014
        self.consume_literal(")")
        return csv_columns1017

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        span_start1024 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1018 = self.consume_terminal("STRING")
        _t1630 = self.parse_relation_id()
        relation_id1019 = _t1630
        self.consume_literal("[")
        xs1020 = []
        cond1021 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1021:
            _t1631 = self.parse_type()
            item1022 = _t1631
            xs1020.append(item1022)
            cond1021 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1023 = xs1020
        self.consume_literal("]")
        self.consume_literal(")")
        _t1632 = logic_pb2.CSVColumn(column_name=string1018, target_id=relation_id1019, types=types1023)
        result1025 = _t1632
        self.record_span(span_start1024, "CSVColumn")
        return result1025

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1026 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1026

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1028 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1633 = self.parse_fragment_id()
        fragment_id1027 = _t1633
        self.consume_literal(")")
        _t1634 = transactions_pb2.Undefine(fragment_id=fragment_id1027)
        result1029 = _t1634
        self.record_span(span_start1028, "Undefine")
        return result1029

    def parse_context(self) -> transactions_pb2.Context:
        span_start1034 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1030 = []
        cond1031 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1031:
            _t1635 = self.parse_relation_id()
            item1032 = _t1635
            xs1030.append(item1032)
            cond1031 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1033 = xs1030
        self.consume_literal(")")
        _t1636 = transactions_pb2.Context(relations=relation_ids1033)
        result1035 = _t1636
        self.record_span(span_start1034, "Context")
        return result1035

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1038 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t1637 = self.parse_rel_edb_path()
        rel_edb_path1036 = _t1637
        _t1638 = self.parse_relation_id()
        relation_id1037 = _t1638
        self.consume_literal(")")
        _t1639 = transactions_pb2.Snapshot(destination_path=rel_edb_path1036, source_relation=relation_id1037)
        result1039 = _t1639
        self.record_span(span_start1038, "Snapshot")
        return result1039

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1040 = []
        cond1041 = self.match_lookahead_literal("(", 0)
        while cond1041:
            _t1640 = self.parse_read()
            item1042 = _t1640
            xs1040.append(item1042)
            cond1041 = self.match_lookahead_literal("(", 0)
        reads1043 = xs1040
        self.consume_literal(")")
        return reads1043

    def parse_read(self) -> transactions_pb2.Read:
        span_start1050 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1642 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1643 = 1
                else:
                    if self.match_lookahead_literal("export", 1):
                        _t1644 = 4
                    else:
                        if self.match_lookahead_literal("demand", 1):
                            _t1645 = 0
                        else:
                            if self.match_lookahead_literal("abort", 1):
                                _t1646 = 3
                            else:
                                _t1646 = -1
                            _t1645 = _t1646
                        _t1644 = _t1645
                    _t1643 = _t1644
                _t1642 = _t1643
            _t1641 = _t1642
        else:
            _t1641 = -1
        prediction1044 = _t1641
        if prediction1044 == 4:
            _t1648 = self.parse_export()
            export1049 = _t1648
            _t1649 = transactions_pb2.Read(export=export1049)
            _t1647 = _t1649
        else:
            if prediction1044 == 3:
                _t1651 = self.parse_abort()
                abort1048 = _t1651
                _t1652 = transactions_pb2.Read(abort=abort1048)
                _t1650 = _t1652
            else:
                if prediction1044 == 2:
                    _t1654 = self.parse_what_if()
                    what_if1047 = _t1654
                    _t1655 = transactions_pb2.Read(what_if=what_if1047)
                    _t1653 = _t1655
                else:
                    if prediction1044 == 1:
                        _t1657 = self.parse_output()
                        output1046 = _t1657
                        _t1658 = transactions_pb2.Read(output=output1046)
                        _t1656 = _t1658
                    else:
                        if prediction1044 == 0:
                            _t1660 = self.parse_demand()
                            demand1045 = _t1660
                            _t1661 = transactions_pb2.Read(demand=demand1045)
                            _t1659 = _t1661
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1656 = _t1659
                    _t1653 = _t1656
                _t1650 = _t1653
            _t1647 = _t1650
        result1051 = _t1647
        self.record_span(span_start1050, "Read")
        return result1051

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1053 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1662 = self.parse_relation_id()
        relation_id1052 = _t1662
        self.consume_literal(")")
        _t1663 = transactions_pb2.Demand(relation_id=relation_id1052)
        result1054 = _t1663
        self.record_span(span_start1053, "Demand")
        return result1054

    def parse_output(self) -> transactions_pb2.Output:
        span_start1057 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t1664 = self.parse_name()
        name1055 = _t1664
        _t1665 = self.parse_relation_id()
        relation_id1056 = _t1665
        self.consume_literal(")")
        _t1666 = transactions_pb2.Output(name=name1055, relation_id=relation_id1056)
        result1058 = _t1666
        self.record_span(span_start1057, "Output")
        return result1058

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1061 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t1667 = self.parse_name()
        name1059 = _t1667
        _t1668 = self.parse_epoch()
        epoch1060 = _t1668
        self.consume_literal(")")
        _t1669 = transactions_pb2.WhatIf(branch=name1059, epoch=epoch1060)
        result1062 = _t1669
        self.record_span(span_start1061, "WhatIf")
        return result1062

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1065 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t1671 = self.parse_name()
            _t1670 = _t1671
        else:
            _t1670 = None
        name1063 = _t1670
        _t1672 = self.parse_relation_id()
        relation_id1064 = _t1672
        self.consume_literal(")")
        _t1673 = transactions_pb2.Abort(name=(name1063 if name1063 is not None else "abort"), relation_id=relation_id1064)
        result1066 = _t1673
        self.record_span(span_start1065, "Abort")
        return result1066

    def parse_export(self) -> transactions_pb2.Export:
        span_start1068 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export")
        _t1674 = self.parse_export_csv_config()
        export_csv_config1067 = _t1674
        self.consume_literal(")")
        _t1675 = transactions_pb2.Export(csv_config=export_csv_config1067)
        result1069 = _t1675
        self.record_span(span_start1068, "Export")
        return result1069

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1073 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_csv_config")
        _t1676 = self.parse_export_csv_path()
        export_csv_path1070 = _t1676
        _t1677 = self.parse_export_csv_columns()
        export_csv_columns1071 = _t1677
        _t1678 = self.parse_config_dict()
        config_dict1072 = _t1678
        self.consume_literal(")")
        _t1679 = self.export_csv_config(export_csv_path1070, export_csv_columns1071, config_dict1072)
        result1074 = _t1679
        self.record_span(span_start1073, "ExportCSVConfig")
        return result1074

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1075 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1075

    def parse_export_csv_columns(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1076 = []
        cond1077 = self.match_lookahead_literal("(", 0)
        while cond1077:
            _t1680 = self.parse_export_csv_column()
            item1078 = _t1680
            xs1076.append(item1078)
            cond1077 = self.match_lookahead_literal("(", 0)
        export_csv_columns1079 = xs1076
        self.consume_literal(")")
        return export_csv_columns1079

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1082 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1080 = self.consume_terminal("STRING")
        _t1681 = self.parse_relation_id()
        relation_id1081 = _t1681
        self.consume_literal(")")
        _t1682 = transactions_pb2.ExportCSVColumn(column_name=string1080, column_data=relation_id1081)
        result1083 = _t1682
        self.record_span(span_start1082, "ExportCSVColumn")
        return result1083


def parse(input_str: str) -> tuple[Any, dict[int, Span]]:
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
