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
        hash_bytes = hashlib.sha256(name.encode()).digest()
        id_low = int.from_bytes(hash_bytes[:8], byteorder='little')
        id_high = int.from_bytes(hash_bytes[8:16], byteorder='little')
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
            _t1339 = value.HasField("int_value")
        else:
            _t1339 = False
        if _t1339:
            assert value is not None
            return int(value.int_value)
        else:
            _t1340 = None
        return int(default)

    def _extract_value_int64(self, value: Optional[logic_pb2.Value], default: int) -> int:
        if value is not None:
            assert value is not None
            _t1341 = value.HasField("int_value")
        else:
            _t1341 = False
        if _t1341:
            assert value is not None
            return value.int_value
        else:
            _t1342 = None
        return default

    def _extract_value_string(self, value: Optional[logic_pb2.Value], default: str) -> str:
        if value is not None:
            assert value is not None
            _t1343 = value.HasField("string_value")
        else:
            _t1343 = False
        if _t1343:
            assert value is not None
            return value.string_value
        else:
            _t1344 = None
        return default

    def _extract_value_boolean(self, value: Optional[logic_pb2.Value], default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t1345 = value.HasField("boolean_value")
        else:
            _t1345 = False
        if _t1345:
            assert value is not None
            return value.boolean_value
        else:
            _t1346 = None
        return default

    def _extract_value_string_list(self, value: Optional[logic_pb2.Value], default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t1347 = value.HasField("string_value")
        else:
            _t1347 = False
        if _t1347:
            assert value is not None
            return [value.string_value]
        else:
            _t1348 = None
        return default

    def _try_extract_value_int64(self, value: Optional[logic_pb2.Value]) -> Optional[int]:
        if value is not None:
            assert value is not None
            _t1349 = value.HasField("int_value")
        else:
            _t1349 = False
        if _t1349:
            assert value is not None
            return value.int_value
        else:
            _t1350 = None
        return None

    def _try_extract_value_float64(self, value: Optional[logic_pb2.Value]) -> Optional[float]:
        if value is not None:
            assert value is not None
            _t1351 = value.HasField("float_value")
        else:
            _t1351 = False
        if _t1351:
            assert value is not None
            return value.float_value
        else:
            _t1352 = None
        return None

    def _try_extract_value_bytes(self, value: Optional[logic_pb2.Value]) -> Optional[bytes]:
        if value is not None:
            assert value is not None
            _t1353 = value.HasField("string_value")
        else:
            _t1353 = False
        if _t1353:
            assert value is not None
            return value.string_value.encode()
        else:
            _t1354 = None
        return None

    def _try_extract_value_uint128(self, value: Optional[logic_pb2.Value]) -> Optional[logic_pb2.UInt128Value]:
        if value is not None:
            assert value is not None
            _t1355 = value.HasField("uint128_value")
        else:
            _t1355 = False
        if _t1355:
            assert value is not None
            return value.uint128_value
        else:
            _t1356 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1357 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t1357
        _t1358 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t1358
        _t1359 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t1359
        _t1360 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t1360
        _t1361 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t1361
        _t1362 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t1362
        _t1363 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t1363
        _t1364 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t1364
        _t1365 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t1365
        _t1366 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t1366
        _t1367 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t1367
        _t1368 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t1368

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1369 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t1369
        _t1370 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t1370
        _t1371 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t1371
        _t1372 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t1372
        _t1373 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1373
        _t1374 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t1374
        _t1375 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t1375
        _t1376 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t1376
        _t1377 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t1377
        _t1378 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1378
        _t1379 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1379

    def default_configure(self) -> transactions_pb2.Configure:
        _t1380 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1380
        _t1381 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1381

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
        _t1382 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1382
        _t1383 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t1383
        _t1384 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1384

    def export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1385 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t1385
        _t1386 = self._extract_value_string(config.get("compression"), "")
        compression = _t1386
        _t1387 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t1387
        _t1388 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t1388
        _t1389 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t1389
        _t1390 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t1390
        _t1391 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t1391
        _t1392 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1392

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t733 = self.parse_configure()
            _t732 = _t733
        else:
            _t732 = None
        configure366 = _t732
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t735 = self.parse_sync()
            _t734 = _t735
        else:
            _t734 = None
        sync367 = _t734
        xs368 = []
        cond369 = self.match_lookahead_literal("(", 0)
        while cond369:
            _t736 = self.parse_epoch()
            item370 = _t736
            xs368.append(item370)
            cond369 = self.match_lookahead_literal("(", 0)
        epochs371 = xs368
        self.consume_literal(")")
        _t737 = self.default_configure()
        _t738 = transactions_pb2.Transaction(epochs=epochs371, configure=(configure366 if configure366 is not None else _t737), sync=sync367)
        return _t738

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal("(")
        self.consume_literal("configure")
        _t739 = self.parse_config_dict()
        config_dict372 = _t739
        self.consume_literal(")")
        _t740 = self.construct_configure(config_dict372)
        return _t740

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs373 = []
        cond374 = self.match_lookahead_literal(":", 0)
        while cond374:
            _t741 = self.parse_config_key_value()
            item375 = _t741
            xs373.append(item375)
            cond374 = self.match_lookahead_literal(":", 0)
        config_key_values376 = xs373
        self.consume_literal("}")
        return config_key_values376

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol377 = self.consume_terminal("SYMBOL")
        _t742 = self.parse_value()
        value378 = _t742
        return (symbol377, value378,)

    def parse_value(self) -> logic_pb2.Value:
        if self.match_lookahead_literal("true", 0):
            _t743 = 9
        else:
            if self.match_lookahead_literal("missing", 0):
                _t744 = 8
            else:
                if self.match_lookahead_literal("false", 0):
                    _t745 = 9
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t747 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t748 = 0
                            else:
                                _t748 = -1
                            _t747 = _t748
                        _t746 = _t747
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t749 = 5
                        else:
                            if self.match_lookahead_terminal("STRING", 0):
                                _t750 = 2
                            else:
                                if self.match_lookahead_terminal("INT128", 0):
                                    _t751 = 6
                                else:
                                    if self.match_lookahead_terminal("INT", 0):
                                        _t752 = 3
                                    else:
                                        if self.match_lookahead_terminal("FLOAT", 0):
                                            _t753 = 4
                                        else:
                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                _t754 = 7
                                            else:
                                                _t754 = -1
                                            _t753 = _t754
                                        _t752 = _t753
                                    _t751 = _t752
                                _t750 = _t751
                            _t749 = _t750
                        _t746 = _t749
                    _t745 = _t746
                _t744 = _t745
            _t743 = _t744
        prediction379 = _t743
        if prediction379 == 9:
            _t756 = self.parse_boolean_value()
            boolean_value388 = _t756
            _t757 = logic_pb2.Value(boolean_value=boolean_value388)
            _t755 = _t757
        else:
            if prediction379 == 8:
                self.consume_literal("missing")
                _t759 = logic_pb2.MissingValue()
                _t760 = logic_pb2.Value(missing_value=_t759)
                _t758 = _t760
            else:
                if prediction379 == 7:
                    decimal387 = self.consume_terminal("DECIMAL")
                    _t762 = logic_pb2.Value(decimal_value=decimal387)
                    _t761 = _t762
                else:
                    if prediction379 == 6:
                        int128386 = self.consume_terminal("INT128")
                        _t764 = logic_pb2.Value(int128_value=int128386)
                        _t763 = _t764
                    else:
                        if prediction379 == 5:
                            uint128385 = self.consume_terminal("UINT128")
                            _t766 = logic_pb2.Value(uint128_value=uint128385)
                            _t765 = _t766
                        else:
                            if prediction379 == 4:
                                float384 = self.consume_terminal("FLOAT")
                                _t768 = logic_pb2.Value(float_value=float384)
                                _t767 = _t768
                            else:
                                if prediction379 == 3:
                                    int383 = self.consume_terminal("INT")
                                    _t770 = logic_pb2.Value(int_value=int383)
                                    _t769 = _t770
                                else:
                                    if prediction379 == 2:
                                        string382 = self.consume_terminal("STRING")
                                        _t772 = logic_pb2.Value(string_value=string382)
                                        _t771 = _t772
                                    else:
                                        if prediction379 == 1:
                                            _t774 = self.parse_datetime()
                                            datetime381 = _t774
                                            _t775 = logic_pb2.Value(datetime_value=datetime381)
                                            _t773 = _t775
                                        else:
                                            if prediction379 == 0:
                                                _t777 = self.parse_date()
                                                date380 = _t777
                                                _t778 = logic_pb2.Value(date_value=date380)
                                                _t776 = _t778
                                            else:
                                                raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t773 = _t776
                                        _t771 = _t773
                                    _t769 = _t771
                                _t767 = _t769
                            _t765 = _t767
                        _t763 = _t765
                    _t761 = _t763
                _t758 = _t761
            _t755 = _t758
        return _t755

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal("(")
        self.consume_literal("date")
        int389 = self.consume_terminal("INT")
        int_3390 = self.consume_terminal("INT")
        int_4391 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t779 = logic_pb2.DateValue(year=int(int389), month=int(int_3390), day=int(int_4391))
        return _t779

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        self.consume_literal("(")
        self.consume_literal("datetime")
        int392 = self.consume_terminal("INT")
        int_3393 = self.consume_terminal("INT")
        int_4394 = self.consume_terminal("INT")
        int_5395 = self.consume_terminal("INT")
        int_6396 = self.consume_terminal("INT")
        int_7397 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t780 = self.consume_terminal("INT")
        else:
            _t780 = None
        int_8398 = _t780
        self.consume_literal(")")
        _t781 = logic_pb2.DateTimeValue(year=int(int392), month=int(int_3393), day=int(int_4394), hour=int(int_5395), minute=int(int_6396), second=int(int_7397), microsecond=int((int_8398 if int_8398 is not None else 0)))
        return _t781

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t782 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t783 = 1
            else:
                _t783 = -1
            _t782 = _t783
        prediction399 = _t782
        if prediction399 == 1:
            self.consume_literal("false")
            _t784 = False
        else:
            if prediction399 == 0:
                self.consume_literal("true")
                _t785 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t784 = _t785
        return _t784

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal("(")
        self.consume_literal("sync")
        xs400 = []
        cond401 = self.match_lookahead_literal(":", 0)
        while cond401:
            _t786 = self.parse_fragment_id()
            item402 = _t786
            xs400.append(item402)
            cond401 = self.match_lookahead_literal(":", 0)
        fragment_ids403 = xs400
        self.consume_literal(")")
        _t787 = transactions_pb2.Sync(fragments=fragment_ids403)
        return _t787

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        self.consume_literal(":")
        symbol404 = self.consume_terminal("SYMBOL")
        return fragments_pb2.FragmentId(id=symbol404.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t789 = self.parse_epoch_writes()
            _t788 = _t789
        else:
            _t788 = None
        epoch_writes405 = _t788
        if self.match_lookahead_literal("(", 0):
            _t791 = self.parse_epoch_reads()
            _t790 = _t791
        else:
            _t790 = None
        epoch_reads406 = _t790
        self.consume_literal(")")
        _t792 = transactions_pb2.Epoch(writes=(epoch_writes405 if epoch_writes405 is not None else []), reads=(epoch_reads406 if epoch_reads406 is not None else []))
        return _t792

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs407 = []
        cond408 = self.match_lookahead_literal("(", 0)
        while cond408:
            _t793 = self.parse_write()
            item409 = _t793
            xs407.append(item409)
            cond408 = self.match_lookahead_literal("(", 0)
        writes410 = xs407
        self.consume_literal(")")
        return writes410

    def parse_write(self) -> transactions_pb2.Write:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t795 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t796 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t797 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t798 = 2
                        else:
                            _t798 = -1
                        _t797 = _t798
                    _t796 = _t797
                _t795 = _t796
            _t794 = _t795
        else:
            _t794 = -1
        prediction411 = _t794
        if prediction411 == 3:
            _t800 = self.parse_snapshot()
            snapshot415 = _t800
            _t801 = transactions_pb2.Write(snapshot=snapshot415)
            _t799 = _t801
        else:
            if prediction411 == 2:
                _t803 = self.parse_context()
                context414 = _t803
                _t804 = transactions_pb2.Write(context=context414)
                _t802 = _t804
            else:
                if prediction411 == 1:
                    _t806 = self.parse_undefine()
                    undefine413 = _t806
                    _t807 = transactions_pb2.Write(undefine=undefine413)
                    _t805 = _t807
                else:
                    if prediction411 == 0:
                        _t809 = self.parse_define()
                        define412 = _t809
                        _t810 = transactions_pb2.Write(define=define412)
                        _t808 = _t810
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t805 = _t808
                _t802 = _t805
            _t799 = _t802
        return _t799

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal("(")
        self.consume_literal("define")
        _t811 = self.parse_fragment()
        fragment416 = _t811
        self.consume_literal(")")
        _t812 = transactions_pb2.Define(fragment=fragment416)
        return _t812

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t813 = self.parse_new_fragment_id()
        new_fragment_id417 = _t813
        xs418 = []
        cond419 = self.match_lookahead_literal("(", 0)
        while cond419:
            _t814 = self.parse_declaration()
            item420 = _t814
            xs418.append(item420)
            cond419 = self.match_lookahead_literal("(", 0)
        declarations421 = xs418
        self.consume_literal(")")
        return self.construct_fragment(new_fragment_id417, declarations421)

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        _t815 = self.parse_fragment_id()
        fragment_id422 = _t815
        self.start_fragment(fragment_id422)
        return fragment_id422

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("functional_dependency", 1):
                _t817 = 2
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t818 = 3
                else:
                    if self.match_lookahead_literal("def", 1):
                        _t819 = 0
                    else:
                        if self.match_lookahead_literal("csv_data", 1):
                            _t820 = 3
                        else:
                            if self.match_lookahead_literal("betree_relation", 1):
                                _t821 = 3
                            else:
                                if self.match_lookahead_literal("algorithm", 1):
                                    _t822 = 1
                                else:
                                    _t822 = -1
                                _t821 = _t822
                            _t820 = _t821
                        _t819 = _t820
                    _t818 = _t819
                _t817 = _t818
            _t816 = _t817
        else:
            _t816 = -1
        prediction423 = _t816
        if prediction423 == 3:
            _t824 = self.parse_data()
            data427 = _t824
            _t825 = logic_pb2.Declaration(data=data427)
            _t823 = _t825
        else:
            if prediction423 == 2:
                _t827 = self.parse_constraint()
                constraint426 = _t827
                _t828 = logic_pb2.Declaration(constraint=constraint426)
                _t826 = _t828
            else:
                if prediction423 == 1:
                    _t830 = self.parse_algorithm()
                    algorithm425 = _t830
                    _t831 = logic_pb2.Declaration(algorithm=algorithm425)
                    _t829 = _t831
                else:
                    if prediction423 == 0:
                        _t833 = self.parse_def()
                        def424 = _t833
                        _t834 = logic_pb2.Declaration()
                        getattr(_t834, 'def').CopyFrom(def424)
                        _t832 = _t834
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t829 = _t832
                _t826 = _t829
            _t823 = _t826
        return _t823

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal("(")
        self.consume_literal("def")
        _t835 = self.parse_relation_id()
        relation_id428 = _t835
        _t836 = self.parse_abstraction()
        abstraction429 = _t836
        if self.match_lookahead_literal("(", 0):
            _t838 = self.parse_attrs()
            _t837 = _t838
        else:
            _t837 = None
        attrs430 = _t837
        self.consume_literal(")")
        _t839 = logic_pb2.Def(name=relation_id428, body=abstraction429, attrs=(attrs430 if attrs430 is not None else []))
        return _t839

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_literal(":", 0):
            _t840 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t841 = 1
            else:
                _t841 = -1
            _t840 = _t841
        prediction431 = _t840
        if prediction431 == 1:
            uint128433 = self.consume_terminal("UINT128")
            _t842 = logic_pb2.RelationId(id_low=uint128433.low, id_high=uint128433.high)
        else:
            if prediction431 == 0:
                self.consume_literal(":")
                symbol432 = self.consume_terminal("SYMBOL")
                _t843 = self.relation_id_from_string(symbol432)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t842 = _t843
        return _t842

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal("(")
        _t844 = self.parse_bindings()
        bindings434 = _t844
        _t845 = self.parse_formula()
        formula435 = _t845
        self.consume_literal(")")
        _t846 = logic_pb2.Abstraction(vars=(list(bindings434[0]) + list(bindings434[1] if bindings434[1] is not None else [])), value=formula435)
        return _t846

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs436 = []
        cond437 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond437:
            _t847 = self.parse_binding()
            item438 = _t847
            xs436.append(item438)
            cond437 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings439 = xs436
        if self.match_lookahead_literal("|", 0):
            _t849 = self.parse_value_bindings()
            _t848 = _t849
        else:
            _t848 = None
        value_bindings440 = _t848
        self.consume_literal("]")
        return (bindings439, (value_bindings440 if value_bindings440 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol441 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t850 = self.parse_type()
        type442 = _t850
        _t851 = logic_pb2.Var(name=symbol441)
        _t852 = logic_pb2.Binding(var=_t851, type=type442)
        return _t852

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t853 = 0
        else:
            if self.match_lookahead_literal("UINT128", 0):
                _t854 = 4
            else:
                if self.match_lookahead_literal("STRING", 0):
                    _t855 = 1
                else:
                    if self.match_lookahead_literal("MISSING", 0):
                        _t856 = 8
                    else:
                        if self.match_lookahead_literal("INT128", 0):
                            _t857 = 5
                        else:
                            if self.match_lookahead_literal("INT", 0):
                                _t858 = 2
                            else:
                                if self.match_lookahead_literal("FLOAT", 0):
                                    _t859 = 3
                                else:
                                    if self.match_lookahead_literal("DATETIME", 0):
                                        _t860 = 7
                                    else:
                                        if self.match_lookahead_literal("DATE", 0):
                                            _t861 = 6
                                        else:
                                            if self.match_lookahead_literal("BOOLEAN", 0):
                                                _t862 = 10
                                            else:
                                                if self.match_lookahead_literal("(", 0):
                                                    _t863 = 9
                                                else:
                                                    _t863 = -1
                                                _t862 = _t863
                                            _t861 = _t862
                                        _t860 = _t861
                                    _t859 = _t860
                                _t858 = _t859
                            _t857 = _t858
                        _t856 = _t857
                    _t855 = _t856
                _t854 = _t855
            _t853 = _t854
        prediction443 = _t853
        if prediction443 == 10:
            _t865 = self.parse_boolean_type()
            boolean_type454 = _t865
            _t866 = logic_pb2.Type(boolean_type=boolean_type454)
            _t864 = _t866
        else:
            if prediction443 == 9:
                _t868 = self.parse_decimal_type()
                decimal_type453 = _t868
                _t869 = logic_pb2.Type(decimal_type=decimal_type453)
                _t867 = _t869
            else:
                if prediction443 == 8:
                    _t871 = self.parse_missing_type()
                    missing_type452 = _t871
                    _t872 = logic_pb2.Type(missing_type=missing_type452)
                    _t870 = _t872
                else:
                    if prediction443 == 7:
                        _t874 = self.parse_datetime_type()
                        datetime_type451 = _t874
                        _t875 = logic_pb2.Type(datetime_type=datetime_type451)
                        _t873 = _t875
                    else:
                        if prediction443 == 6:
                            _t877 = self.parse_date_type()
                            date_type450 = _t877
                            _t878 = logic_pb2.Type(date_type=date_type450)
                            _t876 = _t878
                        else:
                            if prediction443 == 5:
                                _t880 = self.parse_int128_type()
                                int128_type449 = _t880
                                _t881 = logic_pb2.Type(int128_type=int128_type449)
                                _t879 = _t881
                            else:
                                if prediction443 == 4:
                                    _t883 = self.parse_uint128_type()
                                    uint128_type448 = _t883
                                    _t884 = logic_pb2.Type(uint128_type=uint128_type448)
                                    _t882 = _t884
                                else:
                                    if prediction443 == 3:
                                        _t886 = self.parse_float_type()
                                        float_type447 = _t886
                                        _t887 = logic_pb2.Type(float_type=float_type447)
                                        _t885 = _t887
                                    else:
                                        if prediction443 == 2:
                                            _t889 = self.parse_int_type()
                                            int_type446 = _t889
                                            _t890 = logic_pb2.Type(int_type=int_type446)
                                            _t888 = _t890
                                        else:
                                            if prediction443 == 1:
                                                _t892 = self.parse_string_type()
                                                string_type445 = _t892
                                                _t893 = logic_pb2.Type(string_type=string_type445)
                                                _t891 = _t893
                                            else:
                                                if prediction443 == 0:
                                                    _t895 = self.parse_unspecified_type()
                                                    unspecified_type444 = _t895
                                                    _t896 = logic_pb2.Type(unspecified_type=unspecified_type444)
                                                    _t894 = _t896
                                                else:
                                                    raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t891 = _t894
                                            _t888 = _t891
                                        _t885 = _t888
                                    _t882 = _t885
                                _t879 = _t882
                            _t876 = _t879
                        _t873 = _t876
                    _t870 = _t873
                _t867 = _t870
            _t864 = _t867
        return _t864

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        self.consume_literal("UNKNOWN")
        _t897 = logic_pb2.UnspecifiedType()
        return _t897

    def parse_string_type(self) -> logic_pb2.StringType:
        self.consume_literal("STRING")
        _t898 = logic_pb2.StringType()
        return _t898

    def parse_int_type(self) -> logic_pb2.IntType:
        self.consume_literal("INT")
        _t899 = logic_pb2.IntType()
        return _t899

    def parse_float_type(self) -> logic_pb2.FloatType:
        self.consume_literal("FLOAT")
        _t900 = logic_pb2.FloatType()
        return _t900

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        self.consume_literal("UINT128")
        _t901 = logic_pb2.UInt128Type()
        return _t901

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        self.consume_literal("INT128")
        _t902 = logic_pb2.Int128Type()
        return _t902

    def parse_date_type(self) -> logic_pb2.DateType:
        self.consume_literal("DATE")
        _t903 = logic_pb2.DateType()
        return _t903

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        self.consume_literal("DATETIME")
        _t904 = logic_pb2.DateTimeType()
        return _t904

    def parse_missing_type(self) -> logic_pb2.MissingType:
        self.consume_literal("MISSING")
        _t905 = logic_pb2.MissingType()
        return _t905

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int455 = self.consume_terminal("INT")
        int_3456 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t906 = logic_pb2.DecimalType(precision=int(int455), scale=int(int_3456))
        return _t906

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal("BOOLEAN")
        _t907 = logic_pb2.BooleanType()
        return _t907

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs457 = []
        cond458 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond458:
            _t908 = self.parse_binding()
            item459 = _t908
            xs457.append(item459)
            cond458 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings460 = xs457
        return bindings460

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t910 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t911 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t912 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t913 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t914 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t915 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t916 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t917 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t918 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t919 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t920 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t921 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t922 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t923 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t924 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t925 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t926 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t927 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t928 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t929 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t930 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t931 = 10
                                                                                                else:
                                                                                                    _t931 = -1
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
                        _t912 = _t913
                    _t911 = _t912
                _t910 = _t911
            _t909 = _t910
        else:
            _t909 = -1
        prediction461 = _t909
        if prediction461 == 12:
            _t933 = self.parse_cast()
            cast474 = _t933
            _t934 = logic_pb2.Formula(cast=cast474)
            _t932 = _t934
        else:
            if prediction461 == 11:
                _t936 = self.parse_rel_atom()
                rel_atom473 = _t936
                _t937 = logic_pb2.Formula(rel_atom=rel_atom473)
                _t935 = _t937
            else:
                if prediction461 == 10:
                    _t939 = self.parse_primitive()
                    primitive472 = _t939
                    _t940 = logic_pb2.Formula(primitive=primitive472)
                    _t938 = _t940
                else:
                    if prediction461 == 9:
                        _t942 = self.parse_pragma()
                        pragma471 = _t942
                        _t943 = logic_pb2.Formula(pragma=pragma471)
                        _t941 = _t943
                    else:
                        if prediction461 == 8:
                            _t945 = self.parse_atom()
                            atom470 = _t945
                            _t946 = logic_pb2.Formula(atom=atom470)
                            _t944 = _t946
                        else:
                            if prediction461 == 7:
                                _t948 = self.parse_ffi()
                                ffi469 = _t948
                                _t949 = logic_pb2.Formula(ffi=ffi469)
                                _t947 = _t949
                            else:
                                if prediction461 == 6:
                                    _t951 = self.parse_not()
                                    not468 = _t951
                                    _t952 = logic_pb2.Formula()
                                    getattr(_t952, 'not').CopyFrom(not468)
                                    _t950 = _t952
                                else:
                                    if prediction461 == 5:
                                        _t954 = self.parse_disjunction()
                                        disjunction467 = _t954
                                        _t955 = logic_pb2.Formula(disjunction=disjunction467)
                                        _t953 = _t955
                                    else:
                                        if prediction461 == 4:
                                            _t957 = self.parse_conjunction()
                                            conjunction466 = _t957
                                            _t958 = logic_pb2.Formula(conjunction=conjunction466)
                                            _t956 = _t958
                                        else:
                                            if prediction461 == 3:
                                                _t960 = self.parse_reduce()
                                                reduce465 = _t960
                                                _t961 = logic_pb2.Formula(reduce=reduce465)
                                                _t959 = _t961
                                            else:
                                                if prediction461 == 2:
                                                    _t963 = self.parse_exists()
                                                    exists464 = _t963
                                                    _t964 = logic_pb2.Formula(exists=exists464)
                                                    _t962 = _t964
                                                else:
                                                    if prediction461 == 1:
                                                        _t966 = self.parse_false()
                                                        false463 = _t966
                                                        _t967 = logic_pb2.Formula(disjunction=false463)
                                                        _t965 = _t967
                                                    else:
                                                        if prediction461 == 0:
                                                            _t969 = self.parse_true()
                                                            true462 = _t969
                                                            _t970 = logic_pb2.Formula(conjunction=true462)
                                                            _t968 = _t970
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t965 = _t968
                                                    _t962 = _t965
                                                _t959 = _t962
                                            _t956 = _t959
                                        _t953 = _t956
                                    _t950 = _t953
                                _t947 = _t950
                            _t944 = _t947
                        _t941 = _t944
                    _t938 = _t941
                _t935 = _t938
            _t932 = _t935
        return _t932

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t971 = logic_pb2.Conjunction(args=[])
        return _t971

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t972 = logic_pb2.Disjunction(args=[])
        return _t972

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal("(")
        self.consume_literal("exists")
        _t973 = self.parse_bindings()
        bindings475 = _t973
        _t974 = self.parse_formula()
        formula476 = _t974
        self.consume_literal(")")
        _t975 = logic_pb2.Abstraction(vars=(list(bindings475[0]) + list(bindings475[1] if bindings475[1] is not None else [])), value=formula476)
        _t976 = logic_pb2.Exists(body=_t975)
        return _t976

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t977 = self.parse_abstraction()
        abstraction477 = _t977
        _t978 = self.parse_abstraction()
        abstraction_3478 = _t978
        _t979 = self.parse_terms()
        terms479 = _t979
        self.consume_literal(")")
        _t980 = logic_pb2.Reduce(op=abstraction477, body=abstraction_3478, terms=terms479)
        return _t980

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs480 = []
        cond481 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond481:
            _t981 = self.parse_term()
            item482 = _t981
            xs480.append(item482)
            cond481 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms483 = xs480
        self.consume_literal(")")
        return terms483

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_literal("true", 0):
            _t982 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t983 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t984 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t985 = 1
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t986 = 1
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t987 = 0
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t988 = 1
                                else:
                                    if self.match_lookahead_terminal("INT128", 0):
                                        _t989 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT", 0):
                                            _t990 = 1
                                        else:
                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                _t991 = 1
                                            else:
                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                    _t992 = 1
                                                else:
                                                    _t992 = -1
                                                _t991 = _t992
                                            _t990 = _t991
                                        _t989 = _t990
                                    _t988 = _t989
                                _t987 = _t988
                            _t986 = _t987
                        _t985 = _t986
                    _t984 = _t985
                _t983 = _t984
            _t982 = _t983
        prediction484 = _t982
        if prediction484 == 1:
            _t994 = self.parse_constant()
            constant486 = _t994
            _t995 = logic_pb2.Term(constant=constant486)
            _t993 = _t995
        else:
            if prediction484 == 0:
                _t997 = self.parse_var()
                var485 = _t997
                _t998 = logic_pb2.Term(var=var485)
                _t996 = _t998
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t993 = _t996
        return _t993

    def parse_var(self) -> logic_pb2.Var:
        symbol487 = self.consume_terminal("SYMBOL")
        _t999 = logic_pb2.Var(name=symbol487)
        return _t999

    def parse_constant(self) -> logic_pb2.Value:
        _t1000 = self.parse_value()
        value488 = _t1000
        return value488

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal("(")
        self.consume_literal("and")
        xs489 = []
        cond490 = self.match_lookahead_literal("(", 0)
        while cond490:
            _t1001 = self.parse_formula()
            item491 = _t1001
            xs489.append(item491)
            cond490 = self.match_lookahead_literal("(", 0)
        formulas492 = xs489
        self.consume_literal(")")
        _t1002 = logic_pb2.Conjunction(args=formulas492)
        return _t1002

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal("(")
        self.consume_literal("or")
        xs493 = []
        cond494 = self.match_lookahead_literal("(", 0)
        while cond494:
            _t1003 = self.parse_formula()
            item495 = _t1003
            xs493.append(item495)
            cond494 = self.match_lookahead_literal("(", 0)
        formulas496 = xs493
        self.consume_literal(")")
        _t1004 = logic_pb2.Disjunction(args=formulas496)
        return _t1004

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal("(")
        self.consume_literal("not")
        _t1005 = self.parse_formula()
        formula497 = _t1005
        self.consume_literal(")")
        _t1006 = logic_pb2.Not(arg=formula497)
        return _t1006

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1007 = self.parse_name()
        name498 = _t1007
        _t1008 = self.parse_ffi_args()
        ffi_args499 = _t1008
        _t1009 = self.parse_terms()
        terms500 = _t1009
        self.consume_literal(")")
        _t1010 = logic_pb2.FFI(name=name498, args=ffi_args499, terms=terms500)
        return _t1010

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol501 = self.consume_terminal("SYMBOL")
        return symbol501

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs502 = []
        cond503 = self.match_lookahead_literal("(", 0)
        while cond503:
            _t1011 = self.parse_abstraction()
            item504 = _t1011
            xs502.append(item504)
            cond503 = self.match_lookahead_literal("(", 0)
        abstractions505 = xs502
        self.consume_literal(")")
        return abstractions505

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1012 = self.parse_relation_id()
        relation_id506 = _t1012
        xs507 = []
        cond508 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond508:
            _t1013 = self.parse_term()
            item509 = _t1013
            xs507.append(item509)
            cond508 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms510 = xs507
        self.consume_literal(")")
        _t1014 = logic_pb2.Atom(name=relation_id506, terms=terms510)
        return _t1014

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1015 = self.parse_name()
        name511 = _t1015
        xs512 = []
        cond513 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond513:
            _t1016 = self.parse_term()
            item514 = _t1016
            xs512.append(item514)
            cond513 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms515 = xs512
        self.consume_literal(")")
        _t1017 = logic_pb2.Pragma(name=name511, terms=terms515)
        return _t1017

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1019 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1020 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1021 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1022 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1023 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1024 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1025 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1026 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1027 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1028 = 7
                                                else:
                                                    _t1028 = -1
                                                _t1027 = _t1028
                                            _t1026 = _t1027
                                        _t1025 = _t1026
                                    _t1024 = _t1025
                                _t1023 = _t1024
                            _t1022 = _t1023
                        _t1021 = _t1022
                    _t1020 = _t1021
                _t1019 = _t1020
            _t1018 = _t1019
        else:
            _t1018 = -1
        prediction516 = _t1018
        if prediction516 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1030 = self.parse_name()
            name526 = _t1030
            xs527 = []
            cond528 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            while cond528:
                _t1031 = self.parse_rel_term()
                item529 = _t1031
                xs527.append(item529)
                cond528 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            rel_terms530 = xs527
            self.consume_literal(")")
            _t1032 = logic_pb2.Primitive(name=name526, terms=rel_terms530)
            _t1029 = _t1032
        else:
            if prediction516 == 8:
                _t1034 = self.parse_divide()
                divide525 = _t1034
                _t1033 = divide525
            else:
                if prediction516 == 7:
                    _t1036 = self.parse_multiply()
                    multiply524 = _t1036
                    _t1035 = multiply524
                else:
                    if prediction516 == 6:
                        _t1038 = self.parse_minus()
                        minus523 = _t1038
                        _t1037 = minus523
                    else:
                        if prediction516 == 5:
                            _t1040 = self.parse_add()
                            add522 = _t1040
                            _t1039 = add522
                        else:
                            if prediction516 == 4:
                                _t1042 = self.parse_gt_eq()
                                gt_eq521 = _t1042
                                _t1041 = gt_eq521
                            else:
                                if prediction516 == 3:
                                    _t1044 = self.parse_gt()
                                    gt520 = _t1044
                                    _t1043 = gt520
                                else:
                                    if prediction516 == 2:
                                        _t1046 = self.parse_lt_eq()
                                        lt_eq519 = _t1046
                                        _t1045 = lt_eq519
                                    else:
                                        if prediction516 == 1:
                                            _t1048 = self.parse_lt()
                                            lt518 = _t1048
                                            _t1047 = lt518
                                        else:
                                            if prediction516 == 0:
                                                _t1050 = self.parse_eq()
                                                eq517 = _t1050
                                                _t1049 = eq517
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1047 = _t1049
                                        _t1045 = _t1047
                                    _t1043 = _t1045
                                _t1041 = _t1043
                            _t1039 = _t1041
                        _t1037 = _t1039
                    _t1035 = _t1037
                _t1033 = _t1035
            _t1029 = _t1033
        return _t1029

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("=")
        _t1051 = self.parse_term()
        term531 = _t1051
        _t1052 = self.parse_term()
        term_3532 = _t1052
        self.consume_literal(")")
        _t1053 = logic_pb2.RelTerm(term=term531)
        _t1054 = logic_pb2.RelTerm(term=term_3532)
        _t1055 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1053, _t1054])
        return _t1055

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("<")
        _t1056 = self.parse_term()
        term533 = _t1056
        _t1057 = self.parse_term()
        term_3534 = _t1057
        self.consume_literal(")")
        _t1058 = logic_pb2.RelTerm(term=term533)
        _t1059 = logic_pb2.RelTerm(term=term_3534)
        _t1060 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1058, _t1059])
        return _t1060

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1061 = self.parse_term()
        term535 = _t1061
        _t1062 = self.parse_term()
        term_3536 = _t1062
        self.consume_literal(")")
        _t1063 = logic_pb2.RelTerm(term=term535)
        _t1064 = logic_pb2.RelTerm(term=term_3536)
        _t1065 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1063, _t1064])
        return _t1065

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal(">")
        _t1066 = self.parse_term()
        term537 = _t1066
        _t1067 = self.parse_term()
        term_3538 = _t1067
        self.consume_literal(")")
        _t1068 = logic_pb2.RelTerm(term=term537)
        _t1069 = logic_pb2.RelTerm(term=term_3538)
        _t1070 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1068, _t1069])
        return _t1070

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1071 = self.parse_term()
        term539 = _t1071
        _t1072 = self.parse_term()
        term_3540 = _t1072
        self.consume_literal(")")
        _t1073 = logic_pb2.RelTerm(term=term539)
        _t1074 = logic_pb2.RelTerm(term=term_3540)
        _t1075 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1073, _t1074])
        return _t1075

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("+")
        _t1076 = self.parse_term()
        term541 = _t1076
        _t1077 = self.parse_term()
        term_3542 = _t1077
        _t1078 = self.parse_term()
        term_4543 = _t1078
        self.consume_literal(")")
        _t1079 = logic_pb2.RelTerm(term=term541)
        _t1080 = logic_pb2.RelTerm(term=term_3542)
        _t1081 = logic_pb2.RelTerm(term=term_4543)
        _t1082 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1079, _t1080, _t1081])
        return _t1082

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("-")
        _t1083 = self.parse_term()
        term544 = _t1083
        _t1084 = self.parse_term()
        term_3545 = _t1084
        _t1085 = self.parse_term()
        term_4546 = _t1085
        self.consume_literal(")")
        _t1086 = logic_pb2.RelTerm(term=term544)
        _t1087 = logic_pb2.RelTerm(term=term_3545)
        _t1088 = logic_pb2.RelTerm(term=term_4546)
        _t1089 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1086, _t1087, _t1088])
        return _t1089

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("*")
        _t1090 = self.parse_term()
        term547 = _t1090
        _t1091 = self.parse_term()
        term_3548 = _t1091
        _t1092 = self.parse_term()
        term_4549 = _t1092
        self.consume_literal(")")
        _t1093 = logic_pb2.RelTerm(term=term547)
        _t1094 = logic_pb2.RelTerm(term=term_3548)
        _t1095 = logic_pb2.RelTerm(term=term_4549)
        _t1096 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1093, _t1094, _t1095])
        return _t1096

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("/")
        _t1097 = self.parse_term()
        term550 = _t1097
        _t1098 = self.parse_term()
        term_3551 = _t1098
        _t1099 = self.parse_term()
        term_4552 = _t1099
        self.consume_literal(")")
        _t1100 = logic_pb2.RelTerm(term=term550)
        _t1101 = logic_pb2.RelTerm(term=term_3551)
        _t1102 = logic_pb2.RelTerm(term=term_4552)
        _t1103 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1100, _t1101, _t1102])
        return _t1103

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_literal("true", 0):
            _t1104 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1105 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1106 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1107 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1108 = 0
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1109 = 1
                            else:
                                if self.match_lookahead_terminal("SYMBOL", 0):
                                    _t1110 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1111 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1112 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1113 = 1
                                            else:
                                                if self.match_lookahead_terminal("FLOAT", 0):
                                                    _t1114 = 1
                                                else:
                                                    if self.match_lookahead_terminal("DECIMAL", 0):
                                                        _t1115 = 1
                                                    else:
                                                        _t1115 = -1
                                                    _t1114 = _t1115
                                                _t1113 = _t1114
                                            _t1112 = _t1113
                                        _t1111 = _t1112
                                    _t1110 = _t1111
                                _t1109 = _t1110
                            _t1108 = _t1109
                        _t1107 = _t1108
                    _t1106 = _t1107
                _t1105 = _t1106
            _t1104 = _t1105
        prediction553 = _t1104
        if prediction553 == 1:
            _t1117 = self.parse_term()
            term555 = _t1117
            _t1118 = logic_pb2.RelTerm(term=term555)
            _t1116 = _t1118
        else:
            if prediction553 == 0:
                _t1120 = self.parse_specialized_value()
                specialized_value554 = _t1120
                _t1121 = logic_pb2.RelTerm(specialized_value=specialized_value554)
                _t1119 = _t1121
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1116 = _t1119
        return _t1116

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal("#")
        _t1122 = self.parse_value()
        value556 = _t1122
        return value556

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1123 = self.parse_name()
        name557 = _t1123
        xs558 = []
        cond559 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond559:
            _t1124 = self.parse_rel_term()
            item560 = _t1124
            xs558.append(item560)
            cond559 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        rel_terms561 = xs558
        self.consume_literal(")")
        _t1125 = logic_pb2.RelAtom(name=name557, terms=rel_terms561)
        return _t1125

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1126 = self.parse_term()
        term562 = _t1126
        _t1127 = self.parse_term()
        term_3563 = _t1127
        self.consume_literal(")")
        _t1128 = logic_pb2.Cast(input=term562, result=term_3563)
        return _t1128

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs564 = []
        cond565 = self.match_lookahead_literal("(", 0)
        while cond565:
            _t1129 = self.parse_attribute()
            item566 = _t1129
            xs564.append(item566)
            cond565 = self.match_lookahead_literal("(", 0)
        attributes567 = xs564
        self.consume_literal(")")
        return attributes567

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1130 = self.parse_name()
        name568 = _t1130
        xs569 = []
        cond570 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond570:
            _t1131 = self.parse_value()
            item571 = _t1131
            xs569.append(item571)
            cond570 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        values572 = xs569
        self.consume_literal(")")
        _t1132 = logic_pb2.Attribute(name=name568, args=values572)
        return _t1132

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs573 = []
        cond574 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond574:
            _t1133 = self.parse_relation_id()
            item575 = _t1133
            xs573.append(item575)
            cond574 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids576 = xs573
        _t1134 = self.parse_script()
        script577 = _t1134
        self.consume_literal(")")
        _t1135 = logic_pb2.Algorithm(body=script577)
        getattr(_t1135, 'global').extend(relation_ids576)
        return _t1135

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal("(")
        self.consume_literal("script")
        xs578 = []
        cond579 = self.match_lookahead_literal("(", 0)
        while cond579:
            _t1136 = self.parse_construct()
            item580 = _t1136
            xs578.append(item580)
            cond579 = self.match_lookahead_literal("(", 0)
        constructs581 = xs578
        self.consume_literal(")")
        _t1137 = logic_pb2.Script(constructs=constructs581)
        return _t1137

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1139 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1140 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1141 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1142 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1143 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1144 = 1
                                else:
                                    _t1144 = -1
                                _t1143 = _t1144
                            _t1142 = _t1143
                        _t1141 = _t1142
                    _t1140 = _t1141
                _t1139 = _t1140
            _t1138 = _t1139
        else:
            _t1138 = -1
        prediction582 = _t1138
        if prediction582 == 1:
            _t1146 = self.parse_instruction()
            instruction584 = _t1146
            _t1147 = logic_pb2.Construct(instruction=instruction584)
            _t1145 = _t1147
        else:
            if prediction582 == 0:
                _t1149 = self.parse_loop()
                loop583 = _t1149
                _t1150 = logic_pb2.Construct(loop=loop583)
                _t1148 = _t1150
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1145 = _t1148
        return _t1145

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1151 = self.parse_init()
        init585 = _t1151
        _t1152 = self.parse_script()
        script586 = _t1152
        self.consume_literal(")")
        _t1153 = logic_pb2.Loop(init=init585, body=script586)
        return _t1153

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs587 = []
        cond588 = self.match_lookahead_literal("(", 0)
        while cond588:
            _t1154 = self.parse_instruction()
            item589 = _t1154
            xs587.append(item589)
            cond588 = self.match_lookahead_literal("(", 0)
        instructions590 = xs587
        self.consume_literal(")")
        return instructions590

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1156 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1157 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1158 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1159 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1160 = 0
                            else:
                                _t1160 = -1
                            _t1159 = _t1160
                        _t1158 = _t1159
                    _t1157 = _t1158
                _t1156 = _t1157
            _t1155 = _t1156
        else:
            _t1155 = -1
        prediction591 = _t1155
        if prediction591 == 4:
            _t1162 = self.parse_monus_def()
            monus_def596 = _t1162
            _t1163 = logic_pb2.Instruction(monus_def=monus_def596)
            _t1161 = _t1163
        else:
            if prediction591 == 3:
                _t1165 = self.parse_monoid_def()
                monoid_def595 = _t1165
                _t1166 = logic_pb2.Instruction(monoid_def=monoid_def595)
                _t1164 = _t1166
            else:
                if prediction591 == 2:
                    _t1168 = self.parse_break()
                    break594 = _t1168
                    _t1169 = logic_pb2.Instruction()
                    getattr(_t1169, 'break').CopyFrom(break594)
                    _t1167 = _t1169
                else:
                    if prediction591 == 1:
                        _t1171 = self.parse_upsert()
                        upsert593 = _t1171
                        _t1172 = logic_pb2.Instruction(upsert=upsert593)
                        _t1170 = _t1172
                    else:
                        if prediction591 == 0:
                            _t1174 = self.parse_assign()
                            assign592 = _t1174
                            _t1175 = logic_pb2.Instruction(assign=assign592)
                            _t1173 = _t1175
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1170 = _t1173
                    _t1167 = _t1170
                _t1164 = _t1167
            _t1161 = _t1164
        return _t1161

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1176 = self.parse_relation_id()
        relation_id597 = _t1176
        _t1177 = self.parse_abstraction()
        abstraction598 = _t1177
        if self.match_lookahead_literal("(", 0):
            _t1179 = self.parse_attrs()
            _t1178 = _t1179
        else:
            _t1178 = None
        attrs599 = _t1178
        self.consume_literal(")")
        _t1180 = logic_pb2.Assign(name=relation_id597, body=abstraction598, attrs=(attrs599 if attrs599 is not None else []))
        return _t1180

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1181 = self.parse_relation_id()
        relation_id600 = _t1181
        _t1182 = self.parse_abstraction_with_arity()
        abstraction_with_arity601 = _t1182
        if self.match_lookahead_literal("(", 0):
            _t1184 = self.parse_attrs()
            _t1183 = _t1184
        else:
            _t1183 = None
        attrs602 = _t1183
        self.consume_literal(")")
        _t1185 = logic_pb2.Upsert(name=relation_id600, body=abstraction_with_arity601[0], attrs=(attrs602 if attrs602 is not None else []), value_arity=abstraction_with_arity601[1])
        return _t1185

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1186 = self.parse_bindings()
        bindings603 = _t1186
        _t1187 = self.parse_formula()
        formula604 = _t1187
        self.consume_literal(")")
        _t1188 = logic_pb2.Abstraction(vars=(list(bindings603[0]) + list(bindings603[1] if bindings603[1] is not None else [])), value=formula604)
        return (_t1188, len(bindings603[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal("(")
        self.consume_literal("break")
        _t1189 = self.parse_relation_id()
        relation_id605 = _t1189
        _t1190 = self.parse_abstraction()
        abstraction606 = _t1190
        if self.match_lookahead_literal("(", 0):
            _t1192 = self.parse_attrs()
            _t1191 = _t1192
        else:
            _t1191 = None
        attrs607 = _t1191
        self.consume_literal(")")
        _t1193 = logic_pb2.Break(name=relation_id605, body=abstraction606, attrs=(attrs607 if attrs607 is not None else []))
        return _t1193

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1194 = self.parse_monoid()
        monoid608 = _t1194
        _t1195 = self.parse_relation_id()
        relation_id609 = _t1195
        _t1196 = self.parse_abstraction_with_arity()
        abstraction_with_arity610 = _t1196
        if self.match_lookahead_literal("(", 0):
            _t1198 = self.parse_attrs()
            _t1197 = _t1198
        else:
            _t1197 = None
        attrs611 = _t1197
        self.consume_literal(")")
        _t1199 = logic_pb2.MonoidDef(monoid=monoid608, name=relation_id609, body=abstraction_with_arity610[0], attrs=(attrs611 if attrs611 is not None else []), value_arity=abstraction_with_arity610[1])
        return _t1199

    def parse_monoid(self) -> logic_pb2.Monoid:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1201 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1202 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1203 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1204 = 2
                        else:
                            _t1204 = -1
                        _t1203 = _t1204
                    _t1202 = _t1203
                _t1201 = _t1202
            _t1200 = _t1201
        else:
            _t1200 = -1
        prediction612 = _t1200
        if prediction612 == 3:
            _t1206 = self.parse_sum_monoid()
            sum_monoid616 = _t1206
            _t1207 = logic_pb2.Monoid(sum_monoid=sum_monoid616)
            _t1205 = _t1207
        else:
            if prediction612 == 2:
                _t1209 = self.parse_max_monoid()
                max_monoid615 = _t1209
                _t1210 = logic_pb2.Monoid(max_monoid=max_monoid615)
                _t1208 = _t1210
            else:
                if prediction612 == 1:
                    _t1212 = self.parse_min_monoid()
                    min_monoid614 = _t1212
                    _t1213 = logic_pb2.Monoid(min_monoid=min_monoid614)
                    _t1211 = _t1213
                else:
                    if prediction612 == 0:
                        _t1215 = self.parse_or_monoid()
                        or_monoid613 = _t1215
                        _t1216 = logic_pb2.Monoid(or_monoid=or_monoid613)
                        _t1214 = _t1216
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1211 = _t1214
                _t1208 = _t1211
            _t1205 = _t1208
        return _t1205

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1217 = logic_pb2.OrMonoid()
        return _t1217

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        self.consume_literal("(")
        self.consume_literal("min")
        _t1218 = self.parse_type()
        type617 = _t1218
        self.consume_literal(")")
        _t1219 = logic_pb2.MinMonoid(type=type617)
        return _t1219

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        self.consume_literal("(")
        self.consume_literal("max")
        _t1220 = self.parse_type()
        type618 = _t1220
        self.consume_literal(")")
        _t1221 = logic_pb2.MaxMonoid(type=type618)
        return _t1221

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1222 = self.parse_type()
        type619 = _t1222
        self.consume_literal(")")
        _t1223 = logic_pb2.SumMonoid(type=type619)
        return _t1223

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1224 = self.parse_monoid()
        monoid620 = _t1224
        _t1225 = self.parse_relation_id()
        relation_id621 = _t1225
        _t1226 = self.parse_abstraction_with_arity()
        abstraction_with_arity622 = _t1226
        if self.match_lookahead_literal("(", 0):
            _t1228 = self.parse_attrs()
            _t1227 = _t1228
        else:
            _t1227 = None
        attrs623 = _t1227
        self.consume_literal(")")
        _t1229 = logic_pb2.MonusDef(monoid=monoid620, name=relation_id621, body=abstraction_with_arity622[0], attrs=(attrs623 if attrs623 is not None else []), value_arity=abstraction_with_arity622[1])
        return _t1229

    def parse_constraint(self) -> logic_pb2.Constraint:
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1230 = self.parse_relation_id()
        relation_id624 = _t1230
        _t1231 = self.parse_abstraction()
        abstraction625 = _t1231
        _t1232 = self.parse_functional_dependency_keys()
        functional_dependency_keys626 = _t1232
        _t1233 = self.parse_functional_dependency_values()
        functional_dependency_values627 = _t1233
        self.consume_literal(")")
        _t1234 = logic_pb2.FunctionalDependency(guard=abstraction625, keys=functional_dependency_keys626, values=functional_dependency_values627)
        _t1235 = logic_pb2.Constraint(name=relation_id624, functional_dependency=_t1234)
        return _t1235

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs628 = []
        cond629 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond629:
            _t1236 = self.parse_var()
            item630 = _t1236
            xs628.append(item630)
            cond629 = self.match_lookahead_terminal("SYMBOL", 0)
        vars631 = xs628
        self.consume_literal(")")
        return vars631

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs632 = []
        cond633 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond633:
            _t1237 = self.parse_var()
            item634 = _t1237
            xs632.append(item634)
            cond633 = self.match_lookahead_terminal("SYMBOL", 0)
        vars635 = xs632
        self.consume_literal(")")
        return vars635

    def parse_data(self) -> logic_pb2.Data:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("edb", 1):
                _t1239 = 0
            else:
                if self.match_lookahead_literal("csv_data", 1):
                    _t1240 = 2
                else:
                    if self.match_lookahead_literal("betree_relation", 1):
                        _t1241 = 1
                    else:
                        _t1241 = -1
                    _t1240 = _t1241
                _t1239 = _t1240
            _t1238 = _t1239
        else:
            _t1238 = -1
        prediction636 = _t1238
        if prediction636 == 2:
            _t1243 = self.parse_csv_data()
            csv_data639 = _t1243
            _t1244 = logic_pb2.Data(csv_data=csv_data639)
            _t1242 = _t1244
        else:
            if prediction636 == 1:
                _t1246 = self.parse_betree_relation()
                betree_relation638 = _t1246
                _t1247 = logic_pb2.Data(betree_relation=betree_relation638)
                _t1245 = _t1247
            else:
                if prediction636 == 0:
                    _t1249 = self.parse_edb()
                    edb637 = _t1249
                    _t1250 = logic_pb2.Data(edb=edb637)
                    _t1248 = _t1250
                else:
                    raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t1245 = _t1248
            _t1242 = _t1245
        return _t1242

    def parse_edb(self) -> logic_pb2.EDB:
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1251 = self.parse_relation_id()
        relation_id640 = _t1251
        _t1252 = self.parse_edb_path()
        edb_path641 = _t1252
        _t1253 = self.parse_edb_types()
        edb_types642 = _t1253
        self.consume_literal(")")
        _t1254 = logic_pb2.EDB(target_id=relation_id640, path=edb_path641, types=edb_types642)
        return _t1254

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs643 = []
        cond644 = self.match_lookahead_terminal("STRING", 0)
        while cond644:
            item645 = self.consume_terminal("STRING")
            xs643.append(item645)
            cond644 = self.match_lookahead_terminal("STRING", 0)
        strings646 = xs643
        self.consume_literal("]")
        return strings646

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs647 = []
        cond648 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond648:
            _t1255 = self.parse_type()
            item649 = _t1255
            xs647.append(item649)
            cond648 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types650 = xs647
        self.consume_literal("]")
        return types650

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1256 = self.parse_relation_id()
        relation_id651 = _t1256
        _t1257 = self.parse_betree_info()
        betree_info652 = _t1257
        self.consume_literal(")")
        _t1258 = logic_pb2.BeTreeRelation(name=relation_id651, relation_info=betree_info652)
        return _t1258

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1259 = self.parse_betree_info_key_types()
        betree_info_key_types653 = _t1259
        _t1260 = self.parse_betree_info_value_types()
        betree_info_value_types654 = _t1260
        _t1261 = self.parse_config_dict()
        config_dict655 = _t1261
        self.consume_literal(")")
        _t1262 = self.construct_betree_info(betree_info_key_types653, betree_info_value_types654, config_dict655)
        return _t1262

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs656 = []
        cond657 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond657:
            _t1263 = self.parse_type()
            item658 = _t1263
            xs656.append(item658)
            cond657 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types659 = xs656
        self.consume_literal(")")
        return types659

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs660 = []
        cond661 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond661:
            _t1264 = self.parse_type()
            item662 = _t1264
            xs660.append(item662)
            cond661 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types663 = xs660
        self.consume_literal(")")
        return types663

    def parse_csv_data(self) -> logic_pb2.CSVData:
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1265 = self.parse_csvlocator()
        csvlocator664 = _t1265
        _t1266 = self.parse_csv_config()
        csv_config665 = _t1266
        _t1267 = self.parse_gnf_columns()
        gnf_columns666 = _t1267
        _t1268 = self.parse_csv_asof()
        csv_asof667 = _t1268
        self.consume_literal(")")
        _t1269 = logic_pb2.CSVData(locator=csvlocator664, config=csv_config665, columns=gnf_columns666, asof=csv_asof667)
        return _t1269

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1271 = self.parse_csv_locator_paths()
            _t1270 = _t1271
        else:
            _t1270 = None
        csv_locator_paths668 = _t1270
        if self.match_lookahead_literal("(", 0):
            _t1273 = self.parse_csv_locator_inline_data()
            _t1272 = _t1273
        else:
            _t1272 = None
        csv_locator_inline_data669 = _t1272
        self.consume_literal(")")
        _t1274 = logic_pb2.CSVLocator(paths=(csv_locator_paths668 if csv_locator_paths668 is not None else []), inline_data=(csv_locator_inline_data669 if csv_locator_inline_data669 is not None else "").encode())
        return _t1274

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs670 = []
        cond671 = self.match_lookahead_terminal("STRING", 0)
        while cond671:
            item672 = self.consume_terminal("STRING")
            xs670.append(item672)
            cond671 = self.match_lookahead_terminal("STRING", 0)
        strings673 = xs670
        self.consume_literal(")")
        return strings673

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string674 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string674

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1275 = self.parse_config_dict()
        config_dict675 = _t1275
        self.consume_literal(")")
        _t1276 = self.construct_csv_config(config_dict675)
        return _t1276

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs676 = []
        cond677 = self.match_lookahead_literal("(", 0)
        while cond677:
            _t1277 = self.parse_gnf_column()
            item678 = _t1277
            xs676.append(item678)
            cond677 = self.match_lookahead_literal("(", 0)
        gnf_columns679 = xs676
        self.consume_literal(")")
        return gnf_columns679

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        self.consume_literal("(")
        self.consume_literal("column")
        _t1278 = self.parse_gnf_column_path()
        gnf_column_path680 = _t1278
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1280 = self.parse_relation_id()
            _t1279 = _t1280
        else:
            _t1279 = None
        relation_id681 = _t1279
        self.consume_literal("[")
        xs682 = []
        cond683 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond683:
            _t1281 = self.parse_type()
            item684 = _t1281
            xs682.append(item684)
            cond683 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types685 = xs682
        self.consume_literal("]")
        self.consume_literal(")")
        _t1282 = logic_pb2.GNFColumn(column_path=gnf_column_path680, target_id=relation_id681, types=types685)
        return _t1282

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1283 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1284 = 0
            else:
                _t1284 = -1
            _t1283 = _t1284
        prediction686 = _t1283
        if prediction686 == 1:
            self.consume_literal("[")
            xs688 = []
            cond689 = self.match_lookahead_terminal("STRING", 0)
            while cond689:
                item690 = self.consume_terminal("STRING")
                xs688.append(item690)
                cond689 = self.match_lookahead_terminal("STRING", 0)
            strings691 = xs688
            self.consume_literal("]")
            _t1285 = strings691
        else:
            if prediction686 == 0:
                string687 = self.consume_terminal("STRING")
                _t1286 = [string687]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1285 = _t1286
        return _t1285

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string692 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string692

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1287 = self.parse_fragment_id()
        fragment_id693 = _t1287
        self.consume_literal(")")
        _t1288 = transactions_pb2.Undefine(fragment_id=fragment_id693)
        return _t1288

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal("(")
        self.consume_literal("context")
        xs694 = []
        cond695 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond695:
            _t1289 = self.parse_relation_id()
            item696 = _t1289
            xs694.append(item696)
            cond695 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids697 = xs694
        self.consume_literal(")")
        _t1290 = transactions_pb2.Context(relations=relation_ids697)
        return _t1290

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        self.consume_literal("(")
        self.consume_literal("snapshot")
        xs698 = []
        cond699 = self.match_lookahead_literal("[", 0)
        while cond699:
            _t1291 = self.parse_snapshot_mapping()
            item700 = _t1291
            xs698.append(item700)
            cond699 = self.match_lookahead_literal("[", 0)
        snapshot_mappings701 = xs698
        self.consume_literal(")")
        _t1292 = transactions_pb2.Snapshot(mappings=snapshot_mappings701)
        return _t1292

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        _t1293 = self.parse_edb_path()
        edb_path702 = _t1293
        _t1294 = self.parse_relation_id()
        relation_id703 = _t1294
        _t1295 = transactions_pb2.SnapshotMapping(destination_path=edb_path702, source_relation=relation_id703)
        return _t1295

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs704 = []
        cond705 = self.match_lookahead_literal("(", 0)
        while cond705:
            _t1296 = self.parse_read()
            item706 = _t1296
            xs704.append(item706)
            cond705 = self.match_lookahead_literal("(", 0)
        reads707 = xs704
        self.consume_literal(")")
        return reads707

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1298 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1299 = 1
                else:
                    if self.match_lookahead_literal("export", 1):
                        _t1300 = 4
                    else:
                        if self.match_lookahead_literal("demand", 1):
                            _t1301 = 0
                        else:
                            if self.match_lookahead_literal("abort", 1):
                                _t1302 = 3
                            else:
                                _t1302 = -1
                            _t1301 = _t1302
                        _t1300 = _t1301
                    _t1299 = _t1300
                _t1298 = _t1299
            _t1297 = _t1298
        else:
            _t1297 = -1
        prediction708 = _t1297
        if prediction708 == 4:
            _t1304 = self.parse_export()
            export713 = _t1304
            _t1305 = transactions_pb2.Read(export=export713)
            _t1303 = _t1305
        else:
            if prediction708 == 3:
                _t1307 = self.parse_abort()
                abort712 = _t1307
                _t1308 = transactions_pb2.Read(abort=abort712)
                _t1306 = _t1308
            else:
                if prediction708 == 2:
                    _t1310 = self.parse_what_if()
                    what_if711 = _t1310
                    _t1311 = transactions_pb2.Read(what_if=what_if711)
                    _t1309 = _t1311
                else:
                    if prediction708 == 1:
                        _t1313 = self.parse_output()
                        output710 = _t1313
                        _t1314 = transactions_pb2.Read(output=output710)
                        _t1312 = _t1314
                    else:
                        if prediction708 == 0:
                            _t1316 = self.parse_demand()
                            demand709 = _t1316
                            _t1317 = transactions_pb2.Read(demand=demand709)
                            _t1315 = _t1317
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1312 = _t1315
                    _t1309 = _t1312
                _t1306 = _t1309
            _t1303 = _t1306
        return _t1303

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1318 = self.parse_relation_id()
        relation_id714 = _t1318
        self.consume_literal(")")
        _t1319 = transactions_pb2.Demand(relation_id=relation_id714)
        return _t1319

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal("(")
        self.consume_literal("output")
        _t1320 = self.parse_name()
        name715 = _t1320
        _t1321 = self.parse_relation_id()
        relation_id716 = _t1321
        self.consume_literal(")")
        _t1322 = transactions_pb2.Output(name=name715, relation_id=relation_id716)
        return _t1322

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t1323 = self.parse_name()
        name717 = _t1323
        _t1324 = self.parse_epoch()
        epoch718 = _t1324
        self.consume_literal(")")
        _t1325 = transactions_pb2.WhatIf(branch=name717, epoch=epoch718)
        return _t1325

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t1327 = self.parse_name()
            _t1326 = _t1327
        else:
            _t1326 = None
        name719 = _t1326
        _t1328 = self.parse_relation_id()
        relation_id720 = _t1328
        self.consume_literal(")")
        _t1329 = transactions_pb2.Abort(name=(name719 if name719 is not None else "abort"), relation_id=relation_id720)
        return _t1329

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal("(")
        self.consume_literal("export")
        _t1330 = self.parse_export_csv_config()
        export_csv_config721 = _t1330
        self.consume_literal(")")
        _t1331 = transactions_pb2.Export(csv_config=export_csv_config721)
        return _t1331

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal("(")
        self.consume_literal("export_csv_config")
        _t1332 = self.parse_export_csv_path()
        export_csv_path722 = _t1332
        _t1333 = self.parse_export_csv_columns()
        export_csv_columns723 = _t1333
        _t1334 = self.parse_config_dict()
        config_dict724 = _t1334
        self.consume_literal(")")
        _t1335 = self.export_csv_config(export_csv_path722, export_csv_columns723, config_dict724)
        return _t1335

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string725 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string725

    def parse_export_csv_columns(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs726 = []
        cond727 = self.match_lookahead_literal("(", 0)
        while cond727:
            _t1336 = self.parse_export_csv_column()
            item728 = _t1336
            xs726.append(item728)
            cond727 = self.match_lookahead_literal("(", 0)
        export_csv_columns729 = xs726
        self.consume_literal(")")
        return export_csv_columns729

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal("(")
        self.consume_literal("column")
        string730 = self.consume_terminal("STRING")
        _t1337 = self.parse_relation_id()
        relation_id731 = _t1337
        self.consume_literal(")")
        _t1338 = transactions_pb2.ExportCSVColumn(column_name=string730, column_data=relation_id731)
        return _t1338


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
