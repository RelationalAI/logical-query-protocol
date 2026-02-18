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
        _t972 = self._extract_value_int32(config.get('csv_header_row'), 1)
        header_row = _t972
        _t973 = self._extract_value_int64(config.get('csv_skip'), 0)
        skip = _t973
        _t974 = self._extract_value_string(config.get('csv_new_line'), '')
        new_line = _t974
        _t975 = self._extract_value_string(config.get('csv_delimiter'), ',')
        delimiter = _t975
        _t976 = self._extract_value_string(config.get('csv_quotechar'), '"')
        quotechar = _t976
        _t977 = self._extract_value_string(config.get('csv_escapechar'), '"')
        escapechar = _t977
        _t978 = self._extract_value_string(config.get('csv_comment'), '')
        comment = _t978
        _t979 = self._extract_value_string_list(config.get('csv_missing_strings'), [])
        missing_strings = _t979
        _t980 = self._extract_value_string(config.get('csv_decimal_separator'), '.')
        decimal_separator = _t980
        _t981 = self._extract_value_string(config.get('csv_encoding'), 'utf-8')
        encoding = _t981
        _t982 = self._extract_value_string(config.get('csv_compression'), 'auto')
        compression = _t982
        _t983 = self._extract_value_int64(config.get('csv_partition_size_mb'), 0)
        partition_size = _t983
        _t984 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size)
        return _t984

    def _extract_value_string(self, value: Optional[logic_pb2.Value], default: str) -> str:
        
        if value is not None:
            assert value is not None
            _t985 = value.HasField('string_value')
        else:
            _t985 = False
        if _t985:
            assert value is not None
            return value.string_value
        return default

    def _try_extract_value_int64(self, value: Optional[logic_pb2.Value]) -> Optional[int]:
        
        if value is not None:
            assert value is not None
            _t986 = value.HasField('int_value')
        else:
            _t986 = False
        if _t986:
            assert value is not None
            return value.int_value
        return None

    def _try_extract_value_float64(self, value: Optional[logic_pb2.Value]) -> Optional[float]:
        
        if value is not None:
            assert value is not None
            _t987 = value.HasField('float_value')
        else:
            _t987 = False
        if _t987:
            assert value is not None
            return value.float_value
        return None

    def _extract_value_int64(self, value: Optional[logic_pb2.Value], default: int) -> int:
        
        if value is not None:
            assert value is not None
            _t988 = value.HasField('int_value')
        else:
            _t988 = False
        if _t988:
            assert value is not None
            return value.int_value
        return default

    def _extract_value_boolean(self, value: Optional[logic_pb2.Value], default: bool) -> bool:
        
        if value is not None:
            assert value is not None
            _t989 = value.HasField('boolean_value')
        else:
            _t989 = False
        if _t989:
            assert value is not None
            return value.boolean_value
        return default

    def _try_extract_value_bytes(self, value: Optional[logic_pb2.Value]) -> Optional[bytes]:
        
        if value is not None:
            assert value is not None
            _t990 = value.HasField('string_value')
        else:
            _t990 = False
        if _t990:
            assert value is not None
            return value.string_value.encode()
        return None

    def _extract_value_int32(self, value: Optional[logic_pb2.Value], default: int) -> int:
        
        if value is not None:
            assert value is not None
            _t991 = value.HasField('int_value')
        else:
            _t991 = False
        if _t991:
            assert value is not None
            return int(value.int_value)
        return int(default)

    def _try_extract_value_uint128(self, value: Optional[logic_pb2.Value]) -> Optional[logic_pb2.UInt128Value]:
        
        if value is not None:
            assert value is not None
            _t992 = value.HasField('uint128_value')
        else:
            _t992 = False
        if _t992:
            assert value is not None
            return value.uint128_value
        return None

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t993 = self._extract_value_int64(config.get('partition_size'), 0)
        partition_size = _t993
        _t994 = self._extract_value_string(config.get('compression'), '')
        compression = _t994
        _t995 = self._extract_value_boolean(config.get('syntax_header_row'), True)
        syntax_header_row = _t995
        _t996 = self._extract_value_string(config.get('syntax_missing_string'), '')
        syntax_missing_string = _t996
        _t997 = self._extract_value_string(config.get('syntax_delim'), ',')
        syntax_delim = _t997
        _t998 = self._extract_value_string(config.get('syntax_quotechar'), '"')
        syntax_quotechar = _t998
        _t999 = self._extract_value_string(config.get('syntax_escapechar'), '\\')
        syntax_escapechar = _t999
        _t1000 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1000

    def default_configure(self) -> transactions_pb2.Configure:
        _t1001 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1001
        _t1002 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1002

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t1003 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t1003

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
        _t1004 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1004
        _t1005 = self._extract_value_int64(config.get('semantics_version'), 0)
        semantics_version = _t1005
        _t1006 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1006

    def _extract_value_string_list(self, value: Optional[logic_pb2.Value], default: Sequence[str]) -> Sequence[str]:
        
        if value is not None:
            assert value is not None
            _t1007 = value.HasField('string_value')
        else:
            _t1007 = False
        if _t1007:
            assert value is not None
            return [value.string_value]
        return default

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1008 = self._try_extract_value_float64(config.get('betree_config_epsilon'))
        epsilon = _t1008
        _t1009 = self._try_extract_value_int64(config.get('betree_config_max_pivots'))
        max_pivots = _t1009
        _t1010 = self._try_extract_value_int64(config.get('betree_config_max_deltas'))
        max_deltas = _t1010
        _t1011 = self._try_extract_value_int64(config.get('betree_config_max_leaf'))
        max_leaf = _t1011
        _t1012 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1012
        _t1013 = self._try_extract_value_uint128(config.get('betree_locator_root_pageid'))
        root_pageid = _t1013
        _t1014 = self._try_extract_value_bytes(config.get('betree_locator_inline_data'))
        inline_data = _t1014
        _t1015 = self._try_extract_value_int64(config.get('betree_locator_element_count'))
        element_count = _t1015
        _t1016 = self._try_extract_value_int64(config.get('betree_locator_tree_height'))
        tree_height = _t1016
        _t1017 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1017
        _t1018 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1018

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        self.consume_literal('(')
        self.consume_literal('transaction')
        
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('configure', 1)):
            _t363 = self.parse_configure()
            _t362 = _t363
        else:
            _t362 = None
        configure0 = _t362
        
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('sync', 1)):
            _t365 = self.parse_sync()
            _t364 = _t365
        else:
            _t364 = None
        sync1 = _t364
        xs2 = []
        cond3 = self.match_lookahead_literal('(', 0)
        while cond3:
            _t366 = self.parse_epoch()
            item4 = _t366
            xs2.append(item4)
            cond3 = self.match_lookahead_literal('(', 0)
        epochs5 = xs2
        self.consume_literal(')')
        _t367 = self.default_configure()
        _t368 = transactions_pb2.Transaction(epochs=epochs5, configure=(configure0 if configure0 is not None else _t367), sync=sync1)
        return _t368

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal('(')
        self.consume_literal('configure')
        _t369 = self.parse_config_dict()
        config_dict6 = _t369
        self.consume_literal(')')
        _t370 = self.construct_configure(config_dict6)
        return _t370

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal('{')
        xs7 = []
        cond8 = self.match_lookahead_literal(':', 0)
        while cond8:
            _t371 = self.parse_config_key_value()
            item9 = _t371
            xs7.append(item9)
            cond8 = self.match_lookahead_literal(':', 0)
        config_key_values10 = xs7
        self.consume_literal('}')
        return config_key_values10

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(':')
        symbol11 = self.consume_terminal('SYMBOL')
        _t372 = self.parse_value()
        value12 = _t372
        return (symbol11, value12,)

    def parse_value(self) -> logic_pb2.Value:
        
        if self.match_lookahead_literal('true', 0):
            _t373 = 9
        else:
            
            if self.match_lookahead_literal('missing', 0):
                _t374 = 8
            else:
                
                if self.match_lookahead_literal('false', 0):
                    _t375 = 9
                else:
                    
                    if self.match_lookahead_literal('(', 0):
                        
                        if self.match_lookahead_literal('datetime', 1):
                            _t377 = 1
                        else:
                            
                            if self.match_lookahead_literal('date', 1):
                                _t378 = 0
                            else:
                                _t378 = -1
                            _t377 = _t378
                        _t376 = _t377
                    else:
                        
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t379 = 5
                        else:
                            
                            if self.match_lookahead_terminal('STRING', 0):
                                _t380 = 2
                            else:
                                
                                if self.match_lookahead_terminal('INT128', 0):
                                    _t381 = 6
                                else:
                                    
                                    if self.match_lookahead_terminal('INT', 0):
                                        _t382 = 3
                                    else:
                                        
                                        if self.match_lookahead_terminal('FLOAT', 0):
                                            _t383 = 4
                                        else:
                                            
                                            if self.match_lookahead_terminal('DECIMAL', 0):
                                                _t384 = 7
                                            else:
                                                _t384 = -1
                                            _t383 = _t384
                                        _t382 = _t383
                                    _t381 = _t382
                                _t380 = _t381
                            _t379 = _t380
                        _t376 = _t379
                    _t375 = _t376
                _t374 = _t375
            _t373 = _t374
        prediction13 = _t373
        
        if prediction13 == 9:
            _t386 = self.parse_boolean_value()
            boolean_value22 = _t386
            _t387 = logic_pb2.Value(boolean_value=boolean_value22)
            _t385 = _t387
        else:
            
            if prediction13 == 8:
                self.consume_literal('missing')
                _t389 = logic_pb2.MissingValue()
                _t390 = logic_pb2.Value(missing_value=_t389)
                _t388 = _t390
            else:
                
                if prediction13 == 7:
                    decimal21 = self.consume_terminal('DECIMAL')
                    _t392 = logic_pb2.Value(decimal_value=decimal21)
                    _t391 = _t392
                else:
                    
                    if prediction13 == 6:
                        int12820 = self.consume_terminal('INT128')
                        _t394 = logic_pb2.Value(int128_value=int12820)
                        _t393 = _t394
                    else:
                        
                        if prediction13 == 5:
                            uint12819 = self.consume_terminal('UINT128')
                            _t396 = logic_pb2.Value(uint128_value=uint12819)
                            _t395 = _t396
                        else:
                            
                            if prediction13 == 4:
                                float18 = self.consume_terminal('FLOAT')
                                _t398 = logic_pb2.Value(float_value=float18)
                                _t397 = _t398
                            else:
                                
                                if prediction13 == 3:
                                    int17 = self.consume_terminal('INT')
                                    _t400 = logic_pb2.Value(int_value=int17)
                                    _t399 = _t400
                                else:
                                    
                                    if prediction13 == 2:
                                        string16 = self.consume_terminal('STRING')
                                        _t402 = logic_pb2.Value(string_value=string16)
                                        _t401 = _t402
                                    else:
                                        
                                        if prediction13 == 1:
                                            _t404 = self.parse_datetime()
                                            datetime15 = _t404
                                            _t405 = logic_pb2.Value(datetime_value=datetime15)
                                            _t403 = _t405
                                        else:
                                            
                                            if prediction13 == 0:
                                                _t407 = self.parse_date()
                                                date14 = _t407
                                                _t408 = logic_pb2.Value(date_value=date14)
                                                _t406 = _t408
                                            else:
                                                raise ParseError(f"{'Unexpected token in value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t403 = _t406
                                        _t401 = _t403
                                    _t399 = _t401
                                _t397 = _t399
                            _t395 = _t397
                        _t393 = _t395
                    _t391 = _t393
                _t388 = _t391
            _t385 = _t388
        return _t385

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal('(')
        self.consume_literal('date')
        int23 = self.consume_terminal('INT')
        int_324 = self.consume_terminal('INT')
        int_425 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t409 = logic_pb2.DateValue(year=int(int23), month=int(int_324), day=int(int_425))
        return _t409

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
            _t410 = self.consume_terminal('INT')
        else:
            _t410 = None
        int_832 = _t410
        self.consume_literal(')')
        _t411 = logic_pb2.DateTimeValue(year=int(int26), month=int(int_327), day=int(int_428), hour=int(int_529), minute=int(int_630), second=int(int_731), microsecond=int((int_832 if int_832 is not None else 0)))
        return _t411

    def parse_boolean_value(self) -> bool:
        
        if self.match_lookahead_literal('true', 0):
            _t412 = 0
        else:
            
            if self.match_lookahead_literal('false', 0):
                _t413 = 1
            else:
                _t413 = -1
            _t412 = _t413
        prediction33 = _t412
        
        if prediction33 == 1:
            self.consume_literal('false')
            _t414 = False
        else:
            
            if prediction33 == 0:
                self.consume_literal('true')
                _t415 = True
            else:
                raise ParseError(f"{'Unexpected token in boolean_value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t414 = _t415
        return _t414

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal('(')
        self.consume_literal('sync')
        xs34 = []
        cond35 = self.match_lookahead_literal(':', 0)
        while cond35:
            _t416 = self.parse_fragment_id()
            item36 = _t416
            xs34.append(item36)
            cond35 = self.match_lookahead_literal(':', 0)
        fragment_ids37 = xs34
        self.consume_literal(')')
        _t417 = transactions_pb2.Sync(fragments=fragment_ids37)
        return _t417

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        self.consume_literal(':')
        symbol38 = self.consume_terminal('SYMBOL')
        return fragments_pb2.FragmentId(id=symbol38.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal('(')
        self.consume_literal('epoch')
        
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('writes', 1)):
            _t419 = self.parse_epoch_writes()
            _t418 = _t419
        else:
            _t418 = None
        epoch_writes39 = _t418
        
        if self.match_lookahead_literal('(', 0):
            _t421 = self.parse_epoch_reads()
            _t420 = _t421
        else:
            _t420 = None
        epoch_reads40 = _t420
        self.consume_literal(')')
        _t422 = transactions_pb2.Epoch(writes=(epoch_writes39 if epoch_writes39 is not None else []), reads=(epoch_reads40 if epoch_reads40 is not None else []))
        return _t422

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal('(')
        self.consume_literal('writes')
        xs41 = []
        cond42 = self.match_lookahead_literal('(', 0)
        while cond42:
            _t423 = self.parse_write()
            item43 = _t423
            xs41.append(item43)
            cond42 = self.match_lookahead_literal('(', 0)
        writes44 = xs41
        self.consume_literal(')')
        return writes44

    def parse_write(self) -> transactions_pb2.Write:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('undefine', 1):
                _t425 = 1
            else:
                
                if self.match_lookahead_literal('define', 1):
                    _t426 = 0
                else:
                    
                    if self.match_lookahead_literal('context', 1):
                        _t427 = 2
                    else:
                        _t427 = -1
                    _t426 = _t427
                _t425 = _t426
            _t424 = _t425
        else:
            _t424 = -1
        prediction45 = _t424
        
        if prediction45 == 2:
            _t429 = self.parse_context()
            context48 = _t429
            _t430 = transactions_pb2.Write(context=context48)
            _t428 = _t430
        else:
            
            if prediction45 == 1:
                _t432 = self.parse_undefine()
                undefine47 = _t432
                _t433 = transactions_pb2.Write(undefine=undefine47)
                _t431 = _t433
            else:
                
                if prediction45 == 0:
                    _t435 = self.parse_define()
                    define46 = _t435
                    _t436 = transactions_pb2.Write(define=define46)
                    _t434 = _t436
                else:
                    raise ParseError(f"{'Unexpected token in write'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t431 = _t434
            _t428 = _t431
        return _t428

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal('(')
        self.consume_literal('define')
        _t437 = self.parse_fragment()
        fragment49 = _t437
        self.consume_literal(')')
        _t438 = transactions_pb2.Define(fragment=fragment49)
        return _t438

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal('(')
        self.consume_literal('fragment')
        _t439 = self.parse_new_fragment_id()
        new_fragment_id50 = _t439
        xs51 = []
        cond52 = self.match_lookahead_literal('(', 0)
        while cond52:
            _t440 = self.parse_declaration()
            item53 = _t440
            xs51.append(item53)
            cond52 = self.match_lookahead_literal('(', 0)
        declarations54 = xs51
        self.consume_literal(')')
        return self.construct_fragment(new_fragment_id50, declarations54)

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        _t441 = self.parse_fragment_id()
        fragment_id55 = _t441
        self.start_fragment(fragment_id55)
        return fragment_id55

    def parse_declaration(self) -> logic_pb2.Declaration:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('rel_edb', 1):
                _t443 = 3
            else:
                
                if self.match_lookahead_literal('functional_dependency', 1):
                    _t444 = 2
                else:
                    
                    if self.match_lookahead_literal('def', 1):
                        _t445 = 0
                    else:
                        
                        if self.match_lookahead_literal('csv_data', 1):
                            _t446 = 3
                        else:
                            
                            if self.match_lookahead_literal('betree_relation', 1):
                                _t447 = 3
                            else:
                                
                                if self.match_lookahead_literal('algorithm', 1):
                                    _t448 = 1
                                else:
                                    _t448 = -1
                                _t447 = _t448
                            _t446 = _t447
                        _t445 = _t446
                    _t444 = _t445
                _t443 = _t444
            _t442 = _t443
        else:
            _t442 = -1
        prediction56 = _t442
        
        if prediction56 == 3:
            _t450 = self.parse_data()
            data60 = _t450
            _t451 = logic_pb2.Declaration(data=data60)
            _t449 = _t451
        else:
            
            if prediction56 == 2:
                _t453 = self.parse_constraint()
                constraint59 = _t453
                _t454 = logic_pb2.Declaration(constraint=constraint59)
                _t452 = _t454
            else:
                
                if prediction56 == 1:
                    _t456 = self.parse_algorithm()
                    algorithm58 = _t456
                    _t457 = logic_pb2.Declaration(algorithm=algorithm58)
                    _t455 = _t457
                else:
                    
                    if prediction56 == 0:
                        _t459 = self.parse_def()
                        def57 = _t459
                        _t460 = logic_pb2.Declaration()
                        getattr(_t460, 'def').CopyFrom(def57)
                        _t458 = _t460
                    else:
                        raise ParseError(f"{'Unexpected token in declaration'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t455 = _t458
                _t452 = _t455
            _t449 = _t452
        return _t449

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal('(')
        self.consume_literal('def')
        _t461 = self.parse_relation_id()
        relation_id61 = _t461
        _t462 = self.parse_abstraction()
        abstraction62 = _t462
        
        if self.match_lookahead_literal('(', 0):
            _t464 = self.parse_attrs()
            _t463 = _t464
        else:
            _t463 = None
        attrs63 = _t463
        self.consume_literal(')')
        _t465 = logic_pb2.Def(name=relation_id61, body=abstraction62, attrs=(attrs63 if attrs63 is not None else []))
        return _t465

    def parse_relation_id(self) -> logic_pb2.RelationId:
        
        if self.match_lookahead_literal(':', 0):
            _t466 = 0
        else:
            
            if self.match_lookahead_terminal('UINT128', 0):
                _t467 = 1
            else:
                _t467 = -1
            _t466 = _t467
        prediction64 = _t466
        
        if prediction64 == 1:
            uint12866 = self.consume_terminal('UINT128')
            _t468 = logic_pb2.RelationId(id_low=uint12866.low, id_high=uint12866.high)
        else:
            
            if prediction64 == 0:
                self.consume_literal(':')
                symbol65 = self.consume_terminal('SYMBOL')
                _t469 = self.relation_id_from_string(symbol65)
            else:
                raise ParseError(f"{'Unexpected token in relation_id'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t468 = _t469
        return _t468

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal('(')
        _t470 = self.parse_bindings()
        bindings67 = _t470
        _t471 = self.parse_formula()
        formula68 = _t471
        self.consume_literal(')')
        _t472 = logic_pb2.Abstraction(vars=(list(bindings67[0]) + list(bindings67[1] if bindings67[1] is not None else [])), value=formula68)
        return _t472

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal('[')
        xs69 = []
        cond70 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond70:
            _t473 = self.parse_binding()
            item71 = _t473
            xs69.append(item71)
            cond70 = self.match_lookahead_terminal('SYMBOL', 0)
        bindings72 = xs69
        
        if self.match_lookahead_literal('|', 0):
            _t475 = self.parse_value_bindings()
            _t474 = _t475
        else:
            _t474 = None
        value_bindings73 = _t474
        self.consume_literal(']')
        return (bindings72, (value_bindings73 if value_bindings73 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol74 = self.consume_terminal('SYMBOL')
        self.consume_literal('::')
        _t476 = self.parse_type()
        type75 = _t476
        _t477 = logic_pb2.Var(name=symbol74)
        _t478 = logic_pb2.Binding(var=_t477, type=type75)
        return _t478

    def parse_type(self) -> logic_pb2.Type:
        
        if self.match_lookahead_literal('UNKNOWN', 0):
            _t479 = 0
        else:
            
            if self.match_lookahead_literal('UINT128', 0):
                _t480 = 4
            else:
                
                if self.match_lookahead_literal('STRING', 0):
                    _t481 = 1
                else:
                    
                    if self.match_lookahead_literal('MISSING', 0):
                        _t482 = 8
                    else:
                        
                        if self.match_lookahead_literal('INT128', 0):
                            _t483 = 5
                        else:
                            
                            if self.match_lookahead_literal('INT', 0):
                                _t484 = 2
                            else:
                                
                                if self.match_lookahead_literal('FLOAT', 0):
                                    _t485 = 3
                                else:
                                    
                                    if self.match_lookahead_literal('DATETIME', 0):
                                        _t486 = 7
                                    else:
                                        
                                        if self.match_lookahead_literal('DATE', 0):
                                            _t487 = 6
                                        else:
                                            
                                            if self.match_lookahead_literal('BOOLEAN', 0):
                                                _t488 = 10
                                            else:
                                                
                                                if self.match_lookahead_literal('(', 0):
                                                    _t489 = 9
                                                else:
                                                    _t489 = -1
                                                _t488 = _t489
                                            _t487 = _t488
                                        _t486 = _t487
                                    _t485 = _t486
                                _t484 = _t485
                            _t483 = _t484
                        _t482 = _t483
                    _t481 = _t482
                _t480 = _t481
            _t479 = _t480
        prediction76 = _t479
        
        if prediction76 == 10:
            _t491 = self.parse_boolean_type()
            boolean_type87 = _t491
            _t492 = logic_pb2.Type(boolean_type=boolean_type87)
            _t490 = _t492
        else:
            
            if prediction76 == 9:
                _t494 = self.parse_decimal_type()
                decimal_type86 = _t494
                _t495 = logic_pb2.Type(decimal_type=decimal_type86)
                _t493 = _t495
            else:
                
                if prediction76 == 8:
                    _t497 = self.parse_missing_type()
                    missing_type85 = _t497
                    _t498 = logic_pb2.Type(missing_type=missing_type85)
                    _t496 = _t498
                else:
                    
                    if prediction76 == 7:
                        _t500 = self.parse_datetime_type()
                        datetime_type84 = _t500
                        _t501 = logic_pb2.Type(datetime_type=datetime_type84)
                        _t499 = _t501
                    else:
                        
                        if prediction76 == 6:
                            _t503 = self.parse_date_type()
                            date_type83 = _t503
                            _t504 = logic_pb2.Type(date_type=date_type83)
                            _t502 = _t504
                        else:
                            
                            if prediction76 == 5:
                                _t506 = self.parse_int128_type()
                                int128_type82 = _t506
                                _t507 = logic_pb2.Type(int128_type=int128_type82)
                                _t505 = _t507
                            else:
                                
                                if prediction76 == 4:
                                    _t509 = self.parse_uint128_type()
                                    uint128_type81 = _t509
                                    _t510 = logic_pb2.Type(uint128_type=uint128_type81)
                                    _t508 = _t510
                                else:
                                    
                                    if prediction76 == 3:
                                        _t512 = self.parse_float_type()
                                        float_type80 = _t512
                                        _t513 = logic_pb2.Type(float_type=float_type80)
                                        _t511 = _t513
                                    else:
                                        
                                        if prediction76 == 2:
                                            _t515 = self.parse_int_type()
                                            int_type79 = _t515
                                            _t516 = logic_pb2.Type(int_type=int_type79)
                                            _t514 = _t516
                                        else:
                                            
                                            if prediction76 == 1:
                                                _t518 = self.parse_string_type()
                                                string_type78 = _t518
                                                _t519 = logic_pb2.Type(string_type=string_type78)
                                                _t517 = _t519
                                            else:
                                                
                                                if prediction76 == 0:
                                                    _t521 = self.parse_unspecified_type()
                                                    unspecified_type77 = _t521
                                                    _t522 = logic_pb2.Type(unspecified_type=unspecified_type77)
                                                    _t520 = _t522
                                                else:
                                                    raise ParseError(f"{'Unexpected token in type'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t517 = _t520
                                            _t514 = _t517
                                        _t511 = _t514
                                    _t508 = _t511
                                _t505 = _t508
                            _t502 = _t505
                        _t499 = _t502
                    _t496 = _t499
                _t493 = _t496
            _t490 = _t493
        return _t490

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        self.consume_literal('UNKNOWN')
        _t523 = logic_pb2.UnspecifiedType()
        return _t523

    def parse_string_type(self) -> logic_pb2.StringType:
        self.consume_literal('STRING')
        _t524 = logic_pb2.StringType()
        return _t524

    def parse_int_type(self) -> logic_pb2.IntType:
        self.consume_literal('INT')
        _t525 = logic_pb2.IntType()
        return _t525

    def parse_float_type(self) -> logic_pb2.FloatType:
        self.consume_literal('FLOAT')
        _t526 = logic_pb2.FloatType()
        return _t526

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        self.consume_literal('UINT128')
        _t527 = logic_pb2.UInt128Type()
        return _t527

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        self.consume_literal('INT128')
        _t528 = logic_pb2.Int128Type()
        return _t528

    def parse_date_type(self) -> logic_pb2.DateType:
        self.consume_literal('DATE')
        _t529 = logic_pb2.DateType()
        return _t529

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        self.consume_literal('DATETIME')
        _t530 = logic_pb2.DateTimeType()
        return _t530

    def parse_missing_type(self) -> logic_pb2.MissingType:
        self.consume_literal('MISSING')
        _t531 = logic_pb2.MissingType()
        return _t531

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        self.consume_literal('(')
        self.consume_literal('DECIMAL')
        int88 = self.consume_terminal('INT')
        int_389 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t532 = logic_pb2.DecimalType(precision=int(int88), scale=int(int_389))
        return _t532

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal('BOOLEAN')
        _t533 = logic_pb2.BooleanType()
        return _t533

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal('|')
        xs90 = []
        cond91 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond91:
            _t534 = self.parse_binding()
            item92 = _t534
            xs90.append(item92)
            cond91 = self.match_lookahead_terminal('SYMBOL', 0)
        bindings93 = xs90
        return bindings93

    def parse_formula(self) -> logic_pb2.Formula:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('true', 1):
                _t536 = 0
            else:
                
                if self.match_lookahead_literal('relatom', 1):
                    _t537 = 11
                else:
                    
                    if self.match_lookahead_literal('reduce', 1):
                        _t538 = 3
                    else:
                        
                        if self.match_lookahead_literal('primitive', 1):
                            _t539 = 10
                        else:
                            
                            if self.match_lookahead_literal('pragma', 1):
                                _t540 = 9
                            else:
                                
                                if self.match_lookahead_literal('or', 1):
                                    _t541 = 5
                                else:
                                    
                                    if self.match_lookahead_literal('not', 1):
                                        _t542 = 6
                                    else:
                                        
                                        if self.match_lookahead_literal('ffi', 1):
                                            _t543 = 7
                                        else:
                                            
                                            if self.match_lookahead_literal('false', 1):
                                                _t544 = 1
                                            else:
                                                
                                                if self.match_lookahead_literal('exists', 1):
                                                    _t545 = 2
                                                else:
                                                    
                                                    if self.match_lookahead_literal('cast', 1):
                                                        _t546 = 12
                                                    else:
                                                        
                                                        if self.match_lookahead_literal('atom', 1):
                                                            _t547 = 8
                                                        else:
                                                            
                                                            if self.match_lookahead_literal('and', 1):
                                                                _t548 = 4
                                                            else:
                                                                
                                                                if self.match_lookahead_literal('>=', 1):
                                                                    _t549 = 10
                                                                else:
                                                                    
                                                                    if self.match_lookahead_literal('>', 1):
                                                                        _t550 = 10
                                                                    else:
                                                                        
                                                                        if self.match_lookahead_literal('=', 1):
                                                                            _t551 = 10
                                                                        else:
                                                                            
                                                                            if self.match_lookahead_literal('<=', 1):
                                                                                _t552 = 10
                                                                            else:
                                                                                
                                                                                if self.match_lookahead_literal('<', 1):
                                                                                    _t553 = 10
                                                                                else:
                                                                                    
                                                                                    if self.match_lookahead_literal('/', 1):
                                                                                        _t554 = 10
                                                                                    else:
                                                                                        
                                                                                        if self.match_lookahead_literal('-', 1):
                                                                                            _t555 = 10
                                                                                        else:
                                                                                            
                                                                                            if self.match_lookahead_literal('+', 1):
                                                                                                _t556 = 10
                                                                                            else:
                                                                                                
                                                                                                if self.match_lookahead_literal('*', 1):
                                                                                                    _t557 = 10
                                                                                                else:
                                                                                                    _t557 = -1
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
        else:
            _t535 = -1
        prediction94 = _t535
        
        if prediction94 == 12:
            _t559 = self.parse_cast()
            cast107 = _t559
            _t560 = logic_pb2.Formula(cast=cast107)
            _t558 = _t560
        else:
            
            if prediction94 == 11:
                _t562 = self.parse_rel_atom()
                rel_atom106 = _t562
                _t563 = logic_pb2.Formula(rel_atom=rel_atom106)
                _t561 = _t563
            else:
                
                if prediction94 == 10:
                    _t565 = self.parse_primitive()
                    primitive105 = _t565
                    _t566 = logic_pb2.Formula(primitive=primitive105)
                    _t564 = _t566
                else:
                    
                    if prediction94 == 9:
                        _t568 = self.parse_pragma()
                        pragma104 = _t568
                        _t569 = logic_pb2.Formula(pragma=pragma104)
                        _t567 = _t569
                    else:
                        
                        if prediction94 == 8:
                            _t571 = self.parse_atom()
                            atom103 = _t571
                            _t572 = logic_pb2.Formula(atom=atom103)
                            _t570 = _t572
                        else:
                            
                            if prediction94 == 7:
                                _t574 = self.parse_ffi()
                                ffi102 = _t574
                                _t575 = logic_pb2.Formula(ffi=ffi102)
                                _t573 = _t575
                            else:
                                
                                if prediction94 == 6:
                                    _t577 = self.parse_not()
                                    not101 = _t577
                                    _t578 = logic_pb2.Formula()
                                    getattr(_t578, 'not').CopyFrom(not101)
                                    _t576 = _t578
                                else:
                                    
                                    if prediction94 == 5:
                                        _t580 = self.parse_disjunction()
                                        disjunction100 = _t580
                                        _t581 = logic_pb2.Formula(disjunction=disjunction100)
                                        _t579 = _t581
                                    else:
                                        
                                        if prediction94 == 4:
                                            _t583 = self.parse_conjunction()
                                            conjunction99 = _t583
                                            _t584 = logic_pb2.Formula(conjunction=conjunction99)
                                            _t582 = _t584
                                        else:
                                            
                                            if prediction94 == 3:
                                                _t586 = self.parse_reduce()
                                                reduce98 = _t586
                                                _t587 = logic_pb2.Formula(reduce=reduce98)
                                                _t585 = _t587
                                            else:
                                                
                                                if prediction94 == 2:
                                                    _t589 = self.parse_exists()
                                                    exists97 = _t589
                                                    _t590 = logic_pb2.Formula(exists=exists97)
                                                    _t588 = _t590
                                                else:
                                                    
                                                    if prediction94 == 1:
                                                        _t592 = self.parse_false()
                                                        false96 = _t592
                                                        _t593 = logic_pb2.Formula(disjunction=false96)
                                                        _t591 = _t593
                                                    else:
                                                        
                                                        if prediction94 == 0:
                                                            _t595 = self.parse_true()
                                                            true95 = _t595
                                                            _t596 = logic_pb2.Formula(conjunction=true95)
                                                            _t594 = _t596
                                                        else:
                                                            raise ParseError(f"{'Unexpected token in formula'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t591 = _t594
                                                    _t588 = _t591
                                                _t585 = _t588
                                            _t582 = _t585
                                        _t579 = _t582
                                    _t576 = _t579
                                _t573 = _t576
                            _t570 = _t573
                        _t567 = _t570
                    _t564 = _t567
                _t561 = _t564
            _t558 = _t561
        return _t558

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('true')
        self.consume_literal(')')
        _t597 = logic_pb2.Conjunction(args=[])
        return _t597

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('false')
        self.consume_literal(')')
        _t598 = logic_pb2.Disjunction(args=[])
        return _t598

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal('(')
        self.consume_literal('exists')
        _t599 = self.parse_bindings()
        bindings108 = _t599
        _t600 = self.parse_formula()
        formula109 = _t600
        self.consume_literal(')')
        _t601 = logic_pb2.Abstraction(vars=(list(bindings108[0]) + list(bindings108[1] if bindings108[1] is not None else [])), value=formula109)
        _t602 = logic_pb2.Exists(body=_t601)
        return _t602

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal('(')
        self.consume_literal('reduce')
        _t603 = self.parse_abstraction()
        abstraction110 = _t603
        _t604 = self.parse_abstraction()
        abstraction_3111 = _t604
        _t605 = self.parse_terms()
        terms112 = _t605
        self.consume_literal(')')
        _t606 = logic_pb2.Reduce(op=abstraction110, body=abstraction_3111, terms=terms112)
        return _t606

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal('(')
        self.consume_literal('terms')
        xs113 = []
        cond114 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond114:
            _t607 = self.parse_term()
            item115 = _t607
            xs113.append(item115)
            cond114 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms116 = xs113
        self.consume_literal(')')
        return terms116

    def parse_term(self) -> logic_pb2.Term:
        
        if self.match_lookahead_literal('true', 0):
            _t608 = 1
        else:
            
            if self.match_lookahead_literal('missing', 0):
                _t609 = 1
            else:
                
                if self.match_lookahead_literal('false', 0):
                    _t610 = 1
                else:
                    
                    if self.match_lookahead_literal('(', 0):
                        _t611 = 1
                    else:
                        
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t612 = 1
                        else:
                            
                            if self.match_lookahead_terminal('SYMBOL', 0):
                                _t613 = 0
                            else:
                                
                                if self.match_lookahead_terminal('STRING', 0):
                                    _t614 = 1
                                else:
                                    
                                    if self.match_lookahead_terminal('INT128', 0):
                                        _t615 = 1
                                    else:
                                        
                                        if self.match_lookahead_terminal('INT', 0):
                                            _t616 = 1
                                        else:
                                            
                                            if self.match_lookahead_terminal('FLOAT', 0):
                                                _t617 = 1
                                            else:
                                                
                                                if self.match_lookahead_terminal('DECIMAL', 0):
                                                    _t618 = 1
                                                else:
                                                    _t618 = -1
                                                _t617 = _t618
                                            _t616 = _t617
                                        _t615 = _t616
                                    _t614 = _t615
                                _t613 = _t614
                            _t612 = _t613
                        _t611 = _t612
                    _t610 = _t611
                _t609 = _t610
            _t608 = _t609
        prediction117 = _t608
        
        if prediction117 == 1:
            _t620 = self.parse_constant()
            constant119 = _t620
            _t621 = logic_pb2.Term(constant=constant119)
            _t619 = _t621
        else:
            
            if prediction117 == 0:
                _t623 = self.parse_var()
                var118 = _t623
                _t624 = logic_pb2.Term(var=var118)
                _t622 = _t624
            else:
                raise ParseError(f"{'Unexpected token in term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t619 = _t622
        return _t619

    def parse_var(self) -> logic_pb2.Var:
        symbol120 = self.consume_terminal('SYMBOL')
        _t625 = logic_pb2.Var(name=symbol120)
        return _t625

    def parse_constant(self) -> logic_pb2.Value:
        _t626 = self.parse_value()
        value121 = _t626
        return value121

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('and')
        xs122 = []
        cond123 = self.match_lookahead_literal('(', 0)
        while cond123:
            _t627 = self.parse_formula()
            item124 = _t627
            xs122.append(item124)
            cond123 = self.match_lookahead_literal('(', 0)
        formulas125 = xs122
        self.consume_literal(')')
        _t628 = logic_pb2.Conjunction(args=formulas125)
        return _t628

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('or')
        xs126 = []
        cond127 = self.match_lookahead_literal('(', 0)
        while cond127:
            _t629 = self.parse_formula()
            item128 = _t629
            xs126.append(item128)
            cond127 = self.match_lookahead_literal('(', 0)
        formulas129 = xs126
        self.consume_literal(')')
        _t630 = logic_pb2.Disjunction(args=formulas129)
        return _t630

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal('(')
        self.consume_literal('not')
        _t631 = self.parse_formula()
        formula130 = _t631
        self.consume_literal(')')
        _t632 = logic_pb2.Not(arg=formula130)
        return _t632

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal('(')
        self.consume_literal('ffi')
        _t633 = self.parse_name()
        name131 = _t633
        _t634 = self.parse_ffi_args()
        ffi_args132 = _t634
        _t635 = self.parse_terms()
        terms133 = _t635
        self.consume_literal(')')
        _t636 = logic_pb2.FFI(name=name131, args=ffi_args132, terms=terms133)
        return _t636

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
            _t637 = self.parse_abstraction()
            item137 = _t637
            xs135.append(item137)
            cond136 = self.match_lookahead_literal('(', 0)
        abstractions138 = xs135
        self.consume_literal(')')
        return abstractions138

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal('(')
        self.consume_literal('atom')
        _t638 = self.parse_relation_id()
        relation_id139 = _t638
        xs140 = []
        cond141 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond141:
            _t639 = self.parse_term()
            item142 = _t639
            xs140.append(item142)
            cond141 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms143 = xs140
        self.consume_literal(')')
        _t640 = logic_pb2.Atom(name=relation_id139, terms=terms143)
        return _t640

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal('(')
        self.consume_literal('pragma')
        _t641 = self.parse_name()
        name144 = _t641
        xs145 = []
        cond146 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond146:
            _t642 = self.parse_term()
            item147 = _t642
            xs145.append(item147)
            cond146 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms148 = xs145
        self.consume_literal(')')
        _t643 = logic_pb2.Pragma(name=name144, terms=terms148)
        return _t643

    def parse_primitive(self) -> logic_pb2.Primitive:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('primitive', 1):
                _t645 = 9
            else:
                
                if self.match_lookahead_literal('>=', 1):
                    _t646 = 4
                else:
                    
                    if self.match_lookahead_literal('>', 1):
                        _t647 = 3
                    else:
                        
                        if self.match_lookahead_literal('=', 1):
                            _t648 = 0
                        else:
                            
                            if self.match_lookahead_literal('<=', 1):
                                _t649 = 2
                            else:
                                
                                if self.match_lookahead_literal('<', 1):
                                    _t650 = 1
                                else:
                                    
                                    if self.match_lookahead_literal('/', 1):
                                        _t651 = 8
                                    else:
                                        
                                        if self.match_lookahead_literal('-', 1):
                                            _t652 = 6
                                        else:
                                            
                                            if self.match_lookahead_literal('+', 1):
                                                _t653 = 5
                                            else:
                                                
                                                if self.match_lookahead_literal('*', 1):
                                                    _t654 = 7
                                                else:
                                                    _t654 = -1
                                                _t653 = _t654
                                            _t652 = _t653
                                        _t651 = _t652
                                    _t650 = _t651
                                _t649 = _t650
                            _t648 = _t649
                        _t647 = _t648
                    _t646 = _t647
                _t645 = _t646
            _t644 = _t645
        else:
            _t644 = -1
        prediction149 = _t644
        
        if prediction149 == 9:
            self.consume_literal('(')
            self.consume_literal('primitive')
            _t656 = self.parse_name()
            name159 = _t656
            xs160 = []
            cond161 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            while cond161:
                _t657 = self.parse_rel_term()
                item162 = _t657
                xs160.append(item162)
                cond161 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            rel_terms163 = xs160
            self.consume_literal(')')
            _t658 = logic_pb2.Primitive(name=name159, terms=rel_terms163)
            _t655 = _t658
        else:
            
            if prediction149 == 8:
                _t660 = self.parse_divide()
                divide158 = _t660
                _t659 = divide158
            else:
                
                if prediction149 == 7:
                    _t662 = self.parse_multiply()
                    multiply157 = _t662
                    _t661 = multiply157
                else:
                    
                    if prediction149 == 6:
                        _t664 = self.parse_minus()
                        minus156 = _t664
                        _t663 = minus156
                    else:
                        
                        if prediction149 == 5:
                            _t666 = self.parse_add()
                            add155 = _t666
                            _t665 = add155
                        else:
                            
                            if prediction149 == 4:
                                _t668 = self.parse_gt_eq()
                                gt_eq154 = _t668
                                _t667 = gt_eq154
                            else:
                                
                                if prediction149 == 3:
                                    _t670 = self.parse_gt()
                                    gt153 = _t670
                                    _t669 = gt153
                                else:
                                    
                                    if prediction149 == 2:
                                        _t672 = self.parse_lt_eq()
                                        lt_eq152 = _t672
                                        _t671 = lt_eq152
                                    else:
                                        
                                        if prediction149 == 1:
                                            _t674 = self.parse_lt()
                                            lt151 = _t674
                                            _t673 = lt151
                                        else:
                                            
                                            if prediction149 == 0:
                                                _t676 = self.parse_eq()
                                                eq150 = _t676
                                                _t675 = eq150
                                            else:
                                                raise ParseError(f"{'Unexpected token in primitive'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t673 = _t675
                                        _t671 = _t673
                                    _t669 = _t671
                                _t667 = _t669
                            _t665 = _t667
                        _t663 = _t665
                    _t661 = _t663
                _t659 = _t661
            _t655 = _t659
        return _t655

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('=')
        _t677 = self.parse_term()
        term164 = _t677
        _t678 = self.parse_term()
        term_3165 = _t678
        self.consume_literal(')')
        _t679 = logic_pb2.RelTerm(term=term164)
        _t680 = logic_pb2.RelTerm(term=term_3165)
        _t681 = logic_pb2.Primitive(name='rel_primitive_eq', terms=[_t679, _t680])
        return _t681

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<')
        _t682 = self.parse_term()
        term166 = _t682
        _t683 = self.parse_term()
        term_3167 = _t683
        self.consume_literal(')')
        _t684 = logic_pb2.RelTerm(term=term166)
        _t685 = logic_pb2.RelTerm(term=term_3167)
        _t686 = logic_pb2.Primitive(name='rel_primitive_lt_monotype', terms=[_t684, _t685])
        return _t686

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<=')
        _t687 = self.parse_term()
        term168 = _t687
        _t688 = self.parse_term()
        term_3169 = _t688
        self.consume_literal(')')
        _t689 = logic_pb2.RelTerm(term=term168)
        _t690 = logic_pb2.RelTerm(term=term_3169)
        _t691 = logic_pb2.Primitive(name='rel_primitive_lt_eq_monotype', terms=[_t689, _t690])
        return _t691

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>')
        _t692 = self.parse_term()
        term170 = _t692
        _t693 = self.parse_term()
        term_3171 = _t693
        self.consume_literal(')')
        _t694 = logic_pb2.RelTerm(term=term170)
        _t695 = logic_pb2.RelTerm(term=term_3171)
        _t696 = logic_pb2.Primitive(name='rel_primitive_gt_monotype', terms=[_t694, _t695])
        return _t696

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>=')
        _t697 = self.parse_term()
        term172 = _t697
        _t698 = self.parse_term()
        term_3173 = _t698
        self.consume_literal(')')
        _t699 = logic_pb2.RelTerm(term=term172)
        _t700 = logic_pb2.RelTerm(term=term_3173)
        _t701 = logic_pb2.Primitive(name='rel_primitive_gt_eq_monotype', terms=[_t699, _t700])
        return _t701

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('+')
        _t702 = self.parse_term()
        term174 = _t702
        _t703 = self.parse_term()
        term_3175 = _t703
        _t704 = self.parse_term()
        term_4176 = _t704
        self.consume_literal(')')
        _t705 = logic_pb2.RelTerm(term=term174)
        _t706 = logic_pb2.RelTerm(term=term_3175)
        _t707 = logic_pb2.RelTerm(term=term_4176)
        _t708 = logic_pb2.Primitive(name='rel_primitive_add_monotype', terms=[_t705, _t706, _t707])
        return _t708

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('-')
        _t709 = self.parse_term()
        term177 = _t709
        _t710 = self.parse_term()
        term_3178 = _t710
        _t711 = self.parse_term()
        term_4179 = _t711
        self.consume_literal(')')
        _t712 = logic_pb2.RelTerm(term=term177)
        _t713 = logic_pb2.RelTerm(term=term_3178)
        _t714 = logic_pb2.RelTerm(term=term_4179)
        _t715 = logic_pb2.Primitive(name='rel_primitive_subtract_monotype', terms=[_t712, _t713, _t714])
        return _t715

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('*')
        _t716 = self.parse_term()
        term180 = _t716
        _t717 = self.parse_term()
        term_3181 = _t717
        _t718 = self.parse_term()
        term_4182 = _t718
        self.consume_literal(')')
        _t719 = logic_pb2.RelTerm(term=term180)
        _t720 = logic_pb2.RelTerm(term=term_3181)
        _t721 = logic_pb2.RelTerm(term=term_4182)
        _t722 = logic_pb2.Primitive(name='rel_primitive_multiply_monotype', terms=[_t719, _t720, _t721])
        return _t722

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('/')
        _t723 = self.parse_term()
        term183 = _t723
        _t724 = self.parse_term()
        term_3184 = _t724
        _t725 = self.parse_term()
        term_4185 = _t725
        self.consume_literal(')')
        _t726 = logic_pb2.RelTerm(term=term183)
        _t727 = logic_pb2.RelTerm(term=term_3184)
        _t728 = logic_pb2.RelTerm(term=term_4185)
        _t729 = logic_pb2.Primitive(name='rel_primitive_divide_monotype', terms=[_t726, _t727, _t728])
        return _t729

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        
        if self.match_lookahead_literal('true', 0):
            _t730 = 1
        else:
            
            if self.match_lookahead_literal('missing', 0):
                _t731 = 1
            else:
                
                if self.match_lookahead_literal('false', 0):
                    _t732 = 1
                else:
                    
                    if self.match_lookahead_literal('(', 0):
                        _t733 = 1
                    else:
                        
                        if self.match_lookahead_literal('#', 0):
                            _t734 = 0
                        else:
                            
                            if self.match_lookahead_terminal('UINT128', 0):
                                _t735 = 1
                            else:
                                
                                if self.match_lookahead_terminal('SYMBOL', 0):
                                    _t736 = 1
                                else:
                                    
                                    if self.match_lookahead_terminal('STRING', 0):
                                        _t737 = 1
                                    else:
                                        
                                        if self.match_lookahead_terminal('INT128', 0):
                                            _t738 = 1
                                        else:
                                            
                                            if self.match_lookahead_terminal('INT', 0):
                                                _t739 = 1
                                            else:
                                                
                                                if self.match_lookahead_terminal('FLOAT', 0):
                                                    _t740 = 1
                                                else:
                                                    
                                                    if self.match_lookahead_terminal('DECIMAL', 0):
                                                        _t741 = 1
                                                    else:
                                                        _t741 = -1
                                                    _t740 = _t741
                                                _t739 = _t740
                                            _t738 = _t739
                                        _t737 = _t738
                                    _t736 = _t737
                                _t735 = _t736
                            _t734 = _t735
                        _t733 = _t734
                    _t732 = _t733
                _t731 = _t732
            _t730 = _t731
        prediction186 = _t730
        
        if prediction186 == 1:
            _t743 = self.parse_term()
            term188 = _t743
            _t744 = logic_pb2.RelTerm(term=term188)
            _t742 = _t744
        else:
            
            if prediction186 == 0:
                _t746 = self.parse_specialized_value()
                specialized_value187 = _t746
                _t747 = logic_pb2.RelTerm(specialized_value=specialized_value187)
                _t745 = _t747
            else:
                raise ParseError(f"{'Unexpected token in rel_term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t742 = _t745
        return _t742

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal('#')
        _t748 = self.parse_value()
        value189 = _t748
        return value189

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        self.consume_literal('(')
        self.consume_literal('relatom')
        _t749 = self.parse_name()
        name190 = _t749
        xs191 = []
        cond192 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond192:
            _t750 = self.parse_rel_term()
            item193 = _t750
            xs191.append(item193)
            cond192 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        rel_terms194 = xs191
        self.consume_literal(')')
        _t751 = logic_pb2.RelAtom(name=name190, terms=rel_terms194)
        return _t751

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal('(')
        self.consume_literal('cast')
        _t752 = self.parse_term()
        term195 = _t752
        _t753 = self.parse_term()
        term_3196 = _t753
        self.consume_literal(')')
        _t754 = logic_pb2.Cast(input=term195, result=term_3196)
        return _t754

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal('(')
        self.consume_literal('attrs')
        xs197 = []
        cond198 = self.match_lookahead_literal('(', 0)
        while cond198:
            _t755 = self.parse_attribute()
            item199 = _t755
            xs197.append(item199)
            cond198 = self.match_lookahead_literal('(', 0)
        attributes200 = xs197
        self.consume_literal(')')
        return attributes200

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal('(')
        self.consume_literal('attribute')
        _t756 = self.parse_name()
        name201 = _t756
        xs202 = []
        cond203 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond203:
            _t757 = self.parse_value()
            item204 = _t757
            xs202.append(item204)
            cond203 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        values205 = xs202
        self.consume_literal(')')
        _t758 = logic_pb2.Attribute(name=name201, args=values205)
        return _t758

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal('(')
        self.consume_literal('algorithm')
        xs206 = []
        cond207 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('UINT128', 0))
        while cond207:
            _t759 = self.parse_relation_id()
            item208 = _t759
            xs206.append(item208)
            cond207 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('UINT128', 0))
        relation_ids209 = xs206
        _t760 = self.parse_script()
        script210 = _t760
        self.consume_literal(')')
        _t761 = logic_pb2.Algorithm(body=script210)
        getattr(_t761, 'global').extend(relation_ids209)
        return _t761

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal('(')
        self.consume_literal('script')
        xs211 = []
        cond212 = self.match_lookahead_literal('(', 0)
        while cond212:
            _t762 = self.parse_construct()
            item213 = _t762
            xs211.append(item213)
            cond212 = self.match_lookahead_literal('(', 0)
        constructs214 = xs211
        self.consume_literal(')')
        _t763 = logic_pb2.Script(constructs=constructs214)
        return _t763

    def parse_construct(self) -> logic_pb2.Construct:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('upsert', 1):
                _t765 = 1
            else:
                
                if self.match_lookahead_literal('monus', 1):
                    _t766 = 1
                else:
                    
                    if self.match_lookahead_literal('monoid', 1):
                        _t767 = 1
                    else:
                        
                        if self.match_lookahead_literal('loop', 1):
                            _t768 = 0
                        else:
                            
                            if self.match_lookahead_literal('break', 1):
                                _t769 = 1
                            else:
                                
                                if self.match_lookahead_literal('assign', 1):
                                    _t770 = 1
                                else:
                                    _t770 = -1
                                _t769 = _t770
                            _t768 = _t769
                        _t767 = _t768
                    _t766 = _t767
                _t765 = _t766
            _t764 = _t765
        else:
            _t764 = -1
        prediction215 = _t764
        
        if prediction215 == 1:
            _t772 = self.parse_instruction()
            instruction217 = _t772
            _t773 = logic_pb2.Construct(instruction=instruction217)
            _t771 = _t773
        else:
            
            if prediction215 == 0:
                _t775 = self.parse_loop()
                loop216 = _t775
                _t776 = logic_pb2.Construct(loop=loop216)
                _t774 = _t776
            else:
                raise ParseError(f"{'Unexpected token in construct'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t771 = _t774
        return _t771

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal('(')
        self.consume_literal('loop')
        _t777 = self.parse_init()
        init218 = _t777
        _t778 = self.parse_script()
        script219 = _t778
        self.consume_literal(')')
        _t779 = logic_pb2.Loop(init=init218, body=script219)
        return _t779

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal('(')
        self.consume_literal('init')
        xs220 = []
        cond221 = self.match_lookahead_literal('(', 0)
        while cond221:
            _t780 = self.parse_instruction()
            item222 = _t780
            xs220.append(item222)
            cond221 = self.match_lookahead_literal('(', 0)
        instructions223 = xs220
        self.consume_literal(')')
        return instructions223

    def parse_instruction(self) -> logic_pb2.Instruction:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('upsert', 1):
                _t782 = 1
            else:
                
                if self.match_lookahead_literal('monus', 1):
                    _t783 = 4
                else:
                    
                    if self.match_lookahead_literal('monoid', 1):
                        _t784 = 3
                    else:
                        
                        if self.match_lookahead_literal('break', 1):
                            _t785 = 2
                        else:
                            
                            if self.match_lookahead_literal('assign', 1):
                                _t786 = 0
                            else:
                                _t786 = -1
                            _t785 = _t786
                        _t784 = _t785
                    _t783 = _t784
                _t782 = _t783
            _t781 = _t782
        else:
            _t781 = -1
        prediction224 = _t781
        
        if prediction224 == 4:
            _t788 = self.parse_monus_def()
            monus_def229 = _t788
            _t789 = logic_pb2.Instruction(monus_def=monus_def229)
            _t787 = _t789
        else:
            
            if prediction224 == 3:
                _t791 = self.parse_monoid_def()
                monoid_def228 = _t791
                _t792 = logic_pb2.Instruction(monoid_def=monoid_def228)
                _t790 = _t792
            else:
                
                if prediction224 == 2:
                    _t794 = self.parse_break()
                    break227 = _t794
                    _t795 = logic_pb2.Instruction()
                    getattr(_t795, 'break').CopyFrom(break227)
                    _t793 = _t795
                else:
                    
                    if prediction224 == 1:
                        _t797 = self.parse_upsert()
                        upsert226 = _t797
                        _t798 = logic_pb2.Instruction(upsert=upsert226)
                        _t796 = _t798
                    else:
                        
                        if prediction224 == 0:
                            _t800 = self.parse_assign()
                            assign225 = _t800
                            _t801 = logic_pb2.Instruction(assign=assign225)
                            _t799 = _t801
                        else:
                            raise ParseError(f"{'Unexpected token in instruction'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t796 = _t799
                    _t793 = _t796
                _t790 = _t793
            _t787 = _t790
        return _t787

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal('(')
        self.consume_literal('assign')
        _t802 = self.parse_relation_id()
        relation_id230 = _t802
        _t803 = self.parse_abstraction()
        abstraction231 = _t803
        
        if self.match_lookahead_literal('(', 0):
            _t805 = self.parse_attrs()
            _t804 = _t805
        else:
            _t804 = None
        attrs232 = _t804
        self.consume_literal(')')
        _t806 = logic_pb2.Assign(name=relation_id230, body=abstraction231, attrs=(attrs232 if attrs232 is not None else []))
        return _t806

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal('(')
        self.consume_literal('upsert')
        _t807 = self.parse_relation_id()
        relation_id233 = _t807
        _t808 = self.parse_abstraction_with_arity()
        abstraction_with_arity234 = _t808
        
        if self.match_lookahead_literal('(', 0):
            _t810 = self.parse_attrs()
            _t809 = _t810
        else:
            _t809 = None
        attrs235 = _t809
        self.consume_literal(')')
        _t811 = logic_pb2.Upsert(name=relation_id233, body=abstraction_with_arity234[0], attrs=(attrs235 if attrs235 is not None else []), value_arity=abstraction_with_arity234[1])
        return _t811

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal('(')
        _t812 = self.parse_bindings()
        bindings236 = _t812
        _t813 = self.parse_formula()
        formula237 = _t813
        self.consume_literal(')')
        _t814 = logic_pb2.Abstraction(vars=(list(bindings236[0]) + list(bindings236[1] if bindings236[1] is not None else [])), value=formula237)
        return (_t814, len(bindings236[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal('(')
        self.consume_literal('break')
        _t815 = self.parse_relation_id()
        relation_id238 = _t815
        _t816 = self.parse_abstraction()
        abstraction239 = _t816
        
        if self.match_lookahead_literal('(', 0):
            _t818 = self.parse_attrs()
            _t817 = _t818
        else:
            _t817 = None
        attrs240 = _t817
        self.consume_literal(')')
        _t819 = logic_pb2.Break(name=relation_id238, body=abstraction239, attrs=(attrs240 if attrs240 is not None else []))
        return _t819

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal('(')
        self.consume_literal('monoid')
        _t820 = self.parse_monoid()
        monoid241 = _t820
        _t821 = self.parse_relation_id()
        relation_id242 = _t821
        _t822 = self.parse_abstraction_with_arity()
        abstraction_with_arity243 = _t822
        
        if self.match_lookahead_literal('(', 0):
            _t824 = self.parse_attrs()
            _t823 = _t824
        else:
            _t823 = None
        attrs244 = _t823
        self.consume_literal(')')
        _t825 = logic_pb2.MonoidDef(monoid=monoid241, name=relation_id242, body=abstraction_with_arity243[0], attrs=(attrs244 if attrs244 is not None else []), value_arity=abstraction_with_arity243[1])
        return _t825

    def parse_monoid(self) -> logic_pb2.Monoid:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('sum', 1):
                _t827 = 3
            else:
                
                if self.match_lookahead_literal('or', 1):
                    _t828 = 0
                else:
                    
                    if self.match_lookahead_literal('min', 1):
                        _t829 = 1
                    else:
                        
                        if self.match_lookahead_literal('max', 1):
                            _t830 = 2
                        else:
                            _t830 = -1
                        _t829 = _t830
                    _t828 = _t829
                _t827 = _t828
            _t826 = _t827
        else:
            _t826 = -1
        prediction245 = _t826
        
        if prediction245 == 3:
            _t832 = self.parse_sum_monoid()
            sum_monoid249 = _t832
            _t833 = logic_pb2.Monoid(sum_monoid=sum_monoid249)
            _t831 = _t833
        else:
            
            if prediction245 == 2:
                _t835 = self.parse_max_monoid()
                max_monoid248 = _t835
                _t836 = logic_pb2.Monoid(max_monoid=max_monoid248)
                _t834 = _t836
            else:
                
                if prediction245 == 1:
                    _t838 = self.parse_min_monoid()
                    min_monoid247 = _t838
                    _t839 = logic_pb2.Monoid(min_monoid=min_monoid247)
                    _t837 = _t839
                else:
                    
                    if prediction245 == 0:
                        _t841 = self.parse_or_monoid()
                        or_monoid246 = _t841
                        _t842 = logic_pb2.Monoid(or_monoid=or_monoid246)
                        _t840 = _t842
                    else:
                        raise ParseError(f"{'Unexpected token in monoid'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t837 = _t840
                _t834 = _t837
            _t831 = _t834
        return _t831

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        self.consume_literal('(')
        self.consume_literal('or')
        self.consume_literal(')')
        _t843 = logic_pb2.OrMonoid()
        return _t843

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        self.consume_literal('(')
        self.consume_literal('min')
        _t844 = self.parse_type()
        type250 = _t844
        self.consume_literal(')')
        _t845 = logic_pb2.MinMonoid(type=type250)
        return _t845

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        self.consume_literal('(')
        self.consume_literal('max')
        _t846 = self.parse_type()
        type251 = _t846
        self.consume_literal(')')
        _t847 = logic_pb2.MaxMonoid(type=type251)
        return _t847

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        self.consume_literal('(')
        self.consume_literal('sum')
        _t848 = self.parse_type()
        type252 = _t848
        self.consume_literal(')')
        _t849 = logic_pb2.SumMonoid(type=type252)
        return _t849

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal('(')
        self.consume_literal('monus')
        _t850 = self.parse_monoid()
        monoid253 = _t850
        _t851 = self.parse_relation_id()
        relation_id254 = _t851
        _t852 = self.parse_abstraction_with_arity()
        abstraction_with_arity255 = _t852
        
        if self.match_lookahead_literal('(', 0):
            _t854 = self.parse_attrs()
            _t853 = _t854
        else:
            _t853 = None
        attrs256 = _t853
        self.consume_literal(')')
        _t855 = logic_pb2.MonusDef(monoid=monoid253, name=relation_id254, body=abstraction_with_arity255[0], attrs=(attrs256 if attrs256 is not None else []), value_arity=abstraction_with_arity255[1])
        return _t855

    def parse_constraint(self) -> logic_pb2.Constraint:
        self.consume_literal('(')
        self.consume_literal('functional_dependency')
        _t856 = self.parse_relation_id()
        relation_id257 = _t856
        _t857 = self.parse_abstraction()
        abstraction258 = _t857
        _t858 = self.parse_functional_dependency_keys()
        functional_dependency_keys259 = _t858
        _t859 = self.parse_functional_dependency_values()
        functional_dependency_values260 = _t859
        self.consume_literal(')')
        _t860 = logic_pb2.FunctionalDependency(guard=abstraction258, keys=functional_dependency_keys259, values=functional_dependency_values260)
        _t861 = logic_pb2.Constraint(name=relation_id257, functional_dependency=_t860)
        return _t861

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('keys')
        xs261 = []
        cond262 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond262:
            _t862 = self.parse_var()
            item263 = _t862
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
            _t863 = self.parse_var()
            item267 = _t863
            xs265.append(item267)
            cond266 = self.match_lookahead_terminal('SYMBOL', 0)
        vars268 = xs265
        self.consume_literal(')')
        return vars268

    def parse_data(self) -> logic_pb2.Data:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('rel_edb', 1):
                _t865 = 0
            else:
                
                if self.match_lookahead_literal('csv_data', 1):
                    _t866 = 2
                else:
                    
                    if self.match_lookahead_literal('betree_relation', 1):
                        _t867 = 1
                    else:
                        _t867 = -1
                    _t866 = _t867
                _t865 = _t866
            _t864 = _t865
        else:
            _t864 = -1
        prediction269 = _t864
        
        if prediction269 == 2:
            _t869 = self.parse_csv_data()
            csv_data272 = _t869
            _t870 = logic_pb2.Data(csv_data=csv_data272)
            _t868 = _t870
        else:
            
            if prediction269 == 1:
                _t872 = self.parse_betree_relation()
                betree_relation271 = _t872
                _t873 = logic_pb2.Data(betree_relation=betree_relation271)
                _t871 = _t873
            else:
                
                if prediction269 == 0:
                    _t875 = self.parse_rel_edb()
                    rel_edb270 = _t875
                    _t876 = logic_pb2.Data(rel_edb=rel_edb270)
                    _t874 = _t876
                else:
                    raise ParseError(f"{'Unexpected token in data'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t871 = _t874
            _t868 = _t871
        return _t868

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        self.consume_literal('(')
        self.consume_literal('rel_edb')
        _t877 = self.parse_relation_id()
        relation_id273 = _t877
        _t878 = self.parse_rel_edb_path()
        rel_edb_path274 = _t878
        _t879 = self.parse_rel_edb_types()
        rel_edb_types275 = _t879
        self.consume_literal(')')
        _t880 = logic_pb2.RelEDB(target_id=relation_id273, path=rel_edb_path274, types=rel_edb_types275)
        return _t880

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
            _t881 = self.parse_type()
            item282 = _t881
            xs280.append(item282)
            cond281 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types283 = xs280
        self.consume_literal(']')
        return types283

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        self.consume_literal('(')
        self.consume_literal('betree_relation')
        _t882 = self.parse_relation_id()
        relation_id284 = _t882
        _t883 = self.parse_betree_info()
        betree_info285 = _t883
        self.consume_literal(')')
        _t884 = logic_pb2.BeTreeRelation(name=relation_id284, relation_info=betree_info285)
        return _t884

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        self.consume_literal('(')
        self.consume_literal('betree_info')
        _t885 = self.parse_betree_info_key_types()
        betree_info_key_types286 = _t885
        _t886 = self.parse_betree_info_value_types()
        betree_info_value_types287 = _t886
        _t887 = self.parse_config_dict()
        config_dict288 = _t887
        self.consume_literal(')')
        _t888 = self.construct_betree_info(betree_info_key_types286, betree_info_value_types287, config_dict288)
        return _t888

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('key_types')
        xs289 = []
        cond290 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond290:
            _t889 = self.parse_type()
            item291 = _t889
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
            _t890 = self.parse_type()
            item295 = _t890
            xs293.append(item295)
            cond294 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types296 = xs293
        self.consume_literal(')')
        return types296

    def parse_csv_data(self) -> logic_pb2.CSVData:
        self.consume_literal('(')
        self.consume_literal('csv_data')
        _t891 = self.parse_csvlocator()
        csvlocator297 = _t891
        _t892 = self.parse_csv_config()
        csv_config298 = _t892
        _t893 = self.parse_csv_columns()
        csv_columns299 = _t893
        _t894 = self.parse_csv_asof()
        csv_asof300 = _t894
        self.consume_literal(')')
        _t895 = logic_pb2.CSVData(locator=csvlocator297, config=csv_config298, columns=csv_columns299, asof=csv_asof300)
        return _t895

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        self.consume_literal('(')
        self.consume_literal('csv_locator')
        
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('paths', 1)):
            _t897 = self.parse_csv_locator_paths()
            _t896 = _t897
        else:
            _t896 = None
        csv_locator_paths301 = _t896
        
        if self.match_lookahead_literal('(', 0):
            _t899 = self.parse_csv_locator_inline_data()
            _t898 = _t899
        else:
            _t898 = None
        csv_locator_inline_data302 = _t898
        self.consume_literal(')')
        _t900 = logic_pb2.CSVLocator(paths=(csv_locator_paths301 if csv_locator_paths301 is not None else []), inline_data=(csv_locator_inline_data302 if csv_locator_inline_data302 is not None else '').encode())
        return _t900

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
        _t901 = self.parse_config_dict()
        config_dict308 = _t901
        self.consume_literal(')')
        _t902 = self.construct_csv_config(config_dict308)
        return _t902

    def parse_csv_columns(self) -> Sequence[logic_pb2.CSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs309 = []
        cond310 = self.match_lookahead_literal('(', 0)
        while cond310:
            _t903 = self.parse_csv_column()
            item311 = _t903
            xs309.append(item311)
            cond310 = self.match_lookahead_literal('(', 0)
        csv_columns312 = xs309
        self.consume_literal(')')
        return csv_columns312

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        string313 = self.consume_terminal('STRING')
        _t904 = self.parse_relation_id()
        relation_id314 = _t904
        self.consume_literal('[')
        xs315 = []
        cond316 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond316:
            _t905 = self.parse_type()
            item317 = _t905
            xs315.append(item317)
            cond316 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types318 = xs315
        self.consume_literal(']')
        self.consume_literal(')')
        _t906 = logic_pb2.CSVColumn(column_name=string313, target_id=relation_id314, types=types318)
        return _t906

    def parse_csv_asof(self) -> str:
        self.consume_literal('(')
        self.consume_literal('asof')
        string319 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return string319

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal('(')
        self.consume_literal('undefine')
        _t907 = self.parse_fragment_id()
        fragment_id320 = _t907
        self.consume_literal(')')
        _t908 = transactions_pb2.Undefine(fragment_id=fragment_id320)
        return _t908

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal('(')
        self.consume_literal('context')
        xs321 = []
        cond322 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('UINT128', 0))
        while cond322:
            _t909 = self.parse_relation_id()
            item323 = _t909
            xs321.append(item323)
            cond322 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('UINT128', 0))
        relation_ids324 = xs321
        self.consume_literal(')')
        _t910 = transactions_pb2.Context(relations=relation_ids324)
        return _t910

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal('(')
        self.consume_literal('reads')
        xs325 = []
        cond326 = self.match_lookahead_literal('(', 0)
        while cond326:
            _t911 = self.parse_read()
            item327 = _t911
            xs325.append(item327)
            cond326 = self.match_lookahead_literal('(', 0)
        reads328 = xs325
        self.consume_literal(')')
        return reads328

    def parse_read(self) -> transactions_pb2.Read:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('what_if', 1):
                _t913 = 2
            else:
                
                if self.match_lookahead_literal('output', 1):
                    _t914 = 1
                else:
                    
                    if self.match_lookahead_literal('export', 1):
                        _t915 = 4
                    else:
                        
                        if self.match_lookahead_literal('demand', 1):
                            _t916 = 0
                        else:
                            
                            if self.match_lookahead_literal('abort', 1):
                                _t917 = 3
                            else:
                                _t917 = -1
                            _t916 = _t917
                        _t915 = _t916
                    _t914 = _t915
                _t913 = _t914
            _t912 = _t913
        else:
            _t912 = -1
        prediction329 = _t912
        
        if prediction329 == 4:
            _t919 = self.parse_export()
            export334 = _t919
            _t920 = transactions_pb2.Read(export=export334)
            _t918 = _t920
        else:
            
            if prediction329 == 3:
                _t922 = self.parse_abort()
                abort333 = _t922
                _t923 = transactions_pb2.Read(abort=abort333)
                _t921 = _t923
            else:
                
                if prediction329 == 2:
                    _t925 = self.parse_what_if()
                    what_if332 = _t925
                    _t926 = transactions_pb2.Read(what_if=what_if332)
                    _t924 = _t926
                else:
                    
                    if prediction329 == 1:
                        _t928 = self.parse_output()
                        output331 = _t928
                        _t929 = transactions_pb2.Read(output=output331)
                        _t927 = _t929
                    else:
                        
                        if prediction329 == 0:
                            _t931 = self.parse_demand()
                            demand330 = _t931
                            _t932 = transactions_pb2.Read(demand=demand330)
                            _t930 = _t932
                        else:
                            raise ParseError(f"{'Unexpected token in read'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t927 = _t930
                    _t924 = _t927
                _t921 = _t924
            _t918 = _t921
        return _t918

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal('(')
        self.consume_literal('demand')
        _t933 = self.parse_relation_id()
        relation_id335 = _t933
        self.consume_literal(')')
        _t934 = transactions_pb2.Demand(relation_id=relation_id335)
        return _t934

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal('(')
        self.consume_literal('output')
        _t935 = self.parse_name()
        name336 = _t935
        _t936 = self.parse_relation_id()
        relation_id337 = _t936
        self.consume_literal(')')
        _t937 = transactions_pb2.Output(name=name336, relation_id=relation_id337)
        return _t937

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal('(')
        self.consume_literal('what_if')
        _t938 = self.parse_name()
        name338 = _t938
        _t939 = self.parse_epoch()
        epoch339 = _t939
        self.consume_literal(')')
        _t940 = transactions_pb2.WhatIf(branch=name338, epoch=epoch339)
        return _t940

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal('(')
        self.consume_literal('abort')
        
        if (self.match_lookahead_literal(':', 0) and self.match_lookahead_terminal('SYMBOL', 1)):
            _t942 = self.parse_name()
            _t941 = _t942
        else:
            _t941 = None
        name340 = _t941
        _t943 = self.parse_relation_id()
        relation_id341 = _t943
        self.consume_literal(')')
        _t944 = transactions_pb2.Abort(name=(name340 if name340 is not None else 'abort'), relation_id=relation_id341)
        return _t944

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal('(')
        self.consume_literal('export')
        _t945 = self.parse_export_csv_config()
        export_csv_config342 = _t945
        self.consume_literal(')')
        _t946 = transactions_pb2.Export(csv_config=export_csv_config342)
        return _t946

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('export_csv_config_v2', 1):
                _t948 = 0
            else:
                
                if self.match_lookahead_literal('export_csv_config', 1):
                    _t949 = 1
                else:
                    _t949 = -1
                _t948 = _t949
            _t947 = _t948
        else:
            _t947 = -1
        prediction343 = _t947
        
        if prediction343 == 1:
            self.consume_literal('(')
            self.consume_literal('export_csv_config')
            _t951 = self.parse_export_csv_path()
            export_csv_path347 = _t951
            self.consume_literal('(')
            self.consume_literal('columns')
            xs348 = []
            cond349 = self.match_lookahead_literal('(', 0)
            while cond349:
                _t952 = self.parse_export_csv_column()
                item350 = _t952
                xs348.append(item350)
                cond349 = self.match_lookahead_literal('(', 0)
            export_csv_columns351 = xs348
            self.consume_literal(')')
            _t953 = self.parse_config_dict()
            config_dict352 = _t953
            self.consume_literal(')')
            _t954 = self.construct_export_csv_config(export_csv_path347, export_csv_columns351, config_dict352)
            _t950 = _t954
        else:
            
            if prediction343 == 0:
                self.consume_literal('(')
                self.consume_literal('export_csv_config_v2')
                _t956 = self.parse_export_csv_path()
                export_csv_path344 = _t956
                _t957 = self.parse_export_csv_source()
                export_csv_source345 = _t957
                _t958 = self.parse_csv_config()
                csv_config346 = _t958
                self.consume_literal(')')
                _t959 = self.construct_export_csv_config_with_source(export_csv_path344, export_csv_source345, csv_config346)
                _t955 = _t959
            else:
                raise ParseError(f"{'Unexpected token in export_csv_config'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t950 = _t955
        return _t950

    def parse_export_csv_path(self) -> str:
        self.consume_literal('(')
        self.consume_literal('path')
        string353 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return string353

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('table_def', 1):
                _t961 = 1
            else:
                
                if self.match_lookahead_literal('gnf_columns', 1):
                    _t962 = 0
                else:
                    _t962 = -1
                _t961 = _t962
            _t960 = _t961
        else:
            _t960 = -1
        prediction354 = _t960
        
        if prediction354 == 1:
            self.consume_literal('(')
            self.consume_literal('table_def')
            _t964 = self.parse_relation_id()
            relation_id359 = _t964
            self.consume_literal(')')
            _t965 = transactions_pb2.ExportCSVSource(table_def=relation_id359)
            _t963 = _t965
        else:
            
            if prediction354 == 0:
                self.consume_literal('(')
                self.consume_literal('gnf_columns')
                xs355 = []
                cond356 = self.match_lookahead_literal('(', 0)
                while cond356:
                    _t967 = self.parse_export_csv_column()
                    item357 = _t967
                    xs355.append(item357)
                    cond356 = self.match_lookahead_literal('(', 0)
                export_csv_columns358 = xs355
                self.consume_literal(')')
                _t968 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns358)
                _t969 = transactions_pb2.ExportCSVSource(gnf_columns=_t968)
                _t966 = _t969
            else:
                raise ParseError(f"{'Unexpected token in export_csv_source'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t963 = _t966
        return _t963

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        string360 = self.consume_terminal('STRING')
        _t970 = self.parse_relation_id()
        relation_id361 = _t970
        self.consume_literal(')')
        _t971 = transactions_pb2.ExportCSVColumn(column_name=string360, column_data=relation_id361)
        return _t971


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
