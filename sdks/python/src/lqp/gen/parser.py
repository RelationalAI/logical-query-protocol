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
            _t1348 = value.HasField("int_value")
        else:
            _t1348 = False
        if _t1348:
            assert value is not None
            return int(value.int_value)
        else:
            _t1349 = None
        return int(default)

    def _extract_value_int64(self, value: Optional[logic_pb2.Value], default: int) -> int:
        if value is not None:
            assert value is not None
            _t1350 = value.HasField("int_value")
        else:
            _t1350 = False
        if _t1350:
            assert value is not None
            return value.int_value
        else:
            _t1351 = None
        return default

    def _extract_value_string(self, value: Optional[logic_pb2.Value], default: str) -> str:
        if value is not None:
            assert value is not None
            _t1352 = value.HasField("string_value")
        else:
            _t1352 = False
        if _t1352:
            assert value is not None
            return value.string_value
        else:
            _t1353 = None
        return default

    def _extract_value_boolean(self, value: Optional[logic_pb2.Value], default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t1354 = value.HasField("boolean_value")
        else:
            _t1354 = False
        if _t1354:
            assert value is not None
            return value.boolean_value
        else:
            _t1355 = None
        return default

    def _extract_value_string_list(self, value: Optional[logic_pb2.Value], default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t1356 = value.HasField("string_value")
        else:
            _t1356 = False
        if _t1356:
            assert value is not None
            return [value.string_value]
        else:
            _t1357 = None
        return default

    def _try_extract_value_int64(self, value: Optional[logic_pb2.Value]) -> Optional[int]:
        if value is not None:
            assert value is not None
            _t1358 = value.HasField("int_value")
        else:
            _t1358 = False
        if _t1358:
            assert value is not None
            return value.int_value
        else:
            _t1359 = None
        return None

    def _try_extract_value_float64(self, value: Optional[logic_pb2.Value]) -> Optional[float]:
        if value is not None:
            assert value is not None
            _t1360 = value.HasField("float_value")
        else:
            _t1360 = False
        if _t1360:
            assert value is not None
            return value.float_value
        else:
            _t1361 = None
        return None

    def _try_extract_value_bytes(self, value: Optional[logic_pb2.Value]) -> Optional[bytes]:
        if value is not None:
            assert value is not None
            _t1362 = value.HasField("string_value")
        else:
            _t1362 = False
        if _t1362:
            assert value is not None
            return value.string_value.encode()
        else:
            _t1363 = None
        return None

    def _try_extract_value_uint128(self, value: Optional[logic_pb2.Value]) -> Optional[logic_pb2.UInt128Value]:
        if value is not None:
            assert value is not None
            _t1364 = value.HasField("uint128_value")
        else:
            _t1364 = False
        if _t1364:
            assert value is not None
            return value.uint128_value
        else:
            _t1365 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1366 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t1366
        _t1367 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t1367
        _t1368 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t1368
        _t1369 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t1369
        _t1370 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t1370
        _t1371 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t1371
        _t1372 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t1372
        _t1373 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t1373
        _t1374 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t1374
        _t1375 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t1375
        _t1376 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t1376
        _t1377 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t1377

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1378 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t1378
        _t1379 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t1379
        _t1380 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t1380
        _t1381 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t1381
        _t1382 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1382
        _t1383 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t1383
        _t1384 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t1384
        _t1385 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t1385
        _t1386 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t1386
        _t1387 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1387
        _t1388 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1388

    def default_configure(self) -> transactions_pb2.Configure:
        _t1389 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1389
        _t1390 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1390

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
        _t1391 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1391
        _t1392 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t1392
        _t1393 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1393

    def export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1394 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t1394
        _t1395 = self._extract_value_string(config.get("compression"), "")
        compression = _t1395
        _t1396 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t1396
        _t1397 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t1397
        _t1398 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t1398
        _t1399 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t1399
        _t1400 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t1400
        _t1401 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1401

    def construct_csv_column(self, path: Sequence[str], tail: Optional[tuple[Optional[logic_pb2.RelationId], Sequence[logic_pb2.Type]]]) -> logic_pb2.CSVColumn:
        if tail is not None:
            assert tail is not None
            t = tail
            _t1403 = logic_pb2.CSVColumn(column_path=path, target_id=t[0], types=t[1])
            return _t1403
        else:
            _t1402 = None
        _t1404 = logic_pb2.CSVColumn(column_path=path, target_id=None, types=[])
        return _t1404

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t737 = self.parse_configure()
            _t736 = _t737
        else:
            _t736 = None
        configure368 = _t736
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t739 = self.parse_sync()
            _t738 = _t739
        else:
            _t738 = None
        sync369 = _t738
        xs370 = []
        cond371 = self.match_lookahead_literal("(", 0)
        while cond371:
            _t740 = self.parse_epoch()
            item372 = _t740
            xs370.append(item372)
            cond371 = self.match_lookahead_literal("(", 0)
        epochs373 = xs370
        self.consume_literal(")")
        _t741 = self.default_configure()
        _t742 = transactions_pb2.Transaction(epochs=epochs373, configure=(configure368 if configure368 is not None else _t741), sync=sync369)
        return _t742

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal("(")
        self.consume_literal("configure")
        _t743 = self.parse_config_dict()
        config_dict374 = _t743
        self.consume_literal(")")
        _t744 = self.construct_configure(config_dict374)
        return _t744

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs375 = []
        cond376 = self.match_lookahead_literal(":", 0)
        while cond376:
            _t745 = self.parse_config_key_value()
            item377 = _t745
            xs375.append(item377)
            cond376 = self.match_lookahead_literal(":", 0)
        config_key_values378 = xs375
        self.consume_literal("}")
        return config_key_values378

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol379 = self.consume_terminal("SYMBOL")
        _t746 = self.parse_value()
        value380 = _t746
        return (symbol379, value380,)

    def parse_value(self) -> logic_pb2.Value:
        if self.match_lookahead_literal("true", 0):
            _t747 = 9
        else:
            if self.match_lookahead_literal("missing", 0):
                _t748 = 8
            else:
                if self.match_lookahead_literal("false", 0):
                    _t749 = 9
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t751 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t752 = 0
                            else:
                                _t752 = -1
                            _t751 = _t752
                        _t750 = _t751
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t753 = 5
                        else:
                            if self.match_lookahead_terminal("STRING", 0):
                                _t754 = 2
                            else:
                                if self.match_lookahead_terminal("INT128", 0):
                                    _t755 = 6
                                else:
                                    if self.match_lookahead_terminal("INT", 0):
                                        _t756 = 3
                                    else:
                                        if self.match_lookahead_terminal("FLOAT", 0):
                                            _t757 = 4
                                        else:
                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                _t758 = 7
                                            else:
                                                _t758 = -1
                                            _t757 = _t758
                                        _t756 = _t757
                                    _t755 = _t756
                                _t754 = _t755
                            _t753 = _t754
                        _t750 = _t753
                    _t749 = _t750
                _t748 = _t749
            _t747 = _t748
        prediction381 = _t747
        if prediction381 == 9:
            _t760 = self.parse_boolean_value()
            boolean_value390 = _t760
            _t761 = logic_pb2.Value(boolean_value=boolean_value390)
            _t759 = _t761
        else:
            if prediction381 == 8:
                self.consume_literal("missing")
                _t763 = logic_pb2.MissingValue()
                _t764 = logic_pb2.Value(missing_value=_t763)
                _t762 = _t764
            else:
                if prediction381 == 7:
                    decimal389 = self.consume_terminal("DECIMAL")
                    _t766 = logic_pb2.Value(decimal_value=decimal389)
                    _t765 = _t766
                else:
                    if prediction381 == 6:
                        int128388 = self.consume_terminal("INT128")
                        _t768 = logic_pb2.Value(int128_value=int128388)
                        _t767 = _t768
                    else:
                        if prediction381 == 5:
                            uint128387 = self.consume_terminal("UINT128")
                            _t770 = logic_pb2.Value(uint128_value=uint128387)
                            _t769 = _t770
                        else:
                            if prediction381 == 4:
                                float386 = self.consume_terminal("FLOAT")
                                _t772 = logic_pb2.Value(float_value=float386)
                                _t771 = _t772
                            else:
                                if prediction381 == 3:
                                    int385 = self.consume_terminal("INT")
                                    _t774 = logic_pb2.Value(int_value=int385)
                                    _t773 = _t774
                                else:
                                    if prediction381 == 2:
                                        string384 = self.consume_terminal("STRING")
                                        _t776 = logic_pb2.Value(string_value=string384)
                                        _t775 = _t776
                                    else:
                                        if prediction381 == 1:
                                            _t778 = self.parse_datetime()
                                            datetime383 = _t778
                                            _t779 = logic_pb2.Value(datetime_value=datetime383)
                                            _t777 = _t779
                                        else:
                                            if prediction381 == 0:
                                                _t781 = self.parse_date()
                                                date382 = _t781
                                                _t782 = logic_pb2.Value(date_value=date382)
                                                _t780 = _t782
                                            else:
                                                raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t777 = _t780
                                        _t775 = _t777
                                    _t773 = _t775
                                _t771 = _t773
                            _t769 = _t771
                        _t767 = _t769
                    _t765 = _t767
                _t762 = _t765
            _t759 = _t762
        return _t759

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal("(")
        self.consume_literal("date")
        int391 = self.consume_terminal("INT")
        int_3392 = self.consume_terminal("INT")
        int_4393 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t783 = logic_pb2.DateValue(year=int(int391), month=int(int_3392), day=int(int_4393))
        return _t783

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        self.consume_literal("(")
        self.consume_literal("datetime")
        int394 = self.consume_terminal("INT")
        int_3395 = self.consume_terminal("INT")
        int_4396 = self.consume_terminal("INT")
        int_5397 = self.consume_terminal("INT")
        int_6398 = self.consume_terminal("INT")
        int_7399 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t784 = self.consume_terminal("INT")
        else:
            _t784 = None
        int_8400 = _t784
        self.consume_literal(")")
        _t785 = logic_pb2.DateTimeValue(year=int(int394), month=int(int_3395), day=int(int_4396), hour=int(int_5397), minute=int(int_6398), second=int(int_7399), microsecond=int((int_8400 if int_8400 is not None else 0)))
        return _t785

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t786 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t787 = 1
            else:
                _t787 = -1
            _t786 = _t787
        prediction401 = _t786
        if prediction401 == 1:
            self.consume_literal("false")
            _t788 = False
        else:
            if prediction401 == 0:
                self.consume_literal("true")
                _t789 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t788 = _t789
        return _t788

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal("(")
        self.consume_literal("sync")
        xs402 = []
        cond403 = self.match_lookahead_literal(":", 0)
        while cond403:
            _t790 = self.parse_fragment_id()
            item404 = _t790
            xs402.append(item404)
            cond403 = self.match_lookahead_literal(":", 0)
        fragment_ids405 = xs402
        self.consume_literal(")")
        _t791 = transactions_pb2.Sync(fragments=fragment_ids405)
        return _t791

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        self.consume_literal(":")
        symbol406 = self.consume_terminal("SYMBOL")
        return fragments_pb2.FragmentId(id=symbol406.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t793 = self.parse_epoch_writes()
            _t792 = _t793
        else:
            _t792 = None
        epoch_writes407 = _t792
        if self.match_lookahead_literal("(", 0):
            _t795 = self.parse_epoch_reads()
            _t794 = _t795
        else:
            _t794 = None
        epoch_reads408 = _t794
        self.consume_literal(")")
        _t796 = transactions_pb2.Epoch(writes=(epoch_writes407 if epoch_writes407 is not None else []), reads=(epoch_reads408 if epoch_reads408 is not None else []))
        return _t796

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs409 = []
        cond410 = self.match_lookahead_literal("(", 0)
        while cond410:
            _t797 = self.parse_write()
            item411 = _t797
            xs409.append(item411)
            cond410 = self.match_lookahead_literal("(", 0)
        writes412 = xs409
        self.consume_literal(")")
        return writes412

    def parse_write(self) -> transactions_pb2.Write:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t799 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t800 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t801 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t802 = 2
                        else:
                            _t802 = -1
                        _t801 = _t802
                    _t800 = _t801
                _t799 = _t800
            _t798 = _t799
        else:
            _t798 = -1
        prediction413 = _t798
        if prediction413 == 3:
            _t804 = self.parse_snapshot()
            snapshot417 = _t804
            _t805 = transactions_pb2.Write(snapshot=snapshot417)
            _t803 = _t805
        else:
            if prediction413 == 2:
                _t807 = self.parse_context()
                context416 = _t807
                _t808 = transactions_pb2.Write(context=context416)
                _t806 = _t808
            else:
                if prediction413 == 1:
                    _t810 = self.parse_undefine()
                    undefine415 = _t810
                    _t811 = transactions_pb2.Write(undefine=undefine415)
                    _t809 = _t811
                else:
                    if prediction413 == 0:
                        _t813 = self.parse_define()
                        define414 = _t813
                        _t814 = transactions_pb2.Write(define=define414)
                        _t812 = _t814
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t809 = _t812
                _t806 = _t809
            _t803 = _t806
        return _t803

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal("(")
        self.consume_literal("define")
        _t815 = self.parse_fragment()
        fragment418 = _t815
        self.consume_literal(")")
        _t816 = transactions_pb2.Define(fragment=fragment418)
        return _t816

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t817 = self.parse_new_fragment_id()
        new_fragment_id419 = _t817
        xs420 = []
        cond421 = self.match_lookahead_literal("(", 0)
        while cond421:
            _t818 = self.parse_declaration()
            item422 = _t818
            xs420.append(item422)
            cond421 = self.match_lookahead_literal("(", 0)
        declarations423 = xs420
        self.consume_literal(")")
        return self.construct_fragment(new_fragment_id419, declarations423)

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        _t819 = self.parse_fragment_id()
        fragment_id424 = _t819
        self.start_fragment(fragment_id424)
        return fragment_id424

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("rel_edb", 1):
                _t821 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t822 = 2
                else:
                    if self.match_lookahead_literal("def", 1):
                        _t823 = 0
                    else:
                        if self.match_lookahead_literal("csv_data", 1):
                            _t824 = 3
                        else:
                            if self.match_lookahead_literal("betree_relation", 1):
                                _t825 = 3
                            else:
                                if self.match_lookahead_literal("algorithm", 1):
                                    _t826 = 1
                                else:
                                    _t826 = -1
                                _t825 = _t826
                            _t824 = _t825
                        _t823 = _t824
                    _t822 = _t823
                _t821 = _t822
            _t820 = _t821
        else:
            _t820 = -1
        prediction425 = _t820
        if prediction425 == 3:
            _t828 = self.parse_data()
            data429 = _t828
            _t829 = logic_pb2.Declaration(data=data429)
            _t827 = _t829
        else:
            if prediction425 == 2:
                _t831 = self.parse_constraint()
                constraint428 = _t831
                _t832 = logic_pb2.Declaration(constraint=constraint428)
                _t830 = _t832
            else:
                if prediction425 == 1:
                    _t834 = self.parse_algorithm()
                    algorithm427 = _t834
                    _t835 = logic_pb2.Declaration(algorithm=algorithm427)
                    _t833 = _t835
                else:
                    if prediction425 == 0:
                        _t837 = self.parse_def()
                        def426 = _t837
                        _t838 = logic_pb2.Declaration()
                        getattr(_t838, 'def').CopyFrom(def426)
                        _t836 = _t838
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t833 = _t836
                _t830 = _t833
            _t827 = _t830
        return _t827

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal("(")
        self.consume_literal("def")
        _t839 = self.parse_relation_id()
        relation_id430 = _t839
        _t840 = self.parse_abstraction()
        abstraction431 = _t840
        if self.match_lookahead_literal("(", 0):
            _t842 = self.parse_attrs()
            _t841 = _t842
        else:
            _t841 = None
        attrs432 = _t841
        self.consume_literal(")")
        _t843 = logic_pb2.Def(name=relation_id430, body=abstraction431, attrs=(attrs432 if attrs432 is not None else []))
        return _t843

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_literal(":", 0):
            _t844 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t845 = 1
            else:
                _t845 = -1
            _t844 = _t845
        prediction433 = _t844
        if prediction433 == 1:
            uint128435 = self.consume_terminal("UINT128")
            _t846 = logic_pb2.RelationId(id_low=uint128435.low, id_high=uint128435.high)
        else:
            if prediction433 == 0:
                self.consume_literal(":")
                symbol434 = self.consume_terminal("SYMBOL")
                _t847 = self.relation_id_from_string(symbol434)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t846 = _t847
        return _t846

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal("(")
        _t848 = self.parse_bindings()
        bindings436 = _t848
        _t849 = self.parse_formula()
        formula437 = _t849
        self.consume_literal(")")
        _t850 = logic_pb2.Abstraction(vars=(list(bindings436[0]) + list(bindings436[1] if bindings436[1] is not None else [])), value=formula437)
        return _t850

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs438 = []
        cond439 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond439:
            _t851 = self.parse_binding()
            item440 = _t851
            xs438.append(item440)
            cond439 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings441 = xs438
        if self.match_lookahead_literal("|", 0):
            _t853 = self.parse_value_bindings()
            _t852 = _t853
        else:
            _t852 = None
        value_bindings442 = _t852
        self.consume_literal("]")
        return (bindings441, (value_bindings442 if value_bindings442 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol443 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t854 = self.parse_type()
        type444 = _t854
        _t855 = logic_pb2.Var(name=symbol443)
        _t856 = logic_pb2.Binding(var=_t855, type=type444)
        return _t856

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t857 = 0
        else:
            if self.match_lookahead_literal("UINT128", 0):
                _t858 = 4
            else:
                if self.match_lookahead_literal("STRING", 0):
                    _t859 = 1
                else:
                    if self.match_lookahead_literal("MISSING", 0):
                        _t860 = 8
                    else:
                        if self.match_lookahead_literal("INT128", 0):
                            _t861 = 5
                        else:
                            if self.match_lookahead_literal("INT", 0):
                                _t862 = 2
                            else:
                                if self.match_lookahead_literal("FLOAT", 0):
                                    _t863 = 3
                                else:
                                    if self.match_lookahead_literal("DATETIME", 0):
                                        _t864 = 7
                                    else:
                                        if self.match_lookahead_literal("DATE", 0):
                                            _t865 = 6
                                        else:
                                            if self.match_lookahead_literal("BOOLEAN", 0):
                                                _t866 = 10
                                            else:
                                                if self.match_lookahead_literal("(", 0):
                                                    _t867 = 9
                                                else:
                                                    _t867 = -1
                                                _t866 = _t867
                                            _t865 = _t866
                                        _t864 = _t865
                                    _t863 = _t864
                                _t862 = _t863
                            _t861 = _t862
                        _t860 = _t861
                    _t859 = _t860
                _t858 = _t859
            _t857 = _t858
        prediction445 = _t857
        if prediction445 == 10:
            _t869 = self.parse_boolean_type()
            boolean_type456 = _t869
            _t870 = logic_pb2.Type(boolean_type=boolean_type456)
            _t868 = _t870
        else:
            if prediction445 == 9:
                _t872 = self.parse_decimal_type()
                decimal_type455 = _t872
                _t873 = logic_pb2.Type(decimal_type=decimal_type455)
                _t871 = _t873
            else:
                if prediction445 == 8:
                    _t875 = self.parse_missing_type()
                    missing_type454 = _t875
                    _t876 = logic_pb2.Type(missing_type=missing_type454)
                    _t874 = _t876
                else:
                    if prediction445 == 7:
                        _t878 = self.parse_datetime_type()
                        datetime_type453 = _t878
                        _t879 = logic_pb2.Type(datetime_type=datetime_type453)
                        _t877 = _t879
                    else:
                        if prediction445 == 6:
                            _t881 = self.parse_date_type()
                            date_type452 = _t881
                            _t882 = logic_pb2.Type(date_type=date_type452)
                            _t880 = _t882
                        else:
                            if prediction445 == 5:
                                _t884 = self.parse_int128_type()
                                int128_type451 = _t884
                                _t885 = logic_pb2.Type(int128_type=int128_type451)
                                _t883 = _t885
                            else:
                                if prediction445 == 4:
                                    _t887 = self.parse_uint128_type()
                                    uint128_type450 = _t887
                                    _t888 = logic_pb2.Type(uint128_type=uint128_type450)
                                    _t886 = _t888
                                else:
                                    if prediction445 == 3:
                                        _t890 = self.parse_float_type()
                                        float_type449 = _t890
                                        _t891 = logic_pb2.Type(float_type=float_type449)
                                        _t889 = _t891
                                    else:
                                        if prediction445 == 2:
                                            _t893 = self.parse_int_type()
                                            int_type448 = _t893
                                            _t894 = logic_pb2.Type(int_type=int_type448)
                                            _t892 = _t894
                                        else:
                                            if prediction445 == 1:
                                                _t896 = self.parse_string_type()
                                                string_type447 = _t896
                                                _t897 = logic_pb2.Type(string_type=string_type447)
                                                _t895 = _t897
                                            else:
                                                if prediction445 == 0:
                                                    _t899 = self.parse_unspecified_type()
                                                    unspecified_type446 = _t899
                                                    _t900 = logic_pb2.Type(unspecified_type=unspecified_type446)
                                                    _t898 = _t900
                                                else:
                                                    raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t895 = _t898
                                            _t892 = _t895
                                        _t889 = _t892
                                    _t886 = _t889
                                _t883 = _t886
                            _t880 = _t883
                        _t877 = _t880
                    _t874 = _t877
                _t871 = _t874
            _t868 = _t871
        return _t868

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        self.consume_literal("UNKNOWN")
        _t901 = logic_pb2.UnspecifiedType()
        return _t901

    def parse_string_type(self) -> logic_pb2.StringType:
        self.consume_literal("STRING")
        _t902 = logic_pb2.StringType()
        return _t902

    def parse_int_type(self) -> logic_pb2.IntType:
        self.consume_literal("INT")
        _t903 = logic_pb2.IntType()
        return _t903

    def parse_float_type(self) -> logic_pb2.FloatType:
        self.consume_literal("FLOAT")
        _t904 = logic_pb2.FloatType()
        return _t904

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        self.consume_literal("UINT128")
        _t905 = logic_pb2.UInt128Type()
        return _t905

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        self.consume_literal("INT128")
        _t906 = logic_pb2.Int128Type()
        return _t906

    def parse_date_type(self) -> logic_pb2.DateType:
        self.consume_literal("DATE")
        _t907 = logic_pb2.DateType()
        return _t907

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        self.consume_literal("DATETIME")
        _t908 = logic_pb2.DateTimeType()
        return _t908

    def parse_missing_type(self) -> logic_pb2.MissingType:
        self.consume_literal("MISSING")
        _t909 = logic_pb2.MissingType()
        return _t909

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int457 = self.consume_terminal("INT")
        int_3458 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t910 = logic_pb2.DecimalType(precision=int(int457), scale=int(int_3458))
        return _t910

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal("BOOLEAN")
        _t911 = logic_pb2.BooleanType()
        return _t911

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs459 = []
        cond460 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond460:
            _t912 = self.parse_binding()
            item461 = _t912
            xs459.append(item461)
            cond460 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings462 = xs459
        return bindings462

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t914 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t915 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t916 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t917 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t918 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t919 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t920 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t921 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t922 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t923 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t924 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t925 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t926 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t927 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t928 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t929 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t930 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t931 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t932 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t933 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t934 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t935 = 10
                                                                                                else:
                                                                                                    _t935 = -1
                                                                                                _t934 = _t935
                                                                                            _t933 = _t934
                                                                                        _t932 = _t933
                                                                                    _t931 = _t932
                                                                                _t930 = _t931
                                                                            _t929 = _t930
                                                                        _t928 = _t929
                                                                    _t927 = _t928
                                                                _t926 = _t927
                                                            _t925 = _t926
                                                        _t924 = _t925
                                                    _t923 = _t924
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
        else:
            _t913 = -1
        prediction463 = _t913
        if prediction463 == 12:
            _t937 = self.parse_cast()
            cast476 = _t937
            _t938 = logic_pb2.Formula(cast=cast476)
            _t936 = _t938
        else:
            if prediction463 == 11:
                _t940 = self.parse_rel_atom()
                rel_atom475 = _t940
                _t941 = logic_pb2.Formula(rel_atom=rel_atom475)
                _t939 = _t941
            else:
                if prediction463 == 10:
                    _t943 = self.parse_primitive()
                    primitive474 = _t943
                    _t944 = logic_pb2.Formula(primitive=primitive474)
                    _t942 = _t944
                else:
                    if prediction463 == 9:
                        _t946 = self.parse_pragma()
                        pragma473 = _t946
                        _t947 = logic_pb2.Formula(pragma=pragma473)
                        _t945 = _t947
                    else:
                        if prediction463 == 8:
                            _t949 = self.parse_atom()
                            atom472 = _t949
                            _t950 = logic_pb2.Formula(atom=atom472)
                            _t948 = _t950
                        else:
                            if prediction463 == 7:
                                _t952 = self.parse_ffi()
                                ffi471 = _t952
                                _t953 = logic_pb2.Formula(ffi=ffi471)
                                _t951 = _t953
                            else:
                                if prediction463 == 6:
                                    _t955 = self.parse_not()
                                    not470 = _t955
                                    _t956 = logic_pb2.Formula()
                                    getattr(_t956, 'not').CopyFrom(not470)
                                    _t954 = _t956
                                else:
                                    if prediction463 == 5:
                                        _t958 = self.parse_disjunction()
                                        disjunction469 = _t958
                                        _t959 = logic_pb2.Formula(disjunction=disjunction469)
                                        _t957 = _t959
                                    else:
                                        if prediction463 == 4:
                                            _t961 = self.parse_conjunction()
                                            conjunction468 = _t961
                                            _t962 = logic_pb2.Formula(conjunction=conjunction468)
                                            _t960 = _t962
                                        else:
                                            if prediction463 == 3:
                                                _t964 = self.parse_reduce()
                                                reduce467 = _t964
                                                _t965 = logic_pb2.Formula(reduce=reduce467)
                                                _t963 = _t965
                                            else:
                                                if prediction463 == 2:
                                                    _t967 = self.parse_exists()
                                                    exists466 = _t967
                                                    _t968 = logic_pb2.Formula(exists=exists466)
                                                    _t966 = _t968
                                                else:
                                                    if prediction463 == 1:
                                                        _t970 = self.parse_false()
                                                        false465 = _t970
                                                        _t971 = logic_pb2.Formula(disjunction=false465)
                                                        _t969 = _t971
                                                    else:
                                                        if prediction463 == 0:
                                                            _t973 = self.parse_true()
                                                            true464 = _t973
                                                            _t974 = logic_pb2.Formula(conjunction=true464)
                                                            _t972 = _t974
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t969 = _t972
                                                    _t966 = _t969
                                                _t963 = _t966
                                            _t960 = _t963
                                        _t957 = _t960
                                    _t954 = _t957
                                _t951 = _t954
                            _t948 = _t951
                        _t945 = _t948
                    _t942 = _t945
                _t939 = _t942
            _t936 = _t939
        return _t936

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t975 = logic_pb2.Conjunction(args=[])
        return _t975

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t976 = logic_pb2.Disjunction(args=[])
        return _t976

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal("(")
        self.consume_literal("exists")
        _t977 = self.parse_bindings()
        bindings477 = _t977
        _t978 = self.parse_formula()
        formula478 = _t978
        self.consume_literal(")")
        _t979 = logic_pb2.Abstraction(vars=(list(bindings477[0]) + list(bindings477[1] if bindings477[1] is not None else [])), value=formula478)
        _t980 = logic_pb2.Exists(body=_t979)
        return _t980

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t981 = self.parse_abstraction()
        abstraction479 = _t981
        _t982 = self.parse_abstraction()
        abstraction_3480 = _t982
        _t983 = self.parse_terms()
        terms481 = _t983
        self.consume_literal(")")
        _t984 = logic_pb2.Reduce(op=abstraction479, body=abstraction_3480, terms=terms481)
        return _t984

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs482 = []
        cond483 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond483:
            _t985 = self.parse_term()
            item484 = _t985
            xs482.append(item484)
            cond483 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms485 = xs482
        self.consume_literal(")")
        return terms485

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_literal("true", 0):
            _t986 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t987 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t988 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t989 = 1
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t990 = 1
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t991 = 0
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t992 = 1
                                else:
                                    if self.match_lookahead_terminal("INT128", 0):
                                        _t993 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT", 0):
                                            _t994 = 1
                                        else:
                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                _t995 = 1
                                            else:
                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                    _t996 = 1
                                                else:
                                                    _t996 = -1
                                                _t995 = _t996
                                            _t994 = _t995
                                        _t993 = _t994
                                    _t992 = _t993
                                _t991 = _t992
                            _t990 = _t991
                        _t989 = _t990
                    _t988 = _t989
                _t987 = _t988
            _t986 = _t987
        prediction486 = _t986
        if prediction486 == 1:
            _t998 = self.parse_constant()
            constant488 = _t998
            _t999 = logic_pb2.Term(constant=constant488)
            _t997 = _t999
        else:
            if prediction486 == 0:
                _t1001 = self.parse_var()
                var487 = _t1001
                _t1002 = logic_pb2.Term(var=var487)
                _t1000 = _t1002
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t997 = _t1000
        return _t997

    def parse_var(self) -> logic_pb2.Var:
        symbol489 = self.consume_terminal("SYMBOL")
        _t1003 = logic_pb2.Var(name=symbol489)
        return _t1003

    def parse_constant(self) -> logic_pb2.Value:
        _t1004 = self.parse_value()
        value490 = _t1004
        return value490

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal("(")
        self.consume_literal("and")
        xs491 = []
        cond492 = self.match_lookahead_literal("(", 0)
        while cond492:
            _t1005 = self.parse_formula()
            item493 = _t1005
            xs491.append(item493)
            cond492 = self.match_lookahead_literal("(", 0)
        formulas494 = xs491
        self.consume_literal(")")
        _t1006 = logic_pb2.Conjunction(args=formulas494)
        return _t1006

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal("(")
        self.consume_literal("or")
        xs495 = []
        cond496 = self.match_lookahead_literal("(", 0)
        while cond496:
            _t1007 = self.parse_formula()
            item497 = _t1007
            xs495.append(item497)
            cond496 = self.match_lookahead_literal("(", 0)
        formulas498 = xs495
        self.consume_literal(")")
        _t1008 = logic_pb2.Disjunction(args=formulas498)
        return _t1008

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal("(")
        self.consume_literal("not")
        _t1009 = self.parse_formula()
        formula499 = _t1009
        self.consume_literal(")")
        _t1010 = logic_pb2.Not(arg=formula499)
        return _t1010

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1011 = self.parse_name()
        name500 = _t1011
        _t1012 = self.parse_ffi_args()
        ffi_args501 = _t1012
        _t1013 = self.parse_terms()
        terms502 = _t1013
        self.consume_literal(")")
        _t1014 = logic_pb2.FFI(name=name500, args=ffi_args501, terms=terms502)
        return _t1014

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol503 = self.consume_terminal("SYMBOL")
        return symbol503

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs504 = []
        cond505 = self.match_lookahead_literal("(", 0)
        while cond505:
            _t1015 = self.parse_abstraction()
            item506 = _t1015
            xs504.append(item506)
            cond505 = self.match_lookahead_literal("(", 0)
        abstractions507 = xs504
        self.consume_literal(")")
        return abstractions507

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1016 = self.parse_relation_id()
        relation_id508 = _t1016
        xs509 = []
        cond510 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond510:
            _t1017 = self.parse_term()
            item511 = _t1017
            xs509.append(item511)
            cond510 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms512 = xs509
        self.consume_literal(")")
        _t1018 = logic_pb2.Atom(name=relation_id508, terms=terms512)
        return _t1018

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1019 = self.parse_name()
        name513 = _t1019
        xs514 = []
        cond515 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond515:
            _t1020 = self.parse_term()
            item516 = _t1020
            xs514.append(item516)
            cond515 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms517 = xs514
        self.consume_literal(")")
        _t1021 = logic_pb2.Pragma(name=name513, terms=terms517)
        return _t1021

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1023 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1024 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1025 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1026 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1027 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1028 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1029 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1030 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1031 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1032 = 7
                                                else:
                                                    _t1032 = -1
                                                _t1031 = _t1032
                                            _t1030 = _t1031
                                        _t1029 = _t1030
                                    _t1028 = _t1029
                                _t1027 = _t1028
                            _t1026 = _t1027
                        _t1025 = _t1026
                    _t1024 = _t1025
                _t1023 = _t1024
            _t1022 = _t1023
        else:
            _t1022 = -1
        prediction518 = _t1022
        if prediction518 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1034 = self.parse_name()
            name528 = _t1034
            xs529 = []
            cond530 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            while cond530:
                _t1035 = self.parse_rel_term()
                item531 = _t1035
                xs529.append(item531)
                cond530 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            rel_terms532 = xs529
            self.consume_literal(")")
            _t1036 = logic_pb2.Primitive(name=name528, terms=rel_terms532)
            _t1033 = _t1036
        else:
            if prediction518 == 8:
                _t1038 = self.parse_divide()
                divide527 = _t1038
                _t1037 = divide527
            else:
                if prediction518 == 7:
                    _t1040 = self.parse_multiply()
                    multiply526 = _t1040
                    _t1039 = multiply526
                else:
                    if prediction518 == 6:
                        _t1042 = self.parse_minus()
                        minus525 = _t1042
                        _t1041 = minus525
                    else:
                        if prediction518 == 5:
                            _t1044 = self.parse_add()
                            add524 = _t1044
                            _t1043 = add524
                        else:
                            if prediction518 == 4:
                                _t1046 = self.parse_gt_eq()
                                gt_eq523 = _t1046
                                _t1045 = gt_eq523
                            else:
                                if prediction518 == 3:
                                    _t1048 = self.parse_gt()
                                    gt522 = _t1048
                                    _t1047 = gt522
                                else:
                                    if prediction518 == 2:
                                        _t1050 = self.parse_lt_eq()
                                        lt_eq521 = _t1050
                                        _t1049 = lt_eq521
                                    else:
                                        if prediction518 == 1:
                                            _t1052 = self.parse_lt()
                                            lt520 = _t1052
                                            _t1051 = lt520
                                        else:
                                            if prediction518 == 0:
                                                _t1054 = self.parse_eq()
                                                eq519 = _t1054
                                                _t1053 = eq519
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1051 = _t1053
                                        _t1049 = _t1051
                                    _t1047 = _t1049
                                _t1045 = _t1047
                            _t1043 = _t1045
                        _t1041 = _t1043
                    _t1039 = _t1041
                _t1037 = _t1039
            _t1033 = _t1037
        return _t1033

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("=")
        _t1055 = self.parse_term()
        term533 = _t1055
        _t1056 = self.parse_term()
        term_3534 = _t1056
        self.consume_literal(")")
        _t1057 = logic_pb2.RelTerm(term=term533)
        _t1058 = logic_pb2.RelTerm(term=term_3534)
        _t1059 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1057, _t1058])
        return _t1059

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("<")
        _t1060 = self.parse_term()
        term535 = _t1060
        _t1061 = self.parse_term()
        term_3536 = _t1061
        self.consume_literal(")")
        _t1062 = logic_pb2.RelTerm(term=term535)
        _t1063 = logic_pb2.RelTerm(term=term_3536)
        _t1064 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1062, _t1063])
        return _t1064

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1065 = self.parse_term()
        term537 = _t1065
        _t1066 = self.parse_term()
        term_3538 = _t1066
        self.consume_literal(")")
        _t1067 = logic_pb2.RelTerm(term=term537)
        _t1068 = logic_pb2.RelTerm(term=term_3538)
        _t1069 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1067, _t1068])
        return _t1069

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal(">")
        _t1070 = self.parse_term()
        term539 = _t1070
        _t1071 = self.parse_term()
        term_3540 = _t1071
        self.consume_literal(")")
        _t1072 = logic_pb2.RelTerm(term=term539)
        _t1073 = logic_pb2.RelTerm(term=term_3540)
        _t1074 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1072, _t1073])
        return _t1074

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1075 = self.parse_term()
        term541 = _t1075
        _t1076 = self.parse_term()
        term_3542 = _t1076
        self.consume_literal(")")
        _t1077 = logic_pb2.RelTerm(term=term541)
        _t1078 = logic_pb2.RelTerm(term=term_3542)
        _t1079 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1077, _t1078])
        return _t1079

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("+")
        _t1080 = self.parse_term()
        term543 = _t1080
        _t1081 = self.parse_term()
        term_3544 = _t1081
        _t1082 = self.parse_term()
        term_4545 = _t1082
        self.consume_literal(")")
        _t1083 = logic_pb2.RelTerm(term=term543)
        _t1084 = logic_pb2.RelTerm(term=term_3544)
        _t1085 = logic_pb2.RelTerm(term=term_4545)
        _t1086 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1083, _t1084, _t1085])
        return _t1086

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("-")
        _t1087 = self.parse_term()
        term546 = _t1087
        _t1088 = self.parse_term()
        term_3547 = _t1088
        _t1089 = self.parse_term()
        term_4548 = _t1089
        self.consume_literal(")")
        _t1090 = logic_pb2.RelTerm(term=term546)
        _t1091 = logic_pb2.RelTerm(term=term_3547)
        _t1092 = logic_pb2.RelTerm(term=term_4548)
        _t1093 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1090, _t1091, _t1092])
        return _t1093

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("*")
        _t1094 = self.parse_term()
        term549 = _t1094
        _t1095 = self.parse_term()
        term_3550 = _t1095
        _t1096 = self.parse_term()
        term_4551 = _t1096
        self.consume_literal(")")
        _t1097 = logic_pb2.RelTerm(term=term549)
        _t1098 = logic_pb2.RelTerm(term=term_3550)
        _t1099 = logic_pb2.RelTerm(term=term_4551)
        _t1100 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1097, _t1098, _t1099])
        return _t1100

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("/")
        _t1101 = self.parse_term()
        term552 = _t1101
        _t1102 = self.parse_term()
        term_3553 = _t1102
        _t1103 = self.parse_term()
        term_4554 = _t1103
        self.consume_literal(")")
        _t1104 = logic_pb2.RelTerm(term=term552)
        _t1105 = logic_pb2.RelTerm(term=term_3553)
        _t1106 = logic_pb2.RelTerm(term=term_4554)
        _t1107 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1104, _t1105, _t1106])
        return _t1107

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_literal("true", 0):
            _t1108 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1109 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1110 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1111 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1112 = 0
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1113 = 1
                            else:
                                if self.match_lookahead_terminal("SYMBOL", 0):
                                    _t1114 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1115 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1116 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1117 = 1
                                            else:
                                                if self.match_lookahead_terminal("FLOAT", 0):
                                                    _t1118 = 1
                                                else:
                                                    if self.match_lookahead_terminal("DECIMAL", 0):
                                                        _t1119 = 1
                                                    else:
                                                        _t1119 = -1
                                                    _t1118 = _t1119
                                                _t1117 = _t1118
                                            _t1116 = _t1117
                                        _t1115 = _t1116
                                    _t1114 = _t1115
                                _t1113 = _t1114
                            _t1112 = _t1113
                        _t1111 = _t1112
                    _t1110 = _t1111
                _t1109 = _t1110
            _t1108 = _t1109
        prediction555 = _t1108
        if prediction555 == 1:
            _t1121 = self.parse_term()
            term557 = _t1121
            _t1122 = logic_pb2.RelTerm(term=term557)
            _t1120 = _t1122
        else:
            if prediction555 == 0:
                _t1124 = self.parse_specialized_value()
                specialized_value556 = _t1124
                _t1125 = logic_pb2.RelTerm(specialized_value=specialized_value556)
                _t1123 = _t1125
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1120 = _t1123
        return _t1120

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal("#")
        _t1126 = self.parse_value()
        value558 = _t1126
        return value558

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1127 = self.parse_name()
        name559 = _t1127
        xs560 = []
        cond561 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond561:
            _t1128 = self.parse_rel_term()
            item562 = _t1128
            xs560.append(item562)
            cond561 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        rel_terms563 = xs560
        self.consume_literal(")")
        _t1129 = logic_pb2.RelAtom(name=name559, terms=rel_terms563)
        return _t1129

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1130 = self.parse_term()
        term564 = _t1130
        _t1131 = self.parse_term()
        term_3565 = _t1131
        self.consume_literal(")")
        _t1132 = logic_pb2.Cast(input=term564, result=term_3565)
        return _t1132

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs566 = []
        cond567 = self.match_lookahead_literal("(", 0)
        while cond567:
            _t1133 = self.parse_attribute()
            item568 = _t1133
            xs566.append(item568)
            cond567 = self.match_lookahead_literal("(", 0)
        attributes569 = xs566
        self.consume_literal(")")
        return attributes569

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1134 = self.parse_name()
        name570 = _t1134
        xs571 = []
        cond572 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond572:
            _t1135 = self.parse_value()
            item573 = _t1135
            xs571.append(item573)
            cond572 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        values574 = xs571
        self.consume_literal(")")
        _t1136 = logic_pb2.Attribute(name=name570, args=values574)
        return _t1136

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs575 = []
        cond576 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond576:
            _t1137 = self.parse_relation_id()
            item577 = _t1137
            xs575.append(item577)
            cond576 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids578 = xs575
        _t1138 = self.parse_script()
        script579 = _t1138
        self.consume_literal(")")
        _t1139 = logic_pb2.Algorithm(body=script579)
        getattr(_t1139, 'global').extend(relation_ids578)
        return _t1139

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal("(")
        self.consume_literal("script")
        xs580 = []
        cond581 = self.match_lookahead_literal("(", 0)
        while cond581:
            _t1140 = self.parse_construct()
            item582 = _t1140
            xs580.append(item582)
            cond581 = self.match_lookahead_literal("(", 0)
        constructs583 = xs580
        self.consume_literal(")")
        _t1141 = logic_pb2.Script(constructs=constructs583)
        return _t1141

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1143 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1144 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1145 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1146 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1147 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1148 = 1
                                else:
                                    _t1148 = -1
                                _t1147 = _t1148
                            _t1146 = _t1147
                        _t1145 = _t1146
                    _t1144 = _t1145
                _t1143 = _t1144
            _t1142 = _t1143
        else:
            _t1142 = -1
        prediction584 = _t1142
        if prediction584 == 1:
            _t1150 = self.parse_instruction()
            instruction586 = _t1150
            _t1151 = logic_pb2.Construct(instruction=instruction586)
            _t1149 = _t1151
        else:
            if prediction584 == 0:
                _t1153 = self.parse_loop()
                loop585 = _t1153
                _t1154 = logic_pb2.Construct(loop=loop585)
                _t1152 = _t1154
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1149 = _t1152
        return _t1149

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1155 = self.parse_init()
        init587 = _t1155
        _t1156 = self.parse_script()
        script588 = _t1156
        self.consume_literal(")")
        _t1157 = logic_pb2.Loop(init=init587, body=script588)
        return _t1157

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs589 = []
        cond590 = self.match_lookahead_literal("(", 0)
        while cond590:
            _t1158 = self.parse_instruction()
            item591 = _t1158
            xs589.append(item591)
            cond590 = self.match_lookahead_literal("(", 0)
        instructions592 = xs589
        self.consume_literal(")")
        return instructions592

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1160 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1161 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1162 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1163 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1164 = 0
                            else:
                                _t1164 = -1
                            _t1163 = _t1164
                        _t1162 = _t1163
                    _t1161 = _t1162
                _t1160 = _t1161
            _t1159 = _t1160
        else:
            _t1159 = -1
        prediction593 = _t1159
        if prediction593 == 4:
            _t1166 = self.parse_monus_def()
            monus_def598 = _t1166
            _t1167 = logic_pb2.Instruction(monus_def=monus_def598)
            _t1165 = _t1167
        else:
            if prediction593 == 3:
                _t1169 = self.parse_monoid_def()
                monoid_def597 = _t1169
                _t1170 = logic_pb2.Instruction(monoid_def=monoid_def597)
                _t1168 = _t1170
            else:
                if prediction593 == 2:
                    _t1172 = self.parse_break()
                    break596 = _t1172
                    _t1173 = logic_pb2.Instruction()
                    getattr(_t1173, 'break').CopyFrom(break596)
                    _t1171 = _t1173
                else:
                    if prediction593 == 1:
                        _t1175 = self.parse_upsert()
                        upsert595 = _t1175
                        _t1176 = logic_pb2.Instruction(upsert=upsert595)
                        _t1174 = _t1176
                    else:
                        if prediction593 == 0:
                            _t1178 = self.parse_assign()
                            assign594 = _t1178
                            _t1179 = logic_pb2.Instruction(assign=assign594)
                            _t1177 = _t1179
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1174 = _t1177
                    _t1171 = _t1174
                _t1168 = _t1171
            _t1165 = _t1168
        return _t1165

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1180 = self.parse_relation_id()
        relation_id599 = _t1180
        _t1181 = self.parse_abstraction()
        abstraction600 = _t1181
        if self.match_lookahead_literal("(", 0):
            _t1183 = self.parse_attrs()
            _t1182 = _t1183
        else:
            _t1182 = None
        attrs601 = _t1182
        self.consume_literal(")")
        _t1184 = logic_pb2.Assign(name=relation_id599, body=abstraction600, attrs=(attrs601 if attrs601 is not None else []))
        return _t1184

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1185 = self.parse_relation_id()
        relation_id602 = _t1185
        _t1186 = self.parse_abstraction_with_arity()
        abstraction_with_arity603 = _t1186
        if self.match_lookahead_literal("(", 0):
            _t1188 = self.parse_attrs()
            _t1187 = _t1188
        else:
            _t1187 = None
        attrs604 = _t1187
        self.consume_literal(")")
        _t1189 = logic_pb2.Upsert(name=relation_id602, body=abstraction_with_arity603[0], attrs=(attrs604 if attrs604 is not None else []), value_arity=abstraction_with_arity603[1])
        return _t1189

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1190 = self.parse_bindings()
        bindings605 = _t1190
        _t1191 = self.parse_formula()
        formula606 = _t1191
        self.consume_literal(")")
        _t1192 = logic_pb2.Abstraction(vars=(list(bindings605[0]) + list(bindings605[1] if bindings605[1] is not None else [])), value=formula606)
        return (_t1192, len(bindings605[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal("(")
        self.consume_literal("break")
        _t1193 = self.parse_relation_id()
        relation_id607 = _t1193
        _t1194 = self.parse_abstraction()
        abstraction608 = _t1194
        if self.match_lookahead_literal("(", 0):
            _t1196 = self.parse_attrs()
            _t1195 = _t1196
        else:
            _t1195 = None
        attrs609 = _t1195
        self.consume_literal(")")
        _t1197 = logic_pb2.Break(name=relation_id607, body=abstraction608, attrs=(attrs609 if attrs609 is not None else []))
        return _t1197

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1198 = self.parse_monoid()
        monoid610 = _t1198
        _t1199 = self.parse_relation_id()
        relation_id611 = _t1199
        _t1200 = self.parse_abstraction_with_arity()
        abstraction_with_arity612 = _t1200
        if self.match_lookahead_literal("(", 0):
            _t1202 = self.parse_attrs()
            _t1201 = _t1202
        else:
            _t1201 = None
        attrs613 = _t1201
        self.consume_literal(")")
        _t1203 = logic_pb2.MonoidDef(monoid=monoid610, name=relation_id611, body=abstraction_with_arity612[0], attrs=(attrs613 if attrs613 is not None else []), value_arity=abstraction_with_arity612[1])
        return _t1203

    def parse_monoid(self) -> logic_pb2.Monoid:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1205 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1206 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1207 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1208 = 2
                        else:
                            _t1208 = -1
                        _t1207 = _t1208
                    _t1206 = _t1207
                _t1205 = _t1206
            _t1204 = _t1205
        else:
            _t1204 = -1
        prediction614 = _t1204
        if prediction614 == 3:
            _t1210 = self.parse_sum_monoid()
            sum_monoid618 = _t1210
            _t1211 = logic_pb2.Monoid(sum_monoid=sum_monoid618)
            _t1209 = _t1211
        else:
            if prediction614 == 2:
                _t1213 = self.parse_max_monoid()
                max_monoid617 = _t1213
                _t1214 = logic_pb2.Monoid(max_monoid=max_monoid617)
                _t1212 = _t1214
            else:
                if prediction614 == 1:
                    _t1216 = self.parse_min_monoid()
                    min_monoid616 = _t1216
                    _t1217 = logic_pb2.Monoid(min_monoid=min_monoid616)
                    _t1215 = _t1217
                else:
                    if prediction614 == 0:
                        _t1219 = self.parse_or_monoid()
                        or_monoid615 = _t1219
                        _t1220 = logic_pb2.Monoid(or_monoid=or_monoid615)
                        _t1218 = _t1220
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1215 = _t1218
                _t1212 = _t1215
            _t1209 = _t1212
        return _t1209

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1221 = logic_pb2.OrMonoid()
        return _t1221

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        self.consume_literal("(")
        self.consume_literal("min")
        _t1222 = self.parse_type()
        type619 = _t1222
        self.consume_literal(")")
        _t1223 = logic_pb2.MinMonoid(type=type619)
        return _t1223

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        self.consume_literal("(")
        self.consume_literal("max")
        _t1224 = self.parse_type()
        type620 = _t1224
        self.consume_literal(")")
        _t1225 = logic_pb2.MaxMonoid(type=type620)
        return _t1225

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1226 = self.parse_type()
        type621 = _t1226
        self.consume_literal(")")
        _t1227 = logic_pb2.SumMonoid(type=type621)
        return _t1227

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1228 = self.parse_monoid()
        monoid622 = _t1228
        _t1229 = self.parse_relation_id()
        relation_id623 = _t1229
        _t1230 = self.parse_abstraction_with_arity()
        abstraction_with_arity624 = _t1230
        if self.match_lookahead_literal("(", 0):
            _t1232 = self.parse_attrs()
            _t1231 = _t1232
        else:
            _t1231 = None
        attrs625 = _t1231
        self.consume_literal(")")
        _t1233 = logic_pb2.MonusDef(monoid=monoid622, name=relation_id623, body=abstraction_with_arity624[0], attrs=(attrs625 if attrs625 is not None else []), value_arity=abstraction_with_arity624[1])
        return _t1233

    def parse_constraint(self) -> logic_pb2.Constraint:
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1234 = self.parse_relation_id()
        relation_id626 = _t1234
        _t1235 = self.parse_abstraction()
        abstraction627 = _t1235
        _t1236 = self.parse_functional_dependency_keys()
        functional_dependency_keys628 = _t1236
        _t1237 = self.parse_functional_dependency_values()
        functional_dependency_values629 = _t1237
        self.consume_literal(")")
        _t1238 = logic_pb2.FunctionalDependency(guard=abstraction627, keys=functional_dependency_keys628, values=functional_dependency_values629)
        _t1239 = logic_pb2.Constraint(name=relation_id626, functional_dependency=_t1238)
        return _t1239

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs630 = []
        cond631 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond631:
            _t1240 = self.parse_var()
            item632 = _t1240
            xs630.append(item632)
            cond631 = self.match_lookahead_terminal("SYMBOL", 0)
        vars633 = xs630
        self.consume_literal(")")
        return vars633

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs634 = []
        cond635 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond635:
            _t1241 = self.parse_var()
            item636 = _t1241
            xs634.append(item636)
            cond635 = self.match_lookahead_terminal("SYMBOL", 0)
        vars637 = xs634
        self.consume_literal(")")
        return vars637

    def parse_data(self) -> logic_pb2.Data:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("rel_edb", 1):
                _t1243 = 0
            else:
                if self.match_lookahead_literal("csv_data", 1):
                    _t1244 = 2
                else:
                    if self.match_lookahead_literal("betree_relation", 1):
                        _t1245 = 1
                    else:
                        _t1245 = -1
                    _t1244 = _t1245
                _t1243 = _t1244
            _t1242 = _t1243
        else:
            _t1242 = -1
        prediction638 = _t1242
        if prediction638 == 2:
            _t1247 = self.parse_csv_data()
            csv_data641 = _t1247
            _t1248 = logic_pb2.Data(csv_data=csv_data641)
            _t1246 = _t1248
        else:
            if prediction638 == 1:
                _t1250 = self.parse_betree_relation()
                betree_relation640 = _t1250
                _t1251 = logic_pb2.Data(betree_relation=betree_relation640)
                _t1249 = _t1251
            else:
                if prediction638 == 0:
                    _t1253 = self.parse_rel_edb()
                    rel_edb639 = _t1253
                    _t1254 = logic_pb2.Data(rel_edb=rel_edb639)
                    _t1252 = _t1254
                else:
                    raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t1249 = _t1252
            _t1246 = _t1249
        return _t1246

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        self.consume_literal("(")
        self.consume_literal("rel_edb")
        _t1255 = self.parse_relation_id()
        relation_id642 = _t1255
        _t1256 = self.parse_rel_edb_path()
        rel_edb_path643 = _t1256
        _t1257 = self.parse_rel_edb_types()
        rel_edb_types644 = _t1257
        self.consume_literal(")")
        _t1258 = logic_pb2.RelEDB(target_id=relation_id642, path=rel_edb_path643, types=rel_edb_types644)
        return _t1258

    def parse_rel_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs645 = []
        cond646 = self.match_lookahead_terminal("STRING", 0)
        while cond646:
            item647 = self.consume_terminal("STRING")
            xs645.append(item647)
            cond646 = self.match_lookahead_terminal("STRING", 0)
        strings648 = xs645
        self.consume_literal("]")
        return strings648

    def parse_rel_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs649 = []
        cond650 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond650:
            _t1259 = self.parse_type()
            item651 = _t1259
            xs649.append(item651)
            cond650 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types652 = xs649
        self.consume_literal("]")
        return types652

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1260 = self.parse_relation_id()
        relation_id653 = _t1260
        _t1261 = self.parse_betree_info()
        betree_info654 = _t1261
        self.consume_literal(")")
        _t1262 = logic_pb2.BeTreeRelation(name=relation_id653, relation_info=betree_info654)
        return _t1262

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1263 = self.parse_betree_info_key_types()
        betree_info_key_types655 = _t1263
        _t1264 = self.parse_betree_info_value_types()
        betree_info_value_types656 = _t1264
        _t1265 = self.parse_config_dict()
        config_dict657 = _t1265
        self.consume_literal(")")
        _t1266 = self.construct_betree_info(betree_info_key_types655, betree_info_value_types656, config_dict657)
        return _t1266

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs658 = []
        cond659 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond659:
            _t1267 = self.parse_type()
            item660 = _t1267
            xs658.append(item660)
            cond659 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types661 = xs658
        self.consume_literal(")")
        return types661

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs662 = []
        cond663 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond663:
            _t1268 = self.parse_type()
            item664 = _t1268
            xs662.append(item664)
            cond663 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types665 = xs662
        self.consume_literal(")")
        return types665

    def parse_csv_data(self) -> logic_pb2.CSVData:
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1269 = self.parse_csvlocator()
        csvlocator666 = _t1269
        _t1270 = self.parse_csv_config()
        csv_config667 = _t1270
        _t1271 = self.parse_csv_columns()
        csv_columns668 = _t1271
        _t1272 = self.parse_csv_asof()
        csv_asof669 = _t1272
        self.consume_literal(")")
        _t1273 = logic_pb2.CSVData(locator=csvlocator666, config=csv_config667, columns=csv_columns668, asof=csv_asof669)
        return _t1273

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1275 = self.parse_csv_locator_paths()
            _t1274 = _t1275
        else:
            _t1274 = None
        csv_locator_paths670 = _t1274
        if self.match_lookahead_literal("(", 0):
            _t1277 = self.parse_csv_locator_inline_data()
            _t1276 = _t1277
        else:
            _t1276 = None
        csv_locator_inline_data671 = _t1276
        self.consume_literal(")")
        _t1278 = logic_pb2.CSVLocator(paths=(csv_locator_paths670 if csv_locator_paths670 is not None else []), inline_data=(csv_locator_inline_data671 if csv_locator_inline_data671 is not None else "").encode())
        return _t1278

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs672 = []
        cond673 = self.match_lookahead_terminal("STRING", 0)
        while cond673:
            item674 = self.consume_terminal("STRING")
            xs672.append(item674)
            cond673 = self.match_lookahead_terminal("STRING", 0)
        strings675 = xs672
        self.consume_literal(")")
        return strings675

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string676 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string676

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1279 = self.parse_config_dict()
        config_dict677 = _t1279
        self.consume_literal(")")
        _t1280 = self.construct_csv_config(config_dict677)
        return _t1280

    def parse_csv_columns(self) -> Sequence[logic_pb2.CSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs678 = []
        cond679 = self.match_lookahead_literal("(", 0)
        while cond679:
            _t1281 = self.parse_csv_column()
            item680 = _t1281
            xs678.append(item680)
            cond679 = self.match_lookahead_literal("(", 0)
        csv_columns681 = xs678
        self.consume_literal(")")
        return csv_columns681

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        self.consume_literal("(")
        self.consume_literal("column")
        _t1282 = self.parse_csv_column_path()
        csv_column_path682 = _t1282
        if ((self.match_lookahead_literal(":", 0) or self.match_lookahead_literal("[", 0)) or self.match_lookahead_terminal("UINT128", 0)):
            _t1284 = self.parse_csv_column_tail()
            _t1283 = _t1284
        else:
            _t1283 = None
        csv_column_tail683 = _t1283
        self.consume_literal(")")
        _t1285 = self.construct_csv_column(csv_column_path682, csv_column_tail683)
        return _t1285

    def parse_csv_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1286 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1287 = 0
            else:
                _t1287 = -1
            _t1286 = _t1287
        prediction684 = _t1286
        if prediction684 == 1:
            self.consume_literal("[")
            xs686 = []
            cond687 = self.match_lookahead_terminal("STRING", 0)
            while cond687:
                item688 = self.consume_terminal("STRING")
                xs686.append(item688)
                cond687 = self.match_lookahead_terminal("STRING", 0)
            strings689 = xs686
            self.consume_literal("]")
            _t1288 = strings689
        else:
            if prediction684 == 0:
                string685 = self.consume_terminal("STRING")
                _t1289 = [string685]
            else:
                raise ParseError("Unexpected token in csv_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1288 = _t1289
        return _t1288

    def parse_csv_column_tail(self) -> tuple[Optional[logic_pb2.RelationId], Sequence[logic_pb2.Type]]:
        if self.match_lookahead_literal("[", 0):
            _t1290 = 1
        else:
            if self.match_lookahead_literal(":", 0):
                _t1291 = 0
            else:
                if self.match_lookahead_terminal("UINT128", 0):
                    _t1292 = 0
                else:
                    _t1292 = -1
                _t1291 = _t1292
            _t1290 = _t1291
        prediction690 = _t1290
        if prediction690 == 1:
            self.consume_literal("[")
            xs696 = []
            cond697 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
            while cond697:
                _t1294 = self.parse_type()
                item698 = _t1294
                xs696.append(item698)
                cond697 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
            types699 = xs696
            self.consume_literal("]")
            _t1293 = (None, types699,)
        else:
            if prediction690 == 0:
                _t1296 = self.parse_relation_id()
                relation_id691 = _t1296
                self.consume_literal("[")
                xs692 = []
                cond693 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
                while cond693:
                    _t1297 = self.parse_type()
                    item694 = _t1297
                    xs692.append(item694)
                    cond693 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
                types695 = xs692
                self.consume_literal("]")
                _t1295 = (relation_id691, types695,)
            else:
                raise ParseError("Unexpected token in csv_column_tail" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1293 = _t1295
        return _t1293

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string700 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string700

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1298 = self.parse_fragment_id()
        fragment_id701 = _t1298
        self.consume_literal(")")
        _t1299 = transactions_pb2.Undefine(fragment_id=fragment_id701)
        return _t1299

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal("(")
        self.consume_literal("context")
        xs702 = []
        cond703 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond703:
            _t1300 = self.parse_relation_id()
            item704 = _t1300
            xs702.append(item704)
            cond703 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids705 = xs702
        self.consume_literal(")")
        _t1301 = transactions_pb2.Context(relations=relation_ids705)
        return _t1301

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t1302 = self.parse_rel_edb_path()
        rel_edb_path706 = _t1302
        _t1303 = self.parse_relation_id()
        relation_id707 = _t1303
        self.consume_literal(")")
        _t1304 = transactions_pb2.Snapshot(destination_path=rel_edb_path706, source_relation=relation_id707)
        return _t1304

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs708 = []
        cond709 = self.match_lookahead_literal("(", 0)
        while cond709:
            _t1305 = self.parse_read()
            item710 = _t1305
            xs708.append(item710)
            cond709 = self.match_lookahead_literal("(", 0)
        reads711 = xs708
        self.consume_literal(")")
        return reads711

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1307 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1308 = 1
                else:
                    if self.match_lookahead_literal("export", 1):
                        _t1309 = 4
                    else:
                        if self.match_lookahead_literal("demand", 1):
                            _t1310 = 0
                        else:
                            if self.match_lookahead_literal("abort", 1):
                                _t1311 = 3
                            else:
                                _t1311 = -1
                            _t1310 = _t1311
                        _t1309 = _t1310
                    _t1308 = _t1309
                _t1307 = _t1308
            _t1306 = _t1307
        else:
            _t1306 = -1
        prediction712 = _t1306
        if prediction712 == 4:
            _t1313 = self.parse_export()
            export717 = _t1313
            _t1314 = transactions_pb2.Read(export=export717)
            _t1312 = _t1314
        else:
            if prediction712 == 3:
                _t1316 = self.parse_abort()
                abort716 = _t1316
                _t1317 = transactions_pb2.Read(abort=abort716)
                _t1315 = _t1317
            else:
                if prediction712 == 2:
                    _t1319 = self.parse_what_if()
                    what_if715 = _t1319
                    _t1320 = transactions_pb2.Read(what_if=what_if715)
                    _t1318 = _t1320
                else:
                    if prediction712 == 1:
                        _t1322 = self.parse_output()
                        output714 = _t1322
                        _t1323 = transactions_pb2.Read(output=output714)
                        _t1321 = _t1323
                    else:
                        if prediction712 == 0:
                            _t1325 = self.parse_demand()
                            demand713 = _t1325
                            _t1326 = transactions_pb2.Read(demand=demand713)
                            _t1324 = _t1326
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1321 = _t1324
                    _t1318 = _t1321
                _t1315 = _t1318
            _t1312 = _t1315
        return _t1312

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1327 = self.parse_relation_id()
        relation_id718 = _t1327
        self.consume_literal(")")
        _t1328 = transactions_pb2.Demand(relation_id=relation_id718)
        return _t1328

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal("(")
        self.consume_literal("output")
        _t1329 = self.parse_name()
        name719 = _t1329
        _t1330 = self.parse_relation_id()
        relation_id720 = _t1330
        self.consume_literal(")")
        _t1331 = transactions_pb2.Output(name=name719, relation_id=relation_id720)
        return _t1331

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t1332 = self.parse_name()
        name721 = _t1332
        _t1333 = self.parse_epoch()
        epoch722 = _t1333
        self.consume_literal(")")
        _t1334 = transactions_pb2.WhatIf(branch=name721, epoch=epoch722)
        return _t1334

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t1336 = self.parse_name()
            _t1335 = _t1336
        else:
            _t1335 = None
        name723 = _t1335
        _t1337 = self.parse_relation_id()
        relation_id724 = _t1337
        self.consume_literal(")")
        _t1338 = transactions_pb2.Abort(name=(name723 if name723 is not None else "abort"), relation_id=relation_id724)
        return _t1338

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal("(")
        self.consume_literal("export")
        _t1339 = self.parse_export_csv_config()
        export_csv_config725 = _t1339
        self.consume_literal(")")
        _t1340 = transactions_pb2.Export(csv_config=export_csv_config725)
        return _t1340

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal("(")
        self.consume_literal("export_csv_config")
        _t1341 = self.parse_export_csv_path()
        export_csv_path726 = _t1341
        _t1342 = self.parse_export_csv_columns()
        export_csv_columns727 = _t1342
        _t1343 = self.parse_config_dict()
        config_dict728 = _t1343
        self.consume_literal(")")
        _t1344 = self.export_csv_config(export_csv_path726, export_csv_columns727, config_dict728)
        return _t1344

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string729 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string729

    def parse_export_csv_columns(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs730 = []
        cond731 = self.match_lookahead_literal("(", 0)
        while cond731:
            _t1345 = self.parse_export_csv_column()
            item732 = _t1345
            xs730.append(item732)
            cond731 = self.match_lookahead_literal("(", 0)
        export_csv_columns733 = xs730
        self.consume_literal(")")
        return export_csv_columns733

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal("(")
        self.consume_literal("column")
        string734 = self.consume_terminal("STRING")
        _t1346 = self.parse_relation_id()
        relation_id735 = _t1346
        self.consume_literal(")")
        _t1347 = transactions_pb2.ExportCSVColumn(column_name=string734, column_data=relation_id735)
        return _t1347


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
