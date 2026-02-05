"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.


Command: python -m meta.cli ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto ../proto/relationalai/lqp/v1/fragments.proto --parser python
"""

import ast
import hashlib
import re
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
            ('LITERAL', re.compile(r'::'), lambda x: x),
            ('LITERAL', re.compile(r'<='), lambda x: x),
            ('LITERAL', re.compile(r'>='), lambda x: x),
            ('LITERAL', re.compile(r'\#'), lambda x: x),
            ('LITERAL', re.compile(r'\('), lambda x: x),
            ('LITERAL', re.compile(r'\)'), lambda x: x),
            ('LITERAL', re.compile(r'\*'), lambda x: x),
            ('LITERAL', re.compile(r'\+'), lambda x: x),
            ('LITERAL', re.compile(r'\-'), lambda x: x),
            ('LITERAL', re.compile(r'/'), lambda x: x),
            ('LITERAL', re.compile(r':'), lambda x: x),
            ('LITERAL', re.compile(r'<'), lambda x: x),
            ('LITERAL', re.compile(r'='), lambda x: x),
            ('LITERAL', re.compile(r'>'), lambda x: x),
            ('LITERAL', re.compile(r'\['), lambda x: x),
            ('LITERAL', re.compile(r'\]'), lambda x: x),
            ('LITERAL', re.compile(r'\{'), lambda x: x),
            ('LITERAL', re.compile(r'\|'), lambda x: x),
            ('LITERAL', re.compile(r'\}'), lambda x: x),
            ('DECIMAL', re.compile(r'[-]?\d+\.\d+d\d+'), lambda x: Lexer.scan_decimal(x)),
            ('FLOAT', re.compile(r'[-]?\d+\.\d+|inf|nan'), lambda x: Lexer.scan_float(x)),
            ('INT', re.compile(r'[-]?\d+'), lambda x: Lexer.scan_int(x)),
            ('INT128', re.compile(r'[-]?\d+i128'), lambda x: Lexer.scan_int128(x)),
            ('STRING', re.compile(r'"(?:[^"\\]|\\.)*"'), lambda x: Lexer.scan_string(x)),
            ('SYMBOL', re.compile(r'[a-zA-Z_][a-zA-Z0-9_.-]*'), lambda x: Lexer.scan_symbol(x)),
            ('UINT128', re.compile(r'0x[0-9a-fA-F]+'), lambda x: Lexer.scan_uint128(x)),
        ]

        whitespace_re = re.compile(r'\s+')
        comment_re = re.compile(r';;.*')

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
                raise ParseError(f'Unexpected character at position {self.pos}: {self.input[self.pos]!r}')

            # Pick the longest match
            token_type, value, action, end_pos = max(candidates, key=lambda x: x[3])
            self.tokens.append(Token(token_type, action(value), self.pos))
            self.pos = end_pos

        self.tokens.append(Token('$', '', self.pos))

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
        return int(n)

    @staticmethod
    def scan_float(f: str) -> float:
        """Parse FLOAT token."""
        if f == 'inf':
            return float('inf')
        elif f == 'nan':
            return float('nan')
        return float(f)

    @staticmethod
    def scan_uint128(u: str) -> Any:
        """Parse UINT128 token."""
        uint128_val = int(u, 16)
        low = uint128_val & 0xFFFFFFFFFFFFFFFF
        high = (uint128_val >> 64) & 0xFFFFFFFFFFFFFFFF
        return logic_pb2.UInt128Value(low=low, high=high)

    @staticmethod
    def scan_int128(u: str) -> Any:
        """Parse INT128 token."""
        u = u[:-4]  # Remove the 'i128' suffix
        int128_val = int(u)
        low = int128_val & 0xFFFFFFFFFFFFFFFF
        high = (int128_val >> 64) & 0xFFFFFFFFFFFFFFFF
        return logic_pb2.Int128Value(low=low, high=high)

    @staticmethod
    def scan_decimal(d: str) -> Any:
        """Parse DECIMAL token."""
        # Decimal is a string like '123.456d12' where the last part after `d` is the
        # precision, and the scale is the number of digits between the decimal point and `d`
        parts = d.split('d')
        if len(parts) != 2:
            raise ValueError(f'Invalid decimal format: {d}')
        scale = len(parts[0].split('.')[1])
        precision = int(parts[1])
        # Parse the integer value directly without calling scan_int128 which strips 'i128' suffix
        int_str = parts[0].replace('.', '')
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
        return self.tokens[idx] if idx < len(self.tokens) else Token('$', '', -1)

    def consume_literal(self, expected: str) -> None:
        """Consume a literal token."""
        if not self.match_lookahead_literal(expected, 0):
            token = self.lookahead(0)
            raise ParseError(f'Expected literal {expected!r} but got {token.type}=`{token.value!r}` at position {token.pos}')
        self.pos += 1

    def consume_terminal(self, expected: str) -> Any:
        """Consume a terminal token and return parsed value."""
        if not self.match_lookahead_terminal(expected, 0):
            token = self.lookahead(0)
            raise ParseError(f'Expected terminal {expected} but got {token.type}=`{token.value!r}` at position {token.pos}')
        token = self.lookahead(0)
        self.pos += 1
        return token.value

    def match_lookahead_literal(self, literal: str, k: int) -> bool:
        """Check if lookahead token at position k matches literal.

        Supports soft keywords: alphanumeric literals are lexed as SYMBOL tokens,
        so we check both LITERAL and SYMBOL token types.
        """
        token = self.lookahead(k)
        if token.type == 'LITERAL' and token.value == literal:
            return True
        if token.type == 'SYMBOL' and token.value == literal:
            return True
        return False

    def match_lookahead_terminal(self, terminal: str, k: int) -> bool:
        """Check if lookahead token at position k matches terminal."""
        token = self.lookahead(k)
        return token.type == terminal

    def start_fragment(self, fragment_id: fragments_pb2.FragmentId) -> fragments_pb2.FragmentId:
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
            self.id_to_debuginfo[self._current_fragment_id][(relation_id.id_low, relation_id.id_high)] = name

        return relation_id

    def construct_fragment(self, fragment_id: fragments_pb2.FragmentId, declarations: List[logic_pb2.Declaration]) -> fragments_pb2.Fragment:
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
        return fragments_pb2.Fragment(id=fragment_id, declarations=declarations, debug_info=debug_info)

    # --- Helper functions ---

    @staticmethod
    def _extract_value_int64(value: Optional[logic_pb2.Value], default: int) -> int:
        if (value is not None and value.HasField('int_value')):
            return value.int_value
        else:
            _t1041 = None
        return default

    @staticmethod
    def _extract_value_float64(value: Optional[logic_pb2.Value], default: float) -> float:
        if (value is not None and value.HasField('float_value')):
            return value.float_value
        else:
            _t1042 = None
        return default

    @staticmethod
    def _extract_value_string(value: Optional[logic_pb2.Value], default: str) -> str:
        if (value is not None and value.HasField('string_value')):
            return value.string_value
        else:
            _t1043 = None
        return default

    @staticmethod
    def _extract_value_boolean(value: Optional[logic_pb2.Value], default: bool) -> bool:
        if (value is not None and value.HasField('boolean_value')):
            return value.boolean_value
        else:
            _t1044 = None
        return default

    @staticmethod
    def _extract_value_bytes(value: Optional[logic_pb2.Value], default: bytes) -> bytes:
        if (value is not None and value.HasField('string_value')):
            _t1046 = value.string_value.encode()
            return _t1046
        else:
            _t1045 = None
        return default

    @staticmethod
    def _extract_value_uint128(value: Optional[logic_pb2.Value], default: logic_pb2.UInt128Value) -> logic_pb2.UInt128Value:
        if (value is not None and value.HasField('uint128_value')):
            return value.uint128_value
        else:
            _t1047 = None
        return default

    @staticmethod
    def _extract_value_string_list(value: Optional[logic_pb2.Value], default: list[str]) -> list[str]:
        if (value is not None and value.HasField('string_value')):
            return [value.string_value]
        else:
            _t1048 = None
        return default

    @staticmethod
    def _try_extract_value_int64(value: Optional[logic_pb2.Value]) -> Optional[int]:
        if (value is not None and value.HasField('int_value')):
            return value.int_value
        else:
            _t1049 = None
        return None

    @staticmethod
    def _try_extract_value_float64(value: Optional[logic_pb2.Value]) -> Optional[float]:
        if (value is not None and value.HasField('float_value')):
            return value.float_value
        else:
            _t1050 = None
        return None

    @staticmethod
    def _try_extract_value_string(value: Optional[logic_pb2.Value]) -> Optional[str]:
        if (value is not None and value.HasField('string_value')):
            return value.string_value
        else:
            _t1051 = None
        return None

    @staticmethod
    def _try_extract_value_bytes(value: Optional[logic_pb2.Value]) -> Optional[bytes]:
        if (value is not None and value.HasField('string_value')):
            _t1053 = value.string_value.encode()
            return _t1053
        else:
            _t1052 = None
        return None

    @staticmethod
    def _try_extract_value_uint128(value: Optional[logic_pb2.Value]) -> Optional[logic_pb2.UInt128Value]:
        if (value is not None and value.HasField('uint128_value')):
            return value.uint128_value
        else:
            _t1054 = None
        return None

    @staticmethod
    def _try_extract_value_string_list(value: Optional[logic_pb2.Value]) -> Optional[list[str]]:
        if (value is not None and value.HasField('string_value')):
            return [value.string_value]
        else:
            _t1055 = None
        return None

    @staticmethod
    def construct_csv_config(config_dict: list[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1056 = Parser._extract_value_int64(config.get('csv_header_row'), 1)
        header_row = _t1056
        _t1057 = Parser._extract_value_int64(config.get('csv_skip'), 0)
        skip = _t1057
        _t1058 = Parser._extract_value_string(config.get('csv_new_line'), '')
        new_line = _t1058
        _t1059 = Parser._extract_value_string(config.get('csv_delimiter'), ',')
        delimiter = _t1059
        _t1060 = Parser._extract_value_string(config.get('csv_quotechar'), '"')
        quotechar = _t1060
        _t1061 = Parser._extract_value_string(config.get('csv_escapechar'), '"')
        escapechar = _t1061
        _t1062 = Parser._extract_value_string(config.get('csv_comment'), '')
        comment = _t1062
        _t1063 = Parser._extract_value_string_list(config.get('csv_missing_strings'), [])
        missing_strings = _t1063
        _t1064 = Parser._extract_value_string(config.get('csv_decimal_separator'), '.')
        decimal_separator = _t1064
        _t1065 = Parser._extract_value_string(config.get('csv_encoding'), 'utf-8')
        encoding = _t1065
        _t1066 = Parser._extract_value_string(config.get('csv_compression'), 'auto')
        compression = _t1066
        _t1067 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t1067

    @staticmethod
    def construct_betree_info(key_types: list[logic_pb2.Type], value_types: list[logic_pb2.Type], config_dict: list[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1068 = Parser._try_extract_value_float64(config.get('betree_config_epsilon'))
        epsilon = _t1068
        _t1069 = Parser._try_extract_value_int64(config.get('betree_config_max_pivots'))
        max_pivots = _t1069
        _t1070 = Parser._try_extract_value_int64(config.get('betree_config_max_deltas'))
        max_deltas = _t1070
        _t1071 = Parser._try_extract_value_int64(config.get('betree_config_max_leaf'))
        max_leaf = _t1071
        _t1072 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1072
        _t1073 = Parser._try_extract_value_uint128(config.get('betree_locator_root_pageid'))
        root_pageid = _t1073
        _t1074 = Parser._try_extract_value_bytes(config.get('betree_locator_inline_data'))
        inline_data = _t1074
        _t1075 = Parser._try_extract_value_int64(config.get('betree_locator_element_count'))
        element_count = _t1075
        _t1076 = Parser._try_extract_value_int64(config.get('betree_locator_tree_height'))
        tree_height = _t1076
        _t1077 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1077
        _t1078 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1078

    @staticmethod
    def construct_configure(config_dict: list[tuple[str, logic_pb2.Value]]) -> transactions_pb2.Configure:
        config = dict(config_dict)
        maintenance_level_val = config.get('ivm.maintenance_level')
        maintenance_level = None
        if (maintenance_level_val is not None and maintenance_level_val.HasField('string_value')):
            _t1080 = maintenance_level_val.string_value.upper()
            level_str = _t1080
            if level_str in ['OFF', 'AUTO', 'ALL']:
                maintenance_level = ('MAINTENANCE_LEVEL_' + level_str)
                _t1081 = None
            else:
                maintenance_level = level_str
                _t1081 = None
            _t1079 = _t1081
        else:
            maintenance_level = 'MAINTENANCE_LEVEL_OFF'
            _t1079 = None
        _t1082 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1082
        _t1083 = Parser._extract_value_int64(config.get('semantics_version'), 0)
        semantics_version = _t1083
        _t1084 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1084

    @staticmethod
    def export_csv_config(path: str, columns: list[transactions_pb2.ExportCSVColumn], config_dict: list[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1085 = Parser._extract_value_int64(config.get('partition_size'), 0)
        partition_size = _t1085
        _t1086 = Parser._extract_value_string(config.get('compression'), '')
        compression = _t1086
        _t1087 = Parser._extract_value_boolean(config.get('syntax_header_row'), True)
        syntax_header_row = _t1087
        _t1088 = Parser._extract_value_string(config.get('syntax_missing_string'), '')
        syntax_missing_string = _t1088
        _t1089 = Parser._extract_value_string(config.get('syntax_delim'), ',')
        syntax_delim = _t1089
        _t1090 = Parser._extract_value_string(config.get('syntax_quotechar'), '"')
        syntax_quotechar = _t1090
        _t1091 = Parser._extract_value_string(config.get('syntax_escapechar'), '\\')
        syntax_escapechar = _t1091
        _t1092 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1092

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        self.consume_literal('(')
        self.consume_literal('transaction')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('configure', 1)):
            _t354 = self.parse_configure()
            _t353 = _t354
        else:
            _t353 = None
        configure0 = _t353
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('sync', 1)):
            _t356 = self.parse_sync()
            _t355 = _t356
        else:
            _t355 = None
        sync1 = _t355
        xs2 = []
        cond3 = self.match_lookahead_literal('(', 0)
        while cond3:
            _t357 = self.parse_epoch()
            item4 = _t357
            xs2.append(item4)
            cond3 = self.match_lookahead_literal('(', 0)
        epochs5 = xs2
        self.consume_literal(')')
        _t358 = transactions_pb2.Transaction(epochs=epochs5, configure=(configure0 if configure0 is not None else self.construct_configure([])), sync=sync1)
        return _t358

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal('(')
        self.consume_literal('configure')
        _t359 = self.parse_config_dict()
        config_dict6 = _t359
        self.consume_literal(')')
        return self.construct_configure(config_dict6)

    def parse_config_dict(self) -> list[tuple[str, logic_pb2.Value]]:
        self.consume_literal('{')
        xs7 = []
        cond8 = self.match_lookahead_literal(':', 0)
        while cond8:
            _t360 = self.parse_config_key_value()
            item9 = _t360
            xs7.append(item9)
            cond8 = self.match_lookahead_literal(':', 0)
        config_key_values10 = xs7
        self.consume_literal('}')
        return config_key_values10

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(':')
        symbol11 = self.consume_terminal('SYMBOL')
        _t361 = self.parse_value()
        value12 = _t361
        return (symbol11, value12,)

    def parse_value(self) -> logic_pb2.Value:
        if self.match_lookahead_literal('true', 0):
            _t362 = 9
        else:
            if self.match_lookahead_literal('missing', 0):
                _t363 = 8
            else:
                if self.match_lookahead_literal('false', 0):
                    _t364 = 9
                else:
                    if self.match_lookahead_literal('(', 0):
                        if self.match_lookahead_literal('datetime', 1):
                            _t367 = 1
                        else:
                            if self.match_lookahead_literal('date', 1):
                                _t368 = 0
                            else:
                                _t368 = -1
                            _t367 = _t368
                        _t365 = _t367
                    else:
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t369 = 5
                        else:
                            if self.match_lookahead_terminal('STRING', 0):
                                _t370 = 2
                            else:
                                if self.match_lookahead_terminal('INT128', 0):
                                    _t371 = 6
                                else:
                                    if self.match_lookahead_terminal('INT', 0):
                                        _t372 = 3
                                    else:
                                        if self.match_lookahead_terminal('FLOAT', 0):
                                            _t373 = 4
                                        else:
                                            if self.match_lookahead_terminal('DECIMAL', 0):
                                                _t374 = 7
                                            else:
                                                _t374 = -1
                                            _t373 = _t374
                                        _t372 = _t373
                                    _t371 = _t372
                                _t370 = _t371
                            _t369 = _t370
                        _t365 = _t369
                    _t364 = _t365
                _t363 = _t364
            _t362 = _t363
        prediction13 = _t362
        if prediction13 == 9:
            _t376 = self.parse_boolean_value()
            boolean_value22 = _t376
            _t377 = logic_pb2.Value(boolean_value=boolean_value22)
            _t375 = _t377
        else:
            if prediction13 == 8:
                self.consume_literal('missing')
                _t379 = logic_pb2.Value(missing_value=logic_pb2.MissingValue())
                _t378 = _t379
            else:
                if prediction13 == 7:
                    decimal21 = self.consume_terminal('DECIMAL')
                    _t381 = logic_pb2.Value(decimal_value=decimal21)
                    _t380 = _t381
                else:
                    if prediction13 == 6:
                        int12820 = self.consume_terminal('INT128')
                        _t383 = logic_pb2.Value(int128_value=int12820)
                        _t382 = _t383
                    else:
                        if prediction13 == 5:
                            uint12819 = self.consume_terminal('UINT128')
                            _t385 = logic_pb2.Value(uint128_value=uint12819)
                            _t384 = _t385
                        else:
                            if prediction13 == 4:
                                float18 = self.consume_terminal('FLOAT')
                                _t387 = logic_pb2.Value(float_value=float18)
                                _t386 = _t387
                            else:
                                if prediction13 == 3:
                                    int17 = self.consume_terminal('INT')
                                    _t389 = logic_pb2.Value(int_value=int17)
                                    _t388 = _t389
                                else:
                                    if prediction13 == 2:
                                        string16 = self.consume_terminal('STRING')
                                        _t391 = logic_pb2.Value(string_value=string16)
                                        _t390 = _t391
                                    else:
                                        if prediction13 == 1:
                                            _t393 = self.parse_datetime()
                                            datetime15 = _t393
                                            _t394 = logic_pb2.Value(datetime_value=datetime15)
                                            _t392 = _t394
                                        else:
                                            if prediction13 == 0:
                                                _t396 = self.parse_date()
                                                date14 = _t396
                                                _t397 = logic_pb2.Value(date_value=date14)
                                                _t395 = _t397
                                            else:
                                                raise ParseError(f"{'Unexpected token in value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t395 = None
                                            _t392 = _t395
                                        _t390 = _t392
                                    _t388 = _t390
                                _t386 = _t388
                            _t384 = _t386
                        _t382 = _t384
                    _t380 = _t382
                _t378 = _t380
            _t375 = _t378
        return _t375

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal('(')
        self.consume_literal('date')
        int23 = self.consume_terminal('INT')
        int_324 = self.consume_terminal('INT')
        int_425 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t398 = logic_pb2.DateValue(year=int(int23), month=int(int_324), day=int(int_425))
        return _t398

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        self.consume_literal('(')
        self.consume_literal('datetime')
        int26 = self.consume_terminal('INT')
        int_327 = self.consume_terminal('INT')
        int_428 = self.consume_terminal('INT')
        int_529 = self.consume_terminal('INT')
        int_630 = self.consume_terminal('INT')
        int_731 = self.consume_terminal('INT')
        if self.match_lookahead_terminal('INT', 0):
            _t399 = self.consume_terminal('INT')
        else:
            _t399 = None
        int_832 = _t399
        self.consume_literal(')')
        _t400 = logic_pb2.DateTimeValue(year=int(int26), month=int(int_327), day=int(int_428), hour=int(int_529), minute=int(int_630), second=int(int_731), microsecond=int((int_832 if int_832 is not None else 0)))
        return _t400

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal('true', 0):
            _t401 = 0
        else:
            _t401 = (self.match_lookahead_literal('false', 0) or -1)
        prediction33 = _t401
        if prediction33 == 1:
            self.consume_literal('false')
            _t402 = False
        else:
            if prediction33 == 0:
                self.consume_literal('true')
                _t403 = True
            else:
                raise ParseError(f"{'Unexpected token in boolean_value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t403 = None
            _t402 = _t403
        return _t402

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal('(')
        self.consume_literal('sync')
        xs34 = []
        cond35 = self.match_lookahead_literal(':', 0)
        while cond35:
            _t404 = self.parse_fragment_id()
            item36 = _t404
            xs34.append(item36)
            cond35 = self.match_lookahead_literal(':', 0)
        fragment_ids37 = xs34
        self.consume_literal(')')
        _t405 = transactions_pb2.Sync(fragments=fragment_ids37)
        return _t405

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        self.consume_literal(':')
        symbol38 = self.consume_terminal('SYMBOL')
        return fragments_pb2.FragmentId(id=symbol38.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal('(')
        self.consume_literal('epoch')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('writes', 1)):
            _t407 = self.parse_epoch_writes()
            _t406 = _t407
        else:
            _t406 = None
        epoch_writes39 = _t406
        if self.match_lookahead_literal('(', 0):
            _t409 = self.parse_epoch_reads()
            _t408 = _t409
        else:
            _t408 = None
        epoch_reads40 = _t408
        self.consume_literal(')')
        _t410 = transactions_pb2.Epoch(writes=(epoch_writes39 if epoch_writes39 is not None else []), reads=(epoch_reads40 if epoch_reads40 is not None else []))
        return _t410

    def parse_epoch_writes(self) -> list[transactions_pb2.Write]:
        self.consume_literal('(')
        self.consume_literal('writes')
        xs41 = []
        cond42 = self.match_lookahead_literal('(', 0)
        while cond42:
            _t411 = self.parse_write()
            item43 = _t411
            xs41.append(item43)
            cond42 = self.match_lookahead_literal('(', 0)
        writes44 = xs41
        self.consume_literal(')')
        return writes44

    def parse_write(self) -> transactions_pb2.Write:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('undefine', 1):
                _t415 = 1
            else:
                if self.match_lookahead_literal('define', 1):
                    _t416 = 0
                else:
                    if self.match_lookahead_literal('context', 1):
                        _t417 = 2
                    else:
                        _t417 = -1
                    _t416 = _t417
                _t415 = _t416
            _t412 = _t415
        else:
            _t412 = -1
        prediction45 = _t412
        if prediction45 == 2:
            _t419 = self.parse_context()
            context48 = _t419
            _t420 = transactions_pb2.Write(context=context48)
            _t418 = _t420
        else:
            if prediction45 == 1:
                _t422 = self.parse_undefine()
                undefine47 = _t422
                _t423 = transactions_pb2.Write(undefine=undefine47)
                _t421 = _t423
            else:
                if prediction45 == 0:
                    _t425 = self.parse_define()
                    define46 = _t425
                    _t426 = transactions_pb2.Write(define=define46)
                    _t424 = _t426
                else:
                    raise ParseError(f"{'Unexpected token in write'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t424 = None
                _t421 = _t424
            _t418 = _t421
        return _t418

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal('(')
        self.consume_literal('define')
        _t427 = self.parse_fragment()
        fragment49 = _t427
        self.consume_literal(')')
        _t428 = transactions_pb2.Define(fragment=fragment49)
        return _t428

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal('(')
        self.consume_literal('fragment')
        _t429 = self.parse_new_fragment_id()
        new_fragment_id50 = _t429
        xs51 = []
        cond52 = self.match_lookahead_literal('(', 0)
        while cond52:
            _t430 = self.parse_declaration()
            item53 = _t430
            xs51.append(item53)
            cond52 = self.match_lookahead_literal('(', 0)
        declarations54 = xs51
        self.consume_literal(')')
        return self.construct_fragment(new_fragment_id50, declarations54)

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        _t431 = self.parse_fragment_id()
        fragment_id55 = _t431
        self.start_fragment(fragment_id55)
        return fragment_id55

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('rel_edb', 1):
                _t433 = 3
            else:
                if self.match_lookahead_literal('functional_dependency', 1):
                    _t434 = 2
                else:
                    if self.match_lookahead_literal('def', 1):
                        _t435 = 0
                    else:
                        if self.match_lookahead_literal('csv_data', 1):
                            _t436 = 3
                        else:
                            if self.match_lookahead_literal('betree_relation', 1):
                                _t437 = 3
                            else:
                                _t437 = (self.match_lookahead_literal('algorithm', 1) or -1)
                            _t436 = _t437
                        _t435 = _t436
                    _t434 = _t435
                _t433 = _t434
            _t432 = _t433
        else:
            _t432 = -1
        prediction56 = _t432
        if prediction56 == 3:
            _t439 = self.parse_data()
            data60 = _t439
            _t440 = logic_pb2.Declaration(data=data60)
            _t438 = _t440
        else:
            if prediction56 == 2:
                _t442 = self.parse_constraint()
                constraint59 = _t442
                _t443 = logic_pb2.Declaration(constraint=constraint59)
                _t441 = _t443
            else:
                if prediction56 == 1:
                    _t445 = self.parse_algorithm()
                    algorithm58 = _t445
                    _t446 = logic_pb2.Declaration(algorithm=algorithm58)
                    _t444 = _t446
                else:
                    if prediction56 == 0:
                        _t448 = self.parse_def()
                        def57 = _t448
                        _t449 = logic_pb2.Declaration()
                        getattr(_t449, 'def').CopyFrom(def57)
                        _t447 = _t449
                    else:
                        raise ParseError(f"{'Unexpected token in declaration'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t447 = None
                    _t444 = _t447
                _t441 = _t444
            _t438 = _t441
        return _t438

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal('(')
        self.consume_literal('def')
        _t450 = self.parse_relation_id()
        relation_id61 = _t450
        _t451 = self.parse_abstraction()
        abstraction62 = _t451
        if self.match_lookahead_literal('(', 0):
            _t453 = self.parse_attrs()
            _t452 = _t453
        else:
            _t452 = None
        attrs63 = _t452
        self.consume_literal(')')
        _t454 = logic_pb2.Def(name=relation_id61, body=abstraction62, attrs=(attrs63 if attrs63 is not None else []))
        return _t454

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_literal(':', 0):
            _t455 = 0
        else:
            _t455 = (self.match_lookahead_terminal('INT', 0) or -1)
        prediction64 = _t455
        if prediction64 == 1:
            int66 = self.consume_terminal('INT')
            _t456 = logic_pb2.RelationId(id_low=int66 & 0xFFFFFFFFFFFFFFFF, id_high=(int66 >> 64) & 0xFFFFFFFFFFFFFFFF)
        else:
            if prediction64 == 0:
                self.consume_literal(':')
                symbol65 = self.consume_terminal('SYMBOL')
                _t457 = self.relation_id_from_string(symbol65)
            else:
                raise ParseError(f"{'Unexpected token in relation_id'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t457 = None
            _t456 = _t457
        return _t456

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal('(')
        _t458 = self.parse_bindings()
        bindings67 = _t458
        _t459 = self.parse_formula()
        formula68 = _t459
        self.consume_literal(')')
        _t460 = logic_pb2.Abstraction(vars=(bindings67[0] + (bindings67[1] if bindings67[1] is not None else [])), value=formula68)
        return _t460

    def parse_bindings(self) -> tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]:
        self.consume_literal('[')
        xs69 = []
        cond70 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond70:
            _t461 = self.parse_binding()
            item71 = _t461
            xs69.append(item71)
            cond70 = self.match_lookahead_terminal('SYMBOL', 0)
        bindings72 = xs69
        if self.match_lookahead_literal('|', 0):
            _t463 = self.parse_value_bindings()
            _t462 = _t463
        else:
            _t462 = None
        value_bindings73 = _t462
        self.consume_literal(']')
        return (bindings72, (value_bindings73 if value_bindings73 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol74 = self.consume_terminal('SYMBOL')
        self.consume_literal('::')
        _t464 = self.parse_type()
        type75 = _t464
        _t465 = logic_pb2.Var(name=symbol74)
        _t466 = logic_pb2.Binding(var=_t465, type=type75)
        return _t466

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal('UNKNOWN', 0):
            _t467 = 0
        else:
            if self.match_lookahead_literal('UINT128', 0):
                _t468 = 4
            else:
                if self.match_lookahead_literal('STRING', 0):
                    _t477 = 1
                else:
                    if self.match_lookahead_literal('MISSING', 0):
                        _t478 = 8
                    else:
                        if self.match_lookahead_literal('INT128', 0):
                            _t479 = 5
                        else:
                            if self.match_lookahead_literal('INT', 0):
                                _t480 = 2
                            else:
                                if self.match_lookahead_literal('FLOAT', 0):
                                    _t481 = 3
                                else:
                                    if self.match_lookahead_literal('DATETIME', 0):
                                        _t482 = 7
                                    else:
                                        if self.match_lookahead_literal('DATE', 0):
                                            _t483 = 6
                                        else:
                                            if self.match_lookahead_literal('BOOLEAN', 0):
                                                _t484 = 10
                                            else:
                                                if self.match_lookahead_literal('(', 0):
                                                    _t485 = 9
                                                else:
                                                    _t485 = -1
                                                _t484 = _t485
                                            _t483 = _t484
                                        _t482 = _t483
                                    _t481 = _t482
                                _t480 = _t481
                            _t479 = _t480
                        _t478 = _t479
                    _t477 = _t478
                _t468 = _t477
            _t467 = _t468
        prediction76 = _t467
        if prediction76 == 10:
            _t487 = self.parse_boolean_type()
            boolean_type87 = _t487
            _t488 = logic_pb2.Type(boolean_type=boolean_type87)
            _t486 = _t488
        else:
            if prediction76 == 9:
                _t490 = self.parse_decimal_type()
                decimal_type86 = _t490
                _t491 = logic_pb2.Type(decimal_type=decimal_type86)
                _t489 = _t491
            else:
                if prediction76 == 8:
                    _t493 = self.parse_missing_type()
                    missing_type85 = _t493
                    _t494 = logic_pb2.Type(missing_type=missing_type85)
                    _t492 = _t494
                else:
                    if prediction76 == 7:
                        _t496 = self.parse_datetime_type()
                        datetime_type84 = _t496
                        _t497 = logic_pb2.Type(datetime_type=datetime_type84)
                        _t495 = _t497
                    else:
                        if prediction76 == 6:
                            _t499 = self.parse_date_type()
                            date_type83 = _t499
                            _t500 = logic_pb2.Type(date_type=date_type83)
                            _t498 = _t500
                        else:
                            if prediction76 == 5:
                                _t502 = self.parse_int128_type()
                                int128_type82 = _t502
                                _t503 = logic_pb2.Type(int128_type=int128_type82)
                                _t501 = _t503
                            else:
                                if prediction76 == 4:
                                    _t505 = self.parse_uint128_type()
                                    uint128_type81 = _t505
                                    _t506 = logic_pb2.Type(uint128_type=uint128_type81)
                                    _t504 = _t506
                                else:
                                    if prediction76 == 3:
                                        _t508 = self.parse_float_type()
                                        float_type80 = _t508
                                        _t509 = logic_pb2.Type(float_type=float_type80)
                                        _t507 = _t509
                                    else:
                                        if prediction76 == 2:
                                            _t511 = self.parse_int_type()
                                            int_type79 = _t511
                                            _t512 = logic_pb2.Type(int_type=int_type79)
                                            _t510 = _t512
                                        else:
                                            if prediction76 == 1:
                                                _t514 = self.parse_string_type()
                                                string_type78 = _t514
                                                _t515 = logic_pb2.Type(string_type=string_type78)
                                                _t513 = _t515
                                            else:
                                                if prediction76 == 0:
                                                    _t517 = self.parse_unspecified_type()
                                                    unspecified_type77 = _t517
                                                    _t518 = logic_pb2.Type(unspecified_type=unspecified_type77)
                                                    _t516 = _t518
                                                else:
                                                    raise ParseError(f"{'Unexpected token in type'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                    _t516 = None
                                                _t513 = _t516
                                            _t510 = _t513
                                        _t507 = _t510
                                    _t504 = _t507
                                _t501 = _t504
                            _t498 = _t501
                        _t495 = _t498
                    _t492 = _t495
                _t489 = _t492
            _t486 = _t489
        return _t486

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        self.consume_literal('UNKNOWN')
        return logic_pb2.UnspecifiedType()

    def parse_string_type(self) -> logic_pb2.StringType:
        self.consume_literal('STRING')
        return logic_pb2.StringType()

    def parse_int_type(self) -> logic_pb2.IntType:
        self.consume_literal('INT')
        return logic_pb2.IntType()

    def parse_float_type(self) -> logic_pb2.FloatType:
        self.consume_literal('FLOAT')
        return logic_pb2.FloatType()

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        self.consume_literal('UINT128')
        return logic_pb2.UInt128Type()

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        self.consume_literal('INT128')
        return logic_pb2.Int128Type()

    def parse_date_type(self) -> logic_pb2.DateType:
        self.consume_literal('DATE')
        return logic_pb2.DateType()

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        self.consume_literal('DATETIME')
        return logic_pb2.DateTimeType()

    def parse_missing_type(self) -> logic_pb2.MissingType:
        self.consume_literal('MISSING')
        return logic_pb2.MissingType()

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        self.consume_literal('(')
        self.consume_literal('DECIMAL')
        int88 = self.consume_terminal('INT')
        int_389 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t519 = logic_pb2.DecimalType(precision=int(int88), scale=int(int_389))
        return _t519

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal('BOOLEAN')
        return logic_pb2.BooleanType()

    def parse_value_bindings(self) -> list[logic_pb2.Binding]:
        self.consume_literal('|')
        xs90 = []
        cond91 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond91:
            _t520 = self.parse_binding()
            item92 = _t520
            xs90.append(item92)
            cond91 = self.match_lookahead_terminal('SYMBOL', 0)
        bindings93 = xs90
        return bindings93

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('true', 1):
                _t522 = 0
            else:
                if self.match_lookahead_literal('relatom', 1):
                    _t523 = 11
                else:
                    if self.match_lookahead_literal('reduce', 1):
                        _t524 = 3
                    else:
                        if self.match_lookahead_literal('primitive', 1):
                            _t525 = 10
                        else:
                            if self.match_lookahead_literal('pragma', 1):
                                _t526 = 9
                            else:
                                if self.match_lookahead_literal('or', 1):
                                    _t527 = 5
                                else:
                                    if self.match_lookahead_literal('not', 1):
                                        _t528 = 6
                                    else:
                                        if self.match_lookahead_literal('ffi', 1):
                                            _t529 = 7
                                        else:
                                            if self.match_lookahead_literal('false', 1):
                                                _t543 = 1
                                            else:
                                                if self.match_lookahead_literal('exists', 1):
                                                    _t544 = 2
                                                else:
                                                    if self.match_lookahead_literal('cast', 1):
                                                        _t545 = 12
                                                    else:
                                                        if self.match_lookahead_literal('atom', 1):
                                                            _t546 = 8
                                                        else:
                                                            if self.match_lookahead_literal('and', 1):
                                                                _t547 = 4
                                                            else:
                                                                if self.match_lookahead_literal('>=', 1):
                                                                    _t548 = 10
                                                                else:
                                                                    if self.match_lookahead_literal('>', 1):
                                                                        _t549 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal('=', 1):
                                                                            _t550 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal('<=', 1):
                                                                                _t551 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal('<', 1):
                                                                                    _t552 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal('/', 1):
                                                                                        _t553 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal('-', 1):
                                                                                            _t554 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal('+', 1):
                                                                                                _t555 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal('*', 1):
                                                                                                    _t556 = 10
                                                                                                else:
                                                                                                    _t556 = -1
                                                                                                _t555 = _t556
                                                                                            _t554 = _t555
                                                                                        _t553 = _t554
                                                                                    _t552 = _t553
                                                                                _t551 = _t552
                                                                            _t550 = _t551
                                                                        _t549 = _t550
                                                                    _t548 = _t549
                                                                _t547 = _t548
                                                            _t546 = _t547
                                                        _t545 = _t546
                                                    _t544 = _t545
                                                _t543 = _t544
                                            _t529 = _t543
                                        _t528 = _t529
                                    _t527 = _t528
                                _t526 = _t527
                            _t525 = _t526
                        _t524 = _t525
                    _t523 = _t524
                _t522 = _t523
            _t521 = _t522
        else:
            _t521 = -1
        prediction94 = _t521
        if prediction94 == 12:
            _t558 = self.parse_cast()
            cast107 = _t558
            _t559 = logic_pb2.Formula(cast=cast107)
            _t557 = _t559
        else:
            if prediction94 == 11:
                _t561 = self.parse_rel_atom()
                rel_atom106 = _t561
                _t562 = logic_pb2.Formula(rel_atom=rel_atom106)
                _t560 = _t562
            else:
                if prediction94 == 10:
                    _t564 = self.parse_primitive()
                    primitive105 = _t564
                    _t565 = logic_pb2.Formula(primitive=primitive105)
                    _t563 = _t565
                else:
                    if prediction94 == 9:
                        _t567 = self.parse_pragma()
                        pragma104 = _t567
                        _t568 = logic_pb2.Formula(pragma=pragma104)
                        _t566 = _t568
                    else:
                        if prediction94 == 8:
                            _t570 = self.parse_atom()
                            atom103 = _t570
                            _t571 = logic_pb2.Formula(atom=atom103)
                            _t569 = _t571
                        else:
                            if prediction94 == 7:
                                _t573 = self.parse_ffi()
                                ffi102 = _t573
                                _t574 = logic_pb2.Formula(ffi=ffi102)
                                _t572 = _t574
                            else:
                                if prediction94 == 6:
                                    _t576 = self.parse_not()
                                    not101 = _t576
                                    _t577 = logic_pb2.Formula()
                                    getattr(_t577, 'not').CopyFrom(not101)
                                    _t575 = _t577
                                else:
                                    if prediction94 == 5:
                                        _t579 = self.parse_disjunction()
                                        disjunction100 = _t579
                                        _t580 = logic_pb2.Formula(disjunction=disjunction100)
                                        _t578 = _t580
                                    else:
                                        if prediction94 == 4:
                                            _t582 = self.parse_conjunction()
                                            conjunction99 = _t582
                                            _t583 = logic_pb2.Formula(conjunction=conjunction99)
                                            _t581 = _t583
                                        else:
                                            if prediction94 == 3:
                                                _t585 = self.parse_reduce()
                                                reduce98 = _t585
                                                _t586 = logic_pb2.Formula(reduce=reduce98)
                                                _t584 = _t586
                                            else:
                                                if prediction94 == 2:
                                                    _t588 = self.parse_exists()
                                                    exists97 = _t588
                                                    _t589 = logic_pb2.Formula(exists=exists97)
                                                    _t587 = _t589
                                                else:
                                                    if prediction94 == 1:
                                                        _t591 = self.parse_false()
                                                        false96 = _t591
                                                        _t592 = logic_pb2.Formula(disjunction=false96)
                                                        _t590 = _t592
                                                    else:
                                                        if prediction94 == 0:
                                                            _t594 = self.parse_true()
                                                            true95 = _t594
                                                            _t595 = logic_pb2.Formula(conjunction=true95)
                                                            _t593 = _t595
                                                        else:
                                                            raise ParseError(f"{'Unexpected token in formula'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t593 = None
                                                        _t590 = _t593
                                                    _t587 = _t590
                                                _t584 = _t587
                                            _t581 = _t584
                                        _t578 = _t581
                                    _t575 = _t578
                                _t572 = _t575
                            _t569 = _t572
                        _t566 = _t569
                    _t563 = _t566
                _t560 = _t563
            _t557 = _t560
        return _t557

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('true')
        self.consume_literal(')')
        _t596 = logic_pb2.Conjunction(args=[])
        return _t596

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('false')
        self.consume_literal(')')
        _t597 = logic_pb2.Disjunction(args=[])
        return _t597

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal('(')
        self.consume_literal('exists')
        _t598 = self.parse_bindings()
        bindings108 = _t598
        _t599 = self.parse_formula()
        formula109 = _t599
        self.consume_literal(')')
        _t600 = logic_pb2.Abstraction(vars=(bindings108[0] + (bindings108[1] if bindings108[1] is not None else [])), value=formula109)
        _t601 = logic_pb2.Exists(body=_t600)
        return _t601

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal('(')
        self.consume_literal('reduce')
        _t602 = self.parse_abstraction()
        abstraction110 = _t602
        _t603 = self.parse_abstraction()
        abstraction_3111 = _t603
        _t604 = self.parse_terms()
        terms112 = _t604
        self.consume_literal(')')
        _t605 = logic_pb2.Reduce(op=abstraction110, body=abstraction_3111, terms=terms112)
        return _t605

    def parse_terms(self) -> list[logic_pb2.Term]:
        self.consume_literal('(')
        self.consume_literal('terms')
        xs113 = []
        cond114 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond114:
            _t606 = self.parse_term()
            item115 = _t606
            xs113.append(item115)
            cond114 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms116 = xs113
        self.consume_literal(')')
        return terms116

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_literal('true', 0):
            _t638 = 1
        else:
            if self.match_lookahead_literal('missing', 0):
                _t654 = 1
            else:
                if self.match_lookahead_literal('false', 0):
                    _t662 = 1
                else:
                    if self.match_lookahead_literal('(', 0):
                        _t666 = 1
                    else:
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t668 = 1
                        else:
                            if self.match_lookahead_terminal('SYMBOL', 0):
                                _t669 = 0
                            else:
                                _t669 = (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or -1)))))
                            _t668 = _t669
                        _t666 = _t668
                    _t662 = _t666
                _t654 = _t662
            _t638 = _t654
        prediction117 = _t638
        if prediction117 == 1:
            _t671 = self.parse_constant()
            constant119 = _t671
            _t672 = logic_pb2.Term(constant=constant119)
            _t670 = _t672
        else:
            if prediction117 == 0:
                _t674 = self.parse_var()
                var118 = _t674
                _t675 = logic_pb2.Term(var=var118)
                _t673 = _t675
            else:
                raise ParseError(f"{'Unexpected token in term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t673 = None
            _t670 = _t673
        return _t670

    def parse_var(self) -> logic_pb2.Var:
        symbol120 = self.consume_terminal('SYMBOL')
        _t676 = logic_pb2.Var(name=symbol120)
        return _t676

    def parse_constant(self) -> logic_pb2.Value:
        _t677 = self.parse_value()
        value121 = _t677
        return value121

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('and')
        xs122 = []
        cond123 = self.match_lookahead_literal('(', 0)
        while cond123:
            _t678 = self.parse_formula()
            item124 = _t678
            xs122.append(item124)
            cond123 = self.match_lookahead_literal('(', 0)
        formulas125 = xs122
        self.consume_literal(')')
        _t679 = logic_pb2.Conjunction(args=formulas125)
        return _t679

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('or')
        xs126 = []
        cond127 = self.match_lookahead_literal('(', 0)
        while cond127:
            _t680 = self.parse_formula()
            item128 = _t680
            xs126.append(item128)
            cond127 = self.match_lookahead_literal('(', 0)
        formulas129 = xs126
        self.consume_literal(')')
        _t681 = logic_pb2.Disjunction(args=formulas129)
        return _t681

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal('(')
        self.consume_literal('not')
        _t682 = self.parse_formula()
        formula130 = _t682
        self.consume_literal(')')
        _t683 = logic_pb2.Not(arg=formula130)
        return _t683

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal('(')
        self.consume_literal('ffi')
        _t684 = self.parse_name()
        name131 = _t684
        _t685 = self.parse_ffi_args()
        ffi_args132 = _t685
        _t686 = self.parse_terms()
        terms133 = _t686
        self.consume_literal(')')
        _t687 = logic_pb2.FFI(name=name131, args=ffi_args132, terms=terms133)
        return _t687

    def parse_name(self) -> str:
        self.consume_literal(':')
        symbol134 = self.consume_terminal('SYMBOL')
        return symbol134

    def parse_ffi_args(self) -> list[logic_pb2.Abstraction]:
        self.consume_literal('(')
        self.consume_literal('args')
        xs135 = []
        cond136 = self.match_lookahead_literal('(', 0)
        while cond136:
            _t688 = self.parse_abstraction()
            item137 = _t688
            xs135.append(item137)
            cond136 = self.match_lookahead_literal('(', 0)
        abstractions138 = xs135
        self.consume_literal(')')
        return abstractions138

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal('(')
        self.consume_literal('atom')
        _t689 = self.parse_relation_id()
        relation_id139 = _t689
        xs140 = []
        cond141 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond141:
            _t690 = self.parse_term()
            item142 = _t690
            xs140.append(item142)
            cond141 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms143 = xs140
        self.consume_literal(')')
        _t691 = logic_pb2.Atom(name=relation_id139, terms=terms143)
        return _t691

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal('(')
        self.consume_literal('pragma')
        _t692 = self.parse_name()
        name144 = _t692
        xs145 = []
        cond146 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond146:
            _t693 = self.parse_term()
            item147 = _t693
            xs145.append(item147)
            cond146 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms148 = xs145
        self.consume_literal(')')
        _t694 = logic_pb2.Pragma(name=name144, terms=terms148)
        return _t694

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('primitive', 1):
                _t696 = 9
            else:
                if self.match_lookahead_literal('>=', 1):
                    _t697 = 4
                else:
                    if self.match_lookahead_literal('>', 1):
                        _t698 = 3
                    else:
                        if self.match_lookahead_literal('=', 1):
                            _t699 = 0
                        else:
                            if self.match_lookahead_literal('<=', 1):
                                _t700 = 2
                            else:
                                if self.match_lookahead_literal('<', 1):
                                    _t705 = 1
                                else:
                                    if self.match_lookahead_literal('/', 1):
                                        _t706 = 8
                                    else:
                                        if self.match_lookahead_literal('-', 1):
                                            _t707 = 6
                                        else:
                                            if self.match_lookahead_literal('+', 1):
                                                _t708 = 5
                                            else:
                                                if self.match_lookahead_literal('*', 1):
                                                    _t709 = 7
                                                else:
                                                    _t709 = -1
                                                _t708 = _t709
                                            _t707 = _t708
                                        _t706 = _t707
                                    _t705 = _t706
                                _t700 = _t705
                            _t699 = _t700
                        _t698 = _t699
                    _t697 = _t698
                _t696 = _t697
            _t695 = _t696
        else:
            _t695 = -1
        prediction149 = _t695
        if prediction149 == 9:
            self.consume_literal('(')
            self.consume_literal('primitive')
            _t711 = self.parse_name()
            name159 = _t711
            xs160 = []
            cond161 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            while cond161:
                _t712 = self.parse_rel_term()
                item162 = _t712
                xs160.append(item162)
                cond161 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            rel_terms163 = xs160
            self.consume_literal(')')
            _t713 = logic_pb2.Primitive(name=name159, terms=rel_terms163)
            _t710 = _t713
        else:
            if prediction149 == 8:
                _t715 = self.parse_divide()
                divide158 = _t715
                _t714 = divide158
            else:
                if prediction149 == 7:
                    _t717 = self.parse_multiply()
                    multiply157 = _t717
                    _t716 = multiply157
                else:
                    if prediction149 == 6:
                        _t719 = self.parse_minus()
                        minus156 = _t719
                        _t718 = minus156
                    else:
                        if prediction149 == 5:
                            _t721 = self.parse_add()
                            add155 = _t721
                            _t720 = add155
                        else:
                            if prediction149 == 4:
                                _t723 = self.parse_gt_eq()
                                gt_eq154 = _t723
                                _t722 = gt_eq154
                            else:
                                if prediction149 == 3:
                                    _t725 = self.parse_gt()
                                    gt153 = _t725
                                    _t724 = gt153
                                else:
                                    if prediction149 == 2:
                                        _t727 = self.parse_lt_eq()
                                        lt_eq152 = _t727
                                        _t726 = lt_eq152
                                    else:
                                        if prediction149 == 1:
                                            _t729 = self.parse_lt()
                                            lt151 = _t729
                                            _t728 = lt151
                                        else:
                                            if prediction149 == 0:
                                                _t731 = self.parse_eq()
                                                eq150 = _t731
                                                _t730 = eq150
                                            else:
                                                raise ParseError(f"{'Unexpected token in primitive'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t730 = None
                                            _t728 = _t730
                                        _t726 = _t728
                                    _t724 = _t726
                                _t722 = _t724
                            _t720 = _t722
                        _t718 = _t720
                    _t716 = _t718
                _t714 = _t716
            _t710 = _t714
        return _t710

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('=')
        _t732 = self.parse_term()
        term164 = _t732
        _t733 = self.parse_term()
        term_3165 = _t733
        self.consume_literal(')')
        _t734 = logic_pb2.RelTerm(term=term164)
        _t735 = logic_pb2.RelTerm(term=term_3165)
        _t736 = logic_pb2.Primitive(name='rel_primitive_eq', terms=[_t734, _t735])
        return _t736

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<')
        _t737 = self.parse_term()
        term166 = _t737
        _t738 = self.parse_term()
        term_3167 = _t738
        self.consume_literal(')')
        _t739 = logic_pb2.RelTerm(term=term166)
        _t740 = logic_pb2.RelTerm(term=term_3167)
        _t741 = logic_pb2.Primitive(name='rel_primitive_lt_monotype', terms=[_t739, _t740])
        return _t741

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<=')
        _t742 = self.parse_term()
        term168 = _t742
        _t743 = self.parse_term()
        term_3169 = _t743
        self.consume_literal(')')
        _t744 = logic_pb2.RelTerm(term=term168)
        _t745 = logic_pb2.RelTerm(term=term_3169)
        _t746 = logic_pb2.Primitive(name='rel_primitive_lt_eq_monotype', terms=[_t744, _t745])
        return _t746

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>')
        _t747 = self.parse_term()
        term170 = _t747
        _t748 = self.parse_term()
        term_3171 = _t748
        self.consume_literal(')')
        _t749 = logic_pb2.RelTerm(term=term170)
        _t750 = logic_pb2.RelTerm(term=term_3171)
        _t751 = logic_pb2.Primitive(name='rel_primitive_gt_monotype', terms=[_t749, _t750])
        return _t751

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>=')
        _t752 = self.parse_term()
        term172 = _t752
        _t753 = self.parse_term()
        term_3173 = _t753
        self.consume_literal(')')
        _t754 = logic_pb2.RelTerm(term=term172)
        _t755 = logic_pb2.RelTerm(term=term_3173)
        _t756 = logic_pb2.Primitive(name='rel_primitive_gt_eq_monotype', terms=[_t754, _t755])
        return _t756

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('+')
        _t757 = self.parse_term()
        term174 = _t757
        _t758 = self.parse_term()
        term_3175 = _t758
        _t759 = self.parse_term()
        term_4176 = _t759
        self.consume_literal(')')
        _t760 = logic_pb2.RelTerm(term=term174)
        _t761 = logic_pb2.RelTerm(term=term_3175)
        _t762 = logic_pb2.RelTerm(term=term_4176)
        _t763 = logic_pb2.Primitive(name='rel_primitive_add_monotype', terms=[_t760, _t761, _t762])
        return _t763

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('-')
        _t764 = self.parse_term()
        term177 = _t764
        _t765 = self.parse_term()
        term_3178 = _t765
        _t766 = self.parse_term()
        term_4179 = _t766
        self.consume_literal(')')
        _t767 = logic_pb2.RelTerm(term=term177)
        _t768 = logic_pb2.RelTerm(term=term_3178)
        _t769 = logic_pb2.RelTerm(term=term_4179)
        _t770 = logic_pb2.Primitive(name='rel_primitive_subtract_monotype', terms=[_t767, _t768, _t769])
        return _t770

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('*')
        _t771 = self.parse_term()
        term180 = _t771
        _t772 = self.parse_term()
        term_3181 = _t772
        _t773 = self.parse_term()
        term_4182 = _t773
        self.consume_literal(')')
        _t774 = logic_pb2.RelTerm(term=term180)
        _t775 = logic_pb2.RelTerm(term=term_3181)
        _t776 = logic_pb2.RelTerm(term=term_4182)
        _t777 = logic_pb2.Primitive(name='rel_primitive_multiply_monotype', terms=[_t774, _t775, _t776])
        return _t777

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('/')
        _t778 = self.parse_term()
        term183 = _t778
        _t779 = self.parse_term()
        term_3184 = _t779
        _t780 = self.parse_term()
        term_4185 = _t780
        self.consume_literal(')')
        _t781 = logic_pb2.RelTerm(term=term183)
        _t782 = logic_pb2.RelTerm(term=term_3184)
        _t783 = logic_pb2.RelTerm(term=term_4185)
        _t784 = logic_pb2.Primitive(name='rel_primitive_divide_monotype', terms=[_t781, _t782, _t783])
        return _t784

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_literal('true', 0):
            _t800 = 1
        else:
            if self.match_lookahead_literal('missing', 0):
                _t808 = 1
            else:
                if self.match_lookahead_literal('false', 0):
                    _t812 = 1
                else:
                    if self.match_lookahead_literal('(', 0):
                        _t814 = 1
                    else:
                        if self.match_lookahead_literal('#', 0):
                            _t815 = 0
                        else:
                            _t815 = (self.match_lookahead_terminal('UINT128', 0) or (self.match_lookahead_terminal('SYMBOL', 0) or (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or -1)))))))
                        _t814 = _t815
                    _t812 = _t814
                _t808 = _t812
            _t800 = _t808
        prediction186 = _t800
        if prediction186 == 1:
            _t817 = self.parse_term()
            term188 = _t817
            _t818 = logic_pb2.RelTerm(term=term188)
            _t816 = _t818
        else:
            if prediction186 == 0:
                _t820 = self.parse_specialized_value()
                specialized_value187 = _t820
                _t821 = logic_pb2.RelTerm(specialized_value=specialized_value187)
                _t819 = _t821
            else:
                raise ParseError(f"{'Unexpected token in rel_term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t819 = None
            _t816 = _t819
        return _t816

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal('#')
        _t822 = self.parse_value()
        value189 = _t822
        return value189

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        self.consume_literal('(')
        self.consume_literal('relatom')
        _t823 = self.parse_name()
        name190 = _t823
        xs191 = []
        cond192 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond192:
            _t824 = self.parse_rel_term()
            item193 = _t824
            xs191.append(item193)
            cond192 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        rel_terms194 = xs191
        self.consume_literal(')')
        _t825 = logic_pb2.RelAtom(name=name190, terms=rel_terms194)
        return _t825

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal('(')
        self.consume_literal('cast')
        _t826 = self.parse_term()
        term195 = _t826
        _t827 = self.parse_term()
        term_3196 = _t827
        self.consume_literal(')')
        _t828 = logic_pb2.Cast(input=term195, result=term_3196)
        return _t828

    def parse_attrs(self) -> list[logic_pb2.Attribute]:
        self.consume_literal('(')
        self.consume_literal('attrs')
        xs197 = []
        cond198 = self.match_lookahead_literal('(', 0)
        while cond198:
            _t829 = self.parse_attribute()
            item199 = _t829
            xs197.append(item199)
            cond198 = self.match_lookahead_literal('(', 0)
        attributes200 = xs197
        self.consume_literal(')')
        return attributes200

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal('(')
        self.consume_literal('attribute')
        _t830 = self.parse_name()
        name201 = _t830
        xs202 = []
        cond203 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond203:
            _t831 = self.parse_value()
            item204 = _t831
            xs202.append(item204)
            cond203 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        values205 = xs202
        self.consume_literal(')')
        _t832 = logic_pb2.Attribute(name=name201, args=values205)
        return _t832

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal('(')
        self.consume_literal('algorithm')
        xs206 = []
        cond207 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        while cond207:
            _t833 = self.parse_relation_id()
            item208 = _t833
            xs206.append(item208)
            cond207 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        relation_ids209 = xs206
        _t834 = self.parse_script()
        script210 = _t834
        self.consume_literal(')')
        _t835 = logic_pb2.Algorithm(body=script210)
        getattr(_t835, 'global').extend(relation_ids209)
        return _t835

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal('(')
        self.consume_literal('script')
        xs211 = []
        cond212 = self.match_lookahead_literal('(', 0)
        while cond212:
            _t836 = self.parse_construct()
            item213 = _t836
            xs211.append(item213)
            cond212 = self.match_lookahead_literal('(', 0)
        constructs214 = xs211
        self.consume_literal(')')
        _t837 = logic_pb2.Script(constructs=constructs214)
        return _t837

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t846 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t850 = 1
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t852 = 1
                    else:
                        if self.match_lookahead_literal('loop', 1):
                            _t853 = 0
                        else:
                            _t853 = (self.match_lookahead_literal('break', 1) or (self.match_lookahead_literal('assign', 1) or -1))
                        _t852 = _t853
                    _t850 = _t852
                _t846 = _t850
            _t838 = _t846
        else:
            _t838 = -1
        prediction215 = _t838
        if prediction215 == 1:
            _t855 = self.parse_instruction()
            instruction217 = _t855
            _t856 = logic_pb2.Construct(instruction=instruction217)
            _t854 = _t856
        else:
            if prediction215 == 0:
                _t858 = self.parse_loop()
                loop216 = _t858
                _t859 = logic_pb2.Construct(loop=loop216)
                _t857 = _t859
            else:
                raise ParseError(f"{'Unexpected token in construct'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t857 = None
            _t854 = _t857
        return _t854

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal('(')
        self.consume_literal('loop')
        _t860 = self.parse_init()
        init218 = _t860
        _t861 = self.parse_script()
        script219 = _t861
        self.consume_literal(')')
        _t862 = logic_pb2.Loop(init=init218, body=script219)
        return _t862

    def parse_init(self) -> list[logic_pb2.Instruction]:
        self.consume_literal('(')
        self.consume_literal('init')
        xs220 = []
        cond221 = self.match_lookahead_literal('(', 0)
        while cond221:
            _t863 = self.parse_instruction()
            item222 = _t863
            xs220.append(item222)
            cond221 = self.match_lookahead_literal('(', 0)
        instructions223 = xs220
        self.consume_literal(')')
        return instructions223

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t869 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t870 = 4
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t871 = 3
                    else:
                        if self.match_lookahead_literal('break', 1):
                            _t872 = 2
                        else:
                            if self.match_lookahead_literal('assign', 1):
                                _t873 = 0
                            else:
                                _t873 = -1
                            _t872 = _t873
                        _t871 = _t872
                    _t870 = _t871
                _t869 = _t870
            _t864 = _t869
        else:
            _t864 = -1
        prediction224 = _t864
        if prediction224 == 4:
            _t875 = self.parse_monus_def()
            monus_def229 = _t875
            _t876 = logic_pb2.Instruction(monus_def=monus_def229)
            _t874 = _t876
        else:
            if prediction224 == 3:
                _t878 = self.parse_monoid_def()
                monoid_def228 = _t878
                _t879 = logic_pb2.Instruction(monoid_def=monoid_def228)
                _t877 = _t879
            else:
                if prediction224 == 2:
                    _t881 = self.parse_break()
                    break227 = _t881
                    _t882 = logic_pb2.Instruction()
                    getattr(_t882, 'break').CopyFrom(break227)
                    _t880 = _t882
                else:
                    if prediction224 == 1:
                        _t884 = self.parse_upsert()
                        upsert226 = _t884
                        _t885 = logic_pb2.Instruction(upsert=upsert226)
                        _t883 = _t885
                    else:
                        if prediction224 == 0:
                            _t887 = self.parse_assign()
                            assign225 = _t887
                            _t888 = logic_pb2.Instruction(assign=assign225)
                            _t886 = _t888
                        else:
                            raise ParseError(f"{'Unexpected token in instruction'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t886 = None
                        _t883 = _t886
                    _t880 = _t883
                _t877 = _t880
            _t874 = _t877
        return _t874

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal('(')
        self.consume_literal('assign')
        _t889 = self.parse_relation_id()
        relation_id230 = _t889
        _t890 = self.parse_abstraction()
        abstraction231 = _t890
        if self.match_lookahead_literal('(', 0):
            _t892 = self.parse_attrs()
            _t891 = _t892
        else:
            _t891 = None
        attrs232 = _t891
        self.consume_literal(')')
        _t893 = logic_pb2.Assign(name=relation_id230, body=abstraction231, attrs=(attrs232 if attrs232 is not None else []))
        return _t893

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal('(')
        self.consume_literal('upsert')
        _t894 = self.parse_relation_id()
        relation_id233 = _t894
        _t895 = self.parse_abstraction_with_arity()
        abstraction_with_arity234 = _t895
        if self.match_lookahead_literal('(', 0):
            _t897 = self.parse_attrs()
            _t896 = _t897
        else:
            _t896 = None
        attrs235 = _t896
        self.consume_literal(')')
        _t898 = logic_pb2.Upsert(name=relation_id233, body=abstraction_with_arity234[0], attrs=(attrs235 if attrs235 is not None else []), value_arity=abstraction_with_arity234[1])
        return _t898

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal('(')
        _t899 = self.parse_bindings()
        bindings236 = _t899
        _t900 = self.parse_formula()
        formula237 = _t900
        self.consume_literal(')')
        _t901 = logic_pb2.Abstraction(vars=(bindings236[0] + (bindings236[1] if bindings236[1] is not None else [])), value=formula237)
        return (_t901, len(bindings236[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal('(')
        self.consume_literal('break')
        _t902 = self.parse_relation_id()
        relation_id238 = _t902
        _t903 = self.parse_abstraction()
        abstraction239 = _t903
        if self.match_lookahead_literal('(', 0):
            _t905 = self.parse_attrs()
            _t904 = _t905
        else:
            _t904 = None
        attrs240 = _t904
        self.consume_literal(')')
        _t906 = logic_pb2.Break(name=relation_id238, body=abstraction239, attrs=(attrs240 if attrs240 is not None else []))
        return _t906

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal('(')
        self.consume_literal('monoid')
        _t907 = self.parse_monoid()
        monoid241 = _t907
        _t908 = self.parse_relation_id()
        relation_id242 = _t908
        _t909 = self.parse_abstraction_with_arity()
        abstraction_with_arity243 = _t909
        if self.match_lookahead_literal('(', 0):
            _t911 = self.parse_attrs()
            _t910 = _t911
        else:
            _t910 = None
        attrs244 = _t910
        self.consume_literal(')')
        _t912 = logic_pb2.MonoidDef(monoid=monoid241, name=relation_id242, body=abstraction_with_arity243[0], attrs=(attrs244 if attrs244 is not None else []), value_arity=abstraction_with_arity243[1])
        return _t912

    def parse_monoid(self) -> logic_pb2.Monoid:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('sum', 1):
                _t914 = 3
            else:
                if self.match_lookahead_literal('or', 1):
                    _t915 = 0
                else:
                    if self.match_lookahead_literal('min', 1):
                        _t917 = 1
                    else:
                        if self.match_lookahead_literal('max', 1):
                            _t918 = 2
                        else:
                            _t918 = -1
                        _t917 = _t918
                    _t915 = _t917
                _t914 = _t915
            _t913 = _t914
        else:
            _t913 = -1
        prediction245 = _t913
        if prediction245 == 3:
            _t920 = self.parse_sum_monoid()
            sum_monoid249 = _t920
            _t921 = logic_pb2.Monoid(sum_monoid=sum_monoid249)
            _t919 = _t921
        else:
            if prediction245 == 2:
                _t923 = self.parse_max_monoid()
                max_monoid248 = _t923
                _t924 = logic_pb2.Monoid(max_monoid=max_monoid248)
                _t922 = _t924
            else:
                if prediction245 == 1:
                    _t926 = self.parse_min_monoid()
                    min_monoid247 = _t926
                    _t927 = logic_pb2.Monoid(min_monoid=min_monoid247)
                    _t925 = _t927
                else:
                    if prediction245 == 0:
                        _t929 = self.parse_or_monoid()
                        or_monoid246 = _t929
                        _t930 = logic_pb2.Monoid(or_monoid=or_monoid246)
                        _t928 = _t930
                    else:
                        raise ParseError(f"{'Unexpected token in monoid'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t928 = None
                    _t925 = _t928
                _t922 = _t925
            _t919 = _t922
        return _t919

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        self.consume_literal('(')
        self.consume_literal('or')
        self.consume_literal(')')
        return logic_pb2.OrMonoid()

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        self.consume_literal('(')
        self.consume_literal('min')
        _t931 = self.parse_type()
        type250 = _t931
        self.consume_literal(')')
        _t932 = logic_pb2.MinMonoid(type=type250)
        return _t932

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        self.consume_literal('(')
        self.consume_literal('max')
        _t933 = self.parse_type()
        type251 = _t933
        self.consume_literal(')')
        _t934 = logic_pb2.MaxMonoid(type=type251)
        return _t934

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        self.consume_literal('(')
        self.consume_literal('sum')
        _t935 = self.parse_type()
        type252 = _t935
        self.consume_literal(')')
        _t936 = logic_pb2.SumMonoid(type=type252)
        return _t936

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal('(')
        self.consume_literal('monus')
        _t937 = self.parse_monoid()
        monoid253 = _t937
        _t938 = self.parse_relation_id()
        relation_id254 = _t938
        _t939 = self.parse_abstraction_with_arity()
        abstraction_with_arity255 = _t939
        if self.match_lookahead_literal('(', 0):
            _t941 = self.parse_attrs()
            _t940 = _t941
        else:
            _t940 = None
        attrs256 = _t940
        self.consume_literal(')')
        _t942 = logic_pb2.MonusDef(monoid=monoid253, name=relation_id254, body=abstraction_with_arity255[0], attrs=(attrs256 if attrs256 is not None else []), value_arity=abstraction_with_arity255[1])
        return _t942

    def parse_constraint(self) -> logic_pb2.Constraint:
        self.consume_literal('(')
        self.consume_literal('functional_dependency')
        _t943 = self.parse_relation_id()
        relation_id257 = _t943
        _t944 = self.parse_abstraction()
        abstraction258 = _t944
        _t945 = self.parse_functional_dependency_keys()
        functional_dependency_keys259 = _t945
        _t946 = self.parse_functional_dependency_values()
        functional_dependency_values260 = _t946
        self.consume_literal(')')
        _t947 = logic_pb2.FunctionalDependency(guard=abstraction258, keys=functional_dependency_keys259, values=functional_dependency_values260)
        _t948 = logic_pb2.Constraint(name=relation_id257, functional_dependency=_t947)
        return _t948

    def parse_functional_dependency_keys(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('keys')
        xs261 = []
        cond262 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond262:
            _t949 = self.parse_var()
            item263 = _t949
            xs261.append(item263)
            cond262 = self.match_lookahead_terminal('SYMBOL', 0)
        vars264 = xs261
        self.consume_literal(')')
        return vars264

    def parse_functional_dependency_values(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('values')
        xs265 = []
        cond266 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond266:
            _t950 = self.parse_var()
            item267 = _t950
            xs265.append(item267)
            cond266 = self.match_lookahead_terminal('SYMBOL', 0)
        vars268 = xs265
        self.consume_literal(')')
        return vars268

    def parse_data(self) -> logic_pb2.Data:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('rel_edb', 1):
                _t952 = 0
            else:
                if self.match_lookahead_literal('csv_data', 1):
                    _t953 = 2
                else:
                    _t953 = (self.match_lookahead_literal('betree_relation', 1) or -1)
                _t952 = _t953
            _t951 = _t952
        else:
            _t951 = -1
        prediction269 = _t951
        if prediction269 == 2:
            _t955 = self.parse_csv_data()
            csv_data272 = _t955
            _t956 = logic_pb2.Data(csv_data=csv_data272)
            _t954 = _t956
        else:
            if prediction269 == 1:
                _t958 = self.parse_betree_relation()
                betree_relation271 = _t958
                _t959 = logic_pb2.Data(betree_relation=betree_relation271)
                _t957 = _t959
            else:
                if prediction269 == 0:
                    _t961 = self.parse_rel_edb()
                    rel_edb270 = _t961
                    _t962 = logic_pb2.Data(rel_edb=rel_edb270)
                    _t960 = _t962
                else:
                    raise ParseError(f"{'Unexpected token in data'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t960 = None
                _t957 = _t960
            _t954 = _t957
        return _t954

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        self.consume_literal('(')
        self.consume_literal('rel_edb')
        _t963 = self.parse_relation_id()
        relation_id273 = _t963
        _t964 = self.parse_rel_edb_path()
        rel_edb_path274 = _t964
        _t965 = self.parse_rel_edb_types()
        rel_edb_types275 = _t965
        self.consume_literal(')')
        _t966 = logic_pb2.RelEDB(target_id=relation_id273, path=rel_edb_path274, types=rel_edb_types275)
        return _t966

    def parse_rel_edb_path(self) -> list[str]:
        self.consume_literal('[')
        xs276 = []
        cond277 = self.match_lookahead_terminal('STRING', 0)
        while cond277:
            item278 = self.consume_terminal('STRING')
            xs276.append(item278)
            cond277 = self.match_lookahead_terminal('STRING', 0)
        strings279 = xs276
        self.consume_literal(']')
        return strings279

    def parse_rel_edb_types(self) -> list[logic_pb2.Type]:
        self.consume_literal('[')
        xs280 = []
        cond281 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond281:
            _t967 = self.parse_type()
            item282 = _t967
            xs280.append(item282)
            cond281 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types283 = xs280
        self.consume_literal(']')
        return types283

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        self.consume_literal('(')
        self.consume_literal('betree_relation')
        _t968 = self.parse_relation_id()
        relation_id284 = _t968
        _t969 = self.parse_betree_info()
        betree_info285 = _t969
        self.consume_literal(')')
        _t970 = logic_pb2.BeTreeRelation(name=relation_id284, relation_info=betree_info285)
        return _t970

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        self.consume_literal('(')
        self.consume_literal('betree_info')
        _t971 = self.parse_betree_info_key_types()
        betree_info_key_types286 = _t971
        _t972 = self.parse_betree_info_value_types()
        betree_info_value_types287 = _t972
        _t973 = self.parse_config_dict()
        config_dict288 = _t973
        self.consume_literal(')')
        return self.construct_betree_info(betree_info_key_types286, betree_info_value_types287, config_dict288)

    def parse_betree_info_key_types(self) -> list[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('key_types')
        xs289 = []
        cond290 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond290:
            _t974 = self.parse_type()
            item291 = _t974
            xs289.append(item291)
            cond290 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types292 = xs289
        self.consume_literal(')')
        return types292

    def parse_betree_info_value_types(self) -> list[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('value_types')
        xs293 = []
        cond294 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond294:
            _t975 = self.parse_type()
            item295 = _t975
            xs293.append(item295)
            cond294 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types296 = xs293
        self.consume_literal(')')
        return types296

    def parse_csv_data(self) -> logic_pb2.CSVData:
        self.consume_literal('(')
        self.consume_literal('csv_data')
        _t976 = self.parse_csvlocator()
        csvlocator297 = _t976
        _t977 = self.parse_csv_config()
        csv_config298 = _t977
        _t978 = self.parse_csv_columns()
        csv_columns299 = _t978
        _t979 = self.parse_csv_asof()
        csv_asof300 = _t979
        self.consume_literal(')')
        _t980 = logic_pb2.CSVData(locator=csvlocator297, config=csv_config298, columns=csv_columns299, asof=csv_asof300)
        return _t980

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        self.consume_literal('(')
        self.consume_literal('csv_locator')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('paths', 1)):
            _t982 = self.parse_csv_locator_paths()
            _t981 = _t982
        else:
            _t981 = None
        csv_locator_paths301 = _t981
        if self.match_lookahead_literal('(', 0):
            _t984 = self.parse_csv_locator_inline_data()
            _t983 = _t984
        else:
            _t983 = None
        csv_locator_inline_data302 = _t983
        self.consume_literal(')')
        _t985 = logic_pb2.CSVLocator(paths=(csv_locator_paths301 if csv_locator_paths301 is not None else []), inline_data=(csv_locator_inline_data302 if csv_locator_inline_data302 is not None else '').encode())
        return _t985

    def parse_csv_locator_paths(self) -> list[str]:
        self.consume_literal('(')
        self.consume_literal('paths')
        xs303 = []
        cond304 = self.match_lookahead_terminal('STRING', 0)
        while cond304:
            item305 = self.consume_terminal('STRING')
            xs303.append(item305)
            cond304 = self.match_lookahead_terminal('STRING', 0)
        strings306 = xs303
        self.consume_literal(')')
        return strings306

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal('(')
        self.consume_literal('inline_data')
        string307 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return string307

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        self.consume_literal('(')
        self.consume_literal('csv_config')
        _t986 = self.parse_config_dict()
        config_dict308 = _t986
        self.consume_literal(')')
        return self.construct_csv_config(config_dict308)

    def parse_csv_columns(self) -> list[logic_pb2.CSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs309 = []
        cond310 = self.match_lookahead_literal('(', 0)
        while cond310:
            _t987 = self.parse_csv_column()
            item311 = _t987
            xs309.append(item311)
            cond310 = self.match_lookahead_literal('(', 0)
        csv_columns312 = xs309
        self.consume_literal(')')
        return csv_columns312

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        string313 = self.consume_terminal('STRING')
        _t988 = self.parse_relation_id()
        relation_id314 = _t988
        self.consume_literal('[')
        xs315 = []
        cond316 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond316:
            _t989 = self.parse_type()
            item317 = _t989
            xs315.append(item317)
            cond316 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types318 = xs315
        self.consume_literal(']')
        self.consume_literal(')')
        _t990 = logic_pb2.CSVColumn(column_name=string313, target_id=relation_id314, types=types318)
        return _t990

    def parse_csv_asof(self) -> str:
        self.consume_literal('(')
        self.consume_literal('asof')
        string319 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return string319

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal('(')
        self.consume_literal('undefine')
        _t991 = self.parse_fragment_id()
        fragment_id320 = _t991
        self.consume_literal(')')
        _t992 = transactions_pb2.Undefine(fragment_id=fragment_id320)
        return _t992

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal('(')
        self.consume_literal('context')
        xs321 = []
        cond322 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        while cond322:
            _t993 = self.parse_relation_id()
            item323 = _t993
            xs321.append(item323)
            cond322 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        relation_ids324 = xs321
        self.consume_literal(')')
        _t994 = transactions_pb2.Context(relations=relation_ids324)
        return _t994

    def parse_epoch_reads(self) -> list[transactions_pb2.Read]:
        self.consume_literal('(')
        self.consume_literal('reads')
        xs325 = []
        cond326 = self.match_lookahead_literal('(', 0)
        while cond326:
            _t995 = self.parse_read()
            item327 = _t995
            xs325.append(item327)
            cond326 = self.match_lookahead_literal('(', 0)
        reads328 = xs325
        self.consume_literal(')')
        return reads328

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('what_if', 1):
                _t997 = 2
            else:
                if self.match_lookahead_literal('output', 1):
                    _t1001 = 1
                else:
                    if self.match_lookahead_literal('export', 1):
                        _t1002 = 4
                    else:
                        if self.match_lookahead_literal('demand', 1):
                            _t1003 = 0
                        else:
                            if self.match_lookahead_literal('abort', 1):
                                _t1004 = 3
                            else:
                                _t1004 = -1
                            _t1003 = _t1004
                        _t1002 = _t1003
                    _t1001 = _t1002
                _t997 = _t1001
            _t996 = _t997
        else:
            _t996 = -1
        prediction329 = _t996
        if prediction329 == 4:
            _t1006 = self.parse_export()
            export334 = _t1006
            _t1007 = transactions_pb2.Read(export=export334)
            _t1005 = _t1007
        else:
            if prediction329 == 3:
                _t1009 = self.parse_abort()
                abort333 = _t1009
                _t1010 = transactions_pb2.Read(abort=abort333)
                _t1008 = _t1010
            else:
                if prediction329 == 2:
                    _t1012 = self.parse_what_if()
                    what_if332 = _t1012
                    _t1013 = transactions_pb2.Read(what_if=what_if332)
                    _t1011 = _t1013
                else:
                    if prediction329 == 1:
                        _t1015 = self.parse_output()
                        output331 = _t1015
                        _t1016 = transactions_pb2.Read(output=output331)
                        _t1014 = _t1016
                    else:
                        if prediction329 == 0:
                            _t1018 = self.parse_demand()
                            demand330 = _t1018
                            _t1019 = transactions_pb2.Read(demand=demand330)
                            _t1017 = _t1019
                        else:
                            raise ParseError(f"{'Unexpected token in read'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t1017 = None
                        _t1014 = _t1017
                    _t1011 = _t1014
                _t1008 = _t1011
            _t1005 = _t1008
        return _t1005

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal('(')
        self.consume_literal('demand')
        _t1020 = self.parse_relation_id()
        relation_id335 = _t1020
        self.consume_literal(')')
        _t1021 = transactions_pb2.Demand(relation_id=relation_id335)
        return _t1021

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal('(')
        self.consume_literal('output')
        if (self.match_lookahead_literal(':', 0) and self.match_lookahead_terminal('SYMBOL', 1)):
            _t1023 = self.parse_name()
            _t1022 = _t1023
        else:
            _t1022 = None
        name336 = _t1022
        _t1024 = self.parse_relation_id()
        relation_id337 = _t1024
        self.consume_literal(')')
        _t1025 = transactions_pb2.Output(name=(name336 if name336 is not None else 'output'), relation_id=relation_id337)
        return _t1025

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal('(')
        self.consume_literal('what_if')
        _t1026 = self.parse_name()
        name338 = _t1026
        _t1027 = self.parse_epoch()
        epoch339 = _t1027
        self.consume_literal(')')
        _t1028 = transactions_pb2.WhatIf(branch=name338, epoch=epoch339)
        return _t1028

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal('(')
        self.consume_literal('abort')
        if (self.match_lookahead_literal(':', 0) and self.match_lookahead_terminal('SYMBOL', 1)):
            _t1030 = self.parse_name()
            _t1029 = _t1030
        else:
            _t1029 = None
        name340 = _t1029
        _t1031 = self.parse_relation_id()
        relation_id341 = _t1031
        self.consume_literal(')')
        _t1032 = transactions_pb2.Abort(name=(name340 if name340 is not None else 'abort'), relation_id=relation_id341)
        return _t1032

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal('(')
        self.consume_literal('export')
        _t1033 = self.parse_export_csv_config()
        export_csv_config342 = _t1033
        self.consume_literal(')')
        _t1034 = transactions_pb2.Export(csv_config=export_csv_config342)
        return _t1034

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal('(')
        self.consume_literal('export_csv_config')
        _t1035 = self.parse_export_csv_path()
        export_csv_path343 = _t1035
        _t1036 = self.parse_export_csv_columns()
        export_csv_columns344 = _t1036
        _t1037 = self.parse_config_dict()
        config_dict345 = _t1037
        self.consume_literal(')')
        return self.export_csv_config(export_csv_path343, export_csv_columns344, config_dict345)

    def parse_export_csv_path(self) -> str:
        self.consume_literal('(')
        self.consume_literal('path')
        string346 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return string346

    def parse_export_csv_columns(self) -> list[transactions_pb2.ExportCSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs347 = []
        cond348 = self.match_lookahead_literal('(', 0)
        while cond348:
            _t1038 = self.parse_export_csv_column()
            item349 = _t1038
            xs347.append(item349)
            cond348 = self.match_lookahead_literal('(', 0)
        export_csv_columns350 = xs347
        self.consume_literal(')')
        return export_csv_columns350

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        string351 = self.consume_terminal('STRING')
        _t1039 = self.parse_relation_id()
        relation_id352 = _t1039
        self.consume_literal(')')
        _t1040 = transactions_pb2.ExportCSVColumn(column_name=string351, column_data=relation_id352)
        return _t1040


def parse(input_str: str) -> Any:
    """Parse input string and return parse tree."""
    lexer = Lexer(input_str)
    parser = Parser(lexer.tokens)
    result = parser.parse_transaction()
    # Check for unconsumed tokens (except EOF)
    if parser.pos < len(parser.tokens):
        remaining_token = parser.lookahead(0)
        if remaining_token.type != '$':
            raise ParseError(f"Unexpected token at end of input: {remaining_token}")
    return result
