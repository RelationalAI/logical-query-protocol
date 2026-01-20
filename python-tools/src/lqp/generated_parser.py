"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.

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
            ('STRING', re.compile(r'"(?:[^"\\]|\\.)*"'), lambda x: Lexer.scan_string(x)),
            ('DECIMAL', re.compile(r'[-]?\d+\.\d+d\d+'), lambda x: Lexer.scan_decimal(x)),
            ('FLOAT', re.compile(r'(?:[-]?\d+\.\d+|inf|nan)'), lambda x: Lexer.scan_float(x)),
            ('INT128', re.compile(r'[-]?\d+i128'), lambda x: Lexer.scan_int128(x)),
            ('UINT128', re.compile(r'0x[0-9a-fA-F]+'), lambda x: Lexer.scan_uint128(x)),
            ('INT', re.compile(r'[-]?\d+'), lambda x: Lexer.scan_int(x)),
            ('SYMBOL', re.compile(r'[a-zA-Z_][a-zA-Z0-9_.-]*'), lambda x: Lexer.scan_symbol(x)),
            ('COLON_SYMBOL', re.compile(r':[a-zA-Z_][a-zA-Z0-9_.-]*'), lambda x: Lexer.scan_colon_symbol(x)),
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
                raise ParseError(f'Unexpected character at position {{self.pos}}: {{self.input[self.pos]!r}}')

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
            raise ValueError(f'Invalid decimal format: {{d}}')
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
        self._current_fragment_id = None
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

    @staticmethod
    def _extract_value(val: Any, value_type: str, default: Any) -> Any:
        """Extract typed value from a protobuf Value wrapper."""
        if val is None:
            return default
        if value_type == 'int':
            return val.int_value if val.HasField('int_value') else default
        elif value_type == 'float':
            return val.float_value if val.HasField('float_value') else default
        elif value_type == 'str':
            return val.string_value if val.HasField('string_value') else default
        elif value_type == 'bool':
            return val.boolean_value if val.HasField('boolean_value') else default
        elif value_type == 'uint128':
            if hasattr(val, 'uint128_value') and val.HasField('uint128_value'):
                return val.uint128_value
            return val if val is not None else default
        elif value_type == 'bytes':
            if hasattr(val, 'string_value') and val.HasField('string_value'):
                return val.string_value.encode()
            return val if val is not None else default
        elif value_type == 'str_list':
            if val.HasField('string_value'):
                return [val.string_value]
            return default
        return default

    @staticmethod
    def _construct_from_schema(config_list: List[Tuple[str, Any]], schema: List[Tuple[str, str, str, Any]], message_class: type) -> Any:
        """Construct a protobuf message from config using a schema.

        Args:
            config_list: List of (key, value) tuples from parsing
            schema: List of (config_key, proto_field, value_type, default) tuples
            message_class: The protobuf message class to construct

        Returns:
            An instance of message_class with fields populated from config
        """
        config = {k: v for k, v in config_list}
        kwargs = {}
        for config_key, proto_field, value_type, default in schema:
            val = config.get(config_key)
            kwargs[proto_field] = Parser._extract_value(val, value_type, default)
        return message_class(**kwargs)

    def construct_configure(self, config_dict: List[Tuple[str, logic_pb2.Value]]) -> Any:
        """Construct Configure from config dictionary."""
        config = {k: v for k, v in config_dict}

        # Special handling for maintenance level enum
        maintenance_level = 'MAINTENANCE_LEVEL_OFF'
        maintenance_level_val = config.get('ivm.maintenance_level')
        if maintenance_level_val and maintenance_level_val.HasField('string_value'):
            level_str = maintenance_level_val.string_value.upper()
            if level_str in ('OFF', 'AUTO', 'ALL'):
                maintenance_level = f'MAINTENANCE_LEVEL_{level_str}'
            else:
                maintenance_level = level_str

        ivm_config = transactions_pb2.IVMConfig(level=maintenance_level)
        semantics_version = self._extract_value(config.get('semantics_version'), 'int', 0)
        return transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)

    def export_csv_config(self, path: str, columns: List[Any], config_dict: List[Tuple[str, logic_pb2.Value]]) -> Any:
        """Construct ExportCsvConfig from path, columns, and config dictionary."""
        schema = [
            ('partition_size', 'partition_size', 'int', 0),
            ('compression', 'compression', 'str', ''),
            ('syntax_header_row', 'syntax_header_row', 'bool', True),
            ('syntax_missing_string', 'syntax_missing_string', 'str', ''),
            ('syntax_delim', 'syntax_delim', 'str', ','),
            ('syntax_quotechar', 'syntax_quotechar', 'str', '"'),
            ('syntax_escapechar', 'syntax_escapechar', 'str', '\\'),
        ]
        msg = self._construct_from_schema(config_dict, schema, transactions_pb2.ExportCSVConfig)
        msg.path = path
        msg.data_columns.extend(columns)
        return msg

    def construct_betree_info(self, key_types: List[Any], value_types: List[Any], config_dict: List[Tuple[str, Any]]) -> Any:
        """Construct BeTreeInfo from key_types, value_types, and config dictionary."""
        config_schema = [
            ('betree_config_epsilon', 'epsilon', 'float', 0.5),
            ('betree_config_max_pivots', 'max_pivots', 'int', 4),
            ('betree_config_max_deltas', 'max_deltas', 'int', 16),
            ('betree_config_max_leaf', 'max_leaf', 'int', 16),
        ]
        storage_config = self._construct_from_schema(config_dict, config_schema, logic_pb2.BeTreeConfig)

        locator_schema = [
            ('betree_locator_root_pageid', 'root_pageid', 'uint128', None),
            ('betree_locator_inline_data', 'inline_data', 'bytes', None),
            ('betree_locator_element_count', 'element_count', 'int', 0),
            ('betree_locator_tree_height', 'tree_height', 'int', 0),
        ]
        relation_locator = self._construct_from_schema(config_dict, locator_schema, logic_pb2.BeTreeLocator)

        return logic_pb2.BeTreeInfo(
            key_types=key_types,
            value_types=value_types,
            storage_config=storage_config,
            relation_locator=relation_locator
        )

    def construct_csv_config(self, config_dict: List[Tuple[str, Any]]) -> Any:
        """Construct CSVConfig from config dictionary."""
        schema = [
            ('csv_header_row', 'header_row', 'int', 1),
            ('csv_skip', 'skip', 'int', 0),
            ('csv_new_line', 'new_line', 'str', ''),
            ('csv_delimiter', 'delimiter', 'str', ','),
            ('csv_quotechar', 'quotechar', 'str', '"'),
            ('csv_escapechar', 'escapechar', 'str', '"'),
            ('csv_comment', 'comment', 'str', ''),
            ('csv_missing_strings', 'missing_strings', 'str_list', []),
            ('csv_decimal_separator', 'decimal_separator', 'str', '.'),
            ('csv_encoding', 'encoding', 'str', 'utf-8'),
            ('csv_compression', 'compression', 'str', 'auto'),
        ]
        return self._construct_from_schema(config_dict, schema, logic_pb2.CSVConfig)

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

    def parse_transaction(self) -> transactions_pb2.Transaction:
        self.consume_literal('(')
        self.consume_literal('transaction')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('configure', 1)):
            _t320 = self.parse_configure()
            _t319 = _t320
        else:
            _t319 = None
        configure0 = _t319
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('sync', 1)):
            _t322 = self.parse_sync()
            _t321 = _t322
        else:
            _t321 = None
        sync1 = _t321
        xs2 = []
        cond3 = self.match_lookahead_literal('(', 0)
        while cond3:
            _t323 = self.parse_epoch()
            xs2.append(_t323)
            cond3 = self.match_lookahead_literal('(', 0)
        epochs4 = xs2
        self.consume_literal(')')
        _t324 = transactions_pb2.Transaction(epochs=epochs4, configure=(configure0 if configure0 is not None else self.construct_configure([])), sync=sync1)
        return _t324

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal('(')
        self.consume_literal('configure')
        _t325 = self.parse_config_dict()
        config_dict5 = _t325
        self.consume_literal(')')
        return self.construct_configure(config_dict5)

    def parse_config_dict(self) -> list[tuple[str, logic_pb2.Value]]:
        self.consume_literal('{')
        xs6 = []
        cond7 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond7:
            _t326 = self.parse_config_key_value()
            xs6.append(_t326)
            cond7 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        x8 = xs6
        self.consume_literal('}')
        return x8

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        symbol9 = self.consume_terminal('COLON_SYMBOL')
        _t327 = self.parse_value()
        value10 = _t327
        return (symbol9, value10,)

    def parse_value(self) -> logic_pb2.Value:
        if self.match_lookahead_literal('true', 0):
            _t328 = 9
        else:
            if self.match_lookahead_literal('missing', 0):
                _t329 = 8
            else:
                if self.match_lookahead_literal('false', 0):
                    _t330 = 9
                else:
                    if self.match_lookahead_literal('(', 0):
                        if self.match_lookahead_literal('datetime', 1):
                            _t333 = 1
                        else:
                            if self.match_lookahead_literal('date', 1):
                                _t334 = 0
                            else:
                                _t334 = -1
                            _t333 = _t334
                        _t331 = _t333
                    else:
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t335 = 5
                        else:
                            if self.match_lookahead_terminal('STRING', 0):
                                _t336 = 2
                            else:
                                if self.match_lookahead_terminal('INT128', 0):
                                    _t337 = 6
                                else:
                                    if self.match_lookahead_terminal('INT', 0):
                                        _t338 = 3
                                    else:
                                        if self.match_lookahead_terminal('FLOAT', 0):
                                            _t339 = 4
                                        else:
                                            if self.match_lookahead_terminal('DECIMAL', 0):
                                                _t340 = 7
                                            else:
                                                _t340 = -1
                                            _t339 = _t340
                                        _t338 = _t339
                                    _t337 = _t338
                                _t336 = _t337
                            _t335 = _t336
                        _t331 = _t335
                    _t330 = _t331
                _t329 = _t330
            _t328 = _t329
        prediction11 = _t328
        if prediction11 == 9:
            _t342 = self.parse_boolean_value()
            value20 = _t342
            _t343 = logic_pb2.Value(boolean_value=value20)
            _t341 = _t343
        else:
            if prediction11 == 8:
                self.consume_literal('missing')
                _t345 = logic_pb2.MissingValue()
                _t346 = logic_pb2.Value(missing_value=_t345)
                _t344 = _t346
            else:
                if prediction11 == 7:
                    value19 = self.consume_terminal('DECIMAL')
                    _t348 = logic_pb2.Value(decimal_value=value19)
                    _t347 = _t348
                else:
                    if prediction11 == 6:
                        value18 = self.consume_terminal('INT128')
                        _t350 = logic_pb2.Value(int128_value=value18)
                        _t349 = _t350
                    else:
                        if prediction11 == 5:
                            value17 = self.consume_terminal('UINT128')
                            _t352 = logic_pb2.Value(uint128_value=value17)
                            _t351 = _t352
                        else:
                            if prediction11 == 4:
                                value16 = self.consume_terminal('FLOAT')
                                _t354 = logic_pb2.Value(float_value=value16)
                                _t353 = _t354
                            else:
                                if prediction11 == 3:
                                    value15 = self.consume_terminal('INT')
                                    _t356 = logic_pb2.Value(int_value=value15)
                                    _t355 = _t356
                                else:
                                    if prediction11 == 2:
                                        value14 = self.consume_terminal('STRING')
                                        _t358 = logic_pb2.Value(string_value=value14)
                                        _t357 = _t358
                                    else:
                                        if prediction11 == 1:
                                            _t360 = self.parse_datetime()
                                            value13 = _t360
                                            _t361 = logic_pb2.Value(datetime_value=value13)
                                            _t359 = _t361
                                        else:
                                            if prediction11 == 0:
                                                _t363 = self.parse_date()
                                                value12 = _t363
                                                _t364 = logic_pb2.Value(date_value=value12)
                                                _t362 = _t364
                                            else:
                                                raise ParseError(f"{'Unexpected token in value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t362 = None
                                            _t359 = _t362
                                        _t357 = _t359
                                    _t355 = _t357
                                _t353 = _t355
                            _t351 = _t353
                        _t349 = _t351
                    _t347 = _t349
                _t344 = _t347
            _t341 = _t344
        return _t341

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal('(')
        self.consume_literal('date')
        year21 = self.consume_terminal('INT')
        month22 = self.consume_terminal('INT')
        day23 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t365 = logic_pb2.DateValue(year=year21, month=month22, day=day23)
        return _t365

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
            _t366 = self.consume_terminal('INT')
        else:
            _t366 = None
        microsecond30 = _t366
        self.consume_literal(')')
        _t367 = logic_pb2.DateTimeValue(year=year24, month=month25, day=day26, hour=hour27, minute=minute28, second=second29, microsecond=(microsecond30 if microsecond30 is not None else 0))
        return _t367

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal('true', 0):
            _t368 = 0
        else:
            _t368 = (self.match_lookahead_literal('false', 0) or -1)
        prediction31 = _t368
        if prediction31 == 1:
            self.consume_literal('false')
            _t369 = False
        else:
            if prediction31 == 0:
                self.consume_literal('true')
                _t370 = True
            else:
                raise ParseError(f"{'Unexpected token in boolean_value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t370 = None
            _t369 = _t370
        return _t369

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal('(')
        self.consume_literal('sync')
        xs32 = []
        cond33 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond33:
            _t371 = self.parse_fragment_id()
            xs32.append(_t371)
            cond33 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        fragments34 = xs32
        self.consume_literal(')')
        _t372 = transactions_pb2.Sync(fragments=fragments34)
        return _t372

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        symbol35 = self.consume_terminal('COLON_SYMBOL')
        return fragments_pb2.FragmentId(id=symbol35.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal('(')
        self.consume_literal('epoch')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('writes', 1)):
            _t374 = self.parse_epoch_writes()
            _t373 = _t374
        else:
            _t373 = None
        writes36 = _t373
        if self.match_lookahead_literal('(', 0):
            _t376 = self.parse_epoch_reads()
            _t375 = _t376
        else:
            _t375 = None
        reads37 = _t375
        self.consume_literal(')')
        _t377 = transactions_pb2.Epoch(writes=(writes36 if writes36 is not None else []), reads=(reads37 if reads37 is not None else []))
        return _t377

    def parse_epoch_writes(self) -> list[transactions_pb2.Write]:
        self.consume_literal('(')
        self.consume_literal('writes')
        xs38 = []
        cond39 = self.match_lookahead_literal('(', 0)
        while cond39:
            _t378 = self.parse_write()
            xs38.append(_t378)
            cond39 = self.match_lookahead_literal('(', 0)
        x40 = xs38
        self.consume_literal(')')
        return x40

    def parse_write(self) -> transactions_pb2.Write:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('undefine', 1):
                _t382 = 1
            else:
                if self.match_lookahead_literal('define', 1):
                    _t383 = 0
                else:
                    if self.match_lookahead_literal('context', 1):
                        _t384 = 2
                    else:
                        _t384 = -1
                    _t383 = _t384
                _t382 = _t383
            _t379 = _t382
        else:
            _t379 = -1
        prediction41 = _t379
        if prediction41 == 2:
            _t386 = self.parse_context()
            value44 = _t386
            _t387 = transactions_pb2.Write(context=value44)
            _t385 = _t387
        else:
            if prediction41 == 1:
                _t389 = self.parse_undefine()
                value43 = _t389
                _t390 = transactions_pb2.Write(undefine=value43)
                _t388 = _t390
            else:
                if prediction41 == 0:
                    _t392 = self.parse_define()
                    value42 = _t392
                    _t393 = transactions_pb2.Write(define=value42)
                    _t391 = _t393
                else:
                    raise ParseError(f"{'Unexpected token in write'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t391 = None
                _t388 = _t391
            _t385 = _t388
        return _t385

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal('(')
        self.consume_literal('define')
        _t394 = self.parse_fragment()
        fragment45 = _t394
        self.consume_literal(')')
        _t395 = transactions_pb2.Define(fragment=fragment45)
        return _t395

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal('(')
        self.consume_literal('fragment')
        _t396 = self.parse_new_fragment_id()
        fragment_id46 = _t396
        xs47 = []
        cond48 = self.match_lookahead_literal('(', 0)
        while cond48:
            _t397 = self.parse_declaration()
            xs47.append(_t397)
            cond48 = self.match_lookahead_literal('(', 0)
        declarations49 = xs47
        self.consume_literal(')')
        return self.construct_fragment(fragment_id46, declarations49)

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        _t398 = self.parse_fragment_id()
        fragment_id50 = _t398
        self.start_fragment(fragment_id50)
        return fragment_id50

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('rel_edb', 1):
                _t400 = 3
            else:
                if self.match_lookahead_literal('functional_dependency', 1):
                    _t401 = 2
                else:
                    if self.match_lookahead_literal('def', 1):
                        _t402 = 0
                    else:
                        if self.match_lookahead_literal('csv_data', 1):
                            _t403 = 3
                        else:
                            if self.match_lookahead_literal('betree_relation', 1):
                                _t404 = 3
                            else:
                                _t404 = (self.match_lookahead_literal('algorithm', 1) or -1)
                            _t403 = _t404
                        _t402 = _t403
                    _t401 = _t402
                _t400 = _t401
            _t399 = _t400
        else:
            _t399 = -1
        prediction51 = _t399
        if prediction51 == 3:
            _t406 = self.parse_data()
            value55 = _t406
            _t407 = logic_pb2.Declaration(data=value55)
            _t405 = _t407
        else:
            if prediction51 == 2:
                _t409 = self.parse_constraint()
                value54 = _t409
                _t410 = logic_pb2.Declaration(constraint=value54)
                _t408 = _t410
            else:
                if prediction51 == 1:
                    _t412 = self.parse_algorithm()
                    value53 = _t412
                    _t413 = logic_pb2.Declaration(algorithm=value53)
                    _t411 = _t413
                else:
                    if prediction51 == 0:
                        _t415 = self.parse_def()
                        value52 = _t415
                        _t416 = logic_pb2.Declaration(**{'def': value52})
                        _t414 = _t416
                    else:
                        raise ParseError(f"{'Unexpected token in declaration'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t414 = None
                    _t411 = _t414
                _t408 = _t411
            _t405 = _t408
        return _t405

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal('(')
        self.consume_literal('def')
        _t417 = self.parse_relation_id()
        name56 = _t417
        _t418 = self.parse_abstraction()
        body57 = _t418
        if self.match_lookahead_literal('(', 0):
            _t420 = self.parse_attrs()
            _t419 = _t420
        else:
            _t419 = None
        attrs58 = _t419
        self.consume_literal(')')
        _t421 = logic_pb2.Def(name=name56, body=body57, attrs=(attrs58 if attrs58 is not None else []))
        return _t421

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_terminal('INT', 0):
            _t423 = 1
        else:
            if self.match_lookahead_terminal('COLON_SYMBOL', 0):
                _t424 = 0
            else:
                _t424 = -1
            _t423 = _t424
        prediction59 = _t423
        if prediction59 == 1:
            INT61 = self.consume_terminal('INT')
            _t425 = logic_pb2.RelationId(id_low=INT61 & 0xFFFFFFFFFFFFFFFF, id_high=(INT61 >> 64) & 0xFFFFFFFFFFFFFFFF)
        else:
            if prediction59 == 0:
                symbol60 = self.consume_terminal('COLON_SYMBOL')
                _t426 = self.relation_id_from_string(symbol60)
            else:
                raise ParseError(f"{'Unexpected token in relation_id'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t426 = None
            _t425 = _t426
        return _t425

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal('(')
        _t427 = self.parse_bindings()
        bindings62 = _t427
        _t428 = self.parse_formula()
        formula63 = _t428
        self.consume_literal(')')
        _t429 = logic_pb2.Abstraction(vars=(bindings62[0] + (bindings62[1] if bindings62[1] is not None else [])), value=formula63)
        return _t429

    def parse_bindings(self) -> tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]:
        self.consume_literal('[')
        xs64 = []
        cond65 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond65:
            _t430 = self.parse_binding()
            xs64.append(_t430)
            cond65 = self.match_lookahead_terminal('SYMBOL', 0)
        keys66 = xs64
        if self.match_lookahead_literal('|', 0):
            _t432 = self.parse_value_bindings()
            _t431 = _t432
        else:
            _t431 = None
        values67 = _t431
        self.consume_literal(']')
        return (keys66, (values67 if values67 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol68 = self.consume_terminal('SYMBOL')
        self.consume_literal('::')
        _t433 = self.parse_type()
        type69 = _t433
        _t434 = logic_pb2.Var(name=symbol68)
        _t435 = logic_pb2.Binding(var=_t434, type=type69)
        return _t435

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal('UNKNOWN', 0):
            _t436 = 0
        else:
            if self.match_lookahead_literal('UINT128', 0):
                _t437 = 4
            else:
                if self.match_lookahead_literal('STRING', 0):
                    _t446 = 1
                else:
                    if self.match_lookahead_literal('MISSING', 0):
                        _t447 = 8
                    else:
                        if self.match_lookahead_literal('INT128', 0):
                            _t448 = 5
                        else:
                            if self.match_lookahead_literal('INT', 0):
                                _t449 = 2
                            else:
                                if self.match_lookahead_literal('FLOAT', 0):
                                    _t450 = 3
                                else:
                                    if self.match_lookahead_literal('DATETIME', 0):
                                        _t451 = 7
                                    else:
                                        if self.match_lookahead_literal('DATE', 0):
                                            _t452 = 6
                                        else:
                                            if self.match_lookahead_literal('BOOLEAN', 0):
                                                _t453 = 10
                                            else:
                                                if self.match_lookahead_literal('(', 0):
                                                    _t454 = 9
                                                else:
                                                    _t454 = -1
                                                _t453 = _t454
                                            _t452 = _t453
                                        _t451 = _t452
                                    _t450 = _t451
                                _t449 = _t450
                            _t448 = _t449
                        _t447 = _t448
                    _t446 = _t447
                _t437 = _t446
            _t436 = _t437
        prediction70 = _t436
        if prediction70 == 10:
            _t456 = self.parse_boolean_type()
            value81 = _t456
            _t457 = logic_pb2.Type(boolean_type=value81)
            _t455 = _t457
        else:
            if prediction70 == 9:
                _t459 = self.parse_decimal_type()
                value80 = _t459
                _t460 = logic_pb2.Type(decimal_type=value80)
                _t458 = _t460
            else:
                if prediction70 == 8:
                    _t462 = self.parse_missing_type()
                    value79 = _t462
                    _t463 = logic_pb2.Type(missing_type=value79)
                    _t461 = _t463
                else:
                    if prediction70 == 7:
                        _t465 = self.parse_datetime_type()
                        value78 = _t465
                        _t466 = logic_pb2.Type(datetime_type=value78)
                        _t464 = _t466
                    else:
                        if prediction70 == 6:
                            _t468 = self.parse_date_type()
                            value77 = _t468
                            _t469 = logic_pb2.Type(date_type=value77)
                            _t467 = _t469
                        else:
                            if prediction70 == 5:
                                _t471 = self.parse_int128_type()
                                value76 = _t471
                                _t472 = logic_pb2.Type(int128_type=value76)
                                _t470 = _t472
                            else:
                                if prediction70 == 4:
                                    _t474 = self.parse_uint128_type()
                                    value75 = _t474
                                    _t475 = logic_pb2.Type(uint128_type=value75)
                                    _t473 = _t475
                                else:
                                    if prediction70 == 3:
                                        _t477 = self.parse_float_type()
                                        value74 = _t477
                                        _t478 = logic_pb2.Type(float_type=value74)
                                        _t476 = _t478
                                    else:
                                        if prediction70 == 2:
                                            _t480 = self.parse_int_type()
                                            value73 = _t480
                                            _t481 = logic_pb2.Type(int_type=value73)
                                            _t479 = _t481
                                        else:
                                            if prediction70 == 1:
                                                _t483 = self.parse_string_type()
                                                value72 = _t483
                                                _t484 = logic_pb2.Type(string_type=value72)
                                                _t482 = _t484
                                            else:
                                                if prediction70 == 0:
                                                    _t486 = self.parse_unspecified_type()
                                                    value71 = _t486
                                                    _t487 = logic_pb2.Type(unspecified_type=value71)
                                                    _t485 = _t487
                                                else:
                                                    raise ParseError(f"{'Unexpected token in type'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                    _t485 = None
                                                _t482 = _t485
                                            _t479 = _t482
                                        _t476 = _t479
                                    _t473 = _t476
                                _t470 = _t473
                            _t467 = _t470
                        _t464 = _t467
                    _t461 = _t464
                _t458 = _t461
            _t455 = _t458
        return _t455

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        self.consume_literal('UNKNOWN')
        _t488 = logic_pb2.UnspecifiedType()
        return _t488

    def parse_string_type(self) -> logic_pb2.StringType:
        self.consume_literal('STRING')
        _t489 = logic_pb2.StringType()
        return _t489

    def parse_int_type(self) -> logic_pb2.IntType:
        self.consume_literal('INT')
        _t490 = logic_pb2.IntType()
        return _t490

    def parse_float_type(self) -> logic_pb2.FloatType:
        self.consume_literal('FLOAT')
        _t491 = logic_pb2.FloatType()
        return _t491

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        self.consume_literal('UINT128')
        _t492 = logic_pb2.UInt128Type()
        return _t492

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        self.consume_literal('INT128')
        _t493 = logic_pb2.Int128Type()
        return _t493

    def parse_date_type(self) -> logic_pb2.DateType:
        self.consume_literal('DATE')
        _t494 = logic_pb2.DateType()
        return _t494

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        self.consume_literal('DATETIME')
        _t495 = logic_pb2.DateTimeType()
        return _t495

    def parse_missing_type(self) -> logic_pb2.MissingType:
        self.consume_literal('MISSING')
        _t496 = logic_pb2.MissingType()
        return _t496

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        self.consume_literal('(')
        self.consume_literal('DECIMAL')
        precision82 = self.consume_terminal('INT')
        scale83 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t497 = logic_pb2.DecimalType(precision=precision82, scale=scale83)
        return _t497

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal('BOOLEAN')
        _t498 = logic_pb2.BooleanType()
        return _t498

    def parse_value_bindings(self) -> list[logic_pb2.Binding]:
        self.consume_literal('|')
        xs84 = []
        cond85 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond85:
            _t499 = self.parse_binding()
            xs84.append(_t499)
            cond85 = self.match_lookahead_terminal('SYMBOL', 0)
        x86 = xs84
        return x86

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('true', 1):
                _t501 = 0
            else:
                if self.match_lookahead_literal('relatom', 1):
                    _t502 = 11
                else:
                    if self.match_lookahead_literal('reduce', 1):
                        _t503 = 3
                    else:
                        if self.match_lookahead_literal('primitive', 1):
                            _t504 = 10
                        else:
                            if self.match_lookahead_literal('pragma', 1):
                                _t505 = 9
                            else:
                                if self.match_lookahead_literal('or', 1):
                                    _t506 = 5
                                else:
                                    if self.match_lookahead_literal('not', 1):
                                        _t507 = 6
                                    else:
                                        if self.match_lookahead_literal('ffi', 1):
                                            _t508 = 7
                                        else:
                                            if self.match_lookahead_literal('false', 1):
                                                _t522 = 1
                                            else:
                                                if self.match_lookahead_literal('exists', 1):
                                                    _t523 = 2
                                                else:
                                                    if self.match_lookahead_literal('cast', 1):
                                                        _t524 = 12
                                                    else:
                                                        if self.match_lookahead_literal('atom', 1):
                                                            _t525 = 8
                                                        else:
                                                            if self.match_lookahead_literal('and', 1):
                                                                _t526 = 4
                                                            else:
                                                                if self.match_lookahead_literal('>=', 1):
                                                                    _t527 = 10
                                                                else:
                                                                    if self.match_lookahead_literal('>', 1):
                                                                        _t528 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal('=', 1):
                                                                            _t529 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal('<=', 1):
                                                                                _t530 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal('<', 1):
                                                                                    _t531 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal('/', 1):
                                                                                        _t532 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal('-', 1):
                                                                                            _t533 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal('+', 1):
                                                                                                _t534 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal('*', 1):
                                                                                                    _t535 = 10
                                                                                                else:
                                                                                                    _t535 = -1
                                                                                                _t534 = _t535
                                                                                            _t533 = _t534
                                                                                        _t532 = _t533
                                                                                    _t531 = _t532
                                                                                _t530 = _t531
                                                                            _t529 = _t530
                                                                        _t528 = _t529
                                                                    _t527 = _t528
                                                                _t526 = _t527
                                                            _t525 = _t526
                                                        _t524 = _t525
                                                    _t523 = _t524
                                                _t522 = _t523
                                            _t508 = _t522
                                        _t507 = _t508
                                    _t506 = _t507
                                _t505 = _t506
                            _t504 = _t505
                        _t503 = _t504
                    _t502 = _t503
                _t501 = _t502
            _t500 = _t501
        else:
            _t500 = -1
        prediction87 = _t500
        if prediction87 == 12:
            _t537 = self.parse_cast()
            value100 = _t537
            _t538 = logic_pb2.Formula(cast=value100)
            _t536 = _t538
        else:
            if prediction87 == 11:
                _t540 = self.parse_rel_atom()
                value99 = _t540
                _t541 = logic_pb2.Formula(rel_atom=value99)
                _t539 = _t541
            else:
                if prediction87 == 10:
                    _t543 = self.parse_primitive()
                    value98 = _t543
                    _t544 = logic_pb2.Formula(primitive=value98)
                    _t542 = _t544
                else:
                    if prediction87 == 9:
                        _t546 = self.parse_pragma()
                        value97 = _t546
                        _t547 = logic_pb2.Formula(pragma=value97)
                        _t545 = _t547
                    else:
                        if prediction87 == 8:
                            _t549 = self.parse_atom()
                            value96 = _t549
                            _t550 = logic_pb2.Formula(atom=value96)
                            _t548 = _t550
                        else:
                            if prediction87 == 7:
                                _t552 = self.parse_ffi()
                                value95 = _t552
                                _t553 = logic_pb2.Formula(ffi=value95)
                                _t551 = _t553
                            else:
                                if prediction87 == 6:
                                    _t555 = self.parse_not()
                                    value94 = _t555
                                    _t556 = logic_pb2.Formula(**{'not': value94})
                                    _t554 = _t556
                                else:
                                    if prediction87 == 5:
                                        _t558 = self.parse_disjunction()
                                        value93 = _t558
                                        _t559 = logic_pb2.Formula(disjunction=value93)
                                        _t557 = _t559
                                    else:
                                        if prediction87 == 4:
                                            _t561 = self.parse_conjunction()
                                            value92 = _t561
                                            _t562 = logic_pb2.Formula(conjunction=value92)
                                            _t560 = _t562
                                        else:
                                            if prediction87 == 3:
                                                _t564 = self.parse_reduce()
                                                value91 = _t564
                                                _t565 = logic_pb2.Formula(reduce=value91)
                                                _t563 = _t565
                                            else:
                                                if prediction87 == 2:
                                                    _t567 = self.parse_exists()
                                                    value90 = _t567
                                                    _t568 = logic_pb2.Formula(exists=value90)
                                                    _t566 = _t568
                                                else:
                                                    if prediction87 == 1:
                                                        _t570 = self.parse_false()
                                                        value89 = _t570
                                                        _t571 = logic_pb2.Formula(disjunction=value89)
                                                        _t569 = _t571
                                                    else:
                                                        if prediction87 == 0:
                                                            _t573 = self.parse_true()
                                                            value88 = _t573
                                                            _t574 = logic_pb2.Formula(conjunction=value88)
                                                            _t572 = _t574
                                                        else:
                                                            raise ParseError(f"{'Unexpected token in formula'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t572 = None
                                                        _t569 = _t572
                                                    _t566 = _t569
                                                _t563 = _t566
                                            _t560 = _t563
                                        _t557 = _t560
                                    _t554 = _t557
                                _t551 = _t554
                            _t548 = _t551
                        _t545 = _t548
                    _t542 = _t545
                _t539 = _t542
            _t536 = _t539
        return _t536

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('true')
        self.consume_literal(')')
        _t575 = logic_pb2.Conjunction(args=[])
        return _t575

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('false')
        self.consume_literal(')')
        _t576 = logic_pb2.Disjunction(args=[])
        return _t576

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal('(')
        self.consume_literal('exists')
        _t577 = self.parse_bindings()
        bindings101 = _t577
        _t578 = self.parse_formula()
        formula102 = _t578
        self.consume_literal(')')
        _t579 = logic_pb2.Abstraction(vars=(bindings101[0] + (bindings101[1] if bindings101[1] is not None else [])), value=formula102)
        _t580 = logic_pb2.Exists(body=_t579)
        return _t580

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal('(')
        self.consume_literal('reduce')
        _t581 = self.parse_abstraction()
        op103 = _t581
        _t582 = self.parse_abstraction()
        body104 = _t582
        _t583 = self.parse_terms()
        terms105 = _t583
        self.consume_literal(')')
        _t584 = logic_pb2.Reduce(op=op103, body=body104, terms=terms105)
        return _t584

    def parse_terms(self) -> list[logic_pb2.Term]:
        self.consume_literal('(')
        self.consume_literal('terms')
        xs106 = []
        cond107 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond107:
            _t585 = self.parse_term()
            xs106.append(_t585)
            cond107 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        x108 = xs106
        self.consume_literal(')')
        return x108

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_literal('true', 0):
            _t617 = 1
        else:
            if self.match_lookahead_literal('missing', 0):
                _t633 = 1
            else:
                if self.match_lookahead_literal('false', 0):
                    _t641 = 1
                else:
                    if self.match_lookahead_literal('(', 0):
                        _t645 = 1
                    else:
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t647 = 1
                        else:
                            if self.match_lookahead_terminal('SYMBOL', 0):
                                _t648 = 0
                            else:
                                _t648 = (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or -1)))))
                            _t647 = _t648
                        _t645 = _t647
                    _t641 = _t645
                _t633 = _t641
            _t617 = _t633
        prediction109 = _t617
        if prediction109 == 1:
            _t650 = self.parse_constant()
            value111 = _t650
            _t651 = logic_pb2.Term(constant=value111)
            _t649 = _t651
        else:
            if prediction109 == 0:
                _t653 = self.parse_var()
                value110 = _t653
                _t654 = logic_pb2.Term(var=value110)
                _t652 = _t654
            else:
                raise ParseError(f"{'Unexpected token in term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t652 = None
            _t649 = _t652
        return _t649

    def parse_var(self) -> logic_pb2.Var:
        symbol112 = self.consume_terminal('SYMBOL')
        _t655 = logic_pb2.Var(name=symbol112)
        return _t655

    def parse_constant(self) -> logic_pb2.Value:
        _t656 = self.parse_value()
        x113 = _t656
        return x113

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('and')
        xs114 = []
        cond115 = self.match_lookahead_literal('(', 0)
        while cond115:
            _t657 = self.parse_formula()
            xs114.append(_t657)
            cond115 = self.match_lookahead_literal('(', 0)
        args116 = xs114
        self.consume_literal(')')
        _t658 = logic_pb2.Conjunction(args=args116)
        return _t658

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('or')
        xs117 = []
        cond118 = self.match_lookahead_literal('(', 0)
        while cond118:
            _t659 = self.parse_formula()
            xs117.append(_t659)
            cond118 = self.match_lookahead_literal('(', 0)
        args119 = xs117
        self.consume_literal(')')
        _t660 = logic_pb2.Disjunction(args=args119)
        return _t660

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal('(')
        self.consume_literal('not')
        _t661 = self.parse_formula()
        arg120 = _t661
        self.consume_literal(')')
        _t662 = logic_pb2.Not(arg=arg120)
        return _t662

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal('(')
        self.consume_literal('ffi')
        _t663 = self.parse_name()
        name121 = _t663
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('args', 1)):
            _t665 = self.parse_ffi_args()
            _t664 = _t665
        else:
            _t664 = None
        args122 = _t664
        if self.match_lookahead_literal('(', 0):
            _t667 = self.parse_terms()
            _t666 = _t667
        else:
            _t666 = None
        terms123 = _t666
        self.consume_literal(')')
        _t668 = logic_pb2.FFI(name=name121, args=(args122 if args122 is not None else []), terms=(terms123 if terms123 is not None else []))
        return _t668

    def parse_name(self) -> str:
        x124 = self.consume_terminal('COLON_SYMBOL')
        return x124

    def parse_ffi_args(self) -> list[logic_pb2.Abstraction]:
        self.consume_literal('(')
        self.consume_literal('args')
        xs125 = []
        cond126 = self.match_lookahead_literal('(', 0)
        while cond126:
            _t669 = self.parse_abstraction()
            xs125.append(_t669)
            cond126 = self.match_lookahead_literal('(', 0)
        x127 = xs125
        self.consume_literal(')')
        return x127

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal('(')
        self.consume_literal('atom')
        _t670 = self.parse_relation_id()
        name128 = _t670
        xs129 = []
        cond130 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond130:
            _t671 = self.parse_term()
            xs129.append(_t671)
            cond130 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms131 = xs129
        self.consume_literal(')')
        _t672 = logic_pb2.Atom(name=name128, terms=terms131)
        return _t672

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal('(')
        self.consume_literal('pragma')
        _t673 = self.parse_name()
        name132 = _t673
        xs133 = []
        cond134 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond134:
            _t674 = self.parse_term()
            xs133.append(_t674)
            cond134 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms135 = xs133
        self.consume_literal(')')
        _t675 = logic_pb2.Pragma(name=name132, terms=terms135)
        return _t675

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('primitive', 1):
                _t677 = 9
            else:
                if self.match_lookahead_literal('>=', 1):
                    _t678 = 4
                else:
                    if self.match_lookahead_literal('>', 1):
                        _t679 = 3
                    else:
                        if self.match_lookahead_literal('=', 1):
                            _t680 = 0
                        else:
                            if self.match_lookahead_literal('<=', 1):
                                _t681 = 2
                            else:
                                if self.match_lookahead_literal('<', 1):
                                    _t686 = 1
                                else:
                                    if self.match_lookahead_literal('/', 1):
                                        _t687 = 8
                                    else:
                                        if self.match_lookahead_literal('-', 1):
                                            _t688 = 6
                                        else:
                                            if self.match_lookahead_literal('+', 1):
                                                _t689 = 5
                                            else:
                                                if self.match_lookahead_literal('*', 1):
                                                    _t690 = 7
                                                else:
                                                    _t690 = -1
                                                _t689 = _t690
                                            _t688 = _t689
                                        _t687 = _t688
                                    _t686 = _t687
                                _t681 = _t686
                            _t680 = _t681
                        _t679 = _t680
                    _t678 = _t679
                _t677 = _t678
            _t676 = _t677
        else:
            _t676 = -1
        prediction136 = _t676
        if prediction136 == 9:
            self.consume_literal('(')
            self.consume_literal('primitive')
            _t692 = self.parse_name()
            name146 = _t692
            xs147 = []
            cond148 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            while cond148:
                _t693 = self.parse_rel_term()
                xs147.append(_t693)
                cond148 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            terms149 = xs147
            self.consume_literal(')')
            _t694 = logic_pb2.Primitive(name=name146, terms=terms149)
            _t691 = _t694
        else:
            if prediction136 == 8:
                _t696 = self.parse_divide()
                op145 = _t696
                _t695 = op145
            else:
                if prediction136 == 7:
                    _t698 = self.parse_multiply()
                    op144 = _t698
                    _t697 = op144
                else:
                    if prediction136 == 6:
                        _t700 = self.parse_minus()
                        op143 = _t700
                        _t699 = op143
                    else:
                        if prediction136 == 5:
                            _t702 = self.parse_add()
                            op142 = _t702
                            _t701 = op142
                        else:
                            if prediction136 == 4:
                                _t704 = self.parse_gt_eq()
                                op141 = _t704
                                _t703 = op141
                            else:
                                if prediction136 == 3:
                                    _t706 = self.parse_gt()
                                    op140 = _t706
                                    _t705 = op140
                                else:
                                    if prediction136 == 2:
                                        _t708 = self.parse_lt_eq()
                                        op139 = _t708
                                        _t707 = op139
                                    else:
                                        if prediction136 == 1:
                                            _t710 = self.parse_lt()
                                            op138 = _t710
                                            _t709 = op138
                                        else:
                                            if prediction136 == 0:
                                                _t712 = self.parse_eq()
                                                op137 = _t712
                                                _t711 = op137
                                            else:
                                                raise ParseError(f"{'Unexpected token in primitive'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t711 = None
                                            _t709 = _t711
                                        _t707 = _t709
                                    _t705 = _t707
                                _t703 = _t705
                            _t701 = _t703
                        _t699 = _t701
                    _t697 = _t699
                _t695 = _t697
            _t691 = _t695
        return _t691

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('=')
        _t713 = self.parse_term()
        left150 = _t713
        _t714 = self.parse_term()
        right151 = _t714
        self.consume_literal(')')
        _t715 = logic_pb2.RelTerm(term=left150)
        _t716 = logic_pb2.RelTerm(term=right151)
        _t717 = logic_pb2.Primitive(name='rel_primitive_eq', terms=[_t715, _t716])
        return _t717

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<')
        _t718 = self.parse_term()
        left152 = _t718
        _t719 = self.parse_term()
        right153 = _t719
        self.consume_literal(')')
        _t720 = logic_pb2.RelTerm(term=left152)
        _t721 = logic_pb2.RelTerm(term=right153)
        _t722 = logic_pb2.Primitive(name='rel_primitive_lt_monotype', terms=[_t720, _t721])
        return _t722

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<=')
        _t723 = self.parse_term()
        left154 = _t723
        _t724 = self.parse_term()
        right155 = _t724
        self.consume_literal(')')
        _t725 = logic_pb2.RelTerm(term=left154)
        _t726 = logic_pb2.RelTerm(term=right155)
        _t727 = logic_pb2.Primitive(name='rel_primitive_lt_eq_monotype', terms=[_t725, _t726])
        return _t727

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>')
        _t728 = self.parse_term()
        left156 = _t728
        _t729 = self.parse_term()
        right157 = _t729
        self.consume_literal(')')
        _t730 = logic_pb2.RelTerm(term=left156)
        _t731 = logic_pb2.RelTerm(term=right157)
        _t732 = logic_pb2.Primitive(name='rel_primitive_gt_monotype', terms=[_t730, _t731])
        return _t732

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>=')
        _t733 = self.parse_term()
        left158 = _t733
        _t734 = self.parse_term()
        right159 = _t734
        self.consume_literal(')')
        _t735 = logic_pb2.RelTerm(term=left158)
        _t736 = logic_pb2.RelTerm(term=right159)
        _t737 = logic_pb2.Primitive(name='rel_primitive_gt_eq_monotype', terms=[_t735, _t736])
        return _t737

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('+')
        _t738 = self.parse_term()
        left160 = _t738
        _t739 = self.parse_term()
        right161 = _t739
        _t740 = self.parse_term()
        result162 = _t740
        self.consume_literal(')')
        _t741 = logic_pb2.RelTerm(term=left160)
        _t742 = logic_pb2.RelTerm(term=right161)
        _t743 = logic_pb2.RelTerm(term=result162)
        _t744 = logic_pb2.Primitive(name='rel_primitive_add_monotype', terms=[_t741, _t742, _t743])
        return _t744

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('-')
        _t745 = self.parse_term()
        left163 = _t745
        _t746 = self.parse_term()
        right164 = _t746
        _t747 = self.parse_term()
        result165 = _t747
        self.consume_literal(')')
        _t748 = logic_pb2.RelTerm(term=left163)
        _t749 = logic_pb2.RelTerm(term=right164)
        _t750 = logic_pb2.RelTerm(term=result165)
        _t751 = logic_pb2.Primitive(name='rel_primitive_subtract_monotype', terms=[_t748, _t749, _t750])
        return _t751

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('*')
        _t752 = self.parse_term()
        left166 = _t752
        _t753 = self.parse_term()
        right167 = _t753
        _t754 = self.parse_term()
        result168 = _t754
        self.consume_literal(')')
        _t755 = logic_pb2.RelTerm(term=left166)
        _t756 = logic_pb2.RelTerm(term=right167)
        _t757 = logic_pb2.RelTerm(term=result168)
        _t758 = logic_pb2.Primitive(name='rel_primitive_multiply_monotype', terms=[_t755, _t756, _t757])
        return _t758

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('/')
        _t759 = self.parse_term()
        left169 = _t759
        _t760 = self.parse_term()
        right170 = _t760
        _t761 = self.parse_term()
        result171 = _t761
        self.consume_literal(')')
        _t762 = logic_pb2.RelTerm(term=left169)
        _t763 = logic_pb2.RelTerm(term=right170)
        _t764 = logic_pb2.RelTerm(term=result171)
        _t765 = logic_pb2.Primitive(name='rel_primitive_divide_monotype', terms=[_t762, _t763, _t764])
        return _t765

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_literal('true', 0):
            _t781 = 1
        else:
            if self.match_lookahead_literal('missing', 0):
                _t789 = 1
            else:
                if self.match_lookahead_literal('false', 0):
                    _t793 = 1
                else:
                    if self.match_lookahead_literal('(', 0):
                        _t795 = 1
                    else:
                        if self.match_lookahead_literal('#', 0):
                            _t796 = 0
                        else:
                            _t796 = (self.match_lookahead_terminal('UINT128', 0) or (self.match_lookahead_terminal('SYMBOL', 0) or (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or -1)))))))
                        _t795 = _t796
                    _t793 = _t795
                _t789 = _t793
            _t781 = _t789
        prediction172 = _t781
        if prediction172 == 1:
            _t798 = self.parse_term()
            value174 = _t798
            _t799 = logic_pb2.RelTerm(term=value174)
            _t797 = _t799
        else:
            if prediction172 == 0:
                _t801 = self.parse_specialized_value()
                value173 = _t801
                _t802 = logic_pb2.RelTerm(specialized_value=value173)
                _t800 = _t802
            else:
                raise ParseError(f"{'Unexpected token in rel_term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t800 = None
            _t797 = _t800
        return _t797

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal('#')
        _t803 = self.parse_value()
        value175 = _t803
        return value175

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        self.consume_literal('(')
        self.consume_literal('relatom')
        _t804 = self.parse_name()
        name176 = _t804
        xs177 = []
        cond178 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond178:
            _t805 = self.parse_rel_term()
            xs177.append(_t805)
            cond178 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms179 = xs177
        self.consume_literal(')')
        _t806 = logic_pb2.RelAtom(name=name176, terms=terms179)
        return _t806

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal('(')
        self.consume_literal('cast')
        _t807 = self.parse_term()
        input180 = _t807
        _t808 = self.parse_term()
        result181 = _t808
        self.consume_literal(')')
        _t809 = logic_pb2.Cast(input=input180, result=result181)
        return _t809

    def parse_attrs(self) -> list[logic_pb2.Attribute]:
        self.consume_literal('(')
        self.consume_literal('attrs')
        xs182 = []
        cond183 = self.match_lookahead_literal('(', 0)
        while cond183:
            _t810 = self.parse_attribute()
            xs182.append(_t810)
            cond183 = self.match_lookahead_literal('(', 0)
        x184 = xs182
        self.consume_literal(')')
        return x184

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal('(')
        self.consume_literal('attribute')
        _t811 = self.parse_name()
        name185 = _t811
        xs186 = []
        cond187 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond187:
            _t812 = self.parse_value()
            xs186.append(_t812)
            cond187 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        args188 = xs186
        self.consume_literal(')')
        _t813 = logic_pb2.Attribute(name=name185, args=args188)
        return _t813

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal('(')
        self.consume_literal('algorithm')
        xs189 = []
        cond190 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        while cond190:
            _t814 = self.parse_relation_id()
            xs189.append(_t814)
            cond190 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        global191 = xs189
        _t815 = self.parse_script()
        body192 = _t815
        self.consume_literal(')')
        _t816 = logic_pb2.Algorithm(**{'global': global191}, body=body192)
        return _t816

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal('(')
        self.consume_literal('script')
        xs193 = []
        cond194 = self.match_lookahead_literal('(', 0)
        while cond194:
            _t817 = self.parse_construct()
            xs193.append(_t817)
            cond194 = self.match_lookahead_literal('(', 0)
        constructs195 = xs193
        self.consume_literal(')')
        _t818 = logic_pb2.Script(constructs=constructs195)
        return _t818

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t827 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t831 = 1
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t833 = 1
                    else:
                        if self.match_lookahead_literal('loop', 1):
                            _t834 = 0
                        else:
                            _t834 = (self.match_lookahead_literal('break', 1) or (self.match_lookahead_literal('assign', 1) or -1))
                        _t833 = _t834
                    _t831 = _t833
                _t827 = _t831
            _t819 = _t827
        else:
            _t819 = -1
        prediction196 = _t819
        if prediction196 == 1:
            _t836 = self.parse_instruction()
            value198 = _t836
            _t837 = logic_pb2.Construct(instruction=value198)
            _t835 = _t837
        else:
            if prediction196 == 0:
                _t839 = self.parse_loop()
                value197 = _t839
                _t840 = logic_pb2.Construct(loop=value197)
                _t838 = _t840
            else:
                raise ParseError(f"{'Unexpected token in construct'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t838 = None
            _t835 = _t838
        return _t835

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal('(')
        self.consume_literal('loop')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('init', 1)):
            _t842 = self.parse_loop_init()
            _t841 = _t842
        else:
            _t841 = None
        init199 = _t841
        _t843 = self.parse_script()
        body200 = _t843
        self.consume_literal(')')
        _t844 = logic_pb2.Loop(init=(init199 if init199 is not None else []), body=body200)
        return _t844

    def parse_loop_init(self) -> list[logic_pb2.Instruction]:
        self.consume_literal('(')
        self.consume_literal('init')
        xs201 = []
        cond202 = self.match_lookahead_literal('(', 0)
        while cond202:
            _t845 = self.parse_instruction()
            xs201.append(_t845)
            cond202 = self.match_lookahead_literal('(', 0)
        x203 = xs201
        self.consume_literal(')')
        return x203

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t851 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t852 = 4
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t853 = 3
                    else:
                        if self.match_lookahead_literal('break', 1):
                            _t854 = 2
                        else:
                            if self.match_lookahead_literal('assign', 1):
                                _t855 = 0
                            else:
                                _t855 = -1
                            _t854 = _t855
                        _t853 = _t854
                    _t852 = _t853
                _t851 = _t852
            _t846 = _t851
        else:
            _t846 = -1
        prediction204 = _t846
        if prediction204 == 4:
            _t857 = self.parse_monus_def()
            value209 = _t857
            _t858 = logic_pb2.Instruction(monus_def=value209)
            _t856 = _t858
        else:
            if prediction204 == 3:
                _t860 = self.parse_monoid_def()
                value208 = _t860
                _t861 = logic_pb2.Instruction(monoid_def=value208)
                _t859 = _t861
            else:
                if prediction204 == 2:
                    _t863 = self.parse_break()
                    value207 = _t863
                    _t864 = logic_pb2.Instruction(**{'break': value207})
                    _t862 = _t864
                else:
                    if prediction204 == 1:
                        _t866 = self.parse_upsert()
                        value206 = _t866
                        _t867 = logic_pb2.Instruction(upsert=value206)
                        _t865 = _t867
                    else:
                        if prediction204 == 0:
                            _t869 = self.parse_assign()
                            value205 = _t869
                            _t870 = logic_pb2.Instruction(assign=value205)
                            _t868 = _t870
                        else:
                            raise ParseError(f"{'Unexpected token in instruction'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t868 = None
                        _t865 = _t868
                    _t862 = _t865
                _t859 = _t862
            _t856 = _t859
        return _t856

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal('(')
        self.consume_literal('assign')
        _t871 = self.parse_relation_id()
        name210 = _t871
        _t872 = self.parse_abstraction()
        body211 = _t872
        if self.match_lookahead_literal('(', 0):
            _t874 = self.parse_attrs()
            _t873 = _t874
        else:
            _t873 = None
        attrs212 = _t873
        self.consume_literal(')')
        _t875 = logic_pb2.Assign(name=name210, body=body211, attrs=(attrs212 if attrs212 is not None else []))
        return _t875

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal('(')
        self.consume_literal('upsert')
        _t876 = self.parse_relation_id()
        name213 = _t876
        _t877 = self.parse_abstraction_with_arity()
        abstraction_with_arity214 = _t877
        if self.match_lookahead_literal('(', 0):
            _t879 = self.parse_attrs()
            _t878 = _t879
        else:
            _t878 = None
        attrs215 = _t878
        self.consume_literal(')')
        abstraction = abstraction_with_arity214[0]
        arity = abstraction_with_arity214[1]
        _t880 = logic_pb2.Upsert(name=name213, body=abstraction, attrs=(attrs215 if attrs215 is not None else []), value_arity=arity)
        return _t880

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal('(')
        _t881 = self.parse_bindings()
        bindings216 = _t881
        _t882 = self.parse_formula()
        formula217 = _t882
        self.consume_literal(')')
        _t883 = logic_pb2.Abstraction(vars=(bindings216[0] + (bindings216[1] if bindings216[1] is not None else [])), value=formula217)
        return (_t883, len(bindings216[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal('(')
        self.consume_literal('break')
        _t884 = self.parse_relation_id()
        name218 = _t884
        _t885 = self.parse_abstraction()
        body219 = _t885
        if self.match_lookahead_literal('(', 0):
            _t887 = self.parse_attrs()
            _t886 = _t887
        else:
            _t886 = None
        attrs220 = _t886
        self.consume_literal(')')
        _t888 = logic_pb2.Break(name=name218, body=body219, attrs=(attrs220 if attrs220 is not None else []))
        return _t888

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal('(')
        self.consume_literal('monoid')
        _t889 = self.parse_monoid()
        monoid221 = _t889
        _t890 = self.parse_relation_id()
        name222 = _t890
        _t891 = self.parse_abstraction_with_arity()
        abstraction_with_arity223 = _t891
        if self.match_lookahead_literal('(', 0):
            _t893 = self.parse_attrs()
            _t892 = _t893
        else:
            _t892 = None
        attrs224 = _t892
        self.consume_literal(')')
        abstraction = abstraction_with_arity223[0]
        arity = abstraction_with_arity223[1]
        _t894 = logic_pb2.MonoidDef(monoid=monoid221, name=name222, body=abstraction, attrs=(attrs224 if attrs224 is not None else []), value_arity=arity)
        return _t894

    def parse_monoid(self) -> logic_pb2.Monoid:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('sum', 1):
                _t896 = 3
            else:
                if self.match_lookahead_literal('or', 1):
                    _t897 = 0
                else:
                    if self.match_lookahead_literal('min', 1):
                        _t899 = 1
                    else:
                        if self.match_lookahead_literal('max', 1):
                            _t900 = 2
                        else:
                            _t900 = -1
                        _t899 = _t900
                    _t897 = _t899
                _t896 = _t897
            _t895 = _t896
        else:
            _t895 = -1
        prediction225 = _t895
        if prediction225 == 3:
            _t902 = self.parse_sum_monoid()
            value229 = _t902
            _t903 = logic_pb2.Monoid(sum_monoid=value229)
            _t901 = _t903
        else:
            if prediction225 == 2:
                _t905 = self.parse_max_monoid()
                value228 = _t905
                _t906 = logic_pb2.Monoid(max_monoid=value228)
                _t904 = _t906
            else:
                if prediction225 == 1:
                    _t908 = self.parse_min_monoid()
                    value227 = _t908
                    _t909 = logic_pb2.Monoid(min_monoid=value227)
                    _t907 = _t909
                else:
                    if prediction225 == 0:
                        _t911 = self.parse_or_monoid()
                        value226 = _t911
                        _t912 = logic_pb2.Monoid(or_monoid=value226)
                        _t910 = _t912
                    else:
                        raise ParseError(f"{'Unexpected token in monoid'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t910 = None
                    _t907 = _t910
                _t904 = _t907
            _t901 = _t904
        return _t901

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        self.consume_literal('(')
        self.consume_literal('or')
        self.consume_literal(')')
        _t913 = logic_pb2.OrMonoid()
        return _t913

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        self.consume_literal('(')
        self.consume_literal('min')
        _t914 = self.parse_type()
        type230 = _t914
        self.consume_literal(')')
        _t915 = logic_pb2.MinMonoid(type=type230)
        return _t915

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        self.consume_literal('(')
        self.consume_literal('max')
        _t916 = self.parse_type()
        type231 = _t916
        self.consume_literal(')')
        _t917 = logic_pb2.MaxMonoid(type=type231)
        return _t917

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        self.consume_literal('(')
        self.consume_literal('sum')
        _t918 = self.parse_type()
        type232 = _t918
        self.consume_literal(')')
        _t919 = logic_pb2.SumMonoid(type=type232)
        return _t919

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal('(')
        self.consume_literal('monus')
        _t920 = self.parse_monoid()
        monoid233 = _t920
        _t921 = self.parse_relation_id()
        name234 = _t921
        _t922 = self.parse_abstraction_with_arity()
        abstraction_with_arity235 = _t922
        if self.match_lookahead_literal('(', 0):
            _t924 = self.parse_attrs()
            _t923 = _t924
        else:
            _t923 = None
        attrs236 = _t923
        self.consume_literal(')')
        abstraction = abstraction_with_arity235[0]
        arity = abstraction_with_arity235[1]
        _t925 = logic_pb2.MonusDef(monoid=monoid233, name=name234, body=abstraction, attrs=(attrs236 if attrs236 is not None else []), value_arity=arity)
        return _t925

    def parse_constraint(self) -> logic_pb2.Constraint:
        _t926 = self.parse_functional_dependency()
        value237 = _t926
        _t927 = logic_pb2.Constraint(functional_dependency=value237)
        return _t927

    def parse_functional_dependency(self) -> logic_pb2.FunctionalDependency:
        self.consume_literal('(')
        self.consume_literal('functional_dependency')
        _t928 = self.parse_abstraction()
        guard238 = _t928
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('keys', 1)):
            _t930 = self.parse_functional_dependency_keys()
            _t929 = _t930
        else:
            _t929 = None
        keys239 = _t929
        if self.match_lookahead_literal('(', 0):
            _t932 = self.parse_functional_dependency_values()
            _t931 = _t932
        else:
            _t931 = None
        values240 = _t931
        self.consume_literal(')')
        _t933 = logic_pb2.FunctionalDependency(guard=guard238, keys=(keys239 if keys239 is not None else []), values=(values240 if values240 is not None else []))
        return _t933

    def parse_functional_dependency_keys(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('keys')
        xs241 = []
        cond242 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond242:
            _t934 = self.parse_var()
            xs241.append(_t934)
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
            _t935 = self.parse_var()
            xs244.append(_t935)
            cond245 = self.match_lookahead_terminal('SYMBOL', 0)
        x246 = xs244
        self.consume_literal(')')
        return x246

    def parse_data(self) -> logic_pb2.Data:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('rel_edb', 1):
                _t937 = 2
            else:
                if self.match_lookahead_literal('csv_data', 1):
                    _t938 = 0
                else:
                    _t938 = (self.match_lookahead_literal('betree_relation', 1) or -1)
                _t937 = _t938
            _t936 = _t937
        else:
            _t936 = -1
        prediction247 = _t936
        if prediction247 == 2:
            _t940 = self.parse_rel_edb()
            rel_edb250 = _t940
            _t941 = logic_pb2.Data(rel_edb=rel_edb250)
            _t939 = _t941
        else:
            if prediction247 == 1:
                _t943 = self.parse_betree_relation()
                betree_relation249 = _t943
                _t944 = logic_pb2.Data(betree_relation=betree_relation249)
                _t942 = _t944
            else:
                if prediction247 == 0:
                    _t946 = self.parse_csv_data()
                    csv_data248 = _t946
                    _t947 = logic_pb2.Data(csv_data=csv_data248)
                    _t945 = _t947
                else:
                    raise ParseError(f"{'Unexpected token in data'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t945 = None
                _t942 = _t945
            _t939 = _t942
        return _t939

    def parse_csv_data(self) -> logic_pb2.CSVData:
        self.consume_literal('(')
        self.consume_literal('csv_data')
        _t948 = self.parse_csv_locator()
        locator251 = _t948
        _t949 = self.parse_csv_config()
        config252 = _t949
        _t950 = self.parse_csv_columns()
        columns253 = _t950
        _t951 = self.parse_csv_asof()
        asof254 = _t951
        self.consume_literal(')')
        _t952 = logic_pb2.CSVData(locator=locator251, config=config252, columns=columns253, asof=asof254)
        return _t952

    def parse_csv_locator(self) -> logic_pb2.CSVLocator:
        self.consume_literal('(')
        self.consume_literal('csv_locator')
        _t953 = self.parse_csv_locator_content()
        x255 = _t953
        self.consume_literal(')')
        return x255

    def parse_csv_locator_content(self) -> logic_pb2.CSVLocator:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('paths', 1):
                _t955 = 0
            else:
                _t955 = (self.match_lookahead_literal('inline_data', 1) or -1)
            _t954 = _t955
        else:
            _t954 = -1
        prediction256 = _t954
        if prediction256 == 1:
            self.consume_literal('(')
            self.consume_literal('inline_data')
            data260 = self.consume_terminal('STRING')
            self.consume_literal(')')
            _t957 = logic_pb2.CSVLocator(paths=[], inline_data=data260.encode())
            _t956 = _t957
        else:
            if prediction256 == 0:
                self.consume_literal('(')
                self.consume_literal('paths')
                xs257 = []
                cond258 = self.match_lookahead_terminal('STRING', 0)
                while cond258:
                    xs257.append(self.consume_terminal('STRING'))
                    cond258 = self.match_lookahead_terminal('STRING', 0)
                paths259 = xs257
                self.consume_literal(')')
                _t959 = logic_pb2.CSVLocator(paths=paths259, inline_data=None)
                _t958 = _t959
            else:
                raise ParseError(f"{'Unexpected token in csv_locator_content'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t958 = None
            _t956 = _t958
        return _t956

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        self.consume_literal('(')
        self.consume_literal('csv_config')
        _t960 = self.parse_config_dict()
        config261 = _t960
        self.consume_literal(')')
        return self.construct_csv_config(config261)

    def parse_csv_columns(self) -> list[logic_pb2.CSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs262 = []
        cond263 = self.match_lookahead_literal('(', 0)
        while cond263:
            _t961 = self.parse_csv_column()
            xs262.append(_t961)
            cond263 = self.match_lookahead_literal('(', 0)
        x264 = xs262
        self.consume_literal(')')
        return x264

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        column_name265 = self.consume_terminal('STRING')
        _t962 = self.parse_relation_id()
        target_id266 = _t962
        _t963 = self.parse_type_list()
        types267 = _t963
        self.consume_literal(')')
        _t964 = logic_pb2.CSVColumn(column_name=column_name265, target_id=target_id266, types=types267)
        return _t964

    def parse_type_list(self) -> list[logic_pb2.Type]:
        self.consume_literal('[')
        xs268 = []
        cond269 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond269:
            _t965 = self.parse_type()
            xs268.append(_t965)
            cond269 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        x270 = xs268
        self.consume_literal(']')
        return x270

    def parse_csv_asof(self) -> str:
        self.consume_literal('(')
        self.consume_literal('asof')
        x271 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return x271

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        self.consume_literal('(')
        self.consume_literal('betree_relation')
        _t966 = self.parse_relation_id()
        name272 = _t966
        _t967 = self.parse_betree_info()
        info273 = _t967
        self.consume_literal(')')
        _t968 = logic_pb2.BeTreeRelation(name=name272, relation_info=info273)
        return _t968

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        self.consume_literal('(')
        self.consume_literal('betree_info')
        _t969 = self.parse_betree_key_types()
        key_types274 = _t969
        _t970 = self.parse_betree_value_types()
        value_types275 = _t970
        _t971 = self.parse_config_dict()
        config276 = _t971
        self.consume_literal(')')
        return self.construct_betree_info(key_types274, value_types275, config276)

    def parse_betree_key_types(self) -> list[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('key_types')
        xs277 = []
        cond278 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond278:
            _t972 = self.parse_type()
            xs277.append(_t972)
            cond278 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        x279 = xs277
        self.consume_literal(')')
        return x279

    def parse_betree_value_types(self) -> list[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('value_types')
        xs280 = []
        cond281 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond281:
            _t973 = self.parse_type()
            xs280.append(_t973)
            cond281 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        x282 = xs280
        self.consume_literal(')')
        return x282

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        self.consume_literal('(')
        self.consume_literal('rel_edb')
        _t974 = self.parse_relation_id()
        target_id283 = _t974
        _t975 = self.parse_string_list()
        path284 = _t975
        _t976 = self.parse_type_list()
        types285 = _t976
        self.consume_literal(')')
        _t977 = logic_pb2.RelEDB(target_id=target_id283, path=path284, types=types285)
        return _t977

    def parse_string_list(self) -> list[str]:
        self.consume_literal('[')
        xs286 = []
        cond287 = self.match_lookahead_terminal('STRING', 0)
        while cond287:
            xs286.append(self.consume_terminal('STRING'))
            cond287 = self.match_lookahead_terminal('STRING', 0)
        x288 = xs286
        self.consume_literal(']')
        return x288

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal('(')
        self.consume_literal('undefine')
        _t978 = self.parse_fragment_id()
        fragment_id289 = _t978
        self.consume_literal(')')
        _t979 = transactions_pb2.Undefine(fragment_id=fragment_id289)
        return _t979

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal('(')
        self.consume_literal('context')
        xs290 = []
        cond291 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        while cond291:
            _t980 = self.parse_relation_id()
            xs290.append(_t980)
            cond291 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        relations292 = xs290
        self.consume_literal(')')
        _t981 = transactions_pb2.Context(relations=relations292)
        return _t981

    def parse_epoch_reads(self) -> list[transactions_pb2.Read]:
        self.consume_literal('(')
        self.consume_literal('reads')
        xs293 = []
        cond294 = self.match_lookahead_literal('(', 0)
        while cond294:
            _t982 = self.parse_read()
            xs293.append(_t982)
            cond294 = self.match_lookahead_literal('(', 0)
        x295 = xs293
        self.consume_literal(')')
        return x295

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('what_if', 1):
                _t984 = 2
            else:
                if self.match_lookahead_literal('output', 1):
                    _t988 = 1
                else:
                    if self.match_lookahead_literal('export', 1):
                        _t989 = 4
                    else:
                        if self.match_lookahead_literal('demand', 1):
                            _t990 = 0
                        else:
                            if self.match_lookahead_literal('abort', 1):
                                _t991 = 3
                            else:
                                _t991 = -1
                            _t990 = _t991
                        _t989 = _t990
                    _t988 = _t989
                _t984 = _t988
            _t983 = _t984
        else:
            _t983 = -1
        prediction296 = _t983
        if prediction296 == 4:
            _t993 = self.parse_export()
            value301 = _t993
            _t994 = transactions_pb2.Read(export=value301)
            _t992 = _t994
        else:
            if prediction296 == 3:
                _t996 = self.parse_abort()
                value300 = _t996
                _t997 = transactions_pb2.Read(abort=value300)
                _t995 = _t997
            else:
                if prediction296 == 2:
                    _t999 = self.parse_what_if()
                    value299 = _t999
                    _t1000 = transactions_pb2.Read(what_if=value299)
                    _t998 = _t1000
                else:
                    if prediction296 == 1:
                        _t1002 = self.parse_output()
                        value298 = _t1002
                        _t1003 = transactions_pb2.Read(output=value298)
                        _t1001 = _t1003
                    else:
                        if prediction296 == 0:
                            _t1005 = self.parse_demand()
                            value297 = _t1005
                            _t1006 = transactions_pb2.Read(demand=value297)
                            _t1004 = _t1006
                        else:
                            raise ParseError(f"{'Unexpected token in read'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t1004 = None
                        _t1001 = _t1004
                    _t998 = _t1001
                _t995 = _t998
            _t992 = _t995
        return _t992

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal('(')
        self.consume_literal('demand')
        _t1007 = self.parse_relation_id()
        relation_id302 = _t1007
        self.consume_literal(')')
        _t1008 = transactions_pb2.Demand(relation_id=relation_id302)
        return _t1008

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal('(')
        self.consume_literal('output')
        if self.match_lookahead_terminal('COLON_SYMBOL', 0):
            _t1010 = self.parse_name()
            _t1009 = _t1010
        else:
            _t1009 = None
        name303 = _t1009
        _t1011 = self.parse_relation_id()
        relation_id304 = _t1011
        self.consume_literal(')')
        _t1012 = transactions_pb2.Output(name=(name303 if name303 is not None else 'output'), relation_id=relation_id304)
        return _t1012

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal('(')
        self.consume_literal('what_if')
        _t1013 = self.parse_name()
        branch305 = _t1013
        _t1014 = self.parse_epoch()
        epoch306 = _t1014
        self.consume_literal(')')
        _t1015 = transactions_pb2.WhatIf(branch=branch305, epoch=epoch306)
        return _t1015

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal('(')
        self.consume_literal('abort')
        if self.match_lookahead_terminal('COLON_SYMBOL', 0):
            _t1017 = self.parse_name()
            _t1016 = _t1017
        else:
            _t1016 = None
        name307 = _t1016
        _t1018 = self.parse_relation_id()
        relation_id308 = _t1018
        self.consume_literal(')')
        _t1019 = transactions_pb2.Abort(name=(name307 if name307 is not None else 'abort'), relation_id=relation_id308)
        return _t1019

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal('(')
        self.consume_literal('export')
        _t1020 = self.parse_export_csvconfig()
        config309 = _t1020
        self.consume_literal(')')
        _t1021 = transactions_pb2.Export(csv_config=config309)
        return _t1021

    def parse_export_csvconfig(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal('(')
        self.consume_literal('export_csv_config')
        _t1022 = self.parse_export_csv_path()
        path310 = _t1022
        _t1023 = self.parse_export_csv_columns()
        columns311 = _t1023
        _t1024 = self.parse_config_dict()
        config312 = _t1024
        self.consume_literal(')')
        return self.export_csv_config(path310, columns311, config312)

    def parse_export_csv_path(self) -> str:
        self.consume_literal('(')
        self.consume_literal('path')
        x313 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return x313

    def parse_export_csv_columns(self) -> list[transactions_pb2.ExportCSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs314 = []
        cond315 = self.match_lookahead_literal('(', 0)
        while cond315:
            _t1025 = self.parse_export_csv_column()
            xs314.append(_t1025)
            cond315 = self.match_lookahead_literal('(', 0)
        x316 = xs314
        self.consume_literal(')')
        return x316

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        name317 = self.consume_terminal('STRING')
        _t1026 = self.parse_relation_id()
        relation_id318 = _t1026
        self.consume_literal(')')
        _t1027 = transactions_pb2.ExportCSVColumn(column_name=name317, column_data=relation_id318)
        return _t1027


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
