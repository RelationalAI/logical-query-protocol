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

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t955 = self._extract_value_int32(config.get('csv_header_row'), 1)
        header_row = _t955
        _t956 = self._extract_value_int64(config.get('csv_skip'), 0)
        skip = _t956
        _t957 = self._extract_value_string(config.get('csv_new_line'), '')
        new_line = _t957
        _t958 = self._extract_value_string(config.get('csv_delimiter'), ',')
        delimiter = _t958
        _t959 = self._extract_value_string(config.get('csv_quotechar'), '"')
        quotechar = _t959
        _t960 = self._extract_value_string(config.get('csv_escapechar'), '"')
        escapechar = _t960
        _t961 = self._extract_value_string(config.get('csv_comment'), '')
        comment = _t961
        _t962 = self._extract_value_string_list(config.get('csv_missing_strings'), [])
        missing_strings = _t962
        _t963 = self._extract_value_string(config.get('csv_decimal_separator'), '.')
        decimal_separator = _t963
        _t964 = self._extract_value_string(config.get('csv_encoding'), 'utf-8')
        encoding = _t964
        _t965 = self._extract_value_string(config.get('csv_compression'), 'auto')
        compression = _t965
        _t966 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t966

    def default_configure(self) -> transactions_pb2.Configure:
        _t967 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t967
        _t968 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t968

    def _extract_value_int64(self, value: Optional[logic_pb2.Value], default: int) -> int:
        
        if value is not None:
            assert value is not None
            _t969 = value.HasField('int_value')
        else:
            _t969 = False
        if _t969:
            assert value is not None
            return value.int_value
        return default

    def _extract_value_string(self, value: Optional[logic_pb2.Value], default: str) -> str:
        
        if value is not None:
            assert value is not None
            _t970 = value.HasField('string_value')
        else:
            _t970 = False
        if _t970:
            assert value is not None
            return value.string_value
        return default

    def _try_extract_value_uint128(self, value: Optional[logic_pb2.Value]) -> Optional[logic_pb2.UInt128Value]:
        
        if value is not None:
            assert value is not None
            _t971 = value.HasField('uint128_value')
        else:
            _t971 = False
        if _t971:
            assert value is not None
            return value.uint128_value
        return None

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

    def _try_extract_value_bytes(self, value: Optional[logic_pb2.Value]) -> Optional[bytes]:
        
        if value is not None:
            assert value is not None
            _t973 = value.HasField('string_value')
        else:
            _t973 = False
        if _t973:
            assert value is not None
            return value.string_value.encode()
        return None

    def export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t974 = self._extract_value_int64(config.get('partition_size'), 0)
        partition_size = _t974
        _t975 = self._extract_value_string(config.get('compression'), '')
        compression = _t975
        _t976 = self._extract_value_boolean(config.get('syntax_header_row'), True)
        syntax_header_row = _t976
        _t977 = self._extract_value_string(config.get('syntax_missing_string'), '')
        syntax_missing_string = _t977
        _t978 = self._extract_value_string(config.get('syntax_delim'), ',')
        syntax_delim = _t978
        _t979 = self._extract_value_string(config.get('syntax_quotechar'), '"')
        syntax_quotechar = _t979
        _t980 = self._extract_value_string(config.get('syntax_escapechar'), '\\')
        syntax_escapechar = _t980
        _t981 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t981

    def _extract_value_string_list(self, value: Optional[logic_pb2.Value], default: Sequence[str]) -> Sequence[str]:
        
        if value is not None:
            assert value is not None
            _t982 = value.HasField('string_value')
        else:
            _t982 = False
        if _t982:
            assert value is not None
            return [value.string_value]
        return default

    def _extract_value_int32(self, value: Optional[logic_pb2.Value], default: int) -> int:
        
        if value is not None:
            assert value is not None
            _t983 = value.HasField('int_value')
        else:
            _t983 = False
        if _t983:
            assert value is not None
            return int(value.int_value)
        return int(default)

    def _try_extract_value_int64(self, value: Optional[logic_pb2.Value]) -> Optional[int]:
        
        if value is not None:
            assert value is not None
            _t984 = value.HasField('int_value')
        else:
            _t984 = False
        if _t984:
            assert value is not None
            return value.int_value
        return None

    def _try_extract_value_float64(self, value: Optional[logic_pb2.Value]) -> Optional[float]:
        
        if value is not None:
            assert value is not None
            _t985 = value.HasField('float_value')
        else:
            _t985 = False
        if _t985:
            assert value is not None
            return value.float_value
        return None

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
        _t986 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t986
        _t987 = self._extract_value_int64(config.get('semantics_version'), 0)
        semantics_version = _t987
        _t988 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t988

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t989 = self._try_extract_value_float64(config.get('betree_config_epsilon'))
        epsilon = _t989
        _t990 = self._try_extract_value_int64(config.get('betree_config_max_pivots'))
        max_pivots = _t990
        _t991 = self._try_extract_value_int64(config.get('betree_config_max_deltas'))
        max_deltas = _t991
        _t992 = self._try_extract_value_int64(config.get('betree_config_max_leaf'))
        max_leaf = _t992
        _t993 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t993
        _t994 = self._try_extract_value_uint128(config.get('betree_locator_root_pageid'))
        root_pageid = _t994
        _t995 = self._try_extract_value_bytes(config.get('betree_locator_inline_data'))
        inline_data = _t995
        _t996 = self._try_extract_value_int64(config.get('betree_locator_element_count'))
        element_count = _t996
        _t997 = self._try_extract_value_int64(config.get('betree_locator_tree_height'))
        tree_height = _t997
        _t998 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t998
        _t999 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t999

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        self.consume_literal('(')
        self.consume_literal('transaction')
        
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('configure', 1)):
            _t357 = self.parse_configure()
            _t356 = _t357
        else:
            _t356 = None
        configure0 = _t356
        
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('sync', 1)):
            _t359 = self.parse_sync()
            _t358 = _t359
        else:
            _t358 = None
        sync1 = _t358
        xs2 = []
        cond3 = self.match_lookahead_literal('(', 0)
        while cond3:
            _t360 = self.parse_epoch()
            item4 = _t360
            xs2.append(item4)
            cond3 = self.match_lookahead_literal('(', 0)
        epochs5 = xs2
        self.consume_literal(')')
        _t361 = self.default_configure()
        _t362 = transactions_pb2.Transaction(epochs=epochs5, configure=(configure0 if configure0 is not None else _t361), sync=sync1)
        return _t362

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal('(')
        self.consume_literal('configure')
        _t363 = self.parse_config_dict()
        config_dict6 = _t363
        self.consume_literal(')')
        _t364 = self.construct_configure(config_dict6)
        return _t364

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal('{')
        xs7 = []
        cond8 = self.match_lookahead_literal(':', 0)
        while cond8:
            _t365 = self.parse_config_key_value()
            item9 = _t365
            xs7.append(item9)
            cond8 = self.match_lookahead_literal(':', 0)
        config_key_values10 = xs7
        self.consume_literal('}')
        return config_key_values10

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(':')
        symbol11 = self.consume_terminal('SYMBOL')
        _t366 = self.parse_value()
        value12 = _t366
        return (symbol11, value12,)

    def parse_value(self) -> logic_pb2.Value:
        
        if self.match_lookahead_literal('true', 0):
            _t367 = 9
        else:
            
            if self.match_lookahead_literal('missing', 0):
                _t368 = 8
            else:
                
                if self.match_lookahead_literal('false', 0):
                    _t369 = 9
                else:
                    
                    if self.match_lookahead_literal('(', 0):
                        
                        if self.match_lookahead_literal('datetime', 1):
                            _t371 = 1
                        else:
                            
                            if self.match_lookahead_literal('date', 1):
                                _t372 = 0
                            else:
                                _t372 = -1
                            _t371 = _t372
                        _t370 = _t371
                    else:
                        
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t373 = 5
                        else:
                            
                            if self.match_lookahead_terminal('STRING', 0):
                                _t374 = 2
                            else:
                                
                                if self.match_lookahead_terminal('INT128', 0):
                                    _t375 = 6
                                else:
                                    
                                    if self.match_lookahead_terminal('INT', 0):
                                        _t376 = 3
                                    else:
                                        
                                        if self.match_lookahead_terminal('FLOAT', 0):
                                            _t377 = 4
                                        else:
                                            
                                            if self.match_lookahead_terminal('DECIMAL', 0):
                                                _t378 = 7
                                            else:
                                                _t378 = -1
                                            _t377 = _t378
                                        _t376 = _t377
                                    _t375 = _t376
                                _t374 = _t375
                            _t373 = _t374
                        _t370 = _t373
                    _t369 = _t370
                _t368 = _t369
            _t367 = _t368
        prediction13 = _t367
        
        if prediction13 == 9:
            _t380 = self.parse_boolean_value()
            boolean_value22 = _t380
            _t381 = logic_pb2.Value(boolean_value=boolean_value22)
            _t379 = _t381
        else:
            
            if prediction13 == 8:
                self.consume_literal('missing')
                _t383 = logic_pb2.MissingValue()
                _t384 = logic_pb2.Value(missing_value=_t383)
                _t382 = _t384
            else:
                
                if prediction13 == 7:
                    decimal21 = self.consume_terminal('DECIMAL')
                    _t386 = logic_pb2.Value(decimal_value=decimal21)
                    _t385 = _t386
                else:
                    
                    if prediction13 == 6:
                        int12820 = self.consume_terminal('INT128')
                        _t388 = logic_pb2.Value(int128_value=int12820)
                        _t387 = _t388
                    else:
                        
                        if prediction13 == 5:
                            uint12819 = self.consume_terminal('UINT128')
                            _t390 = logic_pb2.Value(uint128_value=uint12819)
                            _t389 = _t390
                        else:
                            
                            if prediction13 == 4:
                                float18 = self.consume_terminal('FLOAT')
                                _t392 = logic_pb2.Value(float_value=float18)
                                _t391 = _t392
                            else:
                                
                                if prediction13 == 3:
                                    int17 = self.consume_terminal('INT')
                                    _t394 = logic_pb2.Value(int_value=int17)
                                    _t393 = _t394
                                else:
                                    
                                    if prediction13 == 2:
                                        string16 = self.consume_terminal('STRING')
                                        _t396 = logic_pb2.Value(string_value=string16)
                                        _t395 = _t396
                                    else:
                                        
                                        if prediction13 == 1:
                                            _t398 = self.parse_datetime()
                                            datetime15 = _t398
                                            _t399 = logic_pb2.Value(datetime_value=datetime15)
                                            _t397 = _t399
                                        else:
                                            
                                            if prediction13 == 0:
                                                _t401 = self.parse_date()
                                                date14 = _t401
                                                _t402 = logic_pb2.Value(date_value=date14)
                                                _t400 = _t402
                                            else:
                                                raise ParseError(f"{'Unexpected token in value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t397 = _t400
                                        _t395 = _t397
                                    _t393 = _t395
                                _t391 = _t393
                            _t389 = _t391
                        _t387 = _t389
                    _t385 = _t387
                _t382 = _t385
            _t379 = _t382
        return _t379

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal('(')
        self.consume_literal('date')
        int23 = self.consume_terminal('INT')
        int_324 = self.consume_terminal('INT')
        int_425 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t403 = logic_pb2.DateValue(year=int(int23), month=int(int_324), day=int(int_425))
        return _t403

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
            _t404 = self.consume_terminal('INT')
        else:
            _t404 = None
        int_832 = _t404
        self.consume_literal(')')
        _t405 = logic_pb2.DateTimeValue(year=int(int26), month=int(int_327), day=int(int_428), hour=int(int_529), minute=int(int_630), second=int(int_731), microsecond=int((int_832 if int_832 is not None else 0)))
        return _t405

    def parse_boolean_value(self) -> bool:
        
        if self.match_lookahead_literal('true', 0):
            _t406 = 0
        else:
            
            if self.match_lookahead_literal('false', 0):
                _t407 = 1
            else:
                _t407 = -1
            _t406 = _t407
        prediction33 = _t406
        
        if prediction33 == 1:
            self.consume_literal('false')
            _t408 = False
        else:
            
            if prediction33 == 0:
                self.consume_literal('true')
                _t409 = True
            else:
                raise ParseError(f"{'Unexpected token in boolean_value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t408 = _t409
        return _t408

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal('(')
        self.consume_literal('sync')
        xs34 = []
        cond35 = self.match_lookahead_literal(':', 0)
        while cond35:
            _t410 = self.parse_fragment_id()
            item36 = _t410
            xs34.append(item36)
            cond35 = self.match_lookahead_literal(':', 0)
        fragment_ids37 = xs34
        self.consume_literal(')')
        _t411 = transactions_pb2.Sync(fragments=fragment_ids37)
        return _t411

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        self.consume_literal(':')
        symbol38 = self.consume_terminal('SYMBOL')
        return fragments_pb2.FragmentId(id=symbol38.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal('(')
        self.consume_literal('epoch')
        
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('writes', 1)):
            _t413 = self.parse_epoch_writes()
            _t412 = _t413
        else:
            _t412 = None
        epoch_writes39 = _t412
        
        if self.match_lookahead_literal('(', 0):
            _t415 = self.parse_epoch_reads()
            _t414 = _t415
        else:
            _t414 = None
        epoch_reads40 = _t414
        self.consume_literal(')')
        _t416 = transactions_pb2.Epoch(writes=(epoch_writes39 if epoch_writes39 is not None else []), reads=(epoch_reads40 if epoch_reads40 is not None else []))
        return _t416

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal('(')
        self.consume_literal('writes')
        xs41 = []
        cond42 = self.match_lookahead_literal('(', 0)
        while cond42:
            _t417 = self.parse_write()
            item43 = _t417
            xs41.append(item43)
            cond42 = self.match_lookahead_literal('(', 0)
        writes44 = xs41
        self.consume_literal(')')
        return writes44

    def parse_write(self) -> transactions_pb2.Write:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('undefine', 1):
                _t419 = 1
            else:
                
                if self.match_lookahead_literal('snapshot', 1):
                    _t420 = 3
                else:
                    
                    if self.match_lookahead_literal('define', 1):
                        _t421 = 0
                    else:
                        
                        if self.match_lookahead_literal('context', 1):
                            _t422 = 2
                        else:
                            _t422 = -1
                        _t421 = _t422
                    _t420 = _t421
                _t419 = _t420
            _t418 = _t419
        else:
            _t418 = -1
        prediction45 = _t418
        
        if prediction45 == 3:
            _t424 = self.parse_snapshot()
            snapshot49 = _t424
            _t425 = transactions_pb2.Write(snapshot=snapshot49)
            _t423 = _t425
        else:
            
            if prediction45 == 2:
                _t427 = self.parse_context()
                context48 = _t427
                _t428 = transactions_pb2.Write(context=context48)
                _t426 = _t428
            else:
                
                if prediction45 == 1:
                    _t430 = self.parse_undefine()
                    undefine47 = _t430
                    _t431 = transactions_pb2.Write(undefine=undefine47)
                    _t429 = _t431
                else:
                    
                    if prediction45 == 0:
                        _t433 = self.parse_define()
                        define46 = _t433
                        _t434 = transactions_pb2.Write(define=define46)
                        _t432 = _t434
                    else:
                        raise ParseError(f"{'Unexpected token in write'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t429 = _t432
                _t426 = _t429
            _t423 = _t426
        return _t423

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal('(')
        self.consume_literal('define')
        _t435 = self.parse_fragment()
        fragment50 = _t435
        self.consume_literal(')')
        _t436 = transactions_pb2.Define(fragment=fragment50)
        return _t436

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal('(')
        self.consume_literal('fragment')
        _t437 = self.parse_new_fragment_id()
        new_fragment_id51 = _t437
        xs52 = []
        cond53 = self.match_lookahead_literal('(', 0)
        while cond53:
            _t438 = self.parse_declaration()
            item54 = _t438
            xs52.append(item54)
            cond53 = self.match_lookahead_literal('(', 0)
        declarations55 = xs52
        self.consume_literal(')')
        return self.construct_fragment(new_fragment_id51, declarations55)

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        _t439 = self.parse_fragment_id()
        fragment_id56 = _t439
        self.start_fragment(fragment_id56)
        return fragment_id56

    def parse_declaration(self) -> logic_pb2.Declaration:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('rel_edb', 1):
                _t441 = 3
            else:
                
                if self.match_lookahead_literal('functional_dependency', 1):
                    _t442 = 2
                else:
                    
                    if self.match_lookahead_literal('def', 1):
                        _t443 = 0
                    else:
                        
                        if self.match_lookahead_literal('csv_data', 1):
                            _t444 = 3
                        else:
                            
                            if self.match_lookahead_literal('betree_relation', 1):
                                _t445 = 3
                            else:
                                
                                if self.match_lookahead_literal('algorithm', 1):
                                    _t446 = 1
                                else:
                                    _t446 = -1
                                _t445 = _t446
                            _t444 = _t445
                        _t443 = _t444
                    _t442 = _t443
                _t441 = _t442
            _t440 = _t441
        else:
            _t440 = -1
        prediction57 = _t440
        
        if prediction57 == 3:
            _t448 = self.parse_data()
            data61 = _t448
            _t449 = logic_pb2.Declaration(data=data61)
            _t447 = _t449
        else:
            
            if prediction57 == 2:
                _t451 = self.parse_constraint()
                constraint60 = _t451
                _t452 = logic_pb2.Declaration(constraint=constraint60)
                _t450 = _t452
            else:
                
                if prediction57 == 1:
                    _t454 = self.parse_algorithm()
                    algorithm59 = _t454
                    _t455 = logic_pb2.Declaration(algorithm=algorithm59)
                    _t453 = _t455
                else:
                    
                    if prediction57 == 0:
                        _t457 = self.parse_def()
                        def58 = _t457
                        _t458 = logic_pb2.Declaration()
                        getattr(_t458, 'def').CopyFrom(def58)
                        _t456 = _t458
                    else:
                        raise ParseError(f"{'Unexpected token in declaration'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t453 = _t456
                _t450 = _t453
            _t447 = _t450
        return _t447

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal('(')
        self.consume_literal('def')
        _t459 = self.parse_relation_id()
        relation_id62 = _t459
        _t460 = self.parse_abstraction()
        abstraction63 = _t460
        
        if self.match_lookahead_literal('(', 0):
            _t462 = self.parse_attrs()
            _t461 = _t462
        else:
            _t461 = None
        attrs64 = _t461
        self.consume_literal(')')
        _t463 = logic_pb2.Def(name=relation_id62, body=abstraction63, attrs=(attrs64 if attrs64 is not None else []))
        return _t463

    def parse_relation_id(self) -> logic_pb2.RelationId:
        
        if self.match_lookahead_literal(':', 0):
            _t464 = 0
        else:
            
            if self.match_lookahead_terminal('UINT128', 0):
                _t465 = 1
            else:
                _t465 = -1
            _t464 = _t465
        prediction65 = _t464
        
        if prediction65 == 1:
            uint12867 = self.consume_terminal('UINT128')
            _t466 = logic_pb2.RelationId(id_low=uint12867.low, id_high=uint12867.high)
        else:
            
            if prediction65 == 0:
                self.consume_literal(':')
                symbol66 = self.consume_terminal('SYMBOL')
                _t467 = self.relation_id_from_string(symbol66)
            else:
                raise ParseError(f"{'Unexpected token in relation_id'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t466 = _t467
        return _t466

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal('(')
        _t468 = self.parse_bindings()
        bindings68 = _t468
        _t469 = self.parse_formula()
        formula69 = _t469
        self.consume_literal(')')
        _t470 = logic_pb2.Abstraction(vars=(list(bindings68[0]) + list(bindings68[1] if bindings68[1] is not None else [])), value=formula69)
        return _t470

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal('[')
        xs70 = []
        cond71 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond71:
            _t471 = self.parse_binding()
            item72 = _t471
            xs70.append(item72)
            cond71 = self.match_lookahead_terminal('SYMBOL', 0)
        bindings73 = xs70
        
        if self.match_lookahead_literal('|', 0):
            _t473 = self.parse_value_bindings()
            _t472 = _t473
        else:
            _t472 = None
        value_bindings74 = _t472
        self.consume_literal(']')
        return (bindings73, (value_bindings74 if value_bindings74 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol75 = self.consume_terminal('SYMBOL')
        self.consume_literal('::')
        _t474 = self.parse_type()
        type76 = _t474
        _t475 = logic_pb2.Var(name=symbol75)
        _t476 = logic_pb2.Binding(var=_t475, type=type76)
        return _t476

    def parse_type(self) -> logic_pb2.Type:
        
        if self.match_lookahead_literal('UNKNOWN', 0):
            _t477 = 0
        else:
            
            if self.match_lookahead_literal('UINT128', 0):
                _t478 = 4
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
                _t478 = _t479
            _t477 = _t478
        prediction77 = _t477
        
        if prediction77 == 10:
            _t489 = self.parse_boolean_type()
            boolean_type88 = _t489
            _t490 = logic_pb2.Type(boolean_type=boolean_type88)
            _t488 = _t490
        else:
            
            if prediction77 == 9:
                _t492 = self.parse_decimal_type()
                decimal_type87 = _t492
                _t493 = logic_pb2.Type(decimal_type=decimal_type87)
                _t491 = _t493
            else:
                
                if prediction77 == 8:
                    _t495 = self.parse_missing_type()
                    missing_type86 = _t495
                    _t496 = logic_pb2.Type(missing_type=missing_type86)
                    _t494 = _t496
                else:
                    
                    if prediction77 == 7:
                        _t498 = self.parse_datetime_type()
                        datetime_type85 = _t498
                        _t499 = logic_pb2.Type(datetime_type=datetime_type85)
                        _t497 = _t499
                    else:
                        
                        if prediction77 == 6:
                            _t501 = self.parse_date_type()
                            date_type84 = _t501
                            _t502 = logic_pb2.Type(date_type=date_type84)
                            _t500 = _t502
                        else:
                            
                            if prediction77 == 5:
                                _t504 = self.parse_int128_type()
                                int128_type83 = _t504
                                _t505 = logic_pb2.Type(int128_type=int128_type83)
                                _t503 = _t505
                            else:
                                
                                if prediction77 == 4:
                                    _t507 = self.parse_uint128_type()
                                    uint128_type82 = _t507
                                    _t508 = logic_pb2.Type(uint128_type=uint128_type82)
                                    _t506 = _t508
                                else:
                                    
                                    if prediction77 == 3:
                                        _t510 = self.parse_float_type()
                                        float_type81 = _t510
                                        _t511 = logic_pb2.Type(float_type=float_type81)
                                        _t509 = _t511
                                    else:
                                        
                                        if prediction77 == 2:
                                            _t513 = self.parse_int_type()
                                            int_type80 = _t513
                                            _t514 = logic_pb2.Type(int_type=int_type80)
                                            _t512 = _t514
                                        else:
                                            
                                            if prediction77 == 1:
                                                _t516 = self.parse_string_type()
                                                string_type79 = _t516
                                                _t517 = logic_pb2.Type(string_type=string_type79)
                                                _t515 = _t517
                                            else:
                                                
                                                if prediction77 == 0:
                                                    _t519 = self.parse_unspecified_type()
                                                    unspecified_type78 = _t519
                                                    _t520 = logic_pb2.Type(unspecified_type=unspecified_type78)
                                                    _t518 = _t520
                                                else:
                                                    raise ParseError(f"{'Unexpected token in type'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
        _t521 = logic_pb2.UnspecifiedType()
        return _t521

    def parse_string_type(self) -> logic_pb2.StringType:
        self.consume_literal('STRING')
        _t522 = logic_pb2.StringType()
        return _t522

    def parse_int_type(self) -> logic_pb2.IntType:
        self.consume_literal('INT')
        _t523 = logic_pb2.IntType()
        return _t523

    def parse_float_type(self) -> logic_pb2.FloatType:
        self.consume_literal('FLOAT')
        _t524 = logic_pb2.FloatType()
        return _t524

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        self.consume_literal('UINT128')
        _t525 = logic_pb2.UInt128Type()
        return _t525

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        self.consume_literal('INT128')
        _t526 = logic_pb2.Int128Type()
        return _t526

    def parse_date_type(self) -> logic_pb2.DateType:
        self.consume_literal('DATE')
        _t527 = logic_pb2.DateType()
        return _t527

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        self.consume_literal('DATETIME')
        _t528 = logic_pb2.DateTimeType()
        return _t528

    def parse_missing_type(self) -> logic_pb2.MissingType:
        self.consume_literal('MISSING')
        _t529 = logic_pb2.MissingType()
        return _t529

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        self.consume_literal('(')
        self.consume_literal('DECIMAL')
        int89 = self.consume_terminal('INT')
        int_390 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t530 = logic_pb2.DecimalType(precision=int(int89), scale=int(int_390))
        return _t530

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal('BOOLEAN')
        _t531 = logic_pb2.BooleanType()
        return _t531

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal('|')
        xs91 = []
        cond92 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond92:
            _t532 = self.parse_binding()
            item93 = _t532
            xs91.append(item93)
            cond92 = self.match_lookahead_terminal('SYMBOL', 0)
        bindings94 = xs91
        return bindings94

    def parse_formula(self) -> logic_pb2.Formula:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('true', 1):
                _t534 = 0
            else:
                
                if self.match_lookahead_literal('relatom', 1):
                    _t535 = 11
                else:
                    
                    if self.match_lookahead_literal('reduce', 1):
                        _t536 = 3
                    else:
                        
                        if self.match_lookahead_literal('primitive', 1):
                            _t537 = 10
                        else:
                            
                            if self.match_lookahead_literal('pragma', 1):
                                _t538 = 9
                            else:
                                
                                if self.match_lookahead_literal('or', 1):
                                    _t539 = 5
                                else:
                                    
                                    if self.match_lookahead_literal('not', 1):
                                        _t540 = 6
                                    else:
                                        
                                        if self.match_lookahead_literal('ffi', 1):
                                            _t541 = 7
                                        else:
                                            
                                            if self.match_lookahead_literal('false', 1):
                                                _t542 = 1
                                            else:
                                                
                                                if self.match_lookahead_literal('exists', 1):
                                                    _t543 = 2
                                                else:
                                                    
                                                    if self.match_lookahead_literal('cast', 1):
                                                        _t544 = 12
                                                    else:
                                                        
                                                        if self.match_lookahead_literal('atom', 1):
                                                            _t545 = 8
                                                        else:
                                                            
                                                            if self.match_lookahead_literal('and', 1):
                                                                _t546 = 4
                                                            else:
                                                                
                                                                if self.match_lookahead_literal('>=', 1):
                                                                    _t547 = 10
                                                                else:
                                                                    
                                                                    if self.match_lookahead_literal('>', 1):
                                                                        _t548 = 10
                                                                    else:
                                                                        
                                                                        if self.match_lookahead_literal('=', 1):
                                                                            _t549 = 10
                                                                        else:
                                                                            
                                                                            if self.match_lookahead_literal('<=', 1):
                                                                                _t550 = 10
                                                                            else:
                                                                                
                                                                                if self.match_lookahead_literal('<', 1):
                                                                                    _t551 = 10
                                                                                else:
                                                                                    
                                                                                    if self.match_lookahead_literal('/', 1):
                                                                                        _t552 = 10
                                                                                    else:
                                                                                        
                                                                                        if self.match_lookahead_literal('-', 1):
                                                                                            _t553 = 10
                                                                                        else:
                                                                                            
                                                                                            if self.match_lookahead_literal('+', 1):
                                                                                                _t554 = 10
                                                                                            else:
                                                                                                
                                                                                                if self.match_lookahead_literal('*', 1):
                                                                                                    _t555 = 10
                                                                                                else:
                                                                                                    _t555 = -1
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
        else:
            _t533 = -1
        prediction95 = _t533
        
        if prediction95 == 12:
            _t557 = self.parse_cast()
            cast108 = _t557
            _t558 = logic_pb2.Formula(cast=cast108)
            _t556 = _t558
        else:
            
            if prediction95 == 11:
                _t560 = self.parse_rel_atom()
                rel_atom107 = _t560
                _t561 = logic_pb2.Formula(rel_atom=rel_atom107)
                _t559 = _t561
            else:
                
                if prediction95 == 10:
                    _t563 = self.parse_primitive()
                    primitive106 = _t563
                    _t564 = logic_pb2.Formula(primitive=primitive106)
                    _t562 = _t564
                else:
                    
                    if prediction95 == 9:
                        _t566 = self.parse_pragma()
                        pragma105 = _t566
                        _t567 = logic_pb2.Formula(pragma=pragma105)
                        _t565 = _t567
                    else:
                        
                        if prediction95 == 8:
                            _t569 = self.parse_atom()
                            atom104 = _t569
                            _t570 = logic_pb2.Formula(atom=atom104)
                            _t568 = _t570
                        else:
                            
                            if prediction95 == 7:
                                _t572 = self.parse_ffi()
                                ffi103 = _t572
                                _t573 = logic_pb2.Formula(ffi=ffi103)
                                _t571 = _t573
                            else:
                                
                                if prediction95 == 6:
                                    _t575 = self.parse_not()
                                    not102 = _t575
                                    _t576 = logic_pb2.Formula()
                                    getattr(_t576, 'not').CopyFrom(not102)
                                    _t574 = _t576
                                else:
                                    
                                    if prediction95 == 5:
                                        _t578 = self.parse_disjunction()
                                        disjunction101 = _t578
                                        _t579 = logic_pb2.Formula(disjunction=disjunction101)
                                        _t577 = _t579
                                    else:
                                        
                                        if prediction95 == 4:
                                            _t581 = self.parse_conjunction()
                                            conjunction100 = _t581
                                            _t582 = logic_pb2.Formula(conjunction=conjunction100)
                                            _t580 = _t582
                                        else:
                                            
                                            if prediction95 == 3:
                                                _t584 = self.parse_reduce()
                                                reduce99 = _t584
                                                _t585 = logic_pb2.Formula(reduce=reduce99)
                                                _t583 = _t585
                                            else:
                                                
                                                if prediction95 == 2:
                                                    _t587 = self.parse_exists()
                                                    exists98 = _t587
                                                    _t588 = logic_pb2.Formula(exists=exists98)
                                                    _t586 = _t588
                                                else:
                                                    
                                                    if prediction95 == 1:
                                                        _t590 = self.parse_false()
                                                        false97 = _t590
                                                        _t591 = logic_pb2.Formula(disjunction=false97)
                                                        _t589 = _t591
                                                    else:
                                                        
                                                        if prediction95 == 0:
                                                            _t593 = self.parse_true()
                                                            true96 = _t593
                                                            _t594 = logic_pb2.Formula(conjunction=true96)
                                                            _t592 = _t594
                                                        else:
                                                            raise ParseError(f"{'Unexpected token in formula'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
            _t556 = _t559
        return _t556

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('true')
        self.consume_literal(')')
        _t595 = logic_pb2.Conjunction(args=[])
        return _t595

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('false')
        self.consume_literal(')')
        _t596 = logic_pb2.Disjunction(args=[])
        return _t596

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal('(')
        self.consume_literal('exists')
        _t597 = self.parse_bindings()
        bindings109 = _t597
        _t598 = self.parse_formula()
        formula110 = _t598
        self.consume_literal(')')
        _t599 = logic_pb2.Abstraction(vars=(list(bindings109[0]) + list(bindings109[1] if bindings109[1] is not None else [])), value=formula110)
        _t600 = logic_pb2.Exists(body=_t599)
        return _t600

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal('(')
        self.consume_literal('reduce')
        _t601 = self.parse_abstraction()
        abstraction111 = _t601
        _t602 = self.parse_abstraction()
        abstraction_3112 = _t602
        _t603 = self.parse_terms()
        terms113 = _t603
        self.consume_literal(')')
        _t604 = logic_pb2.Reduce(op=abstraction111, body=abstraction_3112, terms=terms113)
        return _t604

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal('(')
        self.consume_literal('terms')
        xs114 = []
        cond115 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond115:
            _t605 = self.parse_term()
            item116 = _t605
            xs114.append(item116)
            cond115 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms117 = xs114
        self.consume_literal(')')
        return terms117

    def parse_term(self) -> logic_pb2.Term:
        
        if self.match_lookahead_literal('true', 0):
            _t606 = 1
        else:
            
            if self.match_lookahead_literal('missing', 0):
                _t607 = 1
            else:
                
                if self.match_lookahead_literal('false', 0):
                    _t608 = 1
                else:
                    
                    if self.match_lookahead_literal('(', 0):
                        _t609 = 1
                    else:
                        
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t610 = 1
                        else:
                            
                            if self.match_lookahead_terminal('SYMBOL', 0):
                                _t611 = 0
                            else:
                                
                                if self.match_lookahead_terminal('STRING', 0):
                                    _t612 = 1
                                else:
                                    
                                    if self.match_lookahead_terminal('INT128', 0):
                                        _t613 = 1
                                    else:
                                        
                                        if self.match_lookahead_terminal('INT', 0):
                                            _t614 = 1
                                        else:
                                            
                                            if self.match_lookahead_terminal('FLOAT', 0):
                                                _t615 = 1
                                            else:
                                                
                                                if self.match_lookahead_terminal('DECIMAL', 0):
                                                    _t616 = 1
                                                else:
                                                    _t616 = -1
                                                _t615 = _t616
                                            _t614 = _t615
                                        _t613 = _t614
                                    _t612 = _t613
                                _t611 = _t612
                            _t610 = _t611
                        _t609 = _t610
                    _t608 = _t609
                _t607 = _t608
            _t606 = _t607
        prediction118 = _t606
        
        if prediction118 == 1:
            _t618 = self.parse_constant()
            constant120 = _t618
            _t619 = logic_pb2.Term(constant=constant120)
            _t617 = _t619
        else:
            
            if prediction118 == 0:
                _t621 = self.parse_var()
                var119 = _t621
                _t622 = logic_pb2.Term(var=var119)
                _t620 = _t622
            else:
                raise ParseError(f"{'Unexpected token in term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t617 = _t620
        return _t617

    def parse_var(self) -> logic_pb2.Var:
        symbol121 = self.consume_terminal('SYMBOL')
        _t623 = logic_pb2.Var(name=symbol121)
        return _t623

    def parse_constant(self) -> logic_pb2.Value:
        _t624 = self.parse_value()
        value122 = _t624
        return value122

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('and')
        xs123 = []
        cond124 = self.match_lookahead_literal('(', 0)
        while cond124:
            _t625 = self.parse_formula()
            item125 = _t625
            xs123.append(item125)
            cond124 = self.match_lookahead_literal('(', 0)
        formulas126 = xs123
        self.consume_literal(')')
        _t626 = logic_pb2.Conjunction(args=formulas126)
        return _t626

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('or')
        xs127 = []
        cond128 = self.match_lookahead_literal('(', 0)
        while cond128:
            _t627 = self.parse_formula()
            item129 = _t627
            xs127.append(item129)
            cond128 = self.match_lookahead_literal('(', 0)
        formulas130 = xs127
        self.consume_literal(')')
        _t628 = logic_pb2.Disjunction(args=formulas130)
        return _t628

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal('(')
        self.consume_literal('not')
        _t629 = self.parse_formula()
        formula131 = _t629
        self.consume_literal(')')
        _t630 = logic_pb2.Not(arg=formula131)
        return _t630

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal('(')
        self.consume_literal('ffi')
        _t631 = self.parse_name()
        name132 = _t631
        _t632 = self.parse_ffi_args()
        ffi_args133 = _t632
        _t633 = self.parse_terms()
        terms134 = _t633
        self.consume_literal(')')
        _t634 = logic_pb2.FFI(name=name132, args=ffi_args133, terms=terms134)
        return _t634

    def parse_name(self) -> str:
        self.consume_literal(':')
        symbol135 = self.consume_terminal('SYMBOL')
        return symbol135

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal('(')
        self.consume_literal('args')
        xs136 = []
        cond137 = self.match_lookahead_literal('(', 0)
        while cond137:
            _t635 = self.parse_abstraction()
            item138 = _t635
            xs136.append(item138)
            cond137 = self.match_lookahead_literal('(', 0)
        abstractions139 = xs136
        self.consume_literal(')')
        return abstractions139

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal('(')
        self.consume_literal('atom')
        _t636 = self.parse_relation_id()
        relation_id140 = _t636
        xs141 = []
        cond142 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond142:
            _t637 = self.parse_term()
            item143 = _t637
            xs141.append(item143)
            cond142 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms144 = xs141
        self.consume_literal(')')
        _t638 = logic_pb2.Atom(name=relation_id140, terms=terms144)
        return _t638

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal('(')
        self.consume_literal('pragma')
        _t639 = self.parse_name()
        name145 = _t639
        xs146 = []
        cond147 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond147:
            _t640 = self.parse_term()
            item148 = _t640
            xs146.append(item148)
            cond147 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms149 = xs146
        self.consume_literal(')')
        _t641 = logic_pb2.Pragma(name=name145, terms=terms149)
        return _t641

    def parse_primitive(self) -> logic_pb2.Primitive:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('primitive', 1):
                _t643 = 9
            else:
                
                if self.match_lookahead_literal('>=', 1):
                    _t644 = 4
                else:
                    
                    if self.match_lookahead_literal('>', 1):
                        _t645 = 3
                    else:
                        
                        if self.match_lookahead_literal('=', 1):
                            _t646 = 0
                        else:
                            
                            if self.match_lookahead_literal('<=', 1):
                                _t647 = 2
                            else:
                                
                                if self.match_lookahead_literal('<', 1):
                                    _t648 = 1
                                else:
                                    
                                    if self.match_lookahead_literal('/', 1):
                                        _t649 = 8
                                    else:
                                        
                                        if self.match_lookahead_literal('-', 1):
                                            _t650 = 6
                                        else:
                                            
                                            if self.match_lookahead_literal('+', 1):
                                                _t651 = 5
                                            else:
                                                
                                                if self.match_lookahead_literal('*', 1):
                                                    _t652 = 7
                                                else:
                                                    _t652 = -1
                                                _t651 = _t652
                                            _t650 = _t651
                                        _t649 = _t650
                                    _t648 = _t649
                                _t647 = _t648
                            _t646 = _t647
                        _t645 = _t646
                    _t644 = _t645
                _t643 = _t644
            _t642 = _t643
        else:
            _t642 = -1
        prediction150 = _t642
        
        if prediction150 == 9:
            self.consume_literal('(')
            self.consume_literal('primitive')
            _t654 = self.parse_name()
            name160 = _t654
            xs161 = []
            cond162 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            while cond162:
                _t655 = self.parse_rel_term()
                item163 = _t655
                xs161.append(item163)
                cond162 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            rel_terms164 = xs161
            self.consume_literal(')')
            _t656 = logic_pb2.Primitive(name=name160, terms=rel_terms164)
            _t653 = _t656
        else:
            
            if prediction150 == 8:
                _t658 = self.parse_divide()
                divide159 = _t658
                _t657 = divide159
            else:
                
                if prediction150 == 7:
                    _t660 = self.parse_multiply()
                    multiply158 = _t660
                    _t659 = multiply158
                else:
                    
                    if prediction150 == 6:
                        _t662 = self.parse_minus()
                        minus157 = _t662
                        _t661 = minus157
                    else:
                        
                        if prediction150 == 5:
                            _t664 = self.parse_add()
                            add156 = _t664
                            _t663 = add156
                        else:
                            
                            if prediction150 == 4:
                                _t666 = self.parse_gt_eq()
                                gt_eq155 = _t666
                                _t665 = gt_eq155
                            else:
                                
                                if prediction150 == 3:
                                    _t668 = self.parse_gt()
                                    gt154 = _t668
                                    _t667 = gt154
                                else:
                                    
                                    if prediction150 == 2:
                                        _t670 = self.parse_lt_eq()
                                        lt_eq153 = _t670
                                        _t669 = lt_eq153
                                    else:
                                        
                                        if prediction150 == 1:
                                            _t672 = self.parse_lt()
                                            lt152 = _t672
                                            _t671 = lt152
                                        else:
                                            
                                            if prediction150 == 0:
                                                _t674 = self.parse_eq()
                                                eq151 = _t674
                                                _t673 = eq151
                                            else:
                                                raise ParseError(f"{'Unexpected token in primitive'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t671 = _t673
                                        _t669 = _t671
                                    _t667 = _t669
                                _t665 = _t667
                            _t663 = _t665
                        _t661 = _t663
                    _t659 = _t661
                _t657 = _t659
            _t653 = _t657
        return _t653

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('=')
        _t675 = self.parse_term()
        term165 = _t675
        _t676 = self.parse_term()
        term_3166 = _t676
        self.consume_literal(')')
        _t677 = logic_pb2.RelTerm(term=term165)
        _t678 = logic_pb2.RelTerm(term=term_3166)
        _t679 = logic_pb2.Primitive(name='rel_primitive_eq', terms=[_t677, _t678])
        return _t679

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<')
        _t680 = self.parse_term()
        term167 = _t680
        _t681 = self.parse_term()
        term_3168 = _t681
        self.consume_literal(')')
        _t682 = logic_pb2.RelTerm(term=term167)
        _t683 = logic_pb2.RelTerm(term=term_3168)
        _t684 = logic_pb2.Primitive(name='rel_primitive_lt_monotype', terms=[_t682, _t683])
        return _t684

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<=')
        _t685 = self.parse_term()
        term169 = _t685
        _t686 = self.parse_term()
        term_3170 = _t686
        self.consume_literal(')')
        _t687 = logic_pb2.RelTerm(term=term169)
        _t688 = logic_pb2.RelTerm(term=term_3170)
        _t689 = logic_pb2.Primitive(name='rel_primitive_lt_eq_monotype', terms=[_t687, _t688])
        return _t689

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>')
        _t690 = self.parse_term()
        term171 = _t690
        _t691 = self.parse_term()
        term_3172 = _t691
        self.consume_literal(')')
        _t692 = logic_pb2.RelTerm(term=term171)
        _t693 = logic_pb2.RelTerm(term=term_3172)
        _t694 = logic_pb2.Primitive(name='rel_primitive_gt_monotype', terms=[_t692, _t693])
        return _t694

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>=')
        _t695 = self.parse_term()
        term173 = _t695
        _t696 = self.parse_term()
        term_3174 = _t696
        self.consume_literal(')')
        _t697 = logic_pb2.RelTerm(term=term173)
        _t698 = logic_pb2.RelTerm(term=term_3174)
        _t699 = logic_pb2.Primitive(name='rel_primitive_gt_eq_monotype', terms=[_t697, _t698])
        return _t699

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('+')
        _t700 = self.parse_term()
        term175 = _t700
        _t701 = self.parse_term()
        term_3176 = _t701
        _t702 = self.parse_term()
        term_4177 = _t702
        self.consume_literal(')')
        _t703 = logic_pb2.RelTerm(term=term175)
        _t704 = logic_pb2.RelTerm(term=term_3176)
        _t705 = logic_pb2.RelTerm(term=term_4177)
        _t706 = logic_pb2.Primitive(name='rel_primitive_add_monotype', terms=[_t703, _t704, _t705])
        return _t706

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('-')
        _t707 = self.parse_term()
        term178 = _t707
        _t708 = self.parse_term()
        term_3179 = _t708
        _t709 = self.parse_term()
        term_4180 = _t709
        self.consume_literal(')')
        _t710 = logic_pb2.RelTerm(term=term178)
        _t711 = logic_pb2.RelTerm(term=term_3179)
        _t712 = logic_pb2.RelTerm(term=term_4180)
        _t713 = logic_pb2.Primitive(name='rel_primitive_subtract_monotype', terms=[_t710, _t711, _t712])
        return _t713

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('*')
        _t714 = self.parse_term()
        term181 = _t714
        _t715 = self.parse_term()
        term_3182 = _t715
        _t716 = self.parse_term()
        term_4183 = _t716
        self.consume_literal(')')
        _t717 = logic_pb2.RelTerm(term=term181)
        _t718 = logic_pb2.RelTerm(term=term_3182)
        _t719 = logic_pb2.RelTerm(term=term_4183)
        _t720 = logic_pb2.Primitive(name='rel_primitive_multiply_monotype', terms=[_t717, _t718, _t719])
        return _t720

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('/')
        _t721 = self.parse_term()
        term184 = _t721
        _t722 = self.parse_term()
        term_3185 = _t722
        _t723 = self.parse_term()
        term_4186 = _t723
        self.consume_literal(')')
        _t724 = logic_pb2.RelTerm(term=term184)
        _t725 = logic_pb2.RelTerm(term=term_3185)
        _t726 = logic_pb2.RelTerm(term=term_4186)
        _t727 = logic_pb2.Primitive(name='rel_primitive_divide_monotype', terms=[_t724, _t725, _t726])
        return _t727

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        
        if self.match_lookahead_literal('true', 0):
            _t728 = 1
        else:
            
            if self.match_lookahead_literal('missing', 0):
                _t729 = 1
            else:
                
                if self.match_lookahead_literal('false', 0):
                    _t730 = 1
                else:
                    
                    if self.match_lookahead_literal('(', 0):
                        _t731 = 1
                    else:
                        
                        if self.match_lookahead_literal('#', 0):
                            _t732 = 0
                        else:
                            
                            if self.match_lookahead_terminal('UINT128', 0):
                                _t733 = 1
                            else:
                                
                                if self.match_lookahead_terminal('SYMBOL', 0):
                                    _t734 = 1
                                else:
                                    
                                    if self.match_lookahead_terminal('STRING', 0):
                                        _t735 = 1
                                    else:
                                        
                                        if self.match_lookahead_terminal('INT128', 0):
                                            _t736 = 1
                                        else:
                                            
                                            if self.match_lookahead_terminal('INT', 0):
                                                _t737 = 1
                                            else:
                                                
                                                if self.match_lookahead_terminal('FLOAT', 0):
                                                    _t738 = 1
                                                else:
                                                    
                                                    if self.match_lookahead_terminal('DECIMAL', 0):
                                                        _t739 = 1
                                                    else:
                                                        _t739 = -1
                                                    _t738 = _t739
                                                _t737 = _t738
                                            _t736 = _t737
                                        _t735 = _t736
                                    _t734 = _t735
                                _t733 = _t734
                            _t732 = _t733
                        _t731 = _t732
                    _t730 = _t731
                _t729 = _t730
            _t728 = _t729
        prediction187 = _t728
        
        if prediction187 == 1:
            _t741 = self.parse_term()
            term189 = _t741
            _t742 = logic_pb2.RelTerm(term=term189)
            _t740 = _t742
        else:
            
            if prediction187 == 0:
                _t744 = self.parse_specialized_value()
                specialized_value188 = _t744
                _t745 = logic_pb2.RelTerm(specialized_value=specialized_value188)
                _t743 = _t745
            else:
                raise ParseError(f"{'Unexpected token in rel_term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t740 = _t743
        return _t740

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal('#')
        _t746 = self.parse_value()
        value190 = _t746
        return value190

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        self.consume_literal('(')
        self.consume_literal('relatom')
        _t747 = self.parse_name()
        name191 = _t747
        xs192 = []
        cond193 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond193:
            _t748 = self.parse_rel_term()
            item194 = _t748
            xs192.append(item194)
            cond193 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        rel_terms195 = xs192
        self.consume_literal(')')
        _t749 = logic_pb2.RelAtom(name=name191, terms=rel_terms195)
        return _t749

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal('(')
        self.consume_literal('cast')
        _t750 = self.parse_term()
        term196 = _t750
        _t751 = self.parse_term()
        term_3197 = _t751
        self.consume_literal(')')
        _t752 = logic_pb2.Cast(input=term196, result=term_3197)
        return _t752

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal('(')
        self.consume_literal('attrs')
        xs198 = []
        cond199 = self.match_lookahead_literal('(', 0)
        while cond199:
            _t753 = self.parse_attribute()
            item200 = _t753
            xs198.append(item200)
            cond199 = self.match_lookahead_literal('(', 0)
        attributes201 = xs198
        self.consume_literal(')')
        return attributes201

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal('(')
        self.consume_literal('attribute')
        _t754 = self.parse_name()
        name202 = _t754
        xs203 = []
        cond204 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond204:
            _t755 = self.parse_value()
            item205 = _t755
            xs203.append(item205)
            cond204 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        values206 = xs203
        self.consume_literal(')')
        _t756 = logic_pb2.Attribute(name=name202, args=values206)
        return _t756

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal('(')
        self.consume_literal('algorithm')
        xs207 = []
        cond208 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('UINT128', 0))
        while cond208:
            _t757 = self.parse_relation_id()
            item209 = _t757
            xs207.append(item209)
            cond208 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('UINT128', 0))
        relation_ids210 = xs207
        _t758 = self.parse_script()
        script211 = _t758
        self.consume_literal(')')
        _t759 = logic_pb2.Algorithm(body=script211)
        getattr(_t759, 'global').extend(relation_ids210)
        return _t759

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal('(')
        self.consume_literal('script')
        xs212 = []
        cond213 = self.match_lookahead_literal('(', 0)
        while cond213:
            _t760 = self.parse_construct()
            item214 = _t760
            xs212.append(item214)
            cond213 = self.match_lookahead_literal('(', 0)
        constructs215 = xs212
        self.consume_literal(')')
        _t761 = logic_pb2.Script(constructs=constructs215)
        return _t761

    def parse_construct(self) -> logic_pb2.Construct:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('upsert', 1):
                _t763 = 1
            else:
                
                if self.match_lookahead_literal('monus', 1):
                    _t764 = 1
                else:
                    
                    if self.match_lookahead_literal('monoid', 1):
                        _t765 = 1
                    else:
                        
                        if self.match_lookahead_literal('loop', 1):
                            _t766 = 0
                        else:
                            
                            if self.match_lookahead_literal('break', 1):
                                _t767 = 1
                            else:
                                
                                if self.match_lookahead_literal('assign', 1):
                                    _t768 = 1
                                else:
                                    _t768 = -1
                                _t767 = _t768
                            _t766 = _t767
                        _t765 = _t766
                    _t764 = _t765
                _t763 = _t764
            _t762 = _t763
        else:
            _t762 = -1
        prediction216 = _t762
        
        if prediction216 == 1:
            _t770 = self.parse_instruction()
            instruction218 = _t770
            _t771 = logic_pb2.Construct(instruction=instruction218)
            _t769 = _t771
        else:
            
            if prediction216 == 0:
                _t773 = self.parse_loop()
                loop217 = _t773
                _t774 = logic_pb2.Construct(loop=loop217)
                _t772 = _t774
            else:
                raise ParseError(f"{'Unexpected token in construct'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t769 = _t772
        return _t769

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal('(')
        self.consume_literal('loop')
        _t775 = self.parse_init()
        init219 = _t775
        _t776 = self.parse_script()
        script220 = _t776
        self.consume_literal(')')
        _t777 = logic_pb2.Loop(init=init219, body=script220)
        return _t777

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal('(')
        self.consume_literal('init')
        xs221 = []
        cond222 = self.match_lookahead_literal('(', 0)
        while cond222:
            _t778 = self.parse_instruction()
            item223 = _t778
            xs221.append(item223)
            cond222 = self.match_lookahead_literal('(', 0)
        instructions224 = xs221
        self.consume_literal(')')
        return instructions224

    def parse_instruction(self) -> logic_pb2.Instruction:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('upsert', 1):
                _t780 = 1
            else:
                
                if self.match_lookahead_literal('monus', 1):
                    _t781 = 4
                else:
                    
                    if self.match_lookahead_literal('monoid', 1):
                        _t782 = 3
                    else:
                        
                        if self.match_lookahead_literal('break', 1):
                            _t783 = 2
                        else:
                            
                            if self.match_lookahead_literal('assign', 1):
                                _t784 = 0
                            else:
                                _t784 = -1
                            _t783 = _t784
                        _t782 = _t783
                    _t781 = _t782
                _t780 = _t781
            _t779 = _t780
        else:
            _t779 = -1
        prediction225 = _t779
        
        if prediction225 == 4:
            _t786 = self.parse_monus_def()
            monus_def230 = _t786
            _t787 = logic_pb2.Instruction(monus_def=monus_def230)
            _t785 = _t787
        else:
            
            if prediction225 == 3:
                _t789 = self.parse_monoid_def()
                monoid_def229 = _t789
                _t790 = logic_pb2.Instruction(monoid_def=monoid_def229)
                _t788 = _t790
            else:
                
                if prediction225 == 2:
                    _t792 = self.parse_break()
                    break228 = _t792
                    _t793 = logic_pb2.Instruction()
                    getattr(_t793, 'break').CopyFrom(break228)
                    _t791 = _t793
                else:
                    
                    if prediction225 == 1:
                        _t795 = self.parse_upsert()
                        upsert227 = _t795
                        _t796 = logic_pb2.Instruction(upsert=upsert227)
                        _t794 = _t796
                    else:
                        
                        if prediction225 == 0:
                            _t798 = self.parse_assign()
                            assign226 = _t798
                            _t799 = logic_pb2.Instruction(assign=assign226)
                            _t797 = _t799
                        else:
                            raise ParseError(f"{'Unexpected token in instruction'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t794 = _t797
                    _t791 = _t794
                _t788 = _t791
            _t785 = _t788
        return _t785

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal('(')
        self.consume_literal('assign')
        _t800 = self.parse_relation_id()
        relation_id231 = _t800
        _t801 = self.parse_abstraction()
        abstraction232 = _t801
        
        if self.match_lookahead_literal('(', 0):
            _t803 = self.parse_attrs()
            _t802 = _t803
        else:
            _t802 = None
        attrs233 = _t802
        self.consume_literal(')')
        _t804 = logic_pb2.Assign(name=relation_id231, body=abstraction232, attrs=(attrs233 if attrs233 is not None else []))
        return _t804

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal('(')
        self.consume_literal('upsert')
        _t805 = self.parse_relation_id()
        relation_id234 = _t805
        _t806 = self.parse_abstraction_with_arity()
        abstraction_with_arity235 = _t806
        
        if self.match_lookahead_literal('(', 0):
            _t808 = self.parse_attrs()
            _t807 = _t808
        else:
            _t807 = None
        attrs236 = _t807
        self.consume_literal(')')
        _t809 = logic_pb2.Upsert(name=relation_id234, body=abstraction_with_arity235[0], attrs=(attrs236 if attrs236 is not None else []), value_arity=abstraction_with_arity235[1])
        return _t809

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal('(')
        _t810 = self.parse_bindings()
        bindings237 = _t810
        _t811 = self.parse_formula()
        formula238 = _t811
        self.consume_literal(')')
        _t812 = logic_pb2.Abstraction(vars=(list(bindings237[0]) + list(bindings237[1] if bindings237[1] is not None else [])), value=formula238)
        return (_t812, len(bindings237[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal('(')
        self.consume_literal('break')
        _t813 = self.parse_relation_id()
        relation_id239 = _t813
        _t814 = self.parse_abstraction()
        abstraction240 = _t814
        
        if self.match_lookahead_literal('(', 0):
            _t816 = self.parse_attrs()
            _t815 = _t816
        else:
            _t815 = None
        attrs241 = _t815
        self.consume_literal(')')
        _t817 = logic_pb2.Break(name=relation_id239, body=abstraction240, attrs=(attrs241 if attrs241 is not None else []))
        return _t817

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal('(')
        self.consume_literal('monoid')
        _t818 = self.parse_monoid()
        monoid242 = _t818
        _t819 = self.parse_relation_id()
        relation_id243 = _t819
        _t820 = self.parse_abstraction_with_arity()
        abstraction_with_arity244 = _t820
        
        if self.match_lookahead_literal('(', 0):
            _t822 = self.parse_attrs()
            _t821 = _t822
        else:
            _t821 = None
        attrs245 = _t821
        self.consume_literal(')')
        _t823 = logic_pb2.MonoidDef(monoid=monoid242, name=relation_id243, body=abstraction_with_arity244[0], attrs=(attrs245 if attrs245 is not None else []), value_arity=abstraction_with_arity244[1])
        return _t823

    def parse_monoid(self) -> logic_pb2.Monoid:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('sum', 1):
                _t825 = 3
            else:
                
                if self.match_lookahead_literal('or', 1):
                    _t826 = 0
                else:
                    
                    if self.match_lookahead_literal('min', 1):
                        _t827 = 1
                    else:
                        
                        if self.match_lookahead_literal('max', 1):
                            _t828 = 2
                        else:
                            _t828 = -1
                        _t827 = _t828
                    _t826 = _t827
                _t825 = _t826
            _t824 = _t825
        else:
            _t824 = -1
        prediction246 = _t824
        
        if prediction246 == 3:
            _t830 = self.parse_sum_monoid()
            sum_monoid250 = _t830
            _t831 = logic_pb2.Monoid(sum_monoid=sum_monoid250)
            _t829 = _t831
        else:
            
            if prediction246 == 2:
                _t833 = self.parse_max_monoid()
                max_monoid249 = _t833
                _t834 = logic_pb2.Monoid(max_monoid=max_monoid249)
                _t832 = _t834
            else:
                
                if prediction246 == 1:
                    _t836 = self.parse_min_monoid()
                    min_monoid248 = _t836
                    _t837 = logic_pb2.Monoid(min_monoid=min_monoid248)
                    _t835 = _t837
                else:
                    
                    if prediction246 == 0:
                        _t839 = self.parse_or_monoid()
                        or_monoid247 = _t839
                        _t840 = logic_pb2.Monoid(or_monoid=or_monoid247)
                        _t838 = _t840
                    else:
                        raise ParseError(f"{'Unexpected token in monoid'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t835 = _t838
                _t832 = _t835
            _t829 = _t832
        return _t829

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        self.consume_literal('(')
        self.consume_literal('or')
        self.consume_literal(')')
        _t841 = logic_pb2.OrMonoid()
        return _t841

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        self.consume_literal('(')
        self.consume_literal('min')
        _t842 = self.parse_type()
        type251 = _t842
        self.consume_literal(')')
        _t843 = logic_pb2.MinMonoid(type=type251)
        return _t843

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        self.consume_literal('(')
        self.consume_literal('max')
        _t844 = self.parse_type()
        type252 = _t844
        self.consume_literal(')')
        _t845 = logic_pb2.MaxMonoid(type=type252)
        return _t845

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        self.consume_literal('(')
        self.consume_literal('sum')
        _t846 = self.parse_type()
        type253 = _t846
        self.consume_literal(')')
        _t847 = logic_pb2.SumMonoid(type=type253)
        return _t847

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal('(')
        self.consume_literal('monus')
        _t848 = self.parse_monoid()
        monoid254 = _t848
        _t849 = self.parse_relation_id()
        relation_id255 = _t849
        _t850 = self.parse_abstraction_with_arity()
        abstraction_with_arity256 = _t850
        
        if self.match_lookahead_literal('(', 0):
            _t852 = self.parse_attrs()
            _t851 = _t852
        else:
            _t851 = None
        attrs257 = _t851
        self.consume_literal(')')
        _t853 = logic_pb2.MonusDef(monoid=monoid254, name=relation_id255, body=abstraction_with_arity256[0], attrs=(attrs257 if attrs257 is not None else []), value_arity=abstraction_with_arity256[1])
        return _t853

    def parse_constraint(self) -> logic_pb2.Constraint:
        self.consume_literal('(')
        self.consume_literal('functional_dependency')
        _t854 = self.parse_relation_id()
        relation_id258 = _t854
        _t855 = self.parse_abstraction()
        abstraction259 = _t855
        _t856 = self.parse_functional_dependency_keys()
        functional_dependency_keys260 = _t856
        _t857 = self.parse_functional_dependency_values()
        functional_dependency_values261 = _t857
        self.consume_literal(')')
        _t858 = logic_pb2.FunctionalDependency(guard=abstraction259, keys=functional_dependency_keys260, values=functional_dependency_values261)
        _t859 = logic_pb2.Constraint(name=relation_id258, functional_dependency=_t858)
        return _t859

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('keys')
        xs262 = []
        cond263 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond263:
            _t860 = self.parse_var()
            item264 = _t860
            xs262.append(item264)
            cond263 = self.match_lookahead_terminal('SYMBOL', 0)
        vars265 = xs262
        self.consume_literal(')')
        return vars265

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('values')
        xs266 = []
        cond267 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond267:
            _t861 = self.parse_var()
            item268 = _t861
            xs266.append(item268)
            cond267 = self.match_lookahead_terminal('SYMBOL', 0)
        vars269 = xs266
        self.consume_literal(')')
        return vars269

    def parse_data(self) -> logic_pb2.Data:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('rel_edb', 1):
                _t863 = 0
            else:
                
                if self.match_lookahead_literal('csv_data', 1):
                    _t864 = 2
                else:
                    
                    if self.match_lookahead_literal('betree_relation', 1):
                        _t865 = 1
                    else:
                        _t865 = -1
                    _t864 = _t865
                _t863 = _t864
            _t862 = _t863
        else:
            _t862 = -1
        prediction270 = _t862
        
        if prediction270 == 2:
            _t867 = self.parse_csv_data()
            csv_data273 = _t867
            _t868 = logic_pb2.Data(csv_data=csv_data273)
            _t866 = _t868
        else:
            
            if prediction270 == 1:
                _t870 = self.parse_betree_relation()
                betree_relation272 = _t870
                _t871 = logic_pb2.Data(betree_relation=betree_relation272)
                _t869 = _t871
            else:
                
                if prediction270 == 0:
                    _t873 = self.parse_rel_edb()
                    rel_edb271 = _t873
                    _t874 = logic_pb2.Data(rel_edb=rel_edb271)
                    _t872 = _t874
                else:
                    raise ParseError(f"{'Unexpected token in data'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t869 = _t872
            _t866 = _t869
        return _t866

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        self.consume_literal('(')
        self.consume_literal('rel_edb')
        _t875 = self.parse_relation_id()
        relation_id274 = _t875
        _t876 = self.parse_rel_edb_path()
        rel_edb_path275 = _t876
        _t877 = self.parse_rel_edb_types()
        rel_edb_types276 = _t877
        self.consume_literal(')')
        _t878 = logic_pb2.RelEDB(target_id=relation_id274, path=rel_edb_path275, types=rel_edb_types276)
        return _t878

    def parse_rel_edb_path(self) -> Sequence[str]:
        self.consume_literal('[')
        xs277 = []
        cond278 = self.match_lookahead_terminal('STRING', 0)
        while cond278:
            item279 = self.consume_terminal('STRING')
            xs277.append(item279)
            cond278 = self.match_lookahead_terminal('STRING', 0)
        strings280 = xs277
        self.consume_literal(']')
        return strings280

    def parse_rel_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal('[')
        xs281 = []
        cond282 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond282:
            _t879 = self.parse_type()
            item283 = _t879
            xs281.append(item283)
            cond282 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types284 = xs281
        self.consume_literal(']')
        return types284

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        self.consume_literal('(')
        self.consume_literal('betree_relation')
        _t880 = self.parse_relation_id()
        relation_id285 = _t880
        _t881 = self.parse_betree_info()
        betree_info286 = _t881
        self.consume_literal(')')
        _t882 = logic_pb2.BeTreeRelation(name=relation_id285, relation_info=betree_info286)
        return _t882

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        self.consume_literal('(')
        self.consume_literal('betree_info')
        _t883 = self.parse_betree_info_key_types()
        betree_info_key_types287 = _t883
        _t884 = self.parse_betree_info_value_types()
        betree_info_value_types288 = _t884
        _t885 = self.parse_config_dict()
        config_dict289 = _t885
        self.consume_literal(')')
        _t886 = self.construct_betree_info(betree_info_key_types287, betree_info_value_types288, config_dict289)
        return _t886

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('key_types')
        xs290 = []
        cond291 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond291:
            _t887 = self.parse_type()
            item292 = _t887
            xs290.append(item292)
            cond291 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types293 = xs290
        self.consume_literal(')')
        return types293

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('value_types')
        xs294 = []
        cond295 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond295:
            _t888 = self.parse_type()
            item296 = _t888
            xs294.append(item296)
            cond295 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types297 = xs294
        self.consume_literal(')')
        return types297

    def parse_csv_data(self) -> logic_pb2.CSVData:
        self.consume_literal('(')
        self.consume_literal('csv_data')
        _t889 = self.parse_csvlocator()
        csvlocator298 = _t889
        _t890 = self.parse_csv_config()
        csv_config299 = _t890
        _t891 = self.parse_csv_columns()
        csv_columns300 = _t891
        _t892 = self.parse_csv_asof()
        csv_asof301 = _t892
        self.consume_literal(')')
        _t893 = logic_pb2.CSVData(locator=csvlocator298, config=csv_config299, columns=csv_columns300, asof=csv_asof301)
        return _t893

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        self.consume_literal('(')
        self.consume_literal('csv_locator')
        
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('paths', 1)):
            _t895 = self.parse_csv_locator_paths()
            _t894 = _t895
        else:
            _t894 = None
        csv_locator_paths302 = _t894
        
        if self.match_lookahead_literal('(', 0):
            _t897 = self.parse_csv_locator_inline_data()
            _t896 = _t897
        else:
            _t896 = None
        csv_locator_inline_data303 = _t896
        self.consume_literal(')')
        _t898 = logic_pb2.CSVLocator(paths=(csv_locator_paths302 if csv_locator_paths302 is not None else []), inline_data=(csv_locator_inline_data303 if csv_locator_inline_data303 is not None else '').encode())
        return _t898

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal('(')
        self.consume_literal('paths')
        xs304 = []
        cond305 = self.match_lookahead_terminal('STRING', 0)
        while cond305:
            item306 = self.consume_terminal('STRING')
            xs304.append(item306)
            cond305 = self.match_lookahead_terminal('STRING', 0)
        strings307 = xs304
        self.consume_literal(')')
        return strings307

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal('(')
        self.consume_literal('inline_data')
        string308 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return string308

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        self.consume_literal('(')
        self.consume_literal('csv_config')
        _t899 = self.parse_config_dict()
        config_dict309 = _t899
        self.consume_literal(')')
        _t900 = self.construct_csv_config(config_dict309)
        return _t900

    def parse_csv_columns(self) -> Sequence[logic_pb2.CSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs310 = []
        cond311 = self.match_lookahead_literal('(', 0)
        while cond311:
            _t901 = self.parse_csv_column()
            item312 = _t901
            xs310.append(item312)
            cond311 = self.match_lookahead_literal('(', 0)
        csv_columns313 = xs310
        self.consume_literal(')')
        return csv_columns313

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        string314 = self.consume_terminal('STRING')
        _t902 = self.parse_relation_id()
        relation_id315 = _t902
        self.consume_literal('[')
        xs316 = []
        cond317 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond317:
            _t903 = self.parse_type()
            item318 = _t903
            xs316.append(item318)
            cond317 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types319 = xs316
        self.consume_literal(']')
        self.consume_literal(')')
        _t904 = logic_pb2.CSVColumn(column_name=string314, target_id=relation_id315, types=types319)
        return _t904

    def parse_csv_asof(self) -> str:
        self.consume_literal('(')
        self.consume_literal('asof')
        string320 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return string320

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal('(')
        self.consume_literal('undefine')
        _t905 = self.parse_fragment_id()
        fragment_id321 = _t905
        self.consume_literal(')')
        _t906 = transactions_pb2.Undefine(fragment_id=fragment_id321)
        return _t906

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal('(')
        self.consume_literal('context')
        xs322 = []
        cond323 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('UINT128', 0))
        while cond323:
            _t907 = self.parse_relation_id()
            item324 = _t907
            xs322.append(item324)
            cond323 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('UINT128', 0))
        relation_ids325 = xs322
        self.consume_literal(')')
        _t908 = transactions_pb2.Context(relations=relation_ids325)
        return _t908

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        self.consume_literal('(')
        self.consume_literal('snapshot')
        _t909 = self.parse_rel_edb_path()
        rel_edb_path326 = _t909
        _t910 = self.parse_relation_id()
        relation_id327 = _t910
        self.consume_literal(')')
        _t911 = transactions_pb2.Snapshot(destination_path=rel_edb_path326, source_relation=relation_id327)
        return _t911

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal('(')
        self.consume_literal('reads')
        xs328 = []
        cond329 = self.match_lookahead_literal('(', 0)
        while cond329:
            _t912 = self.parse_read()
            item330 = _t912
            xs328.append(item330)
            cond329 = self.match_lookahead_literal('(', 0)
        reads331 = xs328
        self.consume_literal(')')
        return reads331

    def parse_read(self) -> transactions_pb2.Read:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('what_if', 1):
                _t914 = 2
            else:
                
                if self.match_lookahead_literal('output', 1):
                    _t915 = 1
                else:
                    
                    if self.match_lookahead_literal('export', 1):
                        _t916 = 4
                    else:
                        
                        if self.match_lookahead_literal('demand', 1):
                            _t917 = 0
                        else:
                            
                            if self.match_lookahead_literal('abort', 1):
                                _t918 = 3
                            else:
                                _t918 = -1
                            _t917 = _t918
                        _t916 = _t917
                    _t915 = _t916
                _t914 = _t915
            _t913 = _t914
        else:
            _t913 = -1
        prediction332 = _t913
        
        if prediction332 == 4:
            _t920 = self.parse_export()
            export337 = _t920
            _t921 = transactions_pb2.Read(export=export337)
            _t919 = _t921
        else:
            
            if prediction332 == 3:
                _t923 = self.parse_abort()
                abort336 = _t923
                _t924 = transactions_pb2.Read(abort=abort336)
                _t922 = _t924
            else:
                
                if prediction332 == 2:
                    _t926 = self.parse_what_if()
                    what_if335 = _t926
                    _t927 = transactions_pb2.Read(what_if=what_if335)
                    _t925 = _t927
                else:
                    
                    if prediction332 == 1:
                        _t929 = self.parse_output()
                        output334 = _t929
                        _t930 = transactions_pb2.Read(output=output334)
                        _t928 = _t930
                    else:
                        
                        if prediction332 == 0:
                            _t932 = self.parse_demand()
                            demand333 = _t932
                            _t933 = transactions_pb2.Read(demand=demand333)
                            _t931 = _t933
                        else:
                            raise ParseError(f"{'Unexpected token in read'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t928 = _t931
                    _t925 = _t928
                _t922 = _t925
            _t919 = _t922
        return _t919

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal('(')
        self.consume_literal('demand')
        _t934 = self.parse_relation_id()
        relation_id338 = _t934
        self.consume_literal(')')
        _t935 = transactions_pb2.Demand(relation_id=relation_id338)
        return _t935

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal('(')
        self.consume_literal('output')
        _t936 = self.parse_name()
        name339 = _t936
        _t937 = self.parse_relation_id()
        relation_id340 = _t937
        self.consume_literal(')')
        _t938 = transactions_pb2.Output(name=name339, relation_id=relation_id340)
        return _t938

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal('(')
        self.consume_literal('what_if')
        _t939 = self.parse_name()
        name341 = _t939
        _t940 = self.parse_epoch()
        epoch342 = _t940
        self.consume_literal(')')
        _t941 = transactions_pb2.WhatIf(branch=name341, epoch=epoch342)
        return _t941

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal('(')
        self.consume_literal('abort')
        
        if (self.match_lookahead_literal(':', 0) and self.match_lookahead_terminal('SYMBOL', 1)):
            _t943 = self.parse_name()
            _t942 = _t943
        else:
            _t942 = None
        name343 = _t942
        _t944 = self.parse_relation_id()
        relation_id344 = _t944
        self.consume_literal(')')
        _t945 = transactions_pb2.Abort(name=(name343 if name343 is not None else 'abort'), relation_id=relation_id344)
        return _t945

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal('(')
        self.consume_literal('export')
        _t946 = self.parse_export_csv_config()
        export_csv_config345 = _t946
        self.consume_literal(')')
        _t947 = transactions_pb2.Export(csv_config=export_csv_config345)
        return _t947

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal('(')
        self.consume_literal('export_csv_config')
        _t948 = self.parse_export_csv_path()
        export_csv_path346 = _t948
        _t949 = self.parse_export_csv_columns()
        export_csv_columns347 = _t949
        _t950 = self.parse_config_dict()
        config_dict348 = _t950
        self.consume_literal(')')
        _t951 = self.export_csv_config(export_csv_path346, export_csv_columns347, config_dict348)
        return _t951

    def parse_export_csv_path(self) -> str:
        self.consume_literal('(')
        self.consume_literal('path')
        string349 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return string349

    def parse_export_csv_columns(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs350 = []
        cond351 = self.match_lookahead_literal('(', 0)
        while cond351:
            _t952 = self.parse_export_csv_column()
            item352 = _t952
            xs350.append(item352)
            cond351 = self.match_lookahead_literal('(', 0)
        export_csv_columns353 = xs350
        self.consume_literal(')')
        return export_csv_columns353

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        string354 = self.consume_terminal('STRING')
        _t953 = self.parse_relation_id()
        relation_id355 = _t953
        self.consume_literal(')')
        _t954 = transactions_pb2.ExportCSVColumn(column_name=string354, column_data=relation_id355)
        return _t954


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
