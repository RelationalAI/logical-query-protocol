"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.


Command: python -m meta.cli ../proto/relationalai/lqp/v1/fragments.proto ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto --parser python
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
        return transactions_pb2.Transaction

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal('(')
        self.consume_literal('configure')
        _t342 = self.parse_config_dict()
        config_dict5 = _t342
        self.consume_literal(')')
        return self.construct_configure(config_dict5)

    def parse_config_dict(self) -> list[tuple[str, logic_pb2.Value]]:
        self.consume_literal('{')
        xs6 = []
        cond7 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond7:
            _t343 = self.parse_config_key_value()
            xs6.append(_t343)
            cond7 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        x8 = xs6
        self.consume_literal('}')
        return x8

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        symbol9 = self.consume_terminal('COLON_SYMBOL')
        _t344 = self.parse_value()
        value10 = _t344
        return (symbol9, value10,)

    def parse_value(self) -> logic_pb2.Value:
        if self.match_lookahead_literal('true', 0):
            _t345 = 9
        else:
            if self.match_lookahead_literal('missing', 0):
                _t346 = 8
            else:
                if self.match_lookahead_literal('false', 0):
                    _t347 = 9
                else:
                    if self.match_lookahead_literal('(', 0):
                        if self.match_lookahead_literal('datetime', 1):
                            _t350 = 1
                        else:
                            if self.match_lookahead_literal('date', 1):
                                _t351 = 0
                            else:
                                _t351 = -1
                            _t350 = _t351
                        _t348 = _t350
                    else:
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t352 = 5
                        else:
                            if self.match_lookahead_terminal('STRING', 0):
                                _t353 = 2
                            else:
                                if self.match_lookahead_terminal('INT128', 0):
                                    _t354 = 6
                                else:
                                    if self.match_lookahead_terminal('INT', 0):
                                        _t355 = 3
                                    else:
                                        if self.match_lookahead_terminal('FLOAT', 0):
                                            _t356 = 4
                                        else:
                                            if self.match_lookahead_terminal('DECIMAL', 0):
                                                _t357 = 7
                                            else:
                                                _t357 = -1
                                            _t356 = _t357
                                        _t355 = _t356
                                    _t354 = _t355
                                _t353 = _t354
                            _t352 = _t353
                        _t348 = _t352
                    _t347 = _t348
                _t346 = _t347
            _t345 = _t346
        prediction11 = _t345
        if prediction11 == 9:
            _t359 = self.parse_boolean_value()
            value20 = _t359
            _t358 = logic_pb2.Value
        else:
            if prediction11 == 8:
                self.consume_literal('missing')
                _t360 = logic_pb2.Value
            else:
                if prediction11 == 7:
                    value19 = self.consume_terminal('DECIMAL')
                    _t361 = logic_pb2.Value
                else:
                    if prediction11 == 6:
                        value18 = self.consume_terminal('INT128')
                        _t362 = logic_pb2.Value
                    else:
                        if prediction11 == 5:
                            value17 = self.consume_terminal('UINT128')
                            _t363 = logic_pb2.Value
                        else:
                            if prediction11 == 4:
                                value16 = self.consume_terminal('FLOAT')
                                _t364 = logic_pb2.Value
                            else:
                                if prediction11 == 3:
                                    value15 = self.consume_terminal('INT')
                                    _t365 = logic_pb2.Value
                                else:
                                    if prediction11 == 2:
                                        value14 = self.consume_terminal('STRING')
                                        _t366 = logic_pb2.Value
                                    else:
                                        if prediction11 == 1:
                                            _t368 = self.parse_datetime()
                                            value13 = _t368
                                            _t367 = logic_pb2.Value
                                        else:
                                            if prediction11 == 0:
                                                _t370 = self.parse_date()
                                                value12 = _t370
                                                _t369 = logic_pb2.Value
                                            else:
                                                raise ParseError(f"{'Unexpected token in value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t369 = None
                                            _t367 = _t369
                                        _t366 = _t367
                                    _t365 = _t366
                                _t364 = _t365
                            _t363 = _t364
                        _t362 = _t363
                    _t361 = _t362
                _t360 = _t361
            _t358 = _t360
        return _t358

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal('(')
        self.consume_literal('date')
        year21 = self.consume_terminal('INT')
        month22 = self.consume_terminal('INT')
        day23 = self.consume_terminal('INT')
        self.consume_literal(')')
        return logic_pb2.DateValue

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
            _t371 = self.consume_terminal('INT')
        else:
            _t371 = None
        microsecond30 = _t371
        self.consume_literal(')')
        return logic_pb2.DateTimeValue

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal('true', 0):
            _t372 = 0
        else:
            _t372 = (self.match_lookahead_literal('false', 0) or -1)
        prediction31 = _t372
        if prediction31 == 1:
            self.consume_literal('false')
            _t373 = False
        else:
            if prediction31 == 0:
                self.consume_literal('true')
                _t374 = True
            else:
                raise ParseError(f"{'Unexpected token in boolean_value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t374 = None
            _t373 = _t374
        return _t373

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal('(')
        self.consume_literal('sync')
        xs32 = []
        cond33 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond33:
            _t375 = self.parse_fragment_id()
            xs32.append(_t375)
            cond33 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        fragments34 = xs32
        self.consume_literal(')')
        return transactions_pb2.Sync

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
        return transactions_pb2.Epoch

    def parse_epoch_writes(self) -> list[transactions_pb2.Write]:
        self.consume_literal('(')
        self.consume_literal('writes')
        xs38 = []
        cond39 = self.match_lookahead_literal('(', 0)
        while cond39:
            _t380 = self.parse_write()
            xs38.append(_t380)
            cond39 = self.match_lookahead_literal('(', 0)
        x40 = xs38
        self.consume_literal(')')
        return x40

    def parse_write(self) -> transactions_pb2.Write:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('undefine', 1):
                _t384 = 1
            else:
                if self.match_lookahead_literal('define', 1):
                    _t385 = 0
                else:
                    if self.match_lookahead_literal('context', 1):
                        _t386 = 2
                    else:
                        _t386 = -1
                    _t385 = _t386
                _t384 = _t385
            _t381 = _t384
        else:
            _t381 = -1
        prediction41 = _t381
        if prediction41 == 2:
            _t388 = self.parse_context()
            value44 = _t388
            _t387 = transactions_pb2.Write
        else:
            if prediction41 == 1:
                _t390 = self.parse_undefine()
                value43 = _t390
                _t389 = transactions_pb2.Write
            else:
                if prediction41 == 0:
                    _t392 = self.parse_define()
                    value42 = _t392
                    _t391 = transactions_pb2.Write
                else:
                    raise ParseError(f"{'Unexpected token in write'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t391 = None
                _t389 = _t391
            _t387 = _t389
        return _t387

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal('(')
        self.consume_literal('define')
        _t393 = self.parse_fragment()
        fragment45 = _t393
        self.consume_literal(')')
        return transactions_pb2.Define

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal('(')
        self.consume_literal('fragment')
        _t394 = self.parse_new_fragment_id()
        fragment_id46 = _t394
        xs47 = []
        cond48 = self.match_lookahead_literal('(', 0)
        while cond48:
            _t395 = self.parse_declaration()
            xs47.append(_t395)
            cond48 = self.match_lookahead_literal('(', 0)
        declarations49 = xs47
        self.consume_literal(')')
        return self.construct_fragment(fragment_id46, declarations49)

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        _t396 = self.parse_fragment_id()
        fragment_id50 = _t396
        self.start_fragment(fragment_id50)
        return fragment_id50

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('rel_edb', 1):
                _t398 = 3
            else:
                if self.match_lookahead_literal('functional_dependency', 1):
                    _t399 = 2
                else:
                    if self.match_lookahead_literal('def', 1):
                        _t400 = 0
                    else:
                        if self.match_lookahead_literal('csvdata', 1):
                            _t401 = 3
                        else:
                            if self.match_lookahead_literal('be_tree_relation', 1):
                                _t402 = 3
                            else:
                                _t402 = (self.match_lookahead_literal('algorithm', 1) or -1)
                            _t401 = _t402
                        _t400 = _t401
                    _t399 = _t400
                _t398 = _t399
            _t397 = _t398
        else:
            _t397 = -1
        prediction51 = _t397
        if prediction51 == 3:
            _t404 = self.parse_data()
            value55 = _t404
            _t403 = logic_pb2.Declaration
        else:
            if prediction51 == 2:
                _t406 = self.parse_constraint()
                value54 = _t406
                _t405 = logic_pb2.Declaration
            else:
                if prediction51 == 1:
                    _t408 = self.parse_algorithm()
                    value53 = _t408
                    _t407 = logic_pb2.Declaration
                else:
                    if prediction51 == 0:
                        _t410 = self.parse_def()
                        value52 = _t410
                        _t409 = logic_pb2.Declaration
                    else:
                        raise ParseError(f"{'Unexpected token in declaration'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t409 = None
                    _t407 = _t409
                _t405 = _t407
            _t403 = _t405
        return _t403

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal('(')
        self.consume_literal('def')
        _t411 = self.parse_relation_id()
        name56 = _t411
        _t412 = self.parse_abstraction()
        body57 = _t412
        if self.match_lookahead_literal('(', 0):
            _t414 = self.parse_attrs()
            _t413 = _t414
        else:
            _t413 = None
        attrs58 = _t413
        self.consume_literal(')')
        return logic_pb2.Def

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_terminal('INT', 0):
            _t416 = 1
        else:
            if self.match_lookahead_terminal('COLON_SYMBOL', 0):
                _t417 = 0
            else:
                _t417 = -1
            _t416 = _t417
        prediction59 = _t416
        if prediction59 == 1:
            INT61 = self.consume_terminal('INT')
            _t418 = logic_pb2.RelationId(id_low=INT61 & 0xFFFFFFFFFFFFFFFF, id_high=(INT61 >> 64) & 0xFFFFFFFFFFFFFFFF)
        else:
            if prediction59 == 0:
                symbol60 = self.consume_terminal('COLON_SYMBOL')
                _t419 = self.relation_id_from_string(symbol60)
            else:
                raise ParseError(f"{'Unexpected token in relation_id'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t419 = None
            _t418 = _t419
        return _t418

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal('(')
        _t420 = self.parse_bindings()
        bindings62 = _t420
        _t421 = self.parse_formula()
        formula63 = _t421
        self.consume_literal(')')
        return logic_pb2.Abstraction

    def parse_bindings(self) -> tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]:
        self.consume_literal('[')
        xs64 = []
        cond65 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond65:
            _t422 = self.parse_binding()
            xs64.append(_t422)
            cond65 = self.match_lookahead_terminal('SYMBOL', 0)
        keys66 = xs64
        if self.match_lookahead_literal('|', 0):
            _t424 = self.parse_value_bindings()
            _t423 = _t424
        else:
            _t423 = None
        values67 = _t423
        self.consume_literal(']')
        return (keys66, (values67 if values67 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol68 = self.consume_terminal('SYMBOL')
        self.consume_literal('::')
        _t425 = self.parse_type()
        type69 = _t425
        return logic_pb2.Binding

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal('UNKNOWN', 0):
            _t426 = 0
        else:
            if self.match_lookahead_literal('UINT128', 0):
                _t427 = 4
            else:
                if self.match_lookahead_literal('STRING', 0):
                    _t436 = 1
                else:
                    if self.match_lookahead_literal('MISSING', 0):
                        _t437 = 8
                    else:
                        if self.match_lookahead_literal('INT128', 0):
                            _t438 = 5
                        else:
                            if self.match_lookahead_literal('INT', 0):
                                _t439 = 2
                            else:
                                if self.match_lookahead_literal('FLOAT', 0):
                                    _t440 = 3
                                else:
                                    if self.match_lookahead_literal('DATETIME', 0):
                                        _t441 = 7
                                    else:
                                        if self.match_lookahead_literal('DATE', 0):
                                            _t442 = 6
                                        else:
                                            if self.match_lookahead_literal('BOOLEAN', 0):
                                                _t443 = 10
                                            else:
                                                if self.match_lookahead_literal('(', 0):
                                                    _t444 = 9
                                                else:
                                                    _t444 = -1
                                                _t443 = _t444
                                            _t442 = _t443
                                        _t441 = _t442
                                    _t440 = _t441
                                _t439 = _t440
                            _t438 = _t439
                        _t437 = _t438
                    _t436 = _t437
                _t427 = _t436
            _t426 = _t427
        prediction70 = _t426
        if prediction70 == 10:
            _t446 = self.parse_boolean_type()
            value81 = _t446
            _t445 = logic_pb2.Type
        else:
            if prediction70 == 9:
                _t448 = self.parse_decimal_type()
                value80 = _t448
                _t447 = logic_pb2.Type
            else:
                if prediction70 == 8:
                    _t450 = self.parse_missing_type()
                    value79 = _t450
                    _t449 = logic_pb2.Type
                else:
                    if prediction70 == 7:
                        _t452 = self.parse_datetime_type()
                        value78 = _t452
                        _t451 = logic_pb2.Type
                    else:
                        if prediction70 == 6:
                            _t454 = self.parse_date_type()
                            value77 = _t454
                            _t453 = logic_pb2.Type
                        else:
                            if prediction70 == 5:
                                _t456 = self.parse_int128_type()
                                value76 = _t456
                                _t455 = logic_pb2.Type
                            else:
                                if prediction70 == 4:
                                    _t458 = self.parse_uint128_type()
                                    value75 = _t458
                                    _t457 = logic_pb2.Type
                                else:
                                    if prediction70 == 3:
                                        _t460 = self.parse_float_type()
                                        value74 = _t460
                                        _t459 = logic_pb2.Type
                                    else:
                                        if prediction70 == 2:
                                            _t462 = self.parse_int_type()
                                            value73 = _t462
                                            _t461 = logic_pb2.Type
                                        else:
                                            if prediction70 == 1:
                                                _t464 = self.parse_string_type()
                                                value72 = _t464
                                                _t463 = logic_pb2.Type
                                            else:
                                                if prediction70 == 0:
                                                    _t466 = self.parse_unspecified_type()
                                                    value71 = _t466
                                                    _t465 = logic_pb2.Type
                                                else:
                                                    raise ParseError(f"{'Unexpected token in type'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                    _t465 = None
                                                _t463 = _t465
                                            _t461 = _t463
                                        _t459 = _t461
                                    _t457 = _t459
                                _t455 = _t457
                            _t453 = _t455
                        _t451 = _t453
                    _t449 = _t451
                _t447 = _t449
            _t445 = _t447
        return _t445

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
        return logic_pb2.DecimalType

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal('BOOLEAN')
        return logic_pb2.BooleanType

    def parse_value_bindings(self) -> list[logic_pb2.Binding]:
        self.consume_literal('|')
        xs84 = []
        cond85 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond85:
            _t467 = self.parse_binding()
            xs84.append(_t467)
            cond85 = self.match_lookahead_terminal('SYMBOL', 0)
        x86 = xs84
        return x86

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('true', 1):
                _t469 = 0
            else:
                if self.match_lookahead_literal('rel_atom', 1):
                    _t470 = 11
                else:
                    if self.match_lookahead_literal('reduce', 1):
                        _t471 = 3
                    else:
                        if self.match_lookahead_literal('primitive', 1):
                            _t472 = 10
                        else:
                            if self.match_lookahead_literal('pragma', 1):
                                _t473 = 9
                            else:
                                if self.match_lookahead_literal('or', 1):
                                    _t474 = 5
                                else:
                                    if self.match_lookahead_literal('not', 1):
                                        _t475 = 6
                                    else:
                                        if self.match_lookahead_literal('ffi', 1):
                                            _t476 = 7
                                        else:
                                            if self.match_lookahead_literal('false', 1):
                                                _t490 = 1
                                            else:
                                                if self.match_lookahead_literal('exists', 1):
                                                    _t491 = 2
                                                else:
                                                    if self.match_lookahead_literal('cast', 1):
                                                        _t492 = 12
                                                    else:
                                                        if self.match_lookahead_literal('atom', 1):
                                                            _t493 = 8
                                                        else:
                                                            if self.match_lookahead_literal('and', 1):
                                                                _t494 = 4
                                                            else:
                                                                if self.match_lookahead_literal('>=', 1):
                                                                    _t495 = 10
                                                                else:
                                                                    if self.match_lookahead_literal('>', 1):
                                                                        _t496 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal('=', 1):
                                                                            _t497 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal('<=', 1):
                                                                                _t498 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal('<', 1):
                                                                                    _t499 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal('/', 1):
                                                                                        _t500 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal('-', 1):
                                                                                            _t501 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal('+', 1):
                                                                                                _t502 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal('*', 1):
                                                                                                    _t503 = 10
                                                                                                else:
                                                                                                    _t503 = -1
                                                                                                _t502 = _t503
                                                                                            _t501 = _t502
                                                                                        _t500 = _t501
                                                                                    _t499 = _t500
                                                                                _t498 = _t499
                                                                            _t497 = _t498
                                                                        _t496 = _t497
                                                                    _t495 = _t496
                                                                _t494 = _t495
                                                            _t493 = _t494
                                                        _t492 = _t493
                                                    _t491 = _t492
                                                _t490 = _t491
                                            _t476 = _t490
                                        _t475 = _t476
                                    _t474 = _t475
                                _t473 = _t474
                            _t472 = _t473
                        _t471 = _t472
                    _t470 = _t471
                _t469 = _t470
            _t468 = _t469
        else:
            _t468 = -1
        prediction87 = _t468
        if prediction87 == 12:
            _t505 = self.parse_cast()
            value100 = _t505
            _t504 = logic_pb2.Formula
        else:
            if prediction87 == 11:
                _t507 = self.parse_rel_atom()
                value99 = _t507
                _t506 = logic_pb2.Formula
            else:
                if prediction87 == 10:
                    _t509 = self.parse_primitive()
                    value98 = _t509
                    _t508 = logic_pb2.Formula
                else:
                    if prediction87 == 9:
                        _t511 = self.parse_pragma()
                        value97 = _t511
                        _t510 = logic_pb2.Formula
                    else:
                        if prediction87 == 8:
                            _t513 = self.parse_atom()
                            value96 = _t513
                            _t512 = logic_pb2.Formula
                        else:
                            if prediction87 == 7:
                                _t515 = self.parse_ffi()
                                value95 = _t515
                                _t514 = logic_pb2.Formula
                            else:
                                if prediction87 == 6:
                                    _t517 = self.parse_not()
                                    value94 = _t517
                                    _t516 = logic_pb2.Formula
                                else:
                                    if prediction87 == 5:
                                        _t519 = self.parse_disjunction()
                                        value93 = _t519
                                        _t518 = logic_pb2.Formula
                                    else:
                                        if prediction87 == 4:
                                            _t521 = self.parse_conjunction()
                                            value92 = _t521
                                            _t520 = logic_pb2.Formula
                                        else:
                                            if prediction87 == 3:
                                                _t523 = self.parse_reduce()
                                                value91 = _t523
                                                _t522 = logic_pb2.Formula
                                            else:
                                                if prediction87 == 2:
                                                    _t525 = self.parse_exists()
                                                    value90 = _t525
                                                    _t524 = logic_pb2.Formula
                                                else:
                                                    if prediction87 == 1:
                                                        _t527 = self.parse_false()
                                                        value89 = _t527
                                                        _t526 = logic_pb2.Formula
                                                    else:
                                                        if prediction87 == 0:
                                                            _t529 = self.parse_true()
                                                            value88 = _t529
                                                            _t528 = logic_pb2.Formula
                                                        else:
                                                            raise ParseError(f"{'Unexpected token in formula'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t528 = None
                                                        _t526 = _t528
                                                    _t524 = _t526
                                                _t522 = _t524
                                            _t520 = _t522
                                        _t518 = _t520
                                    _t516 = _t518
                                _t514 = _t516
                            _t512 = _t514
                        _t510 = _t512
                    _t508 = _t510
                _t506 = _t508
            _t504 = _t506
        return _t504

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('true')
        self.consume_literal(')')
        return logic_pb2.Conjunction

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('false')
        self.consume_literal(')')
        return logic_pb2.Disjunction

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal('(')
        self.consume_literal('exists')
        _t530 = self.parse_bindings()
        bindings101 = _t530
        _t531 = self.parse_formula()
        formula102 = _t531
        self.consume_literal(')')
        return logic_pb2.Exists

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal('(')
        self.consume_literal('reduce')
        _t532 = self.parse_abstraction()
        op103 = _t532
        _t533 = self.parse_abstraction()
        body104 = _t533
        _t534 = self.parse_terms()
        terms105 = _t534
        self.consume_literal(')')
        return logic_pb2.Reduce

    def parse_terms(self) -> list[logic_pb2.Term]:
        self.consume_literal('(')
        self.consume_literal('terms')
        xs106 = []
        cond107 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond107:
            _t535 = self.parse_term()
            xs106.append(_t535)
            cond107 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        x108 = xs106
        self.consume_literal(')')
        return x108

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_literal('true', 0):
            _t567 = 1
        else:
            if self.match_lookahead_literal('missing', 0):
                _t583 = 1
            else:
                if self.match_lookahead_literal('false', 0):
                    _t591 = 1
                else:
                    if self.match_lookahead_literal('(', 0):
                        _t595 = 1
                    else:
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t597 = 1
                        else:
                            if self.match_lookahead_terminal('SYMBOL', 0):
                                _t598 = 0
                            else:
                                _t598 = (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or -1)))))
                            _t597 = _t598
                        _t595 = _t597
                    _t591 = _t595
                _t583 = _t591
            _t567 = _t583
        prediction109 = _t567
        if prediction109 == 1:
            _t600 = self.parse_constant()
            value111 = _t600
            _t599 = logic_pb2.Term
        else:
            if prediction109 == 0:
                _t602 = self.parse_var()
                value110 = _t602
                _t601 = logic_pb2.Term
            else:
                raise ParseError(f"{'Unexpected token in term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t601 = None
            _t599 = _t601
        return _t599

    def parse_var(self) -> logic_pb2.Var:
        symbol112 = self.consume_terminal('SYMBOL')
        return logic_pb2.Var

    def parse_constant(self) -> logic_pb2.Value:
        _t603 = self.parse_value()
        x113 = _t603
        return x113

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('and')
        xs114 = []
        cond115 = self.match_lookahead_literal('(', 0)
        while cond115:
            _t604 = self.parse_formula()
            xs114.append(_t604)
            cond115 = self.match_lookahead_literal('(', 0)
        args116 = xs114
        self.consume_literal(')')
        return logic_pb2.Conjunction

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('or')
        xs117 = []
        cond118 = self.match_lookahead_literal('(', 0)
        while cond118:
            _t605 = self.parse_formula()
            xs117.append(_t605)
            cond118 = self.match_lookahead_literal('(', 0)
        args119 = xs117
        self.consume_literal(')')
        return logic_pb2.Disjunction

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal('(')
        self.consume_literal('not')
        _t606 = self.parse_formula()
        arg120 = _t606
        self.consume_literal(')')
        return logic_pb2.Not

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal('(')
        self.consume_literal('ffi')
        _t607 = self.parse_name()
        name121 = _t607
        _t608 = self.parse_ffi_args()
        args122 = _t608
        _t609 = self.parse_terms()
        terms123 = _t609
        self.consume_literal(')')
        return logic_pb2.FFI

    def parse_name(self) -> str:
        x124 = self.consume_terminal('COLON_SYMBOL')
        return x124

    def parse_ffi_args(self) -> list[logic_pb2.Abstraction]:
        self.consume_literal('(')
        self.consume_literal('args')
        xs125 = []
        cond126 = self.match_lookahead_literal('(', 0)
        while cond126:
            _t610 = self.parse_abstraction()
            xs125.append(_t610)
            cond126 = self.match_lookahead_literal('(', 0)
        x127 = xs125
        self.consume_literal(')')
        return x127

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal('(')
        self.consume_literal('atom')
        _t611 = self.parse_relation_id()
        name128 = _t611
        xs129 = []
        cond130 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond130:
            _t612 = self.parse_term()
            xs129.append(_t612)
            cond130 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms131 = xs129
        self.consume_literal(')')
        return logic_pb2.Atom

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal('(')
        self.consume_literal('pragma')
        _t613 = self.parse_name()
        name132 = _t613
        xs133 = []
        cond134 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond134:
            _t614 = self.parse_term()
            xs133.append(_t614)
            cond134 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms135 = xs133
        self.consume_literal(')')
        return logic_pb2.Pragma

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('primitive', 1):
                _t616 = 9
            else:
                if self.match_lookahead_literal('>=', 1):
                    _t617 = 4
                else:
                    if self.match_lookahead_literal('>', 1):
                        _t618 = 3
                    else:
                        if self.match_lookahead_literal('=', 1):
                            _t619 = 0
                        else:
                            if self.match_lookahead_literal('<=', 1):
                                _t620 = 2
                            else:
                                if self.match_lookahead_literal('<', 1):
                                    _t625 = 1
                                else:
                                    if self.match_lookahead_literal('/', 1):
                                        _t626 = 8
                                    else:
                                        if self.match_lookahead_literal('-', 1):
                                            _t627 = 6
                                        else:
                                            if self.match_lookahead_literal('+', 1):
                                                _t628 = 5
                                            else:
                                                if self.match_lookahead_literal('*', 1):
                                                    _t629 = 7
                                                else:
                                                    _t629 = -1
                                                _t628 = _t629
                                            _t627 = _t628
                                        _t626 = _t627
                                    _t625 = _t626
                                _t620 = _t625
                            _t619 = _t620
                        _t618 = _t619
                    _t617 = _t618
                _t616 = _t617
            _t615 = _t616
        else:
            _t615 = -1
        prediction136 = _t615
        if prediction136 == 9:
            self.consume_literal('(')
            self.consume_literal('primitive')
            _t631 = self.parse_name()
            name146 = _t631
            xs147 = []
            cond148 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            while cond148:
                _t632 = self.parse_rel_term()
                xs147.append(_t632)
                cond148 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            terms149 = xs147
            self.consume_literal(')')
            _t630 = logic_pb2.Primitive
        else:
            if prediction136 == 8:
                _t634 = self.parse_divide()
                op145 = _t634
                _t633 = op145
            else:
                if prediction136 == 7:
                    _t636 = self.parse_multiply()
                    op144 = _t636
                    _t635 = op144
                else:
                    if prediction136 == 6:
                        _t638 = self.parse_minus()
                        op143 = _t638
                        _t637 = op143
                    else:
                        if prediction136 == 5:
                            _t640 = self.parse_add()
                            op142 = _t640
                            _t639 = op142
                        else:
                            if prediction136 == 4:
                                _t642 = self.parse_gt_eq()
                                op141 = _t642
                                _t641 = op141
                            else:
                                if prediction136 == 3:
                                    _t644 = self.parse_gt()
                                    op140 = _t644
                                    _t643 = op140
                                else:
                                    if prediction136 == 2:
                                        _t646 = self.parse_lt_eq()
                                        op139 = _t646
                                        _t645 = op139
                                    else:
                                        if prediction136 == 1:
                                            _t648 = self.parse_lt()
                                            op138 = _t648
                                            _t647 = op138
                                        else:
                                            if prediction136 == 0:
                                                _t650 = self.parse_eq()
                                                op137 = _t650
                                                _t649 = op137
                                            else:
                                                raise ParseError(f"{'Unexpected token in primitive'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t649 = None
                                            _t647 = _t649
                                        _t645 = _t647
                                    _t643 = _t645
                                _t641 = _t643
                            _t639 = _t641
                        _t637 = _t639
                    _t635 = _t637
                _t633 = _t635
            _t630 = _t633
        return _t630

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('=')
        _t651 = self.parse_term()
        left150 = _t651
        _t652 = self.parse_term()
        right151 = _t652
        self.consume_literal(')')
        return logic_pb2.Primitive

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<')
        _t653 = self.parse_term()
        left152 = _t653
        _t654 = self.parse_term()
        right153 = _t654
        self.consume_literal(')')
        return logic_pb2.Primitive

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<=')
        _t655 = self.parse_term()
        left154 = _t655
        _t656 = self.parse_term()
        right155 = _t656
        self.consume_literal(')')
        return logic_pb2.Primitive

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>')
        _t657 = self.parse_term()
        left156 = _t657
        _t658 = self.parse_term()
        right157 = _t658
        self.consume_literal(')')
        return logic_pb2.Primitive

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>=')
        _t659 = self.parse_term()
        left158 = _t659
        _t660 = self.parse_term()
        right159 = _t660
        self.consume_literal(')')
        return logic_pb2.Primitive

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('+')
        _t661 = self.parse_term()
        left160 = _t661
        _t662 = self.parse_term()
        right161 = _t662
        _t663 = self.parse_term()
        result162 = _t663
        self.consume_literal(')')
        return logic_pb2.Primitive

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('-')
        _t664 = self.parse_term()
        left163 = _t664
        _t665 = self.parse_term()
        right164 = _t665
        _t666 = self.parse_term()
        result165 = _t666
        self.consume_literal(')')
        return logic_pb2.Primitive

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('*')
        _t667 = self.parse_term()
        left166 = _t667
        _t668 = self.parse_term()
        right167 = _t668
        _t669 = self.parse_term()
        result168 = _t669
        self.consume_literal(')')
        return logic_pb2.Primitive

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('/')
        _t670 = self.parse_term()
        left169 = _t670
        _t671 = self.parse_term()
        right170 = _t671
        _t672 = self.parse_term()
        result171 = _t672
        self.consume_literal(')')
        return logic_pb2.Primitive

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_literal('true', 0):
            _t688 = 1
        else:
            if self.match_lookahead_literal('missing', 0):
                _t696 = 1
            else:
                if self.match_lookahead_literal('false', 0):
                    _t700 = 1
                else:
                    if self.match_lookahead_literal('(', 0):
                        _t702 = 1
                    else:
                        if self.match_lookahead_literal('#', 0):
                            _t703 = 0
                        else:
                            _t703 = (self.match_lookahead_terminal('UINT128', 0) or (self.match_lookahead_terminal('SYMBOL', 0) or (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or -1)))))))
                        _t702 = _t703
                    _t700 = _t702
                _t696 = _t700
            _t688 = _t696
        prediction172 = _t688
        if prediction172 == 1:
            _t705 = self.parse_term()
            value174 = _t705
            _t704 = logic_pb2.RelTerm
        else:
            if prediction172 == 0:
                _t707 = self.parse_specialized_value()
                value173 = _t707
                _t706 = logic_pb2.RelTerm
            else:
                raise ParseError(f"{'Unexpected token in rel_term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t706 = None
            _t704 = _t706
        return _t704

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal('#')
        _t708 = self.parse_value()
        value175 = _t708
        return value175

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        self.consume_literal('(')
        self.consume_literal('rel_atom')
        _t709 = self.parse_name()
        name176 = _t709
        xs177 = []
        cond178 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond178:
            _t710 = self.parse_rel_term()
            xs177.append(_t710)
            cond178 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms179 = xs177
        self.consume_literal(')')
        return logic_pb2.RelAtom

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal('(')
        self.consume_literal('cast')
        _t711 = self.parse_term()
        input180 = _t711
        _t712 = self.parse_term()
        result181 = _t712
        self.consume_literal(')')
        return logic_pb2.Cast

    def parse_attrs(self) -> list[logic_pb2.Attribute]:
        self.consume_literal('(')
        self.consume_literal('attrs')
        xs182 = []
        cond183 = self.match_lookahead_literal('(', 0)
        while cond183:
            _t713 = self.parse_attribute()
            xs182.append(_t713)
            cond183 = self.match_lookahead_literal('(', 0)
        x184 = xs182
        self.consume_literal(')')
        return x184

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal('(')
        self.consume_literal('attribute')
        _t714 = self.parse_name()
        name185 = _t714
        xs186 = []
        cond187 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond187:
            _t715 = self.parse_value()
            xs186.append(_t715)
            cond187 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        args188 = xs186
        self.consume_literal(')')
        return logic_pb2.Attribute

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal('(')
        self.consume_literal('algorithm')
        xs189 = []
        cond190 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        while cond190:
            _t716 = self.parse_relation_id()
            xs189.append(_t716)
            cond190 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        global191 = xs189
        _t717 = self.parse_script()
        body192 = _t717
        self.consume_literal(')')
        return logic_pb2.Algorithm

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal('(')
        self.consume_literal('script')
        xs193 = []
        cond194 = self.match_lookahead_literal('(', 0)
        while cond194:
            _t718 = self.parse_construct()
            xs193.append(_t718)
            cond194 = self.match_lookahead_literal('(', 0)
        constructs195 = xs193
        self.consume_literal(')')
        return logic_pb2.Script

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t727 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t731 = 1
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t733 = 1
                    else:
                        if self.match_lookahead_literal('loop', 1):
                            _t734 = 0
                        else:
                            _t734 = (self.match_lookahead_literal('break', 1) or (self.match_lookahead_literal('assign', 1) or -1))
                        _t733 = _t734
                    _t731 = _t733
                _t727 = _t731
            _t719 = _t727
        else:
            _t719 = -1
        prediction196 = _t719
        if prediction196 == 1:
            _t736 = self.parse_instruction()
            value198 = _t736
            _t735 = logic_pb2.Construct
        else:
            if prediction196 == 0:
                _t738 = self.parse_loop()
                value197 = _t738
                _t737 = logic_pb2.Construct
            else:
                raise ParseError(f"{'Unexpected token in construct'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t737 = None
            _t735 = _t737
        return _t735

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal('(')
        self.consume_literal('loop')
        _t739 = self.parse_init()
        init199 = _t739
        _t740 = self.parse_script()
        body200 = _t740
        self.consume_literal(')')
        return logic_pb2.Loop

    def parse_init(self) -> list[logic_pb2.Instruction]:
        self.consume_literal('(')
        self.consume_literal('init')
        xs201 = []
        cond202 = self.match_lookahead_literal('(', 0)
        while cond202:
            _t741 = self.parse_instruction()
            xs201.append(_t741)
            cond202 = self.match_lookahead_literal('(', 0)
        x203 = xs201
        self.consume_literal(')')
        return x203

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t747 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t748 = 4
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t749 = 3
                    else:
                        if self.match_lookahead_literal('break', 1):
                            _t750 = 2
                        else:
                            if self.match_lookahead_literal('assign', 1):
                                _t751 = 0
                            else:
                                _t751 = -1
                            _t750 = _t751
                        _t749 = _t750
                    _t748 = _t749
                _t747 = _t748
            _t742 = _t747
        else:
            _t742 = -1
        prediction204 = _t742
        if prediction204 == 4:
            _t753 = self.parse_monus_def()
            value209 = _t753
            _t752 = logic_pb2.Instruction
        else:
            if prediction204 == 3:
                _t755 = self.parse_monoid_def()
                value208 = _t755
                _t754 = logic_pb2.Instruction
            else:
                if prediction204 == 2:
                    _t757 = self.parse_break()
                    value207 = _t757
                    _t756 = logic_pb2.Instruction
                else:
                    if prediction204 == 1:
                        _t759 = self.parse_upsert()
                        value206 = _t759
                        _t758 = logic_pb2.Instruction
                    else:
                        if prediction204 == 0:
                            _t761 = self.parse_assign()
                            value205 = _t761
                            _t760 = logic_pb2.Instruction
                        else:
                            raise ParseError(f"{'Unexpected token in instruction'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t760 = None
                        _t758 = _t760
                    _t756 = _t758
                _t754 = _t756
            _t752 = _t754
        return _t752

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal('(')
        self.consume_literal('assign')
        _t762 = self.parse_relation_id()
        name210 = _t762
        _t763 = self.parse_abstraction()
        body211 = _t763
        if self.match_lookahead_literal('(', 0):
            _t765 = self.parse_attrs()
            _t764 = _t765
        else:
            _t764 = None
        attrs212 = _t764
        self.consume_literal(')')
        return logic_pb2.Assign

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal('(')
        self.consume_literal('upsert')
        _t766 = self.parse_relation_id()
        name213 = _t766
        _t767 = self.parse_abstraction_with_arity()
        abstraction_with_arity214 = _t767
        if self.match_lookahead_literal('(', 0):
            _t769 = self.parse_attrs()
            _t768 = _t769
        else:
            _t768 = None
        attrs215 = _t768
        self.consume_literal(')')
        abstraction = abstraction_with_arity214[0]
        arity = abstraction_with_arity214[1]
        return logic_pb2.Upsert

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal('(')
        _t770 = self.parse_bindings()
        bindings216 = _t770
        _t771 = self.parse_formula()
        formula217 = _t771
        self.consume_literal(')')
        return (logic_pb2.Abstraction, len(bindings216[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal('(')
        self.consume_literal('break')
        _t772 = self.parse_relation_id()
        name218 = _t772
        _t773 = self.parse_abstraction()
        body219 = _t773
        if self.match_lookahead_literal('(', 0):
            _t775 = self.parse_attrs()
            _t774 = _t775
        else:
            _t774 = None
        attrs220 = _t774
        self.consume_literal(')')
        return logic_pb2.Break

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal('(')
        self.consume_literal('monoid')
        _t776 = self.parse_monoid()
        monoid221 = _t776
        _t777 = self.parse_relation_id()
        name222 = _t777
        _t778 = self.parse_abstraction_with_arity()
        abstraction_with_arity223 = _t778
        if self.match_lookahead_literal('(', 0):
            _t780 = self.parse_attrs()
            _t779 = _t780
        else:
            _t779 = None
        attrs224 = _t779
        self.consume_literal(')')
        abstraction = abstraction_with_arity223[0]
        arity = abstraction_with_arity223[1]
        return logic_pb2.MonoidDef

    def parse_monoid(self) -> logic_pb2.Monoid:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('sum', 1):
                _t782 = 3
            else:
                if self.match_lookahead_literal('or', 1):
                    _t783 = 0
                else:
                    if self.match_lookahead_literal('min', 1):
                        _t785 = 1
                    else:
                        if self.match_lookahead_literal('max', 1):
                            _t786 = 2
                        else:
                            _t786 = -1
                        _t785 = _t786
                    _t783 = _t785
                _t782 = _t783
            _t781 = _t782
        else:
            _t781 = -1
        prediction225 = _t781
        if prediction225 == 3:
            _t788 = self.parse_sum_monoid()
            value229 = _t788
            _t787 = logic_pb2.Monoid
        else:
            if prediction225 == 2:
                _t790 = self.parse_max_monoid()
                value228 = _t790
                _t789 = logic_pb2.Monoid
            else:
                if prediction225 == 1:
                    _t792 = self.parse_min_monoid()
                    value227 = _t792
                    _t791 = logic_pb2.Monoid
                else:
                    if prediction225 == 0:
                        _t794 = self.parse_or_monoid()
                        value226 = _t794
                        _t793 = logic_pb2.Monoid
                    else:
                        raise ParseError(f"{'Unexpected token in monoid'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t793 = None
                    _t791 = _t793
                _t789 = _t791
            _t787 = _t789
        return _t787

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        self.consume_literal('(')
        self.consume_literal('or')
        self.consume_literal(')')
        return logic_pb2.OrMonoid

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        self.consume_literal('(')
        self.consume_literal('min')
        _t795 = self.parse_type()
        type230 = _t795
        self.consume_literal(')')
        return logic_pb2.MinMonoid

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        self.consume_literal('(')
        self.consume_literal('max')
        _t796 = self.parse_type()
        type231 = _t796
        self.consume_literal(')')
        return logic_pb2.MaxMonoid

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        self.consume_literal('(')
        self.consume_literal('sum')
        _t797 = self.parse_type()
        type232 = _t797
        self.consume_literal(')')
        return logic_pb2.SumMonoid

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal('(')
        self.consume_literal('monus')
        _t798 = self.parse_monoid()
        monoid233 = _t798
        _t799 = self.parse_relation_id()
        name234 = _t799
        _t800 = self.parse_abstraction_with_arity()
        abstraction_with_arity235 = _t800
        if self.match_lookahead_literal('(', 0):
            _t802 = self.parse_attrs()
            _t801 = _t802
        else:
            _t801 = None
        attrs236 = _t801
        self.consume_literal(')')
        abstraction = abstraction_with_arity235[0]
        arity = abstraction_with_arity235[1]
        return logic_pb2.MonusDef

    def parse_constraint(self) -> logic_pb2.Constraint:
        self.consume_literal('(')
        self.consume_literal('functional_dependency')
        _t803 = self.parse_relation_id()
        name237 = _t803
        _t804 = self.parse_abstraction()
        guard238 = _t804
        _t805 = self.parse_functional_dependency_keys()
        keys239 = _t805
        _t806 = self.parse_functional_dependency_values()
        values240 = _t806
        self.consume_literal(')')
        return logic_pb2.Constraint

    def parse_functional_dependency_keys(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('keys')
        xs241 = []
        cond242 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond242:
            _t807 = self.parse_var()
            xs241.append(_t807)
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
            _t808 = self.parse_var()
            xs244.append(_t808)
            cond245 = self.match_lookahead_terminal('SYMBOL', 0)
        x246 = xs244
        self.consume_literal(')')
        return x246

    def parse_data(self) -> logic_pb2.Data:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('rel_edb', 1):
                _t810 = 0
            else:
                if self.match_lookahead_literal('csvdata', 1):
                    _t811 = 2
                else:
                    _t811 = (self.match_lookahead_literal('be_tree_relation', 1) or -1)
                _t810 = _t811
            _t809 = _t810
        else:
            _t809 = -1
        prediction247 = _t809
        if prediction247 == 2:
            _t813 = self.parse_csv_data()
            value250 = _t813
            _t812 = logic_pb2.Data
        else:
            if prediction247 == 1:
                _t815 = self.parse_betree_relation()
                value249 = _t815
                _t814 = logic_pb2.Data
            else:
                if prediction247 == 0:
                    _t817 = self.parse_rel_edb()
                    value248 = _t817
                    _t816 = logic_pb2.Data
                else:
                    raise ParseError(f"{'Unexpected token in data'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t816 = None
                _t814 = _t816
            _t812 = _t814
        return _t812

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        self.consume_literal('(')
        self.consume_literal('rel_edb')
        _t818 = self.parse_relation_id()
        target_id251 = _t818
        xs252 = []
        cond253 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond253:
            _t819 = self.parse_name()
            xs252.append(_t819)
            cond253 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        path254 = xs252
        if self.match_lookahead_literal('(', 0):
            _t821 = self.parse_rel_edb_types()
            _t820 = _t821
        else:
            _t820 = None
        types255 = _t820
        self.consume_literal(')')
        return logic_pb2.RelEDB

    def parse_rel_edb_types(self) -> list[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('types')
        xs256 = []
        cond257 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond257:
            _t822 = self.parse_type()
            xs256.append(_t822)
            cond257 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        x258 = xs256
        self.consume_literal(')')
        return x258

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        _t823 = self.parse_be_tree_relation()
        x259 = _t823
        return x259

    def parse_be_tree_relation(self) -> logic_pb2.BeTreeRelation:
        self.consume_literal('(')
        self.consume_literal('be_tree_relation')
        _t824 = self.parse_relation_id()
        name260 = _t824
        _t825 = self.parse_be_tree_info()
        relation_info261 = _t825
        self.consume_literal(')')
        return logic_pb2.BeTreeRelation

    def parse_be_tree_info(self) -> logic_pb2.BeTreeInfo:
        self.consume_literal('(')
        self.consume_literal('be_tree_info')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('key_types', 1)):
            _t827 = self.parse_be_tree_info_key_types()
            _t826 = _t827
        else:
            _t826 = None
        key_types262 = _t826
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('value_types', 1)):
            _t829 = self.parse_be_tree_info_value_types()
            _t828 = _t829
        else:
            _t828 = None
        value_types263 = _t828
        _t830 = self.parse_be_tree_config()
        storage_config264 = _t830
        _t831 = self.parse_be_tree_locator()
        relation_locator265 = _t831
        self.consume_literal(')')
        return logic_pb2.BeTreeInfo

    def parse_be_tree_info_key_types(self) -> list[logic_pb2.Type]:
        self.consume_literal('(')
        self.consume_literal('key_types')
        xs266 = []
        cond267 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond267:
            _t832 = self.parse_type()
            xs266.append(_t832)
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
            _t833 = self.parse_type()
            xs269.append(_t833)
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
        return logic_pb2.BeTreeConfig

    def parse_be_tree_locator(self) -> logic_pb2.BeTreeLocator:
        self.consume_literal('(')
        self.consume_literal('be_tree_locator')
        element_count276 = self.consume_terminal('INT')
        tree_height277 = self.consume_terminal('INT')
        self.consume_literal(')')
        return logic_pb2.BeTreeLocator

    def parse_csv_data(self) -> logic_pb2.CSVData:
        _t834 = self.parse_csvdata()
        x278 = _t834
        return x278

    def parse_csvdata(self) -> logic_pb2.CSVData:
        self.consume_literal('(')
        self.consume_literal('csvdata')
        _t835 = self.parse_csvlocator()
        locator279 = _t835
        _t836 = self.parse_csv_config()
        config280 = _t836
        xs281 = []
        cond282 = self.match_lookahead_literal('(', 0)
        while cond282:
            _t837 = self.parse_csv_column()
            xs281.append(_t837)
            cond282 = self.match_lookahead_literal('(', 0)
        columns283 = xs281
        _t838 = self.parse_name()
        asof284 = _t838
        self.consume_literal(')')
        return logic_pb2.CSVData

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        self.consume_literal('(')
        self.consume_literal('csvlocator')
        xs285 = []
        cond286 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond286:
            _t839 = self.parse_name()
            xs285.append(_t839)
            cond286 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        paths287 = xs285
        _t840 = self.parse_name()
        inline_data288 = _t840
        self.consume_literal(')')
        return logic_pb2.CSVLocator

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        self.consume_literal('(')
        self.consume_literal('csv_config')
        header_row289 = self.consume_terminal('INT')
        skip290 = self.consume_terminal('INT')
        _t841 = self.parse_name()
        new_line291 = _t841
        _t842 = self.parse_name()
        delimiter292 = _t842
        _t843 = self.parse_name()
        quotechar293 = _t843
        _t844 = self.parse_name()
        escapechar294 = _t844
        _t845 = self.parse_name()
        comment295 = _t845
        xs296 = []
        cond297 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond297:
            _t846 = self.parse_name()
            xs296.append(_t846)
            cond297 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        missing_strings298 = xs296
        _t847 = self.parse_name()
        decimal_separator299 = _t847
        _t848 = self.parse_name()
        encoding300 = _t848
        _t849 = self.parse_name()
        compression301 = _t849
        self.consume_literal(')')
        return logic_pb2.CSVConfig

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        self.consume_literal('(')
        self.consume_literal('csv_column')
        _t850 = self.parse_name()
        column_name302 = _t850
        _t851 = self.parse_relation_id()
        target_id303 = _t851
        xs304 = []
        cond305 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        while cond305:
            _t852 = self.parse_type()
            xs304.append(_t852)
            cond305 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types306 = xs304
        self.consume_literal(')')
        return logic_pb2.CSVColumn

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal('(')
        self.consume_literal('undefine')
        _t853 = self.parse_fragment_id()
        fragment_id307 = _t853
        self.consume_literal(')')
        return transactions_pb2.Undefine

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal('(')
        self.consume_literal('context')
        xs308 = []
        cond309 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        while cond309:
            _t854 = self.parse_relation_id()
            xs308.append(_t854)
            cond309 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        relations310 = xs308
        self.consume_literal(')')
        return transactions_pb2.Context

    def parse_epoch_reads(self) -> list[transactions_pb2.Read]:
        self.consume_literal('(')
        self.consume_literal('reads')
        xs311 = []
        cond312 = self.match_lookahead_literal('(', 0)
        while cond312:
            _t855 = self.parse_read()
            xs311.append(_t855)
            cond312 = self.match_lookahead_literal('(', 0)
        x313 = xs311
        self.consume_literal(')')
        return x313

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('what_if', 1):
                _t857 = 2
            else:
                if self.match_lookahead_literal('output', 1):
                    _t861 = 1
                else:
                    if self.match_lookahead_literal('export', 1):
                        _t862 = 4
                    else:
                        if self.match_lookahead_literal('demand', 1):
                            _t863 = 0
                        else:
                            if self.match_lookahead_literal('abort', 1):
                                _t864 = 3
                            else:
                                _t864 = -1
                            _t863 = _t864
                        _t862 = _t863
                    _t861 = _t862
                _t857 = _t861
            _t856 = _t857
        else:
            _t856 = -1
        prediction314 = _t856
        if prediction314 == 4:
            _t866 = self.parse_export()
            value319 = _t866
            _t865 = transactions_pb2.Read
        else:
            if prediction314 == 3:
                _t868 = self.parse_abort()
                value318 = _t868
                _t867 = transactions_pb2.Read
            else:
                if prediction314 == 2:
                    _t870 = self.parse_what_if()
                    value317 = _t870
                    _t869 = transactions_pb2.Read
                else:
                    if prediction314 == 1:
                        _t872 = self.parse_output()
                        value316 = _t872
                        _t871 = transactions_pb2.Read
                    else:
                        if prediction314 == 0:
                            _t874 = self.parse_demand()
                            value315 = _t874
                            _t873 = transactions_pb2.Read
                        else:
                            raise ParseError(f"{'Unexpected token in read'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t873 = None
                        _t871 = _t873
                    _t869 = _t871
                _t867 = _t869
            _t865 = _t867
        return _t865

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal('(')
        self.consume_literal('demand')
        _t875 = self.parse_relation_id()
        relation_id320 = _t875
        self.consume_literal(')')
        return transactions_pb2.Demand

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal('(')
        self.consume_literal('output')
        if self.match_lookahead_terminal('COLON_SYMBOL', 0):
            _t877 = self.parse_name()
            _t876 = _t877
        else:
            _t876 = None
        name321 = _t876
        _t878 = self.parse_relation_id()
        relation_id322 = _t878
        self.consume_literal(')')
        return transactions_pb2.Output

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal('(')
        self.consume_literal('what_if')
        _t879 = self.parse_name()
        branch323 = _t879
        _t880 = self.parse_epoch()
        epoch324 = _t880
        self.consume_literal(')')
        return transactions_pb2.WhatIf

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal('(')
        self.consume_literal('abort')
        if self.match_lookahead_terminal('COLON_SYMBOL', 0):
            _t882 = self.parse_name()
            _t881 = _t882
        else:
            _t881 = None
        name325 = _t881
        _t883 = self.parse_relation_id()
        relation_id326 = _t883
        self.consume_literal(')')
        return transactions_pb2.Abort

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal('(')
        self.consume_literal('export')
        _t884 = self.parse_export_csv_config()
        config327 = _t884
        self.consume_literal(')')
        return transactions_pb2.Export

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal('(')
        self.consume_literal('export_csv_config')
        _t885 = self.parse_export_csv_path()
        path328 = _t885
        _t886 = self.parse_export_csv_columns()
        columns329 = _t886
        _t887 = self.parse_config_dict()
        config330 = _t887
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
            _t888 = self.parse_export_csv_column()
            xs332.append(_t888)
            cond333 = self.match_lookahead_literal('(', 0)
        x334 = xs332
        self.consume_literal(')')
        return x334

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        name335 = self.consume_terminal('STRING')
        _t889 = self.parse_relation_id()
        relation_id336 = _t889
        self.consume_literal(')')
        return transactions_pb2.ExportCSVColumn


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
