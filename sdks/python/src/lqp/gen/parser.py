"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `meta/` or edit the protobuf specification in `proto/v1`.


Command: python -m meta.cli ../proto/relationalai/lqp/v1/fragments.proto ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto --grammar src/meta/grammar.y --parser python
"""

import ast
import hashlib
import re
from collections.abc import Sequence
from typing import List, Optional, Any, Tuple, Callable
from decimal import Decimal

from lqp.proto.v1 import logic_pb2, fragments_pb2, transactions_pb2


class ParseError(Exception):
    """Parse error exception."""

    pass


class Token:
    """Token representation."""

    def __init__(self, type: str, value: str, pos: int):
        self.type = type
        self.value = value
        self.pos = pos

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value!r}, {self.pos})"


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
        self.tokens: List[Token] = []
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
            self.tokens.append(Token(token_type, action(value), self.pos))
            self.pos = end_pos

        self.tokens.append(Token("$", "", self.pos))

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


class Parser:
    """LL(k) recursive-descent parser with backtracking."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.id_to_debuginfo = {}
        self._current_fragment_id: bytes | None = None
        self._relation_id_to_name = {}

    def lookahead(self, k: int = 0) -> Token:
        """Get lookahead token at offset k."""
        idx = self.pos + k
        return self.tokens[idx] if idx < len(self.tokens) else Token("$", "", -1)

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
        declarations: List[logic_pb2.Declaration],
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

    def _extract_value_int32(self, value: Optional[logic_pb2.Value], default: int) -> int:
        if value is not None:
            assert value is not None
            _t1329 = value.HasField("int_value")
        else:
            _t1329 = False
        if _t1329:
            assert value is not None
            return int(value.int_value)
        else:
            _t1330 = None
        return int(default)

    def _extract_value_int64(self, value: Optional[logic_pb2.Value], default: int) -> int:
        if value is not None:
            assert value is not None
            _t1331 = value.HasField("int_value")
        else:
            _t1331 = False
        if _t1331:
            assert value is not None
            return value.int_value
        else:
            _t1332 = None
        return default

    def _extract_value_string(self, value: Optional[logic_pb2.Value], default: str) -> str:
        if value is not None:
            assert value is not None
            _t1333 = value.HasField("string_value")
        else:
            _t1333 = False
        if _t1333:
            assert value is not None
            return value.string_value
        else:
            _t1334 = None
        return default

    def _extract_value_boolean(self, value: Optional[logic_pb2.Value], default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t1335 = value.HasField("boolean_value")
        else:
            _t1335 = False
        if _t1335:
            assert value is not None
            return value.boolean_value
        else:
            _t1336 = None
        return default

    def _extract_value_string_list(self, value: Optional[logic_pb2.Value], default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t1337 = value.HasField("string_value")
        else:
            _t1337 = False
        if _t1337:
            assert value is not None
            return [value.string_value]
        else:
            _t1338 = None
        return default

    def _try_extract_value_int64(self, value: Optional[logic_pb2.Value]) -> Optional[int]:
        if value is not None:
            assert value is not None
            _t1339 = value.HasField("int_value")
        else:
            _t1339 = False
        if _t1339:
            assert value is not None
            return value.int_value
        else:
            _t1340 = None
        return None

    def _try_extract_value_float64(self, value: Optional[logic_pb2.Value]) -> Optional[float]:
        if value is not None:
            assert value is not None
            _t1341 = value.HasField("float_value")
        else:
            _t1341 = False
        if _t1341:
            assert value is not None
            return value.float_value
        else:
            _t1342 = None
        return None

    def _try_extract_value_bytes(self, value: Optional[logic_pb2.Value]) -> Optional[bytes]:
        if value is not None:
            assert value is not None
            _t1343 = value.HasField("string_value")
        else:
            _t1343 = False
        if _t1343:
            assert value is not None
            return value.string_value.encode()
        else:
            _t1344 = None
        return None

    def _try_extract_value_uint128(self, value: Optional[logic_pb2.Value]) -> Optional[logic_pb2.UInt128Value]:
        if value is not None:
            assert value is not None
            _t1345 = value.HasField("uint128_value")
        else:
            _t1345 = False
        if _t1345:
            assert value is not None
            return value.uint128_value
        else:
            _t1346 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1347 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t1347
        _t1348 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t1348
        _t1349 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t1349
        _t1350 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t1350
        _t1351 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t1351
        _t1352 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t1352
        _t1353 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t1353
        _t1354 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t1354
        _t1355 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t1355
        _t1356 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t1356
        _t1357 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t1357
        _t1358 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t1358

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1359 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t1359
        _t1360 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t1360
        _t1361 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t1361
        _t1362 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t1362
        _t1363 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1363
        _t1364 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t1364
        _t1365 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t1365
        _t1366 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t1366
        _t1367 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t1367
        _t1368 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1368
        _t1369 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1369

    def default_configure(self) -> transactions_pb2.Configure:
        _t1370 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1370
        _t1371 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1371

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
        _t1372 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1372
        _t1373 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t1373
        _t1374 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1374

    def export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1375 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t1375
        _t1376 = self._extract_value_string(config.get("compression"), "")
        compression = _t1376
        _t1377 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t1377
        _t1378 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t1378
        _t1379 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t1379
        _t1380 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t1380
        _t1381 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t1381
        _t1382 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1382

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t725 = self.parse_configure()
            _t724 = _t725
        else:
            _t724 = None
        configure362 = _t724
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t727 = self.parse_sync()
            _t726 = _t727
        else:
            _t726 = None
        sync363 = _t726
        xs364 = []
        cond365 = self.match_lookahead_literal("(", 0)
        while cond365:
            _t728 = self.parse_epoch()
            item366 = _t728
            xs364.append(item366)
            cond365 = self.match_lookahead_literal("(", 0)
        epochs367 = xs364
        self.consume_literal(")")
        _t729 = self.default_configure()
        _t730 = transactions_pb2.Transaction(epochs=epochs367, configure=(configure362 if configure362 is not None else _t729), sync=sync363)
        return _t730

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal("(")
        self.consume_literal("configure")
        _t731 = self.parse_config_dict()
        config_dict368 = _t731
        self.consume_literal(")")
        _t732 = self.construct_configure(config_dict368)
        return _t732

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs369 = []
        cond370 = self.match_lookahead_literal(":", 0)
        while cond370:
            _t733 = self.parse_config_key_value()
            item371 = _t733
            xs369.append(item371)
            cond370 = self.match_lookahead_literal(":", 0)
        config_key_values372 = xs369
        self.consume_literal("}")
        return config_key_values372

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol373 = self.consume_terminal("SYMBOL")
        _t734 = self.parse_value()
        value374 = _t734
        return (symbol373, value374,)

    def parse_value(self) -> logic_pb2.Value:
        if self.match_lookahead_literal("true", 0):
            _t735 = 9
        else:
            if self.match_lookahead_literal("missing", 0):
                _t736 = 8
            else:
                if self.match_lookahead_literal("false", 0):
                    _t737 = 9
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t739 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t740 = 0
                            else:
                                _t740 = -1
                            _t739 = _t740
                        _t738 = _t739
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t741 = 5
                        else:
                            if self.match_lookahead_terminal("STRING", 0):
                                _t742 = 2
                            else:
                                if self.match_lookahead_terminal("INT128", 0):
                                    _t743 = 6
                                else:
                                    if self.match_lookahead_terminal("INT", 0):
                                        _t744 = 3
                                    else:
                                        if self.match_lookahead_terminal("FLOAT", 0):
                                            _t745 = 4
                                        else:
                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                _t746 = 7
                                            else:
                                                _t746 = -1
                                            _t745 = _t746
                                        _t744 = _t745
                                    _t743 = _t744
                                _t742 = _t743
                            _t741 = _t742
                        _t738 = _t741
                    _t737 = _t738
                _t736 = _t737
            _t735 = _t736
        prediction375 = _t735
        if prediction375 == 9:
            _t748 = self.parse_boolean_value()
            boolean_value384 = _t748
            _t749 = logic_pb2.Value(boolean_value=boolean_value384)
            _t747 = _t749
        else:
            if prediction375 == 8:
                self.consume_literal("missing")
                _t751 = logic_pb2.MissingValue()
                _t752 = logic_pb2.Value(missing_value=_t751)
                _t750 = _t752
            else:
                if prediction375 == 7:
                    decimal383 = self.consume_terminal("DECIMAL")
                    _t754 = logic_pb2.Value(decimal_value=decimal383)
                    _t753 = _t754
                else:
                    if prediction375 == 6:
                        int128382 = self.consume_terminal("INT128")
                        _t756 = logic_pb2.Value(int128_value=int128382)
                        _t755 = _t756
                    else:
                        if prediction375 == 5:
                            uint128381 = self.consume_terminal("UINT128")
                            _t758 = logic_pb2.Value(uint128_value=uint128381)
                            _t757 = _t758
                        else:
                            if prediction375 == 4:
                                float380 = self.consume_terminal("FLOAT")
                                _t760 = logic_pb2.Value(float_value=float380)
                                _t759 = _t760
                            else:
                                if prediction375 == 3:
                                    int379 = self.consume_terminal("INT")
                                    _t762 = logic_pb2.Value(int_value=int379)
                                    _t761 = _t762
                                else:
                                    if prediction375 == 2:
                                        string378 = self.consume_terminal("STRING")
                                        _t764 = logic_pb2.Value(string_value=string378)
                                        _t763 = _t764
                                    else:
                                        if prediction375 == 1:
                                            _t766 = self.parse_datetime()
                                            datetime377 = _t766
                                            _t767 = logic_pb2.Value(datetime_value=datetime377)
                                            _t765 = _t767
                                        else:
                                            if prediction375 == 0:
                                                _t769 = self.parse_date()
                                                date376 = _t769
                                                _t770 = logic_pb2.Value(date_value=date376)
                                                _t768 = _t770
                                            else:
                                                raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t765 = _t768
                                        _t763 = _t765
                                    _t761 = _t763
                                _t759 = _t761
                            _t757 = _t759
                        _t755 = _t757
                    _t753 = _t755
                _t750 = _t753
            _t747 = _t750
        return _t747

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal("(")
        self.consume_literal("date")
        int385 = self.consume_terminal("INT")
        int_3386 = self.consume_terminal("INT")
        int_4387 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t771 = logic_pb2.DateValue(year=int(int385), month=int(int_3386), day=int(int_4387))
        return _t771

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        self.consume_literal("(")
        self.consume_literal("datetime")
        int388 = self.consume_terminal("INT")
        int_3389 = self.consume_terminal("INT")
        int_4390 = self.consume_terminal("INT")
        int_5391 = self.consume_terminal("INT")
        int_6392 = self.consume_terminal("INT")
        int_7393 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t772 = self.consume_terminal("INT")
        else:
            _t772 = None
        int_8394 = _t772
        self.consume_literal(")")
        _t773 = logic_pb2.DateTimeValue(year=int(int388), month=int(int_3389), day=int(int_4390), hour=int(int_5391), minute=int(int_6392), second=int(int_7393), microsecond=int((int_8394 if int_8394 is not None else 0)))
        return _t773

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t774 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t775 = 1
            else:
                _t775 = -1
            _t774 = _t775
        prediction395 = _t774
        if prediction395 == 1:
            self.consume_literal("false")
            _t776 = False
        else:
            if prediction395 == 0:
                self.consume_literal("true")
                _t777 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t776 = _t777
        return _t776

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal("(")
        self.consume_literal("sync")
        xs396 = []
        cond397 = self.match_lookahead_literal(":", 0)
        while cond397:
            _t778 = self.parse_fragment_id()
            item398 = _t778
            xs396.append(item398)
            cond397 = self.match_lookahead_literal(":", 0)
        fragment_ids399 = xs396
        self.consume_literal(")")
        _t779 = transactions_pb2.Sync(fragments=fragment_ids399)
        return _t779

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        self.consume_literal(":")
        symbol400 = self.consume_terminal("SYMBOL")
        return fragments_pb2.FragmentId(id=symbol400.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t781 = self.parse_epoch_writes()
            _t780 = _t781
        else:
            _t780 = None
        epoch_writes401 = _t780
        if self.match_lookahead_literal("(", 0):
            _t783 = self.parse_epoch_reads()
            _t782 = _t783
        else:
            _t782 = None
        epoch_reads402 = _t782
        self.consume_literal(")")
        _t784 = transactions_pb2.Epoch(writes=(epoch_writes401 if epoch_writes401 is not None else []), reads=(epoch_reads402 if epoch_reads402 is not None else []))
        return _t784

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs403 = []
        cond404 = self.match_lookahead_literal("(", 0)
        while cond404:
            _t785 = self.parse_write()
            item405 = _t785
            xs403.append(item405)
            cond404 = self.match_lookahead_literal("(", 0)
        writes406 = xs403
        self.consume_literal(")")
        return writes406

    def parse_write(self) -> transactions_pb2.Write:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t787 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t788 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t789 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t790 = 2
                        else:
                            _t790 = -1
                        _t789 = _t790
                    _t788 = _t789
                _t787 = _t788
            _t786 = _t787
        else:
            _t786 = -1
        prediction407 = _t786
        if prediction407 == 3:
            _t792 = self.parse_snapshot()
            snapshot411 = _t792
            _t793 = transactions_pb2.Write(snapshot=snapshot411)
            _t791 = _t793
        else:
            if prediction407 == 2:
                _t795 = self.parse_context()
                context410 = _t795
                _t796 = transactions_pb2.Write(context=context410)
                _t794 = _t796
            else:
                if prediction407 == 1:
                    _t798 = self.parse_undefine()
                    undefine409 = _t798
                    _t799 = transactions_pb2.Write(undefine=undefine409)
                    _t797 = _t799
                else:
                    if prediction407 == 0:
                        _t801 = self.parse_define()
                        define408 = _t801
                        _t802 = transactions_pb2.Write(define=define408)
                        _t800 = _t802
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t797 = _t800
                _t794 = _t797
            _t791 = _t794
        return _t791

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal("(")
        self.consume_literal("define")
        _t803 = self.parse_fragment()
        fragment412 = _t803
        self.consume_literal(")")
        _t804 = transactions_pb2.Define(fragment=fragment412)
        return _t804

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t805 = self.parse_new_fragment_id()
        new_fragment_id413 = _t805
        xs414 = []
        cond415 = self.match_lookahead_literal("(", 0)
        while cond415:
            _t806 = self.parse_declaration()
            item416 = _t806
            xs414.append(item416)
            cond415 = self.match_lookahead_literal("(", 0)
        declarations417 = xs414
        self.consume_literal(")")
        return self.construct_fragment(new_fragment_id413, declarations417)

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        _t807 = self.parse_fragment_id()
        fragment_id418 = _t807
        self.start_fragment(fragment_id418)
        return fragment_id418

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("functional_dependency", 1):
                _t809 = 2
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t810 = 3
                else:
                    if self.match_lookahead_literal("def", 1):
                        _t811 = 0
                    else:
                        if self.match_lookahead_literal("csv_data", 1):
                            _t812 = 3
                        else:
                            if self.match_lookahead_literal("betree_relation", 1):
                                _t813 = 3
                            else:
                                if self.match_lookahead_literal("algorithm", 1):
                                    _t814 = 1
                                else:
                                    _t814 = -1
                                _t813 = _t814
                            _t812 = _t813
                        _t811 = _t812
                    _t810 = _t811
                _t809 = _t810
            _t808 = _t809
        else:
            _t808 = -1
        prediction419 = _t808
        if prediction419 == 3:
            _t816 = self.parse_data()
            data423 = _t816
            _t817 = logic_pb2.Declaration(data=data423)
            _t815 = _t817
        else:
            if prediction419 == 2:
                _t819 = self.parse_constraint()
                constraint422 = _t819
                _t820 = logic_pb2.Declaration(constraint=constraint422)
                _t818 = _t820
            else:
                if prediction419 == 1:
                    _t822 = self.parse_algorithm()
                    algorithm421 = _t822
                    _t823 = logic_pb2.Declaration(algorithm=algorithm421)
                    _t821 = _t823
                else:
                    if prediction419 == 0:
                        _t825 = self.parse_def()
                        def420 = _t825
                        _t826 = logic_pb2.Declaration()
                        getattr(_t826, 'def').CopyFrom(def420)
                        _t824 = _t826
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t821 = _t824
                _t818 = _t821
            _t815 = _t818
        return _t815

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal("(")
        self.consume_literal("def")
        _t827 = self.parse_relation_id()
        relation_id424 = _t827
        _t828 = self.parse_abstraction()
        abstraction425 = _t828
        if self.match_lookahead_literal("(", 0):
            _t830 = self.parse_attrs()
            _t829 = _t830
        else:
            _t829 = None
        attrs426 = _t829
        self.consume_literal(")")
        _t831 = logic_pb2.Def(name=relation_id424, body=abstraction425, attrs=(attrs426 if attrs426 is not None else []))
        return _t831

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_literal(":", 0):
            _t832 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t833 = 1
            else:
                _t833 = -1
            _t832 = _t833
        prediction427 = _t832
        if prediction427 == 1:
            uint128429 = self.consume_terminal("UINT128")
            _t834 = logic_pb2.RelationId(id_low=uint128429.low, id_high=uint128429.high)
        else:
            if prediction427 == 0:
                self.consume_literal(":")
                symbol428 = self.consume_terminal("SYMBOL")
                _t835 = self.relation_id_from_string(symbol428)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t834 = _t835
        return _t834

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal("(")
        _t836 = self.parse_bindings()
        bindings430 = _t836
        _t837 = self.parse_formula()
        formula431 = _t837
        self.consume_literal(")")
        _t838 = logic_pb2.Abstraction(vars=(list(bindings430[0]) + list(bindings430[1] if bindings430[1] is not None else [])), value=formula431)
        return _t838

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs432 = []
        cond433 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond433:
            _t839 = self.parse_binding()
            item434 = _t839
            xs432.append(item434)
            cond433 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings435 = xs432
        if self.match_lookahead_literal("|", 0):
            _t841 = self.parse_value_bindings()
            _t840 = _t841
        else:
            _t840 = None
        value_bindings436 = _t840
        self.consume_literal("]")
        return (bindings435, (value_bindings436 if value_bindings436 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol437 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t842 = self.parse_type()
        type438 = _t842
        _t843 = logic_pb2.Var(name=symbol437)
        _t844 = logic_pb2.Binding(var=_t843, type=type438)
        return _t844

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t845 = 0
        else:
            if self.match_lookahead_literal("UINT128", 0):
                _t846 = 4
            else:
                if self.match_lookahead_literal("STRING", 0):
                    _t847 = 1
                else:
                    if self.match_lookahead_literal("MISSING", 0):
                        _t848 = 8
                    else:
                        if self.match_lookahead_literal("INT128", 0):
                            _t849 = 5
                        else:
                            if self.match_lookahead_literal("INT", 0):
                                _t850 = 2
                            else:
                                if self.match_lookahead_literal("FLOAT", 0):
                                    _t851 = 3
                                else:
                                    if self.match_lookahead_literal("DATETIME", 0):
                                        _t852 = 7
                                    else:
                                        if self.match_lookahead_literal("DATE", 0):
                                            _t853 = 6
                                        else:
                                            if self.match_lookahead_literal("BOOLEAN", 0):
                                                _t854 = 10
                                            else:
                                                if self.match_lookahead_literal("(", 0):
                                                    _t855 = 9
                                                else:
                                                    _t855 = -1
                                                _t854 = _t855
                                            _t853 = _t854
                                        _t852 = _t853
                                    _t851 = _t852
                                _t850 = _t851
                            _t849 = _t850
                        _t848 = _t849
                    _t847 = _t848
                _t846 = _t847
            _t845 = _t846
        prediction439 = _t845
        if prediction439 == 10:
            _t857 = self.parse_boolean_type()
            boolean_type450 = _t857
            _t858 = logic_pb2.Type(boolean_type=boolean_type450)
            _t856 = _t858
        else:
            if prediction439 == 9:
                _t860 = self.parse_decimal_type()
                decimal_type449 = _t860
                _t861 = logic_pb2.Type(decimal_type=decimal_type449)
                _t859 = _t861
            else:
                if prediction439 == 8:
                    _t863 = self.parse_missing_type()
                    missing_type448 = _t863
                    _t864 = logic_pb2.Type(missing_type=missing_type448)
                    _t862 = _t864
                else:
                    if prediction439 == 7:
                        _t866 = self.parse_datetime_type()
                        datetime_type447 = _t866
                        _t867 = logic_pb2.Type(datetime_type=datetime_type447)
                        _t865 = _t867
                    else:
                        if prediction439 == 6:
                            _t869 = self.parse_date_type()
                            date_type446 = _t869
                            _t870 = logic_pb2.Type(date_type=date_type446)
                            _t868 = _t870
                        else:
                            if prediction439 == 5:
                                _t872 = self.parse_int128_type()
                                int128_type445 = _t872
                                _t873 = logic_pb2.Type(int128_type=int128_type445)
                                _t871 = _t873
                            else:
                                if prediction439 == 4:
                                    _t875 = self.parse_uint128_type()
                                    uint128_type444 = _t875
                                    _t876 = logic_pb2.Type(uint128_type=uint128_type444)
                                    _t874 = _t876
                                else:
                                    if prediction439 == 3:
                                        _t878 = self.parse_float_type()
                                        float_type443 = _t878
                                        _t879 = logic_pb2.Type(float_type=float_type443)
                                        _t877 = _t879
                                    else:
                                        if prediction439 == 2:
                                            _t881 = self.parse_int_type()
                                            int_type442 = _t881
                                            _t882 = logic_pb2.Type(int_type=int_type442)
                                            _t880 = _t882
                                        else:
                                            if prediction439 == 1:
                                                _t884 = self.parse_string_type()
                                                string_type441 = _t884
                                                _t885 = logic_pb2.Type(string_type=string_type441)
                                                _t883 = _t885
                                            else:
                                                if prediction439 == 0:
                                                    _t887 = self.parse_unspecified_type()
                                                    unspecified_type440 = _t887
                                                    _t888 = logic_pb2.Type(unspecified_type=unspecified_type440)
                                                    _t886 = _t888
                                                else:
                                                    raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t883 = _t886
                                            _t880 = _t883
                                        _t877 = _t880
                                    _t874 = _t877
                                _t871 = _t874
                            _t868 = _t871
                        _t865 = _t868
                    _t862 = _t865
                _t859 = _t862
            _t856 = _t859
        return _t856

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        self.consume_literal("UNKNOWN")
        _t889 = logic_pb2.UnspecifiedType()
        return _t889

    def parse_string_type(self) -> logic_pb2.StringType:
        self.consume_literal("STRING")
        _t890 = logic_pb2.StringType()
        return _t890

    def parse_int_type(self) -> logic_pb2.IntType:
        self.consume_literal("INT")
        _t891 = logic_pb2.IntType()
        return _t891

    def parse_float_type(self) -> logic_pb2.FloatType:
        self.consume_literal("FLOAT")
        _t892 = logic_pb2.FloatType()
        return _t892

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        self.consume_literal("UINT128")
        _t893 = logic_pb2.UInt128Type()
        return _t893

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        self.consume_literal("INT128")
        _t894 = logic_pb2.Int128Type()
        return _t894

    def parse_date_type(self) -> logic_pb2.DateType:
        self.consume_literal("DATE")
        _t895 = logic_pb2.DateType()
        return _t895

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        self.consume_literal("DATETIME")
        _t896 = logic_pb2.DateTimeType()
        return _t896

    def parse_missing_type(self) -> logic_pb2.MissingType:
        self.consume_literal("MISSING")
        _t897 = logic_pb2.MissingType()
        return _t897

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int451 = self.consume_terminal("INT")
        int_3452 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t898 = logic_pb2.DecimalType(precision=int(int451), scale=int(int_3452))
        return _t898

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal("BOOLEAN")
        _t899 = logic_pb2.BooleanType()
        return _t899

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs453 = []
        cond454 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond454:
            _t900 = self.parse_binding()
            item455 = _t900
            xs453.append(item455)
            cond454 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings456 = xs453
        return bindings456

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t902 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t903 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t904 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t905 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t906 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t907 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t908 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t909 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t910 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t911 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t912 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t913 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t914 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t915 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t916 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t917 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t918 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t919 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t920 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t921 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t922 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t923 = 10
                                                                                                else:
                                                                                                    _t923 = -1
                                                                                                _t922 = _t923
                                                                                            _t921 = _t922
                                                                                        _t920 = _t921
                                                                                    _t919 = _t920
                                                                                _t918 = _t919
                                                                            _t917 = _t918
                                                                        _t916 = _t917
                                                                    _t915 = _t916
                                                                _t914 = _t915
                                                            _t913 = _t914
                                                        _t912 = _t913
                                                    _t911 = _t912
                                                _t910 = _t911
                                            _t909 = _t910
                                        _t908 = _t909
                                    _t907 = _t908
                                _t906 = _t907
                            _t905 = _t906
                        _t904 = _t905
                    _t903 = _t904
                _t902 = _t903
            _t901 = _t902
        else:
            _t901 = -1
        prediction457 = _t901
        if prediction457 == 12:
            _t925 = self.parse_cast()
            cast470 = _t925
            _t926 = logic_pb2.Formula(cast=cast470)
            _t924 = _t926
        else:
            if prediction457 == 11:
                _t928 = self.parse_rel_atom()
                rel_atom469 = _t928
                _t929 = logic_pb2.Formula(rel_atom=rel_atom469)
                _t927 = _t929
            else:
                if prediction457 == 10:
                    _t931 = self.parse_primitive()
                    primitive468 = _t931
                    _t932 = logic_pb2.Formula(primitive=primitive468)
                    _t930 = _t932
                else:
                    if prediction457 == 9:
                        _t934 = self.parse_pragma()
                        pragma467 = _t934
                        _t935 = logic_pb2.Formula(pragma=pragma467)
                        _t933 = _t935
                    else:
                        if prediction457 == 8:
                            _t937 = self.parse_atom()
                            atom466 = _t937
                            _t938 = logic_pb2.Formula(atom=atom466)
                            _t936 = _t938
                        else:
                            if prediction457 == 7:
                                _t940 = self.parse_ffi()
                                ffi465 = _t940
                                _t941 = logic_pb2.Formula(ffi=ffi465)
                                _t939 = _t941
                            else:
                                if prediction457 == 6:
                                    _t943 = self.parse_not()
                                    not464 = _t943
                                    _t944 = logic_pb2.Formula()
                                    getattr(_t944, 'not').CopyFrom(not464)
                                    _t942 = _t944
                                else:
                                    if prediction457 == 5:
                                        _t946 = self.parse_disjunction()
                                        disjunction463 = _t946
                                        _t947 = logic_pb2.Formula(disjunction=disjunction463)
                                        _t945 = _t947
                                    else:
                                        if prediction457 == 4:
                                            _t949 = self.parse_conjunction()
                                            conjunction462 = _t949
                                            _t950 = logic_pb2.Formula(conjunction=conjunction462)
                                            _t948 = _t950
                                        else:
                                            if prediction457 == 3:
                                                _t952 = self.parse_reduce()
                                                reduce461 = _t952
                                                _t953 = logic_pb2.Formula(reduce=reduce461)
                                                _t951 = _t953
                                            else:
                                                if prediction457 == 2:
                                                    _t955 = self.parse_exists()
                                                    exists460 = _t955
                                                    _t956 = logic_pb2.Formula(exists=exists460)
                                                    _t954 = _t956
                                                else:
                                                    if prediction457 == 1:
                                                        _t958 = self.parse_false()
                                                        false459 = _t958
                                                        _t959 = logic_pb2.Formula(disjunction=false459)
                                                        _t957 = _t959
                                                    else:
                                                        if prediction457 == 0:
                                                            _t961 = self.parse_true()
                                                            true458 = _t961
                                                            _t962 = logic_pb2.Formula(conjunction=true458)
                                                            _t960 = _t962
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t957 = _t960
                                                    _t954 = _t957
                                                _t951 = _t954
                                            _t948 = _t951
                                        _t945 = _t948
                                    _t942 = _t945
                                _t939 = _t942
                            _t936 = _t939
                        _t933 = _t936
                    _t930 = _t933
                _t927 = _t930
            _t924 = _t927
        return _t924

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t963 = logic_pb2.Conjunction(args=[])
        return _t963

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t964 = logic_pb2.Disjunction(args=[])
        return _t964

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal("(")
        self.consume_literal("exists")
        _t965 = self.parse_bindings()
        bindings471 = _t965
        _t966 = self.parse_formula()
        formula472 = _t966
        self.consume_literal(")")
        _t967 = logic_pb2.Abstraction(vars=(list(bindings471[0]) + list(bindings471[1] if bindings471[1] is not None else [])), value=formula472)
        _t968 = logic_pb2.Exists(body=_t967)
        return _t968

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t969 = self.parse_abstraction()
        abstraction473 = _t969
        _t970 = self.parse_abstraction()
        abstraction_3474 = _t970
        _t971 = self.parse_terms()
        terms475 = _t971
        self.consume_literal(")")
        _t972 = logic_pb2.Reduce(op=abstraction473, body=abstraction_3474, terms=terms475)
        return _t972

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs476 = []
        cond477 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond477:
            _t973 = self.parse_term()
            item478 = _t973
            xs476.append(item478)
            cond477 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms479 = xs476
        self.consume_literal(")")
        return terms479

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_literal("true", 0):
            _t974 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t975 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t976 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t977 = 1
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t978 = 1
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t979 = 0
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t980 = 1
                                else:
                                    if self.match_lookahead_terminal("INT128", 0):
                                        _t981 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT", 0):
                                            _t982 = 1
                                        else:
                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                _t983 = 1
                                            else:
                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                    _t984 = 1
                                                else:
                                                    _t984 = -1
                                                _t983 = _t984
                                            _t982 = _t983
                                        _t981 = _t982
                                    _t980 = _t981
                                _t979 = _t980
                            _t978 = _t979
                        _t977 = _t978
                    _t976 = _t977
                _t975 = _t976
            _t974 = _t975
        prediction480 = _t974
        if prediction480 == 1:
            _t986 = self.parse_constant()
            constant482 = _t986
            _t987 = logic_pb2.Term(constant=constant482)
            _t985 = _t987
        else:
            if prediction480 == 0:
                _t989 = self.parse_var()
                var481 = _t989
                _t990 = logic_pb2.Term(var=var481)
                _t988 = _t990
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t985 = _t988
        return _t985

    def parse_var(self) -> logic_pb2.Var:
        symbol483 = self.consume_terminal("SYMBOL")
        _t991 = logic_pb2.Var(name=symbol483)
        return _t991

    def parse_constant(self) -> logic_pb2.Value:
        _t992 = self.parse_value()
        value484 = _t992
        return value484

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal("(")
        self.consume_literal("and")
        xs485 = []
        cond486 = self.match_lookahead_literal("(", 0)
        while cond486:
            _t993 = self.parse_formula()
            item487 = _t993
            xs485.append(item487)
            cond486 = self.match_lookahead_literal("(", 0)
        formulas488 = xs485
        self.consume_literal(")")
        _t994 = logic_pb2.Conjunction(args=formulas488)
        return _t994

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal("(")
        self.consume_literal("or")
        xs489 = []
        cond490 = self.match_lookahead_literal("(", 0)
        while cond490:
            _t995 = self.parse_formula()
            item491 = _t995
            xs489.append(item491)
            cond490 = self.match_lookahead_literal("(", 0)
        formulas492 = xs489
        self.consume_literal(")")
        _t996 = logic_pb2.Disjunction(args=formulas492)
        return _t996

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal("(")
        self.consume_literal("not")
        _t997 = self.parse_formula()
        formula493 = _t997
        self.consume_literal(")")
        _t998 = logic_pb2.Not(arg=formula493)
        return _t998

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t999 = self.parse_name()
        name494 = _t999
        _t1000 = self.parse_ffi_args()
        ffi_args495 = _t1000
        _t1001 = self.parse_terms()
        terms496 = _t1001
        self.consume_literal(")")
        _t1002 = logic_pb2.FFI(name=name494, args=ffi_args495, terms=terms496)
        return _t1002

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol497 = self.consume_terminal("SYMBOL")
        return symbol497

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs498 = []
        cond499 = self.match_lookahead_literal("(", 0)
        while cond499:
            _t1003 = self.parse_abstraction()
            item500 = _t1003
            xs498.append(item500)
            cond499 = self.match_lookahead_literal("(", 0)
        abstractions501 = xs498
        self.consume_literal(")")
        return abstractions501

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1004 = self.parse_relation_id()
        relation_id502 = _t1004
        xs503 = []
        cond504 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond504:
            _t1005 = self.parse_term()
            item505 = _t1005
            xs503.append(item505)
            cond504 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms506 = xs503
        self.consume_literal(")")
        _t1006 = logic_pb2.Atom(name=relation_id502, terms=terms506)
        return _t1006

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1007 = self.parse_name()
        name507 = _t1007
        xs508 = []
        cond509 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond509:
            _t1008 = self.parse_term()
            item510 = _t1008
            xs508.append(item510)
            cond509 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms511 = xs508
        self.consume_literal(")")
        _t1009 = logic_pb2.Pragma(name=name507, terms=terms511)
        return _t1009

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1011 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1012 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1013 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1014 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1015 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1016 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1017 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1018 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1019 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1020 = 7
                                                else:
                                                    _t1020 = -1
                                                _t1019 = _t1020
                                            _t1018 = _t1019
                                        _t1017 = _t1018
                                    _t1016 = _t1017
                                _t1015 = _t1016
                            _t1014 = _t1015
                        _t1013 = _t1014
                    _t1012 = _t1013
                _t1011 = _t1012
            _t1010 = _t1011
        else:
            _t1010 = -1
        prediction512 = _t1010
        if prediction512 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1022 = self.parse_name()
            name522 = _t1022
            xs523 = []
            cond524 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            while cond524:
                _t1023 = self.parse_rel_term()
                item525 = _t1023
                xs523.append(item525)
                cond524 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            rel_terms526 = xs523
            self.consume_literal(")")
            _t1024 = logic_pb2.Primitive(name=name522, terms=rel_terms526)
            _t1021 = _t1024
        else:
            if prediction512 == 8:
                _t1026 = self.parse_divide()
                divide521 = _t1026
                _t1025 = divide521
            else:
                if prediction512 == 7:
                    _t1028 = self.parse_multiply()
                    multiply520 = _t1028
                    _t1027 = multiply520
                else:
                    if prediction512 == 6:
                        _t1030 = self.parse_minus()
                        minus519 = _t1030
                        _t1029 = minus519
                    else:
                        if prediction512 == 5:
                            _t1032 = self.parse_add()
                            add518 = _t1032
                            _t1031 = add518
                        else:
                            if prediction512 == 4:
                                _t1034 = self.parse_gt_eq()
                                gt_eq517 = _t1034
                                _t1033 = gt_eq517
                            else:
                                if prediction512 == 3:
                                    _t1036 = self.parse_gt()
                                    gt516 = _t1036
                                    _t1035 = gt516
                                else:
                                    if prediction512 == 2:
                                        _t1038 = self.parse_lt_eq()
                                        lt_eq515 = _t1038
                                        _t1037 = lt_eq515
                                    else:
                                        if prediction512 == 1:
                                            _t1040 = self.parse_lt()
                                            lt514 = _t1040
                                            _t1039 = lt514
                                        else:
                                            if prediction512 == 0:
                                                _t1042 = self.parse_eq()
                                                eq513 = _t1042
                                                _t1041 = eq513
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1039 = _t1041
                                        _t1037 = _t1039
                                    _t1035 = _t1037
                                _t1033 = _t1035
                            _t1031 = _t1033
                        _t1029 = _t1031
                    _t1027 = _t1029
                _t1025 = _t1027
            _t1021 = _t1025
        return _t1021

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("=")
        _t1043 = self.parse_term()
        term527 = _t1043
        _t1044 = self.parse_term()
        term_3528 = _t1044
        self.consume_literal(")")
        _t1045 = logic_pb2.RelTerm(term=term527)
        _t1046 = logic_pb2.RelTerm(term=term_3528)
        _t1047 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1045, _t1046])
        return _t1047

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("<")
        _t1048 = self.parse_term()
        term529 = _t1048
        _t1049 = self.parse_term()
        term_3530 = _t1049
        self.consume_literal(")")
        _t1050 = logic_pb2.RelTerm(term=term529)
        _t1051 = logic_pb2.RelTerm(term=term_3530)
        _t1052 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1050, _t1051])
        return _t1052

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1053 = self.parse_term()
        term531 = _t1053
        _t1054 = self.parse_term()
        term_3532 = _t1054
        self.consume_literal(")")
        _t1055 = logic_pb2.RelTerm(term=term531)
        _t1056 = logic_pb2.RelTerm(term=term_3532)
        _t1057 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1055, _t1056])
        return _t1057

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal(">")
        _t1058 = self.parse_term()
        term533 = _t1058
        _t1059 = self.parse_term()
        term_3534 = _t1059
        self.consume_literal(")")
        _t1060 = logic_pb2.RelTerm(term=term533)
        _t1061 = logic_pb2.RelTerm(term=term_3534)
        _t1062 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1060, _t1061])
        return _t1062

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1063 = self.parse_term()
        term535 = _t1063
        _t1064 = self.parse_term()
        term_3536 = _t1064
        self.consume_literal(")")
        _t1065 = logic_pb2.RelTerm(term=term535)
        _t1066 = logic_pb2.RelTerm(term=term_3536)
        _t1067 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1065, _t1066])
        return _t1067

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("+")
        _t1068 = self.parse_term()
        term537 = _t1068
        _t1069 = self.parse_term()
        term_3538 = _t1069
        _t1070 = self.parse_term()
        term_4539 = _t1070
        self.consume_literal(")")
        _t1071 = logic_pb2.RelTerm(term=term537)
        _t1072 = logic_pb2.RelTerm(term=term_3538)
        _t1073 = logic_pb2.RelTerm(term=term_4539)
        _t1074 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1071, _t1072, _t1073])
        return _t1074

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("-")
        _t1075 = self.parse_term()
        term540 = _t1075
        _t1076 = self.parse_term()
        term_3541 = _t1076
        _t1077 = self.parse_term()
        term_4542 = _t1077
        self.consume_literal(")")
        _t1078 = logic_pb2.RelTerm(term=term540)
        _t1079 = logic_pb2.RelTerm(term=term_3541)
        _t1080 = logic_pb2.RelTerm(term=term_4542)
        _t1081 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1078, _t1079, _t1080])
        return _t1081

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("*")
        _t1082 = self.parse_term()
        term543 = _t1082
        _t1083 = self.parse_term()
        term_3544 = _t1083
        _t1084 = self.parse_term()
        term_4545 = _t1084
        self.consume_literal(")")
        _t1085 = logic_pb2.RelTerm(term=term543)
        _t1086 = logic_pb2.RelTerm(term=term_3544)
        _t1087 = logic_pb2.RelTerm(term=term_4545)
        _t1088 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1085, _t1086, _t1087])
        return _t1088

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("/")
        _t1089 = self.parse_term()
        term546 = _t1089
        _t1090 = self.parse_term()
        term_3547 = _t1090
        _t1091 = self.parse_term()
        term_4548 = _t1091
        self.consume_literal(")")
        _t1092 = logic_pb2.RelTerm(term=term546)
        _t1093 = logic_pb2.RelTerm(term=term_3547)
        _t1094 = logic_pb2.RelTerm(term=term_4548)
        _t1095 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1092, _t1093, _t1094])
        return _t1095

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_literal("true", 0):
            _t1096 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1097 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1098 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1099 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1100 = 0
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1101 = 1
                            else:
                                if self.match_lookahead_terminal("SYMBOL", 0):
                                    _t1102 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1103 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1104 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1105 = 1
                                            else:
                                                if self.match_lookahead_terminal("FLOAT", 0):
                                                    _t1106 = 1
                                                else:
                                                    if self.match_lookahead_terminal("DECIMAL", 0):
                                                        _t1107 = 1
                                                    else:
                                                        _t1107 = -1
                                                    _t1106 = _t1107
                                                _t1105 = _t1106
                                            _t1104 = _t1105
                                        _t1103 = _t1104
                                    _t1102 = _t1103
                                _t1101 = _t1102
                            _t1100 = _t1101
                        _t1099 = _t1100
                    _t1098 = _t1099
                _t1097 = _t1098
            _t1096 = _t1097
        prediction549 = _t1096
        if prediction549 == 1:
            _t1109 = self.parse_term()
            term551 = _t1109
            _t1110 = logic_pb2.RelTerm(term=term551)
            _t1108 = _t1110
        else:
            if prediction549 == 0:
                _t1112 = self.parse_specialized_value()
                specialized_value550 = _t1112
                _t1113 = logic_pb2.RelTerm(specialized_value=specialized_value550)
                _t1111 = _t1113
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1108 = _t1111
        return _t1108

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal("#")
        _t1114 = self.parse_value()
        value552 = _t1114
        return value552

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1115 = self.parse_name()
        name553 = _t1115
        xs554 = []
        cond555 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond555:
            _t1116 = self.parse_rel_term()
            item556 = _t1116
            xs554.append(item556)
            cond555 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        rel_terms557 = xs554
        self.consume_literal(")")
        _t1117 = logic_pb2.RelAtom(name=name553, terms=rel_terms557)
        return _t1117

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1118 = self.parse_term()
        term558 = _t1118
        _t1119 = self.parse_term()
        term_3559 = _t1119
        self.consume_literal(")")
        _t1120 = logic_pb2.Cast(input=term558, result=term_3559)
        return _t1120

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs560 = []
        cond561 = self.match_lookahead_literal("(", 0)
        while cond561:
            _t1121 = self.parse_attribute()
            item562 = _t1121
            xs560.append(item562)
            cond561 = self.match_lookahead_literal("(", 0)
        attributes563 = xs560
        self.consume_literal(")")
        return attributes563

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1122 = self.parse_name()
        name564 = _t1122
        xs565 = []
        cond566 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond566:
            _t1123 = self.parse_value()
            item567 = _t1123
            xs565.append(item567)
            cond566 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        values568 = xs565
        self.consume_literal(")")
        _t1124 = logic_pb2.Attribute(name=name564, args=values568)
        return _t1124

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs569 = []
        cond570 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond570:
            _t1125 = self.parse_relation_id()
            item571 = _t1125
            xs569.append(item571)
            cond570 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids572 = xs569
        _t1126 = self.parse_script()
        script573 = _t1126
        self.consume_literal(")")
        _t1127 = logic_pb2.Algorithm(body=script573)
        getattr(_t1127, 'global').extend(relation_ids572)
        return _t1127

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal("(")
        self.consume_literal("script")
        xs574 = []
        cond575 = self.match_lookahead_literal("(", 0)
        while cond575:
            _t1128 = self.parse_construct()
            item576 = _t1128
            xs574.append(item576)
            cond575 = self.match_lookahead_literal("(", 0)
        constructs577 = xs574
        self.consume_literal(")")
        _t1129 = logic_pb2.Script(constructs=constructs577)
        return _t1129

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1131 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1132 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1133 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1134 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1135 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1136 = 1
                                else:
                                    _t1136 = -1
                                _t1135 = _t1136
                            _t1134 = _t1135
                        _t1133 = _t1134
                    _t1132 = _t1133
                _t1131 = _t1132
            _t1130 = _t1131
        else:
            _t1130 = -1
        prediction578 = _t1130
        if prediction578 == 1:
            _t1138 = self.parse_instruction()
            instruction580 = _t1138
            _t1139 = logic_pb2.Construct(instruction=instruction580)
            _t1137 = _t1139
        else:
            if prediction578 == 0:
                _t1141 = self.parse_loop()
                loop579 = _t1141
                _t1142 = logic_pb2.Construct(loop=loop579)
                _t1140 = _t1142
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1137 = _t1140
        return _t1137

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1143 = self.parse_init()
        init581 = _t1143
        _t1144 = self.parse_script()
        script582 = _t1144
        self.consume_literal(")")
        _t1145 = logic_pb2.Loop(init=init581, body=script582)
        return _t1145

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs583 = []
        cond584 = self.match_lookahead_literal("(", 0)
        while cond584:
            _t1146 = self.parse_instruction()
            item585 = _t1146
            xs583.append(item585)
            cond584 = self.match_lookahead_literal("(", 0)
        instructions586 = xs583
        self.consume_literal(")")
        return instructions586

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1148 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1149 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1150 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1151 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1152 = 0
                            else:
                                _t1152 = -1
                            _t1151 = _t1152
                        _t1150 = _t1151
                    _t1149 = _t1150
                _t1148 = _t1149
            _t1147 = _t1148
        else:
            _t1147 = -1
        prediction587 = _t1147
        if prediction587 == 4:
            _t1154 = self.parse_monus_def()
            monus_def592 = _t1154
            _t1155 = logic_pb2.Instruction(monus_def=monus_def592)
            _t1153 = _t1155
        else:
            if prediction587 == 3:
                _t1157 = self.parse_monoid_def()
                monoid_def591 = _t1157
                _t1158 = logic_pb2.Instruction(monoid_def=monoid_def591)
                _t1156 = _t1158
            else:
                if prediction587 == 2:
                    _t1160 = self.parse_break()
                    break590 = _t1160
                    _t1161 = logic_pb2.Instruction()
                    getattr(_t1161, 'break').CopyFrom(break590)
                    _t1159 = _t1161
                else:
                    if prediction587 == 1:
                        _t1163 = self.parse_upsert()
                        upsert589 = _t1163
                        _t1164 = logic_pb2.Instruction(upsert=upsert589)
                        _t1162 = _t1164
                    else:
                        if prediction587 == 0:
                            _t1166 = self.parse_assign()
                            assign588 = _t1166
                            _t1167 = logic_pb2.Instruction(assign=assign588)
                            _t1165 = _t1167
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1162 = _t1165
                    _t1159 = _t1162
                _t1156 = _t1159
            _t1153 = _t1156
        return _t1153

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1168 = self.parse_relation_id()
        relation_id593 = _t1168
        _t1169 = self.parse_abstraction()
        abstraction594 = _t1169
        if self.match_lookahead_literal("(", 0):
            _t1171 = self.parse_attrs()
            _t1170 = _t1171
        else:
            _t1170 = None
        attrs595 = _t1170
        self.consume_literal(")")
        _t1172 = logic_pb2.Assign(name=relation_id593, body=abstraction594, attrs=(attrs595 if attrs595 is not None else []))
        return _t1172

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1173 = self.parse_relation_id()
        relation_id596 = _t1173
        _t1174 = self.parse_abstraction_with_arity()
        abstraction_with_arity597 = _t1174
        if self.match_lookahead_literal("(", 0):
            _t1176 = self.parse_attrs()
            _t1175 = _t1176
        else:
            _t1175 = None
        attrs598 = _t1175
        self.consume_literal(")")
        _t1177 = logic_pb2.Upsert(name=relation_id596, body=abstraction_with_arity597[0], attrs=(attrs598 if attrs598 is not None else []), value_arity=abstraction_with_arity597[1])
        return _t1177

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1178 = self.parse_bindings()
        bindings599 = _t1178
        _t1179 = self.parse_formula()
        formula600 = _t1179
        self.consume_literal(")")
        _t1180 = logic_pb2.Abstraction(vars=(list(bindings599[0]) + list(bindings599[1] if bindings599[1] is not None else [])), value=formula600)
        return (_t1180, len(bindings599[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal("(")
        self.consume_literal("break")
        _t1181 = self.parse_relation_id()
        relation_id601 = _t1181
        _t1182 = self.parse_abstraction()
        abstraction602 = _t1182
        if self.match_lookahead_literal("(", 0):
            _t1184 = self.parse_attrs()
            _t1183 = _t1184
        else:
            _t1183 = None
        attrs603 = _t1183
        self.consume_literal(")")
        _t1185 = logic_pb2.Break(name=relation_id601, body=abstraction602, attrs=(attrs603 if attrs603 is not None else []))
        return _t1185

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1186 = self.parse_monoid()
        monoid604 = _t1186
        _t1187 = self.parse_relation_id()
        relation_id605 = _t1187
        _t1188 = self.parse_abstraction_with_arity()
        abstraction_with_arity606 = _t1188
        if self.match_lookahead_literal("(", 0):
            _t1190 = self.parse_attrs()
            _t1189 = _t1190
        else:
            _t1189 = None
        attrs607 = _t1189
        self.consume_literal(")")
        _t1191 = logic_pb2.MonoidDef(monoid=monoid604, name=relation_id605, body=abstraction_with_arity606[0], attrs=(attrs607 if attrs607 is not None else []), value_arity=abstraction_with_arity606[1])
        return _t1191

    def parse_monoid(self) -> logic_pb2.Monoid:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1193 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1194 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1195 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1196 = 2
                        else:
                            _t1196 = -1
                        _t1195 = _t1196
                    _t1194 = _t1195
                _t1193 = _t1194
            _t1192 = _t1193
        else:
            _t1192 = -1
        prediction608 = _t1192
        if prediction608 == 3:
            _t1198 = self.parse_sum_monoid()
            sum_monoid612 = _t1198
            _t1199 = logic_pb2.Monoid(sum_monoid=sum_monoid612)
            _t1197 = _t1199
        else:
            if prediction608 == 2:
                _t1201 = self.parse_max_monoid()
                max_monoid611 = _t1201
                _t1202 = logic_pb2.Monoid(max_monoid=max_monoid611)
                _t1200 = _t1202
            else:
                if prediction608 == 1:
                    _t1204 = self.parse_min_monoid()
                    min_monoid610 = _t1204
                    _t1205 = logic_pb2.Monoid(min_monoid=min_monoid610)
                    _t1203 = _t1205
                else:
                    if prediction608 == 0:
                        _t1207 = self.parse_or_monoid()
                        or_monoid609 = _t1207
                        _t1208 = logic_pb2.Monoid(or_monoid=or_monoid609)
                        _t1206 = _t1208
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1203 = _t1206
                _t1200 = _t1203
            _t1197 = _t1200
        return _t1197

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1209 = logic_pb2.OrMonoid()
        return _t1209

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        self.consume_literal("(")
        self.consume_literal("min")
        _t1210 = self.parse_type()
        type613 = _t1210
        self.consume_literal(")")
        _t1211 = logic_pb2.MinMonoid(type=type613)
        return _t1211

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        self.consume_literal("(")
        self.consume_literal("max")
        _t1212 = self.parse_type()
        type614 = _t1212
        self.consume_literal(")")
        _t1213 = logic_pb2.MaxMonoid(type=type614)
        return _t1213

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1214 = self.parse_type()
        type615 = _t1214
        self.consume_literal(")")
        _t1215 = logic_pb2.SumMonoid(type=type615)
        return _t1215

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1216 = self.parse_monoid()
        monoid616 = _t1216
        _t1217 = self.parse_relation_id()
        relation_id617 = _t1217
        _t1218 = self.parse_abstraction_with_arity()
        abstraction_with_arity618 = _t1218
        if self.match_lookahead_literal("(", 0):
            _t1220 = self.parse_attrs()
            _t1219 = _t1220
        else:
            _t1219 = None
        attrs619 = _t1219
        self.consume_literal(")")
        _t1221 = logic_pb2.MonusDef(monoid=monoid616, name=relation_id617, body=abstraction_with_arity618[0], attrs=(attrs619 if attrs619 is not None else []), value_arity=abstraction_with_arity618[1])
        return _t1221

    def parse_constraint(self) -> logic_pb2.Constraint:
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1222 = self.parse_relation_id()
        relation_id620 = _t1222
        _t1223 = self.parse_abstraction()
        abstraction621 = _t1223
        _t1224 = self.parse_functional_dependency_keys()
        functional_dependency_keys622 = _t1224
        _t1225 = self.parse_functional_dependency_values()
        functional_dependency_values623 = _t1225
        self.consume_literal(")")
        _t1226 = logic_pb2.FunctionalDependency(guard=abstraction621, keys=functional_dependency_keys622, values=functional_dependency_values623)
        _t1227 = logic_pb2.Constraint(name=relation_id620, functional_dependency=_t1226)
        return _t1227

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs624 = []
        cond625 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond625:
            _t1228 = self.parse_var()
            item626 = _t1228
            xs624.append(item626)
            cond625 = self.match_lookahead_terminal("SYMBOL", 0)
        vars627 = xs624
        self.consume_literal(")")
        return vars627

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs628 = []
        cond629 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond629:
            _t1229 = self.parse_var()
            item630 = _t1229
            xs628.append(item630)
            cond629 = self.match_lookahead_terminal("SYMBOL", 0)
        vars631 = xs628
        self.consume_literal(")")
        return vars631

    def parse_data(self) -> logic_pb2.Data:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("edb", 1):
                _t1231 = 0
            else:
                if self.match_lookahead_literal("csv_data", 1):
                    _t1232 = 2
                else:
                    if self.match_lookahead_literal("betree_relation", 1):
                        _t1233 = 1
                    else:
                        _t1233 = -1
                    _t1232 = _t1233
                _t1231 = _t1232
            _t1230 = _t1231
        else:
            _t1230 = -1
        prediction632 = _t1230
        if prediction632 == 2:
            _t1235 = self.parse_csv_data()
            csv_data635 = _t1235
            _t1236 = logic_pb2.Data(csv_data=csv_data635)
            _t1234 = _t1236
        else:
            if prediction632 == 1:
                _t1238 = self.parse_betree_relation()
                betree_relation634 = _t1238
                _t1239 = logic_pb2.Data(betree_relation=betree_relation634)
                _t1237 = _t1239
            else:
                if prediction632 == 0:
                    _t1241 = self.parse_edb()
                    edb633 = _t1241
                    _t1242 = logic_pb2.Data(edb=edb633)
                    _t1240 = _t1242
                else:
                    raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t1237 = _t1240
            _t1234 = _t1237
        return _t1234

    def parse_edb(self) -> logic_pb2.EDB:
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1243 = self.parse_relation_id()
        relation_id636 = _t1243
        _t1244 = self.parse_edb_path()
        edb_path637 = _t1244
        _t1245 = self.parse_edb_types()
        edb_types638 = _t1245
        self.consume_literal(")")
        _t1246 = logic_pb2.EDB(target_id=relation_id636, path=edb_path637, types=edb_types638)
        return _t1246

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs639 = []
        cond640 = self.match_lookahead_terminal("STRING", 0)
        while cond640:
            item641 = self.consume_terminal("STRING")
            xs639.append(item641)
            cond640 = self.match_lookahead_terminal("STRING", 0)
        strings642 = xs639
        self.consume_literal("]")
        return strings642

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs643 = []
        cond644 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond644:
            _t1247 = self.parse_type()
            item645 = _t1247
            xs643.append(item645)
            cond644 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types646 = xs643
        self.consume_literal("]")
        return types646

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1248 = self.parse_relation_id()
        relation_id647 = _t1248
        _t1249 = self.parse_betree_info()
        betree_info648 = _t1249
        self.consume_literal(")")
        _t1250 = logic_pb2.BeTreeRelation(name=relation_id647, relation_info=betree_info648)
        return _t1250

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1251 = self.parse_betree_info_key_types()
        betree_info_key_types649 = _t1251
        _t1252 = self.parse_betree_info_value_types()
        betree_info_value_types650 = _t1252
        _t1253 = self.parse_config_dict()
        config_dict651 = _t1253
        self.consume_literal(")")
        _t1254 = self.construct_betree_info(betree_info_key_types649, betree_info_value_types650, config_dict651)
        return _t1254

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs652 = []
        cond653 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond653:
            _t1255 = self.parse_type()
            item654 = _t1255
            xs652.append(item654)
            cond653 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types655 = xs652
        self.consume_literal(")")
        return types655

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs656 = []
        cond657 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond657:
            _t1256 = self.parse_type()
            item658 = _t1256
            xs656.append(item658)
            cond657 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types659 = xs656
        self.consume_literal(")")
        return types659

    def parse_csv_data(self) -> logic_pb2.CSVData:
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1257 = self.parse_csvlocator()
        csvlocator660 = _t1257
        _t1258 = self.parse_csv_config()
        csv_config661 = _t1258
        _t1259 = self.parse_gnf_columns()
        gnf_columns662 = _t1259
        _t1260 = self.parse_csv_asof()
        csv_asof663 = _t1260
        self.consume_literal(")")
        _t1261 = logic_pb2.CSVData(locator=csvlocator660, config=csv_config661, columns=gnf_columns662, asof=csv_asof663)
        return _t1261

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1263 = self.parse_csv_locator_paths()
            _t1262 = _t1263
        else:
            _t1262 = None
        csv_locator_paths664 = _t1262
        if self.match_lookahead_literal("(", 0):
            _t1265 = self.parse_csv_locator_inline_data()
            _t1264 = _t1265
        else:
            _t1264 = None
        csv_locator_inline_data665 = _t1264
        self.consume_literal(")")
        _t1266 = logic_pb2.CSVLocator(paths=(csv_locator_paths664 if csv_locator_paths664 is not None else []), inline_data=(csv_locator_inline_data665 if csv_locator_inline_data665 is not None else "").encode())
        return _t1266

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs666 = []
        cond667 = self.match_lookahead_terminal("STRING", 0)
        while cond667:
            item668 = self.consume_terminal("STRING")
            xs666.append(item668)
            cond667 = self.match_lookahead_terminal("STRING", 0)
        strings669 = xs666
        self.consume_literal(")")
        return strings669

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string670 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string670

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1267 = self.parse_config_dict()
        config_dict671 = _t1267
        self.consume_literal(")")
        _t1268 = self.construct_csv_config(config_dict671)
        return _t1268

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs672 = []
        cond673 = self.match_lookahead_literal("(", 0)
        while cond673:
            _t1269 = self.parse_gnf_column()
            item674 = _t1269
            xs672.append(item674)
            cond673 = self.match_lookahead_literal("(", 0)
        gnf_columns675 = xs672
        self.consume_literal(")")
        return gnf_columns675

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        self.consume_literal("(")
        self.consume_literal("column")
        _t1270 = self.parse_gnf_column_path()
        gnf_column_path676 = _t1270
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1272 = self.parse_relation_id()
            _t1271 = _t1272
        else:
            _t1271 = None
        relation_id677 = _t1271
        self.consume_literal("[")
        xs678 = []
        cond679 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond679:
            _t1273 = self.parse_type()
            item680 = _t1273
            xs678.append(item680)
            cond679 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types681 = xs678
        self.consume_literal("]")
        self.consume_literal(")")
        _t1274 = logic_pb2.GNFColumn(column_path=gnf_column_path676, target_id=relation_id677, types=types681)
        return _t1274

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1275 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1276 = 0
            else:
                _t1276 = -1
            _t1275 = _t1276
        prediction682 = _t1275
        if prediction682 == 1:
            self.consume_literal("[")
            xs684 = []
            cond685 = self.match_lookahead_terminal("STRING", 0)
            while cond685:
                item686 = self.consume_terminal("STRING")
                xs684.append(item686)
                cond685 = self.match_lookahead_terminal("STRING", 0)
            strings687 = xs684
            self.consume_literal("]")
            _t1277 = strings687
        else:
            if prediction682 == 0:
                string683 = self.consume_terminal("STRING")
                _t1278 = [string683]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1277 = _t1278
        return _t1277

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string688 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string688

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1279 = self.parse_fragment_id()
        fragment_id689 = _t1279
        self.consume_literal(")")
        _t1280 = transactions_pb2.Undefine(fragment_id=fragment_id689)
        return _t1280

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal("(")
        self.consume_literal("context")
        xs690 = []
        cond691 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond691:
            _t1281 = self.parse_relation_id()
            item692 = _t1281
            xs690.append(item692)
            cond691 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids693 = xs690
        self.consume_literal(")")
        _t1282 = transactions_pb2.Context(relations=relation_ids693)
        return _t1282

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t1283 = self.parse_edb_path()
        edb_path694 = _t1283
        _t1284 = self.parse_relation_id()
        relation_id695 = _t1284
        self.consume_literal(")")
        _t1285 = transactions_pb2.Snapshot(destination_path=edb_path694, source_relation=relation_id695)
        return _t1285

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs696 = []
        cond697 = self.match_lookahead_literal("(", 0)
        while cond697:
            _t1286 = self.parse_read()
            item698 = _t1286
            xs696.append(item698)
            cond697 = self.match_lookahead_literal("(", 0)
        reads699 = xs696
        self.consume_literal(")")
        return reads699

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1288 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1289 = 1
                else:
                    if self.match_lookahead_literal("export", 1):
                        _t1290 = 4
                    else:
                        if self.match_lookahead_literal("demand", 1):
                            _t1291 = 0
                        else:
                            if self.match_lookahead_literal("abort", 1):
                                _t1292 = 3
                            else:
                                _t1292 = -1
                            _t1291 = _t1292
                        _t1290 = _t1291
                    _t1289 = _t1290
                _t1288 = _t1289
            _t1287 = _t1288
        else:
            _t1287 = -1
        prediction700 = _t1287
        if prediction700 == 4:
            _t1294 = self.parse_export()
            export705 = _t1294
            _t1295 = transactions_pb2.Read(export=export705)
            _t1293 = _t1295
        else:
            if prediction700 == 3:
                _t1297 = self.parse_abort()
                abort704 = _t1297
                _t1298 = transactions_pb2.Read(abort=abort704)
                _t1296 = _t1298
            else:
                if prediction700 == 2:
                    _t1300 = self.parse_what_if()
                    what_if703 = _t1300
                    _t1301 = transactions_pb2.Read(what_if=what_if703)
                    _t1299 = _t1301
                else:
                    if prediction700 == 1:
                        _t1303 = self.parse_output()
                        output702 = _t1303
                        _t1304 = transactions_pb2.Read(output=output702)
                        _t1302 = _t1304
                    else:
                        if prediction700 == 0:
                            _t1306 = self.parse_demand()
                            demand701 = _t1306
                            _t1307 = transactions_pb2.Read(demand=demand701)
                            _t1305 = _t1307
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1302 = _t1305
                    _t1299 = _t1302
                _t1296 = _t1299
            _t1293 = _t1296
        return _t1293

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1308 = self.parse_relation_id()
        relation_id706 = _t1308
        self.consume_literal(")")
        _t1309 = transactions_pb2.Demand(relation_id=relation_id706)
        return _t1309

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal("(")
        self.consume_literal("output")
        _t1310 = self.parse_name()
        name707 = _t1310
        _t1311 = self.parse_relation_id()
        relation_id708 = _t1311
        self.consume_literal(")")
        _t1312 = transactions_pb2.Output(name=name707, relation_id=relation_id708)
        return _t1312

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t1313 = self.parse_name()
        name709 = _t1313
        _t1314 = self.parse_epoch()
        epoch710 = _t1314
        self.consume_literal(")")
        _t1315 = transactions_pb2.WhatIf(branch=name709, epoch=epoch710)
        return _t1315

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t1317 = self.parse_name()
            _t1316 = _t1317
        else:
            _t1316 = None
        name711 = _t1316
        _t1318 = self.parse_relation_id()
        relation_id712 = _t1318
        self.consume_literal(")")
        _t1319 = transactions_pb2.Abort(name=(name711 if name711 is not None else "abort"), relation_id=relation_id712)
        return _t1319

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal("(")
        self.consume_literal("export")
        _t1320 = self.parse_export_csv_config()
        export_csv_config713 = _t1320
        self.consume_literal(")")
        _t1321 = transactions_pb2.Export(csv_config=export_csv_config713)
        return _t1321

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal("(")
        self.consume_literal("export_csv_config")
        _t1322 = self.parse_export_csv_path()
        export_csv_path714 = _t1322
        _t1323 = self.parse_export_csv_columns()
        export_csv_columns715 = _t1323
        _t1324 = self.parse_config_dict()
        config_dict716 = _t1324
        self.consume_literal(")")
        _t1325 = self.export_csv_config(export_csv_path714, export_csv_columns715, config_dict716)
        return _t1325

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string717 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string717

    def parse_export_csv_columns(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs718 = []
        cond719 = self.match_lookahead_literal("(", 0)
        while cond719:
            _t1326 = self.parse_export_csv_column()
            item720 = _t1326
            xs718.append(item720)
            cond719 = self.match_lookahead_literal("(", 0)
        export_csv_columns721 = xs718
        self.consume_literal(")")
        return export_csv_columns721

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal("(")
        self.consume_literal("column")
        string722 = self.consume_terminal("STRING")
        _t1327 = self.parse_relation_id()
        relation_id723 = _t1327
        self.consume_literal(")")
        _t1328 = transactions_pb2.ExportCSVColumn(column_name=string722, column_data=relation_id723)
        return _t1328


def parse(input_str: str) -> Any:
    """Parse input string and return parse tree."""
    lexer = Lexer(input_str)
    parser = Parser(lexer.tokens)
    result = parser.parse_transaction()
    # Check for unconsumed tokens (except EOF)
    if parser.pos < len(parser.tokens):
        remaining_token = parser.lookahead(0)
        if remaining_token.type != "$":
            raise ParseError(f"Unexpected token at end of input: {remaining_token}")
    return result
