"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.


Command: python -m meta.cli /Users/nystrom/rai/nn-meta-2-sexp-all/proto/relationalai/lqp/v1/logic.proto /Users/nystrom/rai/nn-meta-2-sexp-all/proto/relationalai/lqp/v1/fragments.proto /Users/nystrom/rai/nn-meta-2-sexp-all/proto/relationalai/lqp/v1/transactions.proto --parser python
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
            _t338 = self.parse_configure()
            _t337 = _t338
        else:
            _t337 = None
        configure0 = _t337
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('sync', 1)):
            _t340 = self.parse_sync()
            _t339 = _t340
        else:
            _t339 = None
        sync1 = _t339
        xs2 = []
        cond3 = self.match_lookahead_literal('(', 0)
        while cond3:
            _t341 = self.parse_epoch()
            xs2.append(_t341)
            cond3 = self.match_lookahead_literal('(', 0)
        epochs4 = xs2
        self.consume_literal(')')
        _t342 = transactions_pb2.Transaction(epochs=epochs4, configure=(configure0 if configure0 is not None else self.construct_configure([])), sync=sync1)
        return _t342

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal('(')
        self.consume_literal('configure')
        _t343 = self.parse_config_dict()
        config_dict5 = _t343
        self.consume_literal(')')
        return self.construct_configure(config_dict5)

    def parse_config_dict(self) -> list[tuple[str, logic_pb2.Value]]:
        self.consume_literal('{')
        xs6 = []
        cond7 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond7:
            _t344 = self.parse_config_key_value()
            xs6.append(_t344)
            cond7 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        x8 = xs6
        self.consume_literal('}')
        return x8

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        symbol9 = self.consume_terminal('COLON_SYMBOL')
        _t345 = self.parse_value()
        value10 = _t345
        return (symbol9, value10,)

    def parse_value(self) -> logic_pb2.Value:
        if self.match_lookahead_literal('true', 0):
            _t346 = 9
        else:
            if self.match_lookahead_literal('missing', 0):
                _t347 = 8
            else:
                if self.match_lookahead_literal('false', 0):
                    _t348 = 9
                else:
                    if self.match_lookahead_literal('(', 0):
                        if self.match_lookahead_literal('datetime', 1):
                            _t351 = 1
                        else:
                            if self.match_lookahead_literal('date', 1):
                                _t352 = 0
                            else:
                                _t352 = -1
                            _t351 = _t352
                        _t349 = _t351
                    else:
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t353 = 5
                        else:
                            if self.match_lookahead_terminal('STRING', 0):
                                _t354 = 2
                            else:
                                if self.match_lookahead_terminal('INT128', 0):
                                    _t355 = 6
                                else:
                                    if self.match_lookahead_terminal('INT', 0):
                                        _t356 = 3
                                    else:
                                        if self.match_lookahead_terminal('FLOAT', 0):
                                            _t357 = 4
                                        else:
                                            if self.match_lookahead_terminal('DECIMAL', 0):
                                                _t358 = 7
                                            else:
                                                _t358 = -1
                                            _t357 = _t358
                                        _t356 = _t357
                                    _t355 = _t356
                                _t354 = _t355
                            _t353 = _t354
                        _t349 = _t353
                    _t348 = _t349
                _t347 = _t348
            _t346 = _t347
        prediction11 = _t346
        if prediction11 == 9:
            _t360 = self.parse_boolean_value()
            value20 = _t360
            _t361 = logic_pb2.Value(boolean_value=value20)
            _t359 = _t361
        else:
            if prediction11 == 8:
                self.consume_literal('missing')
                _t363 = logic_pb2.Value(missing_value=logic_pb2.MissingValue())
                _t362 = _t363
            else:
                if prediction11 == 7:
                    value19 = self.consume_terminal('DECIMAL')
                    _t365 = logic_pb2.Value(decimal_value=value19)
                    _t364 = _t365
                else:
                    if prediction11 == 6:
                        value18 = self.consume_terminal('INT128')
                        _t367 = logic_pb2.Value(int128_value=value18)
                        _t366 = _t367
                    else:
                        if prediction11 == 5:
                            value17 = self.consume_terminal('UINT128')
                            _t369 = logic_pb2.Value(uint128_value=value17)
                            _t368 = _t369
                        else:
                            if prediction11 == 4:
                                value16 = self.consume_terminal('FLOAT')
                                _t371 = logic_pb2.Value(float_value=value16)
                                _t370 = _t371
                            else:
                                if prediction11 == 3:
                                    value15 = self.consume_terminal('INT')
                                    _t373 = logic_pb2.Value(int_value=value15)
                                    _t372 = _t373
                                else:
                                    if prediction11 == 2:
                                        value14 = self.consume_terminal('STRING')
                                        _t375 = logic_pb2.Value(string_value=value14)
                                        _t374 = _t375
                                    else:
                                        if prediction11 == 1:
                                            _t377 = self.parse_datetime()
                                            value13 = _t377
                                            _t378 = logic_pb2.Value(datetime_value=value13)
                                            _t376 = _t378
                                        else:
                                            if prediction11 == 0:
                                                _t380 = self.parse_date()
                                                value12 = _t380
                                                _t381 = logic_pb2.Value(date_value=value12)
                                                _t379 = _t381
                                            else:
                                                raise ParseError(f"{'Unexpected token in value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t379 = None
                                            _t376 = _t379
                                        _t374 = _t376
                                    _t372 = _t374
                                _t370 = _t372
                            _t368 = _t370
                        _t366 = _t368
                    _t364 = _t366
                _t362 = _t364
            _t359 = _t362
        return _t359

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal('(')
        self.consume_literal('date')
        year21 = self.consume_terminal('INT')
        month22 = self.consume_terminal('INT')
        day23 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t382 = logic_pb2.DateValue(year=int(year21), month=int(month22), day=int(day23))
        return _t382

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
            _t383 = self.consume_terminal('INT')
        else:
            _t383 = None
        microsecond30 = _t383
        self.consume_literal(')')
        _t384 = logic_pb2.DateTimeValue(year=int(year24), month=int(month25), day=int(day26), hour=int(hour27), minute=int(minute28), second=int(second29), microsecond=int((microsecond30 if microsecond30 is not None else 0)))
        return _t384

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal('true', 0):
            _t385 = 0
        else:
            _t385 = (self.match_lookahead_literal('false', 0) or -1)
        prediction31 = _t385
        if prediction31 == 1:
            self.consume_literal('false')
            _t386 = False
        else:
            if prediction31 == 0:
                self.consume_literal('true')
                _t387 = True
            else:
                raise ParseError(f"{'Unexpected token in boolean_value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t387 = None
            _t386 = _t387
        return _t386

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal('(')
        self.consume_literal('sync')
        xs32 = []
        cond33 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond33:
            _t388 = self.parse_fragment_id()
            xs32.append(_t388)
            cond33 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        fragments34 = xs32
        self.consume_literal(')')
        _t389 = transactions_pb2.Sync(fragments=fragments34)
        return _t389

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        symbol35 = self.consume_terminal('COLON_SYMBOL')
        return fragments_pb2.FragmentId(id=symbol35.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal('(')
        self.consume_literal('epoch')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('writes', 1)):
            _t391 = self.parse_epoch_writes()
            _t390 = _t391
        else:
            _t390 = None
        writes36 = _t390
        if self.match_lookahead_literal('(', 0):
            _t393 = self.parse_epoch_reads()
            _t392 = _t393
        else:
            _t392 = None
        reads37 = _t392
        self.consume_literal(')')
        _t394 = transactions_pb2.Epoch(writes=(writes36 if writes36 is not None else []), reads=(reads37 if reads37 is not None else []))
        return _t394

    def parse_epoch_writes(self) -> list[transactions_pb2.Write]:
        self.consume_literal('(')
        self.consume_literal('writes')
        xs38 = []
        cond39 = self.match_lookahead_literal('(', 0)
        while cond39:
            _t395 = self.parse_write()
            xs38.append(_t395)
            cond39 = self.match_lookahead_literal('(', 0)
        x40 = xs38
        self.consume_literal(')')
        return x40

    def parse_write(self) -> transactions_pb2.Write:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('undefine', 1):
                _t399 = 1
            else:
                if self.match_lookahead_literal('define', 1):
                    _t400 = 0
                else:
                    if self.match_lookahead_literal('context', 1):
                        _t401 = 2
                    else:
                        _t401 = -1
                    _t400 = _t401
                _t399 = _t400
            _t396 = _t399
        else:
            _t396 = -1
        prediction41 = _t396
        if prediction41 == 2:
            _t403 = self.parse_context()
            value44 = _t403
            _t404 = transactions_pb2.Write(context=value44)
            _t402 = _t404
        else:
            if prediction41 == 1:
                _t406 = self.parse_undefine()
                value43 = _t406
                _t407 = transactions_pb2.Write(undefine=value43)
                _t405 = _t407
            else:
                if prediction41 == 0:
                    _t409 = self.parse_define()
                    value42 = _t409
                    _t410 = transactions_pb2.Write(define=value42)
                    _t408 = _t410
                else:
                    raise ParseError(f"{'Unexpected token in write'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t408 = None
                _t405 = _t408
            _t402 = _t405
        return _t402

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal('(')
        self.consume_literal('define')
        _t411 = self.parse_fragment()
        fragment45 = _t411
        self.consume_literal(')')
        _t412 = transactions_pb2.Define(fragment=fragment45)
        return _t412

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal('(')
        self.consume_literal('fragment')
        _t413 = self.parse_new_fragment_id()
        fragment_id46 = _t413
        xs47 = []
        cond48 = self.match_lookahead_literal('(', 0)
        while cond48:
            _t414 = self.parse_declaration()
            xs47.append(_t414)
            cond48 = self.match_lookahead_literal('(', 0)
        declarations49 = xs47
        self.consume_literal(')')
        return self.construct_fragment(fragment_id46, declarations49)

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        _t415 = self.parse_fragment_id()
        fragment_id50 = _t415
        self.start_fragment(fragment_id50)
        return fragment_id50

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('rel_edb', 1):
                _t417 = 3
            else:
                if self.match_lookahead_literal('functional_dependency', 1):
                    _t418 = 2
                else:
                    if self.match_lookahead_literal('def', 1):
                        _t419 = 0
                    else:
                        if self.match_lookahead_literal('csv_data', 1):
                            _t420 = 3
                        else:
                            if self.match_lookahead_literal('betree_relation', 1):
                                _t421 = 3
                            else:
                                _t421 = (self.match_lookahead_literal('algorithm', 1) or -1)
                            _t420 = _t421
                        _t419 = _t420
                    _t418 = _t419
                _t417 = _t418
            _t416 = _t417
        else:
            _t416 = -1
        prediction51 = _t416
        if prediction51 == 3:
            _t423 = self.parse_data()
            value55 = _t423
            _t424 = logic_pb2.Declaration(data=value55)
            _t422 = _t424
        else:
            if prediction51 == 2:
                _t426 = self.parse_constraint()
                value54 = _t426
                _t427 = logic_pb2.Declaration(constraint=value54)
                _t425 = _t427
            else:
                if prediction51 == 1:
                    _t429 = self.parse_algorithm()
                    value53 = _t429
                    _t430 = logic_pb2.Declaration(algorithm=value53)
                    _t428 = _t430
                else:
                    if prediction51 == 0:
                        _t432 = self.parse_def()
                        value52 = _t432
                        _t433 = logic_pb2.Declaration()
                        getattr(_t433, 'def').CopyFrom(value52)
                        _t431 = _t433
                    else:
                        raise ParseError(f"{'Unexpected token in declaration'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t431 = None
                    _t428 = _t431
                _t425 = _t428
            _t422 = _t425
        return _t422

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal('(')
        self.consume_literal('def')
        _t434 = self.parse_relation_id()
        name56 = _t434
        _t435 = self.parse_abstraction()
        body57 = _t435
        if self.match_lookahead_literal('(', 0):
            _t437 = self.parse_attrs()
            _t436 = _t437
        else:
            _t436 = None
        attrs58 = _t436
        self.consume_literal(')')
        _t438 = logic_pb2.Def(name=name56, body=body57, attrs=(attrs58 if attrs58 is not None else []))
        return _t438

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_terminal('INT', 0):
            _t440 = 1
        else:
            if self.match_lookahead_terminal('COLON_SYMBOL', 0):
                _t441 = 0
            else:
                _t441 = -1
            _t440 = _t441
        prediction59 = _t440
        if prediction59 == 1:
            INT61 = self.consume_terminal('INT')
            _t442 = logic_pb2.RelationId(id_low=INT61 & 0xFFFFFFFFFFFFFFFF, id_high=(INT61 >> 64) & 0xFFFFFFFFFFFFFFFF)
        else:
            if prediction59 == 0:
                symbol60 = self.consume_terminal('COLON_SYMBOL')
                _t443 = self.relation_id_from_string(symbol60)
            else:
                raise ParseError(f"{'Unexpected token in relation_id'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t443 = None
            _t442 = _t443
        return _t442

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal('(')
        _t444 = self.parse_bindings()
        bindings62 = _t444
        _t445 = self.parse_formula()
        formula63 = _t445
        self.consume_literal(')')
        _t446 = logic_pb2.Abstraction(vars=(bindings62[0] + (bindings62[1] if bindings62[1] is not None else [])), value=formula63)
        return _t446

    def parse_bindings(self) -> tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]:
        self.consume_literal('[')
        xs64 = []
        cond65 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond65:
            _t447 = self.parse_binding()
            xs64.append(_t447)
            cond65 = self.match_lookahead_terminal('SYMBOL', 0)
        keys66 = xs64
        if self.match_lookahead_literal('|', 0):
            _t449 = self.parse_value_bindings()
            _t448 = _t449
        else:
            _t448 = None
        values67 = _t448
        self.consume_literal(']')
        return (keys66, (values67 if values67 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol68 = self.consume_terminal('SYMBOL')
        self.consume_literal('::')
        _t450 = self.parse_type()
        type69 = _t450
        _t451 = logic_pb2.Var(name=symbol68)
        _t452 = logic_pb2.Binding(var=_t451, type=type69)
        return _t452

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal('UNKNOWN', 0):
            _t453 = 0
        else:
            if self.match_lookahead_literal('UINT128', 0):
                _t454 = 4
            else:
                if self.match_lookahead_literal('STRING', 0):
                    _t463 = 1
                else:
                    if self.match_lookahead_literal('MISSING', 0):
                        _t464 = 8
                    else:
                        if self.match_lookahead_literal('INT128', 0):
                            _t465 = 5
                        else:
                            if self.match_lookahead_literal('INT', 0):
                                _t466 = 2
                            else:
                                if self.match_lookahead_literal('FLOAT', 0):
                                    _t467 = 3
                                else:
                                    if self.match_lookahead_literal('DATETIME', 0):
                                        _t468 = 7
                                    else:
                                        if self.match_lookahead_literal('DATE', 0):
                                            _t469 = 6
                                        else:
                                            if self.match_lookahead_literal('BOOLEAN', 0):
                                                _t470 = 10
                                            else:
                                                if self.match_lookahead_literal('(', 0):
                                                    _t471 = 9
                                                else:
                                                    _t471 = -1
                                                _t470 = _t471
                                            _t469 = _t470
                                        _t468 = _t469
                                    _t467 = _t468
                                _t466 = _t467
                            _t465 = _t466
                        _t464 = _t465
                    _t463 = _t464
                _t454 = _t463
            _t453 = _t454
        prediction70 = _t453
        if prediction70 == 10:
            _t473 = self.parse_boolean_type()
            value81 = _t473
            _t474 = logic_pb2.Type(boolean_type=value81)
            _t472 = _t474
        else:
            if prediction70 == 9:
                _t476 = self.parse_decimal_type()
                value80 = _t476
                _t477 = logic_pb2.Type(decimal_type=value80)
                _t475 = _t477
            else:
                if prediction70 == 8:
                    _t479 = self.parse_missing_type()
                    value79 = _t479
                    _t480 = logic_pb2.Type(missing_type=value79)
                    _t478 = _t480
                else:
                    if prediction70 == 7:
                        _t482 = self.parse_datetime_type()
                        value78 = _t482
                        _t483 = logic_pb2.Type(datetime_type=value78)
                        _t481 = _t483
                    else:
                        if prediction70 == 6:
                            _t485 = self.parse_date_type()
                            value77 = _t485
                            _t486 = logic_pb2.Type(date_type=value77)
                            _t484 = _t486
                        else:
                            if prediction70 == 5:
                                _t488 = self.parse_int128_type()
                                value76 = _t488
                                _t489 = logic_pb2.Type(int128_type=value76)
                                _t487 = _t489
                            else:
                                if prediction70 == 4:
                                    _t491 = self.parse_uint128_type()
                                    value75 = _t491
                                    _t492 = logic_pb2.Type(uint128_type=value75)
                                    _t490 = _t492
                                else:
                                    if prediction70 == 3:
                                        _t494 = self.parse_float_type()
                                        value74 = _t494
                                        _t495 = logic_pb2.Type(float_type=value74)
                                        _t493 = _t495
                                    else:
                                        if prediction70 == 2:
                                            _t497 = self.parse_int_type()
                                            value73 = _t497
                                            _t498 = logic_pb2.Type(int_type=value73)
                                            _t496 = _t498
                                        else:
                                            if prediction70 == 1:
                                                _t500 = self.parse_string_type()
                                                value72 = _t500
                                                _t501 = logic_pb2.Type(string_type=value72)
                                                _t499 = _t501
                                            else:
                                                if prediction70 == 0:
                                                    _t503 = self.parse_unspecified_type()
                                                    value71 = _t503
                                                    _t504 = logic_pb2.Type(unspecified_type=value71)
                                                    _t502 = _t504
                                                else:
                                                    raise ParseError(f"{'Unexpected token in type'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                    _t502 = None
                                                _t499 = _t502
                                            _t496 = _t499
                                        _t493 = _t496
                                    _t490 = _t493
                                _t487 = _t490
                            _t484 = _t487
                        _t481 = _t484
                    _t478 = _t481
                _t475 = _t478
            _t472 = _t475
        return _t472

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
        _t505 = logic_pb2.DecimalType(precision=int(precision82), scale=int(scale83))
        return _t505

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal('BOOLEAN')
        return logic_pb2.BooleanType()

    def parse_value_bindings(self) -> list[logic_pb2.Binding]:
        self.consume_literal('|')
        xs84 = []
        cond85 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond85:
            _t506 = self.parse_binding()
            xs84.append(_t506)
            cond85 = self.match_lookahead_terminal('SYMBOL', 0)
        x86 = xs84
        return x86

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('true', 1):
                _t508 = 0
            else:
                if self.match_lookahead_literal('relatom', 1):
                    _t509 = 11
                else:
                    if self.match_lookahead_literal('reduce', 1):
                        _t510 = 3
                    else:
                        if self.match_lookahead_literal('primitive', 1):
                            _t511 = 10
                        else:
                            if self.match_lookahead_literal('pragma', 1):
                                _t512 = 9
                            else:
                                if self.match_lookahead_literal('or', 1):
                                    _t513 = 5
                                else:
                                    if self.match_lookahead_literal('not', 1):
                                        _t514 = 6
                                    else:
                                        if self.match_lookahead_literal('ffi', 1):
                                            _t515 = 7
                                        else:
                                            if self.match_lookahead_literal('false', 1):
                                                _t529 = 1
                                            else:
                                                if self.match_lookahead_literal('exists', 1):
                                                    _t530 = 2
                                                else:
                                                    if self.match_lookahead_literal('cast', 1):
                                                        _t531 = 12
                                                    else:
                                                        if self.match_lookahead_literal('atom', 1):
                                                            _t532 = 8
                                                        else:
                                                            if self.match_lookahead_literal('and', 1):
                                                                _t533 = 4
                                                            else:
                                                                if self.match_lookahead_literal('>=', 1):
                                                                    _t534 = 10
                                                                else:
                                                                    if self.match_lookahead_literal('>', 1):
                                                                        _t535 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal('=', 1):
                                                                            _t536 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal('<=', 1):
                                                                                _t537 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal('<', 1):
                                                                                    _t538 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal('/', 1):
                                                                                        _t539 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal('-', 1):
                                                                                            _t540 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal('+', 1):
                                                                                                _t541 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal('*', 1):
                                                                                                    _t542 = 10
                                                                                                else:
                                                                                                    _t542 = -1
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
                                            _t515 = _t529
                                        _t514 = _t515
                                    _t513 = _t514
                                _t512 = _t513
                            _t511 = _t512
                        _t510 = _t511
                    _t509 = _t510
                _t508 = _t509
            _t507 = _t508
        else:
            _t507 = -1
        prediction87 = _t507
        if prediction87 == 12:
            _t544 = self.parse_cast()
            value100 = _t544
            _t545 = logic_pb2.Formula(cast=value100)
            _t543 = _t545
        else:
            if prediction87 == 11:
                _t547 = self.parse_rel_atom()
                value99 = _t547
                _t548 = logic_pb2.Formula(rel_atom=value99)
                _t546 = _t548
            else:
                if prediction87 == 10:
                    _t550 = self.parse_primitive()
                    value98 = _t550
                    _t551 = logic_pb2.Formula(primitive=value98)
                    _t549 = _t551
                else:
                    if prediction87 == 9:
                        _t553 = self.parse_pragma()
                        value97 = _t553
                        _t554 = logic_pb2.Formula(pragma=value97)
                        _t552 = _t554
                    else:
                        if prediction87 == 8:
                            _t556 = self.parse_atom()
                            value96 = _t556
                            _t557 = logic_pb2.Formula(atom=value96)
                            _t555 = _t557
                        else:
                            if prediction87 == 7:
                                _t559 = self.parse_ffi()
                                value95 = _t559
                                _t560 = logic_pb2.Formula(ffi=value95)
                                _t558 = _t560
                            else:
                                if prediction87 == 6:
                                    _t562 = self.parse_not()
                                    value94 = _t562
                                    _t563 = logic_pb2.Formula()
                                    getattr(_t563, 'not').CopyFrom(value94)
                                    _t561 = _t563
                                else:
                                    if prediction87 == 5:
                                        _t565 = self.parse_disjunction()
                                        value93 = _t565
                                        _t566 = logic_pb2.Formula(disjunction=value93)
                                        _t564 = _t566
                                    else:
                                        if prediction87 == 4:
                                            _t568 = self.parse_conjunction()
                                            value92 = _t568
                                            _t569 = logic_pb2.Formula(conjunction=value92)
                                            _t567 = _t569
                                        else:
                                            if prediction87 == 3:
                                                _t571 = self.parse_reduce()
                                                value91 = _t571
                                                _t572 = logic_pb2.Formula(reduce=value91)
                                                _t570 = _t572
                                            else:
                                                if prediction87 == 2:
                                                    _t574 = self.parse_exists()
                                                    value90 = _t574
                                                    _t575 = logic_pb2.Formula(exists=value90)
                                                    _t573 = _t575
                                                else:
                                                    if prediction87 == 1:
                                                        _t577 = self.parse_false()
                                                        value89 = _t577
                                                        _t578 = logic_pb2.Formula(disjunction=value89)
                                                        _t576 = _t578
                                                    else:
                                                        if prediction87 == 0:
                                                            _t580 = self.parse_true()
                                                            value88 = _t580
                                                            _t581 = logic_pb2.Formula(conjunction=value88)
                                                            _t579 = _t581
                                                        else:
                                                            raise ParseError(f"{'Unexpected token in formula'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t579 = None
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
                _t546 = _t549
            _t543 = _t546
        return _t543

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('true')
        self.consume_literal(')')
        _t582 = logic_pb2.Conjunction(args=[])
        return _t582

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('false')
        self.consume_literal(')')
        _t583 = logic_pb2.Disjunction(args=[])
        return _t583

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal('(')
        self.consume_literal('exists')
        _t584 = self.parse_bindings()
        bindings101 = _t584
        _t585 = self.parse_formula()
        formula102 = _t585
        self.consume_literal(')')
        _t586 = logic_pb2.Abstraction(vars=(bindings101[0] + (bindings101[1] if bindings101[1] is not None else [])), value=formula102)
        _t587 = logic_pb2.Exists(body=_t586)
        return _t587

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal('(')
        self.consume_literal('reduce')
        _t588 = self.parse_abstraction()
        op103 = _t588
        _t589 = self.parse_abstraction()
        body104 = _t589
        _t590 = self.parse_terms()
        terms105 = _t590
        self.consume_literal(')')
        _t591 = logic_pb2.Reduce(op=op103, body=body104, terms=terms105)
        return _t591

    def parse_terms(self) -> list[logic_pb2.Term]:
        self.consume_literal('(')
        self.consume_literal('terms')
        xs106 = []
        cond107 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond107:
            _t592 = self.parse_term()
            xs106.append(_t592)
            cond107 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        x108 = xs106
        self.consume_literal(')')
        return x108

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_literal('true', 0):
            _t624 = 1
        else:
            if self.match_lookahead_literal('missing', 0):
                _t640 = 1
            else:
                if self.match_lookahead_literal('false', 0):
                    _t648 = 1
                else:
                    if self.match_lookahead_literal('(', 0):
                        _t652 = 1
                    else:
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t654 = 1
                        else:
                            if self.match_lookahead_terminal('SYMBOL', 0):
                                _t655 = 0
                            else:
                                _t655 = (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or -1)))))
                            _t654 = _t655
                        _t652 = _t654
                    _t648 = _t652
                _t640 = _t648
            _t624 = _t640
        prediction109 = _t624
        if prediction109 == 1:
            _t657 = self.parse_constant()
            value111 = _t657
            _t658 = logic_pb2.Term(constant=value111)
            _t656 = _t658
        else:
            if prediction109 == 0:
                _t660 = self.parse_var()
                value110 = _t660
                _t661 = logic_pb2.Term(var=value110)
                _t659 = _t661
            else:
                raise ParseError(f"{'Unexpected token in term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t659 = None
            _t656 = _t659
        return _t656

    def parse_var(self) -> logic_pb2.Var:
        symbol112 = self.consume_terminal('SYMBOL')
        _t662 = logic_pb2.Var(name=symbol112)
        return _t662

    def parse_constant(self) -> logic_pb2.Value:
        _t663 = self.parse_value()
        x113 = _t663
        return x113

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('and')
        xs114 = []
        cond115 = self.match_lookahead_literal('(', 0)
        while cond115:
            _t664 = self.parse_formula()
            xs114.append(_t664)
            cond115 = self.match_lookahead_literal('(', 0)
        args116 = xs114
        self.consume_literal(')')
        _t665 = logic_pb2.Conjunction(args=args116)
        return _t665

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('or')
        xs117 = []
        cond118 = self.match_lookahead_literal('(', 0)
        while cond118:
            _t666 = self.parse_formula()
            xs117.append(_t666)
            cond118 = self.match_lookahead_literal('(', 0)
        args119 = xs117
        self.consume_literal(')')
        _t667 = logic_pb2.Disjunction(args=args119)
        return _t667

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal('(')
        self.consume_literal('not')
        _t668 = self.parse_formula()
        arg120 = _t668
        self.consume_literal(')')
        _t669 = logic_pb2.Not(arg=arg120)
        return _t669

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal('(')
        self.consume_literal('ffi')
        _t670 = self.parse_name()
        name121 = _t670
        _t671 = self.parse_ffi_args()
        args122 = _t671
        _t672 = self.parse_terms()
        terms123 = _t672
        self.consume_literal(')')
        _t673 = logic_pb2.FFI(name=name121, args=args122, terms=terms123)
        return _t673

    def parse_name(self) -> str:
        x124 = self.consume_terminal('COLON_SYMBOL')
        return x124

    def parse_ffi_args(self) -> list[logic_pb2.Abstraction]:
        self.consume_literal('(')
        self.consume_literal('args')
        xs125 = []
        cond126 = self.match_lookahead_literal('(', 0)
        while cond126:
            _t674 = self.parse_abstraction()
            xs125.append(_t674)
            cond126 = self.match_lookahead_literal('(', 0)
        x127 = xs125
        self.consume_literal(')')
        return x127

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal('(')
        self.consume_literal('atom')
        _t675 = self.parse_relation_id()
        name128 = _t675
        xs129 = []
        cond130 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond130:
            _t676 = self.parse_term()
            xs129.append(_t676)
            cond130 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms131 = xs129
        self.consume_literal(')')
        _t677 = logic_pb2.Atom(name=name128, terms=terms131)
        return _t677

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal('(')
        self.consume_literal('pragma')
        _t678 = self.parse_name()
        name132 = _t678
        xs133 = []
        cond134 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond134:
            _t679 = self.parse_term()
            xs133.append(_t679)
            cond134 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms135 = xs133
        self.consume_literal(')')
        _t680 = logic_pb2.Pragma(name=name132, terms=terms135)
        return _t680

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('primitive', 1):
                _t682 = 9
            else:
                if self.match_lookahead_literal('>=', 1):
                    _t683 = 4
                else:
                    if self.match_lookahead_literal('>', 1):
                        _t684 = 3
                    else:
                        if self.match_lookahead_literal('=', 1):
                            _t685 = 0
                        else:
                            if self.match_lookahead_literal('<=', 1):
                                _t686 = 2
                            else:
                                if self.match_lookahead_literal('<', 1):
                                    _t691 = 1
                                else:
                                    if self.match_lookahead_literal('/', 1):
                                        _t692 = 8
                                    else:
                                        if self.match_lookahead_literal('-', 1):
                                            _t693 = 6
                                        else:
                                            if self.match_lookahead_literal('+', 1):
                                                _t694 = 5
                                            else:
                                                if self.match_lookahead_literal('*', 1):
                                                    _t695 = 7
                                                else:
                                                    _t695 = -1
                                                _t694 = _t695
                                            _t693 = _t694
                                        _t692 = _t693
                                    _t691 = _t692
                                _t686 = _t691
                            _t685 = _t686
                        _t684 = _t685
                    _t683 = _t684
                _t682 = _t683
            _t681 = _t682
        else:
            _t681 = -1
        prediction136 = _t681
        if prediction136 == 9:
            self.consume_literal('(')
            self.consume_literal('primitive')
            _t697 = self.parse_name()
            name146 = _t697
            xs147 = []
            cond148 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            while cond148:
                _t698 = self.parse_rel_term()
                xs147.append(_t698)
                cond148 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            terms149 = xs147
            self.consume_literal(')')
            _t699 = logic_pb2.Primitive(name=name146, terms=terms149)
            _t696 = _t699
        else:
            if prediction136 == 8:
                _t701 = self.parse_divide()
                op145 = _t701
                _t700 = op145
            else:
                if prediction136 == 7:
                    _t703 = self.parse_multiply()
                    op144 = _t703
                    _t702 = op144
                else:
                    if prediction136 == 6:
                        _t705 = self.parse_minus()
                        op143 = _t705
                        _t704 = op143
                    else:
                        if prediction136 == 5:
                            _t707 = self.parse_add()
                            op142 = _t707
                            _t706 = op142
                        else:
                            if prediction136 == 4:
                                _t709 = self.parse_gt_eq()
                                op141 = _t709
                                _t708 = op141
                            else:
                                if prediction136 == 3:
                                    _t711 = self.parse_gt()
                                    op140 = _t711
                                    _t710 = op140
                                else:
                                    if prediction136 == 2:
                                        _t713 = self.parse_lt_eq()
                                        op139 = _t713
                                        _t712 = op139
                                    else:
                                        if prediction136 == 1:
                                            _t715 = self.parse_lt()
                                            op138 = _t715
                                            _t714 = op138
                                        else:
                                            if prediction136 == 0:
                                                _t717 = self.parse_eq()
                                                op137 = _t717
                                                _t716 = op137
                                            else:
                                                raise ParseError(f"{'Unexpected token in primitive'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t716 = None
                                            _t714 = _t716
                                        _t712 = _t714
                                    _t710 = _t712
                                _t708 = _t710
                            _t706 = _t708
                        _t704 = _t706
                    _t702 = _t704
                _t700 = _t702
            _t696 = _t700
        return _t696

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('=')
        _t718 = self.parse_term()
        left150 = _t718
        _t719 = self.parse_term()
        right151 = _t719
        self.consume_literal(')')
        _t720 = logic_pb2.RelTerm(term=left150)
        _t721 = logic_pb2.RelTerm(term=right151)
        _t722 = logic_pb2.Primitive(name='rel_primitive_eq', terms=[_t720, _t721])
        return _t722

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<')
        _t723 = self.parse_term()
        left152 = _t723
        _t724 = self.parse_term()
        right153 = _t724
        self.consume_literal(')')
        _t725 = logic_pb2.RelTerm(term=left152)
        _t726 = logic_pb2.RelTerm(term=right153)
        _t727 = logic_pb2.Primitive(name='rel_primitive_lt_monotype', terms=[_t725, _t726])
        return _t727

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<=')
        _t728 = self.parse_term()
        left154 = _t728
        _t729 = self.parse_term()
        right155 = _t729
        self.consume_literal(')')
        _t730 = logic_pb2.RelTerm(term=left154)
        _t731 = logic_pb2.RelTerm(term=right155)
        _t732 = logic_pb2.Primitive(name='rel_primitive_lt_eq_monotype', terms=[_t730, _t731])
        return _t732

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>')
        _t733 = self.parse_term()
        left156 = _t733
        _t734 = self.parse_term()
        right157 = _t734
        self.consume_literal(')')
        _t735 = logic_pb2.RelTerm(term=left156)
        _t736 = logic_pb2.RelTerm(term=right157)
        _t737 = logic_pb2.Primitive(name='rel_primitive_gt_monotype', terms=[_t735, _t736])
        return _t737

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>=')
        _t738 = self.parse_term()
        left158 = _t738
        _t739 = self.parse_term()
        right159 = _t739
        self.consume_literal(')')
        _t740 = logic_pb2.RelTerm(term=left158)
        _t741 = logic_pb2.RelTerm(term=right159)
        _t742 = logic_pb2.Primitive(name='rel_primitive_gt_eq_monotype', terms=[_t740, _t741])
        return _t742

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('+')
        _t743 = self.parse_term()
        left160 = _t743
        _t744 = self.parse_term()
        right161 = _t744
        _t745 = self.parse_term()
        result162 = _t745
        self.consume_literal(')')
        _t746 = logic_pb2.RelTerm(term=left160)
        _t747 = logic_pb2.RelTerm(term=right161)
        _t748 = logic_pb2.RelTerm(term=result162)
        _t749 = logic_pb2.Primitive(name='rel_primitive_add_monotype', terms=[_t746, _t747, _t748])
        return _t749

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('-')
        _t750 = self.parse_term()
        left163 = _t750
        _t751 = self.parse_term()
        right164 = _t751
        _t752 = self.parse_term()
        result165 = _t752
        self.consume_literal(')')
        _t753 = logic_pb2.RelTerm(term=left163)
        _t754 = logic_pb2.RelTerm(term=right164)
        _t755 = logic_pb2.RelTerm(term=result165)
        _t756 = logic_pb2.Primitive(name='rel_primitive_subtract_monotype', terms=[_t753, _t754, _t755])
        return _t756

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('*')
        _t757 = self.parse_term()
        left166 = _t757
        _t758 = self.parse_term()
        right167 = _t758
        _t759 = self.parse_term()
        result168 = _t759
        self.consume_literal(')')
        _t760 = logic_pb2.RelTerm(term=left166)
        _t761 = logic_pb2.RelTerm(term=right167)
        _t762 = logic_pb2.RelTerm(term=result168)
        _t763 = logic_pb2.Primitive(name='rel_primitive_multiply_monotype', terms=[_t760, _t761, _t762])
        return _t763

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('/')
        _t764 = self.parse_term()
        left169 = _t764
        _t765 = self.parse_term()
        right170 = _t765
        _t766 = self.parse_term()
        result171 = _t766
        self.consume_literal(')')
        _t767 = logic_pb2.RelTerm(term=left169)
        _t768 = logic_pb2.RelTerm(term=right170)
        _t769 = logic_pb2.RelTerm(term=result171)
        _t770 = logic_pb2.Primitive(name='rel_primitive_divide_monotype', terms=[_t767, _t768, _t769])
        return _t770

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_literal('true', 0):
            _t786 = 1
        else:
            if self.match_lookahead_literal('missing', 0):
                _t794 = 1
            else:
                if self.match_lookahead_literal('false', 0):
                    _t798 = 1
                else:
                    if self.match_lookahead_literal('(', 0):
                        _t800 = 1
                    else:
                        if self.match_lookahead_literal('#', 0):
                            _t801 = 0
                        else:
                            _t801 = (self.match_lookahead_terminal('UINT128', 0) or (self.match_lookahead_terminal('SYMBOL', 0) or (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or -1)))))))
                        _t800 = _t801
                    _t798 = _t800
                _t794 = _t798
            _t786 = _t794
        prediction172 = _t786
        if prediction172 == 1:
            _t803 = self.parse_term()
            value174 = _t803
            _t804 = logic_pb2.RelTerm(term=value174)
            _t802 = _t804
        else:
            if prediction172 == 0:
                _t806 = self.parse_specialized_value()
                value173 = _t806
                _t807 = logic_pb2.RelTerm(specialized_value=value173)
                _t805 = _t807
            else:
                raise ParseError(f"{'Unexpected token in rel_term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t805 = None
            _t802 = _t805
        return _t802

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal('#')
        _t808 = self.parse_value()
        value175 = _t808
        return value175

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        self.consume_literal('(')
        self.consume_literal('relatom')
        _t809 = self.parse_name()
        name176 = _t809
        xs177 = []
        cond178 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond178:
            _t810 = self.parse_rel_term()
            xs177.append(_t810)
            cond178 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms179 = xs177
        self.consume_literal(')')
        _t811 = logic_pb2.RelAtom(name=name176, terms=terms179)
        return _t811

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal('(')
        self.consume_literal('cast')
        _t812 = self.parse_term()
        input180 = _t812
        _t813 = self.parse_term()
        result181 = _t813
        self.consume_literal(')')
        _t814 = logic_pb2.Cast(input=input180, result=result181)
        return _t814

    def parse_attrs(self) -> list[logic_pb2.Attribute]:
        self.consume_literal('(')
        self.consume_literal('attrs')
        xs182 = []
        cond183 = self.match_lookahead_literal('(', 0)
        while cond183:
            _t815 = self.parse_attribute()
            xs182.append(_t815)
            cond183 = self.match_lookahead_literal('(', 0)
        x184 = xs182
        self.consume_literal(')')
        return x184

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal('(')
        self.consume_literal('attribute')
        _t816 = self.parse_name()
        name185 = _t816
        xs186 = []
        cond187 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond187:
            _t817 = self.parse_value()
            xs186.append(_t817)
            cond187 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        args188 = xs186
        self.consume_literal(')')
        _t818 = logic_pb2.Attribute(name=name185, args=args188)
        return _t818

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal('(')
        self.consume_literal('algorithm')
        xs189 = []
        cond190 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        while cond190:
            _t819 = self.parse_relation_id()
            xs189.append(_t819)
            cond190 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        global191 = xs189
        _t820 = self.parse_script()
        body192 = _t820
        self.consume_literal(')')
        _t821 = logic_pb2.Algorithm(body=body192)
        getattr(_t821, 'global').extend(global191)
        return _t821

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal('(')
        self.consume_literal('script')
        xs193 = []
        cond194 = self.match_lookahead_literal('(', 0)
        while cond194:
            _t822 = self.parse_construct()
            xs193.append(_t822)
            cond194 = self.match_lookahead_literal('(', 0)
        constructs195 = xs193
        self.consume_literal(')')
        _t823 = logic_pb2.Script(constructs=constructs195)
        return _t823

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t832 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t836 = 1
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t838 = 1
                    else:
                        if self.match_lookahead_literal('loop', 1):
                            _t839 = 0
                        else:
                            _t839 = (self.match_lookahead_literal('break', 1) or (self.match_lookahead_literal('assign', 1) or -1))
                        _t838 = _t839
                    _t836 = _t838
                _t832 = _t836
            _t824 = _t832
        else:
            _t824 = -1
        prediction196 = _t824
        if prediction196 == 1:
            _t841 = self.parse_instruction()
            value198 = _t841
            _t842 = logic_pb2.Construct(instruction=value198)
            _t840 = _t842
        else:
            if prediction196 == 0:
                _t844 = self.parse_loop()
                value197 = _t844
                _t845 = logic_pb2.Construct(loop=value197)
                _t843 = _t845
            else:
                raise ParseError(f"{'Unexpected token in construct'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t843 = None
            _t840 = _t843
        return _t840

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal('(')
        self.consume_literal('loop')
        _t846 = self.parse_init()
        init199 = _t846
        _t847 = self.parse_script()
        body200 = _t847
        self.consume_literal(')')
        _t848 = logic_pb2.Loop(init=init199, body=body200)
        return _t848

    def parse_init(self) -> list[logic_pb2.Instruction]:
        self.consume_literal('(')
        self.consume_literal('init')
        xs201 = []
        cond202 = self.match_lookahead_literal('(', 0)
        while cond202:
            _t849 = self.parse_instruction()
            xs201.append(_t849)
            cond202 = self.match_lookahead_literal('(', 0)
        x203 = xs201
        self.consume_literal(')')
        return x203

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t855 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t856 = 4
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t857 = 3
                    else:
                        if self.match_lookahead_literal('break', 1):
                            _t858 = 2
                        else:
                            if self.match_lookahead_literal('assign', 1):
                                _t859 = 0
                            else:
                                _t859 = -1
                            _t858 = _t859
                        _t857 = _t858
                    _t856 = _t857
                _t855 = _t856
            _t850 = _t855
        else:
            _t850 = -1
        prediction204 = _t850
        if prediction204 == 4:
            _t861 = self.parse_monus_def()
            value209 = _t861
            _t862 = logic_pb2.Instruction(monus_def=value209)
            _t860 = _t862
        else:
            if prediction204 == 3:
                _t864 = self.parse_monoid_def()
                value208 = _t864
                _t865 = logic_pb2.Instruction(monoid_def=value208)
                _t863 = _t865
            else:
                if prediction204 == 2:
                    _t867 = self.parse_break()
                    value207 = _t867
                    _t868 = logic_pb2.Instruction()
                    getattr(_t868, 'break').CopyFrom(value207)
                    _t866 = _t868
                else:
                    if prediction204 == 1:
                        _t870 = self.parse_upsert()
                        value206 = _t870
                        _t871 = logic_pb2.Instruction(upsert=value206)
                        _t869 = _t871
                    else:
                        if prediction204 == 0:
                            _t873 = self.parse_assign()
                            value205 = _t873
                            _t874 = logic_pb2.Instruction(assign=value205)
                            _t872 = _t874
                        else:
                            raise ParseError(f"{'Unexpected token in instruction'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t872 = None
                        _t869 = _t872
                    _t866 = _t869
                _t863 = _t866
            _t860 = _t863
        return _t860

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal('(')
        self.consume_literal('assign')
        _t875 = self.parse_relation_id()
        name210 = _t875
        _t876 = self.parse_abstraction()
        body211 = _t876
        if self.match_lookahead_literal('(', 0):
            _t878 = self.parse_attrs()
            _t877 = _t878
        else:
            _t877 = None
        attrs212 = _t877
        self.consume_literal(')')
        _t879 = logic_pb2.Assign(name=name210, body=body211, attrs=(attrs212 if attrs212 is not None else []))
        return _t879

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal('(')
        self.consume_literal('upsert')
        _t880 = self.parse_relation_id()
        name213 = _t880
        _t881 = self.parse_abstraction_with_arity()
        abstraction_with_arity214 = _t881
        if self.match_lookahead_literal('(', 0):
            _t883 = self.parse_attrs()
            _t882 = _t883
        else:
            _t882 = None
        attrs215 = _t882
        self.consume_literal(')')
        abstraction = abstraction_with_arity214[0]
        arity = abstraction_with_arity214[1]
        _t884 = logic_pb2.Upsert(name=name213, body=abstraction, attrs=(attrs215 if attrs215 is not None else []), value_arity=arity)
        return _t884

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal('(')
        _t885 = self.parse_bindings()
        bindings216 = _t885
        _t886 = self.parse_formula()
        formula217 = _t886
        self.consume_literal(')')
        _t887 = logic_pb2.Abstraction(vars=(bindings216[0] + (bindings216[1] if bindings216[1] is not None else [])), value=formula217)
        return (_t887, len(bindings216[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal('(')
        self.consume_literal('break')
        _t888 = self.parse_relation_id()
        name218 = _t888
        _t889 = self.parse_abstraction()
        body219 = _t889
        if self.match_lookahead_literal('(', 0):
            _t891 = self.parse_attrs()
            _t890 = _t891
        else:
            _t890 = None
        attrs220 = _t890
        self.consume_literal(')')
        _t892 = logic_pb2.Break(name=name218, body=body219, attrs=(attrs220 if attrs220 is not None else []))
        return _t892

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal('(')
        self.consume_literal('monoid')
        _t893 = self.parse_monoid()
        monoid221 = _t893
        _t894 = self.parse_relation_id()
        name222 = _t894
        _t895 = self.parse_abstraction_with_arity()
        abstraction_with_arity223 = _t895
        if self.match_lookahead_literal('(', 0):
            _t897 = self.parse_attrs()
            _t896 = _t897
        else:
            _t896 = None
        attrs224 = _t896
        self.consume_literal(')')
        abstraction = abstraction_with_arity223[0]
        arity = abstraction_with_arity223[1]
        _t898 = logic_pb2.MonoidDef(monoid=monoid221, name=name222, body=abstraction, attrs=(attrs224 if attrs224 is not None else []), value_arity=arity)
        return _t898

    def parse_monoid(self) -> logic_pb2.Monoid:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('sum', 1):
                _t900 = 3
            else:
                if self.match_lookahead_literal('or', 1):
                    _t901 = 0
                else:
                    if self.match_lookahead_literal('min', 1):
                        _t903 = 1
                    else:
                        if self.match_lookahead_literal('max', 1):
                            _t904 = 2
                        else:
                            _t904 = -1
                        _t903 = _t904
                    _t901 = _t903
                _t900 = _t901
            _t899 = _t900
        else:
            _t899 = -1
        prediction225 = _t899
        if prediction225 == 3:
            _t906 = self.parse_sum_monoid()
            value229 = _t906
            _t907 = logic_pb2.Monoid(sum_monoid=value229)
            _t905 = _t907
        else:
            if prediction225 == 2:
                _t909 = self.parse_max_monoid()
                value228 = _t909
                _t910 = logic_pb2.Monoid(max_monoid=value228)
                _t908 = _t910
            else:
                if prediction225 == 1:
                    _t912 = self.parse_min_monoid()
                    value227 = _t912
                    _t913 = logic_pb2.Monoid(min_monoid=value227)
                    _t911 = _t913
                else:
                    if prediction225 == 0:
                        _t915 = self.parse_or_monoid()
                        value226 = _t915
                        _t916 = logic_pb2.Monoid(or_monoid=value226)
                        _t914 = _t916
                    else:
                        raise ParseError(f"{'Unexpected token in monoid'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t914 = None
                    _t911 = _t914
                _t908 = _t911
            _t905 = _t908
        return _t905

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        self.consume_literal('(')
        self.consume_literal('or')
        self.consume_literal(')')
        return logic_pb2.OrMonoid()

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        self.consume_literal('(')
        self.consume_literal('min')
        _t917 = self.parse_type()
        type230 = _t917
        self.consume_literal(')')
        _t918 = logic_pb2.MinMonoid(type=type230)
        return _t918

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        self.consume_literal('(')
        self.consume_literal('max')
        _t919 = self.parse_type()
        type231 = _t919
        self.consume_literal(')')
        _t920 = logic_pb2.MaxMonoid(type=type231)
        return _t920

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        self.consume_literal('(')
        self.consume_literal('sum')
        _t921 = self.parse_type()
        type232 = _t921
        self.consume_literal(')')
        _t922 = logic_pb2.SumMonoid(type=type232)
        return _t922

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal('(')
        self.consume_literal('monus')
        _t923 = self.parse_monoid()
        monoid233 = _t923
        _t924 = self.parse_relation_id()
        name234 = _t924
        _t925 = self.parse_abstraction_with_arity()
        abstraction_with_arity235 = _t925
        if self.match_lookahead_literal('(', 0):
            _t927 = self.parse_attrs()
            _t926 = _t927
        else:
            _t926 = None
        attrs236 = _t926
        self.consume_literal(')')
        abstraction = abstraction_with_arity235[0]
        arity = abstraction_with_arity235[1]
        _t928 = logic_pb2.MonusDef(monoid=monoid233, name=name234, body=abstraction, attrs=(attrs236 if attrs236 is not None else []), value_arity=arity)
        return _t928

    def parse_constraint(self) -> logic_pb2.Constraint:
        self.consume_literal('(')
        self.consume_literal('functional_dependency')
        _t929 = self.parse_relation_id()
        name237 = _t929
        _t930 = self.parse_abstraction()
        guard238 = _t930
        _t931 = self.parse_functional_dependency_keys()
        keys239 = _t931
        _t932 = self.parse_functional_dependency_values()
        values240 = _t932
        self.consume_literal(')')
        _t933 = logic_pb2.FunctionalDependency(guard=guard238, keys=keys239, values=values240)
        _t934 = logic_pb2.Constraint(name=name237, functional_dependency=_t933)
        return _t934

    def parse_functional_dependency_keys(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('keys')
        xs241 = []
        cond242 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond242:
            _t935 = self.parse_var()
            xs241.append(_t935)
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
            _t936 = self.parse_var()
            xs244.append(_t936)
            cond245 = self.match_lookahead_terminal('SYMBOL', 0)
        x246 = xs244
        self.consume_literal(')')
        return x246

    def parse_data(self) -> logic_pb2.Data:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('rel_edb', 1):
                _t938 = 0
            else:
                if self.match_lookahead_literal('csv_data', 1):
                    _t939 = 2
                else:
                    _t939 = (self.match_lookahead_literal('betree_relation', 1) or -1)
                _t938 = _t939
            _t937 = _t938
        else:
            _t937 = -1
        prediction247 = _t937
        if prediction247 == 2:
            _t941 = self.parse_csv_data()
            value250 = _t941
            _t942 = logic_pb2.Data(csv_data=value250)
            _t940 = _t942
        else:
            if prediction247 == 1:
                _t944 = self.parse_betree_relation()
                value249 = _t944
                _t945 = logic_pb2.Data(betree_relation=value249)
                _t943 = _t945
            else:
                if prediction247 == 0:
                    _t947 = self.parse_rel_edb()
                    value248 = _t947
                    _t948 = logic_pb2.Data(rel_edb=value248)
                    _t946 = _t948
                else:
                    raise ParseError(f"{'Unexpected token in data'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t946 = None
                _t943 = _t946
            _t940 = _t943
        return _t940

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        self.consume_literal('(')
        self.consume_literal('rel_edb')
        _t949 = self.parse_relation_id()
        target_id251 = _t949
        xs252 = []
        cond253 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond253:
            _t950 = self.parse_name()
            xs252.append(_t950)
            cond253 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        path254 = xs252
        if self.match_lookahead_literal('(', 0):
            _t952 = self.parse_rel_edb_types()
            _t951 = _t952
        else:
            _t951 = None
        types255 = _t951
        self.consume_literal(')')
        _t953 = logic_pb2.RelEDB(target_id=target_id251, path=path254, types=(types255 if types255 is not None else []))
        return _t953

    def parse_rel_edb_types(self) -> list[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('types')
        xs256 = []
        cond257 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond257:
            _t954 = self.parse_type()
            xs256.append(_t954)
            cond257 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        x258 = xs256
        self.consume_literal(')')
        return x258

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        _t955 = self.parse_be_tree_relation()
        x259 = _t955
        return x259

    def parse_be_tree_relation(self) -> logic_pb2.BeTreeRelation:
        self.consume_literal('(')
        self.consume_literal('betree_relation')
        _t956 = self.parse_relation_id()
        name260 = _t956
        _t957 = self.parse_be_tree_info()
        relation_info261 = _t957
        self.consume_literal(')')
        _t958 = logic_pb2.BeTreeRelation(name=name260, relation_info=relation_info261)
        return _t958

    def parse_be_tree_info(self) -> logic_pb2.BeTreeInfo:
        self.consume_literal('(')
        self.consume_literal('be_tree_info')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('key_types', 1)):
            _t960 = self.parse_be_tree_info_key_types()
            _t959 = _t960
        else:
            _t959 = None
        key_types262 = _t959
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('value_types', 1)):
            _t962 = self.parse_be_tree_info_value_types()
            _t961 = _t962
        else:
            _t961 = None
        value_types263 = _t961
        _t963 = self.parse_be_tree_config()
        storage_config264 = _t963
        _t964 = self.parse_be_tree_locator()
        relation_locator265 = _t964
        self.consume_literal(')')
        _t965 = logic_pb2.BeTreeInfo(key_types=(key_types262 if key_types262 is not None else []), value_types=(value_types263 if value_types263 is not None else []), storage_config=storage_config264, relation_locator=relation_locator265)
        return _t965

    def parse_be_tree_info_key_types(self) -> list[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('key_types')
        xs266 = []
        cond267 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond267:
            _t966 = self.parse_type()
            xs266.append(_t966)
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
            _t967 = self.parse_type()
            xs269.append(_t967)
            cond270 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        x271 = xs269
        self.consume_literal(')')
        return x271

    def parse_be_tree_config(self) -> logic_pb2.BeTreeConfig:
        self.consume_literal('(')
        self.consume_literal('be_tree_config')
        epsilon272 = self.consume_terminal('FLOAT')
        max_pivots273 = self.consume_terminal('INT')
        max_deltas274 = self.consume_terminal('INT')
        max_leaf275 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t968 = logic_pb2.BeTreeConfig(epsilon=epsilon272, max_pivots=max_pivots273, max_deltas=max_deltas274, max_leaf=max_leaf275)
        return _t968

    def parse_be_tree_locator(self) -> logic_pb2.BeTreeLocator:
        self.consume_literal('(')
        self.consume_literal('be_tree_locator')
        element_count276 = self.consume_terminal('INT')
        tree_height277 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t969 = logic_pb2.BeTreeLocator(element_count=element_count276, tree_height=tree_height277)
        return _t969

    def parse_csv_data(self) -> logic_pb2.CSVData:
        _t970 = self.parse_csvdata()
        x278 = _t970
        return x278

    def parse_csvdata(self) -> logic_pb2.CSVData:
        self.consume_literal('(')
        self.consume_literal('csv_data')
        _t971 = self.parse_csvlocator()
        locator279 = _t971
        _t972 = self.parse_csv_config()
        config280 = _t972
        xs281 = []
        cond282 = self.match_lookahead_literal('(', 0)
        while cond282:
            _t973 = self.parse_csv_column()
            xs281.append(_t973)
            cond282 = self.match_lookahead_literal('(', 0)
        columns283 = xs281
        _t974 = self.parse_name()
        asof284 = _t974
        self.consume_literal(')')
        _t975 = logic_pb2.CSVData(locator=locator279, config=config280, columns=columns283, asof=asof284)
        return _t975

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        self.consume_literal('(')
        self.consume_literal('csv_locator')
        xs285 = []
        cond286 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond286:
            _t976 = self.parse_name()
            xs285.append(_t976)
            cond286 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        paths287 = xs285
        _t977 = self.parse_name()
        inline_data288 = _t977
        self.consume_literal(')')
        _t978 = logic_pb2.CSVLocator(paths=paths287, inline_data=inline_data288.encode())
        return _t978

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        self.consume_literal('(')
        self.consume_literal('csv_config')
        header_row289 = self.consume_terminal('INT')
        skip290 = self.consume_terminal('INT')
        _t979 = self.parse_name()
        new_line291 = _t979
        _t980 = self.parse_name()
        delimiter292 = _t980
        _t981 = self.parse_name()
        quotechar293 = _t981
        _t982 = self.parse_name()
        escapechar294 = _t982
        _t983 = self.parse_name()
        comment295 = _t983
        xs296 = []
        cond297 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond297:
            _t984 = self.parse_name()
            xs296.append(_t984)
            cond297 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        missing_strings298 = xs296
        _t985 = self.parse_name()
        decimal_separator299 = _t985
        _t986 = self.parse_name()
        encoding300 = _t986
        _t987 = self.parse_name()
        compression301 = _t987
        self.consume_literal(')')
        _t988 = logic_pb2.CSVConfig(header_row=int(header_row289), skip=skip290, new_line=new_line291, delimiter=delimiter292, quotechar=quotechar293, escapechar=escapechar294, comment=comment295, missing_strings=missing_strings298, decimal_separator=decimal_separator299, encoding=encoding300, compression=compression301)
        return _t988

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        self.consume_literal('(')
        self.consume_literal('csv_column')
        _t989 = self.parse_name()
        column_name302 = _t989
        _t990 = self.parse_relation_id()
        target_id303 = _t990
        xs304 = []
        cond305 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond305:
            _t991 = self.parse_type()
            xs304.append(_t991)
            cond305 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types306 = xs304
        self.consume_literal(')')
        _t992 = logic_pb2.CSVColumn(column_name=column_name302, target_id=target_id303, types=types306)
        return _t992

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal('(')
        self.consume_literal('undefine')
        _t993 = self.parse_fragment_id()
        fragment_id307 = _t993
        self.consume_literal(')')
        _t994 = transactions_pb2.Undefine(fragment_id=fragment_id307)
        return _t994

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal('(')
        self.consume_literal('context')
        xs308 = []
        cond309 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        while cond309:
            _t995 = self.parse_relation_id()
            xs308.append(_t995)
            cond309 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        relations310 = xs308
        self.consume_literal(')')
        _t996 = transactions_pb2.Context(relations=relations310)
        return _t996

    def parse_epoch_reads(self) -> list[transactions_pb2.Read]:
        self.consume_literal('(')
        self.consume_literal('reads')
        xs311 = []
        cond312 = self.match_lookahead_literal('(', 0)
        while cond312:
            _t997 = self.parse_read()
            xs311.append(_t997)
            cond312 = self.match_lookahead_literal('(', 0)
        x313 = xs311
        self.consume_literal(')')
        return x313

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('what_if', 1):
                _t999 = 2
            else:
                if self.match_lookahead_literal('output', 1):
                    _t1003 = 1
                else:
                    if self.match_lookahead_literal('export', 1):
                        _t1004 = 4
                    else:
                        if self.match_lookahead_literal('demand', 1):
                            _t1005 = 0
                        else:
                            if self.match_lookahead_literal('abort', 1):
                                _t1006 = 3
                            else:
                                _t1006 = -1
                            _t1005 = _t1006
                        _t1004 = _t1005
                    _t1003 = _t1004
                _t999 = _t1003
            _t998 = _t999
        else:
            _t998 = -1
        prediction314 = _t998
        if prediction314 == 4:
            _t1008 = self.parse_export()
            value319 = _t1008
            _t1009 = transactions_pb2.Read(export=value319)
            _t1007 = _t1009
        else:
            if prediction314 == 3:
                _t1011 = self.parse_abort()
                value318 = _t1011
                _t1012 = transactions_pb2.Read(abort=value318)
                _t1010 = _t1012
            else:
                if prediction314 == 2:
                    _t1014 = self.parse_what_if()
                    value317 = _t1014
                    _t1015 = transactions_pb2.Read(what_if=value317)
                    _t1013 = _t1015
                else:
                    if prediction314 == 1:
                        _t1017 = self.parse_output()
                        value316 = _t1017
                        _t1018 = transactions_pb2.Read(output=value316)
                        _t1016 = _t1018
                    else:
                        if prediction314 == 0:
                            _t1020 = self.parse_demand()
                            value315 = _t1020
                            _t1021 = transactions_pb2.Read(demand=value315)
                            _t1019 = _t1021
                        else:
                            raise ParseError(f"{'Unexpected token in read'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t1019 = None
                        _t1016 = _t1019
                    _t1013 = _t1016
                _t1010 = _t1013
            _t1007 = _t1010
        return _t1007

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal('(')
        self.consume_literal('demand')
        _t1022 = self.parse_relation_id()
        relation_id320 = _t1022
        self.consume_literal(')')
        _t1023 = transactions_pb2.Demand(relation_id=relation_id320)
        return _t1023

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal('(')
        self.consume_literal('output')
        if self.match_lookahead_terminal('COLON_SYMBOL', 0):
            _t1025 = self.parse_name()
            _t1024 = _t1025
        else:
            _t1024 = None
        name321 = _t1024
        _t1026 = self.parse_relation_id()
        relation_id322 = _t1026
        self.consume_literal(')')
        _t1027 = transactions_pb2.Output(name=(name321 if name321 is not None else 'output'), relation_id=relation_id322)
        return _t1027

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal('(')
        self.consume_literal('what_if')
        _t1028 = self.parse_name()
        branch323 = _t1028
        _t1029 = self.parse_epoch()
        epoch324 = _t1029
        self.consume_literal(')')
        _t1030 = transactions_pb2.WhatIf(branch=branch323, epoch=epoch324)
        return _t1030

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal('(')
        self.consume_literal('abort')
        if self.match_lookahead_terminal('COLON_SYMBOL', 0):
            _t1032 = self.parse_name()
            _t1031 = _t1032
        else:
            _t1031 = None
        name325 = _t1031
        _t1033 = self.parse_relation_id()
        relation_id326 = _t1033
        self.consume_literal(')')
        _t1034 = transactions_pb2.Abort(name=(name325 if name325 is not None else 'abort'), relation_id=relation_id326)
        return _t1034

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal('(')
        self.consume_literal('export')
        _t1035 = self.parse_export_csv_config()
        config327 = _t1035
        self.consume_literal(')')
        _t1036 = transactions_pb2.Export(csv_config=config327)
        return _t1036

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal('(')
        self.consume_literal('export_csv_config')
        _t1037 = self.parse_export_csv_path()
        path328 = _t1037
        _t1038 = self.parse_export_csv_columns()
        columns329 = _t1038
        _t1039 = self.parse_config_dict()
        config330 = _t1039
        self.consume_literal(')')
        return self.export_csv_config(path328, columns329, config330)

    def parse_export_csv_path(self) -> str:
        self.consume_literal('(')
        self.consume_literal('path')
        x331 = self.consume_terminal('STRING')
        self.consume_literal(')')
        return x331

    def parse_export_csv_columns(self) -> list[transactions_pb2.ExportCSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs332 = []
        cond333 = self.match_lookahead_literal('(', 0)
        while cond333:
            _t1040 = self.parse_export_csv_column()
            xs332.append(_t1040)
            cond333 = self.match_lookahead_literal('(', 0)
        x334 = xs332
        self.consume_literal(')')
        return x334

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        name335 = self.consume_terminal('STRING')
        _t1041 = self.parse_relation_id()
        relation_id336 = _t1041
        self.consume_literal(')')
        _t1042 = transactions_pb2.ExportCSVColumn(column_name=name335, column_data=relation_id336)
        return _t1042


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
