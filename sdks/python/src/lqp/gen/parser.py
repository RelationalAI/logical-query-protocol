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


class Lexer:
    """Tokenizer for the input."""

    def __init__(self, input_str: str):
        self.input = input_str
        self.pos = 0
        self.tokens: List[Token] = []
        self._tokenize()

    def _tokenize(self) -> None:
        """Tokenize the input string."""
        token_specs = [
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
            (
                "DECIMAL",
                re.compile(r"[-]?\d+\.\d+d\d+"),
                lambda x: Lexer.scan_decimal(x),
            ),
            (
                "FLOAT",
                re.compile(r"[-]?\d+\.\d+|inf|nan"),
                lambda x: Lexer.scan_float(x),
            ),
            ("INT", re.compile(r"[-]?\d+"), lambda x: Lexer.scan_int(x)),
            ("INT128", re.compile(r"[-]?\d+i128"), lambda x: Lexer.scan_int128(x)),
            (
                "STRING",
                re.compile(r'"(?:[^"\\]|\\.)*"'),
                lambda x: Lexer.scan_string(x),
            ),
            (
                "SYMBOL",
                re.compile(r"[a-zA-Z_][a-zA-Z0-9_.-]*"),
                lambda x: Lexer.scan_symbol(x),
            ),
            ("UINT128", re.compile(r"0x[0-9a-fA-F]+"), lambda x: Lexer.scan_uint128(x)),
        ]

        whitespace_re = re.compile(r"\s+")
        comment_re = re.compile(r";;.*")

        while self.pos < len(self.input):
            match = whitespace_re.match(self.input, self.pos)
            if match:
                self.pos = match.end()
                continue

            match = comment_re.match(self.input, self.pos)
            if match:
                self.pos = match.end()
                continue

            # Collect all matching tokens
            candidates = []

            for token_type, regex, action in token_specs:
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
    def scan_colon_symbol(s: str) -> str:
        """Parse COLON_SYMBOL token."""
        return s[1:]

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
        val = int(hashlib.sha256(name.encode()).hexdigest()[:16], 16)
        id_low = val & 0xFFFFFFFFFFFFFFFF
        id_high = (val >> 64) & 0xFFFFFFFFFFFFFFFF
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
            _t1855 = value.HasField("int_value")
        else:
            _t1855 = False
        if _t1855:
            assert value is not None
            return int(value.int_value)
        else:
            _t1856 = None
        return int(default)

    def _extract_value_int64(self, value: Optional[logic_pb2.Value], default: int) -> int:
        if value is not None:
            assert value is not None
            _t1857 = value.HasField("int_value")
        else:
            _t1857 = False
        if _t1857:
            assert value is not None
            return value.int_value
        else:
            _t1858 = None
        return default

    def _extract_value_string(self, value: Optional[logic_pb2.Value], default: str) -> str:
        if value is not None:
            assert value is not None
            _t1859 = value.HasField("string_value")
        else:
            _t1859 = False
        if _t1859:
            assert value is not None
            return value.string_value
        else:
            _t1860 = None
        return default

    def _extract_value_boolean(self, value: Optional[logic_pb2.Value], default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t1861 = value.HasField("boolean_value")
        else:
            _t1861 = False
        if _t1861:
            assert value is not None
            return value.boolean_value
        else:
            _t1862 = None
        return default

    def _extract_value_string_list(self, value: Optional[logic_pb2.Value], default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t1863 = value.HasField("string_value")
        else:
            _t1863 = False
        if _t1863:
            assert value is not None
            return [value.string_value]
        else:
            _t1864 = None
        return default

    def _try_extract_value_int64(self, value: Optional[logic_pb2.Value]) -> Optional[int]:
        if value is not None:
            assert value is not None
            _t1865 = value.HasField("int_value")
        else:
            _t1865 = False
        if _t1865:
            assert value is not None
            return value.int_value
        else:
            _t1866 = None
        return None

    def _try_extract_value_float64(self, value: Optional[logic_pb2.Value]) -> Optional[float]:
        if value is not None:
            assert value is not None
            _t1867 = value.HasField("float_value")
        else:
            _t1867 = False
        if _t1867:
            assert value is not None
            return value.float_value
        else:
            _t1868 = None
        return None

    def _try_extract_value_bytes(self, value: Optional[logic_pb2.Value]) -> Optional[bytes]:
        if value is not None:
            assert value is not None
            _t1869 = value.HasField("string_value")
        else:
            _t1869 = False
        if _t1869:
            assert value is not None
            return value.string_value.encode()
        else:
            _t1870 = None
        return None

    def _try_extract_value_uint128(self, value: Optional[logic_pb2.Value]) -> Optional[logic_pb2.UInt128Value]:
        if value is not None:
            assert value is not None
            _t1871 = value.HasField("uint128_value")
        else:
            _t1871 = False
        if _t1871:
            assert value is not None
            return value.uint128_value
        else:
            _t1872 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1873 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t1873
        _t1874 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t1874
        _t1875 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t1875
        _t1876 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t1876
        _t1877 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t1877
        _t1878 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t1878
        _t1879 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t1879
        _t1880 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t1880
        _t1881 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t1881
        _t1882 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t1882
        _t1883 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t1883
        _t1884 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t1884

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1885 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t1885
        _t1886 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t1886
        _t1887 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t1887
        _t1888 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t1888
        _t1889 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1889
        _t1890 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t1890
        _t1891 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t1891
        _t1892 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t1892
        _t1893 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t1893
        _t1894 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1894
        _t1895 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1895

    def default_configure(self) -> transactions_pb2.Configure:
        _t1896 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1896
        _t1897 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1897

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
        _t1898 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1898
        _t1899 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t1899
        _t1900 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1900

    def export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1901 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t1901
        _t1902 = self._extract_value_string(config.get("compression"), "")
        compression = _t1902
        _t1903 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t1903
        _t1904 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t1904
        _t1905 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t1905
        _t1906 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t1906
        _t1907 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t1907
        _t1908 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1908

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1264 = self.parse_configure()
            _t1263 = _t1264
        else:
            _t1263 = None
        configure910 = _t1263
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1266 = self.parse_sync()
            _t1265 = _t1266
        else:
            _t1265 = None
        sync911 = _t1265
        xs912 = []
        cond913 = self.match_lookahead_literal("(", 0)
        while cond913:
            _t1267 = self.parse_epoch()
            item914 = _t1267
            xs912.append(item914)
            cond913 = self.match_lookahead_literal("(", 0)
        epochs915 = xs912
        self.consume_literal(")")
        _t1268 = self.default_configure()
        _t1269 = transactions_pb2.Transaction(epochs=epochs915, configure=(configure910 if configure910 is not None else _t1268), sync=sync911)
        return _t1269

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1270 = self.parse_config_dict()
        config_dict916 = _t1270
        self.consume_literal(")")
        _t1271 = self.construct_configure(config_dict916)
        return _t1271

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs917 = []
        cond918 = self.match_lookahead_literal(":", 0)
        while cond918:
            _t1272 = self.parse_config_key_value()
            item919 = _t1272
            xs917.append(item919)
            cond918 = self.match_lookahead_literal(":", 0)
        config_key_values920 = xs917
        self.consume_literal("}")
        return config_key_values920

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol921 = self.consume_terminal("SYMBOL")
        _t1273 = self.parse_value()
        value922 = _t1273
        return (symbol921, value922,)

    def parse_value(self) -> logic_pb2.Value:
        if self.match_lookahead_literal("true", 0):
            _t1274 = 9
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1275 = 8
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1276 = 9
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1278 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1279 = 0
                            else:
                                _t1279 = -1
                            _t1278 = _t1279
                        _t1277 = _t1278
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t1280 = 5
                        else:
                            if self.match_lookahead_terminal("STRING", 0):
                                _t1281 = 2
                            else:
                                if self.match_lookahead_terminal("INT128", 0):
                                    _t1282 = 6
                                else:
                                    if self.match_lookahead_terminal("INT", 0):
                                        _t1283 = 3
                                    else:
                                        if self.match_lookahead_terminal("FLOAT", 0):
                                            _t1284 = 4
                                        else:
                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                _t1285 = 7
                                            else:
                                                _t1285 = -1
                                            _t1284 = _t1285
                                        _t1283 = _t1284
                                    _t1282 = _t1283
                                _t1281 = _t1282
                            _t1280 = _t1281
                        _t1277 = _t1280
                    _t1276 = _t1277
                _t1275 = _t1276
            _t1274 = _t1275
        prediction923 = _t1274
        if prediction923 == 9:
            _t1287 = self.parse_boolean_value()
            boolean_value932 = _t1287
            _t1288 = logic_pb2.Value(boolean_value=boolean_value932)
            _t1286 = _t1288
        else:
            if prediction923 == 8:
                self.consume_literal("missing")
                _t1290 = logic_pb2.MissingValue()
                _t1291 = logic_pb2.Value(missing_value=_t1290)
                _t1289 = _t1291
            else:
                if prediction923 == 7:
                    decimal931 = self.consume_terminal("DECIMAL")
                    _t1293 = logic_pb2.Value(decimal_value=decimal931)
                    _t1292 = _t1293
                else:
                    if prediction923 == 6:
                        int128930 = self.consume_terminal("INT128")
                        _t1295 = logic_pb2.Value(int128_value=int128930)
                        _t1294 = _t1295
                    else:
                        if prediction923 == 5:
                            uint128929 = self.consume_terminal("UINT128")
                            _t1297 = logic_pb2.Value(uint128_value=uint128929)
                            _t1296 = _t1297
                        else:
                            if prediction923 == 4:
                                float928 = self.consume_terminal("FLOAT")
                                _t1299 = logic_pb2.Value(float_value=float928)
                                _t1298 = _t1299
                            else:
                                if prediction923 == 3:
                                    int927 = self.consume_terminal("INT")
                                    _t1301 = logic_pb2.Value(int_value=int927)
                                    _t1300 = _t1301
                                else:
                                    if prediction923 == 2:
                                        string926 = self.consume_terminal("STRING")
                                        _t1303 = logic_pb2.Value(string_value=string926)
                                        _t1302 = _t1303
                                    else:
                                        if prediction923 == 1:
                                            _t1305 = self.parse_datetime()
                                            datetime925 = _t1305
                                            _t1306 = logic_pb2.Value(datetime_value=datetime925)
                                            _t1304 = _t1306
                                        else:
                                            if prediction923 == 0:
                                                _t1308 = self.parse_date()
                                                date924 = _t1308
                                                _t1309 = logic_pb2.Value(date_value=date924)
                                                _t1307 = _t1309
                                            else:
                                                raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1304 = _t1307
                                        _t1302 = _t1304
                                    _t1300 = _t1302
                                _t1298 = _t1300
                            _t1296 = _t1298
                        _t1294 = _t1296
                    _t1292 = _t1294
                _t1289 = _t1292
            _t1286 = _t1289
        return _t1286

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal("(")
        self.consume_literal("date")
        int933 = self.consume_terminal("INT")
        int_3934 = self.consume_terminal("INT")
        int_4935 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1310 = logic_pb2.DateValue(year=int(int933), month=int(int_3934), day=int(int_4935))
        return _t1310

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        self.consume_literal("(")
        self.consume_literal("datetime")
        int936 = self.consume_terminal("INT")
        int_3937 = self.consume_terminal("INT")
        int_4938 = self.consume_terminal("INT")
        int_5939 = self.consume_terminal("INT")
        int_6940 = self.consume_terminal("INT")
        int_7941 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1311 = self.consume_terminal("INT")
        else:
            _t1311 = None
        int_8942 = _t1311
        self.consume_literal(")")
        _t1312 = logic_pb2.DateTimeValue(year=int(int936), month=int(int_3937), day=int(int_4938), hour=int(int_5939), minute=int(int_6940), second=int(int_7941), microsecond=int((int_8942 if int_8942 is not None else 0)))
        return _t1312

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1313 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1314 = 1
            else:
                _t1314 = -1
            _t1313 = _t1314
        prediction943 = _t1313
        if prediction943 == 1:
            self.consume_literal("false")
            _t1315 = False
        else:
            if prediction943 == 0:
                self.consume_literal("true")
                _t1316 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1315 = _t1316
        return _t1315

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal("(")
        self.consume_literal("sync")
        xs944 = []
        cond945 = self.match_lookahead_literal(":", 0)
        while cond945:
            _t1317 = self.parse_fragment_id()
            item946 = _t1317
            xs944.append(item946)
            cond945 = self.match_lookahead_literal(":", 0)
        fragment_ids947 = xs944
        self.consume_literal(")")
        _t1318 = transactions_pb2.Sync(fragments=fragment_ids947)
        return _t1318

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        self.consume_literal(":")
        symbol948 = self.consume_terminal("SYMBOL")
        return fragments_pb2.FragmentId(id=symbol948.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1320 = self.parse_epoch_writes()
            _t1319 = _t1320
        else:
            _t1319 = None
        epoch_writes949 = _t1319
        if self.match_lookahead_literal("(", 0):
            _t1322 = self.parse_epoch_reads()
            _t1321 = _t1322
        else:
            _t1321 = None
        epoch_reads950 = _t1321
        self.consume_literal(")")
        _t1323 = transactions_pb2.Epoch(writes=(epoch_writes949 if epoch_writes949 is not None else []), reads=(epoch_reads950 if epoch_reads950 is not None else []))
        return _t1323

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs951 = []
        cond952 = self.match_lookahead_literal("(", 0)
        while cond952:
            _t1324 = self.parse_write()
            item953 = _t1324
            xs951.append(item953)
            cond952 = self.match_lookahead_literal("(", 0)
        writes954 = xs951
        self.consume_literal(")")
        return writes954

    def parse_write(self) -> transactions_pb2.Write:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1326 = 1
            else:
                if self.match_lookahead_literal("define", 1):
                    _t1327 = 0
                else:
                    if self.match_lookahead_literal("context", 1):
                        _t1328 = 2
                    else:
                        _t1328 = -1
                    _t1327 = _t1328
                _t1326 = _t1327
            _t1325 = _t1326
        else:
            _t1325 = -1
        prediction955 = _t1325
        if prediction955 == 2:
            _t1330 = self.parse_context()
            context958 = _t1330
            _t1331 = transactions_pb2.Write(context=context958)
            _t1329 = _t1331
        else:
            if prediction955 == 1:
                _t1333 = self.parse_undefine()
                undefine957 = _t1333
                _t1334 = transactions_pb2.Write(undefine=undefine957)
                _t1332 = _t1334
            else:
                if prediction955 == 0:
                    _t1336 = self.parse_define()
                    define956 = _t1336
                    _t1337 = transactions_pb2.Write(define=define956)
                    _t1335 = _t1337
                else:
                    raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t1332 = _t1335
            _t1329 = _t1332
        return _t1329

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal("(")
        self.consume_literal("define")
        _t1338 = self.parse_fragment()
        fragment959 = _t1338
        self.consume_literal(")")
        _t1339 = transactions_pb2.Define(fragment=fragment959)
        return _t1339

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1340 = self.parse_new_fragment_id()
        new_fragment_id960 = _t1340
        xs961 = []
        cond962 = self.match_lookahead_literal("(", 0)
        while cond962:
            _t1341 = self.parse_declaration()
            item963 = _t1341
            xs961.append(item963)
            cond962 = self.match_lookahead_literal("(", 0)
        declarations964 = xs961
        self.consume_literal(")")
        return self.construct_fragment(new_fragment_id960, declarations964)

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        _t1342 = self.parse_fragment_id()
        fragment_id965 = _t1342
        self.start_fragment(fragment_id965)
        return fragment_id965

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("rel_edb", 1):
                _t1344 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1345 = 2
                else:
                    if self.match_lookahead_literal("def", 1):
                        _t1346 = 0
                    else:
                        if self.match_lookahead_literal("csv_data", 1):
                            _t1347 = 3
                        else:
                            if self.match_lookahead_literal("betree_relation", 1):
                                _t1348 = 3
                            else:
                                if self.match_lookahead_literal("algorithm", 1):
                                    _t1349 = 1
                                else:
                                    _t1349 = -1
                                _t1348 = _t1349
                            _t1347 = _t1348
                        _t1346 = _t1347
                    _t1345 = _t1346
                _t1344 = _t1345
            _t1343 = _t1344
        else:
            _t1343 = -1
        prediction966 = _t1343
        if prediction966 == 3:
            _t1351 = self.parse_data()
            data970 = _t1351
            _t1352 = logic_pb2.Declaration(data=data970)
            _t1350 = _t1352
        else:
            if prediction966 == 2:
                _t1354 = self.parse_constraint()
                constraint969 = _t1354
                _t1355 = logic_pb2.Declaration(constraint=constraint969)
                _t1353 = _t1355
            else:
                if prediction966 == 1:
                    _t1357 = self.parse_algorithm()
                    algorithm968 = _t1357
                    _t1358 = logic_pb2.Declaration(algorithm=algorithm968)
                    _t1356 = _t1358
                else:
                    if prediction966 == 0:
                        _t1360 = self.parse_def()
                        def967 = _t1360
                        _t1361 = logic_pb2.Declaration()
                        getattr(_t1361, 'def').CopyFrom(def967)
                        _t1359 = _t1361
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1356 = _t1359
                _t1353 = _t1356
            _t1350 = _t1353
        return _t1350

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal("(")
        self.consume_literal("def")
        _t1362 = self.parse_relation_id()
        relation_id971 = _t1362
        _t1363 = self.parse_abstraction()
        abstraction972 = _t1363
        if self.match_lookahead_literal("(", 0):
            _t1365 = self.parse_attrs()
            _t1364 = _t1365
        else:
            _t1364 = None
        attrs973 = _t1364
        self.consume_literal(")")
        _t1366 = logic_pb2.Def(name=relation_id971, body=abstraction972, attrs=(attrs973 if attrs973 is not None else []))
        return _t1366

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_literal(":", 0):
            _t1367 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1368 = 1
            else:
                _t1368 = -1
            _t1367 = _t1368
        prediction974 = _t1367
        if prediction974 == 1:
            uint128976 = self.consume_terminal("UINT128")
            _t1369 = logic_pb2.RelationId(id_low=uint128976.low, id_high=uint128976.high)
        else:
            if prediction974 == 0:
                self.consume_literal(":")
                symbol975 = self.consume_terminal("SYMBOL")
                _t1370 = self.relation_id_from_string(symbol975)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1369 = _t1370
        return _t1369

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal("(")
        _t1371 = self.parse_bindings()
        bindings977 = _t1371
        _t1372 = self.parse_formula()
        formula978 = _t1372
        self.consume_literal(")")
        _t1373 = logic_pb2.Abstraction(vars=(list(bindings977[0]) + list(bindings977[1] if bindings977[1] is not None else [])), value=formula978)
        return _t1373

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs979 = []
        cond980 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond980:
            _t1374 = self.parse_binding()
            item981 = _t1374
            xs979.append(item981)
            cond980 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings982 = xs979
        if self.match_lookahead_literal("|", 0):
            _t1376 = self.parse_value_bindings()
            _t1375 = _t1376
        else:
            _t1375 = None
        value_bindings983 = _t1375
        self.consume_literal("]")
        return (bindings982, (value_bindings983 if value_bindings983 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol984 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1377 = self.parse_type()
        type985 = _t1377
        _t1378 = logic_pb2.Var(name=symbol984)
        _t1379 = logic_pb2.Binding(var=_t1378, type=type985)
        return _t1379

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1380 = 0
        else:
            if self.match_lookahead_literal("UINT128", 0):
                _t1381 = 4
            else:
                if self.match_lookahead_literal("STRING", 0):
                    _t1382 = 1
                else:
                    if self.match_lookahead_literal("MISSING", 0):
                        _t1383 = 8
                    else:
                        if self.match_lookahead_literal("INT128", 0):
                            _t1384 = 5
                        else:
                            if self.match_lookahead_literal("INT", 0):
                                _t1385 = 2
                            else:
                                if self.match_lookahead_literal("FLOAT", 0):
                                    _t1386 = 3
                                else:
                                    if self.match_lookahead_literal("DATETIME", 0):
                                        _t1387 = 7
                                    else:
                                        if self.match_lookahead_literal("DATE", 0):
                                            _t1388 = 6
                                        else:
                                            if self.match_lookahead_literal("BOOLEAN", 0):
                                                _t1389 = 10
                                            else:
                                                if self.match_lookahead_literal("(", 0):
                                                    _t1390 = 9
                                                else:
                                                    _t1390 = -1
                                                _t1389 = _t1390
                                            _t1388 = _t1389
                                        _t1387 = _t1388
                                    _t1386 = _t1387
                                _t1385 = _t1386
                            _t1384 = _t1385
                        _t1383 = _t1384
                    _t1382 = _t1383
                _t1381 = _t1382
            _t1380 = _t1381
        prediction986 = _t1380
        if prediction986 == 10:
            _t1392 = self.parse_boolean_type()
            boolean_type997 = _t1392
            _t1393 = logic_pb2.Type(boolean_type=boolean_type997)
            _t1391 = _t1393
        else:
            if prediction986 == 9:
                _t1395 = self.parse_decimal_type()
                decimal_type996 = _t1395
                _t1396 = logic_pb2.Type(decimal_type=decimal_type996)
                _t1394 = _t1396
            else:
                if prediction986 == 8:
                    _t1398 = self.parse_missing_type()
                    missing_type995 = _t1398
                    _t1399 = logic_pb2.Type(missing_type=missing_type995)
                    _t1397 = _t1399
                else:
                    if prediction986 == 7:
                        _t1401 = self.parse_datetime_type()
                        datetime_type994 = _t1401
                        _t1402 = logic_pb2.Type(datetime_type=datetime_type994)
                        _t1400 = _t1402
                    else:
                        if prediction986 == 6:
                            _t1404 = self.parse_date_type()
                            date_type993 = _t1404
                            _t1405 = logic_pb2.Type(date_type=date_type993)
                            _t1403 = _t1405
                        else:
                            if prediction986 == 5:
                                _t1407 = self.parse_int128_type()
                                int128_type992 = _t1407
                                _t1408 = logic_pb2.Type(int128_type=int128_type992)
                                _t1406 = _t1408
                            else:
                                if prediction986 == 4:
                                    _t1410 = self.parse_uint128_type()
                                    uint128_type991 = _t1410
                                    _t1411 = logic_pb2.Type(uint128_type=uint128_type991)
                                    _t1409 = _t1411
                                else:
                                    if prediction986 == 3:
                                        _t1413 = self.parse_float_type()
                                        float_type990 = _t1413
                                        _t1414 = logic_pb2.Type(float_type=float_type990)
                                        _t1412 = _t1414
                                    else:
                                        if prediction986 == 2:
                                            _t1416 = self.parse_int_type()
                                            int_type989 = _t1416
                                            _t1417 = logic_pb2.Type(int_type=int_type989)
                                            _t1415 = _t1417
                                        else:
                                            if prediction986 == 1:
                                                _t1419 = self.parse_string_type()
                                                string_type988 = _t1419
                                                _t1420 = logic_pb2.Type(string_type=string_type988)
                                                _t1418 = _t1420
                                            else:
                                                if prediction986 == 0:
                                                    _t1422 = self.parse_unspecified_type()
                                                    unspecified_type987 = _t1422
                                                    _t1423 = logic_pb2.Type(unspecified_type=unspecified_type987)
                                                    _t1421 = _t1423
                                                else:
                                                    raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t1418 = _t1421
                                            _t1415 = _t1418
                                        _t1412 = _t1415
                                    _t1409 = _t1412
                                _t1406 = _t1409
                            _t1403 = _t1406
                        _t1400 = _t1403
                    _t1397 = _t1400
                _t1394 = _t1397
            _t1391 = _t1394
        return _t1391

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        self.consume_literal("UNKNOWN")
        _t1424 = logic_pb2.UnspecifiedType()
        return _t1424

    def parse_string_type(self) -> logic_pb2.StringType:
        self.consume_literal("STRING")
        _t1425 = logic_pb2.StringType()
        return _t1425

    def parse_int_type(self) -> logic_pb2.IntType:
        self.consume_literal("INT")
        _t1426 = logic_pb2.IntType()
        return _t1426

    def parse_float_type(self) -> logic_pb2.FloatType:
        self.consume_literal("FLOAT")
        _t1427 = logic_pb2.FloatType()
        return _t1427

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        self.consume_literal("UINT128")
        _t1428 = logic_pb2.UInt128Type()
        return _t1428

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        self.consume_literal("INT128")
        _t1429 = logic_pb2.Int128Type()
        return _t1429

    def parse_date_type(self) -> logic_pb2.DateType:
        self.consume_literal("DATE")
        _t1430 = logic_pb2.DateType()
        return _t1430

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        self.consume_literal("DATETIME")
        _t1431 = logic_pb2.DateTimeType()
        return _t1431

    def parse_missing_type(self) -> logic_pb2.MissingType:
        self.consume_literal("MISSING")
        _t1432 = logic_pb2.MissingType()
        return _t1432

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int998 = self.consume_terminal("INT")
        int_3999 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1433 = logic_pb2.DecimalType(precision=int(int998), scale=int(int_3999))
        return _t1433

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal("BOOLEAN")
        _t1434 = logic_pb2.BooleanType()
        return _t1434

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs1000 = []
        cond1001 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1001:
            _t1435 = self.parse_binding()
            item1002 = _t1435
            xs1000.append(item1002)
            cond1001 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings1003 = xs1000
        return bindings1003

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1437 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1438 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1439 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1440 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1441 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1442 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1443 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1444 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1445 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1446 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1447 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1448 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1449 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1450 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1451 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1452 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1453 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1454 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1455 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1456 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1457 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1458 = 10
                                                                                                else:
                                                                                                    _t1458 = -1
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
                                    _t1442 = _t1443
                                _t1441 = _t1442
                            _t1440 = _t1441
                        _t1439 = _t1440
                    _t1438 = _t1439
                _t1437 = _t1438
            _t1436 = _t1437
        else:
            _t1436 = -1
        prediction1004 = _t1436
        if prediction1004 == 12:
            _t1460 = self.parse_cast()
            cast1017 = _t1460
            _t1461 = logic_pb2.Formula(cast=cast1017)
            _t1459 = _t1461
        else:
            if prediction1004 == 11:
                _t1463 = self.parse_rel_atom()
                rel_atom1016 = _t1463
                _t1464 = logic_pb2.Formula(rel_atom=rel_atom1016)
                _t1462 = _t1464
            else:
                if prediction1004 == 10:
                    _t1466 = self.parse_primitive()
                    primitive1015 = _t1466
                    _t1467 = logic_pb2.Formula(primitive=primitive1015)
                    _t1465 = _t1467
                else:
                    if prediction1004 == 9:
                        _t1469 = self.parse_pragma()
                        pragma1014 = _t1469
                        _t1470 = logic_pb2.Formula(pragma=pragma1014)
                        _t1468 = _t1470
                    else:
                        if prediction1004 == 8:
                            _t1472 = self.parse_atom()
                            atom1013 = _t1472
                            _t1473 = logic_pb2.Formula(atom=atom1013)
                            _t1471 = _t1473
                        else:
                            if prediction1004 == 7:
                                _t1475 = self.parse_ffi()
                                ffi1012 = _t1475
                                _t1476 = logic_pb2.Formula(ffi=ffi1012)
                                _t1474 = _t1476
                            else:
                                if prediction1004 == 6:
                                    _t1478 = self.parse_not()
                                    not1011 = _t1478
                                    _t1479 = logic_pb2.Formula()
                                    getattr(_t1479, 'not').CopyFrom(not1011)
                                    _t1477 = _t1479
                                else:
                                    if prediction1004 == 5:
                                        _t1481 = self.parse_disjunction()
                                        disjunction1010 = _t1481
                                        _t1482 = logic_pb2.Formula(disjunction=disjunction1010)
                                        _t1480 = _t1482
                                    else:
                                        if prediction1004 == 4:
                                            _t1484 = self.parse_conjunction()
                                            conjunction1009 = _t1484
                                            _t1485 = logic_pb2.Formula(conjunction=conjunction1009)
                                            _t1483 = _t1485
                                        else:
                                            if prediction1004 == 3:
                                                _t1487 = self.parse_reduce()
                                                reduce1008 = _t1487
                                                _t1488 = logic_pb2.Formula(reduce=reduce1008)
                                                _t1486 = _t1488
                                            else:
                                                if prediction1004 == 2:
                                                    _t1490 = self.parse_exists()
                                                    exists1007 = _t1490
                                                    _t1491 = logic_pb2.Formula(exists=exists1007)
                                                    _t1489 = _t1491
                                                else:
                                                    if prediction1004 == 1:
                                                        _t1493 = self.parse_false()
                                                        false1006 = _t1493
                                                        _t1494 = logic_pb2.Formula(disjunction=false1006)
                                                        _t1492 = _t1494
                                                    else:
                                                        if prediction1004 == 0:
                                                            _t1496 = self.parse_true()
                                                            true1005 = _t1496
                                                            _t1497 = logic_pb2.Formula(conjunction=true1005)
                                                            _t1495 = _t1497
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1492 = _t1495
                                                    _t1489 = _t1492
                                                _t1486 = _t1489
                                            _t1483 = _t1486
                                        _t1480 = _t1483
                                    _t1477 = _t1480
                                _t1474 = _t1477
                            _t1471 = _t1474
                        _t1468 = _t1471
                    _t1465 = _t1468
                _t1462 = _t1465
            _t1459 = _t1462
        return _t1459

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1498 = logic_pb2.Conjunction(args=[])
        return _t1498

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1499 = logic_pb2.Disjunction(args=[])
        return _t1499

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1500 = self.parse_bindings()
        bindings1018 = _t1500
        _t1501 = self.parse_formula()
        formula1019 = _t1501
        self.consume_literal(")")
        _t1502 = logic_pb2.Abstraction(vars=(list(bindings1018[0]) + list(bindings1018[1] if bindings1018[1] is not None else [])), value=formula1019)
        _t1503 = logic_pb2.Exists(body=_t1502)
        return _t1503

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1504 = self.parse_abstraction()
        abstraction1020 = _t1504
        _t1505 = self.parse_abstraction()
        abstraction_31021 = _t1505
        _t1506 = self.parse_terms()
        terms1022 = _t1506
        self.consume_literal(")")
        _t1507 = logic_pb2.Reduce(op=abstraction1020, body=abstraction_31021, terms=terms1022)
        return _t1507

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs1023 = []
        cond1024 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond1024:
            _t1508 = self.parse_term()
            item1025 = _t1508
            xs1023.append(item1025)
            cond1024 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms1026 = xs1023
        self.consume_literal(")")
        return terms1026

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_literal("true", 0):
            _t1509 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1510 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1511 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1512 = 1
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t1513 = 1
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1514 = 0
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1515 = 1
                                else:
                                    if self.match_lookahead_terminal("INT128", 0):
                                        _t1516 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT", 0):
                                            _t1517 = 1
                                        else:
                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                _t1518 = 1
                                            else:
                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                    _t1519 = 1
                                                else:
                                                    _t1519 = -1
                                                _t1518 = _t1519
                                            _t1517 = _t1518
                                        _t1516 = _t1517
                                    _t1515 = _t1516
                                _t1514 = _t1515
                            _t1513 = _t1514
                        _t1512 = _t1513
                    _t1511 = _t1512
                _t1510 = _t1511
            _t1509 = _t1510
        prediction1027 = _t1509
        if prediction1027 == 1:
            _t1521 = self.parse_constant()
            constant1029 = _t1521
            _t1522 = logic_pb2.Term(constant=constant1029)
            _t1520 = _t1522
        else:
            if prediction1027 == 0:
                _t1524 = self.parse_var()
                var1028 = _t1524
                _t1525 = logic_pb2.Term(var=var1028)
                _t1523 = _t1525
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1520 = _t1523
        return _t1520

    def parse_var(self) -> logic_pb2.Var:
        symbol1030 = self.consume_terminal("SYMBOL")
        _t1526 = logic_pb2.Var(name=symbol1030)
        return _t1526

    def parse_constant(self) -> logic_pb2.Value:
        _t1527 = self.parse_value()
        value1031 = _t1527
        return value1031

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal("(")
        self.consume_literal("and")
        xs1032 = []
        cond1033 = self.match_lookahead_literal("(", 0)
        while cond1033:
            _t1528 = self.parse_formula()
            item1034 = _t1528
            xs1032.append(item1034)
            cond1033 = self.match_lookahead_literal("(", 0)
        formulas1035 = xs1032
        self.consume_literal(")")
        _t1529 = logic_pb2.Conjunction(args=formulas1035)
        return _t1529

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal("(")
        self.consume_literal("or")
        xs1036 = []
        cond1037 = self.match_lookahead_literal("(", 0)
        while cond1037:
            _t1530 = self.parse_formula()
            item1038 = _t1530
            xs1036.append(item1038)
            cond1037 = self.match_lookahead_literal("(", 0)
        formulas1039 = xs1036
        self.consume_literal(")")
        _t1531 = logic_pb2.Disjunction(args=formulas1039)
        return _t1531

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal("(")
        self.consume_literal("not")
        _t1532 = self.parse_formula()
        formula1040 = _t1532
        self.consume_literal(")")
        _t1533 = logic_pb2.Not(arg=formula1040)
        return _t1533

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1534 = self.parse_name()
        name1041 = _t1534
        _t1535 = self.parse_ffi_args()
        ffi_args1042 = _t1535
        _t1536 = self.parse_terms()
        terms1043 = _t1536
        self.consume_literal(")")
        _t1537 = logic_pb2.FFI(name=name1041, args=ffi_args1042, terms=terms1043)
        return _t1537

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol1044 = self.consume_terminal("SYMBOL")
        return symbol1044

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs1045 = []
        cond1046 = self.match_lookahead_literal("(", 0)
        while cond1046:
            _t1538 = self.parse_abstraction()
            item1047 = _t1538
            xs1045.append(item1047)
            cond1046 = self.match_lookahead_literal("(", 0)
        abstractions1048 = xs1045
        self.consume_literal(")")
        return abstractions1048

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1539 = self.parse_relation_id()
        relation_id1049 = _t1539
        xs1050 = []
        cond1051 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond1051:
            _t1540 = self.parse_term()
            item1052 = _t1540
            xs1050.append(item1052)
            cond1051 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms1053 = xs1050
        self.consume_literal(")")
        _t1541 = logic_pb2.Atom(name=relation_id1049, terms=terms1053)
        return _t1541

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1542 = self.parse_name()
        name1054 = _t1542
        xs1055 = []
        cond1056 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond1056:
            _t1543 = self.parse_term()
            item1057 = _t1543
            xs1055.append(item1057)
            cond1056 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms1058 = xs1055
        self.consume_literal(")")
        _t1544 = logic_pb2.Pragma(name=name1054, terms=terms1058)
        return _t1544

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1546 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1547 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1548 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1549 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1550 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1551 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1552 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1553 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1554 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1555 = 7
                                                else:
                                                    _t1555 = -1
                                                _t1554 = _t1555
                                            _t1553 = _t1554
                                        _t1552 = _t1553
                                    _t1551 = _t1552
                                _t1550 = _t1551
                            _t1549 = _t1550
                        _t1548 = _t1549
                    _t1547 = _t1548
                _t1546 = _t1547
            _t1545 = _t1546
        else:
            _t1545 = -1
        prediction1059 = _t1545
        if prediction1059 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1557 = self.parse_name()
            name1069 = _t1557
            xs1070 = []
            cond1071 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            while cond1071:
                _t1558 = self.parse_rel_term()
                item1072 = _t1558
                xs1070.append(item1072)
                cond1071 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            rel_terms1073 = xs1070
            self.consume_literal(")")
            _t1559 = logic_pb2.Primitive(name=name1069, terms=rel_terms1073)
            _t1556 = _t1559
        else:
            if prediction1059 == 8:
                _t1561 = self.parse_divide()
                divide1068 = _t1561
                _t1560 = divide1068
            else:
                if prediction1059 == 7:
                    _t1563 = self.parse_multiply()
                    multiply1067 = _t1563
                    _t1562 = multiply1067
                else:
                    if prediction1059 == 6:
                        _t1565 = self.parse_minus()
                        minus1066 = _t1565
                        _t1564 = minus1066
                    else:
                        if prediction1059 == 5:
                            _t1567 = self.parse_add()
                            add1065 = _t1567
                            _t1566 = add1065
                        else:
                            if prediction1059 == 4:
                                _t1569 = self.parse_gt_eq()
                                gt_eq1064 = _t1569
                                _t1568 = gt_eq1064
                            else:
                                if prediction1059 == 3:
                                    _t1571 = self.parse_gt()
                                    gt1063 = _t1571
                                    _t1570 = gt1063
                                else:
                                    if prediction1059 == 2:
                                        _t1573 = self.parse_lt_eq()
                                        lt_eq1062 = _t1573
                                        _t1572 = lt_eq1062
                                    else:
                                        if prediction1059 == 1:
                                            _t1575 = self.parse_lt()
                                            lt1061 = _t1575
                                            _t1574 = lt1061
                                        else:
                                            if prediction1059 == 0:
                                                _t1577 = self.parse_eq()
                                                eq1060 = _t1577
                                                _t1576 = eq1060
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1574 = _t1576
                                        _t1572 = _t1574
                                    _t1570 = _t1572
                                _t1568 = _t1570
                            _t1566 = _t1568
                        _t1564 = _t1566
                    _t1562 = _t1564
                _t1560 = _t1562
            _t1556 = _t1560
        return _t1556

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("=")
        _t1578 = self.parse_term()
        term1074 = _t1578
        _t1579 = self.parse_term()
        term_31075 = _t1579
        self.consume_literal(")")
        _t1580 = logic_pb2.RelTerm(term=term1074)
        _t1581 = logic_pb2.RelTerm(term=term_31075)
        _t1582 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1580, _t1581])
        return _t1582

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("<")
        _t1583 = self.parse_term()
        term1076 = _t1583
        _t1584 = self.parse_term()
        term_31077 = _t1584
        self.consume_literal(")")
        _t1585 = logic_pb2.RelTerm(term=term1076)
        _t1586 = logic_pb2.RelTerm(term=term_31077)
        _t1587 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1585, _t1586])
        return _t1587

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1588 = self.parse_term()
        term1078 = _t1588
        _t1589 = self.parse_term()
        term_31079 = _t1589
        self.consume_literal(")")
        _t1590 = logic_pb2.RelTerm(term=term1078)
        _t1591 = logic_pb2.RelTerm(term=term_31079)
        _t1592 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1590, _t1591])
        return _t1592

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal(">")
        _t1593 = self.parse_term()
        term1080 = _t1593
        _t1594 = self.parse_term()
        term_31081 = _t1594
        self.consume_literal(")")
        _t1595 = logic_pb2.RelTerm(term=term1080)
        _t1596 = logic_pb2.RelTerm(term=term_31081)
        _t1597 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1595, _t1596])
        return _t1597

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1598 = self.parse_term()
        term1082 = _t1598
        _t1599 = self.parse_term()
        term_31083 = _t1599
        self.consume_literal(")")
        _t1600 = logic_pb2.RelTerm(term=term1082)
        _t1601 = logic_pb2.RelTerm(term=term_31083)
        _t1602 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1600, _t1601])
        return _t1602

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("+")
        _t1603 = self.parse_term()
        term1084 = _t1603
        _t1604 = self.parse_term()
        term_31085 = _t1604
        _t1605 = self.parse_term()
        term_41086 = _t1605
        self.consume_literal(")")
        _t1606 = logic_pb2.RelTerm(term=term1084)
        _t1607 = logic_pb2.RelTerm(term=term_31085)
        _t1608 = logic_pb2.RelTerm(term=term_41086)
        _t1609 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1606, _t1607, _t1608])
        return _t1609

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("-")
        _t1610 = self.parse_term()
        term1087 = _t1610
        _t1611 = self.parse_term()
        term_31088 = _t1611
        _t1612 = self.parse_term()
        term_41089 = _t1612
        self.consume_literal(")")
        _t1613 = logic_pb2.RelTerm(term=term1087)
        _t1614 = logic_pb2.RelTerm(term=term_31088)
        _t1615 = logic_pb2.RelTerm(term=term_41089)
        _t1616 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1613, _t1614, _t1615])
        return _t1616

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("*")
        _t1617 = self.parse_term()
        term1090 = _t1617
        _t1618 = self.parse_term()
        term_31091 = _t1618
        _t1619 = self.parse_term()
        term_41092 = _t1619
        self.consume_literal(")")
        _t1620 = logic_pb2.RelTerm(term=term1090)
        _t1621 = logic_pb2.RelTerm(term=term_31091)
        _t1622 = logic_pb2.RelTerm(term=term_41092)
        _t1623 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1620, _t1621, _t1622])
        return _t1623

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal("(")
        self.consume_literal("/")
        _t1624 = self.parse_term()
        term1093 = _t1624
        _t1625 = self.parse_term()
        term_31094 = _t1625
        _t1626 = self.parse_term()
        term_41095 = _t1626
        self.consume_literal(")")
        _t1627 = logic_pb2.RelTerm(term=term1093)
        _t1628 = logic_pb2.RelTerm(term=term_31094)
        _t1629 = logic_pb2.RelTerm(term=term_41095)
        _t1630 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1627, _t1628, _t1629])
        return _t1630

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_literal("true", 0):
            _t1631 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1632 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1633 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1634 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1635 = 0
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1636 = 1
                            else:
                                if self.match_lookahead_terminal("SYMBOL", 0):
                                    _t1637 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1638 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1639 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1640 = 1
                                            else:
                                                if self.match_lookahead_terminal("FLOAT", 0):
                                                    _t1641 = 1
                                                else:
                                                    if self.match_lookahead_terminal("DECIMAL", 0):
                                                        _t1642 = 1
                                                    else:
                                                        _t1642 = -1
                                                    _t1641 = _t1642
                                                _t1640 = _t1641
                                            _t1639 = _t1640
                                        _t1638 = _t1639
                                    _t1637 = _t1638
                                _t1636 = _t1637
                            _t1635 = _t1636
                        _t1634 = _t1635
                    _t1633 = _t1634
                _t1632 = _t1633
            _t1631 = _t1632
        prediction1096 = _t1631
        if prediction1096 == 1:
            _t1644 = self.parse_term()
            term1098 = _t1644
            _t1645 = logic_pb2.RelTerm(term=term1098)
            _t1643 = _t1645
        else:
            if prediction1096 == 0:
                _t1647 = self.parse_specialized_value()
                specialized_value1097 = _t1647
                _t1648 = logic_pb2.RelTerm(specialized_value=specialized_value1097)
                _t1646 = _t1648
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1643 = _t1646
        return _t1643

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal("#")
        _t1649 = self.parse_value()
        value1099 = _t1649
        return value1099

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1650 = self.parse_name()
        name1100 = _t1650
        xs1101 = []
        cond1102 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond1102:
            _t1651 = self.parse_rel_term()
            item1103 = _t1651
            xs1101.append(item1103)
            cond1102 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        rel_terms1104 = xs1101
        self.consume_literal(")")
        _t1652 = logic_pb2.RelAtom(name=name1100, terms=rel_terms1104)
        return _t1652

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1653 = self.parse_term()
        term1105 = _t1653
        _t1654 = self.parse_term()
        term_31106 = _t1654
        self.consume_literal(")")
        _t1655 = logic_pb2.Cast(input=term1105, result=term_31106)
        return _t1655

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1107 = []
        cond1108 = self.match_lookahead_literal("(", 0)
        while cond1108:
            _t1656 = self.parse_attribute()
            item1109 = _t1656
            xs1107.append(item1109)
            cond1108 = self.match_lookahead_literal("(", 0)
        attributes1110 = xs1107
        self.consume_literal(")")
        return attributes1110

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1657 = self.parse_name()
        name1111 = _t1657
        xs1112 = []
        cond1113 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond1113:
            _t1658 = self.parse_value()
            item1114 = _t1658
            xs1112.append(item1114)
            cond1113 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        values1115 = xs1112
        self.consume_literal(")")
        _t1659 = logic_pb2.Attribute(name=name1111, args=values1115)
        return _t1659

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1116 = []
        cond1117 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1117:
            _t1660 = self.parse_relation_id()
            item1118 = _t1660
            xs1116.append(item1118)
            cond1117 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1119 = xs1116
        _t1661 = self.parse_script()
        script1120 = _t1661
        self.consume_literal(")")
        _t1662 = logic_pb2.Algorithm(body=script1120)
        getattr(_t1662, 'global').extend(relation_ids1119)
        return _t1662

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal("(")
        self.consume_literal("script")
        xs1121 = []
        cond1122 = self.match_lookahead_literal("(", 0)
        while cond1122:
            _t1663 = self.parse_construct()
            item1123 = _t1663
            xs1121.append(item1123)
            cond1122 = self.match_lookahead_literal("(", 0)
        constructs1124 = xs1121
        self.consume_literal(")")
        _t1664 = logic_pb2.Script(constructs=constructs1124)
        return _t1664

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1666 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1667 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1668 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1669 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1670 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1671 = 1
                                else:
                                    _t1671 = -1
                                _t1670 = _t1671
                            _t1669 = _t1670
                        _t1668 = _t1669
                    _t1667 = _t1668
                _t1666 = _t1667
            _t1665 = _t1666
        else:
            _t1665 = -1
        prediction1125 = _t1665
        if prediction1125 == 1:
            _t1673 = self.parse_instruction()
            instruction1127 = _t1673
            _t1674 = logic_pb2.Construct(instruction=instruction1127)
            _t1672 = _t1674
        else:
            if prediction1125 == 0:
                _t1676 = self.parse_loop()
                loop1126 = _t1676
                _t1677 = logic_pb2.Construct(loop=loop1126)
                _t1675 = _t1677
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1672 = _t1675
        return _t1672

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1678 = self.parse_init()
        init1128 = _t1678
        _t1679 = self.parse_script()
        script1129 = _t1679
        self.consume_literal(")")
        _t1680 = logic_pb2.Loop(init=init1128, body=script1129)
        return _t1680

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1130 = []
        cond1131 = self.match_lookahead_literal("(", 0)
        while cond1131:
            _t1681 = self.parse_instruction()
            item1132 = _t1681
            xs1130.append(item1132)
            cond1131 = self.match_lookahead_literal("(", 0)
        instructions1133 = xs1130
        self.consume_literal(")")
        return instructions1133

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1683 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1684 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1685 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1686 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1687 = 0
                            else:
                                _t1687 = -1
                            _t1686 = _t1687
                        _t1685 = _t1686
                    _t1684 = _t1685
                _t1683 = _t1684
            _t1682 = _t1683
        else:
            _t1682 = -1
        prediction1134 = _t1682
        if prediction1134 == 4:
            _t1689 = self.parse_monus_def()
            monus_def1139 = _t1689
            _t1690 = logic_pb2.Instruction(monus_def=monus_def1139)
            _t1688 = _t1690
        else:
            if prediction1134 == 3:
                _t1692 = self.parse_monoid_def()
                monoid_def1138 = _t1692
                _t1693 = logic_pb2.Instruction(monoid_def=monoid_def1138)
                _t1691 = _t1693
            else:
                if prediction1134 == 2:
                    _t1695 = self.parse_break()
                    break1137 = _t1695
                    _t1696 = logic_pb2.Instruction()
                    getattr(_t1696, 'break').CopyFrom(break1137)
                    _t1694 = _t1696
                else:
                    if prediction1134 == 1:
                        _t1698 = self.parse_upsert()
                        upsert1136 = _t1698
                        _t1699 = logic_pb2.Instruction(upsert=upsert1136)
                        _t1697 = _t1699
                    else:
                        if prediction1134 == 0:
                            _t1701 = self.parse_assign()
                            assign1135 = _t1701
                            _t1702 = logic_pb2.Instruction(assign=assign1135)
                            _t1700 = _t1702
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1697 = _t1700
                    _t1694 = _t1697
                _t1691 = _t1694
            _t1688 = _t1691
        return _t1688

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1703 = self.parse_relation_id()
        relation_id1140 = _t1703
        _t1704 = self.parse_abstraction()
        abstraction1141 = _t1704
        if self.match_lookahead_literal("(", 0):
            _t1706 = self.parse_attrs()
            _t1705 = _t1706
        else:
            _t1705 = None
        attrs1142 = _t1705
        self.consume_literal(")")
        _t1707 = logic_pb2.Assign(name=relation_id1140, body=abstraction1141, attrs=(attrs1142 if attrs1142 is not None else []))
        return _t1707

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1708 = self.parse_relation_id()
        relation_id1143 = _t1708
        _t1709 = self.parse_abstraction_with_arity()
        abstraction_with_arity1144 = _t1709
        if self.match_lookahead_literal("(", 0):
            _t1711 = self.parse_attrs()
            _t1710 = _t1711
        else:
            _t1710 = None
        attrs1145 = _t1710
        self.consume_literal(")")
        _t1712 = logic_pb2.Upsert(name=relation_id1143, body=abstraction_with_arity1144[0], attrs=(attrs1145 if attrs1145 is not None else []), value_arity=abstraction_with_arity1144[1])
        return _t1712

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1713 = self.parse_bindings()
        bindings1146 = _t1713
        _t1714 = self.parse_formula()
        formula1147 = _t1714
        self.consume_literal(")")
        _t1715 = logic_pb2.Abstraction(vars=(list(bindings1146[0]) + list(bindings1146[1] if bindings1146[1] is not None else [])), value=formula1147)
        return (_t1715, len(bindings1146[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal("(")
        self.consume_literal("break")
        _t1716 = self.parse_relation_id()
        relation_id1148 = _t1716
        _t1717 = self.parse_abstraction()
        abstraction1149 = _t1717
        if self.match_lookahead_literal("(", 0):
            _t1719 = self.parse_attrs()
            _t1718 = _t1719
        else:
            _t1718 = None
        attrs1150 = _t1718
        self.consume_literal(")")
        _t1720 = logic_pb2.Break(name=relation_id1148, body=abstraction1149, attrs=(attrs1150 if attrs1150 is not None else []))
        return _t1720

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1721 = self.parse_monoid()
        monoid1151 = _t1721
        _t1722 = self.parse_relation_id()
        relation_id1152 = _t1722
        _t1723 = self.parse_abstraction_with_arity()
        abstraction_with_arity1153 = _t1723
        if self.match_lookahead_literal("(", 0):
            _t1725 = self.parse_attrs()
            _t1724 = _t1725
        else:
            _t1724 = None
        attrs1154 = _t1724
        self.consume_literal(")")
        _t1726 = logic_pb2.MonoidDef(monoid=monoid1151, name=relation_id1152, body=abstraction_with_arity1153[0], attrs=(attrs1154 if attrs1154 is not None else []), value_arity=abstraction_with_arity1153[1])
        return _t1726

    def parse_monoid(self) -> logic_pb2.Monoid:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1728 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1729 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1730 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1731 = 2
                        else:
                            _t1731 = -1
                        _t1730 = _t1731
                    _t1729 = _t1730
                _t1728 = _t1729
            _t1727 = _t1728
        else:
            _t1727 = -1
        prediction1155 = _t1727
        if prediction1155 == 3:
            _t1733 = self.parse_sum_monoid()
            sum_monoid1159 = _t1733
            _t1734 = logic_pb2.Monoid(sum_monoid=sum_monoid1159)
            _t1732 = _t1734
        else:
            if prediction1155 == 2:
                _t1736 = self.parse_max_monoid()
                max_monoid1158 = _t1736
                _t1737 = logic_pb2.Monoid(max_monoid=max_monoid1158)
                _t1735 = _t1737
            else:
                if prediction1155 == 1:
                    _t1739 = self.parse_min_monoid()
                    min_monoid1157 = _t1739
                    _t1740 = logic_pb2.Monoid(min_monoid=min_monoid1157)
                    _t1738 = _t1740
                else:
                    if prediction1155 == 0:
                        _t1742 = self.parse_or_monoid()
                        or_monoid1156 = _t1742
                        _t1743 = logic_pb2.Monoid(or_monoid=or_monoid1156)
                        _t1741 = _t1743
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1738 = _t1741
                _t1735 = _t1738
            _t1732 = _t1735
        return _t1732

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1744 = logic_pb2.OrMonoid()
        return _t1744

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        self.consume_literal("(")
        self.consume_literal("min")
        _t1745 = self.parse_type()
        type1160 = _t1745
        self.consume_literal(")")
        _t1746 = logic_pb2.MinMonoid(type=type1160)
        return _t1746

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        self.consume_literal("(")
        self.consume_literal("max")
        _t1747 = self.parse_type()
        type1161 = _t1747
        self.consume_literal(")")
        _t1748 = logic_pb2.MaxMonoid(type=type1161)
        return _t1748

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1749 = self.parse_type()
        type1162 = _t1749
        self.consume_literal(")")
        _t1750 = logic_pb2.SumMonoid(type=type1162)
        return _t1750

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1751 = self.parse_monoid()
        monoid1163 = _t1751
        _t1752 = self.parse_relation_id()
        relation_id1164 = _t1752
        _t1753 = self.parse_abstraction_with_arity()
        abstraction_with_arity1165 = _t1753
        if self.match_lookahead_literal("(", 0):
            _t1755 = self.parse_attrs()
            _t1754 = _t1755
        else:
            _t1754 = None
        attrs1166 = _t1754
        self.consume_literal(")")
        _t1756 = logic_pb2.MonusDef(monoid=monoid1163, name=relation_id1164, body=abstraction_with_arity1165[0], attrs=(attrs1166 if attrs1166 is not None else []), value_arity=abstraction_with_arity1165[1])
        return _t1756

    def parse_constraint(self) -> logic_pb2.Constraint:
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1757 = self.parse_relation_id()
        relation_id1167 = _t1757
        _t1758 = self.parse_abstraction()
        abstraction1168 = _t1758
        _t1759 = self.parse_functional_dependency_keys()
        functional_dependency_keys1169 = _t1759
        _t1760 = self.parse_functional_dependency_values()
        functional_dependency_values1170 = _t1760
        self.consume_literal(")")
        _t1761 = logic_pb2.FunctionalDependency(guard=abstraction1168, keys=functional_dependency_keys1169, values=functional_dependency_values1170)
        _t1762 = logic_pb2.Constraint(name=relation_id1167, functional_dependency=_t1761)
        return _t1762

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1171 = []
        cond1172 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1172:
            _t1763 = self.parse_var()
            item1173 = _t1763
            xs1171.append(item1173)
            cond1172 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1174 = xs1171
        self.consume_literal(")")
        return vars1174

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1175 = []
        cond1176 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1176:
            _t1764 = self.parse_var()
            item1177 = _t1764
            xs1175.append(item1177)
            cond1176 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1178 = xs1175
        self.consume_literal(")")
        return vars1178

    def parse_data(self) -> logic_pb2.Data:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("rel_edb", 1):
                _t1766 = 0
            else:
                if self.match_lookahead_literal("csv_data", 1):
                    _t1767 = 2
                else:
                    if self.match_lookahead_literal("betree_relation", 1):
                        _t1768 = 1
                    else:
                        _t1768 = -1
                    _t1767 = _t1768
                _t1766 = _t1767
            _t1765 = _t1766
        else:
            _t1765 = -1
        prediction1179 = _t1765
        if prediction1179 == 2:
            _t1770 = self.parse_csv_data()
            csv_data1182 = _t1770
            _t1771 = logic_pb2.Data(csv_data=csv_data1182)
            _t1769 = _t1771
        else:
            if prediction1179 == 1:
                _t1773 = self.parse_betree_relation()
                betree_relation1181 = _t1773
                _t1774 = logic_pb2.Data(betree_relation=betree_relation1181)
                _t1772 = _t1774
            else:
                if prediction1179 == 0:
                    _t1776 = self.parse_rel_edb()
                    rel_edb1180 = _t1776
                    _t1777 = logic_pb2.Data(rel_edb=rel_edb1180)
                    _t1775 = _t1777
                else:
                    raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t1772 = _t1775
            _t1769 = _t1772
        return _t1769

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        self.consume_literal("(")
        self.consume_literal("rel_edb")
        _t1778 = self.parse_relation_id()
        relation_id1183 = _t1778
        _t1779 = self.parse_rel_edb_path()
        rel_edb_path1184 = _t1779
        _t1780 = self.parse_rel_edb_types()
        rel_edb_types1185 = _t1780
        self.consume_literal(")")
        _t1781 = logic_pb2.RelEDB(target_id=relation_id1183, path=rel_edb_path1184, types=rel_edb_types1185)
        return _t1781

    def parse_rel_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1186 = []
        cond1187 = self.match_lookahead_terminal("STRING", 0)
        while cond1187:
            item1188 = self.consume_terminal("STRING")
            xs1186.append(item1188)
            cond1187 = self.match_lookahead_terminal("STRING", 0)
        strings1189 = xs1186
        self.consume_literal("]")
        return strings1189

    def parse_rel_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1190 = []
        cond1191 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1191:
            _t1782 = self.parse_type()
            item1192 = _t1782
            xs1190.append(item1192)
            cond1191 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1193 = xs1190
        self.consume_literal("]")
        return types1193

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1783 = self.parse_relation_id()
        relation_id1194 = _t1783
        _t1784 = self.parse_betree_info()
        betree_info1195 = _t1784
        self.consume_literal(")")
        _t1785 = logic_pb2.BeTreeRelation(name=relation_id1194, relation_info=betree_info1195)
        return _t1785

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1786 = self.parse_betree_info_key_types()
        betree_info_key_types1196 = _t1786
        _t1787 = self.parse_betree_info_value_types()
        betree_info_value_types1197 = _t1787
        _t1788 = self.parse_config_dict()
        config_dict1198 = _t1788
        self.consume_literal(")")
        _t1789 = self.construct_betree_info(betree_info_key_types1196, betree_info_value_types1197, config_dict1198)
        return _t1789

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1199 = []
        cond1200 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1200:
            _t1790 = self.parse_type()
            item1201 = _t1790
            xs1199.append(item1201)
            cond1200 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1202 = xs1199
        self.consume_literal(")")
        return types1202

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1203 = []
        cond1204 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1204:
            _t1791 = self.parse_type()
            item1205 = _t1791
            xs1203.append(item1205)
            cond1204 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1206 = xs1203
        self.consume_literal(")")
        return types1206

    def parse_csv_data(self) -> logic_pb2.CSVData:
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1792 = self.parse_csvlocator()
        csvlocator1207 = _t1792
        _t1793 = self.parse_csv_config()
        csv_config1208 = _t1793
        _t1794 = self.parse_csv_columns()
        csv_columns1209 = _t1794
        _t1795 = self.parse_csv_asof()
        csv_asof1210 = _t1795
        self.consume_literal(")")
        _t1796 = logic_pb2.CSVData(locator=csvlocator1207, config=csv_config1208, columns=csv_columns1209, asof=csv_asof1210)
        return _t1796

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1798 = self.parse_csv_locator_paths()
            _t1797 = _t1798
        else:
            _t1797 = None
        csv_locator_paths1211 = _t1797
        if self.match_lookahead_literal("(", 0):
            _t1800 = self.parse_csv_locator_inline_data()
            _t1799 = _t1800
        else:
            _t1799 = None
        csv_locator_inline_data1212 = _t1799
        self.consume_literal(")")
        _t1801 = logic_pb2.CSVLocator(paths=(csv_locator_paths1211 if csv_locator_paths1211 is not None else []), inline_data=(csv_locator_inline_data1212 if csv_locator_inline_data1212 is not None else "").encode())
        return _t1801

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1213 = []
        cond1214 = self.match_lookahead_terminal("STRING", 0)
        while cond1214:
            item1215 = self.consume_terminal("STRING")
            xs1213.append(item1215)
            cond1214 = self.match_lookahead_terminal("STRING", 0)
        strings1216 = xs1213
        self.consume_literal(")")
        return strings1216

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1217 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1217

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1802 = self.parse_config_dict()
        config_dict1218 = _t1802
        self.consume_literal(")")
        _t1803 = self.construct_csv_config(config_dict1218)
        return _t1803

    def parse_csv_columns(self) -> Sequence[logic_pb2.CSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1219 = []
        cond1220 = self.match_lookahead_literal("(", 0)
        while cond1220:
            _t1804 = self.parse_csv_column()
            item1221 = _t1804
            xs1219.append(item1221)
            cond1220 = self.match_lookahead_literal("(", 0)
        csv_columns1222 = xs1219
        self.consume_literal(")")
        return csv_columns1222

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        self.consume_literal("(")
        self.consume_literal("column")
        string1223 = self.consume_terminal("STRING")
        _t1805 = self.parse_relation_id()
        relation_id1224 = _t1805
        self.consume_literal("[")
        xs1225 = []
        cond1226 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1226:
            _t1806 = self.parse_type()
            item1227 = _t1806
            xs1225.append(item1227)
            cond1226 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1228 = xs1225
        self.consume_literal("]")
        self.consume_literal(")")
        _t1807 = logic_pb2.CSVColumn(column_name=string1223, target_id=relation_id1224, types=types1228)
        return _t1807

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1229 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1229

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1808 = self.parse_fragment_id()
        fragment_id1230 = _t1808
        self.consume_literal(")")
        _t1809 = transactions_pb2.Undefine(fragment_id=fragment_id1230)
        return _t1809

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal("(")
        self.consume_literal("context")
        xs1231 = []
        cond1232 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1232:
            _t1810 = self.parse_relation_id()
            item1233 = _t1810
            xs1231.append(item1233)
            cond1232 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1234 = xs1231
        self.consume_literal(")")
        _t1811 = transactions_pb2.Context(relations=relation_ids1234)
        return _t1811

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1235 = []
        cond1236 = self.match_lookahead_literal("(", 0)
        while cond1236:
            _t1812 = self.parse_read()
            item1237 = _t1812
            xs1235.append(item1237)
            cond1236 = self.match_lookahead_literal("(", 0)
        reads1238 = xs1235
        self.consume_literal(")")
        return reads1238

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1814 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1815 = 1
                else:
                    if self.match_lookahead_literal("export", 1):
                        _t1816 = 4
                    else:
                        if self.match_lookahead_literal("demand", 1):
                            _t1817 = 0
                        else:
                            if self.match_lookahead_literal("abort", 1):
                                _t1818 = 3
                            else:
                                _t1818 = -1
                            _t1817 = _t1818
                        _t1816 = _t1817
                    _t1815 = _t1816
                _t1814 = _t1815
            _t1813 = _t1814
        else:
            _t1813 = -1
        prediction1239 = _t1813
        if prediction1239 == 4:
            _t1820 = self.parse_export()
            export1244 = _t1820
            _t1821 = transactions_pb2.Read(export=export1244)
            _t1819 = _t1821
        else:
            if prediction1239 == 3:
                _t1823 = self.parse_abort()
                abort1243 = _t1823
                _t1824 = transactions_pb2.Read(abort=abort1243)
                _t1822 = _t1824
            else:
                if prediction1239 == 2:
                    _t1826 = self.parse_what_if()
                    what_if1242 = _t1826
                    _t1827 = transactions_pb2.Read(what_if=what_if1242)
                    _t1825 = _t1827
                else:
                    if prediction1239 == 1:
                        _t1829 = self.parse_output()
                        output1241 = _t1829
                        _t1830 = transactions_pb2.Read(output=output1241)
                        _t1828 = _t1830
                    else:
                        if prediction1239 == 0:
                            _t1832 = self.parse_demand()
                            demand1240 = _t1832
                            _t1833 = transactions_pb2.Read(demand=demand1240)
                            _t1831 = _t1833
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1828 = _t1831
                    _t1825 = _t1828
                _t1822 = _t1825
            _t1819 = _t1822
        return _t1819

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1834 = self.parse_relation_id()
        relation_id1245 = _t1834
        self.consume_literal(")")
        _t1835 = transactions_pb2.Demand(relation_id=relation_id1245)
        return _t1835

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal("(")
        self.consume_literal("output")
        _t1836 = self.parse_name()
        name1246 = _t1836
        _t1837 = self.parse_relation_id()
        relation_id1247 = _t1837
        self.consume_literal(")")
        _t1838 = transactions_pb2.Output(name=name1246, relation_id=relation_id1247)
        return _t1838

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t1839 = self.parse_name()
        name1248 = _t1839
        _t1840 = self.parse_epoch()
        epoch1249 = _t1840
        self.consume_literal(")")
        _t1841 = transactions_pb2.WhatIf(branch=name1248, epoch=epoch1249)
        return _t1841

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t1843 = self.parse_name()
            _t1842 = _t1843
        else:
            _t1842 = None
        name1250 = _t1842
        _t1844 = self.parse_relation_id()
        relation_id1251 = _t1844
        self.consume_literal(")")
        _t1845 = transactions_pb2.Abort(name=(name1250 if name1250 is not None else "abort"), relation_id=relation_id1251)
        return _t1845

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal("(")
        self.consume_literal("export")
        _t1846 = self.parse_export_csv_config()
        export_csv_config1252 = _t1846
        self.consume_literal(")")
        _t1847 = transactions_pb2.Export(csv_config=export_csv_config1252)
        return _t1847

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal("(")
        self.consume_literal("export_csv_config")
        _t1848 = self.parse_export_csv_path()
        export_csv_path1253 = _t1848
        _t1849 = self.parse_export_csv_columns()
        export_csv_columns1254 = _t1849
        _t1850 = self.parse_config_dict()
        config_dict1255 = _t1850
        self.consume_literal(")")
        _t1851 = self.export_csv_config(export_csv_path1253, export_csv_columns1254, config_dict1255)
        return _t1851

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1256 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1256

    def parse_export_csv_columns(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1257 = []
        cond1258 = self.match_lookahead_literal("(", 0)
        while cond1258:
            _t1852 = self.parse_export_csv_column()
            item1259 = _t1852
            xs1257.append(item1259)
            cond1258 = self.match_lookahead_literal("(", 0)
        export_csv_columns1260 = xs1257
        self.consume_literal(")")
        return export_csv_columns1260

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal("(")
        self.consume_literal("column")
        string1261 = self.consume_terminal("STRING")
        _t1853 = self.parse_relation_id()
        relation_id1262 = _t1853
        self.consume_literal(")")
        _t1854 = transactions_pb2.ExportCSVColumn(column_name=string1261, column_data=relation_id1262)
        return _t1854


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
