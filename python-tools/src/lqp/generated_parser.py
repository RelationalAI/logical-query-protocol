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
            ('LITERAL', re.compile(r'<'), lambda x: x),
            ('LITERAL', re.compile(r'='), lambda x: x),
            ('LITERAL', re.compile(r'>'), lambda x: x),
            ('LITERAL', re.compile(r'\['), lambda x: x),
            ('LITERAL', re.compile(r'\]'), lambda x: x),
            ('LITERAL', re.compile(r'\{'), lambda x: x),
            ('LITERAL', re.compile(r'\|'), lambda x: x),
            ('LITERAL', re.compile(r'\}'), lambda x: x),
            ('COLON_SYMBOL', re.compile(r':[a-zA-Z_][a-zA-Z0-9_.-]*'), lambda x: Lexer.scan_colon_symbol(x)),
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
            _t1019 = default
        else:
            val = value
            if val.HasField('int_value'):
                _t1020 = val.int_value
            else:
                _t1020 = default
            _t1019 = _t1020
        return _t1019

    @staticmethod
    def _extract_value_float64(value: Optional[logic_pb2.Value], default: float) -> float:
        if value is None:
            _t1021 = default
        else:
            val = value
            if val.HasField('float_value'):
                _t1022 = val.float_value
            else:
                _t1022 = default
            _t1021 = _t1022
        return _t1021

    @staticmethod
    def _extract_value_string(value: Optional[logic_pb2.Value], default: str) -> str:
        if value is None:
            _t1023 = default
        else:
            val = value
            if val.HasField('string_value'):
                _t1024 = val.string_value
            else:
                _t1024 = default
            _t1023 = _t1024
        return _t1023

    @staticmethod
    def _extract_value_boolean(value: Optional[logic_pb2.Value], default: bool) -> bool:
        if value is None:
            _t1025 = default
        else:
            val = value
            if val.HasField('boolean_value'):
                _t1026 = val.boolean_value
            else:
                _t1026 = default
            _t1025 = _t1026
        return _t1025

    @staticmethod
    def _extract_value_bytes(value: Optional[logic_pb2.Value], default: bytes) -> bytes:
        if value is None:
            _t1027 = default
        else:
            val = value
            if val.HasField('string_value'):
                _t1028 = val.string_value.encode()
            else:
                _t1028 = default
            _t1027 = _t1028
        return _t1027

    @staticmethod
    def _extract_value_uint128(value: Optional[logic_pb2.Value], default: logic_pb2.UInt128Value) -> logic_pb2.UInt128Value:
        if value is None:
            _t1029 = default
        else:
            val = value
            if val.HasField('uint128_value'):
                _t1030 = val.uint128_value
            else:
                _t1030 = default
            _t1029 = _t1030
        return _t1029

    @staticmethod
    def _extract_value_string_list(value: Optional[logic_pb2.Value], default: list[str]) -> list[str]:
        if value is None:
            _t1031 = default
        else:
            val = value
            if val.HasField('string_value'):
                _t1032 = [val.string_value]
            else:
                _t1032 = default
            _t1031 = _t1032
        return _t1031

    @staticmethod
    def construct_csv_config(config_dict: list[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1033 = Parser._extract_value_int64(config.get('csv_header_row'), 1)
        header_row = _t1033
        _t1034 = Parser._extract_value_int64(config.get('csv_skip'), 0)
        skip = _t1034
        _t1035 = Parser._extract_value_string(config.get('csv_new_line'), '')
        new_line = _t1035
        _t1036 = Parser._extract_value_string(config.get('csv_delimiter'), ',')
        delimiter = _t1036
        _t1037 = Parser._extract_value_string(config.get('csv_quotechar'), '"')
        quotechar = _t1037
        _t1038 = Parser._extract_value_string(config.get('csv_escapechar'), '"')
        escapechar = _t1038
        _t1039 = Parser._extract_value_string(config.get('csv_comment'), '')
        comment = _t1039
        _t1040 = Parser._extract_value_string_list(config.get('csv_missing_strings'), [])
        missing_strings = _t1040
        _t1041 = Parser._extract_value_string(config.get('csv_decimal_separator'), '.')
        decimal_separator = _t1041
        _t1042 = Parser._extract_value_string(config.get('csv_encoding'), 'utf-8')
        encoding = _t1042
        _t1043 = Parser._extract_value_string(config.get('csv_compression'), 'auto')
        compression = _t1043
        _t1044 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t1044

    @staticmethod
    def construct_betree_info(key_types: list[Any], value_types: list[Any], config_dict: list[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1045 = Parser._extract_value_float64(config.get('betree_config_epsilon'), 0.5)
        epsilon = _t1045
        _t1046 = Parser._extract_value_int64(config.get('betree_config_max_pivots'), 4)
        max_pivots = _t1046
        _t1047 = Parser._extract_value_int64(config.get('betree_config_max_deltas'), 16)
        max_deltas = _t1047
        _t1048 = Parser._extract_value_int64(config.get('betree_config_max_leaf'), 16)
        max_leaf = _t1048
        _t1049 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1049
        _t1050 = Parser._extract_value_uint128(config.get('betree_locator_root_pageid'), None)
        root_pageid = _t1050
        _t1051 = Parser._extract_value_bytes(config.get('betree_locator_inline_data'), None)
        inline_data = _t1051
        _t1052 = Parser._extract_value_int64(config.get('betree_locator_element_count'), 0)
        element_count = _t1052
        _t1053 = Parser._extract_value_int64(config.get('betree_locator_tree_height'), 0)
        tree_height = _t1053
        _t1054 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1054
        _t1055 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1055

    @staticmethod
    def construct_configure(config_dict: list[tuple[str, logic_pb2.Value]]) -> transactions_pb2.Configure:
        config = dict(config_dict)
        maintenance_level_val = config.get('ivm.maintenance_level')
        if (maintenance_level_val is not None and maintenance_level_val.HasField('string_value')):
            level_str = maintenance_level_val.string_value.upper()
            if level_str in ['OFF', 'AUTO', 'ALL']:
                _t1057 = ('MAINTENANCE_LEVEL_' + level_str)
            else:
                _t1057 = level_str
            _t1056 = _t1057
        else:
            _t1056 = 'MAINTENANCE_LEVEL_OFF'
        maintenance_level = _t1056
        _t1058 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1058
        _t1059 = Parser._extract_value_int64(config.get('semantics_version'), 0)
        semantics_version = _t1059
        _t1060 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1060

    @staticmethod
    def export_csv_config(path: str, columns: list[Any], config_dict: list[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1061 = Parser._extract_value_int64(config.get('partition_size'), 0)
        partition_size = _t1061
        _t1062 = Parser._extract_value_string(config.get('compression'), '')
        compression = _t1062
        _t1063 = Parser._extract_value_boolean(config.get('syntax_header_row'), True)
        syntax_header_row = _t1063
        _t1064 = Parser._extract_value_string(config.get('syntax_missing_string'), '')
        syntax_missing_string = _t1064
        _t1065 = Parser._extract_value_string(config.get('syntax_delim'), ',')
        syntax_delim = _t1065
        _t1066 = Parser._extract_value_string(config.get('syntax_quotechar'), '"')
        syntax_quotechar = _t1066
        _t1067 = Parser._extract_value_string(config.get('syntax_escapechar'), '\\')
        syntax_escapechar = _t1067
        _t1068 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1068

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
        cond7 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond7:
            _t330 = self.parse_config_key_value()
            xs6.append(_t330)
            cond7 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        x8 = xs6
        self.consume_literal('}')
        return x8

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        symbol9 = self.consume_terminal('COLON_SYMBOL')
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
            value20 = _t346
            _t347 = logic_pb2.Value(boolean_value=value20)
            _t345 = _t347
        else:
            if prediction11 == 8:
                self.consume_literal('missing')
                _t349 = logic_pb2.Value(missing_value=logic_pb2.MissingValue())
                _t348 = _t349
            else:
                if prediction11 == 7:
                    value19 = self.consume_terminal('DECIMAL')
                    _t351 = logic_pb2.Value(decimal_value=value19)
                    _t350 = _t351
                else:
                    if prediction11 == 6:
                        value18 = self.consume_terminal('INT128')
                        _t353 = logic_pb2.Value(int128_value=value18)
                        _t352 = _t353
                    else:
                        if prediction11 == 5:
                            value17 = self.consume_terminal('UINT128')
                            _t355 = logic_pb2.Value(uint128_value=value17)
                            _t354 = _t355
                        else:
                            if prediction11 == 4:
                                value16 = self.consume_terminal('FLOAT')
                                _t357 = logic_pb2.Value(float_value=value16)
                                _t356 = _t357
                            else:
                                if prediction11 == 3:
                                    value15 = self.consume_terminal('INT')
                                    _t359 = logic_pb2.Value(int_value=value15)
                                    _t358 = _t359
                                else:
                                    if prediction11 == 2:
                                        value14 = self.consume_terminal('STRING')
                                        _t361 = logic_pb2.Value(string_value=value14)
                                        _t360 = _t361
                                    else:
                                        if prediction11 == 1:
                                            _t363 = self.parse_datetime()
                                            value13 = _t363
                                            _t364 = logic_pb2.Value(datetime_value=value13)
                                            _t362 = _t364
                                        else:
                                            if prediction11 == 0:
                                                _t366 = self.parse_date()
                                                value12 = _t366
                                                _t367 = logic_pb2.Value(date_value=value12)
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
        year21 = self.consume_terminal('INT')
        month22 = self.consume_terminal('INT')
        day23 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t368 = logic_pb2.DateValue(year=int(year21), month=int(month22), day=int(day23))
        return _t368

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        self.consume_literal('(')
        self.consume_literal('datetime')
        year24 = self.consume_terminal('INT')
        month25 = self.consume_terminal('INT')
        day26 = self.consume_terminal('INT')
        hour27 = self.consume_terminal('INT')
        minute28 = self.consume_terminal('INT')
        second29 = self.consume_terminal('INT')
        if self.match_lookahead_terminal('INT', 0):
            _t369 = self.consume_terminal('INT')
        else:
            _t369 = None
        microsecond30 = _t369
        self.consume_literal(')')
        _t370 = logic_pb2.DateTimeValue(year=int(year24), month=int(month25), day=int(day26), hour=int(hour27), minute=int(minute28), second=int(second29), microsecond=int((microsecond30 if microsecond30 is not None else 0)))
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
        cond33 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond33:
            _t374 = self.parse_fragment_id()
            xs32.append(_t374)
            cond33 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        fragments34 = xs32
        self.consume_literal(')')
        _t375 = transactions_pb2.Sync(fragments=fragments34)
        return _t375

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        symbol35 = self.consume_terminal('COLON_SYMBOL')
        return fragments_pb2.FragmentId(id=symbol35.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal('(')
        self.consume_literal('epoch')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('writes', 1)):
            _t377 = self.parse_epoch_writes()
            _t376 = _t377
        else:
            _t376 = None
        writes36 = _t376
        if self.match_lookahead_literal('(', 0):
            _t379 = self.parse_epoch_reads()
            _t378 = _t379
        else:
            _t378 = None
        reads37 = _t378
        self.consume_literal(')')
        _t380 = transactions_pb2.Epoch(writes=(writes36 if writes36 is not None else []), reads=(reads37 if reads37 is not None else []))
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
        x40 = xs38
        self.consume_literal(')')
        return x40

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
            value44 = _t389
            _t390 = transactions_pb2.Write(context=value44)
            _t388 = _t390
        else:
            if prediction41 == 1:
                _t392 = self.parse_undefine()
                value43 = _t392
                _t393 = transactions_pb2.Write(undefine=value43)
                _t391 = _t393
            else:
                if prediction41 == 0:
                    _t395 = self.parse_define()
                    value42 = _t395
                    _t396 = transactions_pb2.Write(define=value42)
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
        fragment_id46 = _t399
        xs47 = []
        cond48 = self.match_lookahead_literal('(', 0)
        while cond48:
            _t400 = self.parse_declaration()
            xs47.append(_t400)
            cond48 = self.match_lookahead_literal('(', 0)
        declarations49 = xs47
        self.consume_literal(')')
        return self.construct_fragment(fragment_id46, declarations49)

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
            value55 = _t409
            _t410 = logic_pb2.Declaration(data=value55)
            _t408 = _t410
        else:
            if prediction51 == 2:
                _t412 = self.parse_constraint()
                value54 = _t412
                _t413 = logic_pb2.Declaration(constraint=value54)
                _t411 = _t413
            else:
                if prediction51 == 1:
                    _t415 = self.parse_algorithm()
                    value53 = _t415
                    _t416 = logic_pb2.Declaration(algorithm=value53)
                    _t414 = _t416
                else:
                    if prediction51 == 0:
                        _t418 = self.parse_def()
                        value52 = _t418
                        _t419 = logic_pb2.Declaration()
                        getattr(_t419, 'def').CopyFrom(value52)
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
        name56 = _t420
        _t421 = self.parse_abstraction()
        body57 = _t421
        if self.match_lookahead_literal('(', 0):
            _t423 = self.parse_attrs()
            _t422 = _t423
        else:
            _t422 = None
        attrs58 = _t422
        self.consume_literal(')')
        _t424 = logic_pb2.Def(name=name56, body=body57, attrs=(attrs58 if attrs58 is not None else []))
        return _t424

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_terminal('INT', 0):
            _t426 = 1
        else:
            if self.match_lookahead_terminal('COLON_SYMBOL', 0):
                _t427 = 0
            else:
                _t427 = -1
            _t426 = _t427
        prediction59 = _t426
        if prediction59 == 1:
            INT61 = self.consume_terminal('INT')
            _t428 = logic_pb2.RelationId(id_low=INT61 & 0xFFFFFFFFFFFFFFFF, id_high=(INT61 >> 64) & 0xFFFFFFFFFFFFFFFF)
        else:
            if prediction59 == 0:
                symbol60 = self.consume_terminal('COLON_SYMBOL')
                _t429 = self.relation_id_from_string(symbol60)
            else:
                raise ParseError(f"{'Unexpected token in relation_id'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t429 = None
            _t428 = _t429
        return _t428

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal('(')
        _t430 = self.parse_bindings()
        bindings62 = _t430
        _t431 = self.parse_formula()
        formula63 = _t431
        self.consume_literal(')')
        _t432 = logic_pb2.Abstraction(vars=(bindings62[0] + (bindings62[1] if bindings62[1] is not None else [])), value=formula63)
        return _t432

    def parse_bindings(self) -> tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]:
        self.consume_literal('[')
        xs64 = []
        cond65 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond65:
            _t433 = self.parse_binding()
            xs64.append(_t433)
            cond65 = self.match_lookahead_terminal('SYMBOL', 0)
        keys66 = xs64
        if self.match_lookahead_literal('|', 0):
            _t435 = self.parse_value_bindings()
            _t434 = _t435
        else:
            _t434 = None
        values67 = _t434
        self.consume_literal(']')
        return (keys66, (values67 if values67 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol68 = self.consume_terminal('SYMBOL')
        self.consume_literal('::')
        _t436 = self.parse_type()
        type69 = _t436
        _t437 = logic_pb2.Var(name=symbol68)
        _t438 = logic_pb2.Binding(var=_t437, type=type69)
        return _t438

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal('UNKNOWN', 0):
            _t439 = 0
        else:
            if self.match_lookahead_literal('UINT128', 0):
                _t440 = 4
            else:
                if self.match_lookahead_literal('STRING', 0):
                    _t449 = 1
                else:
                    if self.match_lookahead_literal('MISSING', 0):
                        _t450 = 8
                    else:
                        if self.match_lookahead_literal('INT128', 0):
                            _t451 = 5
                        else:
                            if self.match_lookahead_literal('INT', 0):
                                _t452 = 2
                            else:
                                if self.match_lookahead_literal('FLOAT', 0):
                                    _t453 = 3
                                else:
                                    if self.match_lookahead_literal('DATETIME', 0):
                                        _t454 = 7
                                    else:
                                        if self.match_lookahead_literal('DATE', 0):
                                            _t455 = 6
                                        else:
                                            if self.match_lookahead_literal('BOOLEAN', 0):
                                                _t456 = 10
                                            else:
                                                if self.match_lookahead_literal('(', 0):
                                                    _t457 = 9
                                                else:
                                                    _t457 = -1
                                                _t456 = _t457
                                            _t455 = _t456
                                        _t454 = _t455
                                    _t453 = _t454
                                _t452 = _t453
                            _t451 = _t452
                        _t450 = _t451
                    _t449 = _t450
                _t440 = _t449
            _t439 = _t440
        prediction70 = _t439
        if prediction70 == 10:
            _t459 = self.parse_boolean_type()
            value81 = _t459
            _t460 = logic_pb2.Type(boolean_type=value81)
            _t458 = _t460
        else:
            if prediction70 == 9:
                _t462 = self.parse_decimal_type()
                value80 = _t462
                _t463 = logic_pb2.Type(decimal_type=value80)
                _t461 = _t463
            else:
                if prediction70 == 8:
                    _t465 = self.parse_missing_type()
                    value79 = _t465
                    _t466 = logic_pb2.Type(missing_type=value79)
                    _t464 = _t466
                else:
                    if prediction70 == 7:
                        _t468 = self.parse_datetime_type()
                        value78 = _t468
                        _t469 = logic_pb2.Type(datetime_type=value78)
                        _t467 = _t469
                    else:
                        if prediction70 == 6:
                            _t471 = self.parse_date_type()
                            value77 = _t471
                            _t472 = logic_pb2.Type(date_type=value77)
                            _t470 = _t472
                        else:
                            if prediction70 == 5:
                                _t474 = self.parse_int128_type()
                                value76 = _t474
                                _t475 = logic_pb2.Type(int128_type=value76)
                                _t473 = _t475
                            else:
                                if prediction70 == 4:
                                    _t477 = self.parse_uint128_type()
                                    value75 = _t477
                                    _t478 = logic_pb2.Type(uint128_type=value75)
                                    _t476 = _t478
                                else:
                                    if prediction70 == 3:
                                        _t480 = self.parse_float_type()
                                        value74 = _t480
                                        _t481 = logic_pb2.Type(float_type=value74)
                                        _t479 = _t481
                                    else:
                                        if prediction70 == 2:
                                            _t483 = self.parse_int_type()
                                            value73 = _t483
                                            _t484 = logic_pb2.Type(int_type=value73)
                                            _t482 = _t484
                                        else:
                                            if prediction70 == 1:
                                                _t486 = self.parse_string_type()
                                                value72 = _t486
                                                _t487 = logic_pb2.Type(string_type=value72)
                                                _t485 = _t487
                                            else:
                                                if prediction70 == 0:
                                                    _t489 = self.parse_unspecified_type()
                                                    value71 = _t489
                                                    _t490 = logic_pb2.Type(unspecified_type=value71)
                                                    _t488 = _t490
                                                else:
                                                    raise ParseError(f"{'Unexpected token in type'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                    _t488 = None
                                                _t485 = _t488
                                            _t482 = _t485
                                        _t479 = _t482
                                    _t476 = _t479
                                _t473 = _t476
                            _t470 = _t473
                        _t467 = _t470
                    _t464 = _t467
                _t461 = _t464
            _t458 = _t461
        return _t458

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
        precision82 = self.consume_terminal('INT')
        scale83 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t491 = logic_pb2.DecimalType(precision=int(precision82), scale=int(scale83))
        return _t491

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal('BOOLEAN')
        return logic_pb2.BooleanType()

    def parse_value_bindings(self) -> list[logic_pb2.Binding]:
        self.consume_literal('|')
        xs84 = []
        cond85 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond85:
            _t492 = self.parse_binding()
            xs84.append(_t492)
            cond85 = self.match_lookahead_terminal('SYMBOL', 0)
        x86 = xs84
        return x86

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('true', 1):
                _t494 = 0
            else:
                if self.match_lookahead_literal('relatom', 1):
                    _t495 = 11
                else:
                    if self.match_lookahead_literal('reduce', 1):
                        _t496 = 3
                    else:
                        if self.match_lookahead_literal('primitive', 1):
                            _t497 = 10
                        else:
                            if self.match_lookahead_literal('pragma', 1):
                                _t498 = 9
                            else:
                                if self.match_lookahead_literal('or', 1):
                                    _t499 = 5
                                else:
                                    if self.match_lookahead_literal('not', 1):
                                        _t500 = 6
                                    else:
                                        if self.match_lookahead_literal('ffi', 1):
                                            _t501 = 7
                                        else:
                                            if self.match_lookahead_literal('false', 1):
                                                _t515 = 1
                                            else:
                                                if self.match_lookahead_literal('exists', 1):
                                                    _t516 = 2
                                                else:
                                                    if self.match_lookahead_literal('cast', 1):
                                                        _t517 = 12
                                                    else:
                                                        if self.match_lookahead_literal('atom', 1):
                                                            _t518 = 8
                                                        else:
                                                            if self.match_lookahead_literal('and', 1):
                                                                _t519 = 4
                                                            else:
                                                                if self.match_lookahead_literal('>=', 1):
                                                                    _t520 = 10
                                                                else:
                                                                    if self.match_lookahead_literal('>', 1):
                                                                        _t521 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal('=', 1):
                                                                            _t522 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal('<=', 1):
                                                                                _t523 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal('<', 1):
                                                                                    _t524 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal('/', 1):
                                                                                        _t525 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal('-', 1):
                                                                                            _t526 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal('+', 1):
                                                                                                _t527 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal('*', 1):
                                                                                                    _t528 = 10
                                                                                                else:
                                                                                                    _t528 = -1
                                                                                                _t527 = _t528
                                                                                            _t526 = _t527
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
                                            _t501 = _t515
                                        _t500 = _t501
                                    _t499 = _t500
                                _t498 = _t499
                            _t497 = _t498
                        _t496 = _t497
                    _t495 = _t496
                _t494 = _t495
            _t493 = _t494
        else:
            _t493 = -1
        prediction87 = _t493
        if prediction87 == 12:
            _t530 = self.parse_cast()
            value100 = _t530
            _t531 = logic_pb2.Formula(cast=value100)
            _t529 = _t531
        else:
            if prediction87 == 11:
                _t533 = self.parse_rel_atom()
                value99 = _t533
                _t534 = logic_pb2.Formula(rel_atom=value99)
                _t532 = _t534
            else:
                if prediction87 == 10:
                    _t536 = self.parse_primitive()
                    value98 = _t536
                    _t537 = logic_pb2.Formula(primitive=value98)
                    _t535 = _t537
                else:
                    if prediction87 == 9:
                        _t539 = self.parse_pragma()
                        value97 = _t539
                        _t540 = logic_pb2.Formula(pragma=value97)
                        _t538 = _t540
                    else:
                        if prediction87 == 8:
                            _t542 = self.parse_atom()
                            value96 = _t542
                            _t543 = logic_pb2.Formula(atom=value96)
                            _t541 = _t543
                        else:
                            if prediction87 == 7:
                                _t545 = self.parse_ffi()
                                value95 = _t545
                                _t546 = logic_pb2.Formula(ffi=value95)
                                _t544 = _t546
                            else:
                                if prediction87 == 6:
                                    _t548 = self.parse_not()
                                    value94 = _t548
                                    _t549 = logic_pb2.Formula()
                                    getattr(_t549, 'not').CopyFrom(value94)
                                    _t547 = _t549
                                else:
                                    if prediction87 == 5:
                                        _t551 = self.parse_disjunction()
                                        value93 = _t551
                                        _t552 = logic_pb2.Formula(disjunction=value93)
                                        _t550 = _t552
                                    else:
                                        if prediction87 == 4:
                                            _t554 = self.parse_conjunction()
                                            value92 = _t554
                                            _t555 = logic_pb2.Formula(conjunction=value92)
                                            _t553 = _t555
                                        else:
                                            if prediction87 == 3:
                                                _t557 = self.parse_reduce()
                                                value91 = _t557
                                                _t558 = logic_pb2.Formula(reduce=value91)
                                                _t556 = _t558
                                            else:
                                                if prediction87 == 2:
                                                    _t560 = self.parse_exists()
                                                    value90 = _t560
                                                    _t561 = logic_pb2.Formula(exists=value90)
                                                    _t559 = _t561
                                                else:
                                                    if prediction87 == 1:
                                                        _t563 = self.parse_false()
                                                        value89 = _t563
                                                        _t564 = logic_pb2.Formula(disjunction=value89)
                                                        _t562 = _t564
                                                    else:
                                                        if prediction87 == 0:
                                                            _t566 = self.parse_true()
                                                            value88 = _t566
                                                            _t567 = logic_pb2.Formula(conjunction=value88)
                                                            _t565 = _t567
                                                        else:
                                                            raise ParseError(f"{'Unexpected token in formula'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t565 = None
                                                        _t562 = _t565
                                                    _t559 = _t562
                                                _t556 = _t559
                                            _t553 = _t556
                                        _t550 = _t553
                                    _t547 = _t550
                                _t544 = _t547
                            _t541 = _t544
                        _t538 = _t541
                    _t535 = _t538
                _t532 = _t535
            _t529 = _t532
        return _t529

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('true')
        self.consume_literal(')')
        _t568 = logic_pb2.Conjunction(args=[])
        return _t568

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('false')
        self.consume_literal(')')
        _t569 = logic_pb2.Disjunction(args=[])
        return _t569

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal('(')
        self.consume_literal('exists')
        _t570 = self.parse_bindings()
        bindings101 = _t570
        _t571 = self.parse_formula()
        formula102 = _t571
        self.consume_literal(')')
        _t572 = logic_pb2.Abstraction(vars=(bindings101[0] + (bindings101[1] if bindings101[1] is not None else [])), value=formula102)
        _t573 = logic_pb2.Exists(body=_t572)
        return _t573

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal('(')
        self.consume_literal('reduce')
        _t574 = self.parse_abstraction()
        op103 = _t574
        _t575 = self.parse_abstraction()
        body104 = _t575
        _t576 = self.parse_terms()
        terms105 = _t576
        self.consume_literal(')')
        _t577 = logic_pb2.Reduce(op=op103, body=body104, terms=terms105)
        return _t577

    def parse_terms(self) -> list[logic_pb2.Term]:
        self.consume_literal('(')
        self.consume_literal('terms')
        xs106 = []
        cond107 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond107:
            _t578 = self.parse_term()
            xs106.append(_t578)
            cond107 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        x108 = xs106
        self.consume_literal(')')
        return x108

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_literal('true', 0):
            _t610 = 1
        else:
            if self.match_lookahead_literal('missing', 0):
                _t626 = 1
            else:
                if self.match_lookahead_literal('false', 0):
                    _t634 = 1
                else:
                    if self.match_lookahead_literal('(', 0):
                        _t638 = 1
                    else:
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t640 = 1
                        else:
                            if self.match_lookahead_terminal('SYMBOL', 0):
                                _t641 = 0
                            else:
                                _t641 = (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or -1)))))
                            _t640 = _t641
                        _t638 = _t640
                    _t634 = _t638
                _t626 = _t634
            _t610 = _t626
        prediction109 = _t610
        if prediction109 == 1:
            _t643 = self.parse_constant()
            value111 = _t643
            _t644 = logic_pb2.Term(constant=value111)
            _t642 = _t644
        else:
            if prediction109 == 0:
                _t646 = self.parse_var()
                value110 = _t646
                _t647 = logic_pb2.Term(var=value110)
                _t645 = _t647
            else:
                raise ParseError(f"{'Unexpected token in term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t645 = None
            _t642 = _t645
        return _t642

    def parse_var(self) -> logic_pb2.Var:
        symbol112 = self.consume_terminal('SYMBOL')
        _t648 = logic_pb2.Var(name=symbol112)
        return _t648

    def parse_constant(self) -> logic_pb2.Value:
        _t649 = self.parse_value()
        x113 = _t649
        return x113

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('and')
        xs114 = []
        cond115 = self.match_lookahead_literal('(', 0)
        while cond115:
            _t650 = self.parse_formula()
            xs114.append(_t650)
            cond115 = self.match_lookahead_literal('(', 0)
        args116 = xs114
        self.consume_literal(')')
        _t651 = logic_pb2.Conjunction(args=args116)
        return _t651

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('or')
        xs117 = []
        cond118 = self.match_lookahead_literal('(', 0)
        while cond118:
            _t652 = self.parse_formula()
            xs117.append(_t652)
            cond118 = self.match_lookahead_literal('(', 0)
        args119 = xs117
        self.consume_literal(')')
        _t653 = logic_pb2.Disjunction(args=args119)
        return _t653

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal('(')
        self.consume_literal('not')
        _t654 = self.parse_formula()
        arg120 = _t654
        self.consume_literal(')')
        _t655 = logic_pb2.Not(arg=arg120)
        return _t655

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal('(')
        self.consume_literal('ffi')
        _t656 = self.parse_name()
        name121 = _t656
        _t657 = self.parse_ffi_args()
        args122 = _t657
        _t658 = self.parse_terms()
        terms123 = _t658
        self.consume_literal(')')
        _t659 = logic_pb2.FFI(name=name121, args=args122, terms=terms123)
        return _t659

    def parse_name(self) -> str:
        x124 = self.consume_terminal('COLON_SYMBOL')
        return x124

    def parse_ffi_args(self) -> list[logic_pb2.Abstraction]:
        self.consume_literal('(')
        self.consume_literal('args')
        xs125 = []
        cond126 = self.match_lookahead_literal('(', 0)
        while cond126:
            _t660 = self.parse_abstraction()
            xs125.append(_t660)
            cond126 = self.match_lookahead_literal('(', 0)
        x127 = xs125
        self.consume_literal(')')
        return x127

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal('(')
        self.consume_literal('atom')
        _t661 = self.parse_relation_id()
        name128 = _t661
        xs129 = []
        cond130 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond130:
            _t662 = self.parse_term()
            xs129.append(_t662)
            cond130 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms131 = xs129
        self.consume_literal(')')
        _t663 = logic_pb2.Atom(name=name128, terms=terms131)
        return _t663

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal('(')
        self.consume_literal('pragma')
        _t664 = self.parse_name()
        name132 = _t664
        xs133 = []
        cond134 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond134:
            _t665 = self.parse_term()
            xs133.append(_t665)
            cond134 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms135 = xs133
        self.consume_literal(')')
        _t666 = logic_pb2.Pragma(name=name132, terms=terms135)
        return _t666

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('primitive', 1):
                _t668 = 9
            else:
                if self.match_lookahead_literal('>=', 1):
                    _t669 = 4
                else:
                    if self.match_lookahead_literal('>', 1):
                        _t670 = 3
                    else:
                        if self.match_lookahead_literal('=', 1):
                            _t671 = 0
                        else:
                            if self.match_lookahead_literal('<=', 1):
                                _t672 = 2
                            else:
                                if self.match_lookahead_literal('<', 1):
                                    _t677 = 1
                                else:
                                    if self.match_lookahead_literal('/', 1):
                                        _t678 = 8
                                    else:
                                        if self.match_lookahead_literal('-', 1):
                                            _t679 = 6
                                        else:
                                            if self.match_lookahead_literal('+', 1):
                                                _t680 = 5
                                            else:
                                                if self.match_lookahead_literal('*', 1):
                                                    _t681 = 7
                                                else:
                                                    _t681 = -1
                                                _t680 = _t681
                                            _t679 = _t680
                                        _t678 = _t679
                                    _t677 = _t678
                                _t672 = _t677
                            _t671 = _t672
                        _t670 = _t671
                    _t669 = _t670
                _t668 = _t669
            _t667 = _t668
        else:
            _t667 = -1
        prediction136 = _t667
        if prediction136 == 9:
            self.consume_literal('(')
            self.consume_literal('primitive')
            _t683 = self.parse_name()
            name146 = _t683
            xs147 = []
            cond148 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            while cond148:
                _t684 = self.parse_rel_term()
                xs147.append(_t684)
                cond148 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            terms149 = xs147
            self.consume_literal(')')
            _t685 = logic_pb2.Primitive(name=name146, terms=terms149)
            _t682 = _t685
        else:
            if prediction136 == 8:
                _t687 = self.parse_divide()
                op145 = _t687
                _t686 = op145
            else:
                if prediction136 == 7:
                    _t689 = self.parse_multiply()
                    op144 = _t689
                    _t688 = op144
                else:
                    if prediction136 == 6:
                        _t691 = self.parse_minus()
                        op143 = _t691
                        _t690 = op143
                    else:
                        if prediction136 == 5:
                            _t693 = self.parse_add()
                            op142 = _t693
                            _t692 = op142
                        else:
                            if prediction136 == 4:
                                _t695 = self.parse_gt_eq()
                                op141 = _t695
                                _t694 = op141
                            else:
                                if prediction136 == 3:
                                    _t697 = self.parse_gt()
                                    op140 = _t697
                                    _t696 = op140
                                else:
                                    if prediction136 == 2:
                                        _t699 = self.parse_lt_eq()
                                        op139 = _t699
                                        _t698 = op139
                                    else:
                                        if prediction136 == 1:
                                            _t701 = self.parse_lt()
                                            op138 = _t701
                                            _t700 = op138
                                        else:
                                            if prediction136 == 0:
                                                _t703 = self.parse_eq()
                                                op137 = _t703
                                                _t702 = op137
                                            else:
                                                raise ParseError(f"{'Unexpected token in primitive'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t702 = None
                                            _t700 = _t702
                                        _t698 = _t700
                                    _t696 = _t698
                                _t694 = _t696
                            _t692 = _t694
                        _t690 = _t692
                    _t688 = _t690
                _t686 = _t688
            _t682 = _t686
        return _t682

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('=')
        _t704 = self.parse_term()
        left150 = _t704
        _t705 = self.parse_term()
        right151 = _t705
        self.consume_literal(')')
        _t706 = logic_pb2.RelTerm(term=left150)
        _t707 = logic_pb2.RelTerm(term=right151)
        _t708 = logic_pb2.Primitive(name='rel_primitive_eq', terms=[_t706, _t707])
        return _t708

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<')
        _t709 = self.parse_term()
        left152 = _t709
        _t710 = self.parse_term()
        right153 = _t710
        self.consume_literal(')')
        _t711 = logic_pb2.RelTerm(term=left152)
        _t712 = logic_pb2.RelTerm(term=right153)
        _t713 = logic_pb2.Primitive(name='rel_primitive_lt_monotype', terms=[_t711, _t712])
        return _t713

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<=')
        _t714 = self.parse_term()
        left154 = _t714
        _t715 = self.parse_term()
        right155 = _t715
        self.consume_literal(')')
        _t716 = logic_pb2.RelTerm(term=left154)
        _t717 = logic_pb2.RelTerm(term=right155)
        _t718 = logic_pb2.Primitive(name='rel_primitive_lt_eq_monotype', terms=[_t716, _t717])
        return _t718

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>')
        _t719 = self.parse_term()
        left156 = _t719
        _t720 = self.parse_term()
        right157 = _t720
        self.consume_literal(')')
        _t721 = logic_pb2.RelTerm(term=left156)
        _t722 = logic_pb2.RelTerm(term=right157)
        _t723 = logic_pb2.Primitive(name='rel_primitive_gt_monotype', terms=[_t721, _t722])
        return _t723

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>=')
        _t724 = self.parse_term()
        left158 = _t724
        _t725 = self.parse_term()
        right159 = _t725
        self.consume_literal(')')
        _t726 = logic_pb2.RelTerm(term=left158)
        _t727 = logic_pb2.RelTerm(term=right159)
        _t728 = logic_pb2.Primitive(name='rel_primitive_gt_eq_monotype', terms=[_t726, _t727])
        return _t728

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('+')
        _t729 = self.parse_term()
        left160 = _t729
        _t730 = self.parse_term()
        right161 = _t730
        _t731 = self.parse_term()
        result162 = _t731
        self.consume_literal(')')
        _t732 = logic_pb2.RelTerm(term=left160)
        _t733 = logic_pb2.RelTerm(term=right161)
        _t734 = logic_pb2.RelTerm(term=result162)
        _t735 = logic_pb2.Primitive(name='rel_primitive_add_monotype', terms=[_t732, _t733, _t734])
        return _t735

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('-')
        _t736 = self.parse_term()
        left163 = _t736
        _t737 = self.parse_term()
        right164 = _t737
        _t738 = self.parse_term()
        result165 = _t738
        self.consume_literal(')')
        _t739 = logic_pb2.RelTerm(term=left163)
        _t740 = logic_pb2.RelTerm(term=right164)
        _t741 = logic_pb2.RelTerm(term=result165)
        _t742 = logic_pb2.Primitive(name='rel_primitive_subtract_monotype', terms=[_t739, _t740, _t741])
        return _t742

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('*')
        _t743 = self.parse_term()
        left166 = _t743
        _t744 = self.parse_term()
        right167 = _t744
        _t745 = self.parse_term()
        result168 = _t745
        self.consume_literal(')')
        _t746 = logic_pb2.RelTerm(term=left166)
        _t747 = logic_pb2.RelTerm(term=right167)
        _t748 = logic_pb2.RelTerm(term=result168)
        _t749 = logic_pb2.Primitive(name='rel_primitive_multiply_monotype', terms=[_t746, _t747, _t748])
        return _t749

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('/')
        _t750 = self.parse_term()
        left169 = _t750
        _t751 = self.parse_term()
        right170 = _t751
        _t752 = self.parse_term()
        result171 = _t752
        self.consume_literal(')')
        _t753 = logic_pb2.RelTerm(term=left169)
        _t754 = logic_pb2.RelTerm(term=right170)
        _t755 = logic_pb2.RelTerm(term=result171)
        _t756 = logic_pb2.Primitive(name='rel_primitive_divide_monotype', terms=[_t753, _t754, _t755])
        return _t756

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_literal('true', 0):
            _t772 = 1
        else:
            if self.match_lookahead_literal('missing', 0):
                _t780 = 1
            else:
                if self.match_lookahead_literal('false', 0):
                    _t784 = 1
                else:
                    if self.match_lookahead_literal('(', 0):
                        _t786 = 1
                    else:
                        if self.match_lookahead_literal('#', 0):
                            _t787 = 0
                        else:
                            _t787 = (self.match_lookahead_terminal('UINT128', 0) or (self.match_lookahead_terminal('SYMBOL', 0) or (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or -1)))))))
                        _t786 = _t787
                    _t784 = _t786
                _t780 = _t784
            _t772 = _t780
        prediction172 = _t772
        if prediction172 == 1:
            _t789 = self.parse_term()
            value174 = _t789
            _t790 = logic_pb2.RelTerm(term=value174)
            _t788 = _t790
        else:
            if prediction172 == 0:
                _t792 = self.parse_specialized_value()
                value173 = _t792
                _t793 = logic_pb2.RelTerm(specialized_value=value173)
                _t791 = _t793
            else:
                raise ParseError(f"{'Unexpected token in rel_term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t791 = None
            _t788 = _t791
        return _t788

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal('#')
        _t794 = self.parse_value()
        value175 = _t794
        return value175

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        self.consume_literal('(')
        self.consume_literal('relatom')
        _t795 = self.parse_name()
        name176 = _t795
        xs177 = []
        cond178 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond178:
            _t796 = self.parse_rel_term()
            xs177.append(_t796)
            cond178 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms179 = xs177
        self.consume_literal(')')
        _t797 = logic_pb2.RelAtom(name=name176, terms=terms179)
        return _t797

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal('(')
        self.consume_literal('cast')
        _t798 = self.parse_term()
        input180 = _t798
        _t799 = self.parse_term()
        result181 = _t799
        self.consume_literal(')')
        _t800 = logic_pb2.Cast(input=input180, result=result181)
        return _t800

    def parse_attrs(self) -> list[logic_pb2.Attribute]:
        self.consume_literal('(')
        self.consume_literal('attrs')
        xs182 = []
        cond183 = self.match_lookahead_literal('(', 0)
        while cond183:
            _t801 = self.parse_attribute()
            xs182.append(_t801)
            cond183 = self.match_lookahead_literal('(', 0)
        x184 = xs182
        self.consume_literal(')')
        return x184

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal('(')
        self.consume_literal('attribute')
        _t802 = self.parse_name()
        name185 = _t802
        xs186 = []
        cond187 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond187:
            _t803 = self.parse_value()
            xs186.append(_t803)
            cond187 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        args188 = xs186
        self.consume_literal(')')
        _t804 = logic_pb2.Attribute(name=name185, args=args188)
        return _t804

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal('(')
        self.consume_literal('algorithm')
        xs189 = []
        cond190 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        while cond190:
            _t805 = self.parse_relation_id()
            xs189.append(_t805)
            cond190 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        global191 = xs189
        _t806 = self.parse_script()
        body192 = _t806
        self.consume_literal(')')
        _t807 = logic_pb2.Algorithm(body=body192)
        getattr(_t807, 'global').extend(global191)
        return _t807

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal('(')
        self.consume_literal('script')
        xs193 = []
        cond194 = self.match_lookahead_literal('(', 0)
        while cond194:
            _t808 = self.parse_construct()
            xs193.append(_t808)
            cond194 = self.match_lookahead_literal('(', 0)
        constructs195 = xs193
        self.consume_literal(')')
        _t809 = logic_pb2.Script(constructs=constructs195)
        return _t809

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t818 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t822 = 1
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t824 = 1
                    else:
                        if self.match_lookahead_literal('loop', 1):
                            _t825 = 0
                        else:
                            _t825 = (self.match_lookahead_literal('break', 1) or (self.match_lookahead_literal('assign', 1) or -1))
                        _t824 = _t825
                    _t822 = _t824
                _t818 = _t822
            _t810 = _t818
        else:
            _t810 = -1
        prediction196 = _t810
        if prediction196 == 1:
            _t827 = self.parse_instruction()
            value198 = _t827
            _t828 = logic_pb2.Construct(instruction=value198)
            _t826 = _t828
        else:
            if prediction196 == 0:
                _t830 = self.parse_loop()
                value197 = _t830
                _t831 = logic_pb2.Construct(loop=value197)
                _t829 = _t831
            else:
                raise ParseError(f"{'Unexpected token in construct'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t829 = None
            _t826 = _t829
        return _t826

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal('(')
        self.consume_literal('loop')
        _t832 = self.parse_init()
        init199 = _t832
        _t833 = self.parse_script()
        body200 = _t833
        self.consume_literal(')')
        _t834 = logic_pb2.Loop(init=init199, body=body200)
        return _t834

    def parse_init(self) -> list[logic_pb2.Instruction]:
        self.consume_literal('(')
        self.consume_literal('init')
        xs201 = []
        cond202 = self.match_lookahead_literal('(', 0)
        while cond202:
            _t835 = self.parse_instruction()
            xs201.append(_t835)
            cond202 = self.match_lookahead_literal('(', 0)
        x203 = xs201
        self.consume_literal(')')
        return x203

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t841 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t842 = 4
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t843 = 3
                    else:
                        if self.match_lookahead_literal('break', 1):
                            _t844 = 2
                        else:
                            if self.match_lookahead_literal('assign', 1):
                                _t845 = 0
                            else:
                                _t845 = -1
                            _t844 = _t845
                        _t843 = _t844
                    _t842 = _t843
                _t841 = _t842
            _t836 = _t841
        else:
            _t836 = -1
        prediction204 = _t836
        if prediction204 == 4:
            _t847 = self.parse_monus_def()
            value209 = _t847
            _t848 = logic_pb2.Instruction(monus_def=value209)
            _t846 = _t848
        else:
            if prediction204 == 3:
                _t850 = self.parse_monoid_def()
                value208 = _t850
                _t851 = logic_pb2.Instruction(monoid_def=value208)
                _t849 = _t851
            else:
                if prediction204 == 2:
                    _t853 = self.parse_break()
                    value207 = _t853
                    _t854 = logic_pb2.Instruction()
                    getattr(_t854, 'break').CopyFrom(value207)
                    _t852 = _t854
                else:
                    if prediction204 == 1:
                        _t856 = self.parse_upsert()
                        value206 = _t856
                        _t857 = logic_pb2.Instruction(upsert=value206)
                        _t855 = _t857
                    else:
                        if prediction204 == 0:
                            _t859 = self.parse_assign()
                            value205 = _t859
                            _t860 = logic_pb2.Instruction(assign=value205)
                            _t858 = _t860
                        else:
                            raise ParseError(f"{'Unexpected token in instruction'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t858 = None
                        _t855 = _t858
                    _t852 = _t855
                _t849 = _t852
            _t846 = _t849
        return _t846

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal('(')
        self.consume_literal('assign')
        _t861 = self.parse_relation_id()
        name210 = _t861
        _t862 = self.parse_abstraction()
        body211 = _t862
        if self.match_lookahead_literal('(', 0):
            _t864 = self.parse_attrs()
            _t863 = _t864
        else:
            _t863 = None
        attrs212 = _t863
        self.consume_literal(')')
        _t865 = logic_pb2.Assign(name=name210, body=body211, attrs=(attrs212 if attrs212 is not None else []))
        return _t865

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal('(')
        self.consume_literal('upsert')
        _t866 = self.parse_relation_id()
        name213 = _t866
        _t867 = self.parse_abstraction_with_arity()
        abstraction_with_arity214 = _t867
        if self.match_lookahead_literal('(', 0):
            _t869 = self.parse_attrs()
            _t868 = _t869
        else:
            _t868 = None
        attrs215 = _t868
        self.consume_literal(')')
        abstraction = abstraction_with_arity214[0]
        arity = abstraction_with_arity214[1]
        _t870 = logic_pb2.Upsert(name=name213, body=abstraction, attrs=(attrs215 if attrs215 is not None else []), value_arity=arity)
        return _t870

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal('(')
        _t871 = self.parse_bindings()
        bindings216 = _t871
        _t872 = self.parse_formula()
        formula217 = _t872
        self.consume_literal(')')
        _t873 = logic_pb2.Abstraction(vars=(bindings216[0] + (bindings216[1] if bindings216[1] is not None else [])), value=formula217)
        return (_t873, len(bindings216[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal('(')
        self.consume_literal('break')
        _t874 = self.parse_relation_id()
        name218 = _t874
        _t875 = self.parse_abstraction()
        body219 = _t875
        if self.match_lookahead_literal('(', 0):
            _t877 = self.parse_attrs()
            _t876 = _t877
        else:
            _t876 = None
        attrs220 = _t876
        self.consume_literal(')')
        _t878 = logic_pb2.Break(name=name218, body=body219, attrs=(attrs220 if attrs220 is not None else []))
        return _t878

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal('(')
        self.consume_literal('monoid')
        _t879 = self.parse_monoid()
        monoid221 = _t879
        _t880 = self.parse_relation_id()
        name222 = _t880
        _t881 = self.parse_abstraction_with_arity()
        abstraction_with_arity223 = _t881
        if self.match_lookahead_literal('(', 0):
            _t883 = self.parse_attrs()
            _t882 = _t883
        else:
            _t882 = None
        attrs224 = _t882
        self.consume_literal(')')
        abstraction = abstraction_with_arity223[0]
        arity = abstraction_with_arity223[1]
        _t884 = logic_pb2.MonoidDef(monoid=monoid221, name=name222, body=abstraction, attrs=(attrs224 if attrs224 is not None else []), value_arity=arity)
        return _t884

    def parse_monoid(self) -> logic_pb2.Monoid:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('sum', 1):
                _t886 = 3
            else:
                if self.match_lookahead_literal('or', 1):
                    _t887 = 0
                else:
                    if self.match_lookahead_literal('min', 1):
                        _t889 = 1
                    else:
                        if self.match_lookahead_literal('max', 1):
                            _t890 = 2
                        else:
                            _t890 = -1
                        _t889 = _t890
                    _t887 = _t889
                _t886 = _t887
            _t885 = _t886
        else:
            _t885 = -1
        prediction225 = _t885
        if prediction225 == 3:
            _t892 = self.parse_sum_monoid()
            value229 = _t892
            _t893 = logic_pb2.Monoid(sum_monoid=value229)
            _t891 = _t893
        else:
            if prediction225 == 2:
                _t895 = self.parse_max_monoid()
                value228 = _t895
                _t896 = logic_pb2.Monoid(max_monoid=value228)
                _t894 = _t896
            else:
                if prediction225 == 1:
                    _t898 = self.parse_min_monoid()
                    value227 = _t898
                    _t899 = logic_pb2.Monoid(min_monoid=value227)
                    _t897 = _t899
                else:
                    if prediction225 == 0:
                        _t901 = self.parse_or_monoid()
                        value226 = _t901
                        _t902 = logic_pb2.Monoid(or_monoid=value226)
                        _t900 = _t902
                    else:
                        raise ParseError(f"{'Unexpected token in monoid'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t900 = None
                    _t897 = _t900
                _t894 = _t897
            _t891 = _t894
        return _t891

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        self.consume_literal('(')
        self.consume_literal('or')
        self.consume_literal(')')
        return logic_pb2.OrMonoid()

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        self.consume_literal('(')
        self.consume_literal('min')
        _t903 = self.parse_type()
        type230 = _t903
        self.consume_literal(')')
        _t904 = logic_pb2.MinMonoid(type=type230)
        return _t904

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        self.consume_literal('(')
        self.consume_literal('max')
        _t905 = self.parse_type()
        type231 = _t905
        self.consume_literal(')')
        _t906 = logic_pb2.MaxMonoid(type=type231)
        return _t906

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        self.consume_literal('(')
        self.consume_literal('sum')
        _t907 = self.parse_type()
        type232 = _t907
        self.consume_literal(')')
        _t908 = logic_pb2.SumMonoid(type=type232)
        return _t908

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal('(')
        self.consume_literal('monus')
        _t909 = self.parse_monoid()
        monoid233 = _t909
        _t910 = self.parse_relation_id()
        name234 = _t910
        _t911 = self.parse_abstraction_with_arity()
        abstraction_with_arity235 = _t911
        if self.match_lookahead_literal('(', 0):
            _t913 = self.parse_attrs()
            _t912 = _t913
        else:
            _t912 = None
        attrs236 = _t912
        self.consume_literal(')')
        abstraction = abstraction_with_arity235[0]
        arity = abstraction_with_arity235[1]
        _t914 = logic_pb2.MonusDef(monoid=monoid233, name=name234, body=abstraction, attrs=(attrs236 if attrs236 is not None else []), value_arity=arity)
        return _t914

    def parse_constraint(self) -> logic_pb2.Constraint:
        self.consume_literal('(')
        self.consume_literal('functional_dependency')
        _t915 = self.parse_relation_id()
        name237 = _t915
        _t916 = self.parse_abstraction()
        guard238 = _t916
        _t917 = self.parse_functional_dependency_keys()
        keys239 = _t917
        _t918 = self.parse_functional_dependency_values()
        values240 = _t918
        self.consume_literal(')')
        _t919 = logic_pb2.FunctionalDependency(guard=guard238, keys=keys239, values=values240)
        _t920 = logic_pb2.Constraint(name=name237, functional_dependency=_t919)
        return _t920

    def parse_functional_dependency_keys(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('keys')
        xs241 = []
        cond242 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond242:
            _t921 = self.parse_var()
            xs241.append(_t921)
            cond242 = self.match_lookahead_terminal('SYMBOL', 0)
        x243 = xs241
        self.consume_literal(')')
        return x243

    def parse_functional_dependency_values(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('values')
        xs244 = []
        cond245 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond245:
            _t922 = self.parse_var()
            xs244.append(_t922)
            cond245 = self.match_lookahead_terminal('SYMBOL', 0)
        x246 = xs244
        self.consume_literal(')')
        return x246

    def parse_data(self) -> logic_pb2.Data:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('rel_edb', 1):
                _t924 = 0
            else:
                if self.match_lookahead_literal('csv_data', 1):
                    _t925 = 2
                else:
                    _t925 = (self.match_lookahead_literal('betree_relation', 1) or -1)
                _t924 = _t925
            _t923 = _t924
        else:
            _t923 = -1
        prediction247 = _t923
        if prediction247 == 2:
            _t927 = self.parse_csv_data()
            value250 = _t927
            _t928 = logic_pb2.Data(csv_data=value250)
            _t926 = _t928
        else:
            if prediction247 == 1:
                _t930 = self.parse_betree_relation()
                value249 = _t930
                _t931 = logic_pb2.Data(betree_relation=value249)
                _t929 = _t931
            else:
                if prediction247 == 0:
                    _t933 = self.parse_rel_edb()
                    value248 = _t933
                    _t934 = logic_pb2.Data(rel_edb=value248)
                    _t932 = _t934
                else:
                    raise ParseError(f"{'Unexpected token in data'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t932 = None
                _t929 = _t932
            _t926 = _t929
        return _t926

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        self.consume_literal('(')
        self.consume_literal('rel_edb')
        _t935 = self.parse_relation_id()
        target_id251 = _t935
        _t936 = self.parse_rel_edb_path()
        path252 = _t936
        if self.match_lookahead_literal('[', 0):
            _t938 = self.parse_rel_edb_types()
            _t937 = _t938
        else:
            _t937 = None
        types253 = _t937
        self.consume_literal(')')
        _t939 = logic_pb2.RelEDB(target_id=target_id251, path=path252, types=(types253 if types253 is not None else []))
        return _t939

    def parse_rel_edb_path(self) -> list[str]:
        self.consume_literal('[')
        xs254 = []
        cond255 = self.match_lookahead_terminal('STRING', 0)
        while cond255:
            xs254.append(self.consume_terminal('STRING'))
            cond255 = self.match_lookahead_terminal('STRING', 0)
        x256 = xs254
        self.consume_literal(']')
        return x256

    def parse_rel_edb_types(self) -> list[logic_pb2.Type]:
        self.consume_literal('[')
        xs257 = []
        cond258 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond258:
            _t940 = self.parse_type()
            xs257.append(_t940)
            cond258 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        x259 = xs257
        self.consume_literal(']')
        return x259

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        _t941 = self.parse_be_tree_relation()
        x260 = _t941
        return x260

    def parse_be_tree_relation(self) -> logic_pb2.BeTreeRelation:
        self.consume_literal('(')
        self.consume_literal('betree_relation')
        _t942 = self.parse_relation_id()
        name261 = _t942
        _t943 = self.parse_be_tree_info()
        relation_info262 = _t943
        self.consume_literal(')')
        _t944 = logic_pb2.BeTreeRelation(name=name261, relation_info=relation_info262)
        return _t944

    def parse_be_tree_info(self) -> logic_pb2.BeTreeInfo:
        self.consume_literal('(')
        self.consume_literal('betree_info')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('key_types', 1)):
            _t946 = self.parse_be_tree_info_key_types()
            _t945 = _t946
        else:
            _t945 = None
        key_types263 = _t945
        if self.match_lookahead_literal('(', 0):
            _t948 = self.parse_be_tree_info_value_types()
            _t947 = _t948
        else:
            _t947 = None
        value_types264 = _t947
        _t949 = self.parse_config_dict()
        config_dict265 = _t949
        self.consume_literal(')')
        return self.construct_betree_info((key_types263 if key_types263 is not None else []), (value_types264 if value_types264 is not None else []), config_dict265)

    def parse_be_tree_info_key_types(self) -> list[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('key_types')
        xs266 = []
        cond267 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond267:
            _t950 = self.parse_type()
            xs266.append(_t950)
            cond267 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        x268 = xs266
        self.consume_literal(')')
        return x268

    def parse_be_tree_info_value_types(self) -> list[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('value_types')
        xs269 = []
        cond270 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond270:
            _t951 = self.parse_type()
            xs269.append(_t951)
            cond270 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        x271 = xs269
        self.consume_literal(')')
        return x271

    def parse_csv_data(self) -> logic_pb2.CSVData:
        _t952 = self.parse_csvdata()
        x272 = _t952
        return x272

    def parse_csvdata(self) -> logic_pb2.CSVData:
        self.consume_literal('(')
        self.consume_literal('csv_data')
        _t953 = self.parse_csvlocator()
        locator273 = _t953
        _t954 = self.parse_csv_config()
        config274 = _t954
        _t955 = self.parse_csv_columns()
        columns275 = _t955
        _t956 = self.parse_csv_asof()
        asof276 = _t956
        self.consume_literal(')')
        _t957 = logic_pb2.CSVData(locator=locator273, config=config274, columns=columns275, asof=asof276)
        return _t957

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        self.consume_literal('(')
        self.consume_literal('csv_locator')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('paths', 1)):
            _t959 = self.parse_csv_locator_paths()
            _t958 = _t959
        else:
            _t958 = None
        paths277 = _t958
        if self.match_lookahead_literal('(', 0):
            _t961 = self.parse_csv_locator_inline_data()
            _t960 = _t961
        else:
            _t960 = None
        inline_data278 = _t960
        self.consume_literal(')')
        _t962 = logic_pb2.CSVLocator(paths=(paths277 if paths277 is not None else []), inline_data=(inline_data278 if inline_data278 is not None else '').encode())
        return _t962

    def parse_csv_locator_paths(self) -> list[str]:
        self.consume_literal('(')
        self.consume_literal('paths')
        xs279 = []
        cond280 = self.match_lookahead_terminal('STRING', 0)
        while cond280:
            xs279.append(self.consume_terminal('STRING'))
            cond280 = self.match_lookahead_terminal('STRING', 0)
        x281 = xs279
        self.consume_literal(')')
        return x281

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal('(')
        self.consume_literal('inline_data')
        x282 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return x282

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        self.consume_literal('(')
        self.consume_literal('csv_config')
        _t963 = self.parse_config_dict()
        config_dict283 = _t963
        self.consume_literal(')')
        return self.construct_csv_config(config_dict283)

    def parse_csv_columns(self) -> list[logic_pb2.CSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs284 = []
        cond285 = self.match_lookahead_literal('(', 0)
        while cond285:
            _t964 = self.parse_csv_column()
            xs284.append(_t964)
            cond285 = self.match_lookahead_literal('(', 0)
        x286 = xs284
        self.consume_literal(')')
        return x286

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        column_name287 = self.consume_terminal('STRING')
        _t965 = self.parse_relation_id()
        target_id288 = _t965
        self.consume_literal('[')
        xs289 = []
        cond290 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond290:
            _t966 = self.parse_type()
            xs289.append(_t966)
            cond290 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types291 = xs289
        self.consume_literal(']')
        self.consume_literal(')')
        _t967 = logic_pb2.CSVColumn(column_name=column_name287, target_id=target_id288, types=types291)
        return _t967

    def parse_csv_asof(self) -> str:
        self.consume_literal('(')
        self.consume_literal('asof')
        x292 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return x292

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal('(')
        self.consume_literal('undefine')
        _t968 = self.parse_fragment_id()
        fragment_id293 = _t968
        self.consume_literal(')')
        _t969 = transactions_pb2.Undefine(fragment_id=fragment_id293)
        return _t969

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal('(')
        self.consume_literal('context')
        xs294 = []
        cond295 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        while cond295:
            _t970 = self.parse_relation_id()
            xs294.append(_t970)
            cond295 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        relations296 = xs294
        self.consume_literal(')')
        _t971 = transactions_pb2.Context(relations=relations296)
        return _t971

    def parse_epoch_reads(self) -> list[transactions_pb2.Read]:
        self.consume_literal('(')
        self.consume_literal('reads')
        xs297 = []
        cond298 = self.match_lookahead_literal('(', 0)
        while cond298:
            _t972 = self.parse_read()
            xs297.append(_t972)
            cond298 = self.match_lookahead_literal('(', 0)
        x299 = xs297
        self.consume_literal(')')
        return x299

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('what_if', 1):
                _t974 = 2
            else:
                if self.match_lookahead_literal('output', 1):
                    _t978 = 1
                else:
                    if self.match_lookahead_literal('export', 1):
                        _t979 = 4
                    else:
                        if self.match_lookahead_literal('demand', 1):
                            _t980 = 0
                        else:
                            if self.match_lookahead_literal('abort', 1):
                                _t981 = 3
                            else:
                                _t981 = -1
                            _t980 = _t981
                        _t979 = _t980
                    _t978 = _t979
                _t974 = _t978
            _t973 = _t974
        else:
            _t973 = -1
        prediction300 = _t973
        if prediction300 == 4:
            _t983 = self.parse_export()
            value305 = _t983
            _t984 = transactions_pb2.Read(export=value305)
            _t982 = _t984
        else:
            if prediction300 == 3:
                _t986 = self.parse_abort()
                value304 = _t986
                _t987 = transactions_pb2.Read(abort=value304)
                _t985 = _t987
            else:
                if prediction300 == 2:
                    _t989 = self.parse_what_if()
                    value303 = _t989
                    _t990 = transactions_pb2.Read(what_if=value303)
                    _t988 = _t990
                else:
                    if prediction300 == 1:
                        _t992 = self.parse_output()
                        value302 = _t992
                        _t993 = transactions_pb2.Read(output=value302)
                        _t991 = _t993
                    else:
                        if prediction300 == 0:
                            _t995 = self.parse_demand()
                            value301 = _t995
                            _t996 = transactions_pb2.Read(demand=value301)
                            _t994 = _t996
                        else:
                            raise ParseError(f"{'Unexpected token in read'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t994 = None
                        _t991 = _t994
                    _t988 = _t991
                _t985 = _t988
            _t982 = _t985
        return _t982

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal('(')
        self.consume_literal('demand')
        _t997 = self.parse_relation_id()
        relation_id306 = _t997
        self.consume_literal(')')
        _t998 = transactions_pb2.Demand(relation_id=relation_id306)
        return _t998

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal('(')
        self.consume_literal('output')
        if self.match_lookahead_terminal('COLON_SYMBOL', 0):
            _t1000 = self.parse_name()
            _t999 = _t1000
        else:
            _t999 = None
        name307 = _t999
        _t1001 = self.parse_relation_id()
        relation_id308 = _t1001
        self.consume_literal(')')
        _t1002 = transactions_pb2.Output(name=(name307 if name307 is not None else 'output'), relation_id=relation_id308)
        return _t1002

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal('(')
        self.consume_literal('what_if')
        _t1003 = self.parse_name()
        branch309 = _t1003
        _t1004 = self.parse_epoch()
        epoch310 = _t1004
        self.consume_literal(')')
        _t1005 = transactions_pb2.WhatIf(branch=branch309, epoch=epoch310)
        return _t1005

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal('(')
        self.consume_literal('abort')
        if self.match_lookahead_terminal('COLON_SYMBOL', 0):
            _t1007 = self.parse_name()
            _t1006 = _t1007
        else:
            _t1006 = None
        name311 = _t1006
        _t1008 = self.parse_relation_id()
        relation_id312 = _t1008
        self.consume_literal(')')
        _t1009 = transactions_pb2.Abort(name=(name311 if name311 is not None else 'abort'), relation_id=relation_id312)
        return _t1009

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal('(')
        self.consume_literal('export')
        _t1010 = self.parse_export_csv_config()
        config313 = _t1010
        self.consume_literal(')')
        _t1011 = transactions_pb2.Export(csv_config=config313)
        return _t1011

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal('(')
        self.consume_literal('export_csv_config')
        _t1012 = self.parse_export_csv_path()
        path314 = _t1012
        _t1013 = self.parse_export_csv_columns()
        columns315 = _t1013
        _t1014 = self.parse_config_dict()
        config316 = _t1014
        self.consume_literal(')')
        _t1015 = self.export_csv_config(path314, columns315, config316)
        return _t1015

    def parse_export_csv_path(self) -> str:
        self.consume_literal('(')
        self.consume_literal('path')
        x317 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return x317

    def parse_export_csv_columns(self) -> list[transactions_pb2.ExportCSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs318 = []
        cond319 = self.match_lookahead_literal('(', 0)
        while cond319:
            _t1016 = self.parse_export_csv_column()
            xs318.append(_t1016)
            cond319 = self.match_lookahead_literal('(', 0)
        x320 = xs318
        self.consume_literal(')')
        return x320

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        name321 = self.consume_terminal('STRING')
        _t1017 = self.parse_relation_id()
        relation_id322 = _t1017
        self.consume_literal(')')
        _t1018 = transactions_pb2.ExportCSVColumn(column_name=name321, column_data=relation_id322)
        return _t1018


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
