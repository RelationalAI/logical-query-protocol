"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.


Command: python -m meta.cli ../proto/relationalai/lqp/v1/transactions.proto ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/fragments.proto --parser python
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
                _t363 = logic_pb2.Value(missing_value=logic_pb2.MissingValue)
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
        _t382 = self.int64_to_int32(year21)
        _t383 = self.int64_to_int32(month22)
        _t384 = self.int64_to_int32(day23)
        _t385 = logic_pb2.DateValue(year=_t382, month=_t383, day=_t384)
        return _t385

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
            _t386 = self.consume_terminal('INT')
        else:
            _t386 = None
        microsecond30 = _t386
        self.consume_literal(')')
        _t387 = self.int64_to_int32(year24)
        _t388 = self.int64_to_int32(month25)
        _t389 = self.int64_to_int32(day26)
        _t390 = self.int64_to_int32(hour27)
        _t391 = self.int64_to_int32(minute28)
        _t392 = self.int64_to_int32(second29)
        _t393 = self.int64_to_int32((microsecond30 if microsecond30 is not None else 0))
        _t394 = logic_pb2.DateTimeValue(year=_t387, month=_t388, day=_t389, hour=_t390, minute=_t391, second=_t392, microsecond=_t393)
        return _t394

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal('true', 0):
            _t395 = 0
        else:
            _t395 = (self.match_lookahead_literal('false', 0) or -1)
        prediction31 = _t395
        if prediction31 == 1:
            self.consume_literal('false')
            _t396 = False
        else:
            if prediction31 == 0:
                self.consume_literal('true')
                _t397 = True
            else:
                raise ParseError(f"{'Unexpected token in boolean_value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t397 = None
            _t396 = _t397
        return _t396

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal('(')
        self.consume_literal('sync')
        xs32 = []
        cond33 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond33:
            _t398 = self.parse_fragment_id()
            xs32.append(_t398)
            cond33 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        fragments34 = xs32
        self.consume_literal(')')
        _t399 = transactions_pb2.Sync(fragments=fragments34)
        return _t399

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        symbol35 = self.consume_terminal('COLON_SYMBOL')
        return fragments_pb2.FragmentId(id=symbol35.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal('(')
        self.consume_literal('epoch')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('writes', 1)):
            _t401 = self.parse_epoch_writes()
            _t400 = _t401
        else:
            _t400 = None
        writes36 = _t400
        if self.match_lookahead_literal('(', 0):
            _t403 = self.parse_epoch_reads()
            _t402 = _t403
        else:
            _t402 = None
        reads37 = _t402
        self.consume_literal(')')
        _t404 = transactions_pb2.Epoch(writes=(writes36 if writes36 is not None else []), reads=(reads37 if reads37 is not None else []))
        return _t404

    def parse_epoch_writes(self) -> list[transactions_pb2.Write]:
        self.consume_literal('(')
        self.consume_literal('writes')
        xs38 = []
        cond39 = self.match_lookahead_literal('(', 0)
        while cond39:
            _t405 = self.parse_write()
            xs38.append(_t405)
            cond39 = self.match_lookahead_literal('(', 0)
        x40 = xs38
        self.consume_literal(')')
        return x40

    def parse_write(self) -> transactions_pb2.Write:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('undefine', 1):
                _t409 = 1
            else:
                if self.match_lookahead_literal('define', 1):
                    _t410 = 0
                else:
                    if self.match_lookahead_literal('context', 1):
                        _t411 = 2
                    else:
                        _t411 = -1
                    _t410 = _t411
                _t409 = _t410
            _t406 = _t409
        else:
            _t406 = -1
        prediction41 = _t406
        if prediction41 == 2:
            _t413 = self.parse_context()
            value44 = _t413
            _t414 = transactions_pb2.Write(context=value44)
            _t412 = _t414
        else:
            if prediction41 == 1:
                _t416 = self.parse_undefine()
                value43 = _t416
                _t417 = transactions_pb2.Write(undefine=value43)
                _t415 = _t417
            else:
                if prediction41 == 0:
                    _t419 = self.parse_define()
                    value42 = _t419
                    _t420 = transactions_pb2.Write(define=value42)
                    _t418 = _t420
                else:
                    raise ParseError(f"{'Unexpected token in write'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t418 = None
                _t415 = _t418
            _t412 = _t415
        return _t412

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal('(')
        self.consume_literal('define')
        _t421 = self.parse_fragment()
        fragment45 = _t421
        self.consume_literal(')')
        _t422 = transactions_pb2.Define(fragment=fragment45)
        return _t422

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal('(')
        self.consume_literal('fragment')
        _t423 = self.parse_new_fragment_id()
        fragment_id46 = _t423
        xs47 = []
        cond48 = self.match_lookahead_literal('(', 0)
        while cond48:
            _t424 = self.parse_declaration()
            xs47.append(_t424)
            cond48 = self.match_lookahead_literal('(', 0)
        declarations49 = xs47
        self.consume_literal(')')
        return self.construct_fragment(fragment_id46, declarations49)

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        _t425 = self.parse_fragment_id()
        fragment_id50 = _t425
        self.start_fragment(fragment_id50)
        return fragment_id50

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('rel_edb', 1):
                _t427 = 3
            else:
                if self.match_lookahead_literal('functional_dependency', 1):
                    _t428 = 2
                else:
                    if self.match_lookahead_literal('def', 1):
                        _t429 = 0
                    else:
                        if self.match_lookahead_literal('csvdata', 1):
                            _t430 = 3
                        else:
                            if self.match_lookahead_literal('be_tree_relation', 1):
                                _t431 = 3
                            else:
                                _t431 = (self.match_lookahead_literal('algorithm', 1) or -1)
                            _t430 = _t431
                        _t429 = _t430
                    _t428 = _t429
                _t427 = _t428
            _t426 = _t427
        else:
            _t426 = -1
        prediction51 = _t426
        if prediction51 == 3:
            _t433 = self.parse_data()
            value55 = _t433
            _t434 = logic_pb2.Declaration(data=value55)
            _t432 = _t434
        else:
            if prediction51 == 2:
                _t436 = self.parse_constraint()
                value54 = _t436
                _t437 = logic_pb2.Declaration(constraint=value54)
                _t435 = _t437
            else:
                if prediction51 == 1:
                    _t439 = self.parse_algorithm()
                    value53 = _t439
                    _t440 = logic_pb2.Declaration(algorithm=value53)
                    _t438 = _t440
                else:
                    if prediction51 == 0:
                        _t442 = self.parse_def()
                        value52 = _t442
                        _t443 = logic_pb2.Declaration()
                        getattr(_t443, 'def').CopyFrom(value52)
                        _t441 = _t443
                    else:
                        raise ParseError(f"{'Unexpected token in declaration'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t441 = None
                    _t438 = _t441
                _t435 = _t438
            _t432 = _t435
        return _t432

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal('(')
        self.consume_literal('def')
        _t444 = self.parse_relation_id()
        name56 = _t444
        _t445 = self.parse_abstraction()
        body57 = _t445
        if self.match_lookahead_literal('(', 0):
            _t447 = self.parse_attrs()
            _t446 = _t447
        else:
            _t446 = None
        attrs58 = _t446
        self.consume_literal(')')
        _t448 = logic_pb2.Def(name=name56, body=body57, attrs=(attrs58 if attrs58 is not None else []))
        return _t448

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_terminal('INT', 0):
            _t450 = 1
        else:
            if self.match_lookahead_terminal('COLON_SYMBOL', 0):
                _t451 = 0
            else:
                _t451 = -1
            _t450 = _t451
        prediction59 = _t450
        if prediction59 == 1:
            INT61 = self.consume_terminal('INT')
            _t452 = logic_pb2.RelationId(id_low=INT61 & 0xFFFFFFFFFFFFFFFF, id_high=(INT61 >> 64) & 0xFFFFFFFFFFFFFFFF)
        else:
            if prediction59 == 0:
                symbol60 = self.consume_terminal('COLON_SYMBOL')
                _t453 = self.relation_id_from_string(symbol60)
            else:
                raise ParseError(f"{'Unexpected token in relation_id'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t453 = None
            _t452 = _t453
        return _t452

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal('(')
        _t454 = self.parse_bindings()
        bindings62 = _t454
        _t455 = self.parse_formula()
        formula63 = _t455
        self.consume_literal(')')
        _t456 = logic_pb2.Abstraction(vars=(bindings62[0] + (bindings62[1] if bindings62[1] is not None else [])), value=formula63)
        return _t456

    def parse_bindings(self) -> tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]:
        self.consume_literal('[')
        xs64 = []
        cond65 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond65:
            _t457 = self.parse_binding()
            xs64.append(_t457)
            cond65 = self.match_lookahead_terminal('SYMBOL', 0)
        keys66 = xs64
        if self.match_lookahead_literal('|', 0):
            _t459 = self.parse_value_bindings()
            _t458 = _t459
        else:
            _t458 = None
        values67 = _t458
        self.consume_literal(']')
        return (keys66, (values67 if values67 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol68 = self.consume_terminal('SYMBOL')
        self.consume_literal('::')
        _t460 = self.parse_type()
        type69 = _t460
        _t461 = logic_pb2.Var(name=symbol68)
        _t462 = logic_pb2.Binding(var=_t461, type=type69)
        return _t462

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal('UNKNOWN', 0):
            _t463 = 0
        else:
            if self.match_lookahead_literal('UINT128', 0):
                _t464 = 4
            else:
                if self.match_lookahead_literal('STRING', 0):
                    _t473 = 1
                else:
                    if self.match_lookahead_literal('MISSING', 0):
                        _t474 = 8
                    else:
                        if self.match_lookahead_literal('INT128', 0):
                            _t475 = 5
                        else:
                            if self.match_lookahead_literal('INT', 0):
                                _t476 = 2
                            else:
                                if self.match_lookahead_literal('FLOAT', 0):
                                    _t477 = 3
                                else:
                                    if self.match_lookahead_literal('DATETIME', 0):
                                        _t478 = 7
                                    else:
                                        if self.match_lookahead_literal('DATE', 0):
                                            _t479 = 6
                                        else:
                                            if self.match_lookahead_literal('BOOLEAN', 0):
                                                _t480 = 10
                                            else:
                                                if self.match_lookahead_literal('(', 0):
                                                    _t481 = 9
                                                else:
                                                    _t481 = -1
                                                _t480 = _t481
                                            _t479 = _t480
                                        _t478 = _t479
                                    _t477 = _t478
                                _t476 = _t477
                            _t475 = _t476
                        _t474 = _t475
                    _t473 = _t474
                _t464 = _t473
            _t463 = _t464
        prediction70 = _t463
        if prediction70 == 10:
            _t483 = self.parse_boolean_type()
            value81 = _t483
            _t484 = logic_pb2.Type(boolean_type=value81)
            _t482 = _t484
        else:
            if prediction70 == 9:
                _t486 = self.parse_decimal_type()
                value80 = _t486
                _t487 = logic_pb2.Type(decimal_type=value80)
                _t485 = _t487
            else:
                if prediction70 == 8:
                    _t489 = self.parse_missing_type()
                    value79 = _t489
                    _t490 = logic_pb2.Type(missing_type=value79)
                    _t488 = _t490
                else:
                    if prediction70 == 7:
                        _t492 = self.parse_datetime_type()
                        value78 = _t492
                        _t493 = logic_pb2.Type(datetime_type=value78)
                        _t491 = _t493
                    else:
                        if prediction70 == 6:
                            _t495 = self.parse_date_type()
                            value77 = _t495
                            _t496 = logic_pb2.Type(date_type=value77)
                            _t494 = _t496
                        else:
                            if prediction70 == 5:
                                _t498 = self.parse_int128_type()
                                value76 = _t498
                                _t499 = logic_pb2.Type(int128_type=value76)
                                _t497 = _t499
                            else:
                                if prediction70 == 4:
                                    _t501 = self.parse_uint128_type()
                                    value75 = _t501
                                    _t502 = logic_pb2.Type(uint128_type=value75)
                                    _t500 = _t502
                                else:
                                    if prediction70 == 3:
                                        _t504 = self.parse_float_type()
                                        value74 = _t504
                                        _t505 = logic_pb2.Type(float_type=value74)
                                        _t503 = _t505
                                    else:
                                        if prediction70 == 2:
                                            _t507 = self.parse_int_type()
                                            value73 = _t507
                                            _t508 = logic_pb2.Type(int_type=value73)
                                            _t506 = _t508
                                        else:
                                            if prediction70 == 1:
                                                _t510 = self.parse_string_type()
                                                value72 = _t510
                                                _t511 = logic_pb2.Type(string_type=value72)
                                                _t509 = _t511
                                            else:
                                                if prediction70 == 0:
                                                    _t513 = self.parse_unspecified_type()
                                                    value71 = _t513
                                                    _t514 = logic_pb2.Type(unspecified_type=value71)
                                                    _t512 = _t514
                                                else:
                                                    raise ParseError(f"{'Unexpected token in type'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                    _t512 = None
                                                _t509 = _t512
                                            _t506 = _t509
                                        _t503 = _t506
                                    _t500 = _t503
                                _t497 = _t500
                            _t494 = _t497
                        _t491 = _t494
                    _t488 = _t491
                _t485 = _t488
            _t482 = _t485
        return _t482

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        self.consume_literal('UNKNOWN')
        return logic_pb2.UnspecifiedType

    def parse_string_type(self) -> logic_pb2.StringType:
        self.consume_literal('STRING')
        return logic_pb2.StringType

    def parse_int_type(self) -> logic_pb2.IntType:
        self.consume_literal('INT')
        return logic_pb2.IntType

    def parse_float_type(self) -> logic_pb2.FloatType:
        self.consume_literal('FLOAT')
        return logic_pb2.FloatType

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        self.consume_literal('UINT128')
        return logic_pb2.UInt128Type

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        self.consume_literal('INT128')
        return logic_pb2.Int128Type

    def parse_date_type(self) -> logic_pb2.DateType:
        self.consume_literal('DATE')
        return logic_pb2.DateType

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        self.consume_literal('DATETIME')
        return logic_pb2.DateTimeType

    def parse_missing_type(self) -> logic_pb2.MissingType:
        self.consume_literal('MISSING')
        return logic_pb2.MissingType

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        self.consume_literal('(')
        self.consume_literal('DECIMAL')
        precision82 = self.consume_terminal('INT')
        scale83 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t515 = self.int64_to_int32(precision82)
        _t516 = self.int64_to_int32(scale83)
        _t517 = logic_pb2.DecimalType(precision=_t515, scale=_t516)
        return _t517

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal('BOOLEAN')
        return logic_pb2.BooleanType

    def parse_value_bindings(self) -> list[logic_pb2.Binding]:
        self.consume_literal('|')
        xs84 = []
        cond85 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond85:
            _t518 = self.parse_binding()
            xs84.append(_t518)
            cond85 = self.match_lookahead_terminal('SYMBOL', 0)
        x86 = xs84
        return x86

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('true', 1):
                _t520 = 0
            else:
                if self.match_lookahead_literal('rel_atom', 1):
                    _t521 = 11
                else:
                    if self.match_lookahead_literal('reduce', 1):
                        _t522 = 3
                    else:
                        if self.match_lookahead_literal('primitive', 1):
                            _t523 = 10
                        else:
                            if self.match_lookahead_literal('pragma', 1):
                                _t524 = 9
                            else:
                                if self.match_lookahead_literal('or', 1):
                                    _t525 = 5
                                else:
                                    if self.match_lookahead_literal('not', 1):
                                        _t526 = 6
                                    else:
                                        if self.match_lookahead_literal('ffi', 1):
                                            _t527 = 7
                                        else:
                                            if self.match_lookahead_literal('false', 1):
                                                _t541 = 1
                                            else:
                                                if self.match_lookahead_literal('exists', 1):
                                                    _t542 = 2
                                                else:
                                                    if self.match_lookahead_literal('cast', 1):
                                                        _t543 = 12
                                                    else:
                                                        if self.match_lookahead_literal('atom', 1):
                                                            _t544 = 8
                                                        else:
                                                            if self.match_lookahead_literal('and', 1):
                                                                _t545 = 4
                                                            else:
                                                                if self.match_lookahead_literal('>=', 1):
                                                                    _t546 = 10
                                                                else:
                                                                    if self.match_lookahead_literal('>', 1):
                                                                        _t547 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal('=', 1):
                                                                            _t548 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal('<=', 1):
                                                                                _t549 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal('<', 1):
                                                                                    _t550 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal('/', 1):
                                                                                        _t551 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal('-', 1):
                                                                                            _t552 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal('+', 1):
                                                                                                _t553 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal('*', 1):
                                                                                                    _t554 = 10
                                                                                                else:
                                                                                                    _t554 = -1
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
                                            _t527 = _t541
                                        _t526 = _t527
                                    _t525 = _t526
                                _t524 = _t525
                            _t523 = _t524
                        _t522 = _t523
                    _t521 = _t522
                _t520 = _t521
            _t519 = _t520
        else:
            _t519 = -1
        prediction87 = _t519
        if prediction87 == 12:
            _t556 = self.parse_cast()
            value100 = _t556
            _t557 = logic_pb2.Formula(cast=value100)
            _t555 = _t557
        else:
            if prediction87 == 11:
                _t559 = self.parse_rel_atom()
                value99 = _t559
                _t560 = logic_pb2.Formula(rel_atom=value99)
                _t558 = _t560
            else:
                if prediction87 == 10:
                    _t562 = self.parse_primitive()
                    value98 = _t562
                    _t563 = logic_pb2.Formula(primitive=value98)
                    _t561 = _t563
                else:
                    if prediction87 == 9:
                        _t565 = self.parse_pragma()
                        value97 = _t565
                        _t566 = logic_pb2.Formula(pragma=value97)
                        _t564 = _t566
                    else:
                        if prediction87 == 8:
                            _t568 = self.parse_atom()
                            value96 = _t568
                            _t569 = logic_pb2.Formula(atom=value96)
                            _t567 = _t569
                        else:
                            if prediction87 == 7:
                                _t571 = self.parse_ffi()
                                value95 = _t571
                                _t572 = logic_pb2.Formula(ffi=value95)
                                _t570 = _t572
                            else:
                                if prediction87 == 6:
                                    _t574 = self.parse_not()
                                    value94 = _t574
                                    _t575 = logic_pb2.Formula()
                                    getattr(_t575, 'not').CopyFrom(value94)
                                    _t573 = _t575
                                else:
                                    if prediction87 == 5:
                                        _t577 = self.parse_disjunction()
                                        value93 = _t577
                                        _t578 = logic_pb2.Formula(disjunction=value93)
                                        _t576 = _t578
                                    else:
                                        if prediction87 == 4:
                                            _t580 = self.parse_conjunction()
                                            value92 = _t580
                                            _t581 = logic_pb2.Formula(conjunction=value92)
                                            _t579 = _t581
                                        else:
                                            if prediction87 == 3:
                                                _t583 = self.parse_reduce()
                                                value91 = _t583
                                                _t584 = logic_pb2.Formula(reduce=value91)
                                                _t582 = _t584
                                            else:
                                                if prediction87 == 2:
                                                    _t586 = self.parse_exists()
                                                    value90 = _t586
                                                    _t587 = logic_pb2.Formula(exists=value90)
                                                    _t585 = _t587
                                                else:
                                                    if prediction87 == 1:
                                                        _t589 = self.parse_false()
                                                        value89 = _t589
                                                        _t590 = logic_pb2.Formula(disjunction=value89)
                                                        _t588 = _t590
                                                    else:
                                                        if prediction87 == 0:
                                                            _t592 = self.parse_true()
                                                            value88 = _t592
                                                            _t593 = logic_pb2.Formula(conjunction=value88)
                                                            _t591 = _t593
                                                        else:
                                                            raise ParseError(f"{'Unexpected token in formula'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t591 = None
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
            _t555 = _t558
        return _t555

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('true')
        self.consume_literal(')')
        _t594 = logic_pb2.Conjunction(args=[])
        return _t594

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('false')
        self.consume_literal(')')
        _t595 = logic_pb2.Disjunction(args=[])
        return _t595

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal('(')
        self.consume_literal('exists')
        _t596 = self.parse_bindings()
        bindings101 = _t596
        _t597 = self.parse_formula()
        formula102 = _t597
        self.consume_literal(')')
        _t598 = logic_pb2.Abstraction(vars=(bindings101[0] + (bindings101[1] if bindings101[1] is not None else [])), value=formula102)
        _t599 = logic_pb2.Exists(body=_t598)
        return _t599

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal('(')
        self.consume_literal('reduce')
        _t600 = self.parse_abstraction()
        op103 = _t600
        _t601 = self.parse_abstraction()
        body104 = _t601
        _t602 = self.parse_terms()
        terms105 = _t602
        self.consume_literal(')')
        _t603 = logic_pb2.Reduce(op=op103, body=body104, terms=terms105)
        return _t603

    def parse_terms(self) -> list[logic_pb2.Term]:
        self.consume_literal('(')
        self.consume_literal('terms')
        xs106 = []
        cond107 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond107:
            _t604 = self.parse_term()
            xs106.append(_t604)
            cond107 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        x108 = xs106
        self.consume_literal(')')
        return x108

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_literal('true', 0):
            _t636 = 1
        else:
            if self.match_lookahead_literal('missing', 0):
                _t652 = 1
            else:
                if self.match_lookahead_literal('false', 0):
                    _t660 = 1
                else:
                    if self.match_lookahead_literal('(', 0):
                        _t664 = 1
                    else:
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t666 = 1
                        else:
                            if self.match_lookahead_terminal('SYMBOL', 0):
                                _t667 = 0
                            else:
                                _t667 = (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or -1)))))
                            _t666 = _t667
                        _t664 = _t666
                    _t660 = _t664
                _t652 = _t660
            _t636 = _t652
        prediction109 = _t636
        if prediction109 == 1:
            _t669 = self.parse_constant()
            value111 = _t669
            _t670 = logic_pb2.Term(constant=value111)
            _t668 = _t670
        else:
            if prediction109 == 0:
                _t672 = self.parse_var()
                value110 = _t672
                _t673 = logic_pb2.Term(var=value110)
                _t671 = _t673
            else:
                raise ParseError(f"{'Unexpected token in term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t671 = None
            _t668 = _t671
        return _t668

    def parse_var(self) -> logic_pb2.Var:
        symbol112 = self.consume_terminal('SYMBOL')
        _t674 = logic_pb2.Var(name=symbol112)
        return _t674

    def parse_constant(self) -> logic_pb2.Value:
        _t675 = self.parse_value()
        x113 = _t675
        return x113

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('and')
        xs114 = []
        cond115 = self.match_lookahead_literal('(', 0)
        while cond115:
            _t676 = self.parse_formula()
            xs114.append(_t676)
            cond115 = self.match_lookahead_literal('(', 0)
        args116 = xs114
        self.consume_literal(')')
        _t677 = logic_pb2.Conjunction(args=args116)
        return _t677

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('or')
        xs117 = []
        cond118 = self.match_lookahead_literal('(', 0)
        while cond118:
            _t678 = self.parse_formula()
            xs117.append(_t678)
            cond118 = self.match_lookahead_literal('(', 0)
        args119 = xs117
        self.consume_literal(')')
        _t679 = logic_pb2.Disjunction(args=args119)
        return _t679

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal('(')
        self.consume_literal('not')
        _t680 = self.parse_formula()
        arg120 = _t680
        self.consume_literal(')')
        _t681 = logic_pb2.Not(arg=arg120)
        return _t681

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal('(')
        self.consume_literal('ffi')
        _t682 = self.parse_name()
        name121 = _t682
        _t683 = self.parse_ffi_args()
        args122 = _t683
        _t684 = self.parse_terms()
        terms123 = _t684
        self.consume_literal(')')
        _t685 = logic_pb2.FFI(name=name121, args=args122, terms=terms123)
        return _t685

    def parse_name(self) -> str:
        x124 = self.consume_terminal('COLON_SYMBOL')
        return x124

    def parse_ffi_args(self) -> list[logic_pb2.Abstraction]:
        self.consume_literal('(')
        self.consume_literal('args')
        xs125 = []
        cond126 = self.match_lookahead_literal('(', 0)
        while cond126:
            _t686 = self.parse_abstraction()
            xs125.append(_t686)
            cond126 = self.match_lookahead_literal('(', 0)
        x127 = xs125
        self.consume_literal(')')
        return x127

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal('(')
        self.consume_literal('atom')
        _t687 = self.parse_relation_id()
        name128 = _t687
        xs129 = []
        cond130 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond130:
            _t688 = self.parse_term()
            xs129.append(_t688)
            cond130 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms131 = xs129
        self.consume_literal(')')
        _t689 = logic_pb2.Atom(name=name128, terms=terms131)
        return _t689

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal('(')
        self.consume_literal('pragma')
        _t690 = self.parse_name()
        name132 = _t690
        xs133 = []
        cond134 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond134:
            _t691 = self.parse_term()
            xs133.append(_t691)
            cond134 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms135 = xs133
        self.consume_literal(')')
        _t692 = logic_pb2.Pragma(name=name132, terms=terms135)
        return _t692

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('primitive', 1):
                _t694 = 9
            else:
                if self.match_lookahead_literal('>=', 1):
                    _t695 = 4
                else:
                    if self.match_lookahead_literal('>', 1):
                        _t696 = 3
                    else:
                        if self.match_lookahead_literal('=', 1):
                            _t697 = 0
                        else:
                            if self.match_lookahead_literal('<=', 1):
                                _t698 = 2
                            else:
                                if self.match_lookahead_literal('<', 1):
                                    _t703 = 1
                                else:
                                    if self.match_lookahead_literal('/', 1):
                                        _t704 = 8
                                    else:
                                        if self.match_lookahead_literal('-', 1):
                                            _t705 = 6
                                        else:
                                            if self.match_lookahead_literal('+', 1):
                                                _t706 = 5
                                            else:
                                                if self.match_lookahead_literal('*', 1):
                                                    _t707 = 7
                                                else:
                                                    _t707 = -1
                                                _t706 = _t707
                                            _t705 = _t706
                                        _t704 = _t705
                                    _t703 = _t704
                                _t698 = _t703
                            _t697 = _t698
                        _t696 = _t697
                    _t695 = _t696
                _t694 = _t695
            _t693 = _t694
        else:
            _t693 = -1
        prediction136 = _t693
        if prediction136 == 9:
            self.consume_literal('(')
            self.consume_literal('primitive')
            _t709 = self.parse_name()
            name146 = _t709
            xs147 = []
            cond148 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            while cond148:
                _t710 = self.parse_rel_term()
                xs147.append(_t710)
                cond148 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            terms149 = xs147
            self.consume_literal(')')
            _t711 = logic_pb2.Primitive(name=name146, terms=terms149)
            _t708 = _t711
        else:
            if prediction136 == 8:
                _t713 = self.parse_divide()
                op145 = _t713
                _t712 = op145
            else:
                if prediction136 == 7:
                    _t715 = self.parse_multiply()
                    op144 = _t715
                    _t714 = op144
                else:
                    if prediction136 == 6:
                        _t717 = self.parse_minus()
                        op143 = _t717
                        _t716 = op143
                    else:
                        if prediction136 == 5:
                            _t719 = self.parse_add()
                            op142 = _t719
                            _t718 = op142
                        else:
                            if prediction136 == 4:
                                _t721 = self.parse_gt_eq()
                                op141 = _t721
                                _t720 = op141
                            else:
                                if prediction136 == 3:
                                    _t723 = self.parse_gt()
                                    op140 = _t723
                                    _t722 = op140
                                else:
                                    if prediction136 == 2:
                                        _t725 = self.parse_lt_eq()
                                        op139 = _t725
                                        _t724 = op139
                                    else:
                                        if prediction136 == 1:
                                            _t727 = self.parse_lt()
                                            op138 = _t727
                                            _t726 = op138
                                        else:
                                            if prediction136 == 0:
                                                _t729 = self.parse_eq()
                                                op137 = _t729
                                                _t728 = op137
                                            else:
                                                raise ParseError(f"{'Unexpected token in primitive'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t728 = None
                                            _t726 = _t728
                                        _t724 = _t726
                                    _t722 = _t724
                                _t720 = _t722
                            _t718 = _t720
                        _t716 = _t718
                    _t714 = _t716
                _t712 = _t714
            _t708 = _t712
        return _t708

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('=')
        _t730 = self.parse_term()
        left150 = _t730
        _t731 = self.parse_term()
        right151 = _t731
        self.consume_literal(')')
        _t732 = logic_pb2.RelTerm(term=left150)
        _t733 = logic_pb2.RelTerm(term=right151)
        _t734 = logic_pb2.Primitive(name='rel_primitive_eq', terms=[_t732, _t733])
        return _t734

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<')
        _t735 = self.parse_term()
        left152 = _t735
        _t736 = self.parse_term()
        right153 = _t736
        self.consume_literal(')')
        _t737 = logic_pb2.RelTerm(term=left152)
        _t738 = logic_pb2.RelTerm(term=right153)
        _t739 = logic_pb2.Primitive(name='rel_primitive_lt_monotype', terms=[_t737, _t738])
        return _t739

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<=')
        _t740 = self.parse_term()
        left154 = _t740
        _t741 = self.parse_term()
        right155 = _t741
        self.consume_literal(')')
        _t742 = logic_pb2.RelTerm(term=left154)
        _t743 = logic_pb2.RelTerm(term=right155)
        _t744 = logic_pb2.Primitive(name='rel_primitive_lt_eq_monotype', terms=[_t742, _t743])
        return _t744

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>')
        _t745 = self.parse_term()
        left156 = _t745
        _t746 = self.parse_term()
        right157 = _t746
        self.consume_literal(')')
        _t747 = logic_pb2.RelTerm(term=left156)
        _t748 = logic_pb2.RelTerm(term=right157)
        _t749 = logic_pb2.Primitive(name='rel_primitive_gt_monotype', terms=[_t747, _t748])
        return _t749

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>=')
        _t750 = self.parse_term()
        left158 = _t750
        _t751 = self.parse_term()
        right159 = _t751
        self.consume_literal(')')
        _t752 = logic_pb2.RelTerm(term=left158)
        _t753 = logic_pb2.RelTerm(term=right159)
        _t754 = logic_pb2.Primitive(name='rel_primitive_gt_eq_monotype', terms=[_t752, _t753])
        return _t754

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('+')
        _t755 = self.parse_term()
        left160 = _t755
        _t756 = self.parse_term()
        right161 = _t756
        _t757 = self.parse_term()
        result162 = _t757
        self.consume_literal(')')
        _t758 = logic_pb2.RelTerm(term=left160)
        _t759 = logic_pb2.RelTerm(term=right161)
        _t760 = logic_pb2.RelTerm(term=result162)
        _t761 = logic_pb2.Primitive(name='rel_primitive_add_monotype', terms=[_t758, _t759, _t760])
        return _t761

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('-')
        _t762 = self.parse_term()
        left163 = _t762
        _t763 = self.parse_term()
        right164 = _t763
        _t764 = self.parse_term()
        result165 = _t764
        self.consume_literal(')')
        _t765 = logic_pb2.RelTerm(term=left163)
        _t766 = logic_pb2.RelTerm(term=right164)
        _t767 = logic_pb2.RelTerm(term=result165)
        _t768 = logic_pb2.Primitive(name='rel_primitive_subtract_monotype', terms=[_t765, _t766, _t767])
        return _t768

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('*')
        _t769 = self.parse_term()
        left166 = _t769
        _t770 = self.parse_term()
        right167 = _t770
        _t771 = self.parse_term()
        result168 = _t771
        self.consume_literal(')')
        _t772 = logic_pb2.RelTerm(term=left166)
        _t773 = logic_pb2.RelTerm(term=right167)
        _t774 = logic_pb2.RelTerm(term=result168)
        _t775 = logic_pb2.Primitive(name='rel_primitive_multiply_monotype', terms=[_t772, _t773, _t774])
        return _t775

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('/')
        _t776 = self.parse_term()
        left169 = _t776
        _t777 = self.parse_term()
        right170 = _t777
        _t778 = self.parse_term()
        result171 = _t778
        self.consume_literal(')')
        _t779 = logic_pb2.RelTerm(term=left169)
        _t780 = logic_pb2.RelTerm(term=right170)
        _t781 = logic_pb2.RelTerm(term=result171)
        _t782 = logic_pb2.Primitive(name='rel_primitive_divide_monotype', terms=[_t779, _t780, _t781])
        return _t782

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_literal('true', 0):
            _t798 = 1
        else:
            if self.match_lookahead_literal('missing', 0):
                _t806 = 1
            else:
                if self.match_lookahead_literal('false', 0):
                    _t810 = 1
                else:
                    if self.match_lookahead_literal('(', 0):
                        _t812 = 1
                    else:
                        if self.match_lookahead_literal('#', 0):
                            _t813 = 0
                        else:
                            _t813 = (self.match_lookahead_terminal('UINT128', 0) or (self.match_lookahead_terminal('SYMBOL', 0) or (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or -1)))))))
                        _t812 = _t813
                    _t810 = _t812
                _t806 = _t810
            _t798 = _t806
        prediction172 = _t798
        if prediction172 == 1:
            _t815 = self.parse_term()
            value174 = _t815
            _t816 = logic_pb2.RelTerm(term=value174)
            _t814 = _t816
        else:
            if prediction172 == 0:
                _t818 = self.parse_specialized_value()
                value173 = _t818
                _t819 = logic_pb2.RelTerm(specialized_value=value173)
                _t817 = _t819
            else:
                raise ParseError(f"{'Unexpected token in rel_term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t817 = None
            _t814 = _t817
        return _t814

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal('#')
        _t820 = self.parse_value()
        value175 = _t820
        return value175

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        self.consume_literal('(')
        self.consume_literal('rel_atom')
        _t821 = self.parse_name()
        name176 = _t821
        xs177 = []
        cond178 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond178:
            _t822 = self.parse_rel_term()
            xs177.append(_t822)
            cond178 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms179 = xs177
        self.consume_literal(')')
        _t823 = logic_pb2.RelAtom(name=name176, terms=terms179)
        return _t823

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal('(')
        self.consume_literal('cast')
        _t824 = self.parse_term()
        input180 = _t824
        _t825 = self.parse_term()
        result181 = _t825
        self.consume_literal(')')
        _t826 = logic_pb2.Cast(input=input180, result=result181)
        return _t826

    def parse_attrs(self) -> list[logic_pb2.Attribute]:
        self.consume_literal('(')
        self.consume_literal('attrs')
        xs182 = []
        cond183 = self.match_lookahead_literal('(', 0)
        while cond183:
            _t827 = self.parse_attribute()
            xs182.append(_t827)
            cond183 = self.match_lookahead_literal('(', 0)
        x184 = xs182
        self.consume_literal(')')
        return x184

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal('(')
        self.consume_literal('attribute')
        _t828 = self.parse_name()
        name185 = _t828
        xs186 = []
        cond187 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond187:
            _t829 = self.parse_value()
            xs186.append(_t829)
            cond187 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        args188 = xs186
        self.consume_literal(')')
        _t830 = logic_pb2.Attribute(name=name185, args=args188)
        return _t830

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal('(')
        self.consume_literal('algorithm')
        xs189 = []
        cond190 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        while cond190:
            _t831 = self.parse_relation_id()
            xs189.append(_t831)
            cond190 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        global191 = xs189
        _t832 = self.parse_script()
        body192 = _t832
        self.consume_literal(')')
        _t833 = logic_pb2.Algorithm(body=body192)
        getattr(_t833, 'global').CopyFrom(global191)
        return _t833

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal('(')
        self.consume_literal('script')
        xs193 = []
        cond194 = self.match_lookahead_literal('(', 0)
        while cond194:
            _t834 = self.parse_construct()
            xs193.append(_t834)
            cond194 = self.match_lookahead_literal('(', 0)
        constructs195 = xs193
        self.consume_literal(')')
        _t835 = logic_pb2.Script(constructs=constructs195)
        return _t835

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t844 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t848 = 1
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t850 = 1
                    else:
                        if self.match_lookahead_literal('loop', 1):
                            _t851 = 0
                        else:
                            _t851 = (self.match_lookahead_literal('break', 1) or (self.match_lookahead_literal('assign', 1) or -1))
                        _t850 = _t851
                    _t848 = _t850
                _t844 = _t848
            _t836 = _t844
        else:
            _t836 = -1
        prediction196 = _t836
        if prediction196 == 1:
            _t853 = self.parse_instruction()
            value198 = _t853
            _t854 = logic_pb2.Construct(instruction=value198)
            _t852 = _t854
        else:
            if prediction196 == 0:
                _t856 = self.parse_loop()
                value197 = _t856
                _t857 = logic_pb2.Construct(loop=value197)
                _t855 = _t857
            else:
                raise ParseError(f"{'Unexpected token in construct'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t855 = None
            _t852 = _t855
        return _t852

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal('(')
        self.consume_literal('loop')
        _t858 = self.parse_init()
        init199 = _t858
        _t859 = self.parse_script()
        body200 = _t859
        self.consume_literal(')')
        _t860 = logic_pb2.Loop(init=init199, body=body200)
        return _t860

    def parse_init(self) -> list[logic_pb2.Instruction]:
        self.consume_literal('(')
        self.consume_literal('init')
        xs201 = []
        cond202 = self.match_lookahead_literal('(', 0)
        while cond202:
            _t861 = self.parse_instruction()
            xs201.append(_t861)
            cond202 = self.match_lookahead_literal('(', 0)
        x203 = xs201
        self.consume_literal(')')
        return x203

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t867 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t868 = 4
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t869 = 3
                    else:
                        if self.match_lookahead_literal('break', 1):
                            _t870 = 2
                        else:
                            if self.match_lookahead_literal('assign', 1):
                                _t871 = 0
                            else:
                                _t871 = -1
                            _t870 = _t871
                        _t869 = _t870
                    _t868 = _t869
                _t867 = _t868
            _t862 = _t867
        else:
            _t862 = -1
        prediction204 = _t862
        if prediction204 == 4:
            _t873 = self.parse_monus_def()
            value209 = _t873
            _t874 = logic_pb2.Instruction(monus_def=value209)
            _t872 = _t874
        else:
            if prediction204 == 3:
                _t876 = self.parse_monoid_def()
                value208 = _t876
                _t877 = logic_pb2.Instruction(monoid_def=value208)
                _t875 = _t877
            else:
                if prediction204 == 2:
                    _t879 = self.parse_break()
                    value207 = _t879
                    _t880 = logic_pb2.Instruction()
                    getattr(_t880, 'break').CopyFrom(value207)
                    _t878 = _t880
                else:
                    if prediction204 == 1:
                        _t882 = self.parse_upsert()
                        value206 = _t882
                        _t883 = logic_pb2.Instruction(upsert=value206)
                        _t881 = _t883
                    else:
                        if prediction204 == 0:
                            _t885 = self.parse_assign()
                            value205 = _t885
                            _t886 = logic_pb2.Instruction(assign=value205)
                            _t884 = _t886
                        else:
                            raise ParseError(f"{'Unexpected token in instruction'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t884 = None
                        _t881 = _t884
                    _t878 = _t881
                _t875 = _t878
            _t872 = _t875
        return _t872

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal('(')
        self.consume_literal('assign')
        _t887 = self.parse_relation_id()
        name210 = _t887
        _t888 = self.parse_abstraction()
        body211 = _t888
        if self.match_lookahead_literal('(', 0):
            _t890 = self.parse_attrs()
            _t889 = _t890
        else:
            _t889 = None
        attrs212 = _t889
        self.consume_literal(')')
        _t891 = logic_pb2.Assign(name=name210, body=body211, attrs=(attrs212 if attrs212 is not None else []))
        return _t891

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal('(')
        self.consume_literal('upsert')
        _t892 = self.parse_relation_id()
        name213 = _t892
        _t893 = self.parse_abstraction_with_arity()
        abstraction_with_arity214 = _t893
        if self.match_lookahead_literal('(', 0):
            _t895 = self.parse_attrs()
            _t894 = _t895
        else:
            _t894 = None
        attrs215 = _t894
        self.consume_literal(')')
        abstraction = abstraction_with_arity214[0]
        arity = abstraction_with_arity214[1]
        _t896 = logic_pb2.Upsert(name=name213, body=abstraction, attrs=(attrs215 if attrs215 is not None else []), value_arity=arity)
        return _t896

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal('(')
        _t897 = self.parse_bindings()
        bindings216 = _t897
        _t898 = self.parse_formula()
        formula217 = _t898
        self.consume_literal(')')
        _t899 = logic_pb2.Abstraction(vars=(bindings216[0] + (bindings216[1] if bindings216[1] is not None else [])), value=formula217)
        return (_t899, len(bindings216[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal('(')
        self.consume_literal('break')
        _t900 = self.parse_relation_id()
        name218 = _t900
        _t901 = self.parse_abstraction()
        body219 = _t901
        if self.match_lookahead_literal('(', 0):
            _t903 = self.parse_attrs()
            _t902 = _t903
        else:
            _t902 = None
        attrs220 = _t902
        self.consume_literal(')')
        _t904 = logic_pb2.Break(name=name218, body=body219, attrs=(attrs220 if attrs220 is not None else []))
        return _t904

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal('(')
        self.consume_literal('monoid')
        _t905 = self.parse_monoid()
        monoid221 = _t905
        _t906 = self.parse_relation_id()
        name222 = _t906
        _t907 = self.parse_abstraction_with_arity()
        abstraction_with_arity223 = _t907
        if self.match_lookahead_literal('(', 0):
            _t909 = self.parse_attrs()
            _t908 = _t909
        else:
            _t908 = None
        attrs224 = _t908
        self.consume_literal(')')
        abstraction = abstraction_with_arity223[0]
        arity = abstraction_with_arity223[1]
        _t910 = logic_pb2.MonoidDef(monoid=monoid221, name=name222, body=abstraction, attrs=(attrs224 if attrs224 is not None else []), value_arity=arity)
        return _t910

    def parse_monoid(self) -> logic_pb2.Monoid:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('sum', 1):
                _t912 = 3
            else:
                if self.match_lookahead_literal('or', 1):
                    _t913 = 0
                else:
                    if self.match_lookahead_literal('min', 1):
                        _t915 = 1
                    else:
                        if self.match_lookahead_literal('max', 1):
                            _t916 = 2
                        else:
                            _t916 = -1
                        _t915 = _t916
                    _t913 = _t915
                _t912 = _t913
            _t911 = _t912
        else:
            _t911 = -1
        prediction225 = _t911
        if prediction225 == 3:
            _t918 = self.parse_sum_monoid()
            value229 = _t918
            _t919 = logic_pb2.Monoid(sum_monoid=value229)
            _t917 = _t919
        else:
            if prediction225 == 2:
                _t921 = self.parse_max_monoid()
                value228 = _t921
                _t922 = logic_pb2.Monoid(max_monoid=value228)
                _t920 = _t922
            else:
                if prediction225 == 1:
                    _t924 = self.parse_min_monoid()
                    value227 = _t924
                    _t925 = logic_pb2.Monoid(min_monoid=value227)
                    _t923 = _t925
                else:
                    if prediction225 == 0:
                        _t927 = self.parse_or_monoid()
                        value226 = _t927
                        _t928 = logic_pb2.Monoid(or_monoid=value226)
                        _t926 = _t928
                    else:
                        raise ParseError(f"{'Unexpected token in monoid'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t926 = None
                    _t923 = _t926
                _t920 = _t923
            _t917 = _t920
        return _t917

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        self.consume_literal('(')
        self.consume_literal('or')
        self.consume_literal(')')
        return logic_pb2.OrMonoid

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        self.consume_literal('(')
        self.consume_literal('min')
        _t929 = self.parse_type()
        type230 = _t929
        self.consume_literal(')')
        _t930 = logic_pb2.MinMonoid(type=type230)
        return _t930

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        self.consume_literal('(')
        self.consume_literal('max')
        _t931 = self.parse_type()
        type231 = _t931
        self.consume_literal(')')
        _t932 = logic_pb2.MaxMonoid(type=type231)
        return _t932

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        self.consume_literal('(')
        self.consume_literal('sum')
        _t933 = self.parse_type()
        type232 = _t933
        self.consume_literal(')')
        _t934 = logic_pb2.SumMonoid(type=type232)
        return _t934

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal('(')
        self.consume_literal('monus')
        _t935 = self.parse_monoid()
        monoid233 = _t935
        _t936 = self.parse_relation_id()
        name234 = _t936
        _t937 = self.parse_abstraction_with_arity()
        abstraction_with_arity235 = _t937
        if self.match_lookahead_literal('(', 0):
            _t939 = self.parse_attrs()
            _t938 = _t939
        else:
            _t938 = None
        attrs236 = _t938
        self.consume_literal(')')
        abstraction = abstraction_with_arity235[0]
        arity = abstraction_with_arity235[1]
        _t940 = logic_pb2.MonusDef(monoid=monoid233, name=name234, body=abstraction, attrs=(attrs236 if attrs236 is not None else []), value_arity=arity)
        return _t940

    def parse_constraint(self) -> logic_pb2.Constraint:
        self.consume_literal('(')
        self.consume_literal('functional_dependency')
        _t941 = self.parse_relation_id()
        name237 = _t941
        _t942 = self.parse_abstraction()
        guard238 = _t942
        _t943 = self.parse_functional_dependency_keys()
        keys239 = _t943
        _t944 = self.parse_functional_dependency_values()
        values240 = _t944
        self.consume_literal(')')
        _t945 = logic_pb2.FunctionalDependency(guard=guard238, keys=keys239, values=values240)
        _t946 = logic_pb2.Constraint(name=name237, functional_dependency=_t945)
        return _t946

    def parse_functional_dependency_keys(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('keys')
        xs241 = []
        cond242 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond242:
            _t947 = self.parse_var()
            xs241.append(_t947)
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
            _t948 = self.parse_var()
            xs244.append(_t948)
            cond245 = self.match_lookahead_terminal('SYMBOL', 0)
        x246 = xs244
        self.consume_literal(')')
        return x246

    def parse_data(self) -> logic_pb2.Data:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('rel_edb', 1):
                _t950 = 0
            else:
                if self.match_lookahead_literal('csvdata', 1):
                    _t951 = 2
                else:
                    _t951 = (self.match_lookahead_literal('be_tree_relation', 1) or -1)
                _t950 = _t951
            _t949 = _t950
        else:
            _t949 = -1
        prediction247 = _t949
        if prediction247 == 2:
            _t953 = self.parse_csv_data()
            value250 = _t953
            _t954 = logic_pb2.Data(csv_data=value250)
            _t952 = _t954
        else:
            if prediction247 == 1:
                _t956 = self.parse_betree_relation()
                value249 = _t956
                _t957 = logic_pb2.Data(betree_relation=value249)
                _t955 = _t957
            else:
                if prediction247 == 0:
                    _t959 = self.parse_rel_edb()
                    value248 = _t959
                    _t960 = logic_pb2.Data(rel_edb=value248)
                    _t958 = _t960
                else:
                    raise ParseError(f"{'Unexpected token in data'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t958 = None
                _t955 = _t958
            _t952 = _t955
        return _t952

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        self.consume_literal('(')
        self.consume_literal('rel_edb')
        _t961 = self.parse_relation_id()
        target_id251 = _t961
        xs252 = []
        cond253 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond253:
            _t962 = self.parse_name()
            xs252.append(_t962)
            cond253 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        path254 = xs252
        if self.match_lookahead_literal('(', 0):
            _t964 = self.parse_rel_edb_types()
            _t963 = _t964
        else:
            _t963 = None
        types255 = _t963
        self.consume_literal(')')
        _t965 = logic_pb2.RelEDB(target_id=target_id251, path=path254, types=(types255 if types255 is not None else []))
        return _t965

    def parse_rel_edb_types(self) -> list[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('types')
        xs256 = []
        cond257 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond257:
            _t966 = self.parse_type()
            xs256.append(_t966)
            cond257 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        x258 = xs256
        self.consume_literal(')')
        return x258

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        _t967 = self.parse_be_tree_relation()
        x259 = _t967
        return x259

    def parse_be_tree_relation(self) -> logic_pb2.BeTreeRelation:
        self.consume_literal('(')
        self.consume_literal('be_tree_relation')
        _t968 = self.parse_relation_id()
        name260 = _t968
        _t969 = self.parse_be_tree_info()
        relation_info261 = _t969
        self.consume_literal(')')
        _t970 = logic_pb2.BeTreeRelation(name=name260, relation_info=relation_info261)
        return _t970

    def parse_be_tree_info(self) -> logic_pb2.BeTreeInfo:
        self.consume_literal('(')
        self.consume_literal('be_tree_info')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('key_types', 1)):
            _t972 = self.parse_be_tree_info_key_types()
            _t971 = _t972
        else:
            _t971 = None
        key_types262 = _t971
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('value_types', 1)):
            _t974 = self.parse_be_tree_info_value_types()
            _t973 = _t974
        else:
            _t973 = None
        value_types263 = _t973
        _t975 = self.parse_be_tree_config()
        storage_config264 = _t975
        _t976 = self.parse_be_tree_locator()
        relation_locator265 = _t976
        self.consume_literal(')')
        _t977 = logic_pb2.BeTreeInfo(key_types=(key_types262 if key_types262 is not None else []), value_types=(value_types263 if value_types263 is not None else []), storage_config=storage_config264, relation_locator=relation_locator265)
        return _t977

    def parse_be_tree_info_key_types(self) -> list[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('key_types')
        xs266 = []
        cond267 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond267:
            _t978 = self.parse_type()
            xs266.append(_t978)
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
            _t979 = self.parse_type()
            xs269.append(_t979)
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
        _t980 = logic_pb2.BeTreeConfig(epsilon=epsilon272, max_pivots=max_pivots273, max_deltas=max_deltas274, max_leaf=max_leaf275)
        return _t980

    def parse_be_tree_locator(self) -> logic_pb2.BeTreeLocator:
        self.consume_literal('(')
        self.consume_literal('be_tree_locator')
        element_count276 = self.consume_terminal('INT')
        tree_height277 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t981 = logic_pb2.BeTreeLocator(element_count=element_count276, tree_height=tree_height277)
        return _t981

    def parse_csv_data(self) -> logic_pb2.CSVData:
        _t982 = self.parse_csvdata()
        x278 = _t982
        return x278

    def parse_csvdata(self) -> logic_pb2.CSVData:
        self.consume_literal('(')
        self.consume_literal('csvdata')
        _t983 = self.parse_csvlocator()
        locator279 = _t983
        _t984 = self.parse_csv_config()
        config280 = _t984
        xs281 = []
        cond282 = self.match_lookahead_literal('(', 0)
        while cond282:
            _t985 = self.parse_csv_column()
            xs281.append(_t985)
            cond282 = self.match_lookahead_literal('(', 0)
        columns283 = xs281
        _t986 = self.parse_name()
        asof284 = _t986
        self.consume_literal(')')
        _t987 = logic_pb2.CSVData(locator=locator279, config=config280, columns=columns283, asof=asof284)
        return _t987

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        self.consume_literal('(')
        self.consume_literal('csvlocator')
        xs285 = []
        cond286 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond286:
            _t988 = self.parse_name()
            xs285.append(_t988)
            cond286 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        paths287 = xs285
        _t989 = self.parse_name()
        inline_data288 = _t989
        self.consume_literal(')')
        _t990 = logic_pb2.CSVLocator(paths=paths287, inline_data=inline_data288)
        return _t990

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        self.consume_literal('(')
        self.consume_literal('csv_config')
        header_row289 = self.consume_terminal('INT')
        skip290 = self.consume_terminal('INT')
        _t991 = self.parse_name()
        new_line291 = _t991
        _t992 = self.parse_name()
        delimiter292 = _t992
        _t993 = self.parse_name()
        quotechar293 = _t993
        _t994 = self.parse_name()
        escapechar294 = _t994
        _t995 = self.parse_name()
        comment295 = _t995
        xs296 = []
        cond297 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond297:
            _t996 = self.parse_name()
            xs296.append(_t996)
            cond297 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        missing_strings298 = xs296
        _t997 = self.parse_name()
        decimal_separator299 = _t997
        _t998 = self.parse_name()
        encoding300 = _t998
        _t999 = self.parse_name()
        compression301 = _t999
        self.consume_literal(')')
        _t1000 = self.int64_to_int32(header_row289)
        _t1001 = logic_pb2.CSVConfig(header_row=_t1000, skip=skip290, new_line=new_line291, delimiter=delimiter292, quotechar=quotechar293, escapechar=escapechar294, comment=comment295, missing_strings=missing_strings298, decimal_separator=decimal_separator299, encoding=encoding300, compression=compression301)
        return _t1001

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        self.consume_literal('(')
        self.consume_literal('csv_column')
        _t1002 = self.parse_name()
        column_name302 = _t1002
        _t1003 = self.parse_relation_id()
        target_id303 = _t1003
        xs304 = []
        cond305 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond305:
            _t1004 = self.parse_type()
            xs304.append(_t1004)
            cond305 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types306 = xs304
        self.consume_literal(')')
        _t1005 = logic_pb2.CSVColumn(column_name=column_name302, target_id=target_id303, types=types306)
        return _t1005

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal('(')
        self.consume_literal('undefine')
        _t1006 = self.parse_fragment_id()
        fragment_id307 = _t1006
        self.consume_literal(')')
        _t1007 = transactions_pb2.Undefine(fragment_id=fragment_id307)
        return _t1007

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal('(')
        self.consume_literal('context')
        xs308 = []
        cond309 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        while cond309:
            _t1008 = self.parse_relation_id()
            xs308.append(_t1008)
            cond309 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        relations310 = xs308
        self.consume_literal(')')
        _t1009 = transactions_pb2.Context(relations=relations310)
        return _t1009

    def parse_epoch_reads(self) -> list[transactions_pb2.Read]:
        self.consume_literal('(')
        self.consume_literal('reads')
        xs311 = []
        cond312 = self.match_lookahead_literal('(', 0)
        while cond312:
            _t1010 = self.parse_read()
            xs311.append(_t1010)
            cond312 = self.match_lookahead_literal('(', 0)
        x313 = xs311
        self.consume_literal(')')
        return x313

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('what_if', 1):
                _t1012 = 2
            else:
                if self.match_lookahead_literal('output', 1):
                    _t1016 = 1
                else:
                    if self.match_lookahead_literal('export', 1):
                        _t1017 = 4
                    else:
                        if self.match_lookahead_literal('demand', 1):
                            _t1018 = 0
                        else:
                            if self.match_lookahead_literal('abort', 1):
                                _t1019 = 3
                            else:
                                _t1019 = -1
                            _t1018 = _t1019
                        _t1017 = _t1018
                    _t1016 = _t1017
                _t1012 = _t1016
            _t1011 = _t1012
        else:
            _t1011 = -1
        prediction314 = _t1011
        if prediction314 == 4:
            _t1021 = self.parse_export()
            value319 = _t1021
            _t1022 = transactions_pb2.Read(export=value319)
            _t1020 = _t1022
        else:
            if prediction314 == 3:
                _t1024 = self.parse_abort()
                value318 = _t1024
                _t1025 = transactions_pb2.Read(abort=value318)
                _t1023 = _t1025
            else:
                if prediction314 == 2:
                    _t1027 = self.parse_what_if()
                    value317 = _t1027
                    _t1028 = transactions_pb2.Read(what_if=value317)
                    _t1026 = _t1028
                else:
                    if prediction314 == 1:
                        _t1030 = self.parse_output()
                        value316 = _t1030
                        _t1031 = transactions_pb2.Read(output=value316)
                        _t1029 = _t1031
                    else:
                        if prediction314 == 0:
                            _t1033 = self.parse_demand()
                            value315 = _t1033
                            _t1034 = transactions_pb2.Read(demand=value315)
                            _t1032 = _t1034
                        else:
                            raise ParseError(f"{'Unexpected token in read'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t1032 = None
                        _t1029 = _t1032
                    _t1026 = _t1029
                _t1023 = _t1026
            _t1020 = _t1023
        return _t1020

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal('(')
        self.consume_literal('demand')
        _t1035 = self.parse_relation_id()
        relation_id320 = _t1035
        self.consume_literal(')')
        _t1036 = transactions_pb2.Demand(relation_id=relation_id320)
        return _t1036

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal('(')
        self.consume_literal('output')
        if self.match_lookahead_terminal('COLON_SYMBOL', 0):
            _t1038 = self.parse_name()
            _t1037 = _t1038
        else:
            _t1037 = None
        name321 = _t1037
        _t1039 = self.parse_relation_id()
        relation_id322 = _t1039
        self.consume_literal(')')
        _t1040 = transactions_pb2.Output(name=(name321 if name321 is not None else 'output'), relation_id=relation_id322)
        return _t1040

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal('(')
        self.consume_literal('what_if')
        _t1041 = self.parse_name()
        branch323 = _t1041
        _t1042 = self.parse_epoch()
        epoch324 = _t1042
        self.consume_literal(')')
        _t1043 = transactions_pb2.WhatIf(branch=branch323, epoch=epoch324)
        return _t1043

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal('(')
        self.consume_literal('abort')
        if self.match_lookahead_terminal('COLON_SYMBOL', 0):
            _t1045 = self.parse_name()
            _t1044 = _t1045
        else:
            _t1044 = None
        name325 = _t1044
        _t1046 = self.parse_relation_id()
        relation_id326 = _t1046
        self.consume_literal(')')
        _t1047 = transactions_pb2.Abort(name=(name325 if name325 is not None else 'abort'), relation_id=relation_id326)
        return _t1047

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal('(')
        self.consume_literal('export')
        _t1048 = self.parse_export_csv_config()
        config327 = _t1048
        self.consume_literal(')')
        _t1049 = transactions_pb2.Export(csv_config=config327)
        return _t1049

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal('(')
        self.consume_literal('export_csv_config')
        _t1050 = self.parse_export_csv_path()
        path328 = _t1050
        _t1051 = self.parse_export_csv_columns()
        columns329 = _t1051
        _t1052 = self.parse_config_dict()
        config330 = _t1052
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
            _t1053 = self.parse_export_csv_column()
            xs332.append(_t1053)
            cond333 = self.match_lookahead_literal('(', 0)
        x334 = xs332
        self.consume_literal(')')
        return x334

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        name335 = self.consume_terminal('STRING')
        _t1054 = self.parse_relation_id()
        relation_id336 = _t1054
        self.consume_literal(')')
        _t1055 = transactions_pb2.ExportCSVColumn(column_name=name335, column_data=relation_id336)
        return _t1055


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
