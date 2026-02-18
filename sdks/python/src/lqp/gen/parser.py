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
            _t1298 = value.HasField("int_value")
        else:
            _t1298 = False
        if _t1298:
            assert value is not None
            return int(value.int_value)
        else:
            _t1299 = None
        return int(default)

    def _extract_value_int64(self, value: Optional[logic_pb2.Value], default: int) -> int:
        if value is not None:
            assert value is not None
            _t1300 = value.HasField("int_value")
        else:
            _t1300 = False
        if _t1300:
            assert value is not None
            return value.int_value
        else:
            _t1301 = None
        return default

    def _extract_value_string(self, value: Optional[logic_pb2.Value], default: str) -> str:
        if value is not None:
            assert value is not None
            _t1302 = value.HasField("string_value")
        else:
            _t1302 = False
        if _t1302:
            assert value is not None
            return value.string_value
        else:
            _t1303 = None
        return default

    def _extract_value_boolean(self, value: Optional[logic_pb2.Value], default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t1304 = value.HasField("boolean_value")
        else:
            _t1304 = False
        if _t1304:
            assert value is not None
            return value.boolean_value
        else:
            _t1305 = None
        return default

    def _extract_value_string_list(self, value: Optional[logic_pb2.Value], default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t1306 = value.HasField("string_value")
        else:
            _t1306 = False
        if _t1306:
            assert value is not None
            return [value.string_value]
        else:
            _t1307 = None
        return default

    def _try_extract_value_int64(self, value: Optional[logic_pb2.Value]) -> Optional[int]:
        if value is not None:
            assert value is not None
            _t1308 = value.HasField("int_value")
        else:
            _t1308 = False
        if _t1308:
            assert value is not None
            return value.int_value
        else:
            _t1309 = None
        return None

    def _try_extract_value_float64(self, value: Optional[logic_pb2.Value]) -> Optional[float]:
        if value is not None:
            assert value is not None
            _t1310 = value.HasField("float_value")
        else:
            _t1310 = False
        if _t1310:
            assert value is not None
            return value.float_value
        else:
            _t1311 = None
        return None

    def _try_extract_value_bytes(self, value: Optional[logic_pb2.Value]) -> Optional[bytes]:
        if value is not None:
            assert value is not None
            _t1312 = value.HasField("string_value")
        else:
            _t1312 = False
        if _t1312:
            assert value is not None
            return value.string_value.encode()
        else:
            _t1313 = None
        return None

    def _try_extract_value_uint128(self, value: Optional[logic_pb2.Value]) -> Optional[logic_pb2.UInt128Value]:
        if value is not None:
            assert value is not None
            _t1314 = value.HasField("uint128_value")
        else:
            _t1314 = False
        if _t1314:
            assert value is not None
            return value.uint128_value
        else:
            _t1315 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1316 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t1316
        _t1317 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t1317
        _t1318 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t1318
        _t1319 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t1319
        _t1320 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t1320
        _t1321 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t1321
        _t1322 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t1322
        _t1323 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t1323
        _t1324 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t1324
        _t1325 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t1325
        _t1326 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t1326
        _t1327 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t1327

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1328 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t1328
        _t1329 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t1329
        _t1330 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t1330
        _t1331 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t1331
        _t1332 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1332
        _t1333 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t1333
        _t1334 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t1334
        _t1335 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t1335
        _t1336 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t1336
        _t1337 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1337
        _t1338 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1338

    def default_configure(self) -> transactions_pb2.Configure:
        _t1339 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1339
        _t1340 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1340

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
        _t1341 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1341
        _t1342 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t1342
        _t1343 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1343

    def export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1344 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t1344
        _t1345 = self._extract_value_string(config.get("compression"), "")
        compression = _t1345
        _t1346 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t1346
        _t1347 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t1347
        _t1348 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t1348
        _t1349 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t1349
        _t1350 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t1350
        _t1351 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1351

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t707 = self.parse_configure()
            _t706 = _t707
        else:
            _t706 = None
        configure353 = _t706
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t709 = self.parse_sync()
            _t708 = _t709
        else:
            _t708 = None
        sync354 = _t708
        xs355 = []
        cond356 = self.match_lookahead_literal("(", 0)
        while cond356:
            _t710 = self.parse_epoch()
            item357 = _t710
            xs355.append(item357)
            cond356 = self.match_lookahead_literal("(", 0)
        epochs358 = xs355
        self.consume_literal(")")
        _t711 = self.default_configure()
        _t712 = transactions_pb2.Transaction(epochs=epochs358, configure=(configure353 if configure353 is not None else _t711), sync=sync354)
        return _t712

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal("(")
        self.consume_literal("configure")
        _t713 = self.parse_config_dict()
        config_dict359 = _t713
        self.consume_literal(")")
        _t714 = self.construct_configure(config_dict359)
        return _t714

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs360 = []
        cond361 = self.match_lookahead_literal(":", 0)
        while cond361:
            _t715 = self.parse_config_key_value()
            item362 = _t715
            xs360.append(item362)
            cond361 = self.match_lookahead_literal(":", 0)
        config_key_values363 = xs360
        self.consume_literal("}")
        return config_key_values363

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol364 = self.consume_terminal("SYMBOL")
        _t716 = self.parse_value()
        value365 = _t716
        return (symbol364, value365,)

    def parse_value(self) -> logic_pb2.Value:
        if self.match_lookahead_literal("true", 0):
            _t717 = 9
        else:
            if self.match_lookahead_literal("missing", 0):
                _t718 = 8
            else:
                if self.match_lookahead_literal("false", 0):
                    _t719 = 9
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t721 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t722 = 0
                            else:
                                _t722 = -1
                            _t721 = _t722
                        _t720 = _t721
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t723 = 5
                        else:
                            if self.match_lookahead_terminal("STRING", 0):
                                _t724 = 2
                            else:
                                if self.match_lookahead_terminal("INT128", 0):
                                    _t725 = 6
                                else:
                                    if self.match_lookahead_terminal("INT", 0):
                                        _t726 = 3
                                    else:
                                        if self.match_lookahead_terminal("FLOAT", 0):
                                            _t727 = 4
                                        else:
                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                _t728 = 7
                                            else:
                                                _t728 = -1
                                            _t727 = _t728
                                        _t726 = _t727
                                    _t725 = _t726
                                _t724 = _t725
                            _t723 = _t724
                        _t720 = _t723
                    _t719 = _t720
                _t718 = _t719
            _t717 = _t718
        prediction366 = _t717
        if prediction366 == 9:
            _t730 = self.parse_boolean_value()
            boolean_value375 = _t730
            _t731 = logic_pb2.Value(boolean_value=boolean_value375)
            _t729 = _t731
        else:
            if prediction366 == 8:
                self.consume_literal("missing")
                _t733 = logic_pb2.MissingValue()
                _t734 = logic_pb2.Value(missing_value=_t733)
                _t732 = _t734
            else:
                if prediction366 == 7:
                    decimal374 = self.consume_terminal("DECIMAL")
                    _t736 = logic_pb2.Value(decimal_value=decimal374)
                    _t735 = _t736
                else:
                    if prediction366 == 6:
                        int128373 = self.consume_terminal("INT128")
                        _t738 = logic_pb2.Value(int128_value=int128373)
                        _t737 = _t738
                    else:
                        if prediction366 == 5:
                            uint128372 = self.consume_terminal("UINT128")
                            _t740 = logic_pb2.Value(uint128_value=uint128372)
                            _t739 = _t740
                        else:
                            if prediction366 == 4:
                                float371 = self.consume_terminal("FLOAT")
                                _t742 = logic_pb2.Value(float_value=float371)
                                _t741 = _t742
                            else:
                                if prediction366 == 3:
                                    int370 = self.consume_terminal("INT")
                                    _t744 = logic_pb2.Value(int_value=int370)
                                    _t743 = _t744
                                else:
                                    if prediction366 == 2:
                                        string369 = self.consume_terminal("STRING")
                                        _t746 = logic_pb2.Value(string_value=string369)
                                        _t745 = _t746
                                    else:
                                        if prediction366 == 1:
                                            _t748 = self.parse_datetime()
                                            datetime368 = _t748
                                            _t749 = logic_pb2.Value(datetime_value=datetime368)
                                            _t747 = _t749
                                        else:
                                            if prediction366 == 0:
                                                _t751 = self.parse_date()
                                                date367 = _t751
                                                _t752 = logic_pb2.Value(date_value=date367)
                                                _t750 = _t752
                                            else:
                                                raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t747 = _t750
                                        _t745 = _t747
                                    _t743 = _t745
                                _t741 = _t743
                            _t739 = _t741
                        _t737 = _t739
                    _t735 = _t737
                _t732 = _t735
            _t729 = _t732
        return _t729

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal("(")
        self.consume_literal("date")
        int376 = self.consume_terminal("INT")
        int_3377 = self.consume_terminal("INT")
        int_4378 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t753 = logic_pb2.DateValue(year=int(int376), month=int(int_3377), day=int(int_4378))
        return _t753

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        self.consume_literal("(")
        self.consume_literal("datetime")
        int379 = self.consume_terminal("INT")
        int_3380 = self.consume_terminal("INT")
        int_4381 = self.consume_terminal("INT")
        int_5382 = self.consume_terminal("INT")
        int_6383 = self.consume_terminal("INT")
        int_7384 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t754 = self.consume_terminal("INT")
        else:
            _t754 = None
        int_8385 = _t754
        self.consume_literal(")")
        _t755 = logic_pb2.DateTimeValue(year=int(int379), month=int(int_3380), day=int(int_4381), hour=int(int_5382), minute=int(int_6383), second=int(int_7384), microsecond=int((int_8385 if int_8385 is not None else 0)))
        return _t755

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t756 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t757 = 1
            else:
                _t757 = -1
            _t756 = _t757
        prediction386 = _t756
        if prediction386 == 1:
            self.consume_literal("false")
            _t758 = False
        else:
            if prediction386 == 0:
                self.consume_literal("true")
                _t759 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t758 = _t759
        return _t758

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal("(")
        self.consume_literal("sync")
        xs387 = []
        cond388 = self.match_lookahead_literal(":", 0)
        while cond388:
            _t760 = self.parse_fragment_id()
            item389 = _t760
            xs387.append(item389)
            cond388 = self.match_lookahead_literal(":", 0)
        fragment_ids390 = xs387
        self.consume_literal(")")
        _t761 = transactions_pb2.Sync(fragments=fragment_ids390)
        return _t761

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        self.consume_literal(":")
        symbol391 = self.consume_terminal("SYMBOL")
        return fragments_pb2.FragmentId(id=symbol391.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t763 = self.parse_epoch_writes()
            _t762 = _t763
        else:
            _t762 = None
        epoch_writes392 = _t762
        if self.match_lookahead_literal("(", 0):
            _t765 = self.parse_epoch_reads()
            _t764 = _t765
        else:
            _t764 = None
        epoch_reads393 = _t764
        self.consume_literal(")")
        _t766 = transactions_pb2.Epoch(writes=(epoch_writes392 if epoch_writes392 is not None else []), reads=(epoch_reads393 if epoch_reads393 is not None else []))
        return _t766

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs394 = []
        cond395 = self.match_lookahead_literal("(", 0)
        while cond395:
            _t767 = self.parse_write()
            item396 = _t767
            xs394.append(item396)
            cond395 = self.match_lookahead_literal("(", 0)
        writes397 = xs394
        self.consume_literal(")")
        return writes397

    def parse_write(self) -> transactions_pb2.Write:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t769 = 1
            else:
                if self.match_lookahead_literal("define", 1):
                    _t770 = 0
                else:
                    if self.match_lookahead_literal("context", 1):
                        _t771 = 2
                    else:
                        _t771 = -1
                    _t770 = _t771
                _t769 = _t770
            _t768 = _t769
        else:
            _t768 = -1
        prediction398 = _t768
        if prediction398 == 2:
            _t773 = self.parse_context()
            context401 = _t773
            _t774 = transactions_pb2.Write(context=context401)
            _t772 = _t774
        else:
            if prediction398 == 1:
                _t776 = self.parse_undefine()
                undefine400 = _t776
                _t777 = transactions_pb2.Write(undefine=undefine400)
                _t775 = _t777
            else:
                if prediction398 == 0:
                    _t779 = self.parse_define()
                    define399 = _t779
                    _t780 = transactions_pb2.Write(define=define399)
                    _t778 = _t780
                else:
                    raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t775 = _t778
            _t772 = _t775
        return _t772

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal("(")
        self.consume_literal("define")
        _t781 = self.parse_fragment()
        fragment402 = _t781
        self.consume_literal(")")
        _t782 = transactions_pb2.Define(fragment=fragment402)
        return _t782

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t783 = self.parse_new_fragment_id()
        new_fragment_id403 = _t783
        xs404 = []
        cond405 = self.match_lookahead_literal("(", 0)
        while cond405:
            _t784 = self.parse_declaration()
            item406 = _t784
            xs404.append(item406)
            cond405 = self.match_lookahead_literal("(", 0)
        declarations407 = xs404
        self.consume_literal(")")
        return self.construct_fragment(new_fragment_id403, declarations407)

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        _t785 = self.parse_fragment_id()
        fragment_id408 = _t785
        self.start_fragment(fragment_id408)
        return fragment_id408

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("rel_edb", 1):
                _t787 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t788 = 2
                else:
                    if self.match_lookahead_literal("def", 1):
                        _t789 = 0
                    else:
                        if self.match_lookahead_literal("csv_data", 1):
                            _t790 = 3
                        else:
                            if self.match_lookahead_literal("betree_relation", 1):
                                _t791 = 3
                            else:
                                if self.match_lookahead_literal("algorithm", 1):
                                    _t792 = 1
                                else:
                                    _t792 = -1
                                _t791 = _t792
                            _t790 = _t791
                        _t789 = _t790
                    _t788 = _t789
                _t787 = _t788
            _t786 = _t787
        else:
            _t786 = -1
        prediction409 = _t786
        if prediction409 == 3:
            _t794 = self.parse_data()
            data413 = _t794
            _t795 = logic_pb2.Declaration(data=data413)
            _t793 = _t795
        else:
            if prediction409 == 2:
                _t797 = self.parse_constraint()
                constraint412 = _t797
                _t798 = logic_pb2.Declaration(constraint=constraint412)
                _t796 = _t798
            else:
                if prediction409 == 1:
                    _t800 = self.parse_algorithm()
                    algorithm411 = _t800
                    _t801 = logic_pb2.Declaration(algorithm=algorithm411)
                    _t799 = _t801
                else:
                    if prediction409 == 0:
                        _t803 = self.parse_def()
                        def410 = _t803
                        _t804 = logic_pb2.Declaration()
                        getattr(_t804, 'def').CopyFrom(def410)
                        _t802 = _t804
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t799 = _t802
                _t796 = _t799
            _t793 = _t796
        return _t793

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal("(")
        self.consume_literal("def")
        _t805 = self.parse_relation_id()
        relation_id414 = _t805
        _t806 = self.parse_abstraction()
        abstraction415 = _t806
        if self.match_lookahead_literal("(", 0):
            _t808 = self.parse_attrs()
            _t807 = _t808
        else:
            _t807 = None
        attrs416 = _t807
        self.consume_literal(")")
        _t809 = logic_pb2.Def(name=relation_id414, body=abstraction415, attrs=(attrs416 if attrs416 is not None else []))
        return _t809

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_literal(":", 0):
            _t810 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t811 = 1
            else:
                _t811 = -1
            _t810 = _t811
        prediction417 = _t810
        if prediction417 == 1:
            uint128419 = self.consume_terminal("UINT128")
            _t812 = logic_pb2.RelationId(id_low=uint128419.low, id_high=uint128419.high)
        else:
            if prediction417 == 0:
                self.consume_literal(":")
                symbol418 = self.consume_terminal("SYMBOL")
                _t813 = self.relation_id_from_string(symbol418)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t812 = _t813
        return _t812

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal("(")
        _t814 = self.parse_bindings()
        bindings420 = _t814
        _t815 = self.parse_formula()
        formula421 = _t815
        self.consume_literal(")")
        _t816 = logic_pb2.Abstraction(vars=(list(bindings420[0]) + list(bindings420[1] if bindings420[1] is not None else [])), value=formula421)
        return _t816

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs422 = []
        cond423 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond423:
            _t817 = self.parse_binding()
            item424 = _t817
            xs422.append(item424)
            cond423 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings425 = xs422
        if self.match_lookahead_literal("|", 0):
            _t819 = self.parse_value_bindings()
            _t818 = _t819
        else:
            _t818 = None
        value_bindings426 = _t818
        self.consume_literal("]")
        return (bindings425, (value_bindings426 if value_bindings426 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol427 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t820 = self.parse_type()
        type428 = _t820
        _t821 = logic_pb2.Var(name=symbol427)
        _t822 = logic_pb2.Binding(var=_t821, type=type428)
        return _t822

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t823 = 0
        else:
            if self.match_lookahead_literal("UINT128", 0):
                _t824 = 4
            else:
                if self.match_lookahead_literal("STRING", 0):
                    _t825 = 1
                else:
                    if self.match_lookahead_literal("MISSING", 0):
                        _t826 = 8
                    else:
                        if self.match_lookahead_literal("INT128", 0):
                            _t827 = 5
                        else:
                            if self.match_lookahead_literal("INT", 0):
                                _t828 = 2
                            else:
                                if self.match_lookahead_literal("FLOAT", 0):
                                    _t829 = 3
                                else:
                                    if self.match_lookahead_literal("DATETIME", 0):
                                        _t830 = 7
                                    else:
                                        if self.match_lookahead_literal("DATE", 0):
                                            _t831 = 6
                                        else:
                                            if self.match_lookahead_literal("BOOLEAN", 0):
                                                _t832 = 10
                                            else:
                                                if self.match_lookahead_literal("(", 0):
                                                    _t833 = 9
                                                else:
                                                    _t833 = -1
                                                _t832 = _t833
                                            _t831 = _t832
                                        _t830 = _t831
                                    _t829 = _t830
                                _t828 = _t829
                            _t827 = _t828
                        _t826 = _t827
                    _t825 = _t826
                _t824 = _t825
            _t823 = _t824
        prediction429 = _t823
        if prediction429 == 10:
            _t835 = self.parse_boolean_type()
            boolean_type440 = _t835
            _t836 = logic_pb2.Type(boolean_type=boolean_type440)
            _t834 = _t836
        else:
            if prediction429 == 9:
                _t838 = self.parse_decimal_type()
                decimal_type439 = _t838
                _t839 = logic_pb2.Type(decimal_type=decimal_type439)
                _t837 = _t839
            else:
                if prediction429 == 8:
                    _t841 = self.parse_missing_type()
                    missing_type438 = _t841
                    _t842 = logic_pb2.Type(missing_type=missing_type438)
                    _t840 = _t842
                else:
                    if prediction429 == 7:
                        _t844 = self.parse_datetime_type()
                        datetime_type437 = _t844
                        _t845 = logic_pb2.Type(datetime_type=datetime_type437)
                        _t843 = _t845
                    else:
                        if prediction429 == 6:
                            _t847 = self.parse_date_type()
                            date_type436 = _t847
                            _t848 = logic_pb2.Type(date_type=date_type436)
                            _t846 = _t848
                        else:
                            if prediction429 == 5:
                                _t850 = self.parse_int128_type()
                                int128_type435 = _t850
                                _t851 = logic_pb2.Type(int128_type=int128_type435)
                                _t849 = _t851
                            else:
                                if prediction429 == 4:
                                    _t853 = self.parse_uint128_type()
                                    uint128_type434 = _t853
                                    _t854 = logic_pb2.Type(uint128_type=uint128_type434)
                                    _t852 = _t854
                                else:
                                    if prediction429 == 3:
                                        _t856 = self.parse_float_type()
                                        float_type433 = _t856
                                        _t857 = logic_pb2.Type(float_type=float_type433)
                                        _t855 = _t857
                                    else:
                                        if prediction429 == 2:
                                            _t859 = self.parse_int_type()
                                            int_type432 = _t859
                                            _t860 = logic_pb2.Type(int_type=int_type432)
                                            _t858 = _t860
                                        else:
                                            if prediction429 == 1:
                                                _t862 = self.parse_string_type()
                                                string_type431 = _t862
                                                _t863 = logic_pb2.Type(string_type=string_type431)
                                                _t861 = _t863
                                            else:
                                                if prediction429 == 0:
                                                    _t865 = self.parse_unspecified_type()
                                                    unspecified_type430 = _t865
                                                    _t866 = logic_pb2.Type(unspecified_type=unspecified_type430)
                                                    _t864 = _t866
                                                else:
                                                    raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t861 = _t864
                                            _t858 = _t861
                                        _t855 = _t858
                                    _t852 = _t855
                                _t849 = _t852
                            _t846 = _t849
                        _t843 = _t846
                    _t840 = _t843
                _t837 = _t840
            _t834 = _t837
        return _t834

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        self.consume_literal("UNKNOWN")
        _t867 = logic_pb2.UnspecifiedType()
        return _t867

    def parse_string_type(self) -> logic_pb2.StringType:
        self.consume_literal("STRING")
        _t868 = logic_pb2.StringType()
        return _t868

    def parse_int_type(self) -> logic_pb2.IntType:
        self.consume_literal("INT")
        _t869 = logic_pb2.IntType()
        return _t869

    def parse_float_type(self) -> logic_pb2.FloatType:
        self.consume_literal("FLOAT")
        _t870 = logic_pb2.FloatType()
        return _t870

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        self.consume_literal("UINT128")
        _t871 = logic_pb2.UInt128Type()
        return _t871

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        self.consume_literal("INT128")
        _t872 = logic_pb2.Int128Type()
        return _t872

    def parse_date_type(self) -> logic_pb2.DateType:
        self.consume_literal("DATE")
        _t873 = logic_pb2.DateType()
        return _t873

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        self.consume_literal("DATETIME")
        _t874 = logic_pb2.DateTimeType()
        return _t874

    def parse_missing_type(self) -> logic_pb2.MissingType:
        self.consume_literal("MISSING")
        _t875 = logic_pb2.MissingType()
        return _t875

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int441 = self.consume_terminal("INT")
        int_3442 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t876 = logic_pb2.DecimalType(precision=int(int441), scale=int(int_3442))
        return _t876

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal("BOOLEAN")
        _t877 = logic_pb2.BooleanType()
        return _t877

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs443 = []
        cond444 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond444:
            _t878 = self.parse_binding()
            item445 = _t878
            xs443.append(item445)
            cond444 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings446 = xs443
        return bindings446

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t880 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t881 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t882 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t883 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t884 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t885 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t886 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t887 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t888 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t889 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t890 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t891 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t892 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t893 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t894 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t895 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t896 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t897 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t898 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t899 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t900 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t901 = 10
                                                                                                else:
                                                                                                    _t901 = -1
                                                                                                _t900 = _t901
                                                                                            _t899 = _t900
                                                                                        _t898 = _t899
                                                                                    _t897 = _t898
                                                                                _t896 = _t897
                                                                            _t895 = _t896
                                                                        _t894 = _t895
                                                                    _t893 = _t894
                                                                _t892 = _t893
                                                            _t891 = _t892
                                                        _t890 = _t891
                                                    _t889 = _t890
                                                _t888 = _t889
                                            _t887 = _t888
                                        _t886 = _t887
                                    _t885 = _t886
                                _t884 = _t885
                            _t883 = _t884
                        _t882 = _t883
                    _t881 = _t882
                _t880 = _t881
            _t879 = _t880
        else:
            _t879 = -1
        prediction447 = _t879
        if prediction447 == 12:
            _t903 = self.parse_cast()
            cast460 = _t903
            _t904 = logic_pb2.Formula(cast=cast460)
            _t902 = _t904
        else:
            if prediction447 == 11:
                _t906 = self.parse_rel_atom()
                rel_atom459 = _t906
                _t907 = logic_pb2.Formula(rel_atom=rel_atom459)
                _t905 = _t907
            else:
                if prediction447 == 10:
                    _t909 = self.parse_primitive()
                    primitive458 = _t909
                    _t910 = logic_pb2.Formula(primitive=primitive458)
                    _t908 = _t910
                else:
                    if prediction447 == 9:
                        _t912 = self.parse_pragma()
                        pragma457 = _t912
                        _t913 = logic_pb2.Formula(pragma=pragma457)
                        _t911 = _t913
                    else:
                        if prediction447 == 8:
                            _t915 = self.parse_atom()
                            atom456 = _t915
                            _t916 = logic_pb2.Formula(atom=atom456)
                            _t914 = _t916
                        else:
                            if prediction447 == 7:
                                _t918 = self.parse_ffi()
                                ffi455 = _t918
                                _t919 = logic_pb2.Formula(ffi=ffi455)
                                _t917 = _t919
                            else:
                                if prediction447 == 6:
                                    _t921 = self.parse_not()
                                    not454 = _t921
                                    _t922 = logic_pb2.Formula()
                                    getattr(_t922, 'not').CopyFrom(not454)
                                    _t920 = _t922
                                else:
                                    if prediction447 == 5:
                                        _t924 = self.parse_disjunction()
                                        disjunction453 = _t924
                                        _t925 = logic_pb2.Formula(disjunction=disjunction453)
                                        _t923 = _t925
                                    else:
                                        if prediction447 == 4:
                                            _t927 = self.parse_conjunction()
                                            conjunction452 = _t927
                                            _t928 = logic_pb2.Formula(conjunction=conjunction452)
                                            _t926 = _t928
                                        else:
                                            if prediction447 == 3:
                                                _t930 = self.parse_reduce()
                                                reduce451 = _t930
                                                _t931 = logic_pb2.Formula(reduce=reduce451)
                                                _t929 = _t931
                                            else:
                                                if prediction447 == 2:
                                                    _t933 = self.parse_exists()
                                                    exists450 = _t933
                                                    _t934 = logic_pb2.Formula(exists=exists450)
                                                    _t932 = _t934
                                                else:
                                                    if prediction447 == 1:
                                                        _t936 = self.parse_false()
                                                        false449 = _t936
                                                        _t937 = logic_pb2.Formula(disjunction=false449)
                                                        _t935 = _t937
                                                    else:
                                                        if prediction447 == 0:
                                                            _t939 = self.parse_true()
                                                            true448 = _t939
                                                            _t940 = logic_pb2.Formula(conjunction=true448)
                                                            _t938 = _t940
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t935 = _t938
                                                    _t932 = _t935
                                                _t929 = _t932
                                            _t926 = _t929
                                        _t923 = _t926
                                    _t920 = _t923
                                _t917 = _t920
                            _t914 = _t917
                        _t911 = _t914
                    _t908 = _t911
                _t905 = _t908
            _t902 = _t905
        return _t902

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t941 = logic_pb2.Conjunction(args=[])
        return _t941

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t942 = logic_pb2.Disjunction(args=[])
        return _t942

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal("(")
        self.consume_literal("exists")
        _t943 = self.parse_bindings()
        bindings461 = _t943
        _t944 = self.parse_formula()
        formula462 = _t944
        self.consume_literal(")")
        _t945 = logic_pb2.Abstraction(vars=(list(bindings461[0]) + list(bindings461[1] if bindings461[1] is not None else [])), value=formula462)
        _t946 = logic_pb2.Exists(body=_t945)
        return _t946

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t947 = self.parse_abstraction()
        abstraction463 = _t947
        _t948 = self.parse_abstraction()
        abstraction_3464 = _t948
        _t949 = self.parse_terms()
        terms465 = _t949
        self.consume_literal(")")
        _t950 = logic_pb2.Reduce(op=abstraction463, body=abstraction_3464, terms=terms465)
        return _t950

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs466 = []
        cond467 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond467:
            _t951 = self.parse_term()
            item468 = _t951
            xs466.append(item468)
            cond467 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms469 = xs466
        self.consume_literal(")")
        return terms469

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_literal("true", 0):
            _t952 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t953 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t954 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t955 = 1
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t956 = 1
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t957 = 0
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t958 = 1
                                else:
                                    if self.match_lookahead_terminal("INT128", 0):
                                        _t959 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT", 0):
                                            _t960 = 1
                                        else:
                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                _t961 = 1
                                            else:
                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                    _t962 = 1
                                                else:
                                                    _t962 = -1
                                                _t961 = _t962
                                            _t960 = _t961
                                        _t959 = _t960
                                    _t958 = _t959
                                _t957 = _t958
                            _t956 = _t957
                        _t955 = _t956
                    _t954 = _t955
                _t953 = _t954
            _t952 = _t953
        prediction470 = _t952
        if prediction470 == 1:
            _t964 = self.parse_constant()
            constant472 = _t964
            _t965 = logic_pb2.Term(constant=constant472)
            _t963 = _t965
        else:
            if prediction470 == 0:
                _t967 = self.parse_var()
                var471 = _t967
                _t968 = logic_pb2.Term(var=var471)
                _t966 = _t968
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t963 = _t966
        return _t963

    def parse_var(self) -> logic_pb2.Var:
        symbol473 = self.consume_terminal("SYMBOL")
        _t969 = logic_pb2.Var(name=symbol473)
        return _t969

    def parse_constant(self) -> logic_pb2.Value:
        _t970 = self.parse_value()
        value474 = _t970
        return value474

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal("(")
        self.consume_literal("and")
        xs475 = []
        cond476 = self.match_lookahead_literal("(", 0)
        while cond476:
            _t971 = self.parse_formula()
            item477 = _t971
            xs475.append(item477)
            cond476 = self.match_lookahead_literal("(", 0)
        formulas478 = xs475
        self.consume_literal(")")
        _t972 = logic_pb2.Conjunction(args=formulas478)
        return _t972

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal("(")
        self.consume_literal("or")
        xs479 = []
        cond480 = self.match_lookahead_literal("(", 0)
        while cond480:
            _t973 = self.parse_formula()
            item481 = _t973
            xs479.append(item481)
            cond480 = self.match_lookahead_literal("(", 0)
        formulas482 = xs479
        self.consume_literal(")")
        _t974 = logic_pb2.Disjunction(args=formulas482)
        return _t974

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal("(")
        self.consume_literal("not")
        _t975 = self.parse_formula()
        formula483 = _t975
        self.consume_literal(")")
        _t976 = logic_pb2.Not(arg=formula483)
        return _t976

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t977 = self.parse_name()
        name484 = _t977
        _t978 = self.parse_ffi_args()
        ffi_args485 = _t978
        _t979 = self.parse_terms()
        terms486 = _t979
        self.consume_literal(")")
        _t980 = logic_pb2.FFI(name=name484, args=ffi_args485, terms=terms486)
        return _t980

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol487 = self.consume_terminal("SYMBOL")
        return symbol487

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs488 = []
        cond489 = self.match_lookahead_literal("(", 0)
        while cond489:
            _t981 = self.parse_abstraction()
            item490 = _t981
            xs488.append(item490)
            cond489 = self.match_lookahead_literal("(", 0)
        abstractions491 = xs488
        self.consume_literal(")")
        return abstractions491

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal("(")
        self.consume_literal("atom")
        _t982 = self.parse_relation_id()
        relation_id492 = _t982
        xs493 = []
        cond494 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond494:
            _t983 = self.parse_term()
            item495 = _t983
            xs493.append(item495)
            cond494 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms496 = xs493
        self.consume_literal(")")
        _t984 = logic_pb2.Atom(name=relation_id492, terms=terms496)
        return _t984

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t985 = self.parse_name()
        name497 = _t985
        xs498 = []
        cond499 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond499:
            _t986 = self.parse_term()
            item500 = _t986
            xs498.append(item500)
            cond499 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms501 = xs498
        self.consume_literal(")")
        _t987 = logic_pb2.Pragma(name=name497, terms=terms501)
        return _t987

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t989 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t990 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t991 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t992 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t993 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t994 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t995 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t996 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t997 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t998 = 7
                                                else:
                                                    _t998 = -1
                                                _t997 = _t998
                                            _t996 = _t997
                                        _t995 = _t996
                                    _t994 = _t995
                                _t993 = _t994
                            _t992 = _t993
                        _t991 = _t992
                    _t990 = _t991
                _t989 = _t990
            _t988 = _t989
        else:
            _t988 = -1
        prediction502 = _t988
        if prediction502 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1000 = self.parse_name()
            name512 = _t1000
            xs513 = []
            cond514 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            while cond514:
                _t1001 = self.parse_rel_term()
                item515 = _t1001
                xs513.append(item515)
                cond514 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            rel_terms516 = xs513
            self.consume_literal(")")
            _t1002 = logic_pb2.Primitive(name=name512, terms=rel_terms516)
            _t999 = _t1002
        else:
            if prediction502 == 8:
                _t1004 = self.parse_divide()
                divide511 = _t1004
                _t1003 = divide511
            else:
                if prediction502 == 7:
                    _t1006 = self.parse_multiply()
                    multiply510 = _t1006
                    _t1005 = multiply510
                else:
                    if prediction502 == 6:
                        _t1008 = self.parse_minus()
                        minus509 = _t1008
                        _t1007 = minus509
                    else:
                        if prediction502 == 5:
                            _t1010 = self.parse_add()
                            add508 = _t1010
                            _t1009 = add508
                        else:
                            if prediction502 == 4:
                                _t1012 = self.parse_gt_eq()
                                gt_eq507 = _t1012
                                _t1011 = gt_eq507
                            else:
                                if prediction502 == 3:
                                    _t1014 = self.parse_gt()
                                    gt506 = _t1014
                                    _t1013 = gt506
                                else:
                                    if prediction502 == 2:
                                        _t1016 = self.parse_lt_eq()
                                        lt_eq505 = _t1016
                                        _t1015 = lt_eq505
                                    else:
                                        if prediction502 == 1:
                                            _t1018 = self.parse_lt()
                                            lt504 = _t1018
                                            _t1017 = lt504
                                        else:
                                            if prediction502 == 0:
                                                _t1020 = self.parse_eq()
                                                eq503 = _t1020
                                                _t1019 = eq503
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1017 = _t1019
                                        _t1015 = _t1017
                                    _t1013 = _t1015
                                _t1011 = _t1013
                            _t1009 = _t1011
                        _t1007 = _t1009
                    _t1005 = _t1007
                _t1003 = _t1005
            _t999 = _t1003
        return _t999

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("=")
        _t1021 = self.parse_term()
        term517 = _t1021
        _t1022 = self.parse_term()
        term_3518 = _t1022
        self.consume_literal(")")
        _t1023 = logic_pb2.RelTerm(term=term517)
        _t1024 = logic_pb2.RelTerm(term=term_3518)
        _t1025 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1023, _t1024])
        return _t1025

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("<")
        _t1026 = self.parse_term()
        term519 = _t1026
        _t1027 = self.parse_term()
        term_3520 = _t1027
        self.consume_literal(")")
        _t1028 = logic_pb2.RelTerm(term=term519)
        _t1029 = logic_pb2.RelTerm(term=term_3520)
        _t1030 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1028, _t1029])
        return _t1030

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1031 = self.parse_term()
        term521 = _t1031
        _t1032 = self.parse_term()
        term_3522 = _t1032
        self.consume_literal(")")
        _t1033 = logic_pb2.RelTerm(term=term521)
        _t1034 = logic_pb2.RelTerm(term=term_3522)
        _t1035 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1033, _t1034])
        return _t1035

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal(">")
        _t1036 = self.parse_term()
        term523 = _t1036
        _t1037 = self.parse_term()
        term_3524 = _t1037
        self.consume_literal(")")
        _t1038 = logic_pb2.RelTerm(term=term523)
        _t1039 = logic_pb2.RelTerm(term=term_3524)
        _t1040 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1038, _t1039])
        return _t1040

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1041 = self.parse_term()
        term525 = _t1041
        _t1042 = self.parse_term()
        term_3526 = _t1042
        self.consume_literal(")")
        _t1043 = logic_pb2.RelTerm(term=term525)
        _t1044 = logic_pb2.RelTerm(term=term_3526)
        _t1045 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1043, _t1044])
        return _t1045

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("+")
        _t1046 = self.parse_term()
        term527 = _t1046
        _t1047 = self.parse_term()
        term_3528 = _t1047
        _t1048 = self.parse_term()
        term_4529 = _t1048
        self.consume_literal(")")
        _t1049 = logic_pb2.RelTerm(term=term527)
        _t1050 = logic_pb2.RelTerm(term=term_3528)
        _t1051 = logic_pb2.RelTerm(term=term_4529)
        _t1052 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1049, _t1050, _t1051])
        return _t1052

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("-")
        _t1053 = self.parse_term()
        term530 = _t1053
        _t1054 = self.parse_term()
        term_3531 = _t1054
        _t1055 = self.parse_term()
        term_4532 = _t1055
        self.consume_literal(")")
        _t1056 = logic_pb2.RelTerm(term=term530)
        _t1057 = logic_pb2.RelTerm(term=term_3531)
        _t1058 = logic_pb2.RelTerm(term=term_4532)
        _t1059 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1056, _t1057, _t1058])
        return _t1059

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("*")
        _t1060 = self.parse_term()
        term533 = _t1060
        _t1061 = self.parse_term()
        term_3534 = _t1061
        _t1062 = self.parse_term()
        term_4535 = _t1062
        self.consume_literal(")")
        _t1063 = logic_pb2.RelTerm(term=term533)
        _t1064 = logic_pb2.RelTerm(term=term_3534)
        _t1065 = logic_pb2.RelTerm(term=term_4535)
        _t1066 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1063, _t1064, _t1065])
        return _t1066

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("/")
        _t1067 = self.parse_term()
        term536 = _t1067
        _t1068 = self.parse_term()
        term_3537 = _t1068
        _t1069 = self.parse_term()
        term_4538 = _t1069
        self.consume_literal(")")
        _t1070 = logic_pb2.RelTerm(term=term536)
        _t1071 = logic_pb2.RelTerm(term=term_3537)
        _t1072 = logic_pb2.RelTerm(term=term_4538)
        _t1073 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1070, _t1071, _t1072])
        return _t1073

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_literal("true", 0):
            _t1074 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1075 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1076 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1077 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1078 = 0
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1079 = 1
                            else:
                                if self.match_lookahead_terminal("SYMBOL", 0):
                                    _t1080 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1081 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1082 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1083 = 1
                                            else:
                                                if self.match_lookahead_terminal("FLOAT", 0):
                                                    _t1084 = 1
                                                else:
                                                    if self.match_lookahead_terminal("DECIMAL", 0):
                                                        _t1085 = 1
                                                    else:
                                                        _t1085 = -1
                                                    _t1084 = _t1085
                                                _t1083 = _t1084
                                            _t1082 = _t1083
                                        _t1081 = _t1082
                                    _t1080 = _t1081
                                _t1079 = _t1080
                            _t1078 = _t1079
                        _t1077 = _t1078
                    _t1076 = _t1077
                _t1075 = _t1076
            _t1074 = _t1075
        prediction539 = _t1074
        if prediction539 == 1:
            _t1087 = self.parse_term()
            term541 = _t1087
            _t1088 = logic_pb2.RelTerm(term=term541)
            _t1086 = _t1088
        else:
            if prediction539 == 0:
                _t1090 = self.parse_specialized_value()
                specialized_value540 = _t1090
                _t1091 = logic_pb2.RelTerm(specialized_value=specialized_value540)
                _t1089 = _t1091
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1086 = _t1089
        return _t1086

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal("#")
        _t1092 = self.parse_value()
        value542 = _t1092
        return value542

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1093 = self.parse_name()
        name543 = _t1093
        xs544 = []
        cond545 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond545:
            _t1094 = self.parse_rel_term()
            item546 = _t1094
            xs544.append(item546)
            cond545 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        rel_terms547 = xs544
        self.consume_literal(")")
        _t1095 = logic_pb2.RelAtom(name=name543, terms=rel_terms547)
        return _t1095

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1096 = self.parse_term()
        term548 = _t1096
        _t1097 = self.parse_term()
        term_3549 = _t1097
        self.consume_literal(")")
        _t1098 = logic_pb2.Cast(input=term548, result=term_3549)
        return _t1098

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs550 = []
        cond551 = self.match_lookahead_literal("(", 0)
        while cond551:
            _t1099 = self.parse_attribute()
            item552 = _t1099
            xs550.append(item552)
            cond551 = self.match_lookahead_literal("(", 0)
        attributes553 = xs550
        self.consume_literal(")")
        return attributes553

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1100 = self.parse_name()
        name554 = _t1100
        xs555 = []
        cond556 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond556:
            _t1101 = self.parse_value()
            item557 = _t1101
            xs555.append(item557)
            cond556 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        values558 = xs555
        self.consume_literal(")")
        _t1102 = logic_pb2.Attribute(name=name554, args=values558)
        return _t1102

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs559 = []
        cond560 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond560:
            _t1103 = self.parse_relation_id()
            item561 = _t1103
            xs559.append(item561)
            cond560 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids562 = xs559
        _t1104 = self.parse_script()
        script563 = _t1104
        self.consume_literal(")")
        _t1105 = logic_pb2.Algorithm(body=script563)
        getattr(_t1105, 'global').extend(relation_ids562)
        return _t1105

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal("(")
        self.consume_literal("script")
        xs564 = []
        cond565 = self.match_lookahead_literal("(", 0)
        while cond565:
            _t1106 = self.parse_construct()
            item566 = _t1106
            xs564.append(item566)
            cond565 = self.match_lookahead_literal("(", 0)
        constructs567 = xs564
        self.consume_literal(")")
        _t1107 = logic_pb2.Script(constructs=constructs567)
        return _t1107

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1109 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1110 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1111 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1112 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1113 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1114 = 1
                                else:
                                    _t1114 = -1
                                _t1113 = _t1114
                            _t1112 = _t1113
                        _t1111 = _t1112
                    _t1110 = _t1111
                _t1109 = _t1110
            _t1108 = _t1109
        else:
            _t1108 = -1
        prediction568 = _t1108
        if prediction568 == 1:
            _t1116 = self.parse_instruction()
            instruction570 = _t1116
            _t1117 = logic_pb2.Construct(instruction=instruction570)
            _t1115 = _t1117
        else:
            if prediction568 == 0:
                _t1119 = self.parse_loop()
                loop569 = _t1119
                _t1120 = logic_pb2.Construct(loop=loop569)
                _t1118 = _t1120
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1115 = _t1118
        return _t1115

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1121 = self.parse_init()
        init571 = _t1121
        _t1122 = self.parse_script()
        script572 = _t1122
        self.consume_literal(")")
        _t1123 = logic_pb2.Loop(init=init571, body=script572)
        return _t1123

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs573 = []
        cond574 = self.match_lookahead_literal("(", 0)
        while cond574:
            _t1124 = self.parse_instruction()
            item575 = _t1124
            xs573.append(item575)
            cond574 = self.match_lookahead_literal("(", 0)
        instructions576 = xs573
        self.consume_literal(")")
        return instructions576

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1126 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1127 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1128 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1129 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1130 = 0
                            else:
                                _t1130 = -1
                            _t1129 = _t1130
                        _t1128 = _t1129
                    _t1127 = _t1128
                _t1126 = _t1127
            _t1125 = _t1126
        else:
            _t1125 = -1
        prediction577 = _t1125
        if prediction577 == 4:
            _t1132 = self.parse_monus_def()
            monus_def582 = _t1132
            _t1133 = logic_pb2.Instruction(monus_def=monus_def582)
            _t1131 = _t1133
        else:
            if prediction577 == 3:
                _t1135 = self.parse_monoid_def()
                monoid_def581 = _t1135
                _t1136 = logic_pb2.Instruction(monoid_def=monoid_def581)
                _t1134 = _t1136
            else:
                if prediction577 == 2:
                    _t1138 = self.parse_break()
                    break580 = _t1138
                    _t1139 = logic_pb2.Instruction()
                    getattr(_t1139, 'break').CopyFrom(break580)
                    _t1137 = _t1139
                else:
                    if prediction577 == 1:
                        _t1141 = self.parse_upsert()
                        upsert579 = _t1141
                        _t1142 = logic_pb2.Instruction(upsert=upsert579)
                        _t1140 = _t1142
                    else:
                        if prediction577 == 0:
                            _t1144 = self.parse_assign()
                            assign578 = _t1144
                            _t1145 = logic_pb2.Instruction(assign=assign578)
                            _t1143 = _t1145
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1140 = _t1143
                    _t1137 = _t1140
                _t1134 = _t1137
            _t1131 = _t1134
        return _t1131

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1146 = self.parse_relation_id()
        relation_id583 = _t1146
        _t1147 = self.parse_abstraction()
        abstraction584 = _t1147
        if self.match_lookahead_literal("(", 0):
            _t1149 = self.parse_attrs()
            _t1148 = _t1149
        else:
            _t1148 = None
        attrs585 = _t1148
        self.consume_literal(")")
        _t1150 = logic_pb2.Assign(name=relation_id583, body=abstraction584, attrs=(attrs585 if attrs585 is not None else []))
        return _t1150

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1151 = self.parse_relation_id()
        relation_id586 = _t1151
        _t1152 = self.parse_abstraction_with_arity()
        abstraction_with_arity587 = _t1152
        if self.match_lookahead_literal("(", 0):
            _t1154 = self.parse_attrs()
            _t1153 = _t1154
        else:
            _t1153 = None
        attrs588 = _t1153
        self.consume_literal(")")
        _t1155 = logic_pb2.Upsert(name=relation_id586, body=abstraction_with_arity587[0], attrs=(attrs588 if attrs588 is not None else []), value_arity=abstraction_with_arity587[1])
        return _t1155

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1156 = self.parse_bindings()
        bindings589 = _t1156
        _t1157 = self.parse_formula()
        formula590 = _t1157
        self.consume_literal(")")
        _t1158 = logic_pb2.Abstraction(vars=(list(bindings589[0]) + list(bindings589[1] if bindings589[1] is not None else [])), value=formula590)
        return (_t1158, len(bindings589[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal("(")
        self.consume_literal("break")
        _t1159 = self.parse_relation_id()
        relation_id591 = _t1159
        _t1160 = self.parse_abstraction()
        abstraction592 = _t1160
        if self.match_lookahead_literal("(", 0):
            _t1162 = self.parse_attrs()
            _t1161 = _t1162
        else:
            _t1161 = None
        attrs593 = _t1161
        self.consume_literal(")")
        _t1163 = logic_pb2.Break(name=relation_id591, body=abstraction592, attrs=(attrs593 if attrs593 is not None else []))
        return _t1163

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1164 = self.parse_monoid()
        monoid594 = _t1164
        _t1165 = self.parse_relation_id()
        relation_id595 = _t1165
        _t1166 = self.parse_abstraction_with_arity()
        abstraction_with_arity596 = _t1166
        if self.match_lookahead_literal("(", 0):
            _t1168 = self.parse_attrs()
            _t1167 = _t1168
        else:
            _t1167 = None
        attrs597 = _t1167
        self.consume_literal(")")
        _t1169 = logic_pb2.MonoidDef(monoid=monoid594, name=relation_id595, body=abstraction_with_arity596[0], attrs=(attrs597 if attrs597 is not None else []), value_arity=abstraction_with_arity596[1])
        return _t1169

    def parse_monoid(self) -> logic_pb2.Monoid:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1171 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1172 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1173 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1174 = 2
                        else:
                            _t1174 = -1
                        _t1173 = _t1174
                    _t1172 = _t1173
                _t1171 = _t1172
            _t1170 = _t1171
        else:
            _t1170 = -1
        prediction598 = _t1170
        if prediction598 == 3:
            _t1176 = self.parse_sum_monoid()
            sum_monoid602 = _t1176
            _t1177 = logic_pb2.Monoid(sum_monoid=sum_monoid602)
            _t1175 = _t1177
        else:
            if prediction598 == 2:
                _t1179 = self.parse_max_monoid()
                max_monoid601 = _t1179
                _t1180 = logic_pb2.Monoid(max_monoid=max_monoid601)
                _t1178 = _t1180
            else:
                if prediction598 == 1:
                    _t1182 = self.parse_min_monoid()
                    min_monoid600 = _t1182
                    _t1183 = logic_pb2.Monoid(min_monoid=min_monoid600)
                    _t1181 = _t1183
                else:
                    if prediction598 == 0:
                        _t1185 = self.parse_or_monoid()
                        or_monoid599 = _t1185
                        _t1186 = logic_pb2.Monoid(or_monoid=or_monoid599)
                        _t1184 = _t1186
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1181 = _t1184
                _t1178 = _t1181
            _t1175 = _t1178
        return _t1175

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1187 = logic_pb2.OrMonoid()
        return _t1187

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        self.consume_literal("(")
        self.consume_literal("min")
        _t1188 = self.parse_type()
        type603 = _t1188
        self.consume_literal(")")
        _t1189 = logic_pb2.MinMonoid(type=type603)
        return _t1189

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        self.consume_literal("(")
        self.consume_literal("max")
        _t1190 = self.parse_type()
        type604 = _t1190
        self.consume_literal(")")
        _t1191 = logic_pb2.MaxMonoid(type=type604)
        return _t1191

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1192 = self.parse_type()
        type605 = _t1192
        self.consume_literal(")")
        _t1193 = logic_pb2.SumMonoid(type=type605)
        return _t1193

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1194 = self.parse_monoid()
        monoid606 = _t1194
        _t1195 = self.parse_relation_id()
        relation_id607 = _t1195
        _t1196 = self.parse_abstraction_with_arity()
        abstraction_with_arity608 = _t1196
        if self.match_lookahead_literal("(", 0):
            _t1198 = self.parse_attrs()
            _t1197 = _t1198
        else:
            _t1197 = None
        attrs609 = _t1197
        self.consume_literal(")")
        _t1199 = logic_pb2.MonusDef(monoid=monoid606, name=relation_id607, body=abstraction_with_arity608[0], attrs=(attrs609 if attrs609 is not None else []), value_arity=abstraction_with_arity608[1])
        return _t1199

    def parse_constraint(self) -> logic_pb2.Constraint:
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1200 = self.parse_relation_id()
        relation_id610 = _t1200
        _t1201 = self.parse_abstraction()
        abstraction611 = _t1201
        _t1202 = self.parse_functional_dependency_keys()
        functional_dependency_keys612 = _t1202
        _t1203 = self.parse_functional_dependency_values()
        functional_dependency_values613 = _t1203
        self.consume_literal(")")
        _t1204 = logic_pb2.FunctionalDependency(guard=abstraction611, keys=functional_dependency_keys612, values=functional_dependency_values613)
        _t1205 = logic_pb2.Constraint(name=relation_id610, functional_dependency=_t1204)
        return _t1205

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs614 = []
        cond615 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond615:
            _t1206 = self.parse_var()
            item616 = _t1206
            xs614.append(item616)
            cond615 = self.match_lookahead_terminal("SYMBOL", 0)
        vars617 = xs614
        self.consume_literal(")")
        return vars617

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs618 = []
        cond619 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond619:
            _t1207 = self.parse_var()
            item620 = _t1207
            xs618.append(item620)
            cond619 = self.match_lookahead_terminal("SYMBOL", 0)
        vars621 = xs618
        self.consume_literal(")")
        return vars621

    def parse_data(self) -> logic_pb2.Data:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("rel_edb", 1):
                _t1209 = 0
            else:
                if self.match_lookahead_literal("csv_data", 1):
                    _t1210 = 2
                else:
                    if self.match_lookahead_literal("betree_relation", 1):
                        _t1211 = 1
                    else:
                        _t1211 = -1
                    _t1210 = _t1211
                _t1209 = _t1210
            _t1208 = _t1209
        else:
            _t1208 = -1
        prediction622 = _t1208
        if prediction622 == 2:
            _t1213 = self.parse_csv_data()
            csv_data625 = _t1213
            _t1214 = logic_pb2.Data(csv_data=csv_data625)
            _t1212 = _t1214
        else:
            if prediction622 == 1:
                _t1216 = self.parse_betree_relation()
                betree_relation624 = _t1216
                _t1217 = logic_pb2.Data(betree_relation=betree_relation624)
                _t1215 = _t1217
            else:
                if prediction622 == 0:
                    _t1219 = self.parse_rel_edb()
                    rel_edb623 = _t1219
                    _t1220 = logic_pb2.Data(rel_edb=rel_edb623)
                    _t1218 = _t1220
                else:
                    raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t1215 = _t1218
            _t1212 = _t1215
        return _t1212

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        self.consume_literal("(")
        self.consume_literal("rel_edb")
        _t1221 = self.parse_relation_id()
        relation_id626 = _t1221
        _t1222 = self.parse_rel_edb_path()
        rel_edb_path627 = _t1222
        _t1223 = self.parse_rel_edb_types()
        rel_edb_types628 = _t1223
        self.consume_literal(")")
        _t1224 = logic_pb2.RelEDB(target_id=relation_id626, path=rel_edb_path627, types=rel_edb_types628)
        return _t1224

    def parse_rel_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs629 = []
        cond630 = self.match_lookahead_terminal("STRING", 0)
        while cond630:
            item631 = self.consume_terminal("STRING")
            xs629.append(item631)
            cond630 = self.match_lookahead_terminal("STRING", 0)
        strings632 = xs629
        self.consume_literal("]")
        return strings632

    def parse_rel_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs633 = []
        cond634 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond634:
            _t1225 = self.parse_type()
            item635 = _t1225
            xs633.append(item635)
            cond634 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types636 = xs633
        self.consume_literal("]")
        return types636

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1226 = self.parse_relation_id()
        relation_id637 = _t1226
        _t1227 = self.parse_betree_info()
        betree_info638 = _t1227
        self.consume_literal(")")
        _t1228 = logic_pb2.BeTreeRelation(name=relation_id637, relation_info=betree_info638)
        return _t1228

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1229 = self.parse_betree_info_key_types()
        betree_info_key_types639 = _t1229
        _t1230 = self.parse_betree_info_value_types()
        betree_info_value_types640 = _t1230
        _t1231 = self.parse_config_dict()
        config_dict641 = _t1231
        self.consume_literal(")")
        _t1232 = self.construct_betree_info(betree_info_key_types639, betree_info_value_types640, config_dict641)
        return _t1232

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs642 = []
        cond643 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond643:
            _t1233 = self.parse_type()
            item644 = _t1233
            xs642.append(item644)
            cond643 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types645 = xs642
        self.consume_literal(")")
        return types645

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs646 = []
        cond647 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond647:
            _t1234 = self.parse_type()
            item648 = _t1234
            xs646.append(item648)
            cond647 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types649 = xs646
        self.consume_literal(")")
        return types649

    def parse_csv_data(self) -> logic_pb2.CSVData:
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1235 = self.parse_csvlocator()
        csvlocator650 = _t1235
        _t1236 = self.parse_csv_config()
        csv_config651 = _t1236
        _t1237 = self.parse_csv_columns()
        csv_columns652 = _t1237
        _t1238 = self.parse_csv_asof()
        csv_asof653 = _t1238
        self.consume_literal(")")
        _t1239 = logic_pb2.CSVData(locator=csvlocator650, config=csv_config651, columns=csv_columns652, asof=csv_asof653)
        return _t1239

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1241 = self.parse_csv_locator_paths()
            _t1240 = _t1241
        else:
            _t1240 = None
        csv_locator_paths654 = _t1240
        if self.match_lookahead_literal("(", 0):
            _t1243 = self.parse_csv_locator_inline_data()
            _t1242 = _t1243
        else:
            _t1242 = None
        csv_locator_inline_data655 = _t1242
        self.consume_literal(")")
        _t1244 = logic_pb2.CSVLocator(paths=(csv_locator_paths654 if csv_locator_paths654 is not None else []), inline_data=(csv_locator_inline_data655 if csv_locator_inline_data655 is not None else "").encode())
        return _t1244

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs656 = []
        cond657 = self.match_lookahead_terminal("STRING", 0)
        while cond657:
            item658 = self.consume_terminal("STRING")
            xs656.append(item658)
            cond657 = self.match_lookahead_terminal("STRING", 0)
        strings659 = xs656
        self.consume_literal(")")
        return strings659

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string660 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string660

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1245 = self.parse_config_dict()
        config_dict661 = _t1245
        self.consume_literal(")")
        _t1246 = self.construct_csv_config(config_dict661)
        return _t1246

    def parse_csv_columns(self) -> Sequence[logic_pb2.CSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs662 = []
        cond663 = self.match_lookahead_literal("(", 0)
        while cond663:
            _t1247 = self.parse_csv_column()
            item664 = _t1247
            xs662.append(item664)
            cond663 = self.match_lookahead_literal("(", 0)
        csv_columns665 = xs662
        self.consume_literal(")")
        return csv_columns665

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        self.consume_literal("(")
        self.consume_literal("column")
        string666 = self.consume_terminal("STRING")
        _t1248 = self.parse_relation_id()
        relation_id667 = _t1248
        self.consume_literal("[")
        xs668 = []
        cond669 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond669:
            _t1249 = self.parse_type()
            item670 = _t1249
            xs668.append(item670)
            cond669 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types671 = xs668
        self.consume_literal("]")
        self.consume_literal(")")
        _t1250 = logic_pb2.CSVColumn(column_name=string666, target_id=relation_id667, types=types671)
        return _t1250

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string672 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string672

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1251 = self.parse_fragment_id()
        fragment_id673 = _t1251
        self.consume_literal(")")
        _t1252 = transactions_pb2.Undefine(fragment_id=fragment_id673)
        return _t1252

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal("(")
        self.consume_literal("context")
        xs674 = []
        cond675 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond675:
            _t1253 = self.parse_relation_id()
            item676 = _t1253
            xs674.append(item676)
            cond675 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids677 = xs674
        self.consume_literal(")")
        _t1254 = transactions_pb2.Context(relations=relation_ids677)
        return _t1254

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs678 = []
        cond679 = self.match_lookahead_literal("(", 0)
        while cond679:
            _t1255 = self.parse_read()
            item680 = _t1255
            xs678.append(item680)
            cond679 = self.match_lookahead_literal("(", 0)
        reads681 = xs678
        self.consume_literal(")")
        return reads681

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1257 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1258 = 1
                else:
                    if self.match_lookahead_literal("export", 1):
                        _t1259 = 4
                    else:
                        if self.match_lookahead_literal("demand", 1):
                            _t1260 = 0
                        else:
                            if self.match_lookahead_literal("abort", 1):
                                _t1261 = 3
                            else:
                                _t1261 = -1
                            _t1260 = _t1261
                        _t1259 = _t1260
                    _t1258 = _t1259
                _t1257 = _t1258
            _t1256 = _t1257
        else:
            _t1256 = -1
        prediction682 = _t1256
        if prediction682 == 4:
            _t1263 = self.parse_export()
            export687 = _t1263
            _t1264 = transactions_pb2.Read(export=export687)
            _t1262 = _t1264
        else:
            if prediction682 == 3:
                _t1266 = self.parse_abort()
                abort686 = _t1266
                _t1267 = transactions_pb2.Read(abort=abort686)
                _t1265 = _t1267
            else:
                if prediction682 == 2:
                    _t1269 = self.parse_what_if()
                    what_if685 = _t1269
                    _t1270 = transactions_pb2.Read(what_if=what_if685)
                    _t1268 = _t1270
                else:
                    if prediction682 == 1:
                        _t1272 = self.parse_output()
                        output684 = _t1272
                        _t1273 = transactions_pb2.Read(output=output684)
                        _t1271 = _t1273
                    else:
                        if prediction682 == 0:
                            _t1275 = self.parse_demand()
                            demand683 = _t1275
                            _t1276 = transactions_pb2.Read(demand=demand683)
                            _t1274 = _t1276
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1271 = _t1274
                    _t1268 = _t1271
                _t1265 = _t1268
            _t1262 = _t1265
        return _t1262

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1277 = self.parse_relation_id()
        relation_id688 = _t1277
        self.consume_literal(")")
        _t1278 = transactions_pb2.Demand(relation_id=relation_id688)
        return _t1278

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal("(")
        self.consume_literal("output")
        _t1279 = self.parse_name()
        name689 = _t1279
        _t1280 = self.parse_relation_id()
        relation_id690 = _t1280
        self.consume_literal(")")
        _t1281 = transactions_pb2.Output(name=name689, relation_id=relation_id690)
        return _t1281

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t1282 = self.parse_name()
        name691 = _t1282
        _t1283 = self.parse_epoch()
        epoch692 = _t1283
        self.consume_literal(")")
        _t1284 = transactions_pb2.WhatIf(branch=name691, epoch=epoch692)
        return _t1284

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t1286 = self.parse_name()
            _t1285 = _t1286
        else:
            _t1285 = None
        name693 = _t1285
        _t1287 = self.parse_relation_id()
        relation_id694 = _t1287
        self.consume_literal(")")
        _t1288 = transactions_pb2.Abort(name=(name693 if name693 is not None else "abort"), relation_id=relation_id694)
        return _t1288

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal("(")
        self.consume_literal("export")
        _t1289 = self.parse_export_csv_config()
        export_csv_config695 = _t1289
        self.consume_literal(")")
        _t1290 = transactions_pb2.Export(csv_config=export_csv_config695)
        return _t1290

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal("(")
        self.consume_literal("export_csv_config")
        _t1291 = self.parse_export_csv_path()
        export_csv_path696 = _t1291
        _t1292 = self.parse_export_csv_columns()
        export_csv_columns697 = _t1292
        _t1293 = self.parse_config_dict()
        config_dict698 = _t1293
        self.consume_literal(")")
        _t1294 = self.export_csv_config(export_csv_path696, export_csv_columns697, config_dict698)
        return _t1294

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string699 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string699

    def parse_export_csv_columns(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs700 = []
        cond701 = self.match_lookahead_literal("(", 0)
        while cond701:
            _t1295 = self.parse_export_csv_column()
            item702 = _t1295
            xs700.append(item702)
            cond701 = self.match_lookahead_literal("(", 0)
        export_csv_columns703 = xs700
        self.consume_literal(")")
        return export_csv_columns703

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal("(")
        self.consume_literal("column")
        string704 = self.consume_terminal("STRING")
        _t1296 = self.parse_relation_id()
        relation_id705 = _t1296
        self.consume_literal(")")
        _t1297 = transactions_pb2.ExportCSVColumn(column_name=string704, column_data=relation_id705)
        return _t1297


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
