"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.


Command: python -m meta.cli ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto ../proto/relationalai/lqp/v1/fragments.proto --parser python
"""

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
        return s[1:-1].encode().decode('unicode_escape')  # Strip quotes and process escaping

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
        if value is None:
            return default
        else:
            _t1045 = None
        if value.HasField('int_value'):
            return value.int_value
        else:
            _t1046 = None
        return default

    @staticmethod
    def _extract_value_float64(value: Optional[logic_pb2.Value], default: float) -> float:
        if value is None:
            return default
        else:
            _t1047 = None
        if value.HasField('float_value'):
            return value.float_value
        else:
            _t1048 = None
        return default

    @staticmethod
    def _extract_value_string(value: Optional[logic_pb2.Value], default: str) -> str:
        if value is None:
            return default
        else:
            _t1049 = None
        if value.HasField('string_value'):
            return value.string_value
        else:
            _t1050 = None
        return default

    @staticmethod
    def _extract_value_boolean(value: Optional[logic_pb2.Value], default: bool) -> bool:
        if value is None:
            return default
        else:
            _t1051 = None
        if value.HasField('boolean_value'):
            return value.boolean_value
        else:
            _t1052 = None
        return default

    @staticmethod
    def _extract_value_bytes(value: Optional[logic_pb2.Value], default: bytes) -> bytes:
        if value is None:
            return default
        else:
            _t1053 = None
        if value.HasField('string_value'):
            _t1055 = value.string_value.encode()
            return _t1055
        else:
            _t1054 = None
        return default

    @staticmethod
    def _extract_value_uint128(value: Optional[logic_pb2.Value], default: logic_pb2.UInt128Value) -> logic_pb2.UInt128Value:
        if value is None:
            return default
        else:
            _t1056 = None
        if value.HasField('uint128_value'):
            return value.uint128_value
        else:
            _t1057 = None
        return default

    @staticmethod
    def _extract_value_string_list(value: Optional[logic_pb2.Value], default: list[str]) -> list[str]:
        if value is None:
            return default
        else:
            _t1058 = None
        if value.HasField('string_value'):
            return [value.string_value]
        else:
            _t1059 = None
        return default

    @staticmethod
    def construct_csv_config(config_dict: list[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1060 = Parser._extract_value_int64(config.get('csv_header_row'), 1)
        header_row = _t1060
        _t1061 = Parser._extract_value_int64(config.get('csv_skip'), 0)
        skip = _t1061
        _t1062 = Parser._extract_value_string(config.get('csv_new_line'), '')
        new_line = _t1062
        _t1063 = Parser._extract_value_string(config.get('csv_delimiter'), ',')
        delimiter = _t1063
        _t1064 = Parser._extract_value_string(config.get('csv_quotechar'), '"')
        quotechar = _t1064
        _t1065 = Parser._extract_value_string(config.get('csv_escapechar'), '"')
        escapechar = _t1065
        _t1066 = Parser._extract_value_string(config.get('csv_comment'), '')
        comment = _t1066
        _t1067 = Parser._extract_value_string_list(config.get('csv_missing_strings'), [])
        missing_strings = _t1067
        _t1068 = Parser._extract_value_string(config.get('csv_decimal_separator'), '.')
        decimal_separator = _t1068
        _t1069 = Parser._extract_value_string(config.get('csv_encoding'), 'utf-8')
        encoding = _t1069
        _t1070 = Parser._extract_value_string(config.get('csv_compression'), 'auto')
        compression = _t1070
        _t1071 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t1071

    @staticmethod
    def construct_betree_info(key_types: list[logic_pb2.Type], value_types: list[logic_pb2.Type], config_dict: list[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1072 = Parser._extract_value_float64(config.get('betree_config_epsilon'), 0.5)
        epsilon = _t1072
        _t1073 = Parser._extract_value_int64(config.get('betree_config_max_pivots'), 4)
        max_pivots = _t1073
        _t1074 = Parser._extract_value_int64(config.get('betree_config_max_deltas'), 16)
        max_deltas = _t1074
        _t1075 = Parser._extract_value_int64(config.get('betree_config_max_leaf'), 16)
        max_leaf = _t1075
        _t1076 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1076
        root_pageid_val = config.get('betree_locator_root_pageid')
        root_pageid = None
        if root_pageid_val is not None:
            _t1078 = logic_pb2.UInt128Value(low=0, high=0)
            _t1079 = Parser._extract_value_uint128(root_pageid_val, _t1078)
            root_pageid = _t1079
            _t1077 = None
        else:
            _t1077 = None
        inline_data_val = config.get('betree_locator_inline_data')
        inline_data = None
        if inline_data_val is not None:
            _t1081 = Parser._extract_value_bytes(inline_data_val, b'')
            inline_data = _t1081
            _t1080 = None
        else:
            _t1080 = None
        _t1082 = Parser._extract_value_int64(config.get('betree_locator_element_count'), 0)
        element_count = _t1082
        _t1083 = Parser._extract_value_int64(config.get('betree_locator_tree_height'), 0)
        tree_height = _t1083
        _t1084 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1084
        _t1085 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1085

    @staticmethod
    def construct_configure(config_dict: list[tuple[str, logic_pb2.Value]]) -> transactions_pb2.Configure:
        config = dict(config_dict)
        maintenance_level_val = config.get('ivm.maintenance_level')
        maintenance_level = None
        if (maintenance_level_val is not None and maintenance_level_val.HasField('string_value')):
            _t1087 = maintenance_level_val.string_value.upper()
            level_str = _t1087
            if level_str in ['OFF', 'AUTO', 'ALL']:
                maintenance_level = ('MAINTENANCE_LEVEL_' + level_str)
                _t1088 = None
            else:
                maintenance_level = level_str
                _t1088 = None
            _t1086 = _t1088
        else:
            maintenance_level = 'MAINTENANCE_LEVEL_OFF'
            _t1086 = None
        _t1089 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1089
        _t1090 = Parser._extract_value_int64(config.get('semantics_version'), 0)
        semantics_version = _t1090
        _t1091 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1091

    @staticmethod
    def export_csv_config(path: str, columns: list[transactions_pb2.ExportCSVColumn], config_dict: list[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1092 = Parser._extract_value_int64(config.get('partition_size'), 0)
        partition_size = _t1092
        _t1093 = Parser._extract_value_string(config.get('compression'), '')
        compression = _t1093
        _t1094 = Parser._extract_value_boolean(config.get('syntax_header_row'), True)
        syntax_header_row = _t1094
        _t1095 = Parser._extract_value_string(config.get('syntax_missing_string'), '')
        syntax_missing_string = _t1095
        _t1096 = Parser._extract_value_string(config.get('syntax_delim'), ',')
        syntax_delim = _t1096
        _t1097 = Parser._extract_value_string(config.get('syntax_quotechar'), '"')
        syntax_quotechar = _t1097
        _t1098 = Parser._extract_value_string(config.get('syntax_escapechar'), '\\')
        syntax_escapechar = _t1098
        _t1099 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1099

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        self.consume_literal('(')
        self.consume_literal('transaction')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('configure', 1)):
            _t356 = self.parse_configure()
            _t355 = _t356
        else:
            _t355 = None
        configure0 = _t355
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('sync', 1)):
            _t358 = self.parse_sync()
            _t357 = _t358
        else:
            _t357 = None
        sync1 = _t357
        xs2 = []
        cond3 = self.match_lookahead_literal('(', 0)
        while cond3:
            _t359 = self.parse_epoch()
            item4 = _t359
            xs2.append(item4)
            cond3 = self.match_lookahead_literal('(', 0)
        epochs5 = xs2
        self.consume_literal(')')
        _t360 = transactions_pb2.Transaction(epochs=epochs5, configure=(configure0 if configure0 is not None else self.construct_configure([])), sync=sync1)
        return _t360

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal('(')
        self.consume_literal('configure')
        _t361 = self.parse_config_dict()
        config_dict6 = _t361
        self.consume_literal(')')
        return self.construct_configure(config_dict6)

    def parse_config_dict(self) -> list[tuple[str, logic_pb2.Value]]:
        self.consume_literal('{')
        xs7 = []
        cond8 = self.match_lookahead_literal(':', 0)
        while cond8:
            _t362 = self.parse_config_key_value()
            item9 = _t362
            xs7.append(item9)
            cond8 = self.match_lookahead_literal(':', 0)
        config_key_values10 = xs7
        self.consume_literal('}')
        return config_key_values10

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(':')
        symbol11 = self.consume_terminal('SYMBOL')
        _t363 = self.parse_value()
        value12 = _t363
        return (symbol11, value12,)

    def parse_value(self) -> logic_pb2.Value:
        if self.match_lookahead_literal('true', 0):
            _t364 = 9
        else:
            if self.match_lookahead_literal('missing', 0):
                _t365 = 8
            else:
                if self.match_lookahead_literal('false', 0):
                    _t366 = 9
                else:
                    if self.match_lookahead_literal('(', 0):
                        if self.match_lookahead_literal('datetime', 1):
                            _t369 = 1
                        else:
                            if self.match_lookahead_literal('date', 1):
                                _t370 = 0
                            else:
                                _t370 = -1
                            _t369 = _t370
                        _t367 = _t369
                    else:
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t371 = 5
                        else:
                            if self.match_lookahead_terminal('STRING', 0):
                                _t372 = 2
                            else:
                                if self.match_lookahead_terminal('INT128', 0):
                                    _t373 = 6
                                else:
                                    if self.match_lookahead_terminal('INT', 0):
                                        _t374 = 3
                                    else:
                                        if self.match_lookahead_terminal('FLOAT', 0):
                                            _t375 = 4
                                        else:
                                            if self.match_lookahead_terminal('DECIMAL', 0):
                                                _t376 = 7
                                            else:
                                                _t376 = -1
                                            _t375 = _t376
                                        _t374 = _t375
                                    _t373 = _t374
                                _t372 = _t373
                            _t371 = _t372
                        _t367 = _t371
                    _t366 = _t367
                _t365 = _t366
            _t364 = _t365
        prediction13 = _t364
        if prediction13 == 9:
            _t378 = self.parse_boolean_value()
            boolean_value22 = _t378
            _t379 = logic_pb2.Value(boolean_value=boolean_value22)
            _t377 = _t379
        else:
            if prediction13 == 8:
                self.consume_literal('missing')
                _t381 = logic_pb2.Value(missing_value=logic_pb2.MissingValue())
                _t380 = _t381
            else:
                if prediction13 == 7:
                    decimal21 = self.consume_terminal('DECIMAL')
                    _t383 = logic_pb2.Value(decimal_value=decimal21)
                    _t382 = _t383
                else:
                    if prediction13 == 6:
                        int12820 = self.consume_terminal('INT128')
                        _t385 = logic_pb2.Value(int128_value=int12820)
                        _t384 = _t385
                    else:
                        if prediction13 == 5:
                            uint12819 = self.consume_terminal('UINT128')
                            _t387 = logic_pb2.Value(uint128_value=uint12819)
                            _t386 = _t387
                        else:
                            if prediction13 == 4:
                                float18 = self.consume_terminal('FLOAT')
                                _t389 = logic_pb2.Value(float_value=float18)
                                _t388 = _t389
                            else:
                                if prediction13 == 3:
                                    int17 = self.consume_terminal('INT')
                                    _t391 = logic_pb2.Value(int_value=int17)
                                    _t390 = _t391
                                else:
                                    if prediction13 == 2:
                                        string16 = self.consume_terminal('STRING')
                                        _t393 = logic_pb2.Value(string_value=string16)
                                        _t392 = _t393
                                    else:
                                        if prediction13 == 1:
                                            _t395 = self.parse_datetime()
                                            datetime15 = _t395
                                            _t396 = logic_pb2.Value(datetime_value=datetime15)
                                            _t394 = _t396
                                        else:
                                            if prediction13 == 0:
                                                _t398 = self.parse_date()
                                                date14 = _t398
                                                _t399 = logic_pb2.Value(date_value=date14)
                                                _t397 = _t399
                                            else:
                                                raise ParseError(f"{'Unexpected token in value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t397 = None
                                            _t394 = _t397
                                        _t392 = _t394
                                    _t390 = _t392
                                _t388 = _t390
                            _t386 = _t388
                        _t384 = _t386
                    _t382 = _t384
                _t380 = _t382
            _t377 = _t380
        return _t377

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal('(')
        self.consume_literal('date')
        int23 = self.consume_terminal('INT')
        int_324 = self.consume_terminal('INT')
        int_425 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t400 = logic_pb2.DateValue(year=int(int23), month=int(int_324), day=int(int_425))
        return _t400

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
            _t401 = self.consume_terminal('INT')
        else:
            _t401 = None
        int_832 = _t401
        self.consume_literal(')')
        _t402 = logic_pb2.DateTimeValue(year=int(int26), month=int(int_327), day=int(int_428), hour=int(int_529), minute=int(int_630), second=int(int_731), microsecond=int((int_832 if int_832 is not None else 0)))
        return _t402

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal('true', 0):
            _t403 = 0
        else:
            _t403 = (self.match_lookahead_literal('false', 0) or -1)
        prediction33 = _t403
        if prediction33 == 1:
            self.consume_literal('false')
            _t404 = False
        else:
            if prediction33 == 0:
                self.consume_literal('true')
                _t405 = True
            else:
                raise ParseError(f"{'Unexpected token in boolean_value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t405 = None
            _t404 = _t405
        return _t404

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal('(')
        self.consume_literal('sync')
        xs34 = []
        cond35 = self.match_lookahead_literal(':', 0)
        while cond35:
            _t406 = self.parse_fragment_id()
            item36 = _t406
            xs34.append(item36)
            cond35 = self.match_lookahead_literal(':', 0)
        fragment_ids37 = xs34
        self.consume_literal(')')
        _t407 = transactions_pb2.Sync(fragments=fragment_ids37)
        return _t407

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        self.consume_literal(':')
        symbol38 = self.consume_terminal('SYMBOL')
        return fragments_pb2.FragmentId(id=symbol38.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal('(')
        self.consume_literal('epoch')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('writes', 1)):
            _t409 = self.parse_epoch_writes()
            _t408 = _t409
        else:
            _t408 = None
        epoch_writes39 = _t408
        if self.match_lookahead_literal('(', 0):
            _t411 = self.parse_epoch_reads()
            _t410 = _t411
        else:
            _t410 = None
        epoch_reads40 = _t410
        self.consume_literal(')')
        _t412 = transactions_pb2.Epoch(writes=(epoch_writes39 if epoch_writes39 is not None else []), reads=(epoch_reads40 if epoch_reads40 is not None else []))
        return _t412

    def parse_epoch_writes(self) -> list[transactions_pb2.Write]:
        self.consume_literal('(')
        self.consume_literal('writes')
        xs41 = []
        cond42 = self.match_lookahead_literal('(', 0)
        while cond42:
            _t413 = self.parse_write()
            item43 = _t413
            xs41.append(item43)
            cond42 = self.match_lookahead_literal('(', 0)
        writes44 = xs41
        self.consume_literal(')')
        return writes44

    def parse_write(self) -> transactions_pb2.Write:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('undefine', 1):
                _t417 = 1
            else:
                if self.match_lookahead_literal('define', 1):
                    _t418 = 0
                else:
                    if self.match_lookahead_literal('context', 1):
                        _t419 = 2
                    else:
                        _t419 = -1
                    _t418 = _t419
                _t417 = _t418
            _t414 = _t417
        else:
            _t414 = -1
        prediction45 = _t414
        if prediction45 == 2:
            _t421 = self.parse_context()
            context48 = _t421
            _t422 = transactions_pb2.Write(context=context48)
            _t420 = _t422
        else:
            if prediction45 == 1:
                _t424 = self.parse_undefine()
                undefine47 = _t424
                _t425 = transactions_pb2.Write(undefine=undefine47)
                _t423 = _t425
            else:
                if prediction45 == 0:
                    _t427 = self.parse_define()
                    define46 = _t427
                    _t428 = transactions_pb2.Write(define=define46)
                    _t426 = _t428
                else:
                    raise ParseError(f"{'Unexpected token in write'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t426 = None
                _t423 = _t426
            _t420 = _t423
        return _t420

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal('(')
        self.consume_literal('define')
        _t429 = self.parse_fragment()
        fragment49 = _t429
        self.consume_literal(')')
        _t430 = transactions_pb2.Define(fragment=fragment49)
        return _t430

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal('(')
        self.consume_literal('fragment')
        _t431 = self.parse_new_fragment_id()
        new_fragment_id50 = _t431
        xs51 = []
        cond52 = self.match_lookahead_literal('(', 0)
        while cond52:
            _t432 = self.parse_declaration()
            item53 = _t432
            xs51.append(item53)
            cond52 = self.match_lookahead_literal('(', 0)
        declarations54 = xs51
        self.consume_literal(')')
        return self.construct_fragment(new_fragment_id50, declarations54)

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        _t433 = self.parse_fragment_id()
        fragment_id55 = _t433
        self.start_fragment(fragment_id55)
        return fragment_id55

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('rel_edb', 1):
                _t435 = 3
            else:
                if self.match_lookahead_literal('functional_dependency', 1):
                    _t436 = 2
                else:
                    if self.match_lookahead_literal('def', 1):
                        _t437 = 0
                    else:
                        if self.match_lookahead_literal('csv_data', 1):
                            _t438 = 3
                        else:
                            if self.match_lookahead_literal('betree_relation', 1):
                                _t439 = 3
                            else:
                                _t439 = (self.match_lookahead_literal('algorithm', 1) or -1)
                            _t438 = _t439
                        _t437 = _t438
                    _t436 = _t437
                _t435 = _t436
            _t434 = _t435
        else:
            _t434 = -1
        prediction56 = _t434
        if prediction56 == 3:
            _t441 = self.parse_data()
            data60 = _t441
            _t442 = logic_pb2.Declaration(data=data60)
            _t440 = _t442
        else:
            if prediction56 == 2:
                _t444 = self.parse_constraint()
                constraint59 = _t444
                _t445 = logic_pb2.Declaration(constraint=constraint59)
                _t443 = _t445
            else:
                if prediction56 == 1:
                    _t447 = self.parse_algorithm()
                    algorithm58 = _t447
                    _t448 = logic_pb2.Declaration(algorithm=algorithm58)
                    _t446 = _t448
                else:
                    if prediction56 == 0:
                        _t450 = self.parse_def()
                        def57 = _t450
                        _t451 = logic_pb2.Declaration()
                        getattr(_t451, 'def').CopyFrom(def57)
                        _t449 = _t451
                    else:
                        raise ParseError(f"{'Unexpected token in declaration'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t449 = None
                    _t446 = _t449
                _t443 = _t446
            _t440 = _t443
        return _t440

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal('(')
        self.consume_literal('def')
        _t452 = self.parse_relation_id()
        relation_id61 = _t452
        _t453 = self.parse_abstraction()
        abstraction62 = _t453
        if self.match_lookahead_literal('(', 0):
            _t455 = self.parse_attrs()
            _t454 = _t455
        else:
            _t454 = None
        attrs63 = _t454
        self.consume_literal(')')
        _t456 = logic_pb2.Def(name=relation_id61, body=abstraction62, attrs=(attrs63 if attrs63 is not None else []))
        return _t456

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_literal(':', 0):
            _t457 = 0
        else:
            _t457 = (self.match_lookahead_terminal('INT', 0) or -1)
        prediction64 = _t457
        if prediction64 == 1:
            int66 = self.consume_terminal('INT')
            _t458 = logic_pb2.RelationId(id_low=int66 & 0xFFFFFFFFFFFFFFFF, id_high=(int66 >> 64) & 0xFFFFFFFFFFFFFFFF)
        else:
            if prediction64 == 0:
                self.consume_literal(':')
                symbol65 = self.consume_terminal('SYMBOL')
                _t459 = self.relation_id_from_string(symbol65)
            else:
                raise ParseError(f"{'Unexpected token in relation_id'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t459 = None
            _t458 = _t459
        return _t458

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal('(')
        _t460 = self.parse_bindings()
        bindings67 = _t460
        _t461 = self.parse_formula()
        formula68 = _t461
        self.consume_literal(')')
        _t462 = logic_pb2.Abstraction(vars=(bindings67[0] + (bindings67[1] if bindings67[1] is not None else [])), value=formula68)
        return _t462

    def parse_bindings(self) -> tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]:
        self.consume_literal('[')
        xs69 = []
        cond70 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond70:
            _t463 = self.parse_binding()
            item71 = _t463
            xs69.append(item71)
            cond70 = self.match_lookahead_terminal('SYMBOL', 0)
        bindings72 = xs69
        if self.match_lookahead_literal('|', 0):
            _t465 = self.parse_value_bindings()
            _t464 = _t465
        else:
            _t464 = None
        value_bindings73 = _t464
        self.consume_literal(']')
        return (bindings72, (value_bindings73 if value_bindings73 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol74 = self.consume_terminal('SYMBOL')
        self.consume_literal('::')
        _t466 = self.parse_type()
        type75 = _t466
        _t467 = logic_pb2.Var(name=symbol74)
        _t468 = logic_pb2.Binding(var=_t467, type=type75)
        return _t468

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal('UNKNOWN', 0):
            _t469 = 0
        else:
            if self.match_lookahead_literal('UINT128', 0):
                _t470 = 4
            else:
                if self.match_lookahead_literal('STRING', 0):
                    _t479 = 1
                else:
                    if self.match_lookahead_literal('MISSING', 0):
                        _t480 = 8
                    else:
                        if self.match_lookahead_literal('INT128', 0):
                            _t481 = 5
                        else:
                            if self.match_lookahead_literal('INT', 0):
                                _t482 = 2
                            else:
                                if self.match_lookahead_literal('FLOAT', 0):
                                    _t483 = 3
                                else:
                                    if self.match_lookahead_literal('DATETIME', 0):
                                        _t484 = 7
                                    else:
                                        if self.match_lookahead_literal('DATE', 0):
                                            _t485 = 6
                                        else:
                                            if self.match_lookahead_literal('BOOLEAN', 0):
                                                _t486 = 10
                                            else:
                                                if self.match_lookahead_literal('(', 0):
                                                    _t487 = 9
                                                else:
                                                    _t487 = -1
                                                _t486 = _t487
                                            _t485 = _t486
                                        _t484 = _t485
                                    _t483 = _t484
                                _t482 = _t483
                            _t481 = _t482
                        _t480 = _t481
                    _t479 = _t480
                _t470 = _t479
            _t469 = _t470
        prediction76 = _t469
        if prediction76 == 10:
            _t489 = self.parse_boolean_type()
            boolean_type87 = _t489
            _t490 = logic_pb2.Type(boolean_type=boolean_type87)
            _t488 = _t490
        else:
            if prediction76 == 9:
                _t492 = self.parse_decimal_type()
                decimal_type86 = _t492
                _t493 = logic_pb2.Type(decimal_type=decimal_type86)
                _t491 = _t493
            else:
                if prediction76 == 8:
                    _t495 = self.parse_missing_type()
                    missing_type85 = _t495
                    _t496 = logic_pb2.Type(missing_type=missing_type85)
                    _t494 = _t496
                else:
                    if prediction76 == 7:
                        _t498 = self.parse_datetime_type()
                        datetime_type84 = _t498
                        _t499 = logic_pb2.Type(datetime_type=datetime_type84)
                        _t497 = _t499
                    else:
                        if prediction76 == 6:
                            _t501 = self.parse_date_type()
                            date_type83 = _t501
                            _t502 = logic_pb2.Type(date_type=date_type83)
                            _t500 = _t502
                        else:
                            if prediction76 == 5:
                                _t504 = self.parse_int128_type()
                                int128_type82 = _t504
                                _t505 = logic_pb2.Type(int128_type=int128_type82)
                                _t503 = _t505
                            else:
                                if prediction76 == 4:
                                    _t507 = self.parse_uint128_type()
                                    uint128_type81 = _t507
                                    _t508 = logic_pb2.Type(uint128_type=uint128_type81)
                                    _t506 = _t508
                                else:
                                    if prediction76 == 3:
                                        _t510 = self.parse_float_type()
                                        float_type80 = _t510
                                        _t511 = logic_pb2.Type(float_type=float_type80)
                                        _t509 = _t511
                                    else:
                                        if prediction76 == 2:
                                            _t513 = self.parse_int_type()
                                            int_type79 = _t513
                                            _t514 = logic_pb2.Type(int_type=int_type79)
                                            _t512 = _t514
                                        else:
                                            if prediction76 == 1:
                                                _t516 = self.parse_string_type()
                                                string_type78 = _t516
                                                _t517 = logic_pb2.Type(string_type=string_type78)
                                                _t515 = _t517
                                            else:
                                                if prediction76 == 0:
                                                    _t519 = self.parse_unspecified_type()
                                                    unspecified_type77 = _t519
                                                    _t520 = logic_pb2.Type(unspecified_type=unspecified_type77)
                                                    _t518 = _t520
                                                else:
                                                    raise ParseError(f"{'Unexpected token in type'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                    _t518 = None
                                                _t515 = _t518
                                            _t512 = _t515
                                        _t509 = _t512
                                    _t506 = _t509
                                _t503 = _t506
                            _t500 = _t503
                        _t497 = _t500
                    _t494 = _t497
                _t491 = _t494
            _t488 = _t491
        return _t488

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
        _t521 = logic_pb2.DecimalType(precision=int(int88), scale=int(int_389))
        return _t521

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal('BOOLEAN')
        return logic_pb2.BooleanType()

    def parse_value_bindings(self) -> list[logic_pb2.Binding]:
        self.consume_literal('|')
        xs90 = []
        cond91 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond91:
            _t522 = self.parse_binding()
            item92 = _t522
            xs90.append(item92)
            cond91 = self.match_lookahead_terminal('SYMBOL', 0)
        bindings93 = xs90
        return bindings93

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('true', 1):
                _t524 = 0
            else:
                if self.match_lookahead_literal('relatom', 1):
                    _t525 = 11
                else:
                    if self.match_lookahead_literal('reduce', 1):
                        _t526 = 3
                    else:
                        if self.match_lookahead_literal('primitive', 1):
                            _t527 = 10
                        else:
                            if self.match_lookahead_literal('pragma', 1):
                                _t528 = 9
                            else:
                                if self.match_lookahead_literal('or', 1):
                                    _t529 = 5
                                else:
                                    if self.match_lookahead_literal('not', 1):
                                        _t530 = 6
                                    else:
                                        if self.match_lookahead_literal('ffi', 1):
                                            _t531 = 7
                                        else:
                                            if self.match_lookahead_literal('false', 1):
                                                _t545 = 1
                                            else:
                                                if self.match_lookahead_literal('exists', 1):
                                                    _t546 = 2
                                                else:
                                                    if self.match_lookahead_literal('cast', 1):
                                                        _t547 = 12
                                                    else:
                                                        if self.match_lookahead_literal('atom', 1):
                                                            _t548 = 8
                                                        else:
                                                            if self.match_lookahead_literal('and', 1):
                                                                _t549 = 4
                                                            else:
                                                                if self.match_lookahead_literal('>=', 1):
                                                                    _t550 = 10
                                                                else:
                                                                    if self.match_lookahead_literal('>', 1):
                                                                        _t551 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal('=', 1):
                                                                            _t552 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal('<=', 1):
                                                                                _t553 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal('<', 1):
                                                                                    _t554 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal('/', 1):
                                                                                        _t555 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal('-', 1):
                                                                                            _t556 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal('+', 1):
                                                                                                _t557 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal('*', 1):
                                                                                                    _t558 = 10
                                                                                                else:
                                                                                                    _t558 = -1
                                                                                                _t557 = _t558
                                                                                            _t556 = _t557
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
                                            _t531 = _t545
                                        _t530 = _t531
                                    _t529 = _t530
                                _t528 = _t529
                            _t527 = _t528
                        _t526 = _t527
                    _t525 = _t526
                _t524 = _t525
            _t523 = _t524
        else:
            _t523 = -1
        prediction94 = _t523
        if prediction94 == 12:
            _t560 = self.parse_cast()
            cast107 = _t560
            _t561 = logic_pb2.Formula(cast=cast107)
            _t559 = _t561
        else:
            if prediction94 == 11:
                _t563 = self.parse_rel_atom()
                rel_atom106 = _t563
                _t564 = logic_pb2.Formula(rel_atom=rel_atom106)
                _t562 = _t564
            else:
                if prediction94 == 10:
                    _t566 = self.parse_primitive()
                    primitive105 = _t566
                    _t567 = logic_pb2.Formula(primitive=primitive105)
                    _t565 = _t567
                else:
                    if prediction94 == 9:
                        _t569 = self.parse_pragma()
                        pragma104 = _t569
                        _t570 = logic_pb2.Formula(pragma=pragma104)
                        _t568 = _t570
                    else:
                        if prediction94 == 8:
                            _t572 = self.parse_atom()
                            atom103 = _t572
                            _t573 = logic_pb2.Formula(atom=atom103)
                            _t571 = _t573
                        else:
                            if prediction94 == 7:
                                _t575 = self.parse_ffi()
                                ffi102 = _t575
                                _t576 = logic_pb2.Formula(ffi=ffi102)
                                _t574 = _t576
                            else:
                                if prediction94 == 6:
                                    _t578 = self.parse_not()
                                    not101 = _t578
                                    _t579 = logic_pb2.Formula()
                                    getattr(_t579, 'not').CopyFrom(not101)
                                    _t577 = _t579
                                else:
                                    if prediction94 == 5:
                                        _t581 = self.parse_disjunction()
                                        disjunction100 = _t581
                                        _t582 = logic_pb2.Formula(disjunction=disjunction100)
                                        _t580 = _t582
                                    else:
                                        if prediction94 == 4:
                                            _t584 = self.parse_conjunction()
                                            conjunction99 = _t584
                                            _t585 = logic_pb2.Formula(conjunction=conjunction99)
                                            _t583 = _t585
                                        else:
                                            if prediction94 == 3:
                                                _t587 = self.parse_reduce()
                                                reduce98 = _t587
                                                _t588 = logic_pb2.Formula(reduce=reduce98)
                                                _t586 = _t588
                                            else:
                                                if prediction94 == 2:
                                                    _t590 = self.parse_exists()
                                                    exists97 = _t590
                                                    _t591 = logic_pb2.Formula(exists=exists97)
                                                    _t589 = _t591
                                                else:
                                                    if prediction94 == 1:
                                                        _t593 = self.parse_false()
                                                        false96 = _t593
                                                        _t594 = logic_pb2.Formula(disjunction=false96)
                                                        _t592 = _t594
                                                    else:
                                                        if prediction94 == 0:
                                                            _t596 = self.parse_true()
                                                            true95 = _t596
                                                            _t597 = logic_pb2.Formula(conjunction=true95)
                                                            _t595 = _t597
                                                        else:
                                                            raise ParseError(f"{'Unexpected token in formula'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t595 = None
                                                        _t592 = _t595
                                                    _t589 = _t592
                                                _t586 = _t589
                                            _t583 = _t586
                                        _t580 = _t583
                                    _t577 = _t580
                                _t574 = _t577
                            _t571 = _t574
                        _t568 = _t571
                    _t565 = _t568
                _t562 = _t565
            _t559 = _t562
        return _t559

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('true')
        self.consume_literal(')')
        _t598 = logic_pb2.Conjunction(args=[])
        return _t598

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('false')
        self.consume_literal(')')
        _t599 = logic_pb2.Disjunction(args=[])
        return _t599

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal('(')
        self.consume_literal('exists')
        _t600 = self.parse_bindings()
        bindings108 = _t600
        _t601 = self.parse_formula()
        formula109 = _t601
        self.consume_literal(')')
        _t602 = logic_pb2.Abstraction(vars=(bindings108[0] + (bindings108[1] if bindings108[1] is not None else [])), value=formula109)
        _t603 = logic_pb2.Exists(body=_t602)
        return _t603

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal('(')
        self.consume_literal('reduce')
        _t604 = self.parse_abstraction()
        abstraction110 = _t604
        _t605 = self.parse_abstraction()
        abstraction_3111 = _t605
        _t606 = self.parse_terms()
        terms112 = _t606
        self.consume_literal(')')
        _t607 = logic_pb2.Reduce(op=abstraction110, body=abstraction_3111, terms=terms112)
        return _t607

    def parse_terms(self) -> list[logic_pb2.Term]:
        self.consume_literal('(')
        self.consume_literal('terms')
        xs113 = []
        cond114 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond114:
            _t608 = self.parse_term()
            item115 = _t608
            xs113.append(item115)
            cond114 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms116 = xs113
        self.consume_literal(')')
        return terms116

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_literal('true', 0):
            _t640 = 1
        else:
            if self.match_lookahead_literal('missing', 0):
                _t656 = 1
            else:
                if self.match_lookahead_literal('false', 0):
                    _t664 = 1
                else:
                    if self.match_lookahead_literal('(', 0):
                        _t668 = 1
                    else:
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t670 = 1
                        else:
                            if self.match_lookahead_terminal('SYMBOL', 0):
                                _t671 = 0
                            else:
                                _t671 = (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or -1)))))
                            _t670 = _t671
                        _t668 = _t670
                    _t664 = _t668
                _t656 = _t664
            _t640 = _t656
        prediction117 = _t640
        if prediction117 == 1:
            _t673 = self.parse_constant()
            constant119 = _t673
            _t674 = logic_pb2.Term(constant=constant119)
            _t672 = _t674
        else:
            if prediction117 == 0:
                _t676 = self.parse_var()
                var118 = _t676
                _t677 = logic_pb2.Term(var=var118)
                _t675 = _t677
            else:
                raise ParseError(f"{'Unexpected token in term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t675 = None
            _t672 = _t675
        return _t672

    def parse_var(self) -> logic_pb2.Var:
        symbol120 = self.consume_terminal('SYMBOL')
        _t678 = logic_pb2.Var(name=symbol120)
        return _t678

    def parse_constant(self) -> logic_pb2.Value:
        _t679 = self.parse_value()
        value121 = _t679
        return value121

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('and')
        xs122 = []
        cond123 = self.match_lookahead_literal('(', 0)
        while cond123:
            _t680 = self.parse_formula()
            item124 = _t680
            xs122.append(item124)
            cond123 = self.match_lookahead_literal('(', 0)
        formulas125 = xs122
        self.consume_literal(')')
        _t681 = logic_pb2.Conjunction(args=formulas125)
        return _t681

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('or')
        xs126 = []
        cond127 = self.match_lookahead_literal('(', 0)
        while cond127:
            _t682 = self.parse_formula()
            item128 = _t682
            xs126.append(item128)
            cond127 = self.match_lookahead_literal('(', 0)
        formulas129 = xs126
        self.consume_literal(')')
        _t683 = logic_pb2.Disjunction(args=formulas129)
        return _t683

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal('(')
        self.consume_literal('not')
        _t684 = self.parse_formula()
        formula130 = _t684
        self.consume_literal(')')
        _t685 = logic_pb2.Not(arg=formula130)
        return _t685

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal('(')
        self.consume_literal('ffi')
        _t686 = self.parse_name()
        name131 = _t686
        _t687 = self.parse_ffi_args()
        ffi_args132 = _t687
        _t688 = self.parse_terms()
        terms133 = _t688
        self.consume_literal(')')
        _t689 = logic_pb2.FFI(name=name131, args=ffi_args132, terms=terms133)
        return _t689

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
            _t690 = self.parse_abstraction()
            item137 = _t690
            xs135.append(item137)
            cond136 = self.match_lookahead_literal('(', 0)
        abstractions138 = xs135
        self.consume_literal(')')
        return abstractions138

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal('(')
        self.consume_literal('atom')
        _t691 = self.parse_relation_id()
        relation_id139 = _t691
        xs140 = []
        cond141 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond141:
            _t692 = self.parse_term()
            item142 = _t692
            xs140.append(item142)
            cond141 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms143 = xs140
        self.consume_literal(')')
        _t693 = logic_pb2.Atom(name=relation_id139, terms=terms143)
        return _t693

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal('(')
        self.consume_literal('pragma')
        _t694 = self.parse_name()
        name144 = _t694
        xs145 = []
        cond146 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond146:
            _t695 = self.parse_term()
            item147 = _t695
            xs145.append(item147)
            cond146 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms148 = xs145
        self.consume_literal(')')
        _t696 = logic_pb2.Pragma(name=name144, terms=terms148)
        return _t696

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('primitive', 1):
                _t698 = 9
            else:
                if self.match_lookahead_literal('>=', 1):
                    _t699 = 4
                else:
                    if self.match_lookahead_literal('>', 1):
                        _t700 = 3
                    else:
                        if self.match_lookahead_literal('=', 1):
                            _t701 = 0
                        else:
                            if self.match_lookahead_literal('<=', 1):
                                _t702 = 2
                            else:
                                if self.match_lookahead_literal('<', 1):
                                    _t707 = 1
                                else:
                                    if self.match_lookahead_literal('/', 1):
                                        _t708 = 8
                                    else:
                                        if self.match_lookahead_literal('-', 1):
                                            _t709 = 6
                                        else:
                                            if self.match_lookahead_literal('+', 1):
                                                _t710 = 5
                                            else:
                                                if self.match_lookahead_literal('*', 1):
                                                    _t711 = 7
                                                else:
                                                    _t711 = -1
                                                _t710 = _t711
                                            _t709 = _t710
                                        _t708 = _t709
                                    _t707 = _t708
                                _t702 = _t707
                            _t701 = _t702
                        _t700 = _t701
                    _t699 = _t700
                _t698 = _t699
            _t697 = _t698
        else:
            _t697 = -1
        prediction149 = _t697
        if prediction149 == 9:
            self.consume_literal('(')
            self.consume_literal('primitive')
            _t713 = self.parse_name()
            name159 = _t713
            xs160 = []
            cond161 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            while cond161:
                _t714 = self.parse_rel_term()
                item162 = _t714
                xs160.append(item162)
                cond161 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            rel_terms163 = xs160
            self.consume_literal(')')
            _t715 = logic_pb2.Primitive(name=name159, terms=rel_terms163)
            _t712 = _t715
        else:
            if prediction149 == 8:
                _t717 = self.parse_divide()
                divide158 = _t717
                _t716 = divide158
            else:
                if prediction149 == 7:
                    _t719 = self.parse_multiply()
                    multiply157 = _t719
                    _t718 = multiply157
                else:
                    if prediction149 == 6:
                        _t721 = self.parse_minus()
                        minus156 = _t721
                        _t720 = minus156
                    else:
                        if prediction149 == 5:
                            _t723 = self.parse_add()
                            add155 = _t723
                            _t722 = add155
                        else:
                            if prediction149 == 4:
                                _t725 = self.parse_gt_eq()
                                gt_eq154 = _t725
                                _t724 = gt_eq154
                            else:
                                if prediction149 == 3:
                                    _t727 = self.parse_gt()
                                    gt153 = _t727
                                    _t726 = gt153
                                else:
                                    if prediction149 == 2:
                                        _t729 = self.parse_lt_eq()
                                        lt_eq152 = _t729
                                        _t728 = lt_eq152
                                    else:
                                        if prediction149 == 1:
                                            _t731 = self.parse_lt()
                                            lt151 = _t731
                                            _t730 = lt151
                                        else:
                                            if prediction149 == 0:
                                                _t733 = self.parse_eq()
                                                eq150 = _t733
                                                _t732 = eq150
                                            else:
                                                raise ParseError(f"{'Unexpected token in primitive'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t732 = None
                                            _t730 = _t732
                                        _t728 = _t730
                                    _t726 = _t728
                                _t724 = _t726
                            _t722 = _t724
                        _t720 = _t722
                    _t718 = _t720
                _t716 = _t718
            _t712 = _t716
        return _t712

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('=')
        _t734 = self.parse_term()
        term164 = _t734
        _t735 = self.parse_term()
        term_3165 = _t735
        self.consume_literal(')')
        _t736 = logic_pb2.RelTerm(term=term164)
        _t737 = logic_pb2.RelTerm(term=term_3165)
        _t738 = logic_pb2.Primitive(name='rel_primitive_eq', terms=[_t736, _t737])
        return _t738

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<')
        _t739 = self.parse_term()
        term166 = _t739
        _t740 = self.parse_term()
        term_3167 = _t740
        self.consume_literal(')')
        _t741 = logic_pb2.RelTerm(term=term166)
        _t742 = logic_pb2.RelTerm(term=term_3167)
        _t743 = logic_pb2.Primitive(name='rel_primitive_lt_monotype', terms=[_t741, _t742])
        return _t743

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<=')
        _t744 = self.parse_term()
        term168 = _t744
        _t745 = self.parse_term()
        term_3169 = _t745
        self.consume_literal(')')
        _t746 = logic_pb2.RelTerm(term=term168)
        _t747 = logic_pb2.RelTerm(term=term_3169)
        _t748 = logic_pb2.Primitive(name='rel_primitive_lt_eq_monotype', terms=[_t746, _t747])
        return _t748

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>')
        _t749 = self.parse_term()
        term170 = _t749
        _t750 = self.parse_term()
        term_3171 = _t750
        self.consume_literal(')')
        _t751 = logic_pb2.RelTerm(term=term170)
        _t752 = logic_pb2.RelTerm(term=term_3171)
        _t753 = logic_pb2.Primitive(name='rel_primitive_gt_monotype', terms=[_t751, _t752])
        return _t753

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>=')
        _t754 = self.parse_term()
        term172 = _t754
        _t755 = self.parse_term()
        term_3173 = _t755
        self.consume_literal(')')
        _t756 = logic_pb2.RelTerm(term=term172)
        _t757 = logic_pb2.RelTerm(term=term_3173)
        _t758 = logic_pb2.Primitive(name='rel_primitive_gt_eq_monotype', terms=[_t756, _t757])
        return _t758

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('+')
        _t759 = self.parse_term()
        term174 = _t759
        _t760 = self.parse_term()
        term_3175 = _t760
        _t761 = self.parse_term()
        term_4176 = _t761
        self.consume_literal(')')
        _t762 = logic_pb2.RelTerm(term=term174)
        _t763 = logic_pb2.RelTerm(term=term_3175)
        _t764 = logic_pb2.RelTerm(term=term_4176)
        _t765 = logic_pb2.Primitive(name='rel_primitive_add_monotype', terms=[_t762, _t763, _t764])
        return _t765

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('-')
        _t766 = self.parse_term()
        term177 = _t766
        _t767 = self.parse_term()
        term_3178 = _t767
        _t768 = self.parse_term()
        term_4179 = _t768
        self.consume_literal(')')
        _t769 = logic_pb2.RelTerm(term=term177)
        _t770 = logic_pb2.RelTerm(term=term_3178)
        _t771 = logic_pb2.RelTerm(term=term_4179)
        _t772 = logic_pb2.Primitive(name='rel_primitive_subtract_monotype', terms=[_t769, _t770, _t771])
        return _t772

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('*')
        _t773 = self.parse_term()
        term180 = _t773
        _t774 = self.parse_term()
        term_3181 = _t774
        _t775 = self.parse_term()
        term_4182 = _t775
        self.consume_literal(')')
        _t776 = logic_pb2.RelTerm(term=term180)
        _t777 = logic_pb2.RelTerm(term=term_3181)
        _t778 = logic_pb2.RelTerm(term=term_4182)
        _t779 = logic_pb2.Primitive(name='rel_primitive_multiply_monotype', terms=[_t776, _t777, _t778])
        return _t779

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('/')
        _t780 = self.parse_term()
        term183 = _t780
        _t781 = self.parse_term()
        term_3184 = _t781
        _t782 = self.parse_term()
        term_4185 = _t782
        self.consume_literal(')')
        _t783 = logic_pb2.RelTerm(term=term183)
        _t784 = logic_pb2.RelTerm(term=term_3184)
        _t785 = logic_pb2.RelTerm(term=term_4185)
        _t786 = logic_pb2.Primitive(name='rel_primitive_divide_monotype', terms=[_t783, _t784, _t785])
        return _t786

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_literal('true', 0):
            _t802 = 1
        else:
            if self.match_lookahead_literal('missing', 0):
                _t810 = 1
            else:
                if self.match_lookahead_literal('false', 0):
                    _t814 = 1
                else:
                    if self.match_lookahead_literal('(', 0):
                        _t816 = 1
                    else:
                        if self.match_lookahead_literal('#', 0):
                            _t817 = 0
                        else:
                            _t817 = (self.match_lookahead_terminal('UINT128', 0) or (self.match_lookahead_terminal('SYMBOL', 0) or (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or -1)))))))
                        _t816 = _t817
                    _t814 = _t816
                _t810 = _t814
            _t802 = _t810
        prediction186 = _t802
        if prediction186 == 1:
            _t819 = self.parse_term()
            term188 = _t819
            _t820 = logic_pb2.RelTerm(term=term188)
            _t818 = _t820
        else:
            if prediction186 == 0:
                _t822 = self.parse_specialized_value()
                specialized_value187 = _t822
                _t823 = logic_pb2.RelTerm(specialized_value=specialized_value187)
                _t821 = _t823
            else:
                raise ParseError(f"{'Unexpected token in rel_term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t821 = None
            _t818 = _t821
        return _t818

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal('#')
        _t824 = self.parse_value()
        value189 = _t824
        return value189

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        self.consume_literal('(')
        self.consume_literal('relatom')
        _t825 = self.parse_name()
        name190 = _t825
        xs191 = []
        cond192 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond192:
            _t826 = self.parse_rel_term()
            item193 = _t826
            xs191.append(item193)
            cond192 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        rel_terms194 = xs191
        self.consume_literal(')')
        _t827 = logic_pb2.RelAtom(name=name190, terms=rel_terms194)
        return _t827

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal('(')
        self.consume_literal('cast')
        _t828 = self.parse_term()
        term195 = _t828
        _t829 = self.parse_term()
        term_3196 = _t829
        self.consume_literal(')')
        _t830 = logic_pb2.Cast(input=term195, result=term_3196)
        return _t830

    def parse_attrs(self) -> list[logic_pb2.Attribute]:
        self.consume_literal('(')
        self.consume_literal('attrs')
        xs197 = []
        cond198 = self.match_lookahead_literal('(', 0)
        while cond198:
            _t831 = self.parse_attribute()
            item199 = _t831
            xs197.append(item199)
            cond198 = self.match_lookahead_literal('(', 0)
        attributes200 = xs197
        self.consume_literal(')')
        return attributes200

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal('(')
        self.consume_literal('attribute')
        _t832 = self.parse_name()
        name201 = _t832
        xs202 = []
        cond203 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond203:
            _t833 = self.parse_value()
            item204 = _t833
            xs202.append(item204)
            cond203 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        values205 = xs202
        self.consume_literal(')')
        _t834 = logic_pb2.Attribute(name=name201, args=values205)
        return _t834

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal('(')
        self.consume_literal('algorithm')
        xs206 = []
        cond207 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        while cond207:
            _t835 = self.parse_relation_id()
            item208 = _t835
            xs206.append(item208)
            cond207 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        relation_ids209 = xs206
        _t836 = self.parse_script()
        script210 = _t836
        self.consume_literal(')')
        _t837 = logic_pb2.Algorithm(body=script210)
        getattr(_t837, 'global').extend(relation_ids209)
        return _t837

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal('(')
        self.consume_literal('script')
        xs211 = []
        cond212 = self.match_lookahead_literal('(', 0)
        while cond212:
            _t838 = self.parse_construct()
            item213 = _t838
            xs211.append(item213)
            cond212 = self.match_lookahead_literal('(', 0)
        constructs214 = xs211
        self.consume_literal(')')
        _t839 = logic_pb2.Script(constructs=constructs214)
        return _t839

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t848 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t852 = 1
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t854 = 1
                    else:
                        if self.match_lookahead_literal('loop', 1):
                            _t855 = 0
                        else:
                            _t855 = (self.match_lookahead_literal('break', 1) or (self.match_lookahead_literal('assign', 1) or -1))
                        _t854 = _t855
                    _t852 = _t854
                _t848 = _t852
            _t840 = _t848
        else:
            _t840 = -1
        prediction215 = _t840
        if prediction215 == 1:
            _t857 = self.parse_instruction()
            instruction217 = _t857
            _t858 = logic_pb2.Construct(instruction=instruction217)
            _t856 = _t858
        else:
            if prediction215 == 0:
                _t860 = self.parse_loop()
                loop216 = _t860
                _t861 = logic_pb2.Construct(loop=loop216)
                _t859 = _t861
            else:
                raise ParseError(f"{'Unexpected token in construct'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t859 = None
            _t856 = _t859
        return _t856

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal('(')
        self.consume_literal('loop')
        _t862 = self.parse_init()
        init218 = _t862
        _t863 = self.parse_script()
        script219 = _t863
        self.consume_literal(')')
        _t864 = logic_pb2.Loop(init=init218, body=script219)
        return _t864

    def parse_init(self) -> list[logic_pb2.Instruction]:
        self.consume_literal('(')
        self.consume_literal('init')
        xs220 = []
        cond221 = self.match_lookahead_literal('(', 0)
        while cond221:
            _t865 = self.parse_instruction()
            item222 = _t865
            xs220.append(item222)
            cond221 = self.match_lookahead_literal('(', 0)
        instructions223 = xs220
        self.consume_literal(')')
        return instructions223

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t871 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t872 = 4
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t873 = 3
                    else:
                        if self.match_lookahead_literal('break', 1):
                            _t874 = 2
                        else:
                            if self.match_lookahead_literal('assign', 1):
                                _t875 = 0
                            else:
                                _t875 = -1
                            _t874 = _t875
                        _t873 = _t874
                    _t872 = _t873
                _t871 = _t872
            _t866 = _t871
        else:
            _t866 = -1
        prediction224 = _t866
        if prediction224 == 4:
            _t877 = self.parse_monus_def()
            monus_def229 = _t877
            _t878 = logic_pb2.Instruction(monus_def=monus_def229)
            _t876 = _t878
        else:
            if prediction224 == 3:
                _t880 = self.parse_monoid_def()
                monoid_def228 = _t880
                _t881 = logic_pb2.Instruction(monoid_def=monoid_def228)
                _t879 = _t881
            else:
                if prediction224 == 2:
                    _t883 = self.parse_break()
                    break227 = _t883
                    _t884 = logic_pb2.Instruction()
                    getattr(_t884, 'break').CopyFrom(break227)
                    _t882 = _t884
                else:
                    if prediction224 == 1:
                        _t886 = self.parse_upsert()
                        upsert226 = _t886
                        _t887 = logic_pb2.Instruction(upsert=upsert226)
                        _t885 = _t887
                    else:
                        if prediction224 == 0:
                            _t889 = self.parse_assign()
                            assign225 = _t889
                            _t890 = logic_pb2.Instruction(assign=assign225)
                            _t888 = _t890
                        else:
                            raise ParseError(f"{'Unexpected token in instruction'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t888 = None
                        _t885 = _t888
                    _t882 = _t885
                _t879 = _t882
            _t876 = _t879
        return _t876

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal('(')
        self.consume_literal('assign')
        _t891 = self.parse_relation_id()
        relation_id230 = _t891
        _t892 = self.parse_abstraction()
        abstraction231 = _t892
        if self.match_lookahead_literal('(', 0):
            _t894 = self.parse_attrs()
            _t893 = _t894
        else:
            _t893 = None
        attrs232 = _t893
        self.consume_literal(')')
        _t895 = logic_pb2.Assign(name=relation_id230, body=abstraction231, attrs=(attrs232 if attrs232 is not None else []))
        return _t895

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal('(')
        self.consume_literal('upsert')
        _t896 = self.parse_relation_id()
        relation_id233 = _t896
        _t897 = self.parse_abstraction_with_arity()
        abstraction_with_arity234 = _t897
        if self.match_lookahead_literal('(', 0):
            _t899 = self.parse_attrs()
            _t898 = _t899
        else:
            _t898 = None
        attrs235 = _t898
        self.consume_literal(')')
        _t900 = logic_pb2.Upsert(name=relation_id233, body=abstraction_with_arity234[0], attrs=(attrs235 if attrs235 is not None else []), value_arity=abstraction_with_arity234[1])
        return _t900

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal('(')
        _t901 = self.parse_bindings()
        bindings236 = _t901
        _t902 = self.parse_formula()
        formula237 = _t902
        self.consume_literal(')')
        _t903 = logic_pb2.Abstraction(vars=(bindings236[0] + (bindings236[1] if bindings236[1] is not None else [])), value=formula237)
        return (_t903, len(bindings236[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal('(')
        self.consume_literal('break')
        _t904 = self.parse_relation_id()
        relation_id238 = _t904
        _t905 = self.parse_abstraction()
        abstraction239 = _t905
        if self.match_lookahead_literal('(', 0):
            _t907 = self.parse_attrs()
            _t906 = _t907
        else:
            _t906 = None
        attrs240 = _t906
        self.consume_literal(')')
        _t908 = logic_pb2.Break(name=relation_id238, body=abstraction239, attrs=(attrs240 if attrs240 is not None else []))
        return _t908

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal('(')
        self.consume_literal('monoid')
        _t909 = self.parse_monoid()
        monoid241 = _t909
        _t910 = self.parse_relation_id()
        relation_id242 = _t910
        _t911 = self.parse_abstraction_with_arity()
        abstraction_with_arity243 = _t911
        if self.match_lookahead_literal('(', 0):
            _t913 = self.parse_attrs()
            _t912 = _t913
        else:
            _t912 = None
        attrs244 = _t912
        self.consume_literal(')')
        _t914 = logic_pb2.MonoidDef(monoid=monoid241, name=relation_id242, body=abstraction_with_arity243[0], attrs=(attrs244 if attrs244 is not None else []), value_arity=abstraction_with_arity243[1])
        return _t914

    def parse_monoid(self) -> logic_pb2.Monoid:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('sum', 1):
                _t916 = 3
            else:
                if self.match_lookahead_literal('or', 1):
                    _t917 = 0
                else:
                    if self.match_lookahead_literal('min', 1):
                        _t919 = 1
                    else:
                        if self.match_lookahead_literal('max', 1):
                            _t920 = 2
                        else:
                            _t920 = -1
                        _t919 = _t920
                    _t917 = _t919
                _t916 = _t917
            _t915 = _t916
        else:
            _t915 = -1
        prediction245 = _t915
        if prediction245 == 3:
            _t922 = self.parse_sum_monoid()
            sum_monoid249 = _t922
            _t923 = logic_pb2.Monoid(sum_monoid=sum_monoid249)
            _t921 = _t923
        else:
            if prediction245 == 2:
                _t925 = self.parse_max_monoid()
                max_monoid248 = _t925
                _t926 = logic_pb2.Monoid(max_monoid=max_monoid248)
                _t924 = _t926
            else:
                if prediction245 == 1:
                    _t928 = self.parse_min_monoid()
                    min_monoid247 = _t928
                    _t929 = logic_pb2.Monoid(min_monoid=min_monoid247)
                    _t927 = _t929
                else:
                    if prediction245 == 0:
                        _t931 = self.parse_or_monoid()
                        or_monoid246 = _t931
                        _t932 = logic_pb2.Monoid(or_monoid=or_monoid246)
                        _t930 = _t932
                    else:
                        raise ParseError(f"{'Unexpected token in monoid'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t930 = None
                    _t927 = _t930
                _t924 = _t927
            _t921 = _t924
        return _t921

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        self.consume_literal('(')
        self.consume_literal('or')
        self.consume_literal(')')
        return logic_pb2.OrMonoid()

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        self.consume_literal('(')
        self.consume_literal('min')
        _t933 = self.parse_type()
        type250 = _t933
        self.consume_literal(')')
        _t934 = logic_pb2.MinMonoid(type=type250)
        return _t934

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        self.consume_literal('(')
        self.consume_literal('max')
        _t935 = self.parse_type()
        type251 = _t935
        self.consume_literal(')')
        _t936 = logic_pb2.MaxMonoid(type=type251)
        return _t936

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        self.consume_literal('(')
        self.consume_literal('sum')
        _t937 = self.parse_type()
        type252 = _t937
        self.consume_literal(')')
        _t938 = logic_pb2.SumMonoid(type=type252)
        return _t938

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal('(')
        self.consume_literal('monus')
        _t939 = self.parse_monoid()
        monoid253 = _t939
        _t940 = self.parse_relation_id()
        relation_id254 = _t940
        _t941 = self.parse_abstraction_with_arity()
        abstraction_with_arity255 = _t941
        if self.match_lookahead_literal('(', 0):
            _t943 = self.parse_attrs()
            _t942 = _t943
        else:
            _t942 = None
        attrs256 = _t942
        self.consume_literal(')')
        _t944 = logic_pb2.MonusDef(monoid=monoid253, name=relation_id254, body=abstraction_with_arity255[0], attrs=(attrs256 if attrs256 is not None else []), value_arity=abstraction_with_arity255[1])
        return _t944

    def parse_constraint(self) -> logic_pb2.Constraint:
        self.consume_literal('(')
        self.consume_literal('functional_dependency')
        _t945 = self.parse_relation_id()
        relation_id257 = _t945
        _t946 = self.parse_abstraction()
        abstraction258 = _t946
        _t947 = self.parse_functional_dependency_keys()
        functional_dependency_keys259 = _t947
        _t948 = self.parse_functional_dependency_values()
        functional_dependency_values260 = _t948
        self.consume_literal(')')
        _t949 = logic_pb2.FunctionalDependency(guard=abstraction258, keys=functional_dependency_keys259, values=functional_dependency_values260)
        _t950 = logic_pb2.Constraint(name=relation_id257, functional_dependency=_t949)
        return _t950

    def parse_functional_dependency_keys(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('keys')
        xs261 = []
        cond262 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond262:
            _t951 = self.parse_var()
            item263 = _t951
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
            _t952 = self.parse_var()
            item267 = _t952
            xs265.append(item267)
            cond266 = self.match_lookahead_terminal('SYMBOL', 0)
        vars268 = xs265
        self.consume_literal(')')
        return vars268

    def parse_data(self) -> logic_pb2.Data:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('rel_edb', 1):
                _t954 = 0
            else:
                if self.match_lookahead_literal('csv_data', 1):
                    _t955 = 2
                else:
                    _t955 = (self.match_lookahead_literal('betree_relation', 1) or -1)
                _t954 = _t955
            _t953 = _t954
        else:
            _t953 = -1
        prediction269 = _t953
        if prediction269 == 2:
            _t957 = self.parse_csv_data()
            csv_data272 = _t957
            _t958 = logic_pb2.Data(csv_data=csv_data272)
            _t956 = _t958
        else:
            if prediction269 == 1:
                _t960 = self.parse_betree_relation()
                betree_relation271 = _t960
                _t961 = logic_pb2.Data(betree_relation=betree_relation271)
                _t959 = _t961
            else:
                if prediction269 == 0:
                    _t963 = self.parse_rel_edb()
                    rel_edb270 = _t963
                    _t964 = logic_pb2.Data(rel_edb=rel_edb270)
                    _t962 = _t964
                else:
                    raise ParseError(f"{'Unexpected token in data'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t962 = None
                _t959 = _t962
            _t956 = _t959
        return _t956

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        self.consume_literal('(')
        self.consume_literal('rel_edb')
        _t965 = self.parse_relation_id()
        relation_id273 = _t965
        _t966 = self.parse_rel_edb_path()
        rel_edb_path274 = _t966
        _t967 = self.parse_rel_edb_types()
        rel_edb_types275 = _t967
        self.consume_literal(')')
        _t968 = logic_pb2.RelEDB(target_id=relation_id273, path=rel_edb_path274, types=rel_edb_types275)
        return _t968

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
            _t969 = self.parse_type()
            item282 = _t969
            xs280.append(item282)
            cond281 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types283 = xs280
        self.consume_literal(']')
        return types283

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        _t970 = self.parse_be_tree_relation()
        be_tree_relation284 = _t970
        return be_tree_relation284

    def parse_be_tree_relation(self) -> logic_pb2.BeTreeRelation:
        self.consume_literal('(')
        self.consume_literal('betree_relation')
        _t971 = self.parse_relation_id()
        relation_id285 = _t971
        _t972 = self.parse_be_tree_info()
        be_tree_info286 = _t972
        self.consume_literal(')')
        _t973 = logic_pb2.BeTreeRelation(name=relation_id285, relation_info=be_tree_info286)
        return _t973

    def parse_be_tree_info(self) -> logic_pb2.BeTreeInfo:
        self.consume_literal('(')
        self.consume_literal('betree_info')
        _t974 = self.parse_be_tree_info_key_types()
        be_tree_info_key_types287 = _t974
        _t975 = self.parse_be_tree_info_value_types()
        be_tree_info_value_types288 = _t975
        _t976 = self.parse_config_dict()
        config_dict289 = _t976
        self.consume_literal(')')
        return self.construct_betree_info(be_tree_info_key_types287, be_tree_info_value_types288, config_dict289)

    def parse_be_tree_info_key_types(self) -> list[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('key_types')
        xs290 = []
        cond291 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond291:
            _t977 = self.parse_type()
            item292 = _t977
            xs290.append(item292)
            cond291 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types293 = xs290
        self.consume_literal(')')
        return types293

    def parse_be_tree_info_value_types(self) -> list[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('value_types')
        xs294 = []
        cond295 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond295:
            _t978 = self.parse_type()
            item296 = _t978
            xs294.append(item296)
            cond295 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types297 = xs294
        self.consume_literal(')')
        return types297

    def parse_csv_data(self) -> logic_pb2.CSVData:
        _t979 = self.parse_csvdata()
        csvdata298 = _t979
        return csvdata298

    def parse_csvdata(self) -> logic_pb2.CSVData:
        self.consume_literal('(')
        self.consume_literal('csv_data')
        _t980 = self.parse_csvlocator()
        csvlocator299 = _t980
        _t981 = self.parse_csv_config()
        csv_config300 = _t981
        _t982 = self.parse_csv_columns()
        csv_columns301 = _t982
        _t983 = self.parse_csv_asof()
        csv_asof302 = _t983
        self.consume_literal(')')
        _t984 = logic_pb2.CSVData(locator=csvlocator299, config=csv_config300, columns=csv_columns301, asof=csv_asof302)
        return _t984

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        self.consume_literal('(')
        self.consume_literal('csv_locator')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('paths', 1)):
            _t986 = self.parse_csv_locator_paths()
            _t985 = _t986
        else:
            _t985 = None
        csv_locator_paths303 = _t985
        if self.match_lookahead_literal('(', 0):
            _t988 = self.parse_csv_locator_inline_data()
            _t987 = _t988
        else:
            _t987 = None
        csv_locator_inline_data304 = _t987
        self.consume_literal(')')
        _t989 = logic_pb2.CSVLocator(paths=(csv_locator_paths303 if csv_locator_paths303 is not None else []), inline_data=(csv_locator_inline_data304 if csv_locator_inline_data304 is not None else '').encode())
        return _t989

    def parse_csv_locator_paths(self) -> list[str]:
        self.consume_literal('(')
        self.consume_literal('paths')
        xs305 = []
        cond306 = self.match_lookahead_terminal('STRING', 0)
        while cond306:
            item307 = self.consume_terminal('STRING')
            xs305.append(item307)
            cond306 = self.match_lookahead_terminal('STRING', 0)
        strings308 = xs305
        self.consume_literal(')')
        return strings308

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal('(')
        self.consume_literal('inline_data')
        string309 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return string309

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        self.consume_literal('(')
        self.consume_literal('csv_config')
        _t990 = self.parse_config_dict()
        config_dict310 = _t990
        self.consume_literal(')')
        return self.construct_csv_config(config_dict310)

    def parse_csv_columns(self) -> list[logic_pb2.CSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs311 = []
        cond312 = self.match_lookahead_literal('(', 0)
        while cond312:
            _t991 = self.parse_csv_column()
            item313 = _t991
            xs311.append(item313)
            cond312 = self.match_lookahead_literal('(', 0)
        csv_columns314 = xs311
        self.consume_literal(')')
        return csv_columns314

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        string315 = self.consume_terminal('STRING')
        _t992 = self.parse_relation_id()
        relation_id316 = _t992
        self.consume_literal('[')
        xs317 = []
        cond318 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond318:
            _t993 = self.parse_type()
            item319 = _t993
            xs317.append(item319)
            cond318 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types320 = xs317
        self.consume_literal(']')
        self.consume_literal(')')
        _t994 = logic_pb2.CSVColumn(column_name=string315, target_id=relation_id316, types=types320)
        return _t994

    def parse_csv_asof(self) -> str:
        self.consume_literal('(')
        self.consume_literal('asof')
        string321 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return string321

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal('(')
        self.consume_literal('undefine')
        _t995 = self.parse_fragment_id()
        fragment_id322 = _t995
        self.consume_literal(')')
        _t996 = transactions_pb2.Undefine(fragment_id=fragment_id322)
        return _t996

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal('(')
        self.consume_literal('context')
        xs323 = []
        cond324 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        while cond324:
            _t997 = self.parse_relation_id()
            item325 = _t997
            xs323.append(item325)
            cond324 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        relation_ids326 = xs323
        self.consume_literal(')')
        _t998 = transactions_pb2.Context(relations=relation_ids326)
        return _t998

    def parse_epoch_reads(self) -> list[transactions_pb2.Read]:
        self.consume_literal('(')
        self.consume_literal('reads')
        xs327 = []
        cond328 = self.match_lookahead_literal('(', 0)
        while cond328:
            _t999 = self.parse_read()
            item329 = _t999
            xs327.append(item329)
            cond328 = self.match_lookahead_literal('(', 0)
        reads330 = xs327
        self.consume_literal(')')
        return reads330

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('what_if', 1):
                _t1001 = 2
            else:
                if self.match_lookahead_literal('output', 1):
                    _t1005 = 1
                else:
                    if self.match_lookahead_literal('export', 1):
                        _t1006 = 4
                    else:
                        if self.match_lookahead_literal('demand', 1):
                            _t1007 = 0
                        else:
                            if self.match_lookahead_literal('abort', 1):
                                _t1008 = 3
                            else:
                                _t1008 = -1
                            _t1007 = _t1008
                        _t1006 = _t1007
                    _t1005 = _t1006
                _t1001 = _t1005
            _t1000 = _t1001
        else:
            _t1000 = -1
        prediction331 = _t1000
        if prediction331 == 4:
            _t1010 = self.parse_export()
            export336 = _t1010
            _t1011 = transactions_pb2.Read(export=export336)
            _t1009 = _t1011
        else:
            if prediction331 == 3:
                _t1013 = self.parse_abort()
                abort335 = _t1013
                _t1014 = transactions_pb2.Read(abort=abort335)
                _t1012 = _t1014
            else:
                if prediction331 == 2:
                    _t1016 = self.parse_what_if()
                    what_if334 = _t1016
                    _t1017 = transactions_pb2.Read(what_if=what_if334)
                    _t1015 = _t1017
                else:
                    if prediction331 == 1:
                        _t1019 = self.parse_output()
                        output333 = _t1019
                        _t1020 = transactions_pb2.Read(output=output333)
                        _t1018 = _t1020
                    else:
                        if prediction331 == 0:
                            _t1022 = self.parse_demand()
                            demand332 = _t1022
                            _t1023 = transactions_pb2.Read(demand=demand332)
                            _t1021 = _t1023
                        else:
                            raise ParseError(f"{'Unexpected token in read'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t1021 = None
                        _t1018 = _t1021
                    _t1015 = _t1018
                _t1012 = _t1015
            _t1009 = _t1012
        return _t1009

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal('(')
        self.consume_literal('demand')
        _t1024 = self.parse_relation_id()
        relation_id337 = _t1024
        self.consume_literal(')')
        _t1025 = transactions_pb2.Demand(relation_id=relation_id337)
        return _t1025

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal('(')
        self.consume_literal('output')
        if (self.match_lookahead_literal(':', 0) and self.match_lookahead_terminal('SYMBOL', 1)):
            _t1027 = self.parse_name()
            _t1026 = _t1027
        else:
            _t1026 = None
        name338 = _t1026
        _t1028 = self.parse_relation_id()
        relation_id339 = _t1028
        self.consume_literal(')')
        _t1029 = transactions_pb2.Output(name=(name338 if name338 is not None else 'output'), relation_id=relation_id339)
        return _t1029

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal('(')
        self.consume_literal('what_if')
        _t1030 = self.parse_name()
        name340 = _t1030
        _t1031 = self.parse_epoch()
        epoch341 = _t1031
        self.consume_literal(')')
        _t1032 = transactions_pb2.WhatIf(branch=name340, epoch=epoch341)
        return _t1032

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal('(')
        self.consume_literal('abort')
        if (self.match_lookahead_literal(':', 0) and self.match_lookahead_terminal('SYMBOL', 1)):
            _t1034 = self.parse_name()
            _t1033 = _t1034
        else:
            _t1033 = None
        name342 = _t1033
        _t1035 = self.parse_relation_id()
        relation_id343 = _t1035
        self.consume_literal(')')
        _t1036 = transactions_pb2.Abort(name=(name342 if name342 is not None else 'abort'), relation_id=relation_id343)
        return _t1036

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal('(')
        self.consume_literal('export')
        _t1037 = self.parse_export_csv_config()
        export_csv_config344 = _t1037
        self.consume_literal(')')
        _t1038 = transactions_pb2.Export(csv_config=export_csv_config344)
        return _t1038

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal('(')
        self.consume_literal('export_csv_config')
        _t1039 = self.parse_export_csv_path()
        export_csv_path345 = _t1039
        _t1040 = self.parse_export_csv_columns()
        export_csv_columns346 = _t1040
        _t1041 = self.parse_config_dict()
        config_dict347 = _t1041
        self.consume_literal(')')
        return self.export_csv_config(export_csv_path345, export_csv_columns346, config_dict347)

    def parse_export_csv_path(self) -> str:
        self.consume_literal('(')
        self.consume_literal('path')
        string348 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return string348

    def parse_export_csv_columns(self) -> list[transactions_pb2.ExportCSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs349 = []
        cond350 = self.match_lookahead_literal('(', 0)
        while cond350:
            _t1042 = self.parse_export_csv_column()
            item351 = _t1042
            xs349.append(item351)
            cond350 = self.match_lookahead_literal('(', 0)
        export_csv_columns352 = xs349
        self.consume_literal(')')
        return export_csv_columns352

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        string353 = self.consume_terminal('STRING')
        _t1043 = self.parse_relation_id()
        relation_id354 = _t1043
        self.consume_literal(')')
        _t1044 = transactions_pb2.ExportCSVColumn(column_name=string353, column_data=relation_id354)
        return _t1044


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
