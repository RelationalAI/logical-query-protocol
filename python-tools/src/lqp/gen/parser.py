"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.


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
        val = int(n)
        if val < -(1 << 63) or val >= (1 << 63):
            raise ParseError(f'Integer literal out of 64-bit range: {n}')
        return val

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
        if uint128_val < 0 or uint128_val >= (1 << 128):
            raise ParseError(f'UInt128 literal out of range: {u}')
        low = uint128_val & 0xFFFFFFFFFFFFFFFF
        high = (uint128_val >> 64) & 0xFFFFFFFFFFFFFFFF
        return logic_pb2.UInt128Value(low=low, high=high)

    @staticmethod
    def scan_int128(u: str) -> Any:
        """Parse INT128 token."""
        u = u[:-4]  # Remove the 'i128' suffix
        int128_val = int(u)
        if int128_val < -(1 << 127) or int128_val >= (1 << 127):
            raise ParseError(f'Int128 literal out of range: {u}')
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

    def relation_id_to_string(self, msg) -> str:
        """Stub: only used in pretty printer."""
        raise NotImplementedError("relation_id_to_string is only available in PrettyPrinter")

    def relation_id_to_uint128(self, msg):
        """Stub: only used in pretty printer."""
        raise NotImplementedError("relation_id_to_uint128 is only available in PrettyPrinter")

    # --- Helper functions ---

    def default_configure(self) -> transactions_pb2.Configure:
        _t945 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t945
        _t946 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t946

    def _try_extract_value_int64(self, value: Optional[logic_pb2.Value]) -> Optional[int]:
        
        if value is not None:
            assert value is not None
            _t947 = value.HasField('int_value')
        else:
            _t947 = False
        if _t947:
            assert value is not None
            return value.int_value
        return None

    def _try_extract_value_uint128(self, value: Optional[logic_pb2.Value]) -> Optional[logic_pb2.UInt128Value]:
        
        if value is not None:
            assert value is not None
            _t948 = value.HasField('uint128_value')
        else:
            _t948 = False
        if _t948:
            assert value is not None
            return value.uint128_value
        return None

    def export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t949 = self._extract_value_int64(config.get('partition_size'), 0)
        partition_size = _t949
        _t950 = self._extract_value_string(config.get('compression'), '')
        compression = _t950
        _t951 = self._extract_value_boolean(config.get('syntax_header_row'), True)
        syntax_header_row = _t951
        _t952 = self._extract_value_string(config.get('syntax_missing_string'), '')
        syntax_missing_string = _t952
        _t953 = self._extract_value_string(config.get('syntax_delim'), ',')
        syntax_delim = _t953
        _t954 = self._extract_value_string(config.get('syntax_quotechar'), '"')
        syntax_quotechar = _t954
        _t955 = self._extract_value_string(config.get('syntax_escapechar'), '\\')
        syntax_escapechar = _t955
        _t956 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t956

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t957 = self._try_extract_value_float64(config.get('betree_config_epsilon'))
        epsilon = _t957
        _t958 = self._try_extract_value_int64(config.get('betree_config_max_pivots'))
        max_pivots = _t958
        _t959 = self._try_extract_value_int64(config.get('betree_config_max_deltas'))
        max_deltas = _t959
        _t960 = self._try_extract_value_int64(config.get('betree_config_max_leaf'))
        max_leaf = _t960
        _t961 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t961
        _t962 = self._try_extract_value_uint128(config.get('betree_locator_root_pageid'))
        root_pageid = _t962
        _t963 = self._try_extract_value_bytes(config.get('betree_locator_inline_data'))
        inline_data = _t963
        _t964 = self._try_extract_value_int64(config.get('betree_locator_element_count'))
        element_count = _t964
        _t965 = self._try_extract_value_int64(config.get('betree_locator_tree_height'))
        tree_height = _t965
        _t966 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t966
        _t967 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t967

    def _extract_value_string(self, value: Optional[logic_pb2.Value], default: str) -> str:
        
        if value is not None:
            assert value is not None
            _t968 = value.HasField('string_value')
        else:
            _t968 = False
        if _t968:
            assert value is not None
            return value.string_value
        return default

    def _extract_value_string_list(self, value: Optional[logic_pb2.Value], default: Sequence[str]) -> Sequence[str]:
        
        if value is not None:
            assert value is not None
            _t969 = value.HasField('string_value')
        else:
            _t969 = False
        if _t969:
            assert value is not None
            return [value.string_value]
        return default

    def _try_extract_value_float64(self, value: Optional[logic_pb2.Value]) -> Optional[float]:
        
        if value is not None:
            assert value is not None
            _t970 = value.HasField('float_value')
        else:
            _t970 = False
        if _t970:
            assert value is not None
            return value.float_value
        return None

    def _extract_value_int32(self, value: Optional[logic_pb2.Value], default: int) -> int:
        
        if value is not None:
            assert value is not None
            _t971 = value.HasField('int_value')
        else:
            _t971 = False
        if _t971:
            assert value is not None
            return int(value.int_value)
        return int(default)

    def _extract_value_boolean(self, value: Optional[logic_pb2.Value], default: bool) -> bool:
        
        if value is not None:
            assert value is not None
            _t972 = value.HasField('boolean_value')
        else:
            _t972 = False
        if _t972:
            assert value is not None
            return value.boolean_value
        return default

    def construct_configure(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.Configure:
        config = dict(config_dict)
        maintenance_level_val = config.get('ivm.maintenance_level')
        maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
        if (maintenance_level_val is not None and maintenance_level_val.HasField('string_value')):
            if maintenance_level_val.string_value == 'off':
                maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
            else:
                if maintenance_level_val.string_value == 'auto':
                    maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
                else:
                    if maintenance_level_val.string_value == 'all':
                        maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
                    else:
                        maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
        _t973 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t973
        _t974 = self._extract_value_int64(config.get('semantics_version'), 0)
        semantics_version = _t974
        _t975 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t975

    def _extract_value_int64(self, value: Optional[logic_pb2.Value], default: int) -> int:
        
        if value is not None:
            assert value is not None
            _t976 = value.HasField('int_value')
        else:
            _t976 = False
        if _t976:
            assert value is not None
            return value.int_value
        return default

    def _try_extract_value_bytes(self, value: Optional[logic_pb2.Value]) -> Optional[bytes]:
        
        if value is not None:
            assert value is not None
            _t977 = value.HasField('string_value')
        else:
            _t977 = False
        if _t977:
            assert value is not None
            return value.string_value.encode()
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t978 = self._extract_value_int32(config.get('csv_header_row'), 1)
        header_row = _t978
        _t979 = self._extract_value_int64(config.get('csv_skip'), 0)
        skip = _t979
        _t980 = self._extract_value_string(config.get('csv_new_line'), '')
        new_line = _t980
        _t981 = self._extract_value_string(config.get('csv_delimiter'), ',')
        delimiter = _t981
        _t982 = self._extract_value_string(config.get('csv_quotechar'), '"')
        quotechar = _t982
        _t983 = self._extract_value_string(config.get('csv_escapechar'), '"')
        escapechar = _t983
        _t984 = self._extract_value_string(config.get('csv_comment'), '')
        comment = _t984
        _t985 = self._extract_value_string_list(config.get('csv_missing_strings'), [])
        missing_strings = _t985
        _t986 = self._extract_value_string(config.get('csv_decimal_separator'), '.')
        decimal_separator = _t986
        _t987 = self._extract_value_string(config.get('csv_encoding'), 'utf-8')
        encoding = _t987
        _t988 = self._extract_value_string(config.get('csv_compression'), 'auto')
        compression = _t988
        _t989 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t989

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
        _t358 = self.default_configure()
        _t359 = transactions_pb2.Transaction(epochs=epochs5, configure=(configure0 if configure0 is not None else _t358), sync=sync1)
        return _t359

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal('(')
        self.consume_literal('configure')
        _t360 = self.parse_config_dict()
        config_dict6 = _t360
        self.consume_literal(')')
        _t361 = self.construct_configure(config_dict6)
        return _t361

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
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
                            _t368 = 1
                        else:
                            
                            if self.match_lookahead_literal('date', 1):
                                _t369 = 0
                            else:
                                _t369 = -1
                            _t368 = _t369
                        _t367 = _t368
                    else:
                        
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t370 = 5
                        else:
                            
                            if self.match_lookahead_terminal('STRING', 0):
                                _t371 = 2
                            else:
                                
                                if self.match_lookahead_terminal('INT128', 0):
                                    _t372 = 6
                                else:
                                    
                                    if self.match_lookahead_terminal('INT', 0):
                                        _t373 = 3
                                    else:
                                        
                                        if self.match_lookahead_terminal('FLOAT', 0):
                                            _t374 = 4
                                        else:
                                            
                                            if self.match_lookahead_terminal('DECIMAL', 0):
                                                _t375 = 7
                                            else:
                                                _t375 = -1
                                            _t374 = _t375
                                        _t373 = _t374
                                    _t372 = _t373
                                _t371 = _t372
                            _t370 = _t371
                        _t367 = _t370
                    _t366 = _t367
                _t365 = _t366
            _t364 = _t365
        prediction13 = _t364
        
        if prediction13 == 9:
            _t377 = self.parse_boolean_value()
            boolean_value22 = _t377
            _t378 = logic_pb2.Value(boolean_value=boolean_value22)
            _t376 = _t378
        else:
            
            if prediction13 == 8:
                self.consume_literal('missing')
                _t380 = logic_pb2.MissingValue()
                _t381 = logic_pb2.Value(missing_value=_t380)
                _t379 = _t381
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
                                            _t394 = _t397
                                        _t392 = _t394
                                    _t390 = _t392
                                _t388 = _t390
                            _t386 = _t388
                        _t384 = _t386
                    _t382 = _t384
                _t379 = _t382
            _t376 = _t379
        return _t376

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
            
            if self.match_lookahead_literal('false', 0):
                _t404 = 1
            else:
                _t404 = -1
            _t403 = _t404
        prediction33 = _t403
        
        if prediction33 == 1:
            self.consume_literal('false')
            _t405 = False
        else:
            
            if prediction33 == 0:
                self.consume_literal('true')
                _t406 = True
            else:
                raise ParseError(f"{'Unexpected token in boolean_value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t405 = _t406
        return _t405

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal('(')
        self.consume_literal('sync')
        xs34 = []
        cond35 = self.match_lookahead_literal(':', 0)
        while cond35:
            _t407 = self.parse_fragment_id()
            item36 = _t407
            xs34.append(item36)
            cond35 = self.match_lookahead_literal(':', 0)
        fragment_ids37 = xs34
        self.consume_literal(')')
        _t408 = transactions_pb2.Sync(fragments=fragment_ids37)
        return _t408

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        self.consume_literal(':')
        symbol38 = self.consume_terminal('SYMBOL')
        return fragments_pb2.FragmentId(id=symbol38.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal('(')
        self.consume_literal('epoch')
        
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('writes', 1)):
            _t410 = self.parse_epoch_writes()
            _t409 = _t410
        else:
            _t409 = None
        epoch_writes39 = _t409
        
        if self.match_lookahead_literal('(', 0):
            _t412 = self.parse_epoch_reads()
            _t411 = _t412
        else:
            _t411 = None
        epoch_reads40 = _t411
        self.consume_literal(')')
        _t413 = transactions_pb2.Epoch(writes=(epoch_writes39 if epoch_writes39 is not None else []), reads=(epoch_reads40 if epoch_reads40 is not None else []))
        return _t413

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal('(')
        self.consume_literal('writes')
        xs41 = []
        cond42 = self.match_lookahead_literal('(', 0)
        while cond42:
            _t414 = self.parse_write()
            item43 = _t414
            xs41.append(item43)
            cond42 = self.match_lookahead_literal('(', 0)
        writes44 = xs41
        self.consume_literal(')')
        return writes44

    def parse_write(self) -> transactions_pb2.Write:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('undefine', 1):
                _t416 = 1
            else:
                
                if self.match_lookahead_literal('define', 1):
                    _t417 = 0
                else:
                    
                    if self.match_lookahead_literal('context', 1):
                        _t418 = 2
                    else:
                        _t418 = -1
                    _t417 = _t418
                _t416 = _t417
            _t415 = _t416
        else:
            _t415 = -1
        prediction45 = _t415
        
        if prediction45 == 2:
            _t420 = self.parse_context()
            context48 = _t420
            _t421 = transactions_pb2.Write(context=context48)
            _t419 = _t421
        else:
            
            if prediction45 == 1:
                _t423 = self.parse_undefine()
                undefine47 = _t423
                _t424 = transactions_pb2.Write(undefine=undefine47)
                _t422 = _t424
            else:
                
                if prediction45 == 0:
                    _t426 = self.parse_define()
                    define46 = _t426
                    _t427 = transactions_pb2.Write(define=define46)
                    _t425 = _t427
                else:
                    raise ParseError(f"{'Unexpected token in write'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t422 = _t425
            _t419 = _t422
        return _t419

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal('(')
        self.consume_literal('define')
        _t428 = self.parse_fragment()
        fragment49 = _t428
        self.consume_literal(')')
        _t429 = transactions_pb2.Define(fragment=fragment49)
        return _t429

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal('(')
        self.consume_literal('fragment')
        _t430 = self.parse_new_fragment_id()
        new_fragment_id50 = _t430
        xs51 = []
        cond52 = self.match_lookahead_literal('(', 0)
        while cond52:
            _t431 = self.parse_declaration()
            item53 = _t431
            xs51.append(item53)
            cond52 = self.match_lookahead_literal('(', 0)
        declarations54 = xs51
        self.consume_literal(')')
        return self.construct_fragment(new_fragment_id50, declarations54)

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        _t432 = self.parse_fragment_id()
        fragment_id55 = _t432
        self.start_fragment(fragment_id55)
        return fragment_id55

    def parse_declaration(self) -> logic_pb2.Declaration:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('rel_edb', 1):
                _t434 = 3
            else:
                
                if self.match_lookahead_literal('functional_dependency', 1):
                    _t435 = 2
                else:
                    
                    if self.match_lookahead_literal('def', 1):
                        _t436 = 0
                    else:
                        
                        if self.match_lookahead_literal('csv_data', 1):
                            _t437 = 3
                        else:
                            
                            if self.match_lookahead_literal('betree_relation', 1):
                                _t438 = 3
                            else:
                                
                                if self.match_lookahead_literal('algorithm', 1):
                                    _t439 = 1
                                else:
                                    _t439 = -1
                                _t438 = _t439
                            _t437 = _t438
                        _t436 = _t437
                    _t435 = _t436
                _t434 = _t435
            _t433 = _t434
        else:
            _t433 = -1
        prediction56 = _t433
        
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
            
            if self.match_lookahead_terminal('UINT128', 0):
                _t458 = 1
            else:
                _t458 = -1
            _t457 = _t458
        prediction64 = _t457
        
        if prediction64 == 1:
            uint12866 = self.consume_terminal('UINT128')
            _t459 = logic_pb2.RelationId(id_low=uint12866.low, id_high=uint12866.high)
        else:
            
            if prediction64 == 0:
                self.consume_literal(':')
                symbol65 = self.consume_terminal('SYMBOL')
                _t460 = self.relation_id_from_string(symbol65)
            else:
                raise ParseError(f"{'Unexpected token in relation_id'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t459 = _t460
        return _t459

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal('(')
        _t461 = self.parse_bindings()
        bindings67 = _t461
        _t462 = self.parse_formula()
        formula68 = _t462
        self.consume_literal(')')
        _t463 = logic_pb2.Abstraction(vars=(list(bindings67[0]) + list(bindings67[1] if bindings67[1] is not None else [])), value=formula68)
        return _t463

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal('[')
        xs69 = []
        cond70 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond70:
            _t464 = self.parse_binding()
            item71 = _t464
            xs69.append(item71)
            cond70 = self.match_lookahead_terminal('SYMBOL', 0)
        bindings72 = xs69
        
        if self.match_lookahead_literal('|', 0):
            _t466 = self.parse_value_bindings()
            _t465 = _t466
        else:
            _t465 = None
        value_bindings73 = _t465
        self.consume_literal(']')
        return (bindings72, (value_bindings73 if value_bindings73 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol74 = self.consume_terminal('SYMBOL')
        self.consume_literal('::')
        _t467 = self.parse_type()
        type75 = _t467
        _t468 = logic_pb2.Var(name=symbol74)
        _t469 = logic_pb2.Binding(var=_t468, type=type75)
        return _t469

    def parse_type(self) -> logic_pb2.Type:
        
        if self.match_lookahead_literal('UNKNOWN', 0):
            _t470 = 0
        else:
            
            if self.match_lookahead_literal('UINT128', 0):
                _t471 = 4
            else:
                
                if self.match_lookahead_literal('STRING', 0):
                    _t472 = 1
                else:
                    
                    if self.match_lookahead_literal('MISSING', 0):
                        _t473 = 8
                    else:
                        
                        if self.match_lookahead_literal('INT128', 0):
                            _t474 = 5
                        else:
                            
                            if self.match_lookahead_literal('INT', 0):
                                _t475 = 2
                            else:
                                
                                if self.match_lookahead_literal('FLOAT', 0):
                                    _t476 = 3
                                else:
                                    
                                    if self.match_lookahead_literal('DATETIME', 0):
                                        _t477 = 7
                                    else:
                                        
                                        if self.match_lookahead_literal('DATE', 0):
                                            _t478 = 6
                                        else:
                                            
                                            if self.match_lookahead_literal('BOOLEAN', 0):
                                                _t479 = 10
                                            else:
                                                
                                                if self.match_lookahead_literal('(', 0):
                                                    _t480 = 9
                                                else:
                                                    _t480 = -1
                                                _t479 = _t480
                                            _t478 = _t479
                                        _t477 = _t478
                                    _t476 = _t477
                                _t475 = _t476
                            _t474 = _t475
                        _t473 = _t474
                    _t472 = _t473
                _t471 = _t472
            _t470 = _t471
        prediction76 = _t470
        
        if prediction76 == 10:
            _t482 = self.parse_boolean_type()
            boolean_type87 = _t482
            _t483 = logic_pb2.Type(boolean_type=boolean_type87)
            _t481 = _t483
        else:
            
            if prediction76 == 9:
                _t485 = self.parse_decimal_type()
                decimal_type86 = _t485
                _t486 = logic_pb2.Type(decimal_type=decimal_type86)
                _t484 = _t486
            else:
                
                if prediction76 == 8:
                    _t488 = self.parse_missing_type()
                    missing_type85 = _t488
                    _t489 = logic_pb2.Type(missing_type=missing_type85)
                    _t487 = _t489
                else:
                    
                    if prediction76 == 7:
                        _t491 = self.parse_datetime_type()
                        datetime_type84 = _t491
                        _t492 = logic_pb2.Type(datetime_type=datetime_type84)
                        _t490 = _t492
                    else:
                        
                        if prediction76 == 6:
                            _t494 = self.parse_date_type()
                            date_type83 = _t494
                            _t495 = logic_pb2.Type(date_type=date_type83)
                            _t493 = _t495
                        else:
                            
                            if prediction76 == 5:
                                _t497 = self.parse_int128_type()
                                int128_type82 = _t497
                                _t498 = logic_pb2.Type(int128_type=int128_type82)
                                _t496 = _t498
                            else:
                                
                                if prediction76 == 4:
                                    _t500 = self.parse_uint128_type()
                                    uint128_type81 = _t500
                                    _t501 = logic_pb2.Type(uint128_type=uint128_type81)
                                    _t499 = _t501
                                else:
                                    
                                    if prediction76 == 3:
                                        _t503 = self.parse_float_type()
                                        float_type80 = _t503
                                        _t504 = logic_pb2.Type(float_type=float_type80)
                                        _t502 = _t504
                                    else:
                                        
                                        if prediction76 == 2:
                                            _t506 = self.parse_int_type()
                                            int_type79 = _t506
                                            _t507 = logic_pb2.Type(int_type=int_type79)
                                            _t505 = _t507
                                        else:
                                            
                                            if prediction76 == 1:
                                                _t509 = self.parse_string_type()
                                                string_type78 = _t509
                                                _t510 = logic_pb2.Type(string_type=string_type78)
                                                _t508 = _t510
                                            else:
                                                
                                                if prediction76 == 0:
                                                    _t512 = self.parse_unspecified_type()
                                                    unspecified_type77 = _t512
                                                    _t513 = logic_pb2.Type(unspecified_type=unspecified_type77)
                                                    _t511 = _t513
                                                else:
                                                    raise ParseError(f"{'Unexpected token in type'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t508 = _t511
                                            _t505 = _t508
                                        _t502 = _t505
                                    _t499 = _t502
                                _t496 = _t499
                            _t493 = _t496
                        _t490 = _t493
                    _t487 = _t490
                _t484 = _t487
            _t481 = _t484
        return _t481

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        self.consume_literal('UNKNOWN')
        _t514 = logic_pb2.UnspecifiedType()
        return _t514

    def parse_string_type(self) -> logic_pb2.StringType:
        self.consume_literal('STRING')
        _t515 = logic_pb2.StringType()
        return _t515

    def parse_int_type(self) -> logic_pb2.IntType:
        self.consume_literal('INT')
        _t516 = logic_pb2.IntType()
        return _t516

    def parse_float_type(self) -> logic_pb2.FloatType:
        self.consume_literal('FLOAT')
        _t517 = logic_pb2.FloatType()
        return _t517

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        self.consume_literal('UINT128')
        _t518 = logic_pb2.UInt128Type()
        return _t518

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        self.consume_literal('INT128')
        _t519 = logic_pb2.Int128Type()
        return _t519

    def parse_date_type(self) -> logic_pb2.DateType:
        self.consume_literal('DATE')
        _t520 = logic_pb2.DateType()
        return _t520

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        self.consume_literal('DATETIME')
        _t521 = logic_pb2.DateTimeType()
        return _t521

    def parse_missing_type(self) -> logic_pb2.MissingType:
        self.consume_literal('MISSING')
        _t522 = logic_pb2.MissingType()
        return _t522

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        self.consume_literal('(')
        self.consume_literal('DECIMAL')
        int88 = self.consume_terminal('INT')
        int_389 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t523 = logic_pb2.DecimalType(precision=int(int88), scale=int(int_389))
        return _t523

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal('BOOLEAN')
        _t524 = logic_pb2.BooleanType()
        return _t524

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal('|')
        xs90 = []
        cond91 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond91:
            _t525 = self.parse_binding()
            item92 = _t525
            xs90.append(item92)
            cond91 = self.match_lookahead_terminal('SYMBOL', 0)
        bindings93 = xs90
        return bindings93

    def parse_formula(self) -> logic_pb2.Formula:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('true', 1):
                _t527 = 0
            else:
                
                if self.match_lookahead_literal('relatom', 1):
                    _t528 = 11
                else:
                    
                    if self.match_lookahead_literal('reduce', 1):
                        _t529 = 3
                    else:
                        
                        if self.match_lookahead_literal('primitive', 1):
                            _t530 = 10
                        else:
                            
                            if self.match_lookahead_literal('pragma', 1):
                                _t531 = 9
                            else:
                                
                                if self.match_lookahead_literal('or', 1):
                                    _t532 = 5
                                else:
                                    
                                    if self.match_lookahead_literal('not', 1):
                                        _t533 = 6
                                    else:
                                        
                                        if self.match_lookahead_literal('ffi', 1):
                                            _t534 = 7
                                        else:
                                            
                                            if self.match_lookahead_literal('false', 1):
                                                _t535 = 1
                                            else:
                                                
                                                if self.match_lookahead_literal('exists', 1):
                                                    _t536 = 2
                                                else:
                                                    
                                                    if self.match_lookahead_literal('cast', 1):
                                                        _t537 = 12
                                                    else:
                                                        
                                                        if self.match_lookahead_literal('atom', 1):
                                                            _t538 = 8
                                                        else:
                                                            
                                                            if self.match_lookahead_literal('and', 1):
                                                                _t539 = 4
                                                            else:
                                                                
                                                                if self.match_lookahead_literal('>=', 1):
                                                                    _t540 = 10
                                                                else:
                                                                    
                                                                    if self.match_lookahead_literal('>', 1):
                                                                        _t541 = 10
                                                                    else:
                                                                        
                                                                        if self.match_lookahead_literal('=', 1):
                                                                            _t542 = 10
                                                                        else:
                                                                            
                                                                            if self.match_lookahead_literal('<=', 1):
                                                                                _t543 = 10
                                                                            else:
                                                                                
                                                                                if self.match_lookahead_literal('<', 1):
                                                                                    _t544 = 10
                                                                                else:
                                                                                    
                                                                                    if self.match_lookahead_literal('/', 1):
                                                                                        _t545 = 10
                                                                                    else:
                                                                                        
                                                                                        if self.match_lookahead_literal('-', 1):
                                                                                            _t546 = 10
                                                                                        else:
                                                                                            
                                                                                            if self.match_lookahead_literal('+', 1):
                                                                                                _t547 = 10
                                                                                            else:
                                                                                                
                                                                                                if self.match_lookahead_literal('*', 1):
                                                                                                    _t548 = 10
                                                                                                else:
                                                                                                    _t548 = -1
                                                                                                _t547 = _t548
                                                                                            _t546 = _t547
                                                                                        _t545 = _t546
                                                                                    _t544 = _t545
                                                                                _t543 = _t544
                                                                            _t542 = _t543
                                                                        _t541 = _t542
                                                                    _t540 = _t541
                                                                _t539 = _t540
                                                            _t538 = _t539
                                                        _t537 = _t538
                                                    _t536 = _t537
                                                _t535 = _t536
                                            _t534 = _t535
                                        _t533 = _t534
                                    _t532 = _t533
                                _t531 = _t532
                            _t530 = _t531
                        _t529 = _t530
                    _t528 = _t529
                _t527 = _t528
            _t526 = _t527
        else:
            _t526 = -1
        prediction94 = _t526
        
        if prediction94 == 12:
            _t550 = self.parse_cast()
            cast107 = _t550
            _t551 = logic_pb2.Formula(cast=cast107)
            _t549 = _t551
        else:
            
            if prediction94 == 11:
                _t553 = self.parse_rel_atom()
                rel_atom106 = _t553
                _t554 = logic_pb2.Formula(rel_atom=rel_atom106)
                _t552 = _t554
            else:
                
                if prediction94 == 10:
                    _t556 = self.parse_primitive()
                    primitive105 = _t556
                    _t557 = logic_pb2.Formula(primitive=primitive105)
                    _t555 = _t557
                else:
                    
                    if prediction94 == 9:
                        _t559 = self.parse_pragma()
                        pragma104 = _t559
                        _t560 = logic_pb2.Formula(pragma=pragma104)
                        _t558 = _t560
                    else:
                        
                        if prediction94 == 8:
                            _t562 = self.parse_atom()
                            atom103 = _t562
                            _t563 = logic_pb2.Formula(atom=atom103)
                            _t561 = _t563
                        else:
                            
                            if prediction94 == 7:
                                _t565 = self.parse_ffi()
                                ffi102 = _t565
                                _t566 = logic_pb2.Formula(ffi=ffi102)
                                _t564 = _t566
                            else:
                                
                                if prediction94 == 6:
                                    _t568 = self.parse_not()
                                    not101 = _t568
                                    _t569 = logic_pb2.Formula()
                                    getattr(_t569, 'not').CopyFrom(not101)
                                    _t567 = _t569
                                else:
                                    
                                    if prediction94 == 5:
                                        _t571 = self.parse_disjunction()
                                        disjunction100 = _t571
                                        _t572 = logic_pb2.Formula(disjunction=disjunction100)
                                        _t570 = _t572
                                    else:
                                        
                                        if prediction94 == 4:
                                            _t574 = self.parse_conjunction()
                                            conjunction99 = _t574
                                            _t575 = logic_pb2.Formula(conjunction=conjunction99)
                                            _t573 = _t575
                                        else:
                                            
                                            if prediction94 == 3:
                                                _t577 = self.parse_reduce()
                                                reduce98 = _t577
                                                _t578 = logic_pb2.Formula(reduce=reduce98)
                                                _t576 = _t578
                                            else:
                                                
                                                if prediction94 == 2:
                                                    _t580 = self.parse_exists()
                                                    exists97 = _t580
                                                    _t581 = logic_pb2.Formula(exists=exists97)
                                                    _t579 = _t581
                                                else:
                                                    
                                                    if prediction94 == 1:
                                                        _t583 = self.parse_false()
                                                        false96 = _t583
                                                        _t584 = logic_pb2.Formula(disjunction=false96)
                                                        _t582 = _t584
                                                    else:
                                                        
                                                        if prediction94 == 0:
                                                            _t586 = self.parse_true()
                                                            true95 = _t586
                                                            _t587 = logic_pb2.Formula(conjunction=true95)
                                                            _t585 = _t587
                                                        else:
                                                            raise ParseError(f"{'Unexpected token in formula'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t582 = _t585
                                                    _t579 = _t582
                                                _t576 = _t579
                                            _t573 = _t576
                                        _t570 = _t573
                                    _t567 = _t570
                                _t564 = _t567
                            _t561 = _t564
                        _t558 = _t561
                    _t555 = _t558
                _t552 = _t555
            _t549 = _t552
        return _t549

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('true')
        self.consume_literal(')')
        _t588 = logic_pb2.Conjunction(args=[])
        return _t588

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('false')
        self.consume_literal(')')
        _t589 = logic_pb2.Disjunction(args=[])
        return _t589

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal('(')
        self.consume_literal('exists')
        _t590 = self.parse_bindings()
        bindings108 = _t590
        _t591 = self.parse_formula()
        formula109 = _t591
        self.consume_literal(')')
        _t592 = logic_pb2.Abstraction(vars=(list(bindings108[0]) + list(bindings108[1] if bindings108[1] is not None else [])), value=formula109)
        _t593 = logic_pb2.Exists(body=_t592)
        return _t593

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal('(')
        self.consume_literal('reduce')
        _t594 = self.parse_abstraction()
        abstraction110 = _t594
        _t595 = self.parse_abstraction()
        abstraction_3111 = _t595
        _t596 = self.parse_terms()
        terms112 = _t596
        self.consume_literal(')')
        _t597 = logic_pb2.Reduce(op=abstraction110, body=abstraction_3111, terms=terms112)
        return _t597

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal('(')
        self.consume_literal('terms')
        xs113 = []
        cond114 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond114:
            _t598 = self.parse_term()
            item115 = _t598
            xs113.append(item115)
            cond114 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms116 = xs113
        self.consume_literal(')')
        return terms116

    def parse_term(self) -> logic_pb2.Term:
        
        if self.match_lookahead_literal('true', 0):
            _t599 = 1
        else:
            
            if self.match_lookahead_literal('missing', 0):
                _t600 = 1
            else:
                
                if self.match_lookahead_literal('false', 0):
                    _t601 = 1
                else:
                    
                    if self.match_lookahead_literal('(', 0):
                        _t602 = 1
                    else:
                        
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t603 = 1
                        else:
                            
                            if self.match_lookahead_terminal('SYMBOL', 0):
                                _t604 = 0
                            else:
                                
                                if self.match_lookahead_terminal('STRING', 0):
                                    _t605 = 1
                                else:
                                    
                                    if self.match_lookahead_terminal('INT128', 0):
                                        _t606 = 1
                                    else:
                                        
                                        if self.match_lookahead_terminal('INT', 0):
                                            _t607 = 1
                                        else:
                                            
                                            if self.match_lookahead_terminal('FLOAT', 0):
                                                _t608 = 1
                                            else:
                                                
                                                if self.match_lookahead_terminal('DECIMAL', 0):
                                                    _t609 = 1
                                                else:
                                                    _t609 = -1
                                                _t608 = _t609
                                            _t607 = _t608
                                        _t606 = _t607
                                    _t605 = _t606
                                _t604 = _t605
                            _t603 = _t604
                        _t602 = _t603
                    _t601 = _t602
                _t600 = _t601
            _t599 = _t600
        prediction117 = _t599
        
        if prediction117 == 1:
            _t611 = self.parse_constant()
            constant119 = _t611
            _t612 = logic_pb2.Term(constant=constant119)
            _t610 = _t612
        else:
            
            if prediction117 == 0:
                _t614 = self.parse_var()
                var118 = _t614
                _t615 = logic_pb2.Term(var=var118)
                _t613 = _t615
            else:
                raise ParseError(f"{'Unexpected token in term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t610 = _t613
        return _t610

    def parse_var(self) -> logic_pb2.Var:
        symbol120 = self.consume_terminal('SYMBOL')
        _t616 = logic_pb2.Var(name=symbol120)
        return _t616

    def parse_constant(self) -> logic_pb2.Value:
        _t617 = self.parse_value()
        value121 = _t617
        return value121

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('and')
        xs122 = []
        cond123 = self.match_lookahead_literal('(', 0)
        while cond123:
            _t618 = self.parse_formula()
            item124 = _t618
            xs122.append(item124)
            cond123 = self.match_lookahead_literal('(', 0)
        formulas125 = xs122
        self.consume_literal(')')
        _t619 = logic_pb2.Conjunction(args=formulas125)
        return _t619

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('or')
        xs126 = []
        cond127 = self.match_lookahead_literal('(', 0)
        while cond127:
            _t620 = self.parse_formula()
            item128 = _t620
            xs126.append(item128)
            cond127 = self.match_lookahead_literal('(', 0)
        formulas129 = xs126
        self.consume_literal(')')
        _t621 = logic_pb2.Disjunction(args=formulas129)
        return _t621

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal('(')
        self.consume_literal('not')
        _t622 = self.parse_formula()
        formula130 = _t622
        self.consume_literal(')')
        _t623 = logic_pb2.Not(arg=formula130)
        return _t623

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal('(')
        self.consume_literal('ffi')
        _t624 = self.parse_name()
        name131 = _t624
        _t625 = self.parse_ffi_args()
        ffi_args132 = _t625
        _t626 = self.parse_terms()
        terms133 = _t626
        self.consume_literal(')')
        _t627 = logic_pb2.FFI(name=name131, args=ffi_args132, terms=terms133)
        return _t627

    def parse_name(self) -> str:
        self.consume_literal(':')
        symbol134 = self.consume_terminal('SYMBOL')
        return symbol134

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal('(')
        self.consume_literal('args')
        xs135 = []
        cond136 = self.match_lookahead_literal('(', 0)
        while cond136:
            _t628 = self.parse_abstraction()
            item137 = _t628
            xs135.append(item137)
            cond136 = self.match_lookahead_literal('(', 0)
        abstractions138 = xs135
        self.consume_literal(')')
        return abstractions138

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal('(')
        self.consume_literal('atom')
        _t629 = self.parse_relation_id()
        relation_id139 = _t629
        xs140 = []
        cond141 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond141:
            _t630 = self.parse_term()
            item142 = _t630
            xs140.append(item142)
            cond141 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms143 = xs140
        self.consume_literal(')')
        _t631 = logic_pb2.Atom(name=relation_id139, terms=terms143)
        return _t631

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal('(')
        self.consume_literal('pragma')
        _t632 = self.parse_name()
        name144 = _t632
        xs145 = []
        cond146 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond146:
            _t633 = self.parse_term()
            item147 = _t633
            xs145.append(item147)
            cond146 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms148 = xs145
        self.consume_literal(')')
        _t634 = logic_pb2.Pragma(name=name144, terms=terms148)
        return _t634

    def parse_primitive(self) -> logic_pb2.Primitive:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('primitive', 1):
                _t636 = 9
            else:
                
                if self.match_lookahead_literal('>=', 1):
                    _t637 = 4
                else:
                    
                    if self.match_lookahead_literal('>', 1):
                        _t638 = 3
                    else:
                        
                        if self.match_lookahead_literal('=', 1):
                            _t639 = 0
                        else:
                            
                            if self.match_lookahead_literal('<=', 1):
                                _t640 = 2
                            else:
                                
                                if self.match_lookahead_literal('<', 1):
                                    _t641 = 1
                                else:
                                    
                                    if self.match_lookahead_literal('/', 1):
                                        _t642 = 8
                                    else:
                                        
                                        if self.match_lookahead_literal('-', 1):
                                            _t643 = 6
                                        else:
                                            
                                            if self.match_lookahead_literal('+', 1):
                                                _t644 = 5
                                            else:
                                                
                                                if self.match_lookahead_literal('*', 1):
                                                    _t645 = 7
                                                else:
                                                    _t645 = -1
                                                _t644 = _t645
                                            _t643 = _t644
                                        _t642 = _t643
                                    _t641 = _t642
                                _t640 = _t641
                            _t639 = _t640
                        _t638 = _t639
                    _t637 = _t638
                _t636 = _t637
            _t635 = _t636
        else:
            _t635 = -1
        prediction149 = _t635
        
        if prediction149 == 9:
            self.consume_literal('(')
            self.consume_literal('primitive')
            _t647 = self.parse_name()
            name159 = _t647
            xs160 = []
            cond161 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            while cond161:
                _t648 = self.parse_rel_term()
                item162 = _t648
                xs160.append(item162)
                cond161 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            rel_terms163 = xs160
            self.consume_literal(')')
            _t649 = logic_pb2.Primitive(name=name159, terms=rel_terms163)
            _t646 = _t649
        else:
            
            if prediction149 == 8:
                _t651 = self.parse_divide()
                divide158 = _t651
                _t650 = divide158
            else:
                
                if prediction149 == 7:
                    _t653 = self.parse_multiply()
                    multiply157 = _t653
                    _t652 = multiply157
                else:
                    
                    if prediction149 == 6:
                        _t655 = self.parse_minus()
                        minus156 = _t655
                        _t654 = minus156
                    else:
                        
                        if prediction149 == 5:
                            _t657 = self.parse_add()
                            add155 = _t657
                            _t656 = add155
                        else:
                            
                            if prediction149 == 4:
                                _t659 = self.parse_gt_eq()
                                gt_eq154 = _t659
                                _t658 = gt_eq154
                            else:
                                
                                if prediction149 == 3:
                                    _t661 = self.parse_gt()
                                    gt153 = _t661
                                    _t660 = gt153
                                else:
                                    
                                    if prediction149 == 2:
                                        _t663 = self.parse_lt_eq()
                                        lt_eq152 = _t663
                                        _t662 = lt_eq152
                                    else:
                                        
                                        if prediction149 == 1:
                                            _t665 = self.parse_lt()
                                            lt151 = _t665
                                            _t664 = lt151
                                        else:
                                            
                                            if prediction149 == 0:
                                                _t667 = self.parse_eq()
                                                eq150 = _t667
                                                _t666 = eq150
                                            else:
                                                raise ParseError(f"{'Unexpected token in primitive'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t664 = _t666
                                        _t662 = _t664
                                    _t660 = _t662
                                _t658 = _t660
                            _t656 = _t658
                        _t654 = _t656
                    _t652 = _t654
                _t650 = _t652
            _t646 = _t650
        return _t646

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('=')
        _t668 = self.parse_term()
        term164 = _t668
        _t669 = self.parse_term()
        term_3165 = _t669
        self.consume_literal(')')
        _t670 = logic_pb2.RelTerm(term=term164)
        _t671 = logic_pb2.RelTerm(term=term_3165)
        _t672 = logic_pb2.Primitive(name='rel_primitive_eq', terms=[_t670, _t671])
        return _t672

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<')
        _t673 = self.parse_term()
        term166 = _t673
        _t674 = self.parse_term()
        term_3167 = _t674
        self.consume_literal(')')
        _t675 = logic_pb2.RelTerm(term=term166)
        _t676 = logic_pb2.RelTerm(term=term_3167)
        _t677 = logic_pb2.Primitive(name='rel_primitive_lt_monotype', terms=[_t675, _t676])
        return _t677

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<=')
        _t678 = self.parse_term()
        term168 = _t678
        _t679 = self.parse_term()
        term_3169 = _t679
        self.consume_literal(')')
        _t680 = logic_pb2.RelTerm(term=term168)
        _t681 = logic_pb2.RelTerm(term=term_3169)
        _t682 = logic_pb2.Primitive(name='rel_primitive_lt_eq_monotype', terms=[_t680, _t681])
        return _t682

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>')
        _t683 = self.parse_term()
        term170 = _t683
        _t684 = self.parse_term()
        term_3171 = _t684
        self.consume_literal(')')
        _t685 = logic_pb2.RelTerm(term=term170)
        _t686 = logic_pb2.RelTerm(term=term_3171)
        _t687 = logic_pb2.Primitive(name='rel_primitive_gt_monotype', terms=[_t685, _t686])
        return _t687

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>=')
        _t688 = self.parse_term()
        term172 = _t688
        _t689 = self.parse_term()
        term_3173 = _t689
        self.consume_literal(')')
        _t690 = logic_pb2.RelTerm(term=term172)
        _t691 = logic_pb2.RelTerm(term=term_3173)
        _t692 = logic_pb2.Primitive(name='rel_primitive_gt_eq_monotype', terms=[_t690, _t691])
        return _t692

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('+')
        _t693 = self.parse_term()
        term174 = _t693
        _t694 = self.parse_term()
        term_3175 = _t694
        _t695 = self.parse_term()
        term_4176 = _t695
        self.consume_literal(')')
        _t696 = logic_pb2.RelTerm(term=term174)
        _t697 = logic_pb2.RelTerm(term=term_3175)
        _t698 = logic_pb2.RelTerm(term=term_4176)
        _t699 = logic_pb2.Primitive(name='rel_primitive_add_monotype', terms=[_t696, _t697, _t698])
        return _t699

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('-')
        _t700 = self.parse_term()
        term177 = _t700
        _t701 = self.parse_term()
        term_3178 = _t701
        _t702 = self.parse_term()
        term_4179 = _t702
        self.consume_literal(')')
        _t703 = logic_pb2.RelTerm(term=term177)
        _t704 = logic_pb2.RelTerm(term=term_3178)
        _t705 = logic_pb2.RelTerm(term=term_4179)
        _t706 = logic_pb2.Primitive(name='rel_primitive_subtract_monotype', terms=[_t703, _t704, _t705])
        return _t706

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('*')
        _t707 = self.parse_term()
        term180 = _t707
        _t708 = self.parse_term()
        term_3181 = _t708
        _t709 = self.parse_term()
        term_4182 = _t709
        self.consume_literal(')')
        _t710 = logic_pb2.RelTerm(term=term180)
        _t711 = logic_pb2.RelTerm(term=term_3181)
        _t712 = logic_pb2.RelTerm(term=term_4182)
        _t713 = logic_pb2.Primitive(name='rel_primitive_multiply_monotype', terms=[_t710, _t711, _t712])
        return _t713

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('/')
        _t714 = self.parse_term()
        term183 = _t714
        _t715 = self.parse_term()
        term_3184 = _t715
        _t716 = self.parse_term()
        term_4185 = _t716
        self.consume_literal(')')
        _t717 = logic_pb2.RelTerm(term=term183)
        _t718 = logic_pb2.RelTerm(term=term_3184)
        _t719 = logic_pb2.RelTerm(term=term_4185)
        _t720 = logic_pb2.Primitive(name='rel_primitive_divide_monotype', terms=[_t717, _t718, _t719])
        return _t720

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        
        if self.match_lookahead_literal('true', 0):
            _t721 = 1
        else:
            
            if self.match_lookahead_literal('missing', 0):
                _t722 = 1
            else:
                
                if self.match_lookahead_literal('false', 0):
                    _t723 = 1
                else:
                    
                    if self.match_lookahead_literal('(', 0):
                        _t724 = 1
                    else:
                        
                        if self.match_lookahead_literal('#', 0):
                            _t725 = 0
                        else:
                            
                            if self.match_lookahead_terminal('UINT128', 0):
                                _t726 = 1
                            else:
                                
                                if self.match_lookahead_terminal('SYMBOL', 0):
                                    _t727 = 1
                                else:
                                    
                                    if self.match_lookahead_terminal('STRING', 0):
                                        _t728 = 1
                                    else:
                                        
                                        if self.match_lookahead_terminal('INT128', 0):
                                            _t729 = 1
                                        else:
                                            
                                            if self.match_lookahead_terminal('INT', 0):
                                                _t730 = 1
                                            else:
                                                
                                                if self.match_lookahead_terminal('FLOAT', 0):
                                                    _t731 = 1
                                                else:
                                                    
                                                    if self.match_lookahead_terminal('DECIMAL', 0):
                                                        _t732 = 1
                                                    else:
                                                        _t732 = -1
                                                    _t731 = _t732
                                                _t730 = _t731
                                            _t729 = _t730
                                        _t728 = _t729
                                    _t727 = _t728
                                _t726 = _t727
                            _t725 = _t726
                        _t724 = _t725
                    _t723 = _t724
                _t722 = _t723
            _t721 = _t722
        prediction186 = _t721
        
        if prediction186 == 1:
            _t734 = self.parse_term()
            term188 = _t734
            _t735 = logic_pb2.RelTerm(term=term188)
            _t733 = _t735
        else:
            
            if prediction186 == 0:
                _t737 = self.parse_specialized_value()
                specialized_value187 = _t737
                _t738 = logic_pb2.RelTerm(specialized_value=specialized_value187)
                _t736 = _t738
            else:
                raise ParseError(f"{'Unexpected token in rel_term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t733 = _t736
        return _t733

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal('#')
        _t739 = self.parse_value()
        value189 = _t739
        return value189

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        self.consume_literal('(')
        self.consume_literal('relatom')
        _t740 = self.parse_name()
        name190 = _t740
        xs191 = []
        cond192 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond192:
            _t741 = self.parse_rel_term()
            item193 = _t741
            xs191.append(item193)
            cond192 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        rel_terms194 = xs191
        self.consume_literal(')')
        _t742 = logic_pb2.RelAtom(name=name190, terms=rel_terms194)
        return _t742

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal('(')
        self.consume_literal('cast')
        _t743 = self.parse_term()
        term195 = _t743
        _t744 = self.parse_term()
        term_3196 = _t744
        self.consume_literal(')')
        _t745 = logic_pb2.Cast(input=term195, result=term_3196)
        return _t745

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal('(')
        self.consume_literal('attrs')
        xs197 = []
        cond198 = self.match_lookahead_literal('(', 0)
        while cond198:
            _t746 = self.parse_attribute()
            item199 = _t746
            xs197.append(item199)
            cond198 = self.match_lookahead_literal('(', 0)
        attributes200 = xs197
        self.consume_literal(')')
        return attributes200

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal('(')
        self.consume_literal('attribute')
        _t747 = self.parse_name()
        name201 = _t747
        xs202 = []
        cond203 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond203:
            _t748 = self.parse_value()
            item204 = _t748
            xs202.append(item204)
            cond203 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        values205 = xs202
        self.consume_literal(')')
        _t749 = logic_pb2.Attribute(name=name201, args=values205)
        return _t749

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal('(')
        self.consume_literal('algorithm')
        xs206 = []
        cond207 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('UINT128', 0))
        while cond207:
            _t750 = self.parse_relation_id()
            item208 = _t750
            xs206.append(item208)
            cond207 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('UINT128', 0))
        relation_ids209 = xs206
        _t751 = self.parse_script()
        script210 = _t751
        self.consume_literal(')')
        _t752 = logic_pb2.Algorithm(body=script210)
        getattr(_t752, 'global').extend(relation_ids209)
        return _t752

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal('(')
        self.consume_literal('script')
        xs211 = []
        cond212 = self.match_lookahead_literal('(', 0)
        while cond212:
            _t753 = self.parse_construct()
            item213 = _t753
            xs211.append(item213)
            cond212 = self.match_lookahead_literal('(', 0)
        constructs214 = xs211
        self.consume_literal(')')
        _t754 = logic_pb2.Script(constructs=constructs214)
        return _t754

    def parse_construct(self) -> logic_pb2.Construct:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('upsert', 1):
                _t756 = 1
            else:
                
                if self.match_lookahead_literal('monus', 1):
                    _t757 = 1
                else:
                    
                    if self.match_lookahead_literal('monoid', 1):
                        _t758 = 1
                    else:
                        
                        if self.match_lookahead_literal('loop', 1):
                            _t759 = 0
                        else:
                            
                            if self.match_lookahead_literal('break', 1):
                                _t760 = 1
                            else:
                                
                                if self.match_lookahead_literal('assign', 1):
                                    _t761 = 1
                                else:
                                    _t761 = -1
                                _t760 = _t761
                            _t759 = _t760
                        _t758 = _t759
                    _t757 = _t758
                _t756 = _t757
            _t755 = _t756
        else:
            _t755 = -1
        prediction215 = _t755
        
        if prediction215 == 1:
            _t763 = self.parse_instruction()
            instruction217 = _t763
            _t764 = logic_pb2.Construct(instruction=instruction217)
            _t762 = _t764
        else:
            
            if prediction215 == 0:
                _t766 = self.parse_loop()
                loop216 = _t766
                _t767 = logic_pb2.Construct(loop=loop216)
                _t765 = _t767
            else:
                raise ParseError(f"{'Unexpected token in construct'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t762 = _t765
        return _t762

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal('(')
        self.consume_literal('loop')
        _t768 = self.parse_init()
        init218 = _t768
        _t769 = self.parse_script()
        script219 = _t769
        self.consume_literal(')')
        _t770 = logic_pb2.Loop(init=init218, body=script219)
        return _t770

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal('(')
        self.consume_literal('init')
        xs220 = []
        cond221 = self.match_lookahead_literal('(', 0)
        while cond221:
            _t771 = self.parse_instruction()
            item222 = _t771
            xs220.append(item222)
            cond221 = self.match_lookahead_literal('(', 0)
        instructions223 = xs220
        self.consume_literal(')')
        return instructions223

    def parse_instruction(self) -> logic_pb2.Instruction:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('upsert', 1):
                _t773 = 1
            else:
                
                if self.match_lookahead_literal('monus', 1):
                    _t774 = 4
                else:
                    
                    if self.match_lookahead_literal('monoid', 1):
                        _t775 = 3
                    else:
                        
                        if self.match_lookahead_literal('break', 1):
                            _t776 = 2
                        else:
                            
                            if self.match_lookahead_literal('assign', 1):
                                _t777 = 0
                            else:
                                _t777 = -1
                            _t776 = _t777
                        _t775 = _t776
                    _t774 = _t775
                _t773 = _t774
            _t772 = _t773
        else:
            _t772 = -1
        prediction224 = _t772
        
        if prediction224 == 4:
            _t779 = self.parse_monus_def()
            monus_def229 = _t779
            _t780 = logic_pb2.Instruction(monus_def=monus_def229)
            _t778 = _t780
        else:
            
            if prediction224 == 3:
                _t782 = self.parse_monoid_def()
                monoid_def228 = _t782
                _t783 = logic_pb2.Instruction(monoid_def=monoid_def228)
                _t781 = _t783
            else:
                
                if prediction224 == 2:
                    _t785 = self.parse_break()
                    break227 = _t785
                    _t786 = logic_pb2.Instruction()
                    getattr(_t786, 'break').CopyFrom(break227)
                    _t784 = _t786
                else:
                    
                    if prediction224 == 1:
                        _t788 = self.parse_upsert()
                        upsert226 = _t788
                        _t789 = logic_pb2.Instruction(upsert=upsert226)
                        _t787 = _t789
                    else:
                        
                        if prediction224 == 0:
                            _t791 = self.parse_assign()
                            assign225 = _t791
                            _t792 = logic_pb2.Instruction(assign=assign225)
                            _t790 = _t792
                        else:
                            raise ParseError(f"{'Unexpected token in instruction'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t787 = _t790
                    _t784 = _t787
                _t781 = _t784
            _t778 = _t781
        return _t778

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal('(')
        self.consume_literal('assign')
        _t793 = self.parse_relation_id()
        relation_id230 = _t793
        _t794 = self.parse_abstraction()
        abstraction231 = _t794
        
        if self.match_lookahead_literal('(', 0):
            _t796 = self.parse_attrs()
            _t795 = _t796
        else:
            _t795 = None
        attrs232 = _t795
        self.consume_literal(')')
        _t797 = logic_pb2.Assign(name=relation_id230, body=abstraction231, attrs=(attrs232 if attrs232 is not None else []))
        return _t797

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal('(')
        self.consume_literal('upsert')
        _t798 = self.parse_relation_id()
        relation_id233 = _t798
        _t799 = self.parse_abstraction_with_arity()
        abstraction_with_arity234 = _t799
        
        if self.match_lookahead_literal('(', 0):
            _t801 = self.parse_attrs()
            _t800 = _t801
        else:
            _t800 = None
        attrs235 = _t800
        self.consume_literal(')')
        _t802 = logic_pb2.Upsert(name=relation_id233, body=abstraction_with_arity234[0], attrs=(attrs235 if attrs235 is not None else []), value_arity=abstraction_with_arity234[1])
        return _t802

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal('(')
        _t803 = self.parse_bindings()
        bindings236 = _t803
        _t804 = self.parse_formula()
        formula237 = _t804
        self.consume_literal(')')
        _t805 = logic_pb2.Abstraction(vars=(list(bindings236[0]) + list(bindings236[1] if bindings236[1] is not None else [])), value=formula237)
        return (_t805, len(bindings236[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal('(')
        self.consume_literal('break')
        _t806 = self.parse_relation_id()
        relation_id238 = _t806
        _t807 = self.parse_abstraction()
        abstraction239 = _t807
        
        if self.match_lookahead_literal('(', 0):
            _t809 = self.parse_attrs()
            _t808 = _t809
        else:
            _t808 = None
        attrs240 = _t808
        self.consume_literal(')')
        _t810 = logic_pb2.Break(name=relation_id238, body=abstraction239, attrs=(attrs240 if attrs240 is not None else []))
        return _t810

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal('(')
        self.consume_literal('monoid')
        _t811 = self.parse_monoid()
        monoid241 = _t811
        _t812 = self.parse_relation_id()
        relation_id242 = _t812
        _t813 = self.parse_abstraction_with_arity()
        abstraction_with_arity243 = _t813
        
        if self.match_lookahead_literal('(', 0):
            _t815 = self.parse_attrs()
            _t814 = _t815
        else:
            _t814 = None
        attrs244 = _t814
        self.consume_literal(')')
        _t816 = logic_pb2.MonoidDef(monoid=monoid241, name=relation_id242, body=abstraction_with_arity243[0], attrs=(attrs244 if attrs244 is not None else []), value_arity=abstraction_with_arity243[1])
        return _t816

    def parse_monoid(self) -> logic_pb2.Monoid:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('sum', 1):
                _t818 = 3
            else:
                
                if self.match_lookahead_literal('or', 1):
                    _t819 = 0
                else:
                    
                    if self.match_lookahead_literal('min', 1):
                        _t820 = 1
                    else:
                        
                        if self.match_lookahead_literal('max', 1):
                            _t821 = 2
                        else:
                            _t821 = -1
                        _t820 = _t821
                    _t819 = _t820
                _t818 = _t819
            _t817 = _t818
        else:
            _t817 = -1
        prediction245 = _t817
        
        if prediction245 == 3:
            _t823 = self.parse_sum_monoid()
            sum_monoid249 = _t823
            _t824 = logic_pb2.Monoid(sum_monoid=sum_monoid249)
            _t822 = _t824
        else:
            
            if prediction245 == 2:
                _t826 = self.parse_max_monoid()
                max_monoid248 = _t826
                _t827 = logic_pb2.Monoid(max_monoid=max_monoid248)
                _t825 = _t827
            else:
                
                if prediction245 == 1:
                    _t829 = self.parse_min_monoid()
                    min_monoid247 = _t829
                    _t830 = logic_pb2.Monoid(min_monoid=min_monoid247)
                    _t828 = _t830
                else:
                    
                    if prediction245 == 0:
                        _t832 = self.parse_or_monoid()
                        or_monoid246 = _t832
                        _t833 = logic_pb2.Monoid(or_monoid=or_monoid246)
                        _t831 = _t833
                    else:
                        raise ParseError(f"{'Unexpected token in monoid'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t828 = _t831
                _t825 = _t828
            _t822 = _t825
        return _t822

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        self.consume_literal('(')
        self.consume_literal('or')
        self.consume_literal(')')
        _t834 = logic_pb2.OrMonoid()
        return _t834

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        self.consume_literal('(')
        self.consume_literal('min')
        _t835 = self.parse_type()
        type250 = _t835
        self.consume_literal(')')
        _t836 = logic_pb2.MinMonoid(type=type250)
        return _t836

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        self.consume_literal('(')
        self.consume_literal('max')
        _t837 = self.parse_type()
        type251 = _t837
        self.consume_literal(')')
        _t838 = logic_pb2.MaxMonoid(type=type251)
        return _t838

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        self.consume_literal('(')
        self.consume_literal('sum')
        _t839 = self.parse_type()
        type252 = _t839
        self.consume_literal(')')
        _t840 = logic_pb2.SumMonoid(type=type252)
        return _t840

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal('(')
        self.consume_literal('monus')
        _t841 = self.parse_monoid()
        monoid253 = _t841
        _t842 = self.parse_relation_id()
        relation_id254 = _t842
        _t843 = self.parse_abstraction_with_arity()
        abstraction_with_arity255 = _t843
        
        if self.match_lookahead_literal('(', 0):
            _t845 = self.parse_attrs()
            _t844 = _t845
        else:
            _t844 = None
        attrs256 = _t844
        self.consume_literal(')')
        _t846 = logic_pb2.MonusDef(monoid=monoid253, name=relation_id254, body=abstraction_with_arity255[0], attrs=(attrs256 if attrs256 is not None else []), value_arity=abstraction_with_arity255[1])
        return _t846

    def parse_constraint(self) -> logic_pb2.Constraint:
        self.consume_literal('(')
        self.consume_literal('functional_dependency')
        _t847 = self.parse_relation_id()
        relation_id257 = _t847
        _t848 = self.parse_abstraction()
        abstraction258 = _t848
        _t849 = self.parse_functional_dependency_keys()
        functional_dependency_keys259 = _t849
        _t850 = self.parse_functional_dependency_values()
        functional_dependency_values260 = _t850
        self.consume_literal(')')
        _t851 = logic_pb2.FunctionalDependency(guard=abstraction258, keys=functional_dependency_keys259, values=functional_dependency_values260)
        _t852 = logic_pb2.Constraint(name=relation_id257, functional_dependency=_t851)
        return _t852

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('keys')
        xs261 = []
        cond262 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond262:
            _t853 = self.parse_var()
            item263 = _t853
            xs261.append(item263)
            cond262 = self.match_lookahead_terminal('SYMBOL', 0)
        vars264 = xs261
        self.consume_literal(')')
        return vars264

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('values')
        xs265 = []
        cond266 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond266:
            _t854 = self.parse_var()
            item267 = _t854
            xs265.append(item267)
            cond266 = self.match_lookahead_terminal('SYMBOL', 0)
        vars268 = xs265
        self.consume_literal(')')
        return vars268

    def parse_data(self) -> logic_pb2.Data:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('rel_edb', 1):
                _t856 = 0
            else:
                
                if self.match_lookahead_literal('csv_data', 1):
                    _t857 = 2
                else:
                    
                    if self.match_lookahead_literal('betree_relation', 1):
                        _t858 = 1
                    else:
                        _t858 = -1
                    _t857 = _t858
                _t856 = _t857
            _t855 = _t856
        else:
            _t855 = -1
        prediction269 = _t855
        
        if prediction269 == 2:
            _t860 = self.parse_csv_data()
            csv_data272 = _t860
            _t861 = logic_pb2.Data(csv_data=csv_data272)
            _t859 = _t861
        else:
            
            if prediction269 == 1:
                _t863 = self.parse_betree_relation()
                betree_relation271 = _t863
                _t864 = logic_pb2.Data(betree_relation=betree_relation271)
                _t862 = _t864
            else:
                
                if prediction269 == 0:
                    _t866 = self.parse_rel_edb()
                    rel_edb270 = _t866
                    _t867 = logic_pb2.Data(rel_edb=rel_edb270)
                    _t865 = _t867
                else:
                    raise ParseError(f"{'Unexpected token in data'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t862 = _t865
            _t859 = _t862
        return _t859

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        self.consume_literal('(')
        self.consume_literal('rel_edb')
        _t868 = self.parse_relation_id()
        relation_id273 = _t868
        _t869 = self.parse_rel_edb_path()
        rel_edb_path274 = _t869
        _t870 = self.parse_rel_edb_types()
        rel_edb_types275 = _t870
        self.consume_literal(')')
        _t871 = logic_pb2.RelEDB(target_id=relation_id273, path=rel_edb_path274, types=rel_edb_types275)
        return _t871

    def parse_rel_edb_path(self) -> Sequence[str]:
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

    def parse_rel_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal('[')
        xs280 = []
        cond281 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond281:
            _t872 = self.parse_type()
            item282 = _t872
            xs280.append(item282)
            cond281 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types283 = xs280
        self.consume_literal(']')
        return types283

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        self.consume_literal('(')
        self.consume_literal('betree_relation')
        _t873 = self.parse_relation_id()
        relation_id284 = _t873
        _t874 = self.parse_betree_info()
        betree_info285 = _t874
        self.consume_literal(')')
        _t875 = logic_pb2.BeTreeRelation(name=relation_id284, relation_info=betree_info285)
        return _t875

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        self.consume_literal('(')
        self.consume_literal('betree_info')
        _t876 = self.parse_betree_info_key_types()
        betree_info_key_types286 = _t876
        _t877 = self.parse_betree_info_value_types()
        betree_info_value_types287 = _t877
        _t878 = self.parse_config_dict()
        config_dict288 = _t878
        self.consume_literal(')')
        _t879 = self.construct_betree_info(betree_info_key_types286, betree_info_value_types287, config_dict288)
        return _t879

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('key_types')
        xs289 = []
        cond290 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond290:
            _t880 = self.parse_type()
            item291 = _t880
            xs289.append(item291)
            cond290 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types292 = xs289
        self.consume_literal(')')
        return types292

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('value_types')
        xs293 = []
        cond294 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond294:
            _t881 = self.parse_type()
            item295 = _t881
            xs293.append(item295)
            cond294 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types296 = xs293
        self.consume_literal(')')
        return types296

    def parse_csv_data(self) -> logic_pb2.CSVData:
        self.consume_literal('(')
        self.consume_literal('csv_data')
        _t882 = self.parse_csvlocator()
        csvlocator297 = _t882
        _t883 = self.parse_csv_config()
        csv_config298 = _t883
        _t884 = self.parse_csv_columns()
        csv_columns299 = _t884
        _t885 = self.parse_csv_asof()
        csv_asof300 = _t885
        self.consume_literal(')')
        _t886 = logic_pb2.CSVData(locator=csvlocator297, config=csv_config298, columns=csv_columns299, asof=csv_asof300)
        return _t886

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        self.consume_literal('(')
        self.consume_literal('csv_locator')
        
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('paths', 1)):
            _t888 = self.parse_csv_locator_paths()
            _t887 = _t888
        else:
            _t887 = None
        csv_locator_paths301 = _t887
        
        if self.match_lookahead_literal('(', 0):
            _t890 = self.parse_csv_locator_inline_data()
            _t889 = _t890
        else:
            _t889 = None
        csv_locator_inline_data302 = _t889
        self.consume_literal(')')
        _t891 = logic_pb2.CSVLocator(paths=(csv_locator_paths301 if csv_locator_paths301 is not None else []), inline_data=(csv_locator_inline_data302 if csv_locator_inline_data302 is not None else '').encode())
        return _t891

    def parse_csv_locator_paths(self) -> Sequence[str]:
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
        _t892 = self.parse_config_dict()
        config_dict308 = _t892
        self.consume_literal(')')
        _t893 = self.construct_csv_config(config_dict308)
        return _t893

    def parse_csv_columns(self) -> Sequence[logic_pb2.CSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs309 = []
        cond310 = self.match_lookahead_literal('(', 0)
        while cond310:
            _t894 = self.parse_csv_column()
            item311 = _t894
            xs309.append(item311)
            cond310 = self.match_lookahead_literal('(', 0)
        csv_columns312 = xs309
        self.consume_literal(')')
        return csv_columns312

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        string313 = self.consume_terminal('STRING')
        _t895 = self.parse_relation_id()
        relation_id314 = _t895
        self.consume_literal('[')
        xs315 = []
        cond316 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond316:
            _t896 = self.parse_type()
            item317 = _t896
            xs315.append(item317)
            cond316 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types318 = xs315
        self.consume_literal(']')
        self.consume_literal(')')
        _t897 = logic_pb2.CSVColumn(column_name=string313, target_id=relation_id314, types=types318)
        return _t897

    def parse_csv_asof(self) -> str:
        self.consume_literal('(')
        self.consume_literal('asof')
        string319 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return string319

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal('(')
        self.consume_literal('undefine')
        _t898 = self.parse_fragment_id()
        fragment_id320 = _t898
        self.consume_literal(')')
        _t899 = transactions_pb2.Undefine(fragment_id=fragment_id320)
        return _t899

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal('(')
        self.consume_literal('context')
        xs321 = []
        cond322 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('UINT128', 0))
        while cond322:
            _t900 = self.parse_relation_id()
            item323 = _t900
            xs321.append(item323)
            cond322 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('UINT128', 0))
        relation_ids324 = xs321
        self.consume_literal(')')
        _t901 = transactions_pb2.Context(relations=relation_ids324)
        return _t901

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal('(')
        self.consume_literal('reads')
        xs325 = []
        cond326 = self.match_lookahead_literal('(', 0)
        while cond326:
            _t902 = self.parse_read()
            item327 = _t902
            xs325.append(item327)
            cond326 = self.match_lookahead_literal('(', 0)
        reads328 = xs325
        self.consume_literal(')')
        return reads328

    def parse_read(self) -> transactions_pb2.Read:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('what_if', 1):
                _t904 = 2
            else:
                
                if self.match_lookahead_literal('output', 1):
                    _t905 = 1
                else:
                    
                    if self.match_lookahead_literal('export', 1):
                        _t906 = 4
                    else:
                        
                        if self.match_lookahead_literal('demand', 1):
                            _t907 = 0
                        else:
                            
                            if self.match_lookahead_literal('abort', 1):
                                _t908 = 3
                            else:
                                _t908 = -1
                            _t907 = _t908
                        _t906 = _t907
                    _t905 = _t906
                _t904 = _t905
            _t903 = _t904
        else:
            _t903 = -1
        prediction329 = _t903
        
        if prediction329 == 4:
            _t910 = self.parse_export()
            export334 = _t910
            _t911 = transactions_pb2.Read(export=export334)
            _t909 = _t911
        else:
            
            if prediction329 == 3:
                _t913 = self.parse_abort()
                abort333 = _t913
                _t914 = transactions_pb2.Read(abort=abort333)
                _t912 = _t914
            else:
                
                if prediction329 == 2:
                    _t916 = self.parse_what_if()
                    what_if332 = _t916
                    _t917 = transactions_pb2.Read(what_if=what_if332)
                    _t915 = _t917
                else:
                    
                    if prediction329 == 1:
                        _t919 = self.parse_output()
                        output331 = _t919
                        _t920 = transactions_pb2.Read(output=output331)
                        _t918 = _t920
                    else:
                        
                        if prediction329 == 0:
                            _t922 = self.parse_demand()
                            demand330 = _t922
                            _t923 = transactions_pb2.Read(demand=demand330)
                            _t921 = _t923
                        else:
                            raise ParseError(f"{'Unexpected token in read'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t918 = _t921
                    _t915 = _t918
                _t912 = _t915
            _t909 = _t912
        return _t909

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal('(')
        self.consume_literal('demand')
        _t924 = self.parse_relation_id()
        relation_id335 = _t924
        self.consume_literal(')')
        _t925 = transactions_pb2.Demand(relation_id=relation_id335)
        return _t925

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal('(')
        self.consume_literal('output')
        _t926 = self.parse_name()
        name336 = _t926
        _t927 = self.parse_relation_id()
        relation_id337 = _t927
        self.consume_literal(')')
        _t928 = transactions_pb2.Output(name=name336, relation_id=relation_id337)
        return _t928

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal('(')
        self.consume_literal('what_if')
        _t929 = self.parse_name()
        name338 = _t929
        _t930 = self.parse_epoch()
        epoch339 = _t930
        self.consume_literal(')')
        _t931 = transactions_pb2.WhatIf(branch=name338, epoch=epoch339)
        return _t931

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal('(')
        self.consume_literal('abort')
        
        if (self.match_lookahead_literal(':', 0) and self.match_lookahead_terminal('SYMBOL', 1)):
            _t933 = self.parse_name()
            _t932 = _t933
        else:
            _t932 = None
        name340 = _t932
        _t934 = self.parse_relation_id()
        relation_id341 = _t934
        self.consume_literal(')')
        _t935 = transactions_pb2.Abort(name=(name340 if name340 is not None else 'abort'), relation_id=relation_id341)
        return _t935

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal('(')
        self.consume_literal('export')
        _t936 = self.parse_export_csv_config()
        export_csv_config342 = _t936
        self.consume_literal(')')
        _t937 = transactions_pb2.Export(csv_config=export_csv_config342)
        return _t937

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal('(')
        self.consume_literal('export_csv_config')
        _t938 = self.parse_export_csv_path()
        export_csv_path343 = _t938
        _t939 = self.parse_export_csv_columns()
        export_csv_columns344 = _t939
        _t940 = self.parse_config_dict()
        config_dict345 = _t940
        self.consume_literal(')')
        _t941 = self.export_csv_config(export_csv_path343, export_csv_columns344, config_dict345)
        return _t941

    def parse_export_csv_path(self) -> str:
        self.consume_literal('(')
        self.consume_literal('path')
        string346 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return string346

    def parse_export_csv_columns(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs347 = []
        cond348 = self.match_lookahead_literal('(', 0)
        while cond348:
            _t942 = self.parse_export_csv_column()
            item349 = _t942
            xs347.append(item349)
            cond348 = self.match_lookahead_literal('(', 0)
        export_csv_columns350 = xs347
        self.consume_literal(')')
        return export_csv_columns350

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        string351 = self.consume_terminal('STRING')
        _t943 = self.parse_relation_id()
        relation_id352 = _t943
        self.consume_literal(')')
        _t944 = transactions_pb2.ExportCSVColumn(column_name=string351, column_data=relation_id352)
        return _t944


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
