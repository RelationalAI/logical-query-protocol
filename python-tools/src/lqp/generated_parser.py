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
            _t1017 = None
        if value.HasField('int_value'):
            return value.int_value
        else:
            _t1018 = None
        return default

    @staticmethod
    def _extract_value_float64(value: Optional[logic_pb2.Value], default: float) -> float:
        if value is None:
            return default
        else:
            _t1019 = None
        if value.HasField('float_value'):
            return value.float_value
        else:
            _t1020 = None
        return default

    @staticmethod
    def _extract_value_string(value: Optional[logic_pb2.Value], default: str) -> str:
        if value is None:
            return default
        else:
            _t1021 = None
        if value.HasField('string_value'):
            return value.string_value
        else:
            _t1022 = None
        return default

    @staticmethod
    def _extract_value_boolean(value: Optional[logic_pb2.Value], default: bool) -> bool:
        if value is None:
            return default
        else:
            _t1023 = None
        if value.HasField('boolean_value'):
            return value.boolean_value
        else:
            _t1024 = None
        return default

    @staticmethod
    def _extract_value_bytes(value: Optional[logic_pb2.Value], default: bytes) -> bytes:
        if value is None:
            return default
        else:
            _t1025 = None
        if value.HasField('string_value'):
            _t1027 = value.string_value.encode()
            return _t1027
        else:
            _t1026 = None
        return default

    @staticmethod
    def _extract_value_uint128(value: Optional[logic_pb2.Value], default: logic_pb2.UInt128Value) -> logic_pb2.UInt128Value:
        if value is None:
            return default
        else:
            _t1028 = None
        if value.HasField('uint128_value'):
            return value.uint128_value
        else:
            _t1029 = None
        return default

    @staticmethod
    def _extract_value_string_list(value: Optional[logic_pb2.Value], default: list[str]) -> list[str]:
        if value is None:
            return default
        else:
            _t1030 = None
        if value.HasField('string_value'):
            return [value.string_value]
        else:
            _t1031 = None
        return default

    @staticmethod
    def construct_csv_config(config_dict: list[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1032 = Parser._extract_value_int64(config.get('csv_header_row'), 1)
        header_row = _t1032
        _t1033 = Parser._extract_value_int64(config.get('csv_skip'), 0)
        skip = _t1033
        _t1034 = Parser._extract_value_string(config.get('csv_new_line'), '')
        new_line = _t1034
        _t1035 = Parser._extract_value_string(config.get('csv_delimiter'), ',')
        delimiter = _t1035
        _t1036 = Parser._extract_value_string(config.get('csv_quotechar'), '"')
        quotechar = _t1036
        _t1037 = Parser._extract_value_string(config.get('csv_escapechar'), '"')
        escapechar = _t1037
        _t1038 = Parser._extract_value_string(config.get('csv_comment'), '')
        comment = _t1038
        _t1039 = Parser._extract_value_string_list(config.get('csv_missing_strings'), [])
        missing_strings = _t1039
        _t1040 = Parser._extract_value_string(config.get('csv_decimal_separator'), '.')
        decimal_separator = _t1040
        _t1041 = Parser._extract_value_string(config.get('csv_encoding'), 'utf-8')
        encoding = _t1041
        _t1042 = Parser._extract_value_string(config.get('csv_compression'), 'auto')
        compression = _t1042
        _t1043 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t1043

    @staticmethod
    def construct_betree_info(key_types: list[logic_pb2.Type], value_types: list[logic_pb2.Type], config_dict: list[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1044 = Parser._extract_value_float64(config.get('betree_config_epsilon'), 0.5)
        epsilon = _t1044
        _t1045 = Parser._extract_value_int64(config.get('betree_config_max_pivots'), 4)
        max_pivots = _t1045
        _t1046 = Parser._extract_value_int64(config.get('betree_config_max_deltas'), 16)
        max_deltas = _t1046
        _t1047 = Parser._extract_value_int64(config.get('betree_config_max_leaf'), 16)
        max_leaf = _t1047
        _t1048 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1048
        root_pageid_val = config.get('betree_locator_root_pageid')
        root_pageid = None
        if root_pageid_val is not None:
            _t1050 = logic_pb2.UInt128Value(low=0, high=0)
            _t1051 = Parser._extract_value_uint128(root_pageid_val, _t1050)
            root_pageid = _t1051
            _t1049 = None
        else:
            _t1049 = None
        inline_data_val = config.get('betree_locator_inline_data')
        inline_data = None
        if inline_data_val is not None:
            _t1053 = Parser._extract_value_bytes(inline_data_val, b'')
            inline_data = _t1053
            _t1052 = None
        else:
            _t1052 = None
        _t1054 = Parser._extract_value_int64(config.get('betree_locator_element_count'), 0)
        element_count = _t1054
        _t1055 = Parser._extract_value_int64(config.get('betree_locator_tree_height'), 0)
        tree_height = _t1055
        _t1056 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1056
        _t1057 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1057

    @staticmethod
    def construct_configure(config_dict: list[tuple[str, logic_pb2.Value]]) -> transactions_pb2.Configure:
        config = dict(config_dict)
        maintenance_level_val = config.get('ivm.maintenance_level')
        maintenance_level = None
        if (maintenance_level_val is not None and maintenance_level_val.HasField('string_value')):
            _t1059 = maintenance_level_val.string_value.upper()
            level_str = _t1059
            if level_str in ['OFF', 'AUTO', 'ALL']:
                maintenance_level = ('MAINTENANCE_LEVEL_' + level_str)
                _t1060 = None
            else:
                maintenance_level = level_str
                _t1060 = None
            _t1058 = _t1060
        else:
            maintenance_level = 'MAINTENANCE_LEVEL_OFF'
            _t1058 = None
        _t1061 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1061
        _t1062 = Parser._extract_value_int64(config.get('semantics_version'), 0)
        semantics_version = _t1062
        _t1063 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1063

    @staticmethod
    def export_csv_config(path: str, columns: list[transactions_pb2.ExportCSVColumn], config_dict: list[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1064 = Parser._extract_value_int64(config.get('partition_size'), 0)
        partition_size = _t1064
        _t1065 = Parser._extract_value_string(config.get('compression'), '')
        compression = _t1065
        _t1066 = Parser._extract_value_boolean(config.get('syntax_header_row'), True)
        syntax_header_row = _t1066
        _t1067 = Parser._extract_value_string(config.get('syntax_missing_string'), '')
        syntax_missing_string = _t1067
        _t1068 = Parser._extract_value_string(config.get('syntax_delim'), ',')
        syntax_delim = _t1068
        _t1069 = Parser._extract_value_string(config.get('syntax_quotechar'), '"')
        syntax_quotechar = _t1069
        _t1070 = Parser._extract_value_string(config.get('syntax_escapechar'), '\\')
        syntax_escapechar = _t1070
        _t1071 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1071

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        self.consume_literal('(')
        self.consume_literal('transaction')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('configure', 1)):
            _t324 = self.parse_configure()
            _t323 = _t324
        else:
            _t323 = None
        configure0 = _t323
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('sync', 1)):
            _t326 = self.parse_sync()
            _t325 = _t326
        else:
            _t325 = None
        sync1 = _t325
        xs2 = []
        cond3 = self.match_lookahead_literal('(', 0)
        while cond3:
            _t327 = self.parse_epoch()
            xs2.append(_t327)
            cond3 = self.match_lookahead_literal('(', 0)
        epochs4 = xs2
        self.consume_literal(')')
        _t328 = transactions_pb2.Transaction(epochs=epochs4, configure=(configure0 if configure0 is not None else self.construct_configure([])), sync=sync1)
        return _t328

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal('(')
        self.consume_literal('configure')
        _t329 = self.parse_config_dict()
        config_dict5 = _t329
        self.consume_literal(')')
        return self.construct_configure(config_dict5)

    def parse_config_dict(self) -> list[tuple[str, logic_pb2.Value]]:
        self.consume_literal('{')
        xs6 = []
        cond7 = self.match_lookahead_literal(':', 0)
        while cond7:
            _t330 = self.parse_config_key_value()
            xs6.append(_t330)
            cond7 = self.match_lookahead_literal(':', 0)
        config_key_values8 = xs6
        self.consume_literal('}')
        return config_key_values8

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(':')
        symbol9 = self.consume_terminal('SYMBOL')
        _t331 = self.parse_value()
        value10 = _t331
        return (symbol9, value10,)

    def parse_value(self) -> logic_pb2.Value:
        if self.match_lookahead_literal('true', 0):
            _t332 = 9
        else:
            if self.match_lookahead_literal('missing', 0):
                _t333 = 8
            else:
                if self.match_lookahead_literal('false', 0):
                    _t334 = 9
                else:
                    if self.match_lookahead_literal('(', 0):
                        if self.match_lookahead_literal('datetime', 1):
                            _t337 = 1
                        else:
                            if self.match_lookahead_literal('date', 1):
                                _t338 = 0
                            else:
                                _t338 = -1
                            _t337 = _t338
                        _t335 = _t337
                    else:
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t339 = 5
                        else:
                            if self.match_lookahead_terminal('STRING', 0):
                                _t340 = 2
                            else:
                                if self.match_lookahead_terminal('INT128', 0):
                                    _t341 = 6
                                else:
                                    if self.match_lookahead_terminal('INT', 0):
                                        _t342 = 3
                                    else:
                                        if self.match_lookahead_terminal('FLOAT', 0):
                                            _t343 = 4
                                        else:
                                            if self.match_lookahead_terminal('DECIMAL', 0):
                                                _t344 = 7
                                            else:
                                                _t344 = -1
                                            _t343 = _t344
                                        _t342 = _t343
                                    _t341 = _t342
                                _t340 = _t341
                            _t339 = _t340
                        _t335 = _t339
                    _t334 = _t335
                _t333 = _t334
            _t332 = _t333
        prediction11 = _t332
        if prediction11 == 9:
            _t346 = self.parse_boolean_value()
            boolean_value20 = _t346
            _t347 = logic_pb2.Value(boolean_value=boolean_value20)
            _t345 = _t347
        else:
            if prediction11 == 8:
                self.consume_literal('missing')
                _t349 = logic_pb2.Value(missing_value=logic_pb2.MissingValue())
                _t348 = _t349
            else:
                if prediction11 == 7:
                    decimal19 = self.consume_terminal('DECIMAL')
                    _t351 = logic_pb2.Value(decimal_value=decimal19)
                    _t350 = _t351
                else:
                    if prediction11 == 6:
                        int12818 = self.consume_terminal('INT128')
                        _t353 = logic_pb2.Value(int128_value=int12818)
                        _t352 = _t353
                    else:
                        if prediction11 == 5:
                            uint12817 = self.consume_terminal('UINT128')
                            _t355 = logic_pb2.Value(uint128_value=uint12817)
                            _t354 = _t355
                        else:
                            if prediction11 == 4:
                                float16 = self.consume_terminal('FLOAT')
                                _t357 = logic_pb2.Value(float_value=float16)
                                _t356 = _t357
                            else:
                                if prediction11 == 3:
                                    int15 = self.consume_terminal('INT')
                                    _t359 = logic_pb2.Value(int_value=int15)
                                    _t358 = _t359
                                else:
                                    if prediction11 == 2:
                                        string14 = self.consume_terminal('STRING')
                                        _t361 = logic_pb2.Value(string_value=string14)
                                        _t360 = _t361
                                    else:
                                        if prediction11 == 1:
                                            _t363 = self.parse_datetime()
                                            datetime13 = _t363
                                            _t364 = logic_pb2.Value(datetime_value=datetime13)
                                            _t362 = _t364
                                        else:
                                            if prediction11 == 0:
                                                _t366 = self.parse_date()
                                                date12 = _t366
                                                _t367 = logic_pb2.Value(date_value=date12)
                                                _t365 = _t367
                                            else:
                                                raise ParseError(f"{'Unexpected token in value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t365 = None
                                            _t362 = _t365
                                        _t360 = _t362
                                    _t358 = _t360
                                _t356 = _t358
                            _t354 = _t356
                        _t352 = _t354
                    _t350 = _t352
                _t348 = _t350
            _t345 = _t348
        return _t345

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal('(')
        self.consume_literal('date')
        int21 = self.consume_terminal('INT')
        int_322 = self.consume_terminal('INT')
        int_423 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t368 = logic_pb2.DateValue(year=int(int21), month=int(int_322), day=int(int_423))
        return _t368

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        self.consume_literal('(')
        self.consume_literal('datetime')
        int24 = self.consume_terminal('INT')
        int_325 = self.consume_terminal('INT')
        int_426 = self.consume_terminal('INT')
        int_527 = self.consume_terminal('INT')
        int_628 = self.consume_terminal('INT')
        int_729 = self.consume_terminal('INT')
        if self.match_lookahead_terminal('INT', 0):
            _t369 = self.consume_terminal('INT')
        else:
            _t369 = None
        int_830 = _t369
        self.consume_literal(')')
        _t370 = logic_pb2.DateTimeValue(year=int(int24), month=int(int_325), day=int(int_426), hour=int(int_527), minute=int(int_628), second=int(int_729), microsecond=int((int_830 if int_830 is not None else 0)))
        return _t370

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal('true', 0):
            _t371 = 0
        else:
            _t371 = (self.match_lookahead_literal('false', 0) or -1)
        prediction31 = _t371
        if prediction31 == 1:
            self.consume_literal('false')
            _t372 = False
        else:
            if prediction31 == 0:
                self.consume_literal('true')
                _t373 = True
            else:
                raise ParseError(f"{'Unexpected token in boolean_value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t373 = None
            _t372 = _t373
        return _t372

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal('(')
        self.consume_literal('sync')
        xs32 = []
        cond33 = self.match_lookahead_literal(':', 0)
        while cond33:
            _t374 = self.parse_fragment_id()
            xs32.append(_t374)
            cond33 = self.match_lookahead_literal(':', 0)
        fragment_ids34 = xs32
        self.consume_literal(')')
        _t375 = transactions_pb2.Sync(fragments=fragment_ids34)
        return _t375

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        self.consume_literal(':')
        symbol35 = self.consume_terminal('SYMBOL')
        return fragments_pb2.FragmentId(id=symbol35.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal('(')
        self.consume_literal('epoch')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('writes', 1)):
            _t377 = self.parse_epoch_writes()
            _t376 = _t377
        else:
            _t376 = None
        epoch_writes36 = _t376
        if self.match_lookahead_literal('(', 0):
            _t379 = self.parse_epoch_reads()
            _t378 = _t379
        else:
            _t378 = None
        epoch_reads37 = _t378
        self.consume_literal(')')
        _t380 = transactions_pb2.Epoch(writes=(epoch_writes36 if epoch_writes36 is not None else []), reads=(epoch_reads37 if epoch_reads37 is not None else []))
        return _t380

    def parse_epoch_writes(self) -> list[transactions_pb2.Write]:
        self.consume_literal('(')
        self.consume_literal('writes')
        xs38 = []
        cond39 = self.match_lookahead_literal('(', 0)
        while cond39:
            _t381 = self.parse_write()
            xs38.append(_t381)
            cond39 = self.match_lookahead_literal('(', 0)
        writes40 = xs38
        self.consume_literal(')')
        return writes40

    def parse_write(self) -> transactions_pb2.Write:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('undefine', 1):
                _t385 = 1
            else:
                if self.match_lookahead_literal('define', 1):
                    _t386 = 0
                else:
                    if self.match_lookahead_literal('context', 1):
                        _t387 = 2
                    else:
                        _t387 = -1
                    _t386 = _t387
                _t385 = _t386
            _t382 = _t385
        else:
            _t382 = -1
        prediction41 = _t382
        if prediction41 == 2:
            _t389 = self.parse_context()
            context44 = _t389
            _t390 = transactions_pb2.Write(context=context44)
            _t388 = _t390
        else:
            if prediction41 == 1:
                _t392 = self.parse_undefine()
                undefine43 = _t392
                _t393 = transactions_pb2.Write(undefine=undefine43)
                _t391 = _t393
            else:
                if prediction41 == 0:
                    _t395 = self.parse_define()
                    define42 = _t395
                    _t396 = transactions_pb2.Write(define=define42)
                    _t394 = _t396
                else:
                    raise ParseError(f"{'Unexpected token in write'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t394 = None
                _t391 = _t394
            _t388 = _t391
        return _t388

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal('(')
        self.consume_literal('define')
        _t397 = self.parse_fragment()
        fragment45 = _t397
        self.consume_literal(')')
        _t398 = transactions_pb2.Define(fragment=fragment45)
        return _t398

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal('(')
        self.consume_literal('fragment')
        _t399 = self.parse_new_fragment_id()
        new_fragment_id46 = _t399
        xs47 = []
        cond48 = self.match_lookahead_literal('(', 0)
        while cond48:
            _t400 = self.parse_declaration()
            xs47.append(_t400)
            cond48 = self.match_lookahead_literal('(', 0)
        declarations49 = xs47
        self.consume_literal(')')
        return self.construct_fragment(new_fragment_id46, declarations49)

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        _t401 = self.parse_fragment_id()
        fragment_id50 = _t401
        self.start_fragment(fragment_id50)
        return fragment_id50

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('rel_edb', 1):
                _t403 = 3
            else:
                if self.match_lookahead_literal('functional_dependency', 1):
                    _t404 = 2
                else:
                    if self.match_lookahead_literal('def', 1):
                        _t405 = 0
                    else:
                        if self.match_lookahead_literal('csv_data', 1):
                            _t406 = 3
                        else:
                            if self.match_lookahead_literal('betree_relation', 1):
                                _t407 = 3
                            else:
                                _t407 = (self.match_lookahead_literal('algorithm', 1) or -1)
                            _t406 = _t407
                        _t405 = _t406
                    _t404 = _t405
                _t403 = _t404
            _t402 = _t403
        else:
            _t402 = -1
        prediction51 = _t402
        if prediction51 == 3:
            _t409 = self.parse_data()
            data55 = _t409
            _t410 = logic_pb2.Declaration(data=data55)
            _t408 = _t410
        else:
            if prediction51 == 2:
                _t412 = self.parse_constraint()
                constraint54 = _t412
                _t413 = logic_pb2.Declaration(constraint=constraint54)
                _t411 = _t413
            else:
                if prediction51 == 1:
                    _t415 = self.parse_algorithm()
                    algorithm53 = _t415
                    _t416 = logic_pb2.Declaration(algorithm=algorithm53)
                    _t414 = _t416
                else:
                    if prediction51 == 0:
                        _t418 = self.parse_def()
                        def52 = _t418
                        _t419 = logic_pb2.Declaration()
                        getattr(_t419, 'def').CopyFrom(def52)
                        _t417 = _t419
                    else:
                        raise ParseError(f"{'Unexpected token in declaration'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t417 = None
                    _t414 = _t417
                _t411 = _t414
            _t408 = _t411
        return _t408

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal('(')
        self.consume_literal('def')
        _t420 = self.parse_relation_id()
        relation_id56 = _t420
        _t421 = self.parse_abstraction()
        abstraction57 = _t421
        if self.match_lookahead_literal('(', 0):
            _t423 = self.parse_attrs()
            _t422 = _t423
        else:
            _t422 = None
        attrs58 = _t422
        self.consume_literal(')')
        _t424 = logic_pb2.Def(name=relation_id56, body=abstraction57, attrs=(attrs58 if attrs58 is not None else []))
        return _t424

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_literal(':', 0):
            _t425 = 0
        else:
            _t425 = (self.match_lookahead_terminal('INT', 0) or -1)
        prediction59 = _t425
        if prediction59 == 1:
            int61 = self.consume_terminal('INT')
            _t426 = logic_pb2.RelationId(id_low=int61 & 0xFFFFFFFFFFFFFFFF, id_high=(int61 >> 64) & 0xFFFFFFFFFFFFFFFF)
        else:
            if prediction59 == 0:
                self.consume_literal(':')
                symbol60 = self.consume_terminal('SYMBOL')
                _t427 = self.relation_id_from_string(symbol60)
            else:
                raise ParseError(f"{'Unexpected token in relation_id'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t427 = None
            _t426 = _t427
        return _t426

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal('(')
        _t428 = self.parse_bindings()
        bindings62 = _t428
        _t429 = self.parse_formula()
        formula63 = _t429
        self.consume_literal(')')
        _t430 = logic_pb2.Abstraction(vars=(bindings62[0] + (bindings62[1] if bindings62[1] is not None else [])), value=formula63)
        return _t430

    def parse_bindings(self) -> tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]:
        self.consume_literal('[')
        xs64 = []
        cond65 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond65:
            _t431 = self.parse_binding()
            xs64.append(_t431)
            cond65 = self.match_lookahead_terminal('SYMBOL', 0)
        bindings66 = xs64
        if self.match_lookahead_literal('|', 0):
            _t433 = self.parse_value_bindings()
            _t432 = _t433
        else:
            _t432 = None
        value_bindings67 = _t432
        self.consume_literal(']')
        return (bindings66, (value_bindings67 if value_bindings67 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol68 = self.consume_terminal('SYMBOL')
        self.consume_literal('::')
        _t434 = self.parse_type()
        type69 = _t434
        _t435 = logic_pb2.Var(name=symbol68)
        _t436 = logic_pb2.Binding(var=_t435, type=type69)
        return _t436

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal('UNKNOWN', 0):
            _t437 = 0
        else:
            if self.match_lookahead_literal('UINT128', 0):
                _t438 = 4
            else:
                if self.match_lookahead_literal('STRING', 0):
                    _t447 = 1
                else:
                    if self.match_lookahead_literal('MISSING', 0):
                        _t448 = 8
                    else:
                        if self.match_lookahead_literal('INT128', 0):
                            _t449 = 5
                        else:
                            if self.match_lookahead_literal('INT', 0):
                                _t450 = 2
                            else:
                                if self.match_lookahead_literal('FLOAT', 0):
                                    _t451 = 3
                                else:
                                    if self.match_lookahead_literal('DATETIME', 0):
                                        _t452 = 7
                                    else:
                                        if self.match_lookahead_literal('DATE', 0):
                                            _t453 = 6
                                        else:
                                            if self.match_lookahead_literal('BOOLEAN', 0):
                                                _t454 = 10
                                            else:
                                                if self.match_lookahead_literal('(', 0):
                                                    _t455 = 9
                                                else:
                                                    _t455 = -1
                                                _t454 = _t455
                                            _t453 = _t454
                                        _t452 = _t453
                                    _t451 = _t452
                                _t450 = _t451
                            _t449 = _t450
                        _t448 = _t449
                    _t447 = _t448
                _t438 = _t447
            _t437 = _t438
        prediction70 = _t437
        if prediction70 == 10:
            _t457 = self.parse_boolean_type()
            boolean_type81 = _t457
            _t458 = logic_pb2.Type(boolean_type=boolean_type81)
            _t456 = _t458
        else:
            if prediction70 == 9:
                _t460 = self.parse_decimal_type()
                decimal_type80 = _t460
                _t461 = logic_pb2.Type(decimal_type=decimal_type80)
                _t459 = _t461
            else:
                if prediction70 == 8:
                    _t463 = self.parse_missing_type()
                    missing_type79 = _t463
                    _t464 = logic_pb2.Type(missing_type=missing_type79)
                    _t462 = _t464
                else:
                    if prediction70 == 7:
                        _t466 = self.parse_datetime_type()
                        datetime_type78 = _t466
                        _t467 = logic_pb2.Type(datetime_type=datetime_type78)
                        _t465 = _t467
                    else:
                        if prediction70 == 6:
                            _t469 = self.parse_date_type()
                            date_type77 = _t469
                            _t470 = logic_pb2.Type(date_type=date_type77)
                            _t468 = _t470
                        else:
                            if prediction70 == 5:
                                _t472 = self.parse_int128_type()
                                int128_type76 = _t472
                                _t473 = logic_pb2.Type(int128_type=int128_type76)
                                _t471 = _t473
                            else:
                                if prediction70 == 4:
                                    _t475 = self.parse_uint128_type()
                                    uint128_type75 = _t475
                                    _t476 = logic_pb2.Type(uint128_type=uint128_type75)
                                    _t474 = _t476
                                else:
                                    if prediction70 == 3:
                                        _t478 = self.parse_float_type()
                                        float_type74 = _t478
                                        _t479 = logic_pb2.Type(float_type=float_type74)
                                        _t477 = _t479
                                    else:
                                        if prediction70 == 2:
                                            _t481 = self.parse_int_type()
                                            int_type73 = _t481
                                            _t482 = logic_pb2.Type(int_type=int_type73)
                                            _t480 = _t482
                                        else:
                                            if prediction70 == 1:
                                                _t484 = self.parse_string_type()
                                                string_type72 = _t484
                                                _t485 = logic_pb2.Type(string_type=string_type72)
                                                _t483 = _t485
                                            else:
                                                if prediction70 == 0:
                                                    _t487 = self.parse_unspecified_type()
                                                    unspecified_type71 = _t487
                                                    _t488 = logic_pb2.Type(unspecified_type=unspecified_type71)
                                                    _t486 = _t488
                                                else:
                                                    raise ParseError(f"{'Unexpected token in type'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                    _t486 = None
                                                _t483 = _t486
                                            _t480 = _t483
                                        _t477 = _t480
                                    _t474 = _t477
                                _t471 = _t474
                            _t468 = _t471
                        _t465 = _t468
                    _t462 = _t465
                _t459 = _t462
            _t456 = _t459
        return _t456

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
        int82 = self.consume_terminal('INT')
        int_383 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t489 = logic_pb2.DecimalType(precision=int(int82), scale=int(int_383))
        return _t489

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal('BOOLEAN')
        return logic_pb2.BooleanType()

    def parse_value_bindings(self) -> list[logic_pb2.Binding]:
        self.consume_literal('|')
        xs84 = []
        cond85 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond85:
            _t490 = self.parse_binding()
            xs84.append(_t490)
            cond85 = self.match_lookahead_terminal('SYMBOL', 0)
        bindings86 = xs84
        return bindings86

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('true', 1):
                _t492 = 0
            else:
                if self.match_lookahead_literal('relatom', 1):
                    _t493 = 11
                else:
                    if self.match_lookahead_literal('reduce', 1):
                        _t494 = 3
                    else:
                        if self.match_lookahead_literal('primitive', 1):
                            _t495 = 10
                        else:
                            if self.match_lookahead_literal('pragma', 1):
                                _t496 = 9
                            else:
                                if self.match_lookahead_literal('or', 1):
                                    _t497 = 5
                                else:
                                    if self.match_lookahead_literal('not', 1):
                                        _t498 = 6
                                    else:
                                        if self.match_lookahead_literal('ffi', 1):
                                            _t499 = 7
                                        else:
                                            if self.match_lookahead_literal('false', 1):
                                                _t513 = 1
                                            else:
                                                if self.match_lookahead_literal('exists', 1):
                                                    _t514 = 2
                                                else:
                                                    if self.match_lookahead_literal('cast', 1):
                                                        _t515 = 12
                                                    else:
                                                        if self.match_lookahead_literal('atom', 1):
                                                            _t516 = 8
                                                        else:
                                                            if self.match_lookahead_literal('and', 1):
                                                                _t517 = 4
                                                            else:
                                                                if self.match_lookahead_literal('>=', 1):
                                                                    _t518 = 10
                                                                else:
                                                                    if self.match_lookahead_literal('>', 1):
                                                                        _t519 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal('=', 1):
                                                                            _t520 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal('<=', 1):
                                                                                _t521 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal('<', 1):
                                                                                    _t522 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal('/', 1):
                                                                                        _t523 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal('-', 1):
                                                                                            _t524 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal('+', 1):
                                                                                                _t525 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal('*', 1):
                                                                                                    _t526 = 10
                                                                                                else:
                                                                                                    _t526 = -1
                                                                                                _t525 = _t526
                                                                                            _t524 = _t525
                                                                                        _t523 = _t524
                                                                                    _t522 = _t523
                                                                                _t521 = _t522
                                                                            _t520 = _t521
                                                                        _t519 = _t520
                                                                    _t518 = _t519
                                                                _t517 = _t518
                                                            _t516 = _t517
                                                        _t515 = _t516
                                                    _t514 = _t515
                                                _t513 = _t514
                                            _t499 = _t513
                                        _t498 = _t499
                                    _t497 = _t498
                                _t496 = _t497
                            _t495 = _t496
                        _t494 = _t495
                    _t493 = _t494
                _t492 = _t493
            _t491 = _t492
        else:
            _t491 = -1
        prediction87 = _t491
        if prediction87 == 12:
            _t528 = self.parse_cast()
            cast100 = _t528
            _t529 = logic_pb2.Formula(cast=cast100)
            _t527 = _t529
        else:
            if prediction87 == 11:
                _t531 = self.parse_rel_atom()
                rel_atom99 = _t531
                _t532 = logic_pb2.Formula(rel_atom=rel_atom99)
                _t530 = _t532
            else:
                if prediction87 == 10:
                    _t534 = self.parse_primitive()
                    primitive98 = _t534
                    _t535 = logic_pb2.Formula(primitive=primitive98)
                    _t533 = _t535
                else:
                    if prediction87 == 9:
                        _t537 = self.parse_pragma()
                        pragma97 = _t537
                        _t538 = logic_pb2.Formula(pragma=pragma97)
                        _t536 = _t538
                    else:
                        if prediction87 == 8:
                            _t540 = self.parse_atom()
                            atom96 = _t540
                            _t541 = logic_pb2.Formula(atom=atom96)
                            _t539 = _t541
                        else:
                            if prediction87 == 7:
                                _t543 = self.parse_ffi()
                                ffi95 = _t543
                                _t544 = logic_pb2.Formula(ffi=ffi95)
                                _t542 = _t544
                            else:
                                if prediction87 == 6:
                                    _t546 = self.parse_not()
                                    not94 = _t546
                                    _t547 = logic_pb2.Formula()
                                    getattr(_t547, 'not').CopyFrom(not94)
                                    _t545 = _t547
                                else:
                                    if prediction87 == 5:
                                        _t549 = self.parse_disjunction()
                                        disjunction93 = _t549
                                        _t550 = logic_pb2.Formula(disjunction=disjunction93)
                                        _t548 = _t550
                                    else:
                                        if prediction87 == 4:
                                            _t552 = self.parse_conjunction()
                                            conjunction92 = _t552
                                            _t553 = logic_pb2.Formula(conjunction=conjunction92)
                                            _t551 = _t553
                                        else:
                                            if prediction87 == 3:
                                                _t555 = self.parse_reduce()
                                                reduce91 = _t555
                                                _t556 = logic_pb2.Formula(reduce=reduce91)
                                                _t554 = _t556
                                            else:
                                                if prediction87 == 2:
                                                    _t558 = self.parse_exists()
                                                    exists90 = _t558
                                                    _t559 = logic_pb2.Formula(exists=exists90)
                                                    _t557 = _t559
                                                else:
                                                    if prediction87 == 1:
                                                        _t561 = self.parse_false()
                                                        false89 = _t561
                                                        _t562 = logic_pb2.Formula(disjunction=false89)
                                                        _t560 = _t562
                                                    else:
                                                        if prediction87 == 0:
                                                            _t564 = self.parse_true()
                                                            true88 = _t564
                                                            _t565 = logic_pb2.Formula(conjunction=true88)
                                                            _t563 = _t565
                                                        else:
                                                            raise ParseError(f"{'Unexpected token in formula'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t563 = None
                                                        _t560 = _t563
                                                    _t557 = _t560
                                                _t554 = _t557
                                            _t551 = _t554
                                        _t548 = _t551
                                    _t545 = _t548
                                _t542 = _t545
                            _t539 = _t542
                        _t536 = _t539
                    _t533 = _t536
                _t530 = _t533
            _t527 = _t530
        return _t527

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('true')
        self.consume_literal(')')
        _t566 = logic_pb2.Conjunction(args=[])
        return _t566

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('false')
        self.consume_literal(')')
        _t567 = logic_pb2.Disjunction(args=[])
        return _t567

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal('(')
        self.consume_literal('exists')
        _t568 = self.parse_bindings()
        bindings101 = _t568
        _t569 = self.parse_formula()
        formula102 = _t569
        self.consume_literal(')')
        _t570 = logic_pb2.Abstraction(vars=(bindings101[0] + (bindings101[1] if bindings101[1] is not None else [])), value=formula102)
        _t571 = logic_pb2.Exists(body=_t570)
        return _t571

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal('(')
        self.consume_literal('reduce')
        _t572 = self.parse_abstraction()
        abstraction103 = _t572
        _t573 = self.parse_abstraction()
        abstraction_3104 = _t573
        _t574 = self.parse_terms()
        terms105 = _t574
        self.consume_literal(')')
        _t575 = logic_pb2.Reduce(op=abstraction103, body=abstraction_3104, terms=terms105)
        return _t575

    def parse_terms(self) -> list[logic_pb2.Term]:
        self.consume_literal('(')
        self.consume_literal('terms')
        xs106 = []
        cond107 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond107:
            _t576 = self.parse_term()
            xs106.append(_t576)
            cond107 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms108 = xs106
        self.consume_literal(')')
        return terms108

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_literal('true', 0):
            _t608 = 1
        else:
            if self.match_lookahead_literal('missing', 0):
                _t624 = 1
            else:
                if self.match_lookahead_literal('false', 0):
                    _t632 = 1
                else:
                    if self.match_lookahead_literal('(', 0):
                        _t636 = 1
                    else:
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t638 = 1
                        else:
                            if self.match_lookahead_terminal('SYMBOL', 0):
                                _t639 = 0
                            else:
                                _t639 = (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or -1)))))
                            _t638 = _t639
                        _t636 = _t638
                    _t632 = _t636
                _t624 = _t632
            _t608 = _t624
        prediction109 = _t608
        if prediction109 == 1:
            _t641 = self.parse_constant()
            constant111 = _t641
            _t642 = logic_pb2.Term(constant=constant111)
            _t640 = _t642
        else:
            if prediction109 == 0:
                _t644 = self.parse_var()
                var110 = _t644
                _t645 = logic_pb2.Term(var=var110)
                _t643 = _t645
            else:
                raise ParseError(f"{'Unexpected token in term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t643 = None
            _t640 = _t643
        return _t640

    def parse_var(self) -> logic_pb2.Var:
        symbol112 = self.consume_terminal('SYMBOL')
        _t646 = logic_pb2.Var(name=symbol112)
        return _t646

    def parse_constant(self) -> logic_pb2.Value:
        _t647 = self.parse_value()
        value113 = _t647
        return value113

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('and')
        xs114 = []
        cond115 = self.match_lookahead_literal('(', 0)
        while cond115:
            _t648 = self.parse_formula()
            xs114.append(_t648)
            cond115 = self.match_lookahead_literal('(', 0)
        formulas116 = xs114
        self.consume_literal(')')
        _t649 = logic_pb2.Conjunction(args=formulas116)
        return _t649

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('or')
        xs117 = []
        cond118 = self.match_lookahead_literal('(', 0)
        while cond118:
            _t650 = self.parse_formula()
            xs117.append(_t650)
            cond118 = self.match_lookahead_literal('(', 0)
        formulas119 = xs117
        self.consume_literal(')')
        _t651 = logic_pb2.Disjunction(args=formulas119)
        return _t651

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal('(')
        self.consume_literal('not')
        _t652 = self.parse_formula()
        formula120 = _t652
        self.consume_literal(')')
        _t653 = logic_pb2.Not(arg=formula120)
        return _t653

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal('(')
        self.consume_literal('ffi')
        _t654 = self.parse_name()
        name121 = _t654
        _t655 = self.parse_ffi_args()
        ffi_args122 = _t655
        _t656 = self.parse_terms()
        terms123 = _t656
        self.consume_literal(')')
        _t657 = logic_pb2.FFI(name=name121, args=ffi_args122, terms=terms123)
        return _t657

    def parse_name(self) -> str:
        self.consume_literal(':')
        symbol124 = self.consume_terminal('SYMBOL')
        return symbol124

    def parse_ffi_args(self) -> list[logic_pb2.Abstraction]:
        self.consume_literal('(')
        self.consume_literal('args')
        xs125 = []
        cond126 = self.match_lookahead_literal('(', 0)
        while cond126:
            _t658 = self.parse_abstraction()
            xs125.append(_t658)
            cond126 = self.match_lookahead_literal('(', 0)
        abstractions127 = xs125
        self.consume_literal(')')
        return abstractions127

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal('(')
        self.consume_literal('atom')
        _t659 = self.parse_relation_id()
        relation_id128 = _t659
        xs129 = []
        cond130 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond130:
            _t660 = self.parse_term()
            xs129.append(_t660)
            cond130 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms131 = xs129
        self.consume_literal(')')
        _t661 = logic_pb2.Atom(name=relation_id128, terms=terms131)
        return _t661

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal('(')
        self.consume_literal('pragma')
        _t662 = self.parse_name()
        name132 = _t662
        xs133 = []
        cond134 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond134:
            _t663 = self.parse_term()
            xs133.append(_t663)
            cond134 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms135 = xs133
        self.consume_literal(')')
        _t664 = logic_pb2.Pragma(name=name132, terms=terms135)
        return _t664

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('primitive', 1):
                _t666 = 9
            else:
                if self.match_lookahead_literal('>=', 1):
                    _t667 = 4
                else:
                    if self.match_lookahead_literal('>', 1):
                        _t668 = 3
                    else:
                        if self.match_lookahead_literal('=', 1):
                            _t669 = 0
                        else:
                            if self.match_lookahead_literal('<=', 1):
                                _t670 = 2
                            else:
                                if self.match_lookahead_literal('<', 1):
                                    _t675 = 1
                                else:
                                    if self.match_lookahead_literal('/', 1):
                                        _t676 = 8
                                    else:
                                        if self.match_lookahead_literal('-', 1):
                                            _t677 = 6
                                        else:
                                            if self.match_lookahead_literal('+', 1):
                                                _t678 = 5
                                            else:
                                                if self.match_lookahead_literal('*', 1):
                                                    _t679 = 7
                                                else:
                                                    _t679 = -1
                                                _t678 = _t679
                                            _t677 = _t678
                                        _t676 = _t677
                                    _t675 = _t676
                                _t670 = _t675
                            _t669 = _t670
                        _t668 = _t669
                    _t667 = _t668
                _t666 = _t667
            _t665 = _t666
        else:
            _t665 = -1
        prediction136 = _t665
        if prediction136 == 9:
            self.consume_literal('(')
            self.consume_literal('primitive')
            _t681 = self.parse_name()
            name146 = _t681
            xs147 = []
            cond148 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            while cond148:
                _t682 = self.parse_rel_term()
                xs147.append(_t682)
                cond148 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            rel_terms149 = xs147
            self.consume_literal(')')
            _t683 = logic_pb2.Primitive(name=name146, terms=rel_terms149)
            _t680 = _t683
        else:
            if prediction136 == 8:
                _t685 = self.parse_divide()
                divide145 = _t685
                _t684 = divide145
            else:
                if prediction136 == 7:
                    _t687 = self.parse_multiply()
                    multiply144 = _t687
                    _t686 = multiply144
                else:
                    if prediction136 == 6:
                        _t689 = self.parse_minus()
                        minus143 = _t689
                        _t688 = minus143
                    else:
                        if prediction136 == 5:
                            _t691 = self.parse_add()
                            add142 = _t691
                            _t690 = add142
                        else:
                            if prediction136 == 4:
                                _t693 = self.parse_gt_eq()
                                gt_eq141 = _t693
                                _t692 = gt_eq141
                            else:
                                if prediction136 == 3:
                                    _t695 = self.parse_gt()
                                    gt140 = _t695
                                    _t694 = gt140
                                else:
                                    if prediction136 == 2:
                                        _t697 = self.parse_lt_eq()
                                        lt_eq139 = _t697
                                        _t696 = lt_eq139
                                    else:
                                        if prediction136 == 1:
                                            _t699 = self.parse_lt()
                                            lt138 = _t699
                                            _t698 = lt138
                                        else:
                                            if prediction136 == 0:
                                                _t701 = self.parse_eq()
                                                eq137 = _t701
                                                _t700 = eq137
                                            else:
                                                raise ParseError(f"{'Unexpected token in primitive'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t700 = None
                                            _t698 = _t700
                                        _t696 = _t698
                                    _t694 = _t696
                                _t692 = _t694
                            _t690 = _t692
                        _t688 = _t690
                    _t686 = _t688
                _t684 = _t686
            _t680 = _t684
        return _t680

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('=')
        _t702 = self.parse_term()
        term150 = _t702
        _t703 = self.parse_term()
        term_3151 = _t703
        self.consume_literal(')')
        _t704 = logic_pb2.RelTerm(term=term150)
        _t705 = logic_pb2.RelTerm(term=term_3151)
        _t706 = logic_pb2.Primitive(name='rel_primitive_eq', terms=[_t704, _t705])
        return _t706

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<')
        _t707 = self.parse_term()
        term152 = _t707
        _t708 = self.parse_term()
        term_3153 = _t708
        self.consume_literal(')')
        _t709 = logic_pb2.RelTerm(term=term152)
        _t710 = logic_pb2.RelTerm(term=term_3153)
        _t711 = logic_pb2.Primitive(name='rel_primitive_lt_monotype', terms=[_t709, _t710])
        return _t711

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<=')
        _t712 = self.parse_term()
        term154 = _t712
        _t713 = self.parse_term()
        term_3155 = _t713
        self.consume_literal(')')
        _t714 = logic_pb2.RelTerm(term=term154)
        _t715 = logic_pb2.RelTerm(term=term_3155)
        _t716 = logic_pb2.Primitive(name='rel_primitive_lt_eq_monotype', terms=[_t714, _t715])
        return _t716

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>')
        _t717 = self.parse_term()
        term156 = _t717
        _t718 = self.parse_term()
        term_3157 = _t718
        self.consume_literal(')')
        _t719 = logic_pb2.RelTerm(term=term156)
        _t720 = logic_pb2.RelTerm(term=term_3157)
        _t721 = logic_pb2.Primitive(name='rel_primitive_gt_monotype', terms=[_t719, _t720])
        return _t721

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>=')
        _t722 = self.parse_term()
        term158 = _t722
        _t723 = self.parse_term()
        term_3159 = _t723
        self.consume_literal(')')
        _t724 = logic_pb2.RelTerm(term=term158)
        _t725 = logic_pb2.RelTerm(term=term_3159)
        _t726 = logic_pb2.Primitive(name='rel_primitive_gt_eq_monotype', terms=[_t724, _t725])
        return _t726

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('+')
        _t727 = self.parse_term()
        term160 = _t727
        _t728 = self.parse_term()
        term_3161 = _t728
        _t729 = self.parse_term()
        term_4162 = _t729
        self.consume_literal(')')
        _t730 = logic_pb2.RelTerm(term=term160)
        _t731 = logic_pb2.RelTerm(term=term_3161)
        _t732 = logic_pb2.RelTerm(term=term_4162)
        _t733 = logic_pb2.Primitive(name='rel_primitive_add_monotype', terms=[_t730, _t731, _t732])
        return _t733

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('-')
        _t734 = self.parse_term()
        term163 = _t734
        _t735 = self.parse_term()
        term_3164 = _t735
        _t736 = self.parse_term()
        term_4165 = _t736
        self.consume_literal(')')
        _t737 = logic_pb2.RelTerm(term=term163)
        _t738 = logic_pb2.RelTerm(term=term_3164)
        _t739 = logic_pb2.RelTerm(term=term_4165)
        _t740 = logic_pb2.Primitive(name='rel_primitive_subtract_monotype', terms=[_t737, _t738, _t739])
        return _t740

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('*')
        _t741 = self.parse_term()
        term166 = _t741
        _t742 = self.parse_term()
        term_3167 = _t742
        _t743 = self.parse_term()
        term_4168 = _t743
        self.consume_literal(')')
        _t744 = logic_pb2.RelTerm(term=term166)
        _t745 = logic_pb2.RelTerm(term=term_3167)
        _t746 = logic_pb2.RelTerm(term=term_4168)
        _t747 = logic_pb2.Primitive(name='rel_primitive_multiply_monotype', terms=[_t744, _t745, _t746])
        return _t747

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('/')
        _t748 = self.parse_term()
        term169 = _t748
        _t749 = self.parse_term()
        term_3170 = _t749
        _t750 = self.parse_term()
        term_4171 = _t750
        self.consume_literal(')')
        _t751 = logic_pb2.RelTerm(term=term169)
        _t752 = logic_pb2.RelTerm(term=term_3170)
        _t753 = logic_pb2.RelTerm(term=term_4171)
        _t754 = logic_pb2.Primitive(name='rel_primitive_divide_monotype', terms=[_t751, _t752, _t753])
        return _t754

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_literal('true', 0):
            _t770 = 1
        else:
            if self.match_lookahead_literal('missing', 0):
                _t778 = 1
            else:
                if self.match_lookahead_literal('false', 0):
                    _t782 = 1
                else:
                    if self.match_lookahead_literal('(', 0):
                        _t784 = 1
                    else:
                        if self.match_lookahead_literal('#', 0):
                            _t785 = 0
                        else:
                            _t785 = (self.match_lookahead_terminal('UINT128', 0) or (self.match_lookahead_terminal('SYMBOL', 0) or (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or -1)))))))
                        _t784 = _t785
                    _t782 = _t784
                _t778 = _t782
            _t770 = _t778
        prediction172 = _t770
        if prediction172 == 1:
            _t787 = self.parse_term()
            term174 = _t787
            _t788 = logic_pb2.RelTerm(term=term174)
            _t786 = _t788
        else:
            if prediction172 == 0:
                _t790 = self.parse_specialized_value()
                specialized_value173 = _t790
                _t791 = logic_pb2.RelTerm(specialized_value=specialized_value173)
                _t789 = _t791
            else:
                raise ParseError(f"{'Unexpected token in rel_term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t789 = None
            _t786 = _t789
        return _t786

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal('#')
        _t792 = self.parse_value()
        value175 = _t792
        return value175

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        self.consume_literal('(')
        self.consume_literal('relatom')
        _t793 = self.parse_name()
        name176 = _t793
        xs177 = []
        cond178 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond178:
            _t794 = self.parse_rel_term()
            xs177.append(_t794)
            cond178 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        rel_terms179 = xs177
        self.consume_literal(')')
        _t795 = logic_pb2.RelAtom(name=name176, terms=rel_terms179)
        return _t795

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal('(')
        self.consume_literal('cast')
        _t796 = self.parse_term()
        term180 = _t796
        _t797 = self.parse_term()
        term_3181 = _t797
        self.consume_literal(')')
        _t798 = logic_pb2.Cast(input=term180, result=term_3181)
        return _t798

    def parse_attrs(self) -> list[logic_pb2.Attribute]:
        self.consume_literal('(')
        self.consume_literal('attrs')
        xs182 = []
        cond183 = self.match_lookahead_literal('(', 0)
        while cond183:
            _t799 = self.parse_attribute()
            xs182.append(_t799)
            cond183 = self.match_lookahead_literal('(', 0)
        attributes184 = xs182
        self.consume_literal(')')
        return attributes184

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal('(')
        self.consume_literal('attribute')
        _t800 = self.parse_name()
        name185 = _t800
        xs186 = []
        cond187 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond187:
            _t801 = self.parse_value()
            xs186.append(_t801)
            cond187 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        values188 = xs186
        self.consume_literal(')')
        _t802 = logic_pb2.Attribute(name=name185, args=values188)
        return _t802

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal('(')
        self.consume_literal('algorithm')
        xs189 = []
        cond190 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        while cond190:
            _t803 = self.parse_relation_id()
            xs189.append(_t803)
            cond190 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        relation_ids191 = xs189
        _t804 = self.parse_script()
        script192 = _t804
        self.consume_literal(')')
        _t805 = logic_pb2.Algorithm(body=script192)
        getattr(_t805, 'global').extend(relation_ids191)
        return _t805

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal('(')
        self.consume_literal('script')
        xs193 = []
        cond194 = self.match_lookahead_literal('(', 0)
        while cond194:
            _t806 = self.parse_construct()
            xs193.append(_t806)
            cond194 = self.match_lookahead_literal('(', 0)
        constructs195 = xs193
        self.consume_literal(')')
        _t807 = logic_pb2.Script(constructs=constructs195)
        return _t807

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t816 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t820 = 1
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t822 = 1
                    else:
                        if self.match_lookahead_literal('loop', 1):
                            _t823 = 0
                        else:
                            _t823 = (self.match_lookahead_literal('break', 1) or (self.match_lookahead_literal('assign', 1) or -1))
                        _t822 = _t823
                    _t820 = _t822
                _t816 = _t820
            _t808 = _t816
        else:
            _t808 = -1
        prediction196 = _t808
        if prediction196 == 1:
            _t825 = self.parse_instruction()
            instruction198 = _t825
            _t826 = logic_pb2.Construct(instruction=instruction198)
            _t824 = _t826
        else:
            if prediction196 == 0:
                _t828 = self.parse_loop()
                loop197 = _t828
                _t829 = logic_pb2.Construct(loop=loop197)
                _t827 = _t829
            else:
                raise ParseError(f"{'Unexpected token in construct'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t827 = None
            _t824 = _t827
        return _t824

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal('(')
        self.consume_literal('loop')
        _t830 = self.parse_init()
        init199 = _t830
        _t831 = self.parse_script()
        script200 = _t831
        self.consume_literal(')')
        _t832 = logic_pb2.Loop(init=init199, body=script200)
        return _t832

    def parse_init(self) -> list[logic_pb2.Instruction]:
        self.consume_literal('(')
        self.consume_literal('init')
        xs201 = []
        cond202 = self.match_lookahead_literal('(', 0)
        while cond202:
            _t833 = self.parse_instruction()
            xs201.append(_t833)
            cond202 = self.match_lookahead_literal('(', 0)
        instructions203 = xs201
        self.consume_literal(')')
        return instructions203

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t839 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t840 = 4
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t841 = 3
                    else:
                        if self.match_lookahead_literal('break', 1):
                            _t842 = 2
                        else:
                            if self.match_lookahead_literal('assign', 1):
                                _t843 = 0
                            else:
                                _t843 = -1
                            _t842 = _t843
                        _t841 = _t842
                    _t840 = _t841
                _t839 = _t840
            _t834 = _t839
        else:
            _t834 = -1
        prediction204 = _t834
        if prediction204 == 4:
            _t845 = self.parse_monus_def()
            monus_def209 = _t845
            _t846 = logic_pb2.Instruction(monus_def=monus_def209)
            _t844 = _t846
        else:
            if prediction204 == 3:
                _t848 = self.parse_monoid_def()
                monoid_def208 = _t848
                _t849 = logic_pb2.Instruction(monoid_def=monoid_def208)
                _t847 = _t849
            else:
                if prediction204 == 2:
                    _t851 = self.parse_break()
                    break207 = _t851
                    _t852 = logic_pb2.Instruction()
                    getattr(_t852, 'break').CopyFrom(break207)
                    _t850 = _t852
                else:
                    if prediction204 == 1:
                        _t854 = self.parse_upsert()
                        upsert206 = _t854
                        _t855 = logic_pb2.Instruction(upsert=upsert206)
                        _t853 = _t855
                    else:
                        if prediction204 == 0:
                            _t857 = self.parse_assign()
                            assign205 = _t857
                            _t858 = logic_pb2.Instruction(assign=assign205)
                            _t856 = _t858
                        else:
                            raise ParseError(f"{'Unexpected token in instruction'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t856 = None
                        _t853 = _t856
                    _t850 = _t853
                _t847 = _t850
            _t844 = _t847
        return _t844

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal('(')
        self.consume_literal('assign')
        _t859 = self.parse_relation_id()
        relation_id210 = _t859
        _t860 = self.parse_abstraction()
        abstraction211 = _t860
        if self.match_lookahead_literal('(', 0):
            _t862 = self.parse_attrs()
            _t861 = _t862
        else:
            _t861 = None
        attrs212 = _t861
        self.consume_literal(')')
        _t863 = logic_pb2.Assign(name=relation_id210, body=abstraction211, attrs=(attrs212 if attrs212 is not None else []))
        return _t863

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal('(')
        self.consume_literal('upsert')
        _t864 = self.parse_relation_id()
        relation_id213 = _t864
        _t865 = self.parse_abstraction_with_arity()
        abstraction_with_arity214 = _t865
        if self.match_lookahead_literal('(', 0):
            _t867 = self.parse_attrs()
            _t866 = _t867
        else:
            _t866 = None
        attrs215 = _t866
        self.consume_literal(')')
        _t868 = logic_pb2.Upsert(name=relation_id213, body=abstraction_with_arity214[0], attrs=(attrs215 if attrs215 is not None else []), value_arity=abstraction_with_arity214[1])
        return _t868

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal('(')
        _t869 = self.parse_bindings()
        bindings216 = _t869
        _t870 = self.parse_formula()
        formula217 = _t870
        self.consume_literal(')')
        _t871 = logic_pb2.Abstraction(vars=(bindings216[0] + (bindings216[1] if bindings216[1] is not None else [])), value=formula217)
        return (_t871, len(bindings216[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal('(')
        self.consume_literal('break')
        _t872 = self.parse_relation_id()
        relation_id218 = _t872
        _t873 = self.parse_abstraction()
        abstraction219 = _t873
        if self.match_lookahead_literal('(', 0):
            _t875 = self.parse_attrs()
            _t874 = _t875
        else:
            _t874 = None
        attrs220 = _t874
        self.consume_literal(')')
        _t876 = logic_pb2.Break(name=relation_id218, body=abstraction219, attrs=(attrs220 if attrs220 is not None else []))
        return _t876

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal('(')
        self.consume_literal('monoid')
        _t877 = self.parse_monoid()
        monoid221 = _t877
        _t878 = self.parse_relation_id()
        relation_id222 = _t878
        _t879 = self.parse_abstraction_with_arity()
        abstraction_with_arity223 = _t879
        if self.match_lookahead_literal('(', 0):
            _t881 = self.parse_attrs()
            _t880 = _t881
        else:
            _t880 = None
        attrs224 = _t880
        self.consume_literal(')')
        _t882 = logic_pb2.MonoidDef(monoid=monoid221, name=relation_id222, body=abstraction_with_arity223[0], attrs=(attrs224 if attrs224 is not None else []), value_arity=abstraction_with_arity223[1])
        return _t882

    def parse_monoid(self) -> logic_pb2.Monoid:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('sum', 1):
                _t884 = 3
            else:
                if self.match_lookahead_literal('or', 1):
                    _t885 = 0
                else:
                    if self.match_lookahead_literal('min', 1):
                        _t887 = 1
                    else:
                        if self.match_lookahead_literal('max', 1):
                            _t888 = 2
                        else:
                            _t888 = -1
                        _t887 = _t888
                    _t885 = _t887
                _t884 = _t885
            _t883 = _t884
        else:
            _t883 = -1
        prediction225 = _t883
        if prediction225 == 3:
            _t890 = self.parse_sum_monoid()
            sum_monoid229 = _t890
            _t891 = logic_pb2.Monoid(sum_monoid=sum_monoid229)
            _t889 = _t891
        else:
            if prediction225 == 2:
                _t893 = self.parse_max_monoid()
                max_monoid228 = _t893
                _t894 = logic_pb2.Monoid(max_monoid=max_monoid228)
                _t892 = _t894
            else:
                if prediction225 == 1:
                    _t896 = self.parse_min_monoid()
                    min_monoid227 = _t896
                    _t897 = logic_pb2.Monoid(min_monoid=min_monoid227)
                    _t895 = _t897
                else:
                    if prediction225 == 0:
                        _t899 = self.parse_or_monoid()
                        or_monoid226 = _t899
                        _t900 = logic_pb2.Monoid(or_monoid=or_monoid226)
                        _t898 = _t900
                    else:
                        raise ParseError(f"{'Unexpected token in monoid'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t898 = None
                    _t895 = _t898
                _t892 = _t895
            _t889 = _t892
        return _t889

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        self.consume_literal('(')
        self.consume_literal('or')
        self.consume_literal(')')
        return logic_pb2.OrMonoid()

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        self.consume_literal('(')
        self.consume_literal('min')
        _t901 = self.parse_type()
        type230 = _t901
        self.consume_literal(')')
        _t902 = logic_pb2.MinMonoid(type=type230)
        return _t902

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        self.consume_literal('(')
        self.consume_literal('max')
        _t903 = self.parse_type()
        type231 = _t903
        self.consume_literal(')')
        _t904 = logic_pb2.MaxMonoid(type=type231)
        return _t904

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        self.consume_literal('(')
        self.consume_literal('sum')
        _t905 = self.parse_type()
        type232 = _t905
        self.consume_literal(')')
        _t906 = logic_pb2.SumMonoid(type=type232)
        return _t906

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal('(')
        self.consume_literal('monus')
        _t907 = self.parse_monoid()
        monoid233 = _t907
        _t908 = self.parse_relation_id()
        relation_id234 = _t908
        _t909 = self.parse_abstraction_with_arity()
        abstraction_with_arity235 = _t909
        if self.match_lookahead_literal('(', 0):
            _t911 = self.parse_attrs()
            _t910 = _t911
        else:
            _t910 = None
        attrs236 = _t910
        self.consume_literal(')')
        _t912 = logic_pb2.MonusDef(monoid=monoid233, name=relation_id234, body=abstraction_with_arity235[0], attrs=(attrs236 if attrs236 is not None else []), value_arity=abstraction_with_arity235[1])
        return _t912

    def parse_constraint(self) -> logic_pb2.Constraint:
        self.consume_literal('(')
        self.consume_literal('functional_dependency')
        _t913 = self.parse_relation_id()
        relation_id237 = _t913
        _t914 = self.parse_abstraction()
        abstraction238 = _t914
        _t915 = self.parse_functional_dependency_keys()
        functional_dependency_keys239 = _t915
        _t916 = self.parse_functional_dependency_values()
        functional_dependency_values240 = _t916
        self.consume_literal(')')
        _t917 = logic_pb2.FunctionalDependency(guard=abstraction238, keys=functional_dependency_keys239, values=functional_dependency_values240)
        _t918 = logic_pb2.Constraint(name=relation_id237, functional_dependency=_t917)
        return _t918

    def parse_functional_dependency_keys(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('keys')
        xs241 = []
        cond242 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond242:
            _t919 = self.parse_var()
            xs241.append(_t919)
            cond242 = self.match_lookahead_terminal('SYMBOL', 0)
        vars243 = xs241
        self.consume_literal(')')
        return vars243

    def parse_functional_dependency_values(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('values')
        xs244 = []
        cond245 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond245:
            _t920 = self.parse_var()
            xs244.append(_t920)
            cond245 = self.match_lookahead_terminal('SYMBOL', 0)
        vars246 = xs244
        self.consume_literal(')')
        return vars246

    def parse_data(self) -> logic_pb2.Data:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('rel_edb', 1):
                _t922 = 0
            else:
                if self.match_lookahead_literal('csv_data', 1):
                    _t923 = 2
                else:
                    _t923 = (self.match_lookahead_literal('betree_relation', 1) or -1)
                _t922 = _t923
            _t921 = _t922
        else:
            _t921 = -1
        prediction247 = _t921
        if prediction247 == 2:
            _t925 = self.parse_csv_data()
            csv_data250 = _t925
            _t926 = logic_pb2.Data(csv_data=csv_data250)
            _t924 = _t926
        else:
            if prediction247 == 1:
                _t928 = self.parse_betree_relation()
                betree_relation249 = _t928
                _t929 = logic_pb2.Data(betree_relation=betree_relation249)
                _t927 = _t929
            else:
                if prediction247 == 0:
                    _t931 = self.parse_rel_edb()
                    rel_edb248 = _t931
                    _t932 = logic_pb2.Data(rel_edb=rel_edb248)
                    _t930 = _t932
                else:
                    raise ParseError(f"{'Unexpected token in data'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t930 = None
                _t927 = _t930
            _t924 = _t927
        return _t924

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        self.consume_literal('(')
        self.consume_literal('rel_edb')
        _t933 = self.parse_relation_id()
        relation_id251 = _t933
        _t934 = self.parse_rel_edb_path()
        rel_edb_path252 = _t934
        if self.match_lookahead_literal('[', 0):
            _t936 = self.parse_rel_edb_types()
            _t935 = _t936
        else:
            _t935 = None
        rel_edb_types253 = _t935
        self.consume_literal(')')
        _t937 = logic_pb2.RelEDB(target_id=relation_id251, path=rel_edb_path252, types=(rel_edb_types253 if rel_edb_types253 is not None else []))
        return _t937

    def parse_rel_edb_path(self) -> list[str]:
        self.consume_literal('[')
        xs254 = []
        cond255 = self.match_lookahead_terminal('STRING', 0)
        while cond255:
            xs254.append(self.consume_terminal('STRING'))
            cond255 = self.match_lookahead_terminal('STRING', 0)
        strings256 = xs254
        self.consume_literal(']')
        return strings256

    def parse_rel_edb_types(self) -> list[logic_pb2.Type]:
        self.consume_literal('[')
        xs257 = []
        cond258 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond258:
            _t938 = self.parse_type()
            xs257.append(_t938)
            cond258 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types259 = xs257
        self.consume_literal(']')
        return types259

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        _t939 = self.parse_be_tree_relation()
        be_tree_relation260 = _t939
        return be_tree_relation260

    def parse_be_tree_relation(self) -> logic_pb2.BeTreeRelation:
        self.consume_literal('(')
        self.consume_literal('betree_relation')
        _t940 = self.parse_relation_id()
        relation_id261 = _t940
        _t941 = self.parse_be_tree_info()
        be_tree_info262 = _t941
        self.consume_literal(')')
        _t942 = logic_pb2.BeTreeRelation(name=relation_id261, relation_info=be_tree_info262)
        return _t942

    def parse_be_tree_info(self) -> logic_pb2.BeTreeInfo:
        self.consume_literal('(')
        self.consume_literal('betree_info')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('key_types', 1)):
            _t944 = self.parse_be_tree_info_key_types()
            _t943 = _t944
        else:
            _t943 = None
        be_tree_info_key_types263 = _t943
        if self.match_lookahead_literal('(', 0):
            _t946 = self.parse_be_tree_info_value_types()
            _t945 = _t946
        else:
            _t945 = None
        be_tree_info_value_types264 = _t945
        _t947 = self.parse_config_dict()
        config_dict265 = _t947
        self.consume_literal(')')
        return self.construct_betree_info((be_tree_info_key_types263 if be_tree_info_key_types263 is not None else []), (be_tree_info_value_types264 if be_tree_info_value_types264 is not None else []), config_dict265)

    def parse_be_tree_info_key_types(self) -> list[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('key_types')
        xs266 = []
        cond267 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond267:
            _t948 = self.parse_type()
            xs266.append(_t948)
            cond267 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types268 = xs266
        self.consume_literal(')')
        return types268

    def parse_be_tree_info_value_types(self) -> list[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('value_types')
        xs269 = []
        cond270 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond270:
            _t949 = self.parse_type()
            xs269.append(_t949)
            cond270 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types271 = xs269
        self.consume_literal(')')
        return types271

    def parse_csv_data(self) -> logic_pb2.CSVData:
        _t950 = self.parse_csvdata()
        csvdata272 = _t950
        return csvdata272

    def parse_csvdata(self) -> logic_pb2.CSVData:
        self.consume_literal('(')
        self.consume_literal('csv_data')
        _t951 = self.parse_csvlocator()
        csvlocator273 = _t951
        _t952 = self.parse_csv_config()
        csv_config274 = _t952
        _t953 = self.parse_csv_columns()
        csv_columns275 = _t953
        _t954 = self.parse_csv_asof()
        csv_asof276 = _t954
        self.consume_literal(')')
        _t955 = logic_pb2.CSVData(locator=csvlocator273, config=csv_config274, columns=csv_columns275, asof=csv_asof276)
        return _t955

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        self.consume_literal('(')
        self.consume_literal('csv_locator')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('paths', 1)):
            _t957 = self.parse_csv_locator_paths()
            _t956 = _t957
        else:
            _t956 = None
        csv_locator_paths277 = _t956
        if self.match_lookahead_literal('(', 0):
            _t959 = self.parse_csv_locator_inline_data()
            _t958 = _t959
        else:
            _t958 = None
        csv_locator_inline_data278 = _t958
        self.consume_literal(')')
        _t960 = logic_pb2.CSVLocator(paths=(csv_locator_paths277 if csv_locator_paths277 is not None else []), inline_data=(csv_locator_inline_data278 if csv_locator_inline_data278 is not None else '').encode())
        return _t960

    def parse_csv_locator_paths(self) -> list[str]:
        self.consume_literal('(')
        self.consume_literal('paths')
        xs279 = []
        cond280 = self.match_lookahead_terminal('STRING', 0)
        while cond280:
            xs279.append(self.consume_terminal('STRING'))
            cond280 = self.match_lookahead_terminal('STRING', 0)
        strings281 = xs279
        self.consume_literal(')')
        return strings281

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal('(')
        self.consume_literal('inline_data')
        string282 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return string282

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        self.consume_literal('(')
        self.consume_literal('csv_config')
        _t961 = self.parse_config_dict()
        config_dict283 = _t961
        self.consume_literal(')')
        return self.construct_csv_config(config_dict283)

    def parse_csv_columns(self) -> list[logic_pb2.CSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs284 = []
        cond285 = self.match_lookahead_literal('(', 0)
        while cond285:
            _t962 = self.parse_csv_column()
            xs284.append(_t962)
            cond285 = self.match_lookahead_literal('(', 0)
        csv_columns286 = xs284
        self.consume_literal(')')
        return csv_columns286

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        string287 = self.consume_terminal('STRING')
        _t963 = self.parse_relation_id()
        relation_id288 = _t963
        self.consume_literal('[')
        xs289 = []
        cond290 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond290:
            _t964 = self.parse_type()
            xs289.append(_t964)
            cond290 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types291 = xs289
        self.consume_literal(']')
        self.consume_literal(')')
        _t965 = logic_pb2.CSVColumn(column_name=string287, target_id=relation_id288, types=types291)
        return _t965

    def parse_csv_asof(self) -> str:
        self.consume_literal('(')
        self.consume_literal('asof')
        string292 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return string292

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal('(')
        self.consume_literal('undefine')
        _t966 = self.parse_fragment_id()
        fragment_id293 = _t966
        self.consume_literal(')')
        _t967 = transactions_pb2.Undefine(fragment_id=fragment_id293)
        return _t967

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal('(')
        self.consume_literal('context')
        xs294 = []
        cond295 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        while cond295:
            _t968 = self.parse_relation_id()
            xs294.append(_t968)
            cond295 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        relation_ids296 = xs294
        self.consume_literal(')')
        _t969 = transactions_pb2.Context(relations=relation_ids296)
        return _t969

    def parse_epoch_reads(self) -> list[transactions_pb2.Read]:
        self.consume_literal('(')
        self.consume_literal('reads')
        xs297 = []
        cond298 = self.match_lookahead_literal('(', 0)
        while cond298:
            _t970 = self.parse_read()
            xs297.append(_t970)
            cond298 = self.match_lookahead_literal('(', 0)
        reads299 = xs297
        self.consume_literal(')')
        return reads299

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('what_if', 1):
                _t972 = 2
            else:
                if self.match_lookahead_literal('output', 1):
                    _t976 = 1
                else:
                    if self.match_lookahead_literal('export', 1):
                        _t977 = 4
                    else:
                        if self.match_lookahead_literal('demand', 1):
                            _t978 = 0
                        else:
                            if self.match_lookahead_literal('abort', 1):
                                _t979 = 3
                            else:
                                _t979 = -1
                            _t978 = _t979
                        _t977 = _t978
                    _t976 = _t977
                _t972 = _t976
            _t971 = _t972
        else:
            _t971 = -1
        prediction300 = _t971
        if prediction300 == 4:
            _t981 = self.parse_export()
            export305 = _t981
            _t982 = transactions_pb2.Read(export=export305)
            _t980 = _t982
        else:
            if prediction300 == 3:
                _t984 = self.parse_abort()
                abort304 = _t984
                _t985 = transactions_pb2.Read(abort=abort304)
                _t983 = _t985
            else:
                if prediction300 == 2:
                    _t987 = self.parse_what_if()
                    what_if303 = _t987
                    _t988 = transactions_pb2.Read(what_if=what_if303)
                    _t986 = _t988
                else:
                    if prediction300 == 1:
                        _t990 = self.parse_output()
                        output302 = _t990
                        _t991 = transactions_pb2.Read(output=output302)
                        _t989 = _t991
                    else:
                        if prediction300 == 0:
                            _t993 = self.parse_demand()
                            demand301 = _t993
                            _t994 = transactions_pb2.Read(demand=demand301)
                            _t992 = _t994
                        else:
                            raise ParseError(f"{'Unexpected token in read'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t992 = None
                        _t989 = _t992
                    _t986 = _t989
                _t983 = _t986
            _t980 = _t983
        return _t980

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal('(')
        self.consume_literal('demand')
        _t995 = self.parse_relation_id()
        relation_id306 = _t995
        self.consume_literal(')')
        _t996 = transactions_pb2.Demand(relation_id=relation_id306)
        return _t996

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal('(')
        self.consume_literal('output')
        if (self.match_lookahead_literal(':', 0) and self.match_lookahead_terminal('SYMBOL', 1)):
            _t998 = self.parse_name()
            _t997 = _t998
        else:
            _t997 = None
        name307 = _t997
        _t999 = self.parse_relation_id()
        relation_id308 = _t999
        self.consume_literal(')')
        _t1000 = transactions_pb2.Output(name=(name307 if name307 is not None else 'output'), relation_id=relation_id308)
        return _t1000

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal('(')
        self.consume_literal('what_if')
        _t1001 = self.parse_name()
        name309 = _t1001
        _t1002 = self.parse_epoch()
        epoch310 = _t1002
        self.consume_literal(')')
        _t1003 = transactions_pb2.WhatIf(branch=name309, epoch=epoch310)
        return _t1003

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal('(')
        self.consume_literal('abort')
        if (self.match_lookahead_literal(':', 0) and self.match_lookahead_terminal('SYMBOL', 1)):
            _t1005 = self.parse_name()
            _t1004 = _t1005
        else:
            _t1004 = None
        name311 = _t1004
        _t1006 = self.parse_relation_id()
        relation_id312 = _t1006
        self.consume_literal(')')
        _t1007 = transactions_pb2.Abort(name=(name311 if name311 is not None else 'abort'), relation_id=relation_id312)
        return _t1007

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal('(')
        self.consume_literal('export')
        _t1008 = self.parse_export_csv_config()
        export_csv_config313 = _t1008
        self.consume_literal(')')
        _t1009 = transactions_pb2.Export(csv_config=export_csv_config313)
        return _t1009

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal('(')
        self.consume_literal('export_csv_config')
        _t1010 = self.parse_export_csv_path()
        export_csv_path314 = _t1010
        _t1011 = self.parse_export_csv_columns()
        export_csv_columns315 = _t1011
        _t1012 = self.parse_config_dict()
        config_dict316 = _t1012
        self.consume_literal(')')
        _t1013 = self.export_csv_config(export_csv_path314, export_csv_columns315, config_dict316)
        return _t1013

    def parse_export_csv_path(self) -> str:
        self.consume_literal('(')
        self.consume_literal('path')
        string317 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return string317

    def parse_export_csv_columns(self) -> list[transactions_pb2.ExportCSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs318 = []
        cond319 = self.match_lookahead_literal('(', 0)
        while cond319:
            _t1014 = self.parse_export_csv_column()
            xs318.append(_t1014)
            cond319 = self.match_lookahead_literal('(', 0)
        export_csv_columns320 = xs318
        self.consume_literal(')')
        return export_csv_columns320

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        string321 = self.consume_terminal('STRING')
        _t1015 = self.parse_relation_id()
        relation_id322 = _t1015
        self.consume_literal(')')
        _t1016 = transactions_pb2.ExportCSVColumn(column_name=string321, column_data=relation_id322)
        return _t1016


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
