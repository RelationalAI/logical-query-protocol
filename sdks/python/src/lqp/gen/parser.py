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
            _t1311 = value.HasField("int_value")
        else:
            _t1311 = False
        if _t1311:
            assert value is not None
            return int(value.int_value)
        else:
            _t1312 = None
        return int(default)

    def _extract_value_int64(self, value: Optional[logic_pb2.Value], default: int) -> int:
        if value is not None:
            assert value is not None
            _t1313 = value.HasField("int_value")
        else:
            _t1313 = False
        if _t1313:
            assert value is not None
            return value.int_value
        else:
            _t1314 = None
        return default

    def _extract_value_string(self, value: Optional[logic_pb2.Value], default: str) -> str:
        if value is not None:
            assert value is not None
            _t1315 = value.HasField("string_value")
        else:
            _t1315 = False
        if _t1315:
            assert value is not None
            return value.string_value
        else:
            _t1316 = None
        return default

    def _extract_value_boolean(self, value: Optional[logic_pb2.Value], default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t1317 = value.HasField("boolean_value")
        else:
            _t1317 = False
        if _t1317:
            assert value is not None
            return value.boolean_value
        else:
            _t1318 = None
        return default

    def _extract_value_string_list(self, value: Optional[logic_pb2.Value], default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t1319 = value.HasField("string_value")
        else:
            _t1319 = False
        if _t1319:
            assert value is not None
            return [value.string_value]
        else:
            _t1320 = None
        return default

    def _try_extract_value_int64(self, value: Optional[logic_pb2.Value]) -> Optional[int]:
        if value is not None:
            assert value is not None
            _t1321 = value.HasField("int_value")
        else:
            _t1321 = False
        if _t1321:
            assert value is not None
            return value.int_value
        else:
            _t1322 = None
        return None

    def _try_extract_value_float64(self, value: Optional[logic_pb2.Value]) -> Optional[float]:
        if value is not None:
            assert value is not None
            _t1323 = value.HasField("float_value")
        else:
            _t1323 = False
        if _t1323:
            assert value is not None
            return value.float_value
        else:
            _t1324 = None
        return None

    def _try_extract_value_bytes(self, value: Optional[logic_pb2.Value]) -> Optional[bytes]:
        if value is not None:
            assert value is not None
            _t1325 = value.HasField("string_value")
        else:
            _t1325 = False
        if _t1325:
            assert value is not None
            return value.string_value.encode()
        else:
            _t1326 = None
        return None

    def _try_extract_value_uint128(self, value: Optional[logic_pb2.Value]) -> Optional[logic_pb2.UInt128Value]:
        if value is not None:
            assert value is not None
            _t1327 = value.HasField("uint128_value")
        else:
            _t1327 = False
        if _t1327:
            assert value is not None
            return value.uint128_value
        else:
            _t1328 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1329 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t1329
        _t1330 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t1330
        _t1331 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t1331
        _t1332 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t1332
        _t1333 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t1333
        _t1334 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t1334
        _t1335 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t1335
        _t1336 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t1336
        _t1337 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t1337
        _t1338 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t1338
        _t1339 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t1339
        _t1340 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t1340

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1341 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t1341
        _t1342 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t1342
        _t1343 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t1343
        _t1344 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t1344
        _t1345 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1345
        _t1346 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t1346
        _t1347 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t1347
        _t1348 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t1348
        _t1349 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t1349
        _t1350 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1350
        _t1351 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1351

    def default_configure(self) -> transactions_pb2.Configure:
        _t1352 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1352
        _t1353 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1353

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
        _t1354 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1354
        _t1355 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t1355
        _t1356 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1356

    def export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1357 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t1357
        _t1358 = self._extract_value_string(config.get("compression"), "")
        compression = _t1358
        _t1359 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t1359
        _t1360 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t1360
        _t1361 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t1361
        _t1362 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t1362
        _t1363 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t1363
        _t1364 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1364

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t713 = self.parse_configure()
            _t712 = _t713
        else:
            _t712 = None
        configure356 = _t712
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t715 = self.parse_sync()
            _t714 = _t715
        else:
            _t714 = None
        sync357 = _t714
        xs358 = []
        cond359 = self.match_lookahead_literal("(", 0)
        while cond359:
            _t716 = self.parse_epoch()
            item360 = _t716
            xs358.append(item360)
            cond359 = self.match_lookahead_literal("(", 0)
        epochs361 = xs358
        self.consume_literal(")")
        _t717 = self.default_configure()
        _t718 = transactions_pb2.Transaction(epochs=epochs361, configure=(configure356 if configure356 is not None else _t717), sync=sync357)
        return _t718

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal("(")
        self.consume_literal("configure")
        _t719 = self.parse_config_dict()
        config_dict362 = _t719
        self.consume_literal(")")
        _t720 = self.construct_configure(config_dict362)
        return _t720

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs363 = []
        cond364 = self.match_lookahead_literal(":", 0)
        while cond364:
            _t721 = self.parse_config_key_value()
            item365 = _t721
            xs363.append(item365)
            cond364 = self.match_lookahead_literal(":", 0)
        config_key_values366 = xs363
        self.consume_literal("}")
        return config_key_values366

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol367 = self.consume_terminal("SYMBOL")
        _t722 = self.parse_value()
        value368 = _t722
        return (symbol367, value368,)

    def parse_value(self) -> logic_pb2.Value:
        if self.match_lookahead_literal("true", 0):
            _t723 = 9
        else:
            if self.match_lookahead_literal("missing", 0):
                _t724 = 8
            else:
                if self.match_lookahead_literal("false", 0):
                    _t725 = 9
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t727 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t728 = 0
                            else:
                                _t728 = -1
                            _t727 = _t728
                        _t726 = _t727
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t729 = 5
                        else:
                            if self.match_lookahead_terminal("STRING", 0):
                                _t730 = 2
                            else:
                                if self.match_lookahead_terminal("INT128", 0):
                                    _t731 = 6
                                else:
                                    if self.match_lookahead_terminal("INT", 0):
                                        _t732 = 3
                                    else:
                                        if self.match_lookahead_terminal("FLOAT", 0):
                                            _t733 = 4
                                        else:
                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                _t734 = 7
                                            else:
                                                _t734 = -1
                                            _t733 = _t734
                                        _t732 = _t733
                                    _t731 = _t732
                                _t730 = _t731
                            _t729 = _t730
                        _t726 = _t729
                    _t725 = _t726
                _t724 = _t725
            _t723 = _t724
        prediction369 = _t723
        if prediction369 == 9:
            _t736 = self.parse_boolean_value()
            boolean_value378 = _t736
            _t737 = logic_pb2.Value(boolean_value=boolean_value378)
            _t735 = _t737
        else:
            if prediction369 == 8:
                self.consume_literal("missing")
                _t739 = logic_pb2.MissingValue()
                _t740 = logic_pb2.Value(missing_value=_t739)
                _t738 = _t740
            else:
                if prediction369 == 7:
                    decimal377 = self.consume_terminal("DECIMAL")
                    _t742 = logic_pb2.Value(decimal_value=decimal377)
                    _t741 = _t742
                else:
                    if prediction369 == 6:
                        int128376 = self.consume_terminal("INT128")
                        _t744 = logic_pb2.Value(int128_value=int128376)
                        _t743 = _t744
                    else:
                        if prediction369 == 5:
                            uint128375 = self.consume_terminal("UINT128")
                            _t746 = logic_pb2.Value(uint128_value=uint128375)
                            _t745 = _t746
                        else:
                            if prediction369 == 4:
                                float374 = self.consume_terminal("FLOAT")
                                _t748 = logic_pb2.Value(float_value=float374)
                                _t747 = _t748
                            else:
                                if prediction369 == 3:
                                    int373 = self.consume_terminal("INT")
                                    _t750 = logic_pb2.Value(int_value=int373)
                                    _t749 = _t750
                                else:
                                    if prediction369 == 2:
                                        string372 = self.consume_terminal("STRING")
                                        _t752 = logic_pb2.Value(string_value=string372)
                                        _t751 = _t752
                                    else:
                                        if prediction369 == 1:
                                            _t754 = self.parse_datetime()
                                            datetime371 = _t754
                                            _t755 = logic_pb2.Value(datetime_value=datetime371)
                                            _t753 = _t755
                                        else:
                                            if prediction369 == 0:
                                                _t757 = self.parse_date()
                                                date370 = _t757
                                                _t758 = logic_pb2.Value(date_value=date370)
                                                _t756 = _t758
                                            else:
                                                raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t753 = _t756
                                        _t751 = _t753
                                    _t749 = _t751
                                _t747 = _t749
                            _t745 = _t747
                        _t743 = _t745
                    _t741 = _t743
                _t738 = _t741
            _t735 = _t738
        return _t735

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal("(")
        self.consume_literal("date")
        int379 = self.consume_terminal("INT")
        int_3380 = self.consume_terminal("INT")
        int_4381 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t759 = logic_pb2.DateValue(year=int(int379), month=int(int_3380), day=int(int_4381))
        return _t759

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        self.consume_literal("(")
        self.consume_literal("datetime")
        int382 = self.consume_terminal("INT")
        int_3383 = self.consume_terminal("INT")
        int_4384 = self.consume_terminal("INT")
        int_5385 = self.consume_terminal("INT")
        int_6386 = self.consume_terminal("INT")
        int_7387 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t760 = self.consume_terminal("INT")
        else:
            _t760 = None
        int_8388 = _t760
        self.consume_literal(")")
        _t761 = logic_pb2.DateTimeValue(year=int(int382), month=int(int_3383), day=int(int_4384), hour=int(int_5385), minute=int(int_6386), second=int(int_7387), microsecond=int((int_8388 if int_8388 is not None else 0)))
        return _t761

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t762 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t763 = 1
            else:
                _t763 = -1
            _t762 = _t763
        prediction389 = _t762
        if prediction389 == 1:
            self.consume_literal("false")
            _t764 = False
        else:
            if prediction389 == 0:
                self.consume_literal("true")
                _t765 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t764 = _t765
        return _t764

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal("(")
        self.consume_literal("sync")
        xs390 = []
        cond391 = self.match_lookahead_literal(":", 0)
        while cond391:
            _t766 = self.parse_fragment_id()
            item392 = _t766
            xs390.append(item392)
            cond391 = self.match_lookahead_literal(":", 0)
        fragment_ids393 = xs390
        self.consume_literal(")")
        _t767 = transactions_pb2.Sync(fragments=fragment_ids393)
        return _t767

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        self.consume_literal(":")
        symbol394 = self.consume_terminal("SYMBOL")
        return fragments_pb2.FragmentId(id=symbol394.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t769 = self.parse_epoch_writes()
            _t768 = _t769
        else:
            _t768 = None
        epoch_writes395 = _t768
        if self.match_lookahead_literal("(", 0):
            _t771 = self.parse_epoch_reads()
            _t770 = _t771
        else:
            _t770 = None
        epoch_reads396 = _t770
        self.consume_literal(")")
        _t772 = transactions_pb2.Epoch(writes=(epoch_writes395 if epoch_writes395 is not None else []), reads=(epoch_reads396 if epoch_reads396 is not None else []))
        return _t772

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs397 = []
        cond398 = self.match_lookahead_literal("(", 0)
        while cond398:
            _t773 = self.parse_write()
            item399 = _t773
            xs397.append(item399)
            cond398 = self.match_lookahead_literal("(", 0)
        writes400 = xs397
        self.consume_literal(")")
        return writes400

    def parse_write(self) -> transactions_pb2.Write:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t775 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t776 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t777 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t778 = 2
                        else:
                            _t778 = -1
                        _t777 = _t778
                    _t776 = _t777
                _t775 = _t776
            _t774 = _t775
        else:
            _t774 = -1
        prediction401 = _t774
        if prediction401 == 3:
            _t780 = self.parse_snapshot()
            snapshot405 = _t780
            _t781 = transactions_pb2.Write(snapshot=snapshot405)
            _t779 = _t781
        else:
            if prediction401 == 2:
                _t783 = self.parse_context()
                context404 = _t783
                _t784 = transactions_pb2.Write(context=context404)
                _t782 = _t784
            else:
                if prediction401 == 1:
                    _t786 = self.parse_undefine()
                    undefine403 = _t786
                    _t787 = transactions_pb2.Write(undefine=undefine403)
                    _t785 = _t787
                else:
                    if prediction401 == 0:
                        _t789 = self.parse_define()
                        define402 = _t789
                        _t790 = transactions_pb2.Write(define=define402)
                        _t788 = _t790
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t785 = _t788
                _t782 = _t785
            _t779 = _t782
        return _t779

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal("(")
        self.consume_literal("define")
        _t791 = self.parse_fragment()
        fragment406 = _t791
        self.consume_literal(")")
        _t792 = transactions_pb2.Define(fragment=fragment406)
        return _t792

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t793 = self.parse_new_fragment_id()
        new_fragment_id407 = _t793
        xs408 = []
        cond409 = self.match_lookahead_literal("(", 0)
        while cond409:
            _t794 = self.parse_declaration()
            item410 = _t794
            xs408.append(item410)
            cond409 = self.match_lookahead_literal("(", 0)
        declarations411 = xs408
        self.consume_literal(")")
        return self.construct_fragment(new_fragment_id407, declarations411)

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        _t795 = self.parse_fragment_id()
        fragment_id412 = _t795
        self.start_fragment(fragment_id412)
        return fragment_id412

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("rel_edb", 1):
                _t797 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t798 = 2
                else:
                    if self.match_lookahead_literal("def", 1):
                        _t799 = 0
                    else:
                        if self.match_lookahead_literal("csv_data", 1):
                            _t800 = 3
                        else:
                            if self.match_lookahead_literal("betree_relation", 1):
                                _t801 = 3
                            else:
                                if self.match_lookahead_literal("algorithm", 1):
                                    _t802 = 1
                                else:
                                    _t802 = -1
                                _t801 = _t802
                            _t800 = _t801
                        _t799 = _t800
                    _t798 = _t799
                _t797 = _t798
            _t796 = _t797
        else:
            _t796 = -1
        prediction413 = _t796
        if prediction413 == 3:
            _t804 = self.parse_data()
            data417 = _t804
            _t805 = logic_pb2.Declaration(data=data417)
            _t803 = _t805
        else:
            if prediction413 == 2:
                _t807 = self.parse_constraint()
                constraint416 = _t807
                _t808 = logic_pb2.Declaration(constraint=constraint416)
                _t806 = _t808
            else:
                if prediction413 == 1:
                    _t810 = self.parse_algorithm()
                    algorithm415 = _t810
                    _t811 = logic_pb2.Declaration(algorithm=algorithm415)
                    _t809 = _t811
                else:
                    if prediction413 == 0:
                        _t813 = self.parse_def()
                        def414 = _t813
                        _t814 = logic_pb2.Declaration()
                        getattr(_t814, 'def').CopyFrom(def414)
                        _t812 = _t814
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t809 = _t812
                _t806 = _t809
            _t803 = _t806
        return _t803

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal("(")
        self.consume_literal("def")
        _t815 = self.parse_relation_id()
        relation_id418 = _t815
        _t816 = self.parse_abstraction()
        abstraction419 = _t816
        if self.match_lookahead_literal("(", 0):
            _t818 = self.parse_attrs()
            _t817 = _t818
        else:
            _t817 = None
        attrs420 = _t817
        self.consume_literal(")")
        _t819 = logic_pb2.Def(name=relation_id418, body=abstraction419, attrs=(attrs420 if attrs420 is not None else []))
        return _t819

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_literal(":", 0):
            _t820 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t821 = 1
            else:
                _t821 = -1
            _t820 = _t821
        prediction421 = _t820
        if prediction421 == 1:
            uint128423 = self.consume_terminal("UINT128")
            _t822 = logic_pb2.RelationId(id_low=uint128423.low, id_high=uint128423.high)
        else:
            if prediction421 == 0:
                self.consume_literal(":")
                symbol422 = self.consume_terminal("SYMBOL")
                _t823 = self.relation_id_from_string(symbol422)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t822 = _t823
        return _t822

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal("(")
        _t824 = self.parse_bindings()
        bindings424 = _t824
        _t825 = self.parse_formula()
        formula425 = _t825
        self.consume_literal(")")
        _t826 = logic_pb2.Abstraction(vars=(list(bindings424[0]) + list(bindings424[1] if bindings424[1] is not None else [])), value=formula425)
        return _t826

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs426 = []
        cond427 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond427:
            _t827 = self.parse_binding()
            item428 = _t827
            xs426.append(item428)
            cond427 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings429 = xs426
        if self.match_lookahead_literal("|", 0):
            _t829 = self.parse_value_bindings()
            _t828 = _t829
        else:
            _t828 = None
        value_bindings430 = _t828
        self.consume_literal("]")
        return (bindings429, (value_bindings430 if value_bindings430 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol431 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t830 = self.parse_type()
        type432 = _t830
        _t831 = logic_pb2.Var(name=symbol431)
        _t832 = logic_pb2.Binding(var=_t831, type=type432)
        return _t832

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t833 = 0
        else:
            if self.match_lookahead_literal("UINT128", 0):
                _t834 = 4
            else:
                if self.match_lookahead_literal("STRING", 0):
                    _t835 = 1
                else:
                    if self.match_lookahead_literal("MISSING", 0):
                        _t836 = 8
                    else:
                        if self.match_lookahead_literal("INT128", 0):
                            _t837 = 5
                        else:
                            if self.match_lookahead_literal("INT", 0):
                                _t838 = 2
                            else:
                                if self.match_lookahead_literal("FLOAT", 0):
                                    _t839 = 3
                                else:
                                    if self.match_lookahead_literal("DATETIME", 0):
                                        _t840 = 7
                                    else:
                                        if self.match_lookahead_literal("DATE", 0):
                                            _t841 = 6
                                        else:
                                            if self.match_lookahead_literal("BOOLEAN", 0):
                                                _t842 = 10
                                            else:
                                                if self.match_lookahead_literal("(", 0):
                                                    _t843 = 9
                                                else:
                                                    _t843 = -1
                                                _t842 = _t843
                                            _t841 = _t842
                                        _t840 = _t841
                                    _t839 = _t840
                                _t838 = _t839
                            _t837 = _t838
                        _t836 = _t837
                    _t835 = _t836
                _t834 = _t835
            _t833 = _t834
        prediction433 = _t833
        if prediction433 == 10:
            _t845 = self.parse_boolean_type()
            boolean_type444 = _t845
            _t846 = logic_pb2.Type(boolean_type=boolean_type444)
            _t844 = _t846
        else:
            if prediction433 == 9:
                _t848 = self.parse_decimal_type()
                decimal_type443 = _t848
                _t849 = logic_pb2.Type(decimal_type=decimal_type443)
                _t847 = _t849
            else:
                if prediction433 == 8:
                    _t851 = self.parse_missing_type()
                    missing_type442 = _t851
                    _t852 = logic_pb2.Type(missing_type=missing_type442)
                    _t850 = _t852
                else:
                    if prediction433 == 7:
                        _t854 = self.parse_datetime_type()
                        datetime_type441 = _t854
                        _t855 = logic_pb2.Type(datetime_type=datetime_type441)
                        _t853 = _t855
                    else:
                        if prediction433 == 6:
                            _t857 = self.parse_date_type()
                            date_type440 = _t857
                            _t858 = logic_pb2.Type(date_type=date_type440)
                            _t856 = _t858
                        else:
                            if prediction433 == 5:
                                _t860 = self.parse_int128_type()
                                int128_type439 = _t860
                                _t861 = logic_pb2.Type(int128_type=int128_type439)
                                _t859 = _t861
                            else:
                                if prediction433 == 4:
                                    _t863 = self.parse_uint128_type()
                                    uint128_type438 = _t863
                                    _t864 = logic_pb2.Type(uint128_type=uint128_type438)
                                    _t862 = _t864
                                else:
                                    if prediction433 == 3:
                                        _t866 = self.parse_float_type()
                                        float_type437 = _t866
                                        _t867 = logic_pb2.Type(float_type=float_type437)
                                        _t865 = _t867
                                    else:
                                        if prediction433 == 2:
                                            _t869 = self.parse_int_type()
                                            int_type436 = _t869
                                            _t870 = logic_pb2.Type(int_type=int_type436)
                                            _t868 = _t870
                                        else:
                                            if prediction433 == 1:
                                                _t872 = self.parse_string_type()
                                                string_type435 = _t872
                                                _t873 = logic_pb2.Type(string_type=string_type435)
                                                _t871 = _t873
                                            else:
                                                if prediction433 == 0:
                                                    _t875 = self.parse_unspecified_type()
                                                    unspecified_type434 = _t875
                                                    _t876 = logic_pb2.Type(unspecified_type=unspecified_type434)
                                                    _t874 = _t876
                                                else:
                                                    raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t871 = _t874
                                            _t868 = _t871
                                        _t865 = _t868
                                    _t862 = _t865
                                _t859 = _t862
                            _t856 = _t859
                        _t853 = _t856
                    _t850 = _t853
                _t847 = _t850
            _t844 = _t847
        return _t844

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        self.consume_literal("UNKNOWN")
        _t877 = logic_pb2.UnspecifiedType()
        return _t877

    def parse_string_type(self) -> logic_pb2.StringType:
        self.consume_literal("STRING")
        _t878 = logic_pb2.StringType()
        return _t878

    def parse_int_type(self) -> logic_pb2.IntType:
        self.consume_literal("INT")
        _t879 = logic_pb2.IntType()
        return _t879

    def parse_float_type(self) -> logic_pb2.FloatType:
        self.consume_literal("FLOAT")
        _t880 = logic_pb2.FloatType()
        return _t880

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        self.consume_literal("UINT128")
        _t881 = logic_pb2.UInt128Type()
        return _t881

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        self.consume_literal("INT128")
        _t882 = logic_pb2.Int128Type()
        return _t882

    def parse_date_type(self) -> logic_pb2.DateType:
        self.consume_literal("DATE")
        _t883 = logic_pb2.DateType()
        return _t883

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        self.consume_literal("DATETIME")
        _t884 = logic_pb2.DateTimeType()
        return _t884

    def parse_missing_type(self) -> logic_pb2.MissingType:
        self.consume_literal("MISSING")
        _t885 = logic_pb2.MissingType()
        return _t885

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int445 = self.consume_terminal("INT")
        int_3446 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t886 = logic_pb2.DecimalType(precision=int(int445), scale=int(int_3446))
        return _t886

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal("BOOLEAN")
        _t887 = logic_pb2.BooleanType()
        return _t887

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs447 = []
        cond448 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond448:
            _t888 = self.parse_binding()
            item449 = _t888
            xs447.append(item449)
            cond448 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings450 = xs447
        return bindings450

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t890 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t891 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t892 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t893 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t894 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t895 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t896 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t897 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t898 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t899 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t900 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t901 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t902 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t903 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t904 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t905 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t906 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t907 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t908 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t909 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t910 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t911 = 10
                                                                                                else:
                                                                                                    _t911 = -1
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
        else:
            _t889 = -1
        prediction451 = _t889
        if prediction451 == 12:
            _t913 = self.parse_cast()
            cast464 = _t913
            _t914 = logic_pb2.Formula(cast=cast464)
            _t912 = _t914
        else:
            if prediction451 == 11:
                _t916 = self.parse_rel_atom()
                rel_atom463 = _t916
                _t917 = logic_pb2.Formula(rel_atom=rel_atom463)
                _t915 = _t917
            else:
                if prediction451 == 10:
                    _t919 = self.parse_primitive()
                    primitive462 = _t919
                    _t920 = logic_pb2.Formula(primitive=primitive462)
                    _t918 = _t920
                else:
                    if prediction451 == 9:
                        _t922 = self.parse_pragma()
                        pragma461 = _t922
                        _t923 = logic_pb2.Formula(pragma=pragma461)
                        _t921 = _t923
                    else:
                        if prediction451 == 8:
                            _t925 = self.parse_atom()
                            atom460 = _t925
                            _t926 = logic_pb2.Formula(atom=atom460)
                            _t924 = _t926
                        else:
                            if prediction451 == 7:
                                _t928 = self.parse_ffi()
                                ffi459 = _t928
                                _t929 = logic_pb2.Formula(ffi=ffi459)
                                _t927 = _t929
                            else:
                                if prediction451 == 6:
                                    _t931 = self.parse_not()
                                    not458 = _t931
                                    _t932 = logic_pb2.Formula()
                                    getattr(_t932, 'not').CopyFrom(not458)
                                    _t930 = _t932
                                else:
                                    if prediction451 == 5:
                                        _t934 = self.parse_disjunction()
                                        disjunction457 = _t934
                                        _t935 = logic_pb2.Formula(disjunction=disjunction457)
                                        _t933 = _t935
                                    else:
                                        if prediction451 == 4:
                                            _t937 = self.parse_conjunction()
                                            conjunction456 = _t937
                                            _t938 = logic_pb2.Formula(conjunction=conjunction456)
                                            _t936 = _t938
                                        else:
                                            if prediction451 == 3:
                                                _t940 = self.parse_reduce()
                                                reduce455 = _t940
                                                _t941 = logic_pb2.Formula(reduce=reduce455)
                                                _t939 = _t941
                                            else:
                                                if prediction451 == 2:
                                                    _t943 = self.parse_exists()
                                                    exists454 = _t943
                                                    _t944 = logic_pb2.Formula(exists=exists454)
                                                    _t942 = _t944
                                                else:
                                                    if prediction451 == 1:
                                                        _t946 = self.parse_false()
                                                        false453 = _t946
                                                        _t947 = logic_pb2.Formula(disjunction=false453)
                                                        _t945 = _t947
                                                    else:
                                                        if prediction451 == 0:
                                                            _t949 = self.parse_true()
                                                            true452 = _t949
                                                            _t950 = logic_pb2.Formula(conjunction=true452)
                                                            _t948 = _t950
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t945 = _t948
                                                    _t942 = _t945
                                                _t939 = _t942
                                            _t936 = _t939
                                        _t933 = _t936
                                    _t930 = _t933
                                _t927 = _t930
                            _t924 = _t927
                        _t921 = _t924
                    _t918 = _t921
                _t915 = _t918
            _t912 = _t915
        return _t912

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t951 = logic_pb2.Conjunction(args=[])
        return _t951

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t952 = logic_pb2.Disjunction(args=[])
        return _t952

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal("(")
        self.consume_literal("exists")
        _t953 = self.parse_bindings()
        bindings465 = _t953
        _t954 = self.parse_formula()
        formula466 = _t954
        self.consume_literal(")")
        _t955 = logic_pb2.Abstraction(vars=(list(bindings465[0]) + list(bindings465[1] if bindings465[1] is not None else [])), value=formula466)
        _t956 = logic_pb2.Exists(body=_t955)
        return _t956

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t957 = self.parse_abstraction()
        abstraction467 = _t957
        _t958 = self.parse_abstraction()
        abstraction_3468 = _t958
        _t959 = self.parse_terms()
        terms469 = _t959
        self.consume_literal(")")
        _t960 = logic_pb2.Reduce(op=abstraction467, body=abstraction_3468, terms=terms469)
        return _t960

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs470 = []
        cond471 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond471:
            _t961 = self.parse_term()
            item472 = _t961
            xs470.append(item472)
            cond471 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms473 = xs470
        self.consume_literal(")")
        return terms473

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_literal("true", 0):
            _t962 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t963 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t964 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t965 = 1
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t966 = 1
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t967 = 0
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t968 = 1
                                else:
                                    if self.match_lookahead_terminal("INT128", 0):
                                        _t969 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT", 0):
                                            _t970 = 1
                                        else:
                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                _t971 = 1
                                            else:
                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                    _t972 = 1
                                                else:
                                                    _t972 = -1
                                                _t971 = _t972
                                            _t970 = _t971
                                        _t969 = _t970
                                    _t968 = _t969
                                _t967 = _t968
                            _t966 = _t967
                        _t965 = _t966
                    _t964 = _t965
                _t963 = _t964
            _t962 = _t963
        prediction474 = _t962
        if prediction474 == 1:
            _t974 = self.parse_constant()
            constant476 = _t974
            _t975 = logic_pb2.Term(constant=constant476)
            _t973 = _t975
        else:
            if prediction474 == 0:
                _t977 = self.parse_var()
                var475 = _t977
                _t978 = logic_pb2.Term(var=var475)
                _t976 = _t978
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t973 = _t976
        return _t973

    def parse_var(self) -> logic_pb2.Var:
        symbol477 = self.consume_terminal("SYMBOL")
        _t979 = logic_pb2.Var(name=symbol477)
        return _t979

    def parse_constant(self) -> logic_pb2.Value:
        _t980 = self.parse_value()
        value478 = _t980
        return value478

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal("(")
        self.consume_literal("and")
        xs479 = []
        cond480 = self.match_lookahead_literal("(", 0)
        while cond480:
            _t981 = self.parse_formula()
            item481 = _t981
            xs479.append(item481)
            cond480 = self.match_lookahead_literal("(", 0)
        formulas482 = xs479
        self.consume_literal(")")
        _t982 = logic_pb2.Conjunction(args=formulas482)
        return _t982

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal("(")
        self.consume_literal("or")
        xs483 = []
        cond484 = self.match_lookahead_literal("(", 0)
        while cond484:
            _t983 = self.parse_formula()
            item485 = _t983
            xs483.append(item485)
            cond484 = self.match_lookahead_literal("(", 0)
        formulas486 = xs483
        self.consume_literal(")")
        _t984 = logic_pb2.Disjunction(args=formulas486)
        return _t984

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal("(")
        self.consume_literal("not")
        _t985 = self.parse_formula()
        formula487 = _t985
        self.consume_literal(")")
        _t986 = logic_pb2.Not(arg=formula487)
        return _t986

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t987 = self.parse_name()
        name488 = _t987
        _t988 = self.parse_ffi_args()
        ffi_args489 = _t988
        _t989 = self.parse_terms()
        terms490 = _t989
        self.consume_literal(")")
        _t990 = logic_pb2.FFI(name=name488, args=ffi_args489, terms=terms490)
        return _t990

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol491 = self.consume_terminal("SYMBOL")
        return symbol491

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs492 = []
        cond493 = self.match_lookahead_literal("(", 0)
        while cond493:
            _t991 = self.parse_abstraction()
            item494 = _t991
            xs492.append(item494)
            cond493 = self.match_lookahead_literal("(", 0)
        abstractions495 = xs492
        self.consume_literal(")")
        return abstractions495

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal("(")
        self.consume_literal("atom")
        _t992 = self.parse_relation_id()
        relation_id496 = _t992
        xs497 = []
        cond498 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond498:
            _t993 = self.parse_term()
            item499 = _t993
            xs497.append(item499)
            cond498 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms500 = xs497
        self.consume_literal(")")
        _t994 = logic_pb2.Atom(name=relation_id496, terms=terms500)
        return _t994

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t995 = self.parse_name()
        name501 = _t995
        xs502 = []
        cond503 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond503:
            _t996 = self.parse_term()
            item504 = _t996
            xs502.append(item504)
            cond503 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms505 = xs502
        self.consume_literal(")")
        _t997 = logic_pb2.Pragma(name=name501, terms=terms505)
        return _t997

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t999 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1000 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1001 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1002 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1003 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1004 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1005 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1006 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1007 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1008 = 7
                                                else:
                                                    _t1008 = -1
                                                _t1007 = _t1008
                                            _t1006 = _t1007
                                        _t1005 = _t1006
                                    _t1004 = _t1005
                                _t1003 = _t1004
                            _t1002 = _t1003
                        _t1001 = _t1002
                    _t1000 = _t1001
                _t999 = _t1000
            _t998 = _t999
        else:
            _t998 = -1
        prediction506 = _t998
        if prediction506 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1010 = self.parse_name()
            name516 = _t1010
            xs517 = []
            cond518 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            while cond518:
                _t1011 = self.parse_rel_term()
                item519 = _t1011
                xs517.append(item519)
                cond518 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            rel_terms520 = xs517
            self.consume_literal(")")
            _t1012 = logic_pb2.Primitive(name=name516, terms=rel_terms520)
            _t1009 = _t1012
        else:
            if prediction506 == 8:
                _t1014 = self.parse_divide()
                divide515 = _t1014
                _t1013 = divide515
            else:
                if prediction506 == 7:
                    _t1016 = self.parse_multiply()
                    multiply514 = _t1016
                    _t1015 = multiply514
                else:
                    if prediction506 == 6:
                        _t1018 = self.parse_minus()
                        minus513 = _t1018
                        _t1017 = minus513
                    else:
                        if prediction506 == 5:
                            _t1020 = self.parse_add()
                            add512 = _t1020
                            _t1019 = add512
                        else:
                            if prediction506 == 4:
                                _t1022 = self.parse_gt_eq()
                                gt_eq511 = _t1022
                                _t1021 = gt_eq511
                            else:
                                if prediction506 == 3:
                                    _t1024 = self.parse_gt()
                                    gt510 = _t1024
                                    _t1023 = gt510
                                else:
                                    if prediction506 == 2:
                                        _t1026 = self.parse_lt_eq()
                                        lt_eq509 = _t1026
                                        _t1025 = lt_eq509
                                    else:
                                        if prediction506 == 1:
                                            _t1028 = self.parse_lt()
                                            lt508 = _t1028
                                            _t1027 = lt508
                                        else:
                                            if prediction506 == 0:
                                                _t1030 = self.parse_eq()
                                                eq507 = _t1030
                                                _t1029 = eq507
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1027 = _t1029
                                        _t1025 = _t1027
                                    _t1023 = _t1025
                                _t1021 = _t1023
                            _t1019 = _t1021
                        _t1017 = _t1019
                    _t1015 = _t1017
                _t1013 = _t1015
            _t1009 = _t1013
        return _t1009

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("=")
        _t1031 = self.parse_term()
        term521 = _t1031
        _t1032 = self.parse_term()
        term_3522 = _t1032
        self.consume_literal(")")
        _t1033 = logic_pb2.RelTerm(term=term521)
        _t1034 = logic_pb2.RelTerm(term=term_3522)
        _t1035 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1033, _t1034])
        return _t1035

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("<")
        _t1036 = self.parse_term()
        term523 = _t1036
        _t1037 = self.parse_term()
        term_3524 = _t1037
        self.consume_literal(")")
        _t1038 = logic_pb2.RelTerm(term=term523)
        _t1039 = logic_pb2.RelTerm(term=term_3524)
        _t1040 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1038, _t1039])
        return _t1040

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1041 = self.parse_term()
        term525 = _t1041
        _t1042 = self.parse_term()
        term_3526 = _t1042
        self.consume_literal(")")
        _t1043 = logic_pb2.RelTerm(term=term525)
        _t1044 = logic_pb2.RelTerm(term=term_3526)
        _t1045 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1043, _t1044])
        return _t1045

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal(">")
        _t1046 = self.parse_term()
        term527 = _t1046
        _t1047 = self.parse_term()
        term_3528 = _t1047
        self.consume_literal(")")
        _t1048 = logic_pb2.RelTerm(term=term527)
        _t1049 = logic_pb2.RelTerm(term=term_3528)
        _t1050 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1048, _t1049])
        return _t1050

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1051 = self.parse_term()
        term529 = _t1051
        _t1052 = self.parse_term()
        term_3530 = _t1052
        self.consume_literal(")")
        _t1053 = logic_pb2.RelTerm(term=term529)
        _t1054 = logic_pb2.RelTerm(term=term_3530)
        _t1055 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1053, _t1054])
        return _t1055

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("+")
        _t1056 = self.parse_term()
        term531 = _t1056
        _t1057 = self.parse_term()
        term_3532 = _t1057
        _t1058 = self.parse_term()
        term_4533 = _t1058
        self.consume_literal(")")
        _t1059 = logic_pb2.RelTerm(term=term531)
        _t1060 = logic_pb2.RelTerm(term=term_3532)
        _t1061 = logic_pb2.RelTerm(term=term_4533)
        _t1062 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1059, _t1060, _t1061])
        return _t1062

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("-")
        _t1063 = self.parse_term()
        term534 = _t1063
        _t1064 = self.parse_term()
        term_3535 = _t1064
        _t1065 = self.parse_term()
        term_4536 = _t1065
        self.consume_literal(")")
        _t1066 = logic_pb2.RelTerm(term=term534)
        _t1067 = logic_pb2.RelTerm(term=term_3535)
        _t1068 = logic_pb2.RelTerm(term=term_4536)
        _t1069 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1066, _t1067, _t1068])
        return _t1069

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("*")
        _t1070 = self.parse_term()
        term537 = _t1070
        _t1071 = self.parse_term()
        term_3538 = _t1071
        _t1072 = self.parse_term()
        term_4539 = _t1072
        self.consume_literal(")")
        _t1073 = logic_pb2.RelTerm(term=term537)
        _t1074 = logic_pb2.RelTerm(term=term_3538)
        _t1075 = logic_pb2.RelTerm(term=term_4539)
        _t1076 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1073, _t1074, _t1075])
        return _t1076

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("/")
        _t1077 = self.parse_term()
        term540 = _t1077
        _t1078 = self.parse_term()
        term_3541 = _t1078
        _t1079 = self.parse_term()
        term_4542 = _t1079
        self.consume_literal(")")
        _t1080 = logic_pb2.RelTerm(term=term540)
        _t1081 = logic_pb2.RelTerm(term=term_3541)
        _t1082 = logic_pb2.RelTerm(term=term_4542)
        _t1083 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1080, _t1081, _t1082])
        return _t1083

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_literal("true", 0):
            _t1084 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1085 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1086 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1087 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1088 = 0
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1089 = 1
                            else:
                                if self.match_lookahead_terminal("SYMBOL", 0):
                                    _t1090 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1091 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1092 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1093 = 1
                                            else:
                                                if self.match_lookahead_terminal("FLOAT", 0):
                                                    _t1094 = 1
                                                else:
                                                    if self.match_lookahead_terminal("DECIMAL", 0):
                                                        _t1095 = 1
                                                    else:
                                                        _t1095 = -1
                                                    _t1094 = _t1095
                                                _t1093 = _t1094
                                            _t1092 = _t1093
                                        _t1091 = _t1092
                                    _t1090 = _t1091
                                _t1089 = _t1090
                            _t1088 = _t1089
                        _t1087 = _t1088
                    _t1086 = _t1087
                _t1085 = _t1086
            _t1084 = _t1085
        prediction543 = _t1084
        if prediction543 == 1:
            _t1097 = self.parse_term()
            term545 = _t1097
            _t1098 = logic_pb2.RelTerm(term=term545)
            _t1096 = _t1098
        else:
            if prediction543 == 0:
                _t1100 = self.parse_specialized_value()
                specialized_value544 = _t1100
                _t1101 = logic_pb2.RelTerm(specialized_value=specialized_value544)
                _t1099 = _t1101
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1096 = _t1099
        return _t1096

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal("#")
        _t1102 = self.parse_value()
        value546 = _t1102
        return value546

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1103 = self.parse_name()
        name547 = _t1103
        xs548 = []
        cond549 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond549:
            _t1104 = self.parse_rel_term()
            item550 = _t1104
            xs548.append(item550)
            cond549 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        rel_terms551 = xs548
        self.consume_literal(")")
        _t1105 = logic_pb2.RelAtom(name=name547, terms=rel_terms551)
        return _t1105

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1106 = self.parse_term()
        term552 = _t1106
        _t1107 = self.parse_term()
        term_3553 = _t1107
        self.consume_literal(")")
        _t1108 = logic_pb2.Cast(input=term552, result=term_3553)
        return _t1108

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs554 = []
        cond555 = self.match_lookahead_literal("(", 0)
        while cond555:
            _t1109 = self.parse_attribute()
            item556 = _t1109
            xs554.append(item556)
            cond555 = self.match_lookahead_literal("(", 0)
        attributes557 = xs554
        self.consume_literal(")")
        return attributes557

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1110 = self.parse_name()
        name558 = _t1110
        xs559 = []
        cond560 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond560:
            _t1111 = self.parse_value()
            item561 = _t1111
            xs559.append(item561)
            cond560 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        values562 = xs559
        self.consume_literal(")")
        _t1112 = logic_pb2.Attribute(name=name558, args=values562)
        return _t1112

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs563 = []
        cond564 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond564:
            _t1113 = self.parse_relation_id()
            item565 = _t1113
            xs563.append(item565)
            cond564 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids566 = xs563
        _t1114 = self.parse_script()
        script567 = _t1114
        self.consume_literal(")")
        _t1115 = logic_pb2.Algorithm(body=script567)
        getattr(_t1115, 'global').extend(relation_ids566)
        return _t1115

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal("(")
        self.consume_literal("script")
        xs568 = []
        cond569 = self.match_lookahead_literal("(", 0)
        while cond569:
            _t1116 = self.parse_construct()
            item570 = _t1116
            xs568.append(item570)
            cond569 = self.match_lookahead_literal("(", 0)
        constructs571 = xs568
        self.consume_literal(")")
        _t1117 = logic_pb2.Script(constructs=constructs571)
        return _t1117

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1119 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1120 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1121 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1122 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1123 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1124 = 1
                                else:
                                    _t1124 = -1
                                _t1123 = _t1124
                            _t1122 = _t1123
                        _t1121 = _t1122
                    _t1120 = _t1121
                _t1119 = _t1120
            _t1118 = _t1119
        else:
            _t1118 = -1
        prediction572 = _t1118
        if prediction572 == 1:
            _t1126 = self.parse_instruction()
            instruction574 = _t1126
            _t1127 = logic_pb2.Construct(instruction=instruction574)
            _t1125 = _t1127
        else:
            if prediction572 == 0:
                _t1129 = self.parse_loop()
                loop573 = _t1129
                _t1130 = logic_pb2.Construct(loop=loop573)
                _t1128 = _t1130
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1125 = _t1128
        return _t1125

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1131 = self.parse_init()
        init575 = _t1131
        _t1132 = self.parse_script()
        script576 = _t1132
        self.consume_literal(")")
        _t1133 = logic_pb2.Loop(init=init575, body=script576)
        return _t1133

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs577 = []
        cond578 = self.match_lookahead_literal("(", 0)
        while cond578:
            _t1134 = self.parse_instruction()
            item579 = _t1134
            xs577.append(item579)
            cond578 = self.match_lookahead_literal("(", 0)
        instructions580 = xs577
        self.consume_literal(")")
        return instructions580

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1136 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1137 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1138 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1139 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1140 = 0
                            else:
                                _t1140 = -1
                            _t1139 = _t1140
                        _t1138 = _t1139
                    _t1137 = _t1138
                _t1136 = _t1137
            _t1135 = _t1136
        else:
            _t1135 = -1
        prediction581 = _t1135
        if prediction581 == 4:
            _t1142 = self.parse_monus_def()
            monus_def586 = _t1142
            _t1143 = logic_pb2.Instruction(monus_def=monus_def586)
            _t1141 = _t1143
        else:
            if prediction581 == 3:
                _t1145 = self.parse_monoid_def()
                monoid_def585 = _t1145
                _t1146 = logic_pb2.Instruction(monoid_def=monoid_def585)
                _t1144 = _t1146
            else:
                if prediction581 == 2:
                    _t1148 = self.parse_break()
                    break584 = _t1148
                    _t1149 = logic_pb2.Instruction()
                    getattr(_t1149, 'break').CopyFrom(break584)
                    _t1147 = _t1149
                else:
                    if prediction581 == 1:
                        _t1151 = self.parse_upsert()
                        upsert583 = _t1151
                        _t1152 = logic_pb2.Instruction(upsert=upsert583)
                        _t1150 = _t1152
                    else:
                        if prediction581 == 0:
                            _t1154 = self.parse_assign()
                            assign582 = _t1154
                            _t1155 = logic_pb2.Instruction(assign=assign582)
                            _t1153 = _t1155
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1150 = _t1153
                    _t1147 = _t1150
                _t1144 = _t1147
            _t1141 = _t1144
        return _t1141

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1156 = self.parse_relation_id()
        relation_id587 = _t1156
        _t1157 = self.parse_abstraction()
        abstraction588 = _t1157
        if self.match_lookahead_literal("(", 0):
            _t1159 = self.parse_attrs()
            _t1158 = _t1159
        else:
            _t1158 = None
        attrs589 = _t1158
        self.consume_literal(")")
        _t1160 = logic_pb2.Assign(name=relation_id587, body=abstraction588, attrs=(attrs589 if attrs589 is not None else []))
        return _t1160

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1161 = self.parse_relation_id()
        relation_id590 = _t1161
        _t1162 = self.parse_abstraction_with_arity()
        abstraction_with_arity591 = _t1162
        if self.match_lookahead_literal("(", 0):
            _t1164 = self.parse_attrs()
            _t1163 = _t1164
        else:
            _t1163 = None
        attrs592 = _t1163
        self.consume_literal(")")
        _t1165 = logic_pb2.Upsert(name=relation_id590, body=abstraction_with_arity591[0], attrs=(attrs592 if attrs592 is not None else []), value_arity=abstraction_with_arity591[1])
        return _t1165

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1166 = self.parse_bindings()
        bindings593 = _t1166
        _t1167 = self.parse_formula()
        formula594 = _t1167
        self.consume_literal(")")
        _t1168 = logic_pb2.Abstraction(vars=(list(bindings593[0]) + list(bindings593[1] if bindings593[1] is not None else [])), value=formula594)
        return (_t1168, len(bindings593[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal("(")
        self.consume_literal("break")
        _t1169 = self.parse_relation_id()
        relation_id595 = _t1169
        _t1170 = self.parse_abstraction()
        abstraction596 = _t1170
        if self.match_lookahead_literal("(", 0):
            _t1172 = self.parse_attrs()
            _t1171 = _t1172
        else:
            _t1171 = None
        attrs597 = _t1171
        self.consume_literal(")")
        _t1173 = logic_pb2.Break(name=relation_id595, body=abstraction596, attrs=(attrs597 if attrs597 is not None else []))
        return _t1173

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1174 = self.parse_monoid()
        monoid598 = _t1174
        _t1175 = self.parse_relation_id()
        relation_id599 = _t1175
        _t1176 = self.parse_abstraction_with_arity()
        abstraction_with_arity600 = _t1176
        if self.match_lookahead_literal("(", 0):
            _t1178 = self.parse_attrs()
            _t1177 = _t1178
        else:
            _t1177 = None
        attrs601 = _t1177
        self.consume_literal(")")
        _t1179 = logic_pb2.MonoidDef(monoid=monoid598, name=relation_id599, body=abstraction_with_arity600[0], attrs=(attrs601 if attrs601 is not None else []), value_arity=abstraction_with_arity600[1])
        return _t1179

    def parse_monoid(self) -> logic_pb2.Monoid:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1181 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1182 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1183 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1184 = 2
                        else:
                            _t1184 = -1
                        _t1183 = _t1184
                    _t1182 = _t1183
                _t1181 = _t1182
            _t1180 = _t1181
        else:
            _t1180 = -1
        prediction602 = _t1180
        if prediction602 == 3:
            _t1186 = self.parse_sum_monoid()
            sum_monoid606 = _t1186
            _t1187 = logic_pb2.Monoid(sum_monoid=sum_monoid606)
            _t1185 = _t1187
        else:
            if prediction602 == 2:
                _t1189 = self.parse_max_monoid()
                max_monoid605 = _t1189
                _t1190 = logic_pb2.Monoid(max_monoid=max_monoid605)
                _t1188 = _t1190
            else:
                if prediction602 == 1:
                    _t1192 = self.parse_min_monoid()
                    min_monoid604 = _t1192
                    _t1193 = logic_pb2.Monoid(min_monoid=min_monoid604)
                    _t1191 = _t1193
                else:
                    if prediction602 == 0:
                        _t1195 = self.parse_or_monoid()
                        or_monoid603 = _t1195
                        _t1196 = logic_pb2.Monoid(or_monoid=or_monoid603)
                        _t1194 = _t1196
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1191 = _t1194
                _t1188 = _t1191
            _t1185 = _t1188
        return _t1185

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1197 = logic_pb2.OrMonoid()
        return _t1197

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        self.consume_literal("(")
        self.consume_literal("min")
        _t1198 = self.parse_type()
        type607 = _t1198
        self.consume_literal(")")
        _t1199 = logic_pb2.MinMonoid(type=type607)
        return _t1199

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        self.consume_literal("(")
        self.consume_literal("max")
        _t1200 = self.parse_type()
        type608 = _t1200
        self.consume_literal(")")
        _t1201 = logic_pb2.MaxMonoid(type=type608)
        return _t1201

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1202 = self.parse_type()
        type609 = _t1202
        self.consume_literal(")")
        _t1203 = logic_pb2.SumMonoid(type=type609)
        return _t1203

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1204 = self.parse_monoid()
        monoid610 = _t1204
        _t1205 = self.parse_relation_id()
        relation_id611 = _t1205
        _t1206 = self.parse_abstraction_with_arity()
        abstraction_with_arity612 = _t1206
        if self.match_lookahead_literal("(", 0):
            _t1208 = self.parse_attrs()
            _t1207 = _t1208
        else:
            _t1207 = None
        attrs613 = _t1207
        self.consume_literal(")")
        _t1209 = logic_pb2.MonusDef(monoid=monoid610, name=relation_id611, body=abstraction_with_arity612[0], attrs=(attrs613 if attrs613 is not None else []), value_arity=abstraction_with_arity612[1])
        return _t1209

    def parse_constraint(self) -> logic_pb2.Constraint:
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1210 = self.parse_relation_id()
        relation_id614 = _t1210
        _t1211 = self.parse_abstraction()
        abstraction615 = _t1211
        _t1212 = self.parse_functional_dependency_keys()
        functional_dependency_keys616 = _t1212
        _t1213 = self.parse_functional_dependency_values()
        functional_dependency_values617 = _t1213
        self.consume_literal(")")
        _t1214 = logic_pb2.FunctionalDependency(guard=abstraction615, keys=functional_dependency_keys616, values=functional_dependency_values617)
        _t1215 = logic_pb2.Constraint(name=relation_id614, functional_dependency=_t1214)
        return _t1215

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs618 = []
        cond619 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond619:
            _t1216 = self.parse_var()
            item620 = _t1216
            xs618.append(item620)
            cond619 = self.match_lookahead_terminal("SYMBOL", 0)
        vars621 = xs618
        self.consume_literal(")")
        return vars621

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs622 = []
        cond623 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond623:
            _t1217 = self.parse_var()
            item624 = _t1217
            xs622.append(item624)
            cond623 = self.match_lookahead_terminal("SYMBOL", 0)
        vars625 = xs622
        self.consume_literal(")")
        return vars625

    def parse_data(self) -> logic_pb2.Data:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("rel_edb", 1):
                _t1219 = 0
            else:
                if self.match_lookahead_literal("csv_data", 1):
                    _t1220 = 2
                else:
                    if self.match_lookahead_literal("betree_relation", 1):
                        _t1221 = 1
                    else:
                        _t1221 = -1
                    _t1220 = _t1221
                _t1219 = _t1220
            _t1218 = _t1219
        else:
            _t1218 = -1
        prediction626 = _t1218
        if prediction626 == 2:
            _t1223 = self.parse_csv_data()
            csv_data629 = _t1223
            _t1224 = logic_pb2.Data(csv_data=csv_data629)
            _t1222 = _t1224
        else:
            if prediction626 == 1:
                _t1226 = self.parse_betree_relation()
                betree_relation628 = _t1226
                _t1227 = logic_pb2.Data(betree_relation=betree_relation628)
                _t1225 = _t1227
            else:
                if prediction626 == 0:
                    _t1229 = self.parse_rel_edb()
                    rel_edb627 = _t1229
                    _t1230 = logic_pb2.Data(rel_edb=rel_edb627)
                    _t1228 = _t1230
                else:
                    raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t1225 = _t1228
            _t1222 = _t1225
        return _t1222

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        self.consume_literal("(")
        self.consume_literal("rel_edb")
        _t1231 = self.parse_relation_id()
        relation_id630 = _t1231
        _t1232 = self.parse_rel_edb_path()
        rel_edb_path631 = _t1232
        _t1233 = self.parse_rel_edb_types()
        rel_edb_types632 = _t1233
        self.consume_literal(")")
        _t1234 = logic_pb2.RelEDB(target_id=relation_id630, path=rel_edb_path631, types=rel_edb_types632)
        return _t1234

    def parse_rel_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs633 = []
        cond634 = self.match_lookahead_terminal("STRING", 0)
        while cond634:
            item635 = self.consume_terminal("STRING")
            xs633.append(item635)
            cond634 = self.match_lookahead_terminal("STRING", 0)
        strings636 = xs633
        self.consume_literal("]")
        return strings636

    def parse_rel_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs637 = []
        cond638 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond638:
            _t1235 = self.parse_type()
            item639 = _t1235
            xs637.append(item639)
            cond638 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types640 = xs637
        self.consume_literal("]")
        return types640

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1236 = self.parse_relation_id()
        relation_id641 = _t1236
        _t1237 = self.parse_betree_info()
        betree_info642 = _t1237
        self.consume_literal(")")
        _t1238 = logic_pb2.BeTreeRelation(name=relation_id641, relation_info=betree_info642)
        return _t1238

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1239 = self.parse_betree_info_key_types()
        betree_info_key_types643 = _t1239
        _t1240 = self.parse_betree_info_value_types()
        betree_info_value_types644 = _t1240
        _t1241 = self.parse_config_dict()
        config_dict645 = _t1241
        self.consume_literal(")")
        _t1242 = self.construct_betree_info(betree_info_key_types643, betree_info_value_types644, config_dict645)
        return _t1242

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs646 = []
        cond647 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond647:
            _t1243 = self.parse_type()
            item648 = _t1243
            xs646.append(item648)
            cond647 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types649 = xs646
        self.consume_literal(")")
        return types649

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs650 = []
        cond651 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond651:
            _t1244 = self.parse_type()
            item652 = _t1244
            xs650.append(item652)
            cond651 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types653 = xs650
        self.consume_literal(")")
        return types653

    def parse_csv_data(self) -> logic_pb2.CSVData:
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1245 = self.parse_csvlocator()
        csvlocator654 = _t1245
        _t1246 = self.parse_csv_config()
        csv_config655 = _t1246
        _t1247 = self.parse_csv_columns()
        csv_columns656 = _t1247
        _t1248 = self.parse_csv_asof()
        csv_asof657 = _t1248
        self.consume_literal(")")
        _t1249 = logic_pb2.CSVData(locator=csvlocator654, config=csv_config655, columns=csv_columns656, asof=csv_asof657)
        return _t1249

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1251 = self.parse_csv_locator_paths()
            _t1250 = _t1251
        else:
            _t1250 = None
        csv_locator_paths658 = _t1250
        if self.match_lookahead_literal("(", 0):
            _t1253 = self.parse_csv_locator_inline_data()
            _t1252 = _t1253
        else:
            _t1252 = None
        csv_locator_inline_data659 = _t1252
        self.consume_literal(")")
        _t1254 = logic_pb2.CSVLocator(paths=(csv_locator_paths658 if csv_locator_paths658 is not None else []), inline_data=(csv_locator_inline_data659 if csv_locator_inline_data659 is not None else "").encode())
        return _t1254

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs660 = []
        cond661 = self.match_lookahead_terminal("STRING", 0)
        while cond661:
            item662 = self.consume_terminal("STRING")
            xs660.append(item662)
            cond661 = self.match_lookahead_terminal("STRING", 0)
        strings663 = xs660
        self.consume_literal(")")
        return strings663

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string664 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string664

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1255 = self.parse_config_dict()
        config_dict665 = _t1255
        self.consume_literal(")")
        _t1256 = self.construct_csv_config(config_dict665)
        return _t1256

    def parse_csv_columns(self) -> Sequence[logic_pb2.CSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs666 = []
        cond667 = self.match_lookahead_literal("(", 0)
        while cond667:
            _t1257 = self.parse_csv_column()
            item668 = _t1257
            xs666.append(item668)
            cond667 = self.match_lookahead_literal("(", 0)
        csv_columns669 = xs666
        self.consume_literal(")")
        return csv_columns669

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        self.consume_literal("(")
        self.consume_literal("column")
        string670 = self.consume_terminal("STRING")
        _t1258 = self.parse_relation_id()
        relation_id671 = _t1258
        self.consume_literal("[")
        xs672 = []
        cond673 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond673:
            _t1259 = self.parse_type()
            item674 = _t1259
            xs672.append(item674)
            cond673 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types675 = xs672
        self.consume_literal("]")
        self.consume_literal(")")
        _t1260 = logic_pb2.CSVColumn(column_name=string670, target_id=relation_id671, types=types675)
        return _t1260

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string676 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string676

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1261 = self.parse_fragment_id()
        fragment_id677 = _t1261
        self.consume_literal(")")
        _t1262 = transactions_pb2.Undefine(fragment_id=fragment_id677)
        return _t1262

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal("(")
        self.consume_literal("context")
        xs678 = []
        cond679 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond679:
            _t1263 = self.parse_relation_id()
            item680 = _t1263
            xs678.append(item680)
            cond679 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids681 = xs678
        self.consume_literal(")")
        _t1264 = transactions_pb2.Context(relations=relation_ids681)
        return _t1264

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t1265 = self.parse_rel_edb_path()
        rel_edb_path682 = _t1265
        _t1266 = self.parse_relation_id()
        relation_id683 = _t1266
        self.consume_literal(")")
        _t1267 = transactions_pb2.Snapshot(destination_path=rel_edb_path682, source_relation=relation_id683)
        return _t1267

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs684 = []
        cond685 = self.match_lookahead_literal("(", 0)
        while cond685:
            _t1268 = self.parse_read()
            item686 = _t1268
            xs684.append(item686)
            cond685 = self.match_lookahead_literal("(", 0)
        reads687 = xs684
        self.consume_literal(")")
        return reads687

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1270 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1271 = 1
                else:
                    if self.match_lookahead_literal("export", 1):
                        _t1272 = 4
                    else:
                        if self.match_lookahead_literal("demand", 1):
                            _t1273 = 0
                        else:
                            if self.match_lookahead_literal("abort", 1):
                                _t1274 = 3
                            else:
                                _t1274 = -1
                            _t1273 = _t1274
                        _t1272 = _t1273
                    _t1271 = _t1272
                _t1270 = _t1271
            _t1269 = _t1270
        else:
            _t1269 = -1
        prediction688 = _t1269
        if prediction688 == 4:
            _t1276 = self.parse_export()
            export693 = _t1276
            _t1277 = transactions_pb2.Read(export=export693)
            _t1275 = _t1277
        else:
            if prediction688 == 3:
                _t1279 = self.parse_abort()
                abort692 = _t1279
                _t1280 = transactions_pb2.Read(abort=abort692)
                _t1278 = _t1280
            else:
                if prediction688 == 2:
                    _t1282 = self.parse_what_if()
                    what_if691 = _t1282
                    _t1283 = transactions_pb2.Read(what_if=what_if691)
                    _t1281 = _t1283
                else:
                    if prediction688 == 1:
                        _t1285 = self.parse_output()
                        output690 = _t1285
                        _t1286 = transactions_pb2.Read(output=output690)
                        _t1284 = _t1286
                    else:
                        if prediction688 == 0:
                            _t1288 = self.parse_demand()
                            demand689 = _t1288
                            _t1289 = transactions_pb2.Read(demand=demand689)
                            _t1287 = _t1289
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1284 = _t1287
                    _t1281 = _t1284
                _t1278 = _t1281
            _t1275 = _t1278
        return _t1275

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1290 = self.parse_relation_id()
        relation_id694 = _t1290
        self.consume_literal(")")
        _t1291 = transactions_pb2.Demand(relation_id=relation_id694)
        return _t1291

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal("(")
        self.consume_literal("output")
        _t1292 = self.parse_name()
        name695 = _t1292
        _t1293 = self.parse_relation_id()
        relation_id696 = _t1293
        self.consume_literal(")")
        _t1294 = transactions_pb2.Output(name=name695, relation_id=relation_id696)
        return _t1294

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t1295 = self.parse_name()
        name697 = _t1295
        _t1296 = self.parse_epoch()
        epoch698 = _t1296
        self.consume_literal(")")
        _t1297 = transactions_pb2.WhatIf(branch=name697, epoch=epoch698)
        return _t1297

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t1299 = self.parse_name()
            _t1298 = _t1299
        else:
            _t1298 = None
        name699 = _t1298
        _t1300 = self.parse_relation_id()
        relation_id700 = _t1300
        self.consume_literal(")")
        _t1301 = transactions_pb2.Abort(name=(name699 if name699 is not None else "abort"), relation_id=relation_id700)
        return _t1301

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal("(")
        self.consume_literal("export")
        _t1302 = self.parse_export_csv_config()
        export_csv_config701 = _t1302
        self.consume_literal(")")
        _t1303 = transactions_pb2.Export(csv_config=export_csv_config701)
        return _t1303

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal("(")
        self.consume_literal("export_csv_config")
        _t1304 = self.parse_export_csv_path()
        export_csv_path702 = _t1304
        _t1305 = self.parse_export_csv_columns()
        export_csv_columns703 = _t1305
        _t1306 = self.parse_config_dict()
        config_dict704 = _t1306
        self.consume_literal(")")
        _t1307 = self.export_csv_config(export_csv_path702, export_csv_columns703, config_dict704)
        return _t1307

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string705 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string705

    def parse_export_csv_columns(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs706 = []
        cond707 = self.match_lookahead_literal("(", 0)
        while cond707:
            _t1308 = self.parse_export_csv_column()
            item708 = _t1308
            xs706.append(item708)
            cond707 = self.match_lookahead_literal("(", 0)
        export_csv_columns709 = xs706
        self.consume_literal(")")
        return export_csv_columns709

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal("(")
        self.consume_literal("column")
        string710 = self.consume_terminal("STRING")
        _t1309 = self.parse_relation_id()
        relation_id711 = _t1309
        self.consume_literal(")")
        _t1310 = transactions_pb2.ExportCSVColumn(column_name=string710, column_data=relation_id711)
        return _t1310


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
