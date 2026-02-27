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
            _t1378 = value.HasField("int_value")
        else:
            _t1378 = False
        if _t1378:
            assert value is not None
            return int(value.int_value)
        else:
            _t1379 = None
        return int(default)

    def _extract_value_int64(self, value: Optional[logic_pb2.Value], default: int) -> int:
        if value is not None:
            assert value is not None
            _t1380 = value.HasField("int_value")
        else:
            _t1380 = False
        if _t1380:
            assert value is not None
            return value.int_value
        else:
            _t1381 = None
        return default

    def _extract_value_string(self, value: Optional[logic_pb2.Value], default: str) -> str:
        if value is not None:
            assert value is not None
            _t1382 = value.HasField("string_value")
        else:
            _t1382 = False
        if _t1382:
            assert value is not None
            return value.string_value
        else:
            _t1383 = None
        return default

    def _extract_value_boolean(self, value: Optional[logic_pb2.Value], default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t1384 = value.HasField("boolean_value")
        else:
            _t1384 = False
        if _t1384:
            assert value is not None
            return value.boolean_value
        else:
            _t1385 = None
        return default

    def _extract_value_string_list(self, value: Optional[logic_pb2.Value], default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t1386 = value.HasField("string_value")
        else:
            _t1386 = False
        if _t1386:
            assert value is not None
            return [value.string_value]
        else:
            _t1387 = None
        return default

    def _try_extract_value_int64(self, value: Optional[logic_pb2.Value]) -> Optional[int]:
        if value is not None:
            assert value is not None
            _t1388 = value.HasField("int_value")
        else:
            _t1388 = False
        if _t1388:
            assert value is not None
            return value.int_value
        else:
            _t1389 = None
        return None

    def _try_extract_value_float64(self, value: Optional[logic_pb2.Value]) -> Optional[float]:
        if value is not None:
            assert value is not None
            _t1390 = value.HasField("float_value")
        else:
            _t1390 = False
        if _t1390:
            assert value is not None
            return value.float_value
        else:
            _t1391 = None
        return None

    def _try_extract_value_bytes(self, value: Optional[logic_pb2.Value]) -> Optional[bytes]:
        if value is not None:
            assert value is not None
            _t1392 = value.HasField("string_value")
        else:
            _t1392 = False
        if _t1392:
            assert value is not None
            return value.string_value.encode()
        else:
            _t1393 = None
        return None

    def _try_extract_value_uint128(self, value: Optional[logic_pb2.Value]) -> Optional[logic_pb2.UInt128Value]:
        if value is not None:
            assert value is not None
            _t1394 = value.HasField("uint128_value")
        else:
            _t1394 = False
        if _t1394:
            assert value is not None
            return value.uint128_value
        else:
            _t1395 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1396 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t1396
        _t1397 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t1397
        _t1398 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t1398
        _t1399 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t1399
        _t1400 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t1400
        _t1401 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t1401
        _t1402 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t1402
        _t1403 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t1403
        _t1404 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t1404
        _t1405 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t1405
        _t1406 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t1406
        _t1407 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t1407
        _t1408 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t1408

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1409 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t1409
        _t1410 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t1410
        _t1411 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t1411
        _t1412 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t1412
        _t1413 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1413
        _t1414 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t1414
        _t1415 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t1415
        _t1416 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t1416
        _t1417 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t1417
        _t1418 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1418
        _t1419 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1419

    def default_configure(self) -> transactions_pb2.Configure:
        _t1420 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1420
        _t1421 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1421

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
        _t1422 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1422
        _t1423 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t1423
        _t1424 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1424

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1425 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t1425
        _t1426 = self._extract_value_string(config.get("compression"), "")
        compression = _t1426
        _t1427 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t1427
        _t1428 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t1428
        _t1429 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t1429
        _t1430 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t1430
        _t1431 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t1431
        _t1432 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1432

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t1433 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t1433

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t753 = self.parse_configure()
            _t752 = _t753
        else:
            _t752 = None
        configure376 = _t752
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t755 = self.parse_sync()
            _t754 = _t755
        else:
            _t754 = None
        sync377 = _t754
        xs378 = []
        cond379 = self.match_lookahead_literal("(", 0)
        while cond379:
            _t756 = self.parse_epoch()
            item380 = _t756
            xs378.append(item380)
            cond379 = self.match_lookahead_literal("(", 0)
        epochs381 = xs378
        self.consume_literal(")")
        _t757 = self.default_configure()
        _t758 = transactions_pb2.Transaction(epochs=epochs381, configure=(configure376 if configure376 is not None else _t757), sync=sync377)
        return _t758

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal("(")
        self.consume_literal("configure")
        _t759 = self.parse_config_dict()
        config_dict382 = _t759
        self.consume_literal(")")
        _t760 = self.construct_configure(config_dict382)
        return _t760

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs383 = []
        cond384 = self.match_lookahead_literal(":", 0)
        while cond384:
            _t761 = self.parse_config_key_value()
            item385 = _t761
            xs383.append(item385)
            cond384 = self.match_lookahead_literal(":", 0)
        config_key_values386 = xs383
        self.consume_literal("}")
        return config_key_values386

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol387 = self.consume_terminal("SYMBOL")
        _t762 = self.parse_value()
        value388 = _t762
        return (symbol387, value388,)

    def parse_value(self) -> logic_pb2.Value:
        if self.match_lookahead_literal("true", 0):
            _t763 = 9
        else:
            if self.match_lookahead_literal("missing", 0):
                _t764 = 8
            else:
                if self.match_lookahead_literal("false", 0):
                    _t765 = 9
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t767 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t768 = 0
                            else:
                                _t768 = -1
                            _t767 = _t768
                        _t766 = _t767
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t769 = 5
                        else:
                            if self.match_lookahead_terminal("STRING", 0):
                                _t770 = 2
                            else:
                                if self.match_lookahead_terminal("INT128", 0):
                                    _t771 = 6
                                else:
                                    if self.match_lookahead_terminal("INT", 0):
                                        _t772 = 3
                                    else:
                                        if self.match_lookahead_terminal("FLOAT", 0):
                                            _t773 = 4
                                        else:
                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                _t774 = 7
                                            else:
                                                _t774 = -1
                                            _t773 = _t774
                                        _t772 = _t773
                                    _t771 = _t772
                                _t770 = _t771
                            _t769 = _t770
                        _t766 = _t769
                    _t765 = _t766
                _t764 = _t765
            _t763 = _t764
        prediction389 = _t763
        if prediction389 == 9:
            _t776 = self.parse_boolean_value()
            boolean_value398 = _t776
            _t777 = logic_pb2.Value(boolean_value=boolean_value398)
            _t775 = _t777
        else:
            if prediction389 == 8:
                self.consume_literal("missing")
                _t779 = logic_pb2.MissingValue()
                _t780 = logic_pb2.Value(missing_value=_t779)
                _t778 = _t780
            else:
                if prediction389 == 7:
                    decimal397 = self.consume_terminal("DECIMAL")
                    _t782 = logic_pb2.Value(decimal_value=decimal397)
                    _t781 = _t782
                else:
                    if prediction389 == 6:
                        int128396 = self.consume_terminal("INT128")
                        _t784 = logic_pb2.Value(int128_value=int128396)
                        _t783 = _t784
                    else:
                        if prediction389 == 5:
                            uint128395 = self.consume_terminal("UINT128")
                            _t786 = logic_pb2.Value(uint128_value=uint128395)
                            _t785 = _t786
                        else:
                            if prediction389 == 4:
                                float394 = self.consume_terminal("FLOAT")
                                _t788 = logic_pb2.Value(float_value=float394)
                                _t787 = _t788
                            else:
                                if prediction389 == 3:
                                    int393 = self.consume_terminal("INT")
                                    _t790 = logic_pb2.Value(int_value=int393)
                                    _t789 = _t790
                                else:
                                    if prediction389 == 2:
                                        string392 = self.consume_terminal("STRING")
                                        _t792 = logic_pb2.Value(string_value=string392)
                                        _t791 = _t792
                                    else:
                                        if prediction389 == 1:
                                            _t794 = self.parse_datetime()
                                            datetime391 = _t794
                                            _t795 = logic_pb2.Value(datetime_value=datetime391)
                                            _t793 = _t795
                                        else:
                                            if prediction389 == 0:
                                                _t797 = self.parse_date()
                                                date390 = _t797
                                                _t798 = logic_pb2.Value(date_value=date390)
                                                _t796 = _t798
                                            else:
                                                raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t793 = _t796
                                        _t791 = _t793
                                    _t789 = _t791
                                _t787 = _t789
                            _t785 = _t787
                        _t783 = _t785
                    _t781 = _t783
                _t778 = _t781
            _t775 = _t778
        return _t775

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal("(")
        self.consume_literal("date")
        int399 = self.consume_terminal("INT")
        int_3400 = self.consume_terminal("INT")
        int_4401 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t799 = logic_pb2.DateValue(year=int(int399), month=int(int_3400), day=int(int_4401))
        return _t799

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        self.consume_literal("(")
        self.consume_literal("datetime")
        int402 = self.consume_terminal("INT")
        int_3403 = self.consume_terminal("INT")
        int_4404 = self.consume_terminal("INT")
        int_5405 = self.consume_terminal("INT")
        int_6406 = self.consume_terminal("INT")
        int_7407 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t800 = self.consume_terminal("INT")
        else:
            _t800 = None
        int_8408 = _t800
        self.consume_literal(")")
        _t801 = logic_pb2.DateTimeValue(year=int(int402), month=int(int_3403), day=int(int_4404), hour=int(int_5405), minute=int(int_6406), second=int(int_7407), microsecond=int((int_8408 if int_8408 is not None else 0)))
        return _t801

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t802 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t803 = 1
            else:
                _t803 = -1
            _t802 = _t803
        prediction409 = _t802
        if prediction409 == 1:
            self.consume_literal("false")
            _t804 = False
        else:
            if prediction409 == 0:
                self.consume_literal("true")
                _t805 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t804 = _t805
        return _t804

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal("(")
        self.consume_literal("sync")
        xs410 = []
        cond411 = self.match_lookahead_literal(":", 0)
        while cond411:
            _t806 = self.parse_fragment_id()
            item412 = _t806
            xs410.append(item412)
            cond411 = self.match_lookahead_literal(":", 0)
        fragment_ids413 = xs410
        self.consume_literal(")")
        _t807 = transactions_pb2.Sync(fragments=fragment_ids413)
        return _t807

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        self.consume_literal(":")
        symbol414 = self.consume_terminal("SYMBOL")
        return fragments_pb2.FragmentId(id=symbol414.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t809 = self.parse_epoch_writes()
            _t808 = _t809
        else:
            _t808 = None
        epoch_writes415 = _t808
        if self.match_lookahead_literal("(", 0):
            _t811 = self.parse_epoch_reads()
            _t810 = _t811
        else:
            _t810 = None
        epoch_reads416 = _t810
        self.consume_literal(")")
        _t812 = transactions_pb2.Epoch(writes=(epoch_writes415 if epoch_writes415 is not None else []), reads=(epoch_reads416 if epoch_reads416 is not None else []))
        return _t812

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs417 = []
        cond418 = self.match_lookahead_literal("(", 0)
        while cond418:
            _t813 = self.parse_write()
            item419 = _t813
            xs417.append(item419)
            cond418 = self.match_lookahead_literal("(", 0)
        writes420 = xs417
        self.consume_literal(")")
        return writes420

    def parse_write(self) -> transactions_pb2.Write:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t815 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t816 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t817 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t818 = 2
                        else:
                            _t818 = -1
                        _t817 = _t818
                    _t816 = _t817
                _t815 = _t816
            _t814 = _t815
        else:
            _t814 = -1
        prediction421 = _t814
        if prediction421 == 3:
            _t820 = self.parse_snapshot()
            snapshot425 = _t820
            _t821 = transactions_pb2.Write(snapshot=snapshot425)
            _t819 = _t821
        else:
            if prediction421 == 2:
                _t823 = self.parse_context()
                context424 = _t823
                _t824 = transactions_pb2.Write(context=context424)
                _t822 = _t824
            else:
                if prediction421 == 1:
                    _t826 = self.parse_undefine()
                    undefine423 = _t826
                    _t827 = transactions_pb2.Write(undefine=undefine423)
                    _t825 = _t827
                else:
                    if prediction421 == 0:
                        _t829 = self.parse_define()
                        define422 = _t829
                        _t830 = transactions_pb2.Write(define=define422)
                        _t828 = _t830
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t825 = _t828
                _t822 = _t825
            _t819 = _t822
        return _t819

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal("(")
        self.consume_literal("define")
        _t831 = self.parse_fragment()
        fragment426 = _t831
        self.consume_literal(")")
        _t832 = transactions_pb2.Define(fragment=fragment426)
        return _t832

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t833 = self.parse_new_fragment_id()
        new_fragment_id427 = _t833
        xs428 = []
        cond429 = self.match_lookahead_literal("(", 0)
        while cond429:
            _t834 = self.parse_declaration()
            item430 = _t834
            xs428.append(item430)
            cond429 = self.match_lookahead_literal("(", 0)
        declarations431 = xs428
        self.consume_literal(")")
        return self.construct_fragment(new_fragment_id427, declarations431)

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        _t835 = self.parse_fragment_id()
        fragment_id432 = _t835
        self.start_fragment(fragment_id432)
        return fragment_id432

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("functional_dependency", 1):
                _t837 = 2
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t838 = 3
                else:
                    if self.match_lookahead_literal("def", 1):
                        _t839 = 0
                    else:
                        if self.match_lookahead_literal("csv_data", 1):
                            _t840 = 3
                        else:
                            if self.match_lookahead_literal("betree_relation", 1):
                                _t841 = 3
                            else:
                                if self.match_lookahead_literal("algorithm", 1):
                                    _t842 = 1
                                else:
                                    _t842 = -1
                                _t841 = _t842
                            _t840 = _t841
                        _t839 = _t840
                    _t838 = _t839
                _t837 = _t838
            _t836 = _t837
        else:
            _t836 = -1
        prediction433 = _t836
        if prediction433 == 3:
            _t844 = self.parse_data()
            data437 = _t844
            _t845 = logic_pb2.Declaration(data=data437)
            _t843 = _t845
        else:
            if prediction433 == 2:
                _t847 = self.parse_constraint()
                constraint436 = _t847
                _t848 = logic_pb2.Declaration(constraint=constraint436)
                _t846 = _t848
            else:
                if prediction433 == 1:
                    _t850 = self.parse_algorithm()
                    algorithm435 = _t850
                    _t851 = logic_pb2.Declaration(algorithm=algorithm435)
                    _t849 = _t851
                else:
                    if prediction433 == 0:
                        _t853 = self.parse_def()
                        def434 = _t853
                        _t854 = logic_pb2.Declaration()
                        getattr(_t854, 'def').CopyFrom(def434)
                        _t852 = _t854
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t849 = _t852
                _t846 = _t849
            _t843 = _t846
        return _t843

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal("(")
        self.consume_literal("def")
        _t855 = self.parse_relation_id()
        relation_id438 = _t855
        _t856 = self.parse_abstraction()
        abstraction439 = _t856
        if self.match_lookahead_literal("(", 0):
            _t858 = self.parse_attrs()
            _t857 = _t858
        else:
            _t857 = None
        attrs440 = _t857
        self.consume_literal(")")
        _t859 = logic_pb2.Def(name=relation_id438, body=abstraction439, attrs=(attrs440 if attrs440 is not None else []))
        return _t859

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_literal(":", 0):
            _t860 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t861 = 1
            else:
                _t861 = -1
            _t860 = _t861
        prediction441 = _t860
        if prediction441 == 1:
            uint128443 = self.consume_terminal("UINT128")
            _t862 = logic_pb2.RelationId(id_low=uint128443.low, id_high=uint128443.high)
        else:
            if prediction441 == 0:
                self.consume_literal(":")
                symbol442 = self.consume_terminal("SYMBOL")
                _t863 = self.relation_id_from_string(symbol442)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t862 = _t863
        return _t862

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal("(")
        _t864 = self.parse_bindings()
        bindings444 = _t864
        _t865 = self.parse_formula()
        formula445 = _t865
        self.consume_literal(")")
        _t866 = logic_pb2.Abstraction(vars=(list(bindings444[0]) + list(bindings444[1] if bindings444[1] is not None else [])), value=formula445)
        return _t866

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs446 = []
        cond447 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond447:
            _t867 = self.parse_binding()
            item448 = _t867
            xs446.append(item448)
            cond447 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings449 = xs446
        if self.match_lookahead_literal("|", 0):
            _t869 = self.parse_value_bindings()
            _t868 = _t869
        else:
            _t868 = None
        value_bindings450 = _t868
        self.consume_literal("]")
        return (bindings449, (value_bindings450 if value_bindings450 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol451 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t870 = self.parse_type()
        type452 = _t870
        _t871 = logic_pb2.Var(name=symbol451)
        _t872 = logic_pb2.Binding(var=_t871, type=type452)
        return _t872

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t873 = 0
        else:
            if self.match_lookahead_literal("UINT128", 0):
                _t874 = 4
            else:
                if self.match_lookahead_literal("STRING", 0):
                    _t875 = 1
                else:
                    if self.match_lookahead_literal("MISSING", 0):
                        _t876 = 8
                    else:
                        if self.match_lookahead_literal("INT128", 0):
                            _t877 = 5
                        else:
                            if self.match_lookahead_literal("INT", 0):
                                _t878 = 2
                            else:
                                if self.match_lookahead_literal("FLOAT", 0):
                                    _t879 = 3
                                else:
                                    if self.match_lookahead_literal("DATETIME", 0):
                                        _t880 = 7
                                    else:
                                        if self.match_lookahead_literal("DATE", 0):
                                            _t881 = 6
                                        else:
                                            if self.match_lookahead_literal("BOOLEAN", 0):
                                                _t882 = 10
                                            else:
                                                if self.match_lookahead_literal("(", 0):
                                                    _t883 = 9
                                                else:
                                                    _t883 = -1
                                                _t882 = _t883
                                            _t881 = _t882
                                        _t880 = _t881
                                    _t879 = _t880
                                _t878 = _t879
                            _t877 = _t878
                        _t876 = _t877
                    _t875 = _t876
                _t874 = _t875
            _t873 = _t874
        prediction453 = _t873
        if prediction453 == 10:
            _t885 = self.parse_boolean_type()
            boolean_type464 = _t885
            _t886 = logic_pb2.Type(boolean_type=boolean_type464)
            _t884 = _t886
        else:
            if prediction453 == 9:
                _t888 = self.parse_decimal_type()
                decimal_type463 = _t888
                _t889 = logic_pb2.Type(decimal_type=decimal_type463)
                _t887 = _t889
            else:
                if prediction453 == 8:
                    _t891 = self.parse_missing_type()
                    missing_type462 = _t891
                    _t892 = logic_pb2.Type(missing_type=missing_type462)
                    _t890 = _t892
                else:
                    if prediction453 == 7:
                        _t894 = self.parse_datetime_type()
                        datetime_type461 = _t894
                        _t895 = logic_pb2.Type(datetime_type=datetime_type461)
                        _t893 = _t895
                    else:
                        if prediction453 == 6:
                            _t897 = self.parse_date_type()
                            date_type460 = _t897
                            _t898 = logic_pb2.Type(date_type=date_type460)
                            _t896 = _t898
                        else:
                            if prediction453 == 5:
                                _t900 = self.parse_int128_type()
                                int128_type459 = _t900
                                _t901 = logic_pb2.Type(int128_type=int128_type459)
                                _t899 = _t901
                            else:
                                if prediction453 == 4:
                                    _t903 = self.parse_uint128_type()
                                    uint128_type458 = _t903
                                    _t904 = logic_pb2.Type(uint128_type=uint128_type458)
                                    _t902 = _t904
                                else:
                                    if prediction453 == 3:
                                        _t906 = self.parse_float_type()
                                        float_type457 = _t906
                                        _t907 = logic_pb2.Type(float_type=float_type457)
                                        _t905 = _t907
                                    else:
                                        if prediction453 == 2:
                                            _t909 = self.parse_int_type()
                                            int_type456 = _t909
                                            _t910 = logic_pb2.Type(int_type=int_type456)
                                            _t908 = _t910
                                        else:
                                            if prediction453 == 1:
                                                _t912 = self.parse_string_type()
                                                string_type455 = _t912
                                                _t913 = logic_pb2.Type(string_type=string_type455)
                                                _t911 = _t913
                                            else:
                                                if prediction453 == 0:
                                                    _t915 = self.parse_unspecified_type()
                                                    unspecified_type454 = _t915
                                                    _t916 = logic_pb2.Type(unspecified_type=unspecified_type454)
                                                    _t914 = _t916
                                                else:
                                                    raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t911 = _t914
                                            _t908 = _t911
                                        _t905 = _t908
                                    _t902 = _t905
                                _t899 = _t902
                            _t896 = _t899
                        _t893 = _t896
                    _t890 = _t893
                _t887 = _t890
            _t884 = _t887
        return _t884

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        self.consume_literal("UNKNOWN")
        _t917 = logic_pb2.UnspecifiedType()
        return _t917

    def parse_string_type(self) -> logic_pb2.StringType:
        self.consume_literal("STRING")
        _t918 = logic_pb2.StringType()
        return _t918

    def parse_int_type(self) -> logic_pb2.IntType:
        self.consume_literal("INT")
        _t919 = logic_pb2.IntType()
        return _t919

    def parse_float_type(self) -> logic_pb2.FloatType:
        self.consume_literal("FLOAT")
        _t920 = logic_pb2.FloatType()
        return _t920

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        self.consume_literal("UINT128")
        _t921 = logic_pb2.UInt128Type()
        return _t921

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        self.consume_literal("INT128")
        _t922 = logic_pb2.Int128Type()
        return _t922

    def parse_date_type(self) -> logic_pb2.DateType:
        self.consume_literal("DATE")
        _t923 = logic_pb2.DateType()
        return _t923

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        self.consume_literal("DATETIME")
        _t924 = logic_pb2.DateTimeType()
        return _t924

    def parse_missing_type(self) -> logic_pb2.MissingType:
        self.consume_literal("MISSING")
        _t925 = logic_pb2.MissingType()
        return _t925

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int465 = self.consume_terminal("INT")
        int_3466 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t926 = logic_pb2.DecimalType(precision=int(int465), scale=int(int_3466))
        return _t926

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal("BOOLEAN")
        _t927 = logic_pb2.BooleanType()
        return _t927

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs467 = []
        cond468 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond468:
            _t928 = self.parse_binding()
            item469 = _t928
            xs467.append(item469)
            cond468 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings470 = xs467
        return bindings470

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t930 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t931 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t932 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t933 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t934 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t935 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t936 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t937 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t938 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t939 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t940 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t941 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t942 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t943 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t944 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t945 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t946 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t947 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t948 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t949 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t950 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t951 = 10
                                                                                                else:
                                                                                                    _t951 = -1
                                                                                                _t950 = _t951
                                                                                            _t949 = _t950
                                                                                        _t948 = _t949
                                                                                    _t947 = _t948
                                                                                _t946 = _t947
                                                                            _t945 = _t946
                                                                        _t944 = _t945
                                                                    _t943 = _t944
                                                                _t942 = _t943
                                                            _t941 = _t942
                                                        _t940 = _t941
                                                    _t939 = _t940
                                                _t938 = _t939
                                            _t937 = _t938
                                        _t936 = _t937
                                    _t935 = _t936
                                _t934 = _t935
                            _t933 = _t934
                        _t932 = _t933
                    _t931 = _t932
                _t930 = _t931
            _t929 = _t930
        else:
            _t929 = -1
        prediction471 = _t929
        if prediction471 == 12:
            _t953 = self.parse_cast()
            cast484 = _t953
            _t954 = logic_pb2.Formula(cast=cast484)
            _t952 = _t954
        else:
            if prediction471 == 11:
                _t956 = self.parse_rel_atom()
                rel_atom483 = _t956
                _t957 = logic_pb2.Formula(rel_atom=rel_atom483)
                _t955 = _t957
            else:
                if prediction471 == 10:
                    _t959 = self.parse_primitive()
                    primitive482 = _t959
                    _t960 = logic_pb2.Formula(primitive=primitive482)
                    _t958 = _t960
                else:
                    if prediction471 == 9:
                        _t962 = self.parse_pragma()
                        pragma481 = _t962
                        _t963 = logic_pb2.Formula(pragma=pragma481)
                        _t961 = _t963
                    else:
                        if prediction471 == 8:
                            _t965 = self.parse_atom()
                            atom480 = _t965
                            _t966 = logic_pb2.Formula(atom=atom480)
                            _t964 = _t966
                        else:
                            if prediction471 == 7:
                                _t968 = self.parse_ffi()
                                ffi479 = _t968
                                _t969 = logic_pb2.Formula(ffi=ffi479)
                                _t967 = _t969
                            else:
                                if prediction471 == 6:
                                    _t971 = self.parse_not()
                                    not478 = _t971
                                    _t972 = logic_pb2.Formula()
                                    getattr(_t972, 'not').CopyFrom(not478)
                                    _t970 = _t972
                                else:
                                    if prediction471 == 5:
                                        _t974 = self.parse_disjunction()
                                        disjunction477 = _t974
                                        _t975 = logic_pb2.Formula(disjunction=disjunction477)
                                        _t973 = _t975
                                    else:
                                        if prediction471 == 4:
                                            _t977 = self.parse_conjunction()
                                            conjunction476 = _t977
                                            _t978 = logic_pb2.Formula(conjunction=conjunction476)
                                            _t976 = _t978
                                        else:
                                            if prediction471 == 3:
                                                _t980 = self.parse_reduce()
                                                reduce475 = _t980
                                                _t981 = logic_pb2.Formula(reduce=reduce475)
                                                _t979 = _t981
                                            else:
                                                if prediction471 == 2:
                                                    _t983 = self.parse_exists()
                                                    exists474 = _t983
                                                    _t984 = logic_pb2.Formula(exists=exists474)
                                                    _t982 = _t984
                                                else:
                                                    if prediction471 == 1:
                                                        _t986 = self.parse_false()
                                                        false473 = _t986
                                                        _t987 = logic_pb2.Formula(disjunction=false473)
                                                        _t985 = _t987
                                                    else:
                                                        if prediction471 == 0:
                                                            _t989 = self.parse_true()
                                                            true472 = _t989
                                                            _t990 = logic_pb2.Formula(conjunction=true472)
                                                            _t988 = _t990
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t985 = _t988
                                                    _t982 = _t985
                                                _t979 = _t982
                                            _t976 = _t979
                                        _t973 = _t976
                                    _t970 = _t973
                                _t967 = _t970
                            _t964 = _t967
                        _t961 = _t964
                    _t958 = _t961
                _t955 = _t958
            _t952 = _t955
        return _t952

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t991 = logic_pb2.Conjunction(args=[])
        return _t991

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t992 = logic_pb2.Disjunction(args=[])
        return _t992

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal("(")
        self.consume_literal("exists")
        _t993 = self.parse_bindings()
        bindings485 = _t993
        _t994 = self.parse_formula()
        formula486 = _t994
        self.consume_literal(")")
        _t995 = logic_pb2.Abstraction(vars=(list(bindings485[0]) + list(bindings485[1] if bindings485[1] is not None else [])), value=formula486)
        _t996 = logic_pb2.Exists(body=_t995)
        return _t996

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t997 = self.parse_abstraction()
        abstraction487 = _t997
        _t998 = self.parse_abstraction()
        abstraction_3488 = _t998
        _t999 = self.parse_terms()
        terms489 = _t999
        self.consume_literal(")")
        _t1000 = logic_pb2.Reduce(op=abstraction487, body=abstraction_3488, terms=terms489)
        return _t1000

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs490 = []
        cond491 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond491:
            _t1001 = self.parse_term()
            item492 = _t1001
            xs490.append(item492)
            cond491 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms493 = xs490
        self.consume_literal(")")
        return terms493

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_literal("true", 0):
            _t1002 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1003 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1004 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1005 = 1
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t1006 = 1
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1007 = 0
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1008 = 1
                                else:
                                    if self.match_lookahead_terminal("INT128", 0):
                                        _t1009 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT", 0):
                                            _t1010 = 1
                                        else:
                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                _t1011 = 1
                                            else:
                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                    _t1012 = 1
                                                else:
                                                    _t1012 = -1
                                                _t1011 = _t1012
                                            _t1010 = _t1011
                                        _t1009 = _t1010
                                    _t1008 = _t1009
                                _t1007 = _t1008
                            _t1006 = _t1007
                        _t1005 = _t1006
                    _t1004 = _t1005
                _t1003 = _t1004
            _t1002 = _t1003
        prediction494 = _t1002
        if prediction494 == 1:
            _t1014 = self.parse_constant()
            constant496 = _t1014
            _t1015 = logic_pb2.Term(constant=constant496)
            _t1013 = _t1015
        else:
            if prediction494 == 0:
                _t1017 = self.parse_var()
                var495 = _t1017
                _t1018 = logic_pb2.Term(var=var495)
                _t1016 = _t1018
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1013 = _t1016
        return _t1013

    def parse_var(self) -> logic_pb2.Var:
        symbol497 = self.consume_terminal("SYMBOL")
        _t1019 = logic_pb2.Var(name=symbol497)
        return _t1019

    def parse_constant(self) -> logic_pb2.Value:
        _t1020 = self.parse_value()
        value498 = _t1020
        return value498

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal("(")
        self.consume_literal("and")
        xs499 = []
        cond500 = self.match_lookahead_literal("(", 0)
        while cond500:
            _t1021 = self.parse_formula()
            item501 = _t1021
            xs499.append(item501)
            cond500 = self.match_lookahead_literal("(", 0)
        formulas502 = xs499
        self.consume_literal(")")
        _t1022 = logic_pb2.Conjunction(args=formulas502)
        return _t1022

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal("(")
        self.consume_literal("or")
        xs503 = []
        cond504 = self.match_lookahead_literal("(", 0)
        while cond504:
            _t1023 = self.parse_formula()
            item505 = _t1023
            xs503.append(item505)
            cond504 = self.match_lookahead_literal("(", 0)
        formulas506 = xs503
        self.consume_literal(")")
        _t1024 = logic_pb2.Disjunction(args=formulas506)
        return _t1024

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal("(")
        self.consume_literal("not")
        _t1025 = self.parse_formula()
        formula507 = _t1025
        self.consume_literal(")")
        _t1026 = logic_pb2.Not(arg=formula507)
        return _t1026

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1027 = self.parse_name()
        name508 = _t1027
        _t1028 = self.parse_ffi_args()
        ffi_args509 = _t1028
        _t1029 = self.parse_terms()
        terms510 = _t1029
        self.consume_literal(")")
        _t1030 = logic_pb2.FFI(name=name508, args=ffi_args509, terms=terms510)
        return _t1030

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol511 = self.consume_terminal("SYMBOL")
        return symbol511

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs512 = []
        cond513 = self.match_lookahead_literal("(", 0)
        while cond513:
            _t1031 = self.parse_abstraction()
            item514 = _t1031
            xs512.append(item514)
            cond513 = self.match_lookahead_literal("(", 0)
        abstractions515 = xs512
        self.consume_literal(")")
        return abstractions515

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1032 = self.parse_relation_id()
        relation_id516 = _t1032
        xs517 = []
        cond518 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond518:
            _t1033 = self.parse_term()
            item519 = _t1033
            xs517.append(item519)
            cond518 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms520 = xs517
        self.consume_literal(")")
        _t1034 = logic_pb2.Atom(name=relation_id516, terms=terms520)
        return _t1034

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1035 = self.parse_name()
        name521 = _t1035
        xs522 = []
        cond523 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond523:
            _t1036 = self.parse_term()
            item524 = _t1036
            xs522.append(item524)
            cond523 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms525 = xs522
        self.consume_literal(")")
        _t1037 = logic_pb2.Pragma(name=name521, terms=terms525)
        return _t1037

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1039 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1040 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1041 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1042 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1043 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1044 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1045 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1046 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1047 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1048 = 7
                                                else:
                                                    _t1048 = -1
                                                _t1047 = _t1048
                                            _t1046 = _t1047
                                        _t1045 = _t1046
                                    _t1044 = _t1045
                                _t1043 = _t1044
                            _t1042 = _t1043
                        _t1041 = _t1042
                    _t1040 = _t1041
                _t1039 = _t1040
            _t1038 = _t1039
        else:
            _t1038 = -1
        prediction526 = _t1038
        if prediction526 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1050 = self.parse_name()
            name536 = _t1050
            xs537 = []
            cond538 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            while cond538:
                _t1051 = self.parse_rel_term()
                item539 = _t1051
                xs537.append(item539)
                cond538 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            rel_terms540 = xs537
            self.consume_literal(")")
            _t1052 = logic_pb2.Primitive(name=name536, terms=rel_terms540)
            _t1049 = _t1052
        else:
            if prediction526 == 8:
                _t1054 = self.parse_divide()
                divide535 = _t1054
                _t1053 = divide535
            else:
                if prediction526 == 7:
                    _t1056 = self.parse_multiply()
                    multiply534 = _t1056
                    _t1055 = multiply534
                else:
                    if prediction526 == 6:
                        _t1058 = self.parse_minus()
                        minus533 = _t1058
                        _t1057 = minus533
                    else:
                        if prediction526 == 5:
                            _t1060 = self.parse_add()
                            add532 = _t1060
                            _t1059 = add532
                        else:
                            if prediction526 == 4:
                                _t1062 = self.parse_gt_eq()
                                gt_eq531 = _t1062
                                _t1061 = gt_eq531
                            else:
                                if prediction526 == 3:
                                    _t1064 = self.parse_gt()
                                    gt530 = _t1064
                                    _t1063 = gt530
                                else:
                                    if prediction526 == 2:
                                        _t1066 = self.parse_lt_eq()
                                        lt_eq529 = _t1066
                                        _t1065 = lt_eq529
                                    else:
                                        if prediction526 == 1:
                                            _t1068 = self.parse_lt()
                                            lt528 = _t1068
                                            _t1067 = lt528
                                        else:
                                            if prediction526 == 0:
                                                _t1070 = self.parse_eq()
                                                eq527 = _t1070
                                                _t1069 = eq527
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1067 = _t1069
                                        _t1065 = _t1067
                                    _t1063 = _t1065
                                _t1061 = _t1063
                            _t1059 = _t1061
                        _t1057 = _t1059
                    _t1055 = _t1057
                _t1053 = _t1055
            _t1049 = _t1053
        return _t1049

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("=")
        _t1071 = self.parse_term()
        term541 = _t1071
        _t1072 = self.parse_term()
        term_3542 = _t1072
        self.consume_literal(")")
        _t1073 = logic_pb2.RelTerm(term=term541)
        _t1074 = logic_pb2.RelTerm(term=term_3542)
        _t1075 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1073, _t1074])
        return _t1075

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("<")
        _t1076 = self.parse_term()
        term543 = _t1076
        _t1077 = self.parse_term()
        term_3544 = _t1077
        self.consume_literal(")")
        _t1078 = logic_pb2.RelTerm(term=term543)
        _t1079 = logic_pb2.RelTerm(term=term_3544)
        _t1080 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1078, _t1079])
        return _t1080

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1081 = self.parse_term()
        term545 = _t1081
        _t1082 = self.parse_term()
        term_3546 = _t1082
        self.consume_literal(")")
        _t1083 = logic_pb2.RelTerm(term=term545)
        _t1084 = logic_pb2.RelTerm(term=term_3546)
        _t1085 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1083, _t1084])
        return _t1085

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal(">")
        _t1086 = self.parse_term()
        term547 = _t1086
        _t1087 = self.parse_term()
        term_3548 = _t1087
        self.consume_literal(")")
        _t1088 = logic_pb2.RelTerm(term=term547)
        _t1089 = logic_pb2.RelTerm(term=term_3548)
        _t1090 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1088, _t1089])
        return _t1090

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1091 = self.parse_term()
        term549 = _t1091
        _t1092 = self.parse_term()
        term_3550 = _t1092
        self.consume_literal(")")
        _t1093 = logic_pb2.RelTerm(term=term549)
        _t1094 = logic_pb2.RelTerm(term=term_3550)
        _t1095 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1093, _t1094])
        return _t1095

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("+")
        _t1096 = self.parse_term()
        term551 = _t1096
        _t1097 = self.parse_term()
        term_3552 = _t1097
        _t1098 = self.parse_term()
        term_4553 = _t1098
        self.consume_literal(")")
        _t1099 = logic_pb2.RelTerm(term=term551)
        _t1100 = logic_pb2.RelTerm(term=term_3552)
        _t1101 = logic_pb2.RelTerm(term=term_4553)
        _t1102 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1099, _t1100, _t1101])
        return _t1102

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("-")
        _t1103 = self.parse_term()
        term554 = _t1103
        _t1104 = self.parse_term()
        term_3555 = _t1104
        _t1105 = self.parse_term()
        term_4556 = _t1105
        self.consume_literal(")")
        _t1106 = logic_pb2.RelTerm(term=term554)
        _t1107 = logic_pb2.RelTerm(term=term_3555)
        _t1108 = logic_pb2.RelTerm(term=term_4556)
        _t1109 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1106, _t1107, _t1108])
        return _t1109

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("*")
        _t1110 = self.parse_term()
        term557 = _t1110
        _t1111 = self.parse_term()
        term_3558 = _t1111
        _t1112 = self.parse_term()
        term_4559 = _t1112
        self.consume_literal(")")
        _t1113 = logic_pb2.RelTerm(term=term557)
        _t1114 = logic_pb2.RelTerm(term=term_3558)
        _t1115 = logic_pb2.RelTerm(term=term_4559)
        _t1116 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1113, _t1114, _t1115])
        return _t1116

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("/")
        _t1117 = self.parse_term()
        term560 = _t1117
        _t1118 = self.parse_term()
        term_3561 = _t1118
        _t1119 = self.parse_term()
        term_4562 = _t1119
        self.consume_literal(")")
        _t1120 = logic_pb2.RelTerm(term=term560)
        _t1121 = logic_pb2.RelTerm(term=term_3561)
        _t1122 = logic_pb2.RelTerm(term=term_4562)
        _t1123 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1120, _t1121, _t1122])
        return _t1123

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_literal("true", 0):
            _t1124 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1125 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1126 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1127 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1128 = 0
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1129 = 1
                            else:
                                if self.match_lookahead_terminal("SYMBOL", 0):
                                    _t1130 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1131 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1132 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1133 = 1
                                            else:
                                                if self.match_lookahead_terminal("FLOAT", 0):
                                                    _t1134 = 1
                                                else:
                                                    if self.match_lookahead_terminal("DECIMAL", 0):
                                                        _t1135 = 1
                                                    else:
                                                        _t1135 = -1
                                                    _t1134 = _t1135
                                                _t1133 = _t1134
                                            _t1132 = _t1133
                                        _t1131 = _t1132
                                    _t1130 = _t1131
                                _t1129 = _t1130
                            _t1128 = _t1129
                        _t1127 = _t1128
                    _t1126 = _t1127
                _t1125 = _t1126
            _t1124 = _t1125
        prediction563 = _t1124
        if prediction563 == 1:
            _t1137 = self.parse_term()
            term565 = _t1137
            _t1138 = logic_pb2.RelTerm(term=term565)
            _t1136 = _t1138
        else:
            if prediction563 == 0:
                _t1140 = self.parse_specialized_value()
                specialized_value564 = _t1140
                _t1141 = logic_pb2.RelTerm(specialized_value=specialized_value564)
                _t1139 = _t1141
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1136 = _t1139
        return _t1136

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal("#")
        _t1142 = self.parse_value()
        value566 = _t1142
        return value566

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1143 = self.parse_name()
        name567 = _t1143
        xs568 = []
        cond569 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond569:
            _t1144 = self.parse_rel_term()
            item570 = _t1144
            xs568.append(item570)
            cond569 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        rel_terms571 = xs568
        self.consume_literal(")")
        _t1145 = logic_pb2.RelAtom(name=name567, terms=rel_terms571)
        return _t1145

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1146 = self.parse_term()
        term572 = _t1146
        _t1147 = self.parse_term()
        term_3573 = _t1147
        self.consume_literal(")")
        _t1148 = logic_pb2.Cast(input=term572, result=term_3573)
        return _t1148

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs574 = []
        cond575 = self.match_lookahead_literal("(", 0)
        while cond575:
            _t1149 = self.parse_attribute()
            item576 = _t1149
            xs574.append(item576)
            cond575 = self.match_lookahead_literal("(", 0)
        attributes577 = xs574
        self.consume_literal(")")
        return attributes577

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1150 = self.parse_name()
        name578 = _t1150
        xs579 = []
        cond580 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond580:
            _t1151 = self.parse_value()
            item581 = _t1151
            xs579.append(item581)
            cond580 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        values582 = xs579
        self.consume_literal(")")
        _t1152 = logic_pb2.Attribute(name=name578, args=values582)
        return _t1152

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs583 = []
        cond584 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond584:
            _t1153 = self.parse_relation_id()
            item585 = _t1153
            xs583.append(item585)
            cond584 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids586 = xs583
        _t1154 = self.parse_script()
        script587 = _t1154
        self.consume_literal(")")
        _t1155 = logic_pb2.Algorithm(body=script587)
        getattr(_t1155, 'global').extend(relation_ids586)
        return _t1155

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal("(")
        self.consume_literal("script")
        xs588 = []
        cond589 = self.match_lookahead_literal("(", 0)
        while cond589:
            _t1156 = self.parse_construct()
            item590 = _t1156
            xs588.append(item590)
            cond589 = self.match_lookahead_literal("(", 0)
        constructs591 = xs588
        self.consume_literal(")")
        _t1157 = logic_pb2.Script(constructs=constructs591)
        return _t1157

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1159 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1160 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1161 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1162 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1163 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1164 = 1
                                else:
                                    _t1164 = -1
                                _t1163 = _t1164
                            _t1162 = _t1163
                        _t1161 = _t1162
                    _t1160 = _t1161
                _t1159 = _t1160
            _t1158 = _t1159
        else:
            _t1158 = -1
        prediction592 = _t1158
        if prediction592 == 1:
            _t1166 = self.parse_instruction()
            instruction594 = _t1166
            _t1167 = logic_pb2.Construct(instruction=instruction594)
            _t1165 = _t1167
        else:
            if prediction592 == 0:
                _t1169 = self.parse_loop()
                loop593 = _t1169
                _t1170 = logic_pb2.Construct(loop=loop593)
                _t1168 = _t1170
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1165 = _t1168
        return _t1165

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1171 = self.parse_init()
        init595 = _t1171
        _t1172 = self.parse_script()
        script596 = _t1172
        self.consume_literal(")")
        _t1173 = logic_pb2.Loop(init=init595, body=script596)
        return _t1173

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs597 = []
        cond598 = self.match_lookahead_literal("(", 0)
        while cond598:
            _t1174 = self.parse_instruction()
            item599 = _t1174
            xs597.append(item599)
            cond598 = self.match_lookahead_literal("(", 0)
        instructions600 = xs597
        self.consume_literal(")")
        return instructions600

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1176 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1177 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1178 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1179 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1180 = 0
                            else:
                                _t1180 = -1
                            _t1179 = _t1180
                        _t1178 = _t1179
                    _t1177 = _t1178
                _t1176 = _t1177
            _t1175 = _t1176
        else:
            _t1175 = -1
        prediction601 = _t1175
        if prediction601 == 4:
            _t1182 = self.parse_monus_def()
            monus_def606 = _t1182
            _t1183 = logic_pb2.Instruction(monus_def=monus_def606)
            _t1181 = _t1183
        else:
            if prediction601 == 3:
                _t1185 = self.parse_monoid_def()
                monoid_def605 = _t1185
                _t1186 = logic_pb2.Instruction(monoid_def=monoid_def605)
                _t1184 = _t1186
            else:
                if prediction601 == 2:
                    _t1188 = self.parse_break()
                    break604 = _t1188
                    _t1189 = logic_pb2.Instruction()
                    getattr(_t1189, 'break').CopyFrom(break604)
                    _t1187 = _t1189
                else:
                    if prediction601 == 1:
                        _t1191 = self.parse_upsert()
                        upsert603 = _t1191
                        _t1192 = logic_pb2.Instruction(upsert=upsert603)
                        _t1190 = _t1192
                    else:
                        if prediction601 == 0:
                            _t1194 = self.parse_assign()
                            assign602 = _t1194
                            _t1195 = logic_pb2.Instruction(assign=assign602)
                            _t1193 = _t1195
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1190 = _t1193
                    _t1187 = _t1190
                _t1184 = _t1187
            _t1181 = _t1184
        return _t1181

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1196 = self.parse_relation_id()
        relation_id607 = _t1196
        _t1197 = self.parse_abstraction()
        abstraction608 = _t1197
        if self.match_lookahead_literal("(", 0):
            _t1199 = self.parse_attrs()
            _t1198 = _t1199
        else:
            _t1198 = None
        attrs609 = _t1198
        self.consume_literal(")")
        _t1200 = logic_pb2.Assign(name=relation_id607, body=abstraction608, attrs=(attrs609 if attrs609 is not None else []))
        return _t1200

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1201 = self.parse_relation_id()
        relation_id610 = _t1201
        _t1202 = self.parse_abstraction_with_arity()
        abstraction_with_arity611 = _t1202
        if self.match_lookahead_literal("(", 0):
            _t1204 = self.parse_attrs()
            _t1203 = _t1204
        else:
            _t1203 = None
        attrs612 = _t1203
        self.consume_literal(")")
        _t1205 = logic_pb2.Upsert(name=relation_id610, body=abstraction_with_arity611[0], attrs=(attrs612 if attrs612 is not None else []), value_arity=abstraction_with_arity611[1])
        return _t1205

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1206 = self.parse_bindings()
        bindings613 = _t1206
        _t1207 = self.parse_formula()
        formula614 = _t1207
        self.consume_literal(")")
        _t1208 = logic_pb2.Abstraction(vars=(list(bindings613[0]) + list(bindings613[1] if bindings613[1] is not None else [])), value=formula614)
        return (_t1208, len(bindings613[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal("(")
        self.consume_literal("break")
        _t1209 = self.parse_relation_id()
        relation_id615 = _t1209
        _t1210 = self.parse_abstraction()
        abstraction616 = _t1210
        if self.match_lookahead_literal("(", 0):
            _t1212 = self.parse_attrs()
            _t1211 = _t1212
        else:
            _t1211 = None
        attrs617 = _t1211
        self.consume_literal(")")
        _t1213 = logic_pb2.Break(name=relation_id615, body=abstraction616, attrs=(attrs617 if attrs617 is not None else []))
        return _t1213

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1214 = self.parse_monoid()
        monoid618 = _t1214
        _t1215 = self.parse_relation_id()
        relation_id619 = _t1215
        _t1216 = self.parse_abstraction_with_arity()
        abstraction_with_arity620 = _t1216
        if self.match_lookahead_literal("(", 0):
            _t1218 = self.parse_attrs()
            _t1217 = _t1218
        else:
            _t1217 = None
        attrs621 = _t1217
        self.consume_literal(")")
        _t1219 = logic_pb2.MonoidDef(monoid=monoid618, name=relation_id619, body=abstraction_with_arity620[0], attrs=(attrs621 if attrs621 is not None else []), value_arity=abstraction_with_arity620[1])
        return _t1219

    def parse_monoid(self) -> logic_pb2.Monoid:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1221 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1222 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1223 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1224 = 2
                        else:
                            _t1224 = -1
                        _t1223 = _t1224
                    _t1222 = _t1223
                _t1221 = _t1222
            _t1220 = _t1221
        else:
            _t1220 = -1
        prediction622 = _t1220
        if prediction622 == 3:
            _t1226 = self.parse_sum_monoid()
            sum_monoid626 = _t1226
            _t1227 = logic_pb2.Monoid(sum_monoid=sum_monoid626)
            _t1225 = _t1227
        else:
            if prediction622 == 2:
                _t1229 = self.parse_max_monoid()
                max_monoid625 = _t1229
                _t1230 = logic_pb2.Monoid(max_monoid=max_monoid625)
                _t1228 = _t1230
            else:
                if prediction622 == 1:
                    _t1232 = self.parse_min_monoid()
                    min_monoid624 = _t1232
                    _t1233 = logic_pb2.Monoid(min_monoid=min_monoid624)
                    _t1231 = _t1233
                else:
                    if prediction622 == 0:
                        _t1235 = self.parse_or_monoid()
                        or_monoid623 = _t1235
                        _t1236 = logic_pb2.Monoid(or_monoid=or_monoid623)
                        _t1234 = _t1236
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1231 = _t1234
                _t1228 = _t1231
            _t1225 = _t1228
        return _t1225

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1237 = logic_pb2.OrMonoid()
        return _t1237

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        self.consume_literal("(")
        self.consume_literal("min")
        _t1238 = self.parse_type()
        type627 = _t1238
        self.consume_literal(")")
        _t1239 = logic_pb2.MinMonoid(type=type627)
        return _t1239

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        self.consume_literal("(")
        self.consume_literal("max")
        _t1240 = self.parse_type()
        type628 = _t1240
        self.consume_literal(")")
        _t1241 = logic_pb2.MaxMonoid(type=type628)
        return _t1241

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1242 = self.parse_type()
        type629 = _t1242
        self.consume_literal(")")
        _t1243 = logic_pb2.SumMonoid(type=type629)
        return _t1243

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1244 = self.parse_monoid()
        monoid630 = _t1244
        _t1245 = self.parse_relation_id()
        relation_id631 = _t1245
        _t1246 = self.parse_abstraction_with_arity()
        abstraction_with_arity632 = _t1246
        if self.match_lookahead_literal("(", 0):
            _t1248 = self.parse_attrs()
            _t1247 = _t1248
        else:
            _t1247 = None
        attrs633 = _t1247
        self.consume_literal(")")
        _t1249 = logic_pb2.MonusDef(monoid=monoid630, name=relation_id631, body=abstraction_with_arity632[0], attrs=(attrs633 if attrs633 is not None else []), value_arity=abstraction_with_arity632[1])
        return _t1249

    def parse_constraint(self) -> logic_pb2.Constraint:
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1250 = self.parse_relation_id()
        relation_id634 = _t1250
        _t1251 = self.parse_abstraction()
        abstraction635 = _t1251
        _t1252 = self.parse_functional_dependency_keys()
        functional_dependency_keys636 = _t1252
        _t1253 = self.parse_functional_dependency_values()
        functional_dependency_values637 = _t1253
        self.consume_literal(")")
        _t1254 = logic_pb2.FunctionalDependency(guard=abstraction635, keys=functional_dependency_keys636, values=functional_dependency_values637)
        _t1255 = logic_pb2.Constraint(name=relation_id634, functional_dependency=_t1254)
        return _t1255

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs638 = []
        cond639 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond639:
            _t1256 = self.parse_var()
            item640 = _t1256
            xs638.append(item640)
            cond639 = self.match_lookahead_terminal("SYMBOL", 0)
        vars641 = xs638
        self.consume_literal(")")
        return vars641

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs642 = []
        cond643 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond643:
            _t1257 = self.parse_var()
            item644 = _t1257
            xs642.append(item644)
            cond643 = self.match_lookahead_terminal("SYMBOL", 0)
        vars645 = xs642
        self.consume_literal(")")
        return vars645

    def parse_data(self) -> logic_pb2.Data:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("edb", 1):
                _t1259 = 0
            else:
                if self.match_lookahead_literal("csv_data", 1):
                    _t1260 = 2
                else:
                    if self.match_lookahead_literal("betree_relation", 1):
                        _t1261 = 1
                    else:
                        _t1261 = -1
                    _t1260 = _t1261
                _t1259 = _t1260
            _t1258 = _t1259
        else:
            _t1258 = -1
        prediction646 = _t1258
        if prediction646 == 2:
            _t1263 = self.parse_csv_data()
            csv_data649 = _t1263
            _t1264 = logic_pb2.Data(csv_data=csv_data649)
            _t1262 = _t1264
        else:
            if prediction646 == 1:
                _t1266 = self.parse_betree_relation()
                betree_relation648 = _t1266
                _t1267 = logic_pb2.Data(betree_relation=betree_relation648)
                _t1265 = _t1267
            else:
                if prediction646 == 0:
                    _t1269 = self.parse_edb()
                    edb647 = _t1269
                    _t1270 = logic_pb2.Data(edb=edb647)
                    _t1268 = _t1270
                else:
                    raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t1265 = _t1268
            _t1262 = _t1265
        return _t1262

    def parse_edb(self) -> logic_pb2.EDB:
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1271 = self.parse_relation_id()
        relation_id650 = _t1271
        _t1272 = self.parse_edb_path()
        edb_path651 = _t1272
        _t1273 = self.parse_edb_types()
        edb_types652 = _t1273
        self.consume_literal(")")
        _t1274 = logic_pb2.EDB(target_id=relation_id650, path=edb_path651, types=edb_types652)
        return _t1274

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs653 = []
        cond654 = self.match_lookahead_terminal("STRING", 0)
        while cond654:
            item655 = self.consume_terminal("STRING")
            xs653.append(item655)
            cond654 = self.match_lookahead_terminal("STRING", 0)
        strings656 = xs653
        self.consume_literal("]")
        return strings656

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs657 = []
        cond658 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond658:
            _t1275 = self.parse_type()
            item659 = _t1275
            xs657.append(item659)
            cond658 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types660 = xs657
        self.consume_literal("]")
        return types660

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1276 = self.parse_relation_id()
        relation_id661 = _t1276
        _t1277 = self.parse_betree_info()
        betree_info662 = _t1277
        self.consume_literal(")")
        _t1278 = logic_pb2.BeTreeRelation(name=relation_id661, relation_info=betree_info662)
        return _t1278

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1279 = self.parse_betree_info_key_types()
        betree_info_key_types663 = _t1279
        _t1280 = self.parse_betree_info_value_types()
        betree_info_value_types664 = _t1280
        _t1281 = self.parse_config_dict()
        config_dict665 = _t1281
        self.consume_literal(")")
        _t1282 = self.construct_betree_info(betree_info_key_types663, betree_info_value_types664, config_dict665)
        return _t1282

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs666 = []
        cond667 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond667:
            _t1283 = self.parse_type()
            item668 = _t1283
            xs666.append(item668)
            cond667 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types669 = xs666
        self.consume_literal(")")
        return types669

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs670 = []
        cond671 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond671:
            _t1284 = self.parse_type()
            item672 = _t1284
            xs670.append(item672)
            cond671 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types673 = xs670
        self.consume_literal(")")
        return types673

    def parse_csv_data(self) -> logic_pb2.CSVData:
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1285 = self.parse_csvlocator()
        csvlocator674 = _t1285
        _t1286 = self.parse_csv_config()
        csv_config675 = _t1286
        _t1287 = self.parse_gnf_columns()
        gnf_columns676 = _t1287
        _t1288 = self.parse_csv_asof()
        csv_asof677 = _t1288
        self.consume_literal(")")
        _t1289 = logic_pb2.CSVData(locator=csvlocator674, config=csv_config675, columns=gnf_columns676, asof=csv_asof677)
        return _t1289

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1291 = self.parse_csv_locator_paths()
            _t1290 = _t1291
        else:
            _t1290 = None
        csv_locator_paths678 = _t1290
        if self.match_lookahead_literal("(", 0):
            _t1293 = self.parse_csv_locator_inline_data()
            _t1292 = _t1293
        else:
            _t1292 = None
        csv_locator_inline_data679 = _t1292
        self.consume_literal(")")
        _t1294 = logic_pb2.CSVLocator(paths=(csv_locator_paths678 if csv_locator_paths678 is not None else []), inline_data=(csv_locator_inline_data679 if csv_locator_inline_data679 is not None else "").encode())
        return _t1294

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs680 = []
        cond681 = self.match_lookahead_terminal("STRING", 0)
        while cond681:
            item682 = self.consume_terminal("STRING")
            xs680.append(item682)
            cond681 = self.match_lookahead_terminal("STRING", 0)
        strings683 = xs680
        self.consume_literal(")")
        return strings683

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string684 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string684

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1295 = self.parse_config_dict()
        config_dict685 = _t1295
        self.consume_literal(")")
        _t1296 = self.construct_csv_config(config_dict685)
        return _t1296

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs686 = []
        cond687 = self.match_lookahead_literal("(", 0)
        while cond687:
            _t1297 = self.parse_gnf_column()
            item688 = _t1297
            xs686.append(item688)
            cond687 = self.match_lookahead_literal("(", 0)
        gnf_columns689 = xs686
        self.consume_literal(")")
        return gnf_columns689

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        self.consume_literal("(")
        self.consume_literal("column")
        _t1298 = self.parse_gnf_column_path()
        gnf_column_path690 = _t1298
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1300 = self.parse_relation_id()
            _t1299 = _t1300
        else:
            _t1299 = None
        relation_id691 = _t1299
        self.consume_literal("[")
        xs692 = []
        cond693 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond693:
            _t1301 = self.parse_type()
            item694 = _t1301
            xs692.append(item694)
            cond693 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types695 = xs692
        self.consume_literal("]")
        self.consume_literal(")")
        _t1302 = logic_pb2.GNFColumn(column_path=gnf_column_path690, target_id=relation_id691, types=types695)
        return _t1302

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1303 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1304 = 0
            else:
                _t1304 = -1
            _t1303 = _t1304
        prediction696 = _t1303
        if prediction696 == 1:
            self.consume_literal("[")
            xs698 = []
            cond699 = self.match_lookahead_terminal("STRING", 0)
            while cond699:
                item700 = self.consume_terminal("STRING")
                xs698.append(item700)
                cond699 = self.match_lookahead_terminal("STRING", 0)
            strings701 = xs698
            self.consume_literal("]")
            _t1305 = strings701
        else:
            if prediction696 == 0:
                string697 = self.consume_terminal("STRING")
                _t1306 = [string697]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1305 = _t1306
        return _t1305

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string702 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string702

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1307 = self.parse_fragment_id()
        fragment_id703 = _t1307
        self.consume_literal(")")
        _t1308 = transactions_pb2.Undefine(fragment_id=fragment_id703)
        return _t1308

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal("(")
        self.consume_literal("context")
        xs704 = []
        cond705 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond705:
            _t1309 = self.parse_relation_id()
            item706 = _t1309
            xs704.append(item706)
            cond705 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids707 = xs704
        self.consume_literal(")")
        _t1310 = transactions_pb2.Context(relations=relation_ids707)
        return _t1310

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        self.consume_literal("(")
        self.consume_literal("snapshot")
        xs708 = []
        cond709 = self.match_lookahead_literal("[", 0)
        while cond709:
            _t1311 = self.parse_snapshot_mapping()
            item710 = _t1311
            xs708.append(item710)
            cond709 = self.match_lookahead_literal("[", 0)
        snapshot_mappings711 = xs708
        self.consume_literal(")")
        _t1312 = transactions_pb2.Snapshot(mappings=snapshot_mappings711)
        return _t1312

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        _t1313 = self.parse_edb_path()
        edb_path712 = _t1313
        _t1314 = self.parse_relation_id()
        relation_id713 = _t1314
        _t1315 = transactions_pb2.SnapshotMapping(destination_path=edb_path712, source_relation=relation_id713)
        return _t1315

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs714 = []
        cond715 = self.match_lookahead_literal("(", 0)
        while cond715:
            _t1316 = self.parse_read()
            item716 = _t1316
            xs714.append(item716)
            cond715 = self.match_lookahead_literal("(", 0)
        reads717 = xs714
        self.consume_literal(")")
        return reads717

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1318 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1319 = 1
                else:
                    if self.match_lookahead_literal("export", 1):
                        _t1320 = 4
                    else:
                        if self.match_lookahead_literal("demand", 1):
                            _t1321 = 0
                        else:
                            if self.match_lookahead_literal("abort", 1):
                                _t1322 = 3
                            else:
                                _t1322 = -1
                            _t1321 = _t1322
                        _t1320 = _t1321
                    _t1319 = _t1320
                _t1318 = _t1319
            _t1317 = _t1318
        else:
            _t1317 = -1
        prediction718 = _t1317
        if prediction718 == 4:
            _t1324 = self.parse_export()
            export723 = _t1324
            _t1325 = transactions_pb2.Read(export=export723)
            _t1323 = _t1325
        else:
            if prediction718 == 3:
                _t1327 = self.parse_abort()
                abort722 = _t1327
                _t1328 = transactions_pb2.Read(abort=abort722)
                _t1326 = _t1328
            else:
                if prediction718 == 2:
                    _t1330 = self.parse_what_if()
                    what_if721 = _t1330
                    _t1331 = transactions_pb2.Read(what_if=what_if721)
                    _t1329 = _t1331
                else:
                    if prediction718 == 1:
                        _t1333 = self.parse_output()
                        output720 = _t1333
                        _t1334 = transactions_pb2.Read(output=output720)
                        _t1332 = _t1334
                    else:
                        if prediction718 == 0:
                            _t1336 = self.parse_demand()
                            demand719 = _t1336
                            _t1337 = transactions_pb2.Read(demand=demand719)
                            _t1335 = _t1337
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1332 = _t1335
                    _t1329 = _t1332
                _t1326 = _t1329
            _t1323 = _t1326
        return _t1323

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1338 = self.parse_relation_id()
        relation_id724 = _t1338
        self.consume_literal(")")
        _t1339 = transactions_pb2.Demand(relation_id=relation_id724)
        return _t1339

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal("(")
        self.consume_literal("output")
        _t1340 = self.parse_name()
        name725 = _t1340
        _t1341 = self.parse_relation_id()
        relation_id726 = _t1341
        self.consume_literal(")")
        _t1342 = transactions_pb2.Output(name=name725, relation_id=relation_id726)
        return _t1342

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t1343 = self.parse_name()
        name727 = _t1343
        _t1344 = self.parse_epoch()
        epoch728 = _t1344
        self.consume_literal(")")
        _t1345 = transactions_pb2.WhatIf(branch=name727, epoch=epoch728)
        return _t1345

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t1347 = self.parse_name()
            _t1346 = _t1347
        else:
            _t1346 = None
        name729 = _t1346
        _t1348 = self.parse_relation_id()
        relation_id730 = _t1348
        self.consume_literal(")")
        _t1349 = transactions_pb2.Abort(name=(name729 if name729 is not None else "abort"), relation_id=relation_id730)
        return _t1349

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal("(")
        self.consume_literal("export")
        _t1350 = self.parse_export_csv_config()
        export_csv_config731 = _t1350
        self.consume_literal(")")
        _t1351 = transactions_pb2.Export(csv_config=export_csv_config731)
        return _t1351

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t1353 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t1354 = 1
                else:
                    _t1354 = -1
                _t1353 = _t1354
            _t1352 = _t1353
        else:
            _t1352 = -1
        prediction732 = _t1352
        if prediction732 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t1356 = self.parse_export_csv_path()
            export_csv_path736 = _t1356
            _t1357 = self.parse_export_csv_columns_list()
            export_csv_columns_list737 = _t1357
            _t1358 = self.parse_config_dict()
            config_dict738 = _t1358
            self.consume_literal(")")
            _t1359 = self.construct_export_csv_config(export_csv_path736, export_csv_columns_list737, config_dict738)
            _t1355 = _t1359
        else:
            if prediction732 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t1361 = self.parse_export_csv_path()
                export_csv_path733 = _t1361
                _t1362 = self.parse_export_csv_source()
                export_csv_source734 = _t1362
                _t1363 = self.parse_csv_config()
                csv_config735 = _t1363
                self.consume_literal(")")
                _t1364 = self.construct_export_csv_config_with_source(export_csv_path733, export_csv_source734, csv_config735)
                _t1360 = _t1364
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1355 = _t1360
        return _t1355

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string739 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string739

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t1366 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t1367 = 0
                else:
                    _t1367 = -1
                _t1366 = _t1367
            _t1365 = _t1366
        else:
            _t1365 = -1
        prediction740 = _t1365
        if prediction740 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t1369 = self.parse_relation_id()
            relation_id745 = _t1369
            self.consume_literal(")")
            _t1370 = transactions_pb2.ExportCSVSource(table_def=relation_id745)
            _t1368 = _t1370
        else:
            if prediction740 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs741 = []
                cond742 = self.match_lookahead_literal("(", 0)
                while cond742:
                    _t1372 = self.parse_export_csv_column()
                    item743 = _t1372
                    xs741.append(item743)
                    cond742 = self.match_lookahead_literal("(", 0)
                export_csv_columns744 = xs741
                self.consume_literal(")")
                _t1373 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns744)
                _t1374 = transactions_pb2.ExportCSVSource(gnf_columns=_t1373)
                _t1371 = _t1374
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1368 = _t1371
        return _t1368

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal("(")
        self.consume_literal("column")
        string746 = self.consume_terminal("STRING")
        _t1375 = self.parse_relation_id()
        relation_id747 = _t1375
        self.consume_literal(")")
        _t1376 = transactions_pb2.ExportCSVColumn(column_name=string746, column_data=relation_id747)
        return _t1376

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs748 = []
        cond749 = self.match_lookahead_literal("(", 0)
        while cond749:
            _t1377 = self.parse_export_csv_column()
            item750 = _t1377
            xs748.append(item750)
            cond749 = self.match_lookahead_literal("(", 0)
        export_csv_columns751 = xs748
        self.consume_literal(")")
        return export_csv_columns751


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
