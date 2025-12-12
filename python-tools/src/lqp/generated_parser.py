"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.


Command: python-tools/src/meta/proto_tool.py proto/relationalai/lqp/v1/fragments.proto proto/relationalai/lqp/v1/logic.proto proto/relationalai/lqp/v1/transactions.proto --parser python --output python-tools/src/lqp/generated_parser.py
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
            ('STRING', r'"(?:[^"\\]|\\.)*"', lambda x: self.scan_string(x)),
            ('INT128', r'[-]?\d+i128', lambda x: self.scan_int128(x)),
            ('INT', r'[-]?\d+', lambda x: self.scan_int(x)),
            ('UINT128', r'0x[0-9a-fA-F]+', lambda x: self.scan_uint128(x)),
            ('DECIMAL', r'[-]?\d+\.\d+d\d+', lambda x: self.scan_decimal(x)),
            ('FLOAT', r'(?:[-]?\d+\.\d+|inf|nan)', lambda x: self.scan_float(x)),
            ('SYMBOL', r'[a-zA-Z_][a-zA-Z0-9_.-]*', lambda x: self.scan_symbol(x)),
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

            matched = False

            # Scan for literals first since they should have priority over symbols
            for literal in self._get_literals():
                if self.input[self.pos:].startswith(literal):
                    # Check word boundary for alphanumeric keywords
                    if literal[0].isalnum():
                        end_pos = self.pos + len(literal)
                        if end_pos < len(self.input) and self.input[end_pos].isalnum():
                            continue
                    self.tokens.append(Token('LITERAL', literal, self.pos))
                    self.pos += len(literal)
                    matched = True
                    break

            # Scan for other tokens
            if not matched:
                for token_type, pattern, action in token_specs:
                    regex = re.compile(pattern)
                    match = regex.match(self.input, self.pos)
                    if match:
                        value = match.group(0)
                        self.tokens.append(Token(token_type, action(value), self.pos))
                        self.pos = match.end()
                        matched = True
                        break

            if not matched:
                raise ParseError(f'Unexpected character at position {{self.pos}}: {{self.input[self.pos]!r}}')

        self.tokens.append(Token('$', '', self.pos))

    def _get_literals(self) -> List[str]:
        """Get all literal strings from the grammar."""
        return [
            'functional_dependency',
            'export_csvconfig',
            'datetime_value',
            'decimal_value',
            'missing_value',
            'uint128_value',
            'int128_value',
            'transaction',
            'date_value',
            'debug_info',
            'max_monoid',
            'min_monoid',
            'sum_monoid',
            'algorithm',
            'attribute',
            'configure',
            'ivmconfig',
            'or_monoid',
            'primitive',
            'DATETIME',
            'datetime',
            'fragment',
            'undefine',
            'BOOLEAN',
            'DECIMAL',
            'MISSING',
            'UINT128',
            'UNKNOWN',
            'columns',
            'context',
            'missing',
            'relatom',
            'what_if',
            'INT128',
            'STRING',
            'assign',
            'column',
            'define',
            'demand',
            'exists',
            'export',
            'monoid',
            'output',
            'pragma',
            'reduce',
            'script',
            'upsert',
            'values',
            'writes',
            'FLOAT',
            'abort',
            'attrs',
            'break',
            'epoch',
            'false',
            'monus',
            'reads',
            'terms',
            'DATE',
            'args',
            'atom',
            'cast',
            'date',
            'init',
            'keys',
            'loop',
            'sync',
            'true',
            'INT',
            'MAX',
            'MIN',
            'SUM',
            'and',
            'def',
            'ffi',
            'ids',
            'not',
            '::',
            '<=',
            '>=',
            'OR',
            'or',
            '#',
            '(',
            ')',
            '*',
            '+',
            '-',
            '/',
            ':',
            '<',
            '=',
            '>',
            '[',
            ']',
            '{',
            '|',
            '}',
        ]

    @staticmethod
    def scan_symbol(s: str) -> str:
        """Parse SYMBOL token."""
        return s

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
        return logic_pb2.UInt128Value(value=uint128_val)

    @staticmethod
    def scan_int128(u: str) -> Any:
        """Parse INT128 token."""
        u = u[:-4]  # Remove the 'i128' suffix
        int128_val = int(u)
        return logic_pb2.Int128Value(value=int128_val)

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
        value = Decimal(parts[0])
        return logic_pb2.DecimalValue(precision=precision, scale=scale, value=value)


class Parser:
    """LL(k) recursive-descent parser with backtracking."""
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.id_to_debuginfo = {}
        self._current_fragment_id = None

    def lookahead(self, k: int = 0) -> Token:
        """Get lookahead token at offset k."""
        idx = self.pos + k
        return self.tokens[idx] if idx < len(self.tokens) else Token('$', '', -1)

    def consume_literal(self, expected: str) -> None:
        """Consume a literal token."""
        if not self.match_lookahead_literal(expected, 0):
            token = self.lookahead(0)
            raise ParseError(f'Expected literal {{expected!r}} but got {{token.type}}={{token.value!r}} at position {{token.pos}}')
        self.pos += 1

    def consume_terminal(self, expected: str) -> Any:
        """Consume a terminal token and return parsed value."""
        if not self.match_lookahead_terminal(expected, 0):
            token = self.lookahead(0)
            raise ParseError(f'Expected terminal {{expected}} but got {{token.type}} at position {{token.pos}}')
        token = self.lookahead(0)
        self.pos += 1
        return token.value

    def match_lookahead_literal(self, literal: str, k: int) -> bool:
        """Check if lookahead token at position k matches literal."""
        token = self.lookahead(k)
        return token.type == 'LITERAL' and token.value == literal

    def match_lookahead_terminal(self, terminal: str, k: int) -> bool:
        """Check if lookahead token at position k matches terminal."""
        token = self.lookahead(k)
        return token.type == terminal

    def construct_configure(self, config_dict: List[Tuple[str, logic_pb2.Value]]) -> Any:
        """Construct Configure from config dictionary."""
        # Build a dict from the list
        config = {}
        for k, v in config_dict:
            config[k] = v

        # Extract maintenance level
        maintenance_level_val = config.get('ivm.maintenance_level')
        if maintenance_level_val:
            if maintenance_level_val.HasField('string_value'):
                level_str = maintenance_level_val.string_value.upper()
                # Map short names to full enum names
                if level_str in ('OFF', 'AUTO', 'ALL'):
                    maintenance_level = f'MAINTENANCE_LEVEL_{level_str}'
                else:
                    maintenance_level = level_str
            else:
                maintenance_level = 'MAINTENANCE_LEVEL_OFF'
        else:
            maintenance_level = 'MAINTENANCE_LEVEL_OFF'

        # Extract semantics version
        semantics_version_val = config.get('semantics_version')
        if semantics_version_val and semantics_version_val.HasField('int_value'):
            semantics_version = semantics_version_val.int_value
        else:
            semantics_version = 0

        # Create IVMConfig and Configure
        ivm_config = transactions_pb2.IVMConfig(level=maintenance_level)
        return transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)

    def export_csv_config(self, path: str, columns: List[Any], config_dict: List[Tuple[str, logic_pb2.Value]]) -> Any:
        """Construct ExportCsvConfig from path, columns, and config dictionary."""
        # Build a dict from the list
        config = {}
        for k, v in config_dict:
            config[k] = v

        # Extract path string
        path_str = path

        # Build kwargs dict for optional fields
        kwargs = {}

        # Extract optional fields
        partition_size_val = config.get('partition_size')
        if partition_size_val and partition_size_val.HasField('int_value'):
            kwargs['partition_size'] = partition_size_val.int_value

        compression_val = config.get('compression')
        if compression_val and compression_val.HasField('string_value'):
            kwargs['compression'] = compression_val.string_value

        header_val = config.get('syntax_header_row')
        if header_val and header_val.HasField('boolean_value'):
            kwargs['syntax_header_row'] = header_val.boolean_value

        missing_val = config.get('syntax_missing_string')
        if missing_val and missing_val.HasField('string_value'):
            kwargs['syntax_missing_string'] = missing_val.string_value

        delim_val = config.get('syntax_delim')
        if delim_val and delim_val.HasField('string_value'):
            kwargs['syntax_delim'] = delim_val.string_value

        quote_val = config.get('syntax_quotechar')
        if quote_val and quote_val.HasField('string_value'):
            kwargs['syntax_quotechar'] = quote_val.string_value

        escape_val = config.get('syntax_escapechar')
        if escape_val and escape_val.HasField('string_value'):
            kwargs['syntax_escapechar'] = escape_val.string_value

        return transactions_pb2.ExportCSVConfig(path=path_str, data_columns=columns, **kwargs)

    def construct_fragment(self, fragment_id: fragments_pb2.FragmentId, declarations: List[logic_pb2.Declaration]) -> fragments_pb2.Fragment:
        """Construct Fragment from fragment_id, declarations, and debug info from parser state."""
        # Get the debug info dict for this fragment_id (use id bytes as key)
        debug_info_dict = self.id_to_debuginfo.get(fragment_id.id, {})

        # Convert dict to parallel arrays
        ids = []
        orig_names = []
        for relation_id, orig_name in debug_info_dict.items():
            ids.append(relation_id)
            orig_names.append(orig_name)

        # Create DebugInfo
        debug_info = fragments_pb2.DebugInfo(ids=ids, orig_names=orig_names)

        # Create and return Fragment
        return fragments_pb2.Fragment(id=fragment_id, declarations=declarations, debug_info=debug_info)

    def parse_transaction(self) -> transactions_pb2.Transaction:
        self.consume_literal('(')
        self.consume_literal('transaction')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('configure', 1)):
            _t268 = self.parse_configure()
            _t267 = _t268
        else:
            _t267 = None
        configure0 = _t267
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('sync', 1)):
            _t270 = self.parse_sync()
            _t269 = _t270
        else:
            _t269 = None
        sync1 = _t269
        xs2 = []
        cond3 = self.match_lookahead_literal('(', 0)
        while cond3:
            _t271 = self.parse_epoch()
            xs2.append(_t271)
            cond3 = self.match_lookahead_literal('(', 0)
        epochs4 = xs2
        self.consume_literal(')')
        _t272 = transactions_pb2.Transaction(epochs=epochs4, configure=(configure0 if configure0 is not None else self.construct_configure([])), sync=sync1)
        return _t272

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal('(')
        self.consume_literal('configure')
        _t273 = self.parse_config_dict()
        config_dict5 = _t273
        self.consume_literal(')')
        return self.construct_configure(config_dict5)

    def parse_config_dict(self) -> list[tuple[str, logic_pb2.Value]]:
        self.consume_literal('{')
        xs6 = []
        cond7 = self.match_lookahead_literal(':', 0)
        while cond7:
            _t274 = self.parse_config_key_value()
            xs6.append(_t274)
            cond7 = self.match_lookahead_literal(':', 0)
        config_key_value8 = xs6
        self.consume_literal('}')
        return config_key_value8

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(':')
        symbol9 = self.consume_terminal('SYMBOL')
        _t275 = self.parse_value()
        value10 = _t275
        return (symbol9, value10,)

    def parse_value(self) -> logic_pb2.Value:
        if self.match_lookahead_terminal('UINT128', 0):
            _t276 = 5
        else:
            if self.match_lookahead_terminal('STRING', 0):
                _t277 = 2
            else:
                if self.match_lookahead_terminal('INT128', 0):
                    _t278 = 6
                else:
                    if self.match_lookahead_terminal('INT', 0):
                        _t279 = 3
                    else:
                        if self.match_lookahead_terminal('FLOAT', 0):
                            _t280 = 4
                        else:
                            if self.match_lookahead_terminal('DECIMAL', 0):
                                _t281 = 7
                            else:
                                if self.match_lookahead_literal('true', 0):
                                    _t282 = 9
                                else:
                                    if self.match_lookahead_literal('missing', 0):
                                        _t283 = 8
                                    else:
                                        if self.match_lookahead_literal('false', 0):
                                            _t284 = 10
                                        else:
                                            if self.match_lookahead_literal('(', 0):
                                                if self.match_lookahead_literal('datetime', 1):
                                                    _t287 = 1
                                                else:
                                                    if self.match_lookahead_literal('date', 1):
                                                        _t288 = 0
                                                    else:
                                                        _t288 = -1
                                                    _t287 = _t288
                                                _t285 = _t287
                                            else:
                                                _t285 = -1
                                            _t284 = _t285
                                        _t283 = _t284
                                    _t282 = _t283
                                _t281 = _t282
                            _t280 = _t281
                        _t279 = _t280
                    _t278 = _t279
                _t277 = _t278
            _t276 = _t277
        prediction11 = _t276
        if prediction11 == 10:
            self.consume_literal('false')
            _t290 = logic_pb2.Value(boolean_value=False)
            _t289 = _t290
        else:
            if prediction11 == 9:
                self.consume_literal('true')
                _t292 = logic_pb2.Value(boolean_value=True)
                _t291 = _t292
            else:
                if prediction11 == 8:
                    self.consume_literal('missing')
                    _t294 = logic_pb2.MissingValue()
                    _t295 = logic_pb2.Value(missing_value=_t294)
                    _t293 = _t295
                else:
                    if prediction11 == 7:
                        value19 = self.consume_terminal('DECIMAL')
                        _t297 = logic_pb2.Value(decimal_value=value19)
                        _t296 = _t297
                    else:
                        if prediction11 == 6:
                            value18 = self.consume_terminal('INT128')
                            _t299 = logic_pb2.Value(int128_value=value18)
                            _t298 = _t299
                        else:
                            if prediction11 == 5:
                                value17 = self.consume_terminal('UINT128')
                                _t301 = logic_pb2.Value(uint128_value=value17)
                                _t300 = _t301
                            else:
                                if prediction11 == 4:
                                    value16 = self.consume_terminal('FLOAT')
                                    _t303 = logic_pb2.Value(float_value=value16)
                                    _t302 = _t303
                                else:
                                    if prediction11 == 3:
                                        value15 = self.consume_terminal('INT')
                                        _t305 = logic_pb2.Value(int_value=value15)
                                        _t304 = _t305
                                    else:
                                        if prediction11 == 2:
                                            value14 = self.consume_terminal('STRING')
                                            _t307 = logic_pb2.Value(string_value=value14)
                                            _t306 = _t307
                                        else:
                                            if prediction11 == 1:
                                                _t309 = self.parse_datetime()
                                                value13 = _t309
                                                _t310 = logic_pb2.Value(datetime_value=value13)
                                                _t308 = _t310
                                            else:
                                                if prediction11 == 0:
                                                    _t312 = self.parse_date()
                                                    value12 = _t312
                                                    _t313 = logic_pb2.Value(date_value=value12)
                                                    _t311 = _t313
                                                else:
                                                    raise ParseError('Unexpected token in value' + ": {self.lookahead(0)}")
                                                    _t311 = None
                                                _t308 = _t311
                                            _t306 = _t308
                                        _t304 = _t306
                                    _t302 = _t304
                                _t300 = _t302
                            _t298 = _t300
                        _t296 = _t298
                    _t293 = _t296
                _t291 = _t293
            _t289 = _t291
        return _t289

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal('(')
        self.consume_literal('date')
        year20 = self.consume_terminal('INT')
        month21 = self.consume_terminal('INT')
        day22 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t314 = logic_pb2.DateValue(year=year20, month=month21, day=day22)
        return _t314

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        self.consume_literal('(')
        self.consume_literal('datetime')
        year23 = self.consume_terminal('INT')
        month24 = self.consume_terminal('INT')
        day25 = self.consume_terminal('INT')
        hour26 = self.consume_terminal('INT')
        minute27 = self.consume_terminal('INT')
        second28 = self.consume_terminal('INT')
        if self.match_lookahead_terminal('INT', 0):
            _t315 = self.consume_terminal('INT')
        else:
            _t315 = None
        microsecond29 = _t315
        self.consume_literal(')')
        if microsecond29 is None:
            _t316 = 0
        else:
            _t316 = microsecond29
        _t317 = logic_pb2.DateTimeValue(year=year23, month=month24, day=day25, hour=hour26, minute=minute27, second=second28, microsecond=_t316)
        return _t317

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal('(')
        self.consume_literal('sync')
        xs30 = []
        cond31 = self.match_lookahead_literal(':', 0)
        while cond31:
            _t318 = self.parse_fragment_id()
            xs30.append(_t318)
            cond31 = self.match_lookahead_literal(':', 0)
        fragments32 = xs30
        self.consume_literal(')')
        _t319 = transactions_pb2.Sync(fragments=fragments32)
        return _t319

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        self.consume_literal(':')
        symbol33 = self.consume_terminal('SYMBOL')
        return fragments_pb2.FragmentId(id=symbol33.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal('(')
        self.consume_literal('epoch')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('writes', 1)):
            _t321 = self.parse_epoch_writes()
            _t320 = _t321
        else:
            _t320 = None
        writes34 = _t320
        if self.match_lookahead_literal('(', 0):
            _t323 = self.parse_epoch_reads()
            _t322 = _t323
        else:
            _t322 = None
        reads35 = _t322
        self.consume_literal(')')
        _t324 = transactions_pb2.Epoch(writes=(writes34 if writes34 is not None else []), reads=(reads35 if reads35 is not None else []))
        return _t324

    def parse_epoch_writes(self) -> list[transactions_pb2.Write]:
        self.consume_literal('(')
        self.consume_literal('writes')
        xs36 = []
        cond37 = self.match_lookahead_literal('(', 0)
        while cond37:
            _t325 = self.parse_write()
            xs36.append(_t325)
            cond37 = self.match_lookahead_literal('(', 0)
        value38 = xs36
        self.consume_literal(')')
        return value38

    def parse_write(self) -> transactions_pb2.Write:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('undefine', 1):
                _t329 = 1
            else:
                if self.match_lookahead_literal('define', 1):
                    _t330 = 0
                else:
                    if self.match_lookahead_literal('context', 1):
                        _t331 = 2
                    else:
                        _t331 = -1
                    _t330 = _t331
                _t329 = _t330
            _t326 = _t329
        else:
            _t326 = -1
        prediction39 = _t326
        if prediction39 == 2:
            _t333 = self.parse_context()
            value42 = _t333
            _t334 = transactions_pb2.Write(context=value42)
            _t332 = _t334
        else:
            if prediction39 == 1:
                _t336 = self.parse_undefine()
                value41 = _t336
                _t337 = transactions_pb2.Write(undefine=value41)
                _t335 = _t337
            else:
                if prediction39 == 0:
                    _t339 = self.parse_define()
                    value40 = _t339
                    _t340 = transactions_pb2.Write(define=value40)
                    _t338 = _t340
                else:
                    raise ParseError('Unexpected token in write' + ": {self.lookahead(0)}")
                    _t338 = None
                _t335 = _t338
            _t332 = _t335
        return _t332

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal('(')
        self.consume_literal('define')
        _t341 = self.parse_fragment()
        fragment43 = _t341
        self.consume_literal(')')
        _t342 = transactions_pb2.Define(fragment=fragment43)
        return _t342

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal('(')
        self.consume_literal('fragment')
        _t343 = self.parse_fragment_id()
        fragment_id44 = _t343
        xs45 = []
        cond46 = self.match_lookahead_literal('(', 0)
        while cond46:
            _t344 = self.parse_declaration()
            xs45.append(_t344)
            cond46 = self.match_lookahead_literal('(', 0)
        declarations47 = xs45
        self.consume_literal(')')
        return self.construct_fragment(fragment_id44, declarations47)

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('functional_dependency', 1):
                _t346 = 2
            else:
                if self.match_lookahead_literal('def', 1):
                    _t347 = 0
                else:
                    _t347 = (self.match_lookahead_literal('algorithm', 1) or -1)
                _t346 = _t347
            _t345 = _t346
        else:
            _t345 = -1
        prediction48 = _t345
        if prediction48 == 2:
            _t349 = self.parse_constraint()
            value51 = _t349
            _t350 = logic_pb2.Declaration(constraint=value51)
            _t348 = _t350
        else:
            if prediction48 == 1:
                _t352 = self.parse_algorithm()
                value50 = _t352
                _t353 = logic_pb2.Declaration(algorithm=value50)
                _t351 = _t353
            else:
                if prediction48 == 0:
                    _t355 = self.parse_def()
                    value49 = _t355
                    _t356 = logic_pb2.Declaration(**{'def': value49})
                    _t354 = _t356
                else:
                    raise ParseError('Unexpected token in declaration' + ": {self.lookahead(0)}")
                    _t354 = None
                _t351 = _t354
            _t348 = _t351
        return _t348

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal('(')
        self.consume_literal('def')
        _t357 = self.parse_relation_id()
        name52 = _t357
        _t358 = self.parse_abstraction()
        body53 = _t358
        if self.match_lookahead_literal('(', 0):
            _t360 = self.parse_attrs()
            _t359 = _t360
        else:
            _t359 = None
        attrs54 = _t359
        self.consume_literal(')')
        _t361 = logic_pb2.Def(name=name52, body=body53, attrs=(attrs54 if attrs54 is not None else []))
        return _t361

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_terminal('INT', 0):
            _t363 = 1
        else:
            if self.match_lookahead_literal(':', 0):
                _t364 = 0
            else:
                _t364 = -1
            _t363 = _t364
        prediction55 = _t363
        if prediction55 == 1:
            INT57 = self.consume_terminal('INT')
            _t365 = logic_pb2.RelationId(id_low=INT57 & 0xFFFFFFFFFFFFFFFF, id_high=(INT57 >> 64) & 0xFFFFFFFFFFFFFFFF)
        else:
            if prediction55 == 0:
                self.consume_literal(':')
                symbol56 = self.consume_terminal('SYMBOL')
                _t366 = logic_pb2.RelationId(id_low=int(hashlib.sha256(symbol56.encode()).hexdigest()[:16], 16) & 0xFFFFFFFFFFFFFFFF, id_high=(int(hashlib.sha256(symbol56.encode()).hexdigest()[:16], 16) >> 64) & 0xFFFFFFFFFFFFFFFF)
            else:
                raise ParseError('Unexpected token in relation_id' + ": {self.lookahead(0)}")
                _t366 = None
            _t365 = _t366
        return _t365

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal('(')
        _t367 = self.parse_bindings()
        bindings58 = _t367
        _t368 = self.parse_formula()
        formula59 = _t368
        self.consume_literal(')')
        _t369 = logic_pb2.Abstraction(vars=(bindings58[0] + (bindings58[1] if bindings58[1] is not None else [])), value=formula59)
        return _t369

    def parse_bindings(self) -> tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]:
        self.consume_literal('[')
        xs60 = []
        cond61 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond61:
            _t370 = self.parse_binding()
            xs60.append(_t370)
            cond61 = self.match_lookahead_terminal('SYMBOL', 0)
        keys62 = xs60
        if self.match_lookahead_literal('|', 0):
            _t372 = self.parse_value_bindings()
            _t371 = _t372
        else:
            _t371 = None
        values63 = _t371
        self.consume_literal(']')
        return (keys62, values63,)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol64 = self.consume_terminal('SYMBOL')
        self.consume_literal('::')
        _t373 = self.parse_type()
        type65 = _t373
        _t374 = logic_pb2.Var(name=symbol64)
        _t375 = logic_pb2.Binding(var=_t374, type=type65)
        return _t375

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal('UNKNOWN', 0):
            _t376 = 0
        else:
            if self.match_lookahead_literal('STRING', 0):
                _t384 = 1
            else:
                if self.match_lookahead_literal('MISSING', 0):
                    _t385 = 8
                else:
                    if self.match_lookahead_literal('INT128', 0):
                        _t386 = 5
                    else:
                        if self.match_lookahead_literal('INT', 0):
                            _t387 = 2
                        else:
                            if self.match_lookahead_literal('FLOAT', 0):
                                _t388 = 3
                            else:
                                if self.match_lookahead_literal('DATE', 0):
                                    _t389 = 6
                                else:
                                    if self.match_lookahead_literal('BOOLEAN', 0):
                                        _t390 = 10
                                    else:
                                        if self.match_lookahead_literal('(', 0):
                                            _t391 = 9
                                        else:
                                            _t391 = -1
                                        _t390 = _t391
                                    _t389 = _t390
                                _t388 = _t389
                            _t387 = _t388
                        _t386 = _t387
                    _t385 = _t386
                _t384 = _t385
            _t376 = _t384
        prediction66 = _t376
        if prediction66 == 10:
            _t393 = self.parse_boolean_type()
            value77 = _t393
            _t394 = logic_pb2.Type(boolean_type=value77)
            _t392 = _t394
        else:
            if prediction66 == 9:
                _t396 = self.parse_decimal_type()
                value76 = _t396
                _t397 = logic_pb2.Type(decimal_type=value76)
                _t395 = _t397
            else:
                if prediction66 == 8:
                    _t399 = self.parse_missing_type()
                    value75 = _t399
                    _t400 = logic_pb2.Type(missing_type=value75)
                    _t398 = _t400
                else:
                    if prediction66 == 7:
                        _t402 = self.parse_datetime_type()
                        value74 = _t402
                        _t403 = logic_pb2.Type(datetime_type=value74)
                        _t401 = _t403
                    else:
                        if prediction66 == 6:
                            _t405 = self.parse_date_type()
                            value73 = _t405
                            _t406 = logic_pb2.Type(date_type=value73)
                            _t404 = _t406
                        else:
                            if prediction66 == 5:
                                _t408 = self.parse_int128_type()
                                value72 = _t408
                                _t409 = logic_pb2.Type(int128_type=value72)
                                _t407 = _t409
                            else:
                                if prediction66 == 4:
                                    _t411 = self.parse_uint128_type()
                                    value71 = _t411
                                    _t412 = logic_pb2.Type(uint128_type=value71)
                                    _t410 = _t412
                                else:
                                    if prediction66 == 3:
                                        _t414 = self.parse_float_type()
                                        value70 = _t414
                                        _t415 = logic_pb2.Type(float_type=value70)
                                        _t413 = _t415
                                    else:
                                        if prediction66 == 2:
                                            _t417 = self.parse_int_type()
                                            value69 = _t417
                                            _t418 = logic_pb2.Type(int_type=value69)
                                            _t416 = _t418
                                        else:
                                            if prediction66 == 1:
                                                _t420 = self.parse_string_type()
                                                value68 = _t420
                                                _t421 = logic_pb2.Type(string_type=value68)
                                                _t419 = _t421
                                            else:
                                                if prediction66 == 0:
                                                    _t423 = self.parse_unspecified_type()
                                                    value67 = _t423
                                                    _t424 = logic_pb2.Type(unspecified_type=value67)
                                                    _t422 = _t424
                                                else:
                                                    raise ParseError('Unexpected token in type' + ": {self.lookahead(0)}")
                                                    _t422 = None
                                                _t419 = _t422
                                            _t416 = _t419
                                        _t413 = _t416
                                    _t410 = _t413
                                _t407 = _t410
                            _t404 = _t407
                        _t401 = _t404
                    _t398 = _t401
                _t395 = _t398
            _t392 = _t395
        return _t392

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        self.consume_literal('UNKNOWN')
        _t425 = logic_pb2.UnspecifiedType()
        return _t425

    def parse_string_type(self) -> logic_pb2.StringType:
        self.consume_literal('STRING')
        _t426 = logic_pb2.StringType()
        return _t426

    def parse_int_type(self) -> logic_pb2.IntType:
        self.consume_literal('INT')
        _t427 = logic_pb2.IntType()
        return _t427

    def parse_float_type(self) -> logic_pb2.FloatType:
        self.consume_literal('FLOAT')
        _t428 = logic_pb2.FloatType()
        return _t428

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        self.consume_literal('INT128')
        _t429 = logic_pb2.Int128Type()
        return _t429

    def parse_date_type(self) -> logic_pb2.DateType:
        self.consume_literal('DATE')
        _t430 = logic_pb2.DateType()
        return _t430

    def parse_missing_type(self) -> logic_pb2.MissingType:
        self.consume_literal('MISSING')
        _t431 = logic_pb2.MissingType()
        return _t431

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        self.consume_literal('(')
        self.consume_literal('DECIMAL')
        precision78 = self.consume_terminal('INT')
        scale79 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t432 = logic_pb2.DecimalType(precision=precision78, scale=scale79)
        return _t432

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal('BOOLEAN')
        _t433 = logic_pb2.BooleanType()
        return _t433

    def parse_value_bindings(self) -> list[logic_pb2.Binding]:
        self.consume_literal('|')
        xs80 = []
        cond81 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond81:
            _t434 = self.parse_binding()
            xs80.append(_t434)
            cond81 = self.match_lookahead_terminal('SYMBOL', 0)
        values82 = xs80
        return values82

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('true', 1):
                _t436 = 0
            else:
                if self.match_lookahead_literal('relatom', 1):
                    _t437 = 11
                else:
                    if self.match_lookahead_literal('reduce', 1):
                        _t438 = 3
                    else:
                        if self.match_lookahead_literal('primitive', 1):
                            _t439 = 10
                        else:
                            if self.match_lookahead_literal('pragma', 1):
                                _t440 = 9
                            else:
                                if self.match_lookahead_literal('or', 1):
                                    _t441 = 5
                                else:
                                    if self.match_lookahead_literal('not', 1):
                                        _t442 = 6
                                    else:
                                        if self.match_lookahead_literal('ffi', 1):
                                            _t443 = 7
                                        else:
                                            if self.match_lookahead_literal('false', 1):
                                                _t457 = 1
                                            else:
                                                if self.match_lookahead_literal('exists', 1):
                                                    _t458 = 2
                                                else:
                                                    if self.match_lookahead_literal('cast', 1):
                                                        _t459 = 12
                                                    else:
                                                        if self.match_lookahead_literal('atom', 1):
                                                            _t460 = 8
                                                        else:
                                                            if self.match_lookahead_literal('and', 1):
                                                                _t461 = 4
                                                            else:
                                                                if self.match_lookahead_literal('>=', 1):
                                                                    _t462 = 10
                                                                else:
                                                                    if self.match_lookahead_literal('>', 1):
                                                                        _t463 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal('=', 1):
                                                                            _t464 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal('<=', 1):
                                                                                _t465 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal('<', 1):
                                                                                    _t466 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal('/', 1):
                                                                                        _t467 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal('-', 1):
                                                                                            _t468 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal('+', 1):
                                                                                                _t469 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal('*', 1):
                                                                                                    _t470 = 10
                                                                                                else:
                                                                                                    _t470 = -1
                                                                                                _t469 = _t470
                                                                                            _t468 = _t469
                                                                                        _t467 = _t468
                                                                                    _t466 = _t467
                                                                                _t465 = _t466
                                                                            _t464 = _t465
                                                                        _t463 = _t464
                                                                    _t462 = _t463
                                                                _t461 = _t462
                                                            _t460 = _t461
                                                        _t459 = _t460
                                                    _t458 = _t459
                                                _t457 = _t458
                                            _t443 = _t457
                                        _t442 = _t443
                                    _t441 = _t442
                                _t440 = _t441
                            _t439 = _t440
                        _t438 = _t439
                    _t437 = _t438
                _t436 = _t437
            _t435 = _t436
        else:
            _t435 = -1
        prediction83 = _t435
        if prediction83 == 12:
            _t472 = self.parse_cast()
            value96 = _t472
            _t473 = logic_pb2.Formula(cast=value96)
            _t471 = _t473
        else:
            if prediction83 == 11:
                _t475 = self.parse_relatom()
                value95 = _t475
                _t476 = logic_pb2.Formula(rel_atom=value95)
                _t474 = _t476
            else:
                if prediction83 == 10:
                    _t478 = self.parse_primitive()
                    value94 = _t478
                    _t479 = logic_pb2.Formula(primitive=value94)
                    _t477 = _t479
                else:
                    if prediction83 == 9:
                        _t481 = self.parse_pragma()
                        value93 = _t481
                        _t482 = logic_pb2.Formula(pragma=value93)
                        _t480 = _t482
                    else:
                        if prediction83 == 8:
                            _t484 = self.parse_atom()
                            value92 = _t484
                            _t485 = logic_pb2.Formula(atom=value92)
                            _t483 = _t485
                        else:
                            if prediction83 == 7:
                                _t487 = self.parse_ffi()
                                value91 = _t487
                                _t488 = logic_pb2.Formula(ffi=value91)
                                _t486 = _t488
                            else:
                                if prediction83 == 6:
                                    _t490 = self.parse_not()
                                    value90 = _t490
                                    _t491 = logic_pb2.Formula(**{'not': value90})
                                    _t489 = _t491
                                else:
                                    if prediction83 == 5:
                                        _t493 = self.parse_disjunction()
                                        value89 = _t493
                                        _t494 = logic_pb2.Formula(disjunction=value89)
                                        _t492 = _t494
                                    else:
                                        if prediction83 == 4:
                                            _t496 = self.parse_conjunction()
                                            value88 = _t496
                                            _t497 = logic_pb2.Formula(conjunction=value88)
                                            _t495 = _t497
                                        else:
                                            if prediction83 == 3:
                                                _t499 = self.parse_reduce()
                                                value87 = _t499
                                                _t500 = logic_pb2.Formula(reduce=value87)
                                                _t498 = _t500
                                            else:
                                                if prediction83 == 2:
                                                    _t502 = self.parse_exists()
                                                    value86 = _t502
                                                    _t503 = logic_pb2.Formula(exists=value86)
                                                    _t501 = _t503
                                                else:
                                                    if prediction83 == 1:
                                                        _t505 = self.parse_false()
                                                        value85 = _t505
                                                        _t506 = logic_pb2.Formula(false=value85)
                                                        _t504 = _t506
                                                    else:
                                                        if prediction83 == 0:
                                                            _t508 = self.parse_true()
                                                            value84 = _t508
                                                            _t509 = logic_pb2.Formula(true=value84)
                                                            _t507 = _t509
                                                        else:
                                                            raise ParseError('Unexpected token in formula' + ": {self.lookahead(0)}")
                                                            _t507 = None
                                                        _t504 = _t507
                                                    _t501 = _t504
                                                _t498 = _t501
                                            _t495 = _t498
                                        _t492 = _t495
                                    _t489 = _t492
                                _t486 = _t489
                            _t483 = _t486
                        _t480 = _t483
                    _t477 = _t480
                _t474 = _t477
            _t471 = _t474
        return _t471

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('true')
        self.consume_literal(')')
        _t510 = logic_pb2.Conjunction(args=[])
        return _t510

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('false')
        self.consume_literal(')')
        _t511 = logic_pb2.Disjunction(args=[])
        return _t511

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal('(')
        self.consume_literal('exists')
        _t512 = self.parse_bindings()
        bindings97 = _t512
        _t513 = self.parse_formula()
        formula98 = _t513
        self.consume_literal(')')
        _t514 = logic_pb2.Abstraction(vars=(bindings97[0] + (bindings97[1] if bindings97[1] is not None else [])), value=formula98)
        _t515 = logic_pb2.Exists(body=_t514)
        return _t515

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal('(')
        self.consume_literal('reduce')
        _t516 = self.parse_abstraction()
        op99 = _t516
        _t517 = self.parse_abstraction()
        body100 = _t517
        if self.match_lookahead_literal('(', 0):
            _t519 = self.parse_terms()
            _t518 = _t519
        else:
            _t518 = None
        terms101 = _t518
        self.consume_literal(')')
        _t520 = logic_pb2.Reduce(op=op99, body=body100, terms=(terms101 if terms101 is not None else []))
        return _t520

    def parse_terms(self) -> list[logic_pb2.Term]:
        self.consume_literal('(')
        self.consume_literal('terms')
        xs102 = []
        cond103 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond103:
            _t521 = self.parse_term()
            xs102.append(_t521)
            cond103 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        value104 = xs102
        self.consume_literal(')')
        return value104

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_terminal('UINT128', 0):
            _t523 = 1
        else:
            if self.match_lookahead_terminal('SYMBOL', 0):
                _t524 = 0
            else:
                _t524 = (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or (self.match_lookahead_literal('true', 0) or (self.match_lookahead_literal('missing', 0) or (self.match_lookahead_literal('false', 0) or (self.match_lookahead_literal('(', 0) or -1)))))))))
            _t523 = _t524
        prediction105 = _t523
        if prediction105 == 1:
            _t526 = self.parse_constant()
            value107 = _t526
            _t527 = logic_pb2.Term(constant=value107)
            _t525 = _t527
        else:
            if prediction105 == 0:
                _t529 = self.parse_var()
                value106 = _t529
                _t530 = logic_pb2.Term(var=value106)
                _t528 = _t530
            else:
                raise ParseError('Unexpected token in term' + ": {self.lookahead(0)}")
                _t528 = None
            _t525 = _t528
        return _t525

    def parse_var(self) -> logic_pb2.Var:
        symbol108 = self.consume_terminal('SYMBOL')
        _t531 = logic_pb2.Var(name=symbol108)
        return _t531

    def parse_constant(self) -> logic_pb2.Value:
        _t532 = self.parse_value()
        x109 = _t532
        return x109

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('and')
        xs110 = []
        cond111 = self.match_lookahead_literal('(', 0)
        while cond111:
            _t533 = self.parse_formula()
            xs110.append(_t533)
            cond111 = self.match_lookahead_literal('(', 0)
        args112 = xs110
        self.consume_literal(')')
        _t534 = logic_pb2.Conjunction(args=args112)
        return _t534

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('or')
        xs113 = []
        cond114 = self.match_lookahead_literal('(', 0)
        while cond114:
            _t535 = self.parse_formula()
            xs113.append(_t535)
            cond114 = self.match_lookahead_literal('(', 0)
        args115 = xs113
        self.consume_literal(')')
        _t536 = logic_pb2.Disjunction(args=args115)
        return _t536

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal('(')
        self.consume_literal('not')
        _t537 = self.parse_formula()
        arg116 = _t537
        self.consume_literal(')')
        _t538 = logic_pb2.Not(arg=arg116)
        return _t538

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal('(')
        self.consume_literal('ffi')
        _t539 = self.parse_name()
        name117 = _t539
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('args', 1)):
            _t541 = self.parse_ffi_args()
            _t540 = _t541
        else:
            _t540 = None
        args118 = _t540
        if self.match_lookahead_literal('(', 0):
            _t543 = self.parse_terms()
            _t542 = _t543
        else:
            _t542 = None
        terms119 = _t542
        self.consume_literal(')')
        _t544 = logic_pb2.FFI(name=name117, args=(args118 if args118 is not None else []), terms=(terms119 if terms119 is not None else []))
        return _t544

    def parse_name(self) -> str:
        self.consume_literal(':')
        symbol120 = self.consume_terminal('SYMBOL')
        return symbol120

    def parse_ffi_args(self) -> list[logic_pb2.Abstraction]:
        self.consume_literal('(')
        self.consume_literal('args')
        xs121 = []
        cond122 = self.match_lookahead_literal('(', 0)
        while cond122:
            _t545 = self.parse_abstraction()
            xs121.append(_t545)
            cond122 = self.match_lookahead_literal('(', 0)
        value123 = xs121
        self.consume_literal(')')
        return value123

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal('(')
        self.consume_literal('atom')
        _t546 = self.parse_relation_id()
        name124 = _t546
        xs125 = []
        cond126 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond126:
            _t547 = self.parse_term()
            xs125.append(_t547)
            cond126 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms127 = xs125
        self.consume_literal(')')
        _t548 = logic_pb2.Atom(name=name124, terms=terms127)
        return _t548

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal('(')
        self.consume_literal('pragma')
        _t549 = self.parse_name()
        name128 = _t549
        xs129 = []
        cond130 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond130:
            _t550 = self.parse_term()
            xs129.append(_t550)
            cond130 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms131 = xs129
        self.consume_literal(')')
        _t551 = logic_pb2.Pragma(name=name128, terms=terms131)
        return _t551

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('primitive', 1):
                _t553 = 9
            else:
                if self.match_lookahead_literal('>=', 1):
                    _t554 = 4
                else:
                    if self.match_lookahead_literal('>', 1):
                        _t555 = 3
                    else:
                        if self.match_lookahead_literal('=', 1):
                            _t556 = 0
                        else:
                            if self.match_lookahead_literal('<=', 1):
                                _t557 = 2
                            else:
                                if self.match_lookahead_literal('<', 1):
                                    _t562 = 1
                                else:
                                    if self.match_lookahead_literal('/', 1):
                                        _t563 = 8
                                    else:
                                        if self.match_lookahead_literal('-', 1):
                                            _t564 = 6
                                        else:
                                            if self.match_lookahead_literal('+', 1):
                                                _t565 = 5
                                            else:
                                                if self.match_lookahead_literal('*', 1):
                                                    _t566 = 7
                                                else:
                                                    _t566 = -1
                                                _t565 = _t566
                                            _t564 = _t565
                                        _t563 = _t564
                                    _t562 = _t563
                                _t557 = _t562
                            _t556 = _t557
                        _t555 = _t556
                    _t554 = _t555
                _t553 = _t554
            _t552 = _t553
        else:
            _t552 = -1
        prediction132 = _t552
        if prediction132 == 9:
            self.consume_literal('(')
            self.consume_literal('primitive')
            _t568 = self.parse_name()
            name142 = _t568
            xs143 = []
            cond144 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            while cond144:
                _t569 = self.parse_relterm()
                xs143.append(_t569)
                cond144 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            terms145 = xs143
            self.consume_literal(')')
            _t570 = logic_pb2.Primitive(name=name142, terms=terms145)
            _t567 = _t570
        else:
            if prediction132 == 8:
                _t572 = self.parse_divide()
                op141 = _t572
                _t571 = op141
            else:
                if prediction132 == 7:
                    _t574 = self.parse_multiply()
                    op140 = _t574
                    _t573 = op140
                else:
                    if prediction132 == 6:
                        _t576 = self.parse_minus()
                        op139 = _t576
                        _t575 = op139
                    else:
                        if prediction132 == 5:
                            _t578 = self.parse_add()
                            op138 = _t578
                            _t577 = op138
                        else:
                            if prediction132 == 4:
                                _t580 = self.parse_gt_eq()
                                op137 = _t580
                                _t579 = op137
                            else:
                                if prediction132 == 3:
                                    _t582 = self.parse_gt()
                                    op136 = _t582
                                    _t581 = op136
                                else:
                                    if prediction132 == 2:
                                        _t584 = self.parse_lt_eq()
                                        op135 = _t584
                                        _t583 = op135
                                    else:
                                        if prediction132 == 1:
                                            _t586 = self.parse_lt()
                                            op134 = _t586
                                            _t585 = op134
                                        else:
                                            if prediction132 == 0:
                                                _t588 = self.parse_eq()
                                                op133 = _t588
                                                _t587 = op133
                                            else:
                                                raise ParseError('Unexpected token in primitive' + ": {self.lookahead(0)}")
                                                _t587 = None
                                            _t585 = _t587
                                        _t583 = _t585
                                    _t581 = _t583
                                _t579 = _t581
                            _t577 = _t579
                        _t575 = _t577
                    _t573 = _t575
                _t571 = _t573
            _t567 = _t571
        return _t567

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('=')
        _t589 = self.parse_term()
        left146 = _t589
        _t590 = self.parse_term()
        right147 = _t590
        self.consume_literal(')')
        _t591 = logic_pb2.RelTerm(term=left146)
        _t592 = logic_pb2.RelTerm(term=right147)
        _t593 = logic_pb2.Primitive(name='rel_primitive_eq', terms=[_t591, _t592])
        return _t593

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<')
        _t594 = self.parse_term()
        left148 = _t594
        _t595 = self.parse_term()
        right149 = _t595
        self.consume_literal(')')
        _t596 = logic_pb2.RelTerm(term=left148)
        _t597 = logic_pb2.RelTerm(term=right149)
        _t598 = logic_pb2.Primitive(name='rel_primitive_lt', terms=[_t596, _t597])
        return _t598

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<=')
        _t599 = self.parse_term()
        left150 = _t599
        _t600 = self.parse_term()
        right151 = _t600
        self.consume_literal(')')
        _t601 = logic_pb2.RelTerm(term=left150)
        _t602 = logic_pb2.RelTerm(term=right151)
        _t603 = logic_pb2.Primitive(name='rel_primitive_lt_eq', terms=[_t601, _t602])
        return _t603

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>')
        _t604 = self.parse_term()
        left152 = _t604
        _t605 = self.parse_term()
        right153 = _t605
        self.consume_literal(')')
        _t606 = logic_pb2.RelTerm(term=left152)
        _t607 = logic_pb2.RelTerm(term=right153)
        _t608 = logic_pb2.Primitive(name='rel_primitive_gt', terms=[_t606, _t607])
        return _t608

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>=')
        _t609 = self.parse_term()
        left154 = _t609
        _t610 = self.parse_term()
        right155 = _t610
        self.consume_literal(')')
        _t611 = logic_pb2.RelTerm(term=left154)
        _t612 = logic_pb2.RelTerm(term=right155)
        _t613 = logic_pb2.Primitive(name='rel_primitive_gt_eq', terms=[_t611, _t612])
        return _t613

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('+')
        _t614 = self.parse_term()
        left156 = _t614
        _t615 = self.parse_term()
        right157 = _t615
        _t616 = self.parse_term()
        result158 = _t616
        self.consume_literal(')')
        _t617 = logic_pb2.RelTerm(term=left156)
        _t618 = logic_pb2.RelTerm(term=right157)
        _t619 = logic_pb2.RelTerm(term=result158)
        _t620 = logic_pb2.Primitive(name='rel_primitive_add', terms=[_t617, _t618, _t619])
        return _t620

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('-')
        _t621 = self.parse_term()
        left159 = _t621
        _t622 = self.parse_term()
        right160 = _t622
        _t623 = self.parse_term()
        result161 = _t623
        self.consume_literal(')')
        _t624 = logic_pb2.RelTerm(term=left159)
        _t625 = logic_pb2.RelTerm(term=right160)
        _t626 = logic_pb2.RelTerm(term=result161)
        _t627 = logic_pb2.Primitive(name='rel_primitive_subtract', terms=[_t624, _t625, _t626])
        return _t627

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('*')
        _t628 = self.parse_term()
        left162 = _t628
        _t629 = self.parse_term()
        right163 = _t629
        _t630 = self.parse_term()
        result164 = _t630
        self.consume_literal(')')
        _t631 = logic_pb2.RelTerm(term=left162)
        _t632 = logic_pb2.RelTerm(term=right163)
        _t633 = logic_pb2.RelTerm(term=result164)
        _t634 = logic_pb2.Primitive(name='rel_primitive_multiply', terms=[_t631, _t632, _t633])
        return _t634

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('/')
        _t635 = self.parse_term()
        left165 = _t635
        _t636 = self.parse_term()
        right166 = _t636
        _t637 = self.parse_term()
        result167 = _t637
        self.consume_literal(')')
        _t638 = logic_pb2.RelTerm(term=left165)
        _t639 = logic_pb2.RelTerm(term=right166)
        _t640 = logic_pb2.RelTerm(term=result167)
        _t641 = logic_pb2.Primitive(name='rel_primitive_divide', terms=[_t638, _t639, _t640])
        return _t641

    def parse_relterm(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_terminal('UINT128', 0):
            _t2689 = 1
        else:
            if self.match_lookahead_terminal('SYMBOL', 0):
                _t3713 = 1
            else:
                if self.match_lookahead_terminal('STRING', 0):
                    _t4225 = 1
                else:
                    if self.match_lookahead_terminal('INT128', 0):
                        _t4481 = 1
                    else:
                        if self.match_lookahead_terminal('INT', 0):
                            _t4609 = 1
                        else:
                            if self.match_lookahead_terminal('FLOAT', 0):
                                _t4673 = 1
                            else:
                                if self.match_lookahead_terminal('DECIMAL', 0):
                                    _t4705 = 1
                                else:
                                    if self.match_lookahead_literal('true', 0):
                                        _t4721 = 1
                                    else:
                                        if self.match_lookahead_literal('missing', 0):
                                            _t4729 = 1
                                        else:
                                            if self.match_lookahead_literal('false', 0):
                                                _t4733 = 1
                                            else:
                                                if self.match_lookahead_literal('(', 0):
                                                    _t4735 = 1
                                                else:
                                                    if self.match_lookahead_literal('#', 0):
                                                        _t4736 = 0
                                                    else:
                                                        _t4736 = -1
                                                    _t4735 = _t4736
                                                _t4733 = _t4735
                                            _t4729 = _t4733
                                        _t4721 = _t4729
                                    _t4705 = _t4721
                                _t4673 = _t4705
                            _t4609 = _t4673
                        _t4481 = _t4609
                    _t4225 = _t4481
                _t3713 = _t4225
            _t2689 = _t3713
        prediction168 = _t2689
        if prediction168 == 1:
            _t4738 = self.parse_term()
            value170 = _t4738
            _t4739 = logic_pb2.RelTerm(term=value170)
            _t4737 = _t4739
        else:
            if prediction168 == 0:
                _t4741 = self.parse_specialized_value()
                value169 = _t4741
                _t4742 = logic_pb2.RelTerm(specialized_value=value169)
                _t4740 = _t4742
            else:
                raise ParseError('Unexpected token in relterm' + ": {self.lookahead(0)}")
                _t4740 = None
            _t4737 = _t4740
        return _t4737

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal('#')
        _t4743 = self.parse_value()
        value171 = _t4743
        return value171

    def parse_relatom(self) -> logic_pb2.RelAtom:
        self.consume_literal('(')
        self.consume_literal('relatom')
        _t4744 = self.parse_name()
        name172 = _t4744
        xs173 = []
        cond174 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond174:
            _t4745 = self.parse_relterm()
            xs173.append(_t4745)
            cond174 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms175 = xs173
        self.consume_literal(')')
        _t4746 = logic_pb2.RelAtom(name=name172, terms=terms175)
        return _t4746

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal('(')
        self.consume_literal('cast')
        _t4747 = self.parse_term()
        input176 = _t4747
        _t4748 = self.parse_term()
        result177 = _t4748
        self.consume_literal(')')
        _t4749 = logic_pb2.Cast(input=input176, result=result177)
        return _t4749

    def parse_attrs(self) -> list[logic_pb2.Attribute]:
        self.consume_literal('(')
        self.consume_literal('attrs')
        xs178 = []
        cond179 = self.match_lookahead_literal('(', 0)
        while cond179:
            _t4750 = self.parse_attribute()
            xs178.append(_t4750)
            cond179 = self.match_lookahead_literal('(', 0)
        value180 = xs178
        self.consume_literal(')')
        return value180

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal('(')
        self.consume_literal('attribute')
        _t4751 = self.parse_name()
        name181 = _t4751
        xs182 = []
        cond183 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond183:
            _t4752 = self.parse_value()
            xs182.append(_t4752)
            cond183 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        args184 = xs182
        self.consume_literal(')')
        _t4753 = logic_pb2.Attribute(name=name181, args=args184)
        return _t4753

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal('(')
        self.consume_literal('algorithm')
        xs185 = []
        cond186 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        while cond186:
            _t4754 = self.parse_relation_id()
            xs185.append(_t4754)
            cond186 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        global187 = xs185
        _t4755 = self.parse_script()
        body188 = _t4755
        self.consume_literal(')')
        _t4756 = logic_pb2.Algorithm(global_=global187, body=body188)
        return _t4756

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal('(')
        self.consume_literal('script')
        xs189 = []
        cond190 = self.match_lookahead_literal('(', 0)
        while cond190:
            _t4757 = self.parse_construct()
            xs189.append(_t4757)
            cond190 = self.match_lookahead_literal('(', 0)
        constructs191 = xs189
        self.consume_literal(')')
        _t4758 = logic_pb2.Script(constructs=constructs191)
        return _t4758

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t4767 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t4771 = 1
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t4773 = 1
                    else:
                        if self.match_lookahead_literal('loop', 1):
                            _t4774 = 0
                        else:
                            _t4774 = (self.match_lookahead_literal('break', 1) or (self.match_lookahead_literal('assign', 1) or -1))
                        _t4773 = _t4774
                    _t4771 = _t4773
                _t4767 = _t4771
            _t4759 = _t4767
        else:
            _t4759 = -1
        prediction192 = _t4759
        if prediction192 == 1:
            _t4776 = self.parse_instruction()
            value194 = _t4776
            _t4777 = logic_pb2.Construct(instruction=value194)
            _t4775 = _t4777
        else:
            if prediction192 == 0:
                _t4779 = self.parse_loop()
                value193 = _t4779
                _t4780 = logic_pb2.Construct(loop=value193)
                _t4778 = _t4780
            else:
                raise ParseError('Unexpected token in construct' + ": {self.lookahead(0)}")
                _t4778 = None
            _t4775 = _t4778
        return _t4775

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal('(')
        self.consume_literal('loop')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('init', 1)):
            _t4782 = self.parse_loop_init()
            _t4781 = _t4782
        else:
            _t4781 = None
        init195 = _t4781
        _t4783 = self.parse_script()
        body196 = _t4783
        self.consume_literal(')')
        _t4784 = logic_pb2.Loop(init=(init195 if init195 is not None else []), body=body196)
        return _t4784

    def parse_loop_init(self) -> list[logic_pb2.Instruction]:
        self.consume_literal('(')
        self.consume_literal('init')
        xs197 = []
        cond198 = self.match_lookahead_literal('(', 0)
        while cond198:
            _t4785 = self.parse_instruction()
            xs197.append(_t4785)
            cond198 = self.match_lookahead_literal('(', 0)
        value199 = xs197
        self.consume_literal(')')
        return value199

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t4791 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t4792 = 4
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t4793 = 3
                    else:
                        if self.match_lookahead_literal('break', 1):
                            _t4794 = 2
                        else:
                            if self.match_lookahead_literal('assign', 1):
                                _t4795 = 0
                            else:
                                _t4795 = -1
                            _t4794 = _t4795
                        _t4793 = _t4794
                    _t4792 = _t4793
                _t4791 = _t4792
            _t4786 = _t4791
        else:
            _t4786 = -1
        prediction200 = _t4786
        if prediction200 == 4:
            _t4797 = self.parse_monus_def()
            value205 = _t4797
            _t4798 = logic_pb2.Instruction(monus_def=value205)
            _t4796 = _t4798
        else:
            if prediction200 == 3:
                _t4800 = self.parse_monoid_def()
                value204 = _t4800
                _t4801 = logic_pb2.Instruction(monoid_def=value204)
                _t4799 = _t4801
            else:
                if prediction200 == 2:
                    _t4803 = self.parse_break()
                    value203 = _t4803
                    _t4804 = logic_pb2.Instruction(**{'break': value203})
                    _t4802 = _t4804
                else:
                    if prediction200 == 1:
                        _t4806 = self.parse_upsert()
                        value202 = _t4806
                        _t4807 = logic_pb2.Instruction(upsert=value202)
                        _t4805 = _t4807
                    else:
                        if prediction200 == 0:
                            _t4809 = self.parse_assign()
                            value201 = _t4809
                            _t4810 = logic_pb2.Instruction(assign=value201)
                            _t4808 = _t4810
                        else:
                            raise ParseError('Unexpected token in instruction' + ": {self.lookahead(0)}")
                            _t4808 = None
                        _t4805 = _t4808
                    _t4802 = _t4805
                _t4799 = _t4802
            _t4796 = _t4799
        return _t4796

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal('(')
        self.consume_literal('assign')
        _t4811 = self.parse_relation_id()
        name206 = _t4811
        _t4812 = self.parse_abstraction()
        body207 = _t4812
        if self.match_lookahead_literal('(', 0):
            _t4814 = self.parse_attrs()
            _t4813 = _t4814
        else:
            _t4813 = None
        attrs208 = _t4813
        self.consume_literal(')')
        _t4815 = logic_pb2.Assign(name=name206, body=body207, attrs=(attrs208 if attrs208 is not None else []))
        return _t4815

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal('(')
        self.consume_literal('upsert')
        _t4816 = self.parse_relation_id()
        name209 = _t4816
        _t4817 = self.parse_abstraction_with_arity()
        body210 = _t4817
        if self.match_lookahead_literal('(', 0):
            _t4819 = self.parse_attrs()
            _t4818 = _t4819
        else:
            _t4818 = None
        attrs211 = _t4818
        self.consume_literal(')')
        _t4820 = logic_pb2.Upsert(name=name209, body=body210[0], attrs=(attrs211 if attrs211 is not None else []), value_arity=body210[1])
        return _t4820

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal('(')
        _t4821 = self.parse_bindings()
        bindings212 = _t4821
        _t4822 = self.parse_formula()
        formula213 = _t4822
        self.consume_literal(')')
        _t4823 = logic_pb2.Abstraction(vars=(bindings212[0] + (bindings212[1] if bindings212[1] is not None else [])), value=formula213)
        return (_t4823, len(bindings212[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal('(')
        self.consume_literal('break')
        _t4824 = self.parse_relation_id()
        name214 = _t4824
        _t4825 = self.parse_abstraction()
        body215 = _t4825
        if self.match_lookahead_literal('(', 0):
            _t4827 = self.parse_attrs()
            _t4826 = _t4827
        else:
            _t4826 = None
        attrs216 = _t4826
        self.consume_literal(')')
        _t4828 = logic_pb2.Break(name=name214, body=body215, attrs=(attrs216 if attrs216 is not None else []))
        return _t4828

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal('(')
        self.consume_literal('monoid')
        _t4829 = self.parse_monoid()
        monoid217 = _t4829
        _t4830 = self.parse_relation_id()
        name218 = _t4830
        _t4831 = self.parse_abstraction_with_arity()
        body219 = _t4831
        if self.match_lookahead_literal('(', 0):
            _t4833 = self.parse_attrs()
            _t4832 = _t4833
        else:
            _t4832 = None
        attrs220 = _t4832
        self.consume_literal(')')
        _t4834 = logic_pb2.MonoidDef(monoid=monoid217, name=name218, body=body219[0], attrs=(attrs220 if attrs220 is not None else []), value_arity=body219[1])
        return _t4834

    def parse_monoid(self) -> logic_pb2.Monoid:
        _t4835 = self.parse_type()
        type221 = _t4835
        self.consume_literal('::')
        _t4836 = self.parse_monoid_op()
        op222 = _t4836
        _t4837 = op222(type221)
        return _t4837

    def parse_monoid_op(self) -> Callable[[logic_pb2.Type], logic_pb2.Monoid]:
        if self.match_lookahead_literal('SUM', 0):
            _t4838 = 3
        else:
            if self.match_lookahead_literal('OR', 0):
                _t4839 = 0
            else:
                if self.match_lookahead_literal('MIN', 0):
                    _t4841 = 1
                else:
                    if self.match_lookahead_literal('MAX', 0):
                        _t4842 = 2
                    else:
                        _t4842 = -1
                    _t4841 = _t4842
                _t4839 = _t4841
            _t4838 = _t4839
        prediction223 = _t4838
        if prediction223 == 3:
            self.consume_literal('SUM')
            def _t4844(type):
                _t4845 = logic_pb2.SumMonoid(type=type)
                _t4846 = logic_pb2.Monoid(sum=_t4845)
                return _t4846
            _t4843 = _t4844
        else:
            if prediction223 == 2:
                self.consume_literal('MAX')
                def _t4848(type):
                    _t4849 = logic_pb2.MaxMonoid(type=type)
                    _t4850 = logic_pb2.Monoid(max_monoid=_t4849)
                    return _t4850
                _t4847 = _t4848
            else:
                if prediction223 == 1:
                    self.consume_literal('MIN')
                    def _t4852(type):
                        _t4853 = logic_pb2.MinMonoid(type=type)
                        _t4854 = logic_pb2.Monoid(min_monoid=_t4853)
                        return _t4854
                    _t4851 = _t4852
                else:
                    if prediction223 == 0:
                        self.consume_literal('OR')
                        def _t4856(type):
                            _t4857 = logic_pb2.OrMonoid()
                            _t4858 = logic_pb2.Monoid(or_monoid=_t4857)
                            return _t4858
                        _t4855 = _t4856
                    else:
                        raise ParseError('Unexpected token in monoid_op' + ": {self.lookahead(0)}")
                        _t4855 = None
                    _t4851 = _t4855
                _t4847 = _t4851
            _t4843 = _t4847
        return _t4843

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal('(')
        self.consume_literal('monus')
        _t4859 = self.parse_monoid()
        monoid224 = _t4859
        _t4860 = self.parse_relation_id()
        name225 = _t4860
        _t4861 = self.parse_abstraction_with_arity()
        body226 = _t4861
        if self.match_lookahead_literal('(', 0):
            _t4863 = self.parse_attrs()
            _t4862 = _t4863
        else:
            _t4862 = None
        attrs227 = _t4862
        self.consume_literal(')')
        _t4864 = logic_pb2.MonusDef(monoid=monoid224, name=name225, body=body226[0], attrs=(attrs227 if attrs227 is not None else []), value_arity=body226[1])
        return _t4864

    def parse_constraint(self) -> logic_pb2.Constraint:
        _t4865 = self.parse_functional_dependency()
        value228 = _t4865
        _t4866 = logic_pb2.Constraint(functional_dependency=value228)
        return _t4866

    def parse_functional_dependency(self) -> logic_pb2.FunctionalDependency:
        self.consume_literal('(')
        self.consume_literal('functional_dependency')
        _t4867 = self.parse_abstraction()
        guard229 = _t4867
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('keys', 1)):
            _t4869 = self.parse_functional_dependency_keys()
            _t4868 = _t4869
        else:
            _t4868 = None
        keys230 = _t4868
        if self.match_lookahead_literal('(', 0):
            _t4871 = self.parse_functional_dependency_values()
            _t4870 = _t4871
        else:
            _t4870 = None
        values231 = _t4870
        self.consume_literal(')')
        _t4872 = logic_pb2.FunctionalDependency(guard=guard229, keys=(keys230 if keys230 is not None else []), values=(values231 if values231 is not None else []))
        return _t4872

    def parse_functional_dependency_keys(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('keys')
        xs232 = []
        cond233 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond233:
            _t4873 = self.parse_var()
            xs232.append(_t4873)
            cond233 = self.match_lookahead_terminal('SYMBOL', 0)
        value234 = xs232
        self.consume_literal(')')
        return value234

    def parse_functional_dependency_values(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('values')
        xs235 = []
        cond236 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond236:
            _t4874 = self.parse_var()
            xs235.append(_t4874)
            cond236 = self.match_lookahead_terminal('SYMBOL', 0)
        value237 = xs235
        self.consume_literal(')')
        return value237

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal('(')
        self.consume_literal('undefine')
        _t4875 = self.parse_fragment_id()
        fragment_id238 = _t4875
        self.consume_literal(')')
        _t4876 = transactions_pb2.Undefine(fragment_id=fragment_id238)
        return _t4876

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal('(')
        self.consume_literal('context')
        xs239 = []
        cond240 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        while cond240:
            _t4877 = self.parse_relation_id()
            xs239.append(_t4877)
            cond240 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        relations241 = xs239
        self.consume_literal(')')
        _t4878 = transactions_pb2.Context(relations=relations241)
        return _t4878

    def parse_epoch_reads(self) -> list[transactions_pb2.Read]:
        self.consume_literal('(')
        self.consume_literal('reads')
        xs242 = []
        cond243 = self.match_lookahead_literal('(', 0)
        while cond243:
            _t4879 = self.parse_read()
            xs242.append(_t4879)
            cond243 = self.match_lookahead_literal('(', 0)
        value244 = xs242
        self.consume_literal(')')
        return value244

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('what_if', 1):
                _t4881 = 2
            else:
                if self.match_lookahead_literal('output', 1):
                    _t4885 = 1
                else:
                    if self.match_lookahead_literal('export', 1):
                        _t4886 = 4
                    else:
                        if self.match_lookahead_literal('demand', 1):
                            _t4887 = 0
                        else:
                            if self.match_lookahead_literal('abort', 1):
                                _t4888 = 3
                            else:
                                _t4888 = -1
                            _t4887 = _t4888
                        _t4886 = _t4887
                    _t4885 = _t4886
                _t4881 = _t4885
            _t4880 = _t4881
        else:
            _t4880 = -1
        prediction245 = _t4880
        if prediction245 == 4:
            _t4890 = self.parse_export()
            value250 = _t4890
            _t4891 = transactions_pb2.Read(export=value250)
            _t4889 = _t4891
        else:
            if prediction245 == 3:
                _t4893 = self.parse_abort()
                value249 = _t4893
                _t4894 = transactions_pb2.Read(abort=value249)
                _t4892 = _t4894
            else:
                if prediction245 == 2:
                    _t4896 = self.parse_what_if()
                    value248 = _t4896
                    _t4897 = transactions_pb2.Read(what_if=value248)
                    _t4895 = _t4897
                else:
                    if prediction245 == 1:
                        _t4899 = self.parse_output()
                        value247 = _t4899
                        _t4900 = transactions_pb2.Read(output=value247)
                        _t4898 = _t4900
                    else:
                        if prediction245 == 0:
                            _t4902 = self.parse_demand()
                            value246 = _t4902
                            _t4903 = transactions_pb2.Read(demand=value246)
                            _t4901 = _t4903
                        else:
                            raise ParseError('Unexpected token in read' + ": {self.lookahead(0)}")
                            _t4901 = None
                        _t4898 = _t4901
                    _t4895 = _t4898
                _t4892 = _t4895
            _t4889 = _t4892
        return _t4889

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal('(')
        self.consume_literal('demand')
        _t4904 = self.parse_relation_id()
        relation_id251 = _t4904
        self.consume_literal(')')
        _t4905 = transactions_pb2.Demand(relation_id=relation_id251)
        return _t4905

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal('(')
        self.consume_literal('output')
        if (self.match_lookahead_literal(':', 0) and self.match_lookahead_terminal('SYMBOL', 1)):
            _t4907 = self.parse_name()
            _t4906 = _t4907
        else:
            _t4906 = None
        name252 = _t4906
        _t4908 = self.parse_relation_id()
        relation_id253 = _t4908
        self.consume_literal(')')
        _t4909 = transactions_pb2.Output(name=name252, relation_id=relation_id253)
        return _t4909

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal('(')
        self.consume_literal('what_if')
        branch254 = self.consume_terminal('STRING')
        _t4910 = self.parse_epoch()
        epoch255 = _t4910
        self.consume_literal(')')
        _t4911 = transactions_pb2.WhatIf(branch=branch254, epoch=epoch255)
        return _t4911

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal('(')
        self.consume_literal('abort')
        if (self.match_lookahead_literal(':', 0) and self.match_lookahead_terminal('SYMBOL', 1)):
            _t4913 = self.parse_name()
            _t4912 = _t4913
        else:
            _t4912 = None
        name256 = _t4912
        _t4914 = self.parse_relation_id()
        relation_id257 = _t4914
        self.consume_literal(')')
        _t4915 = transactions_pb2.Abort(name=name256, relation_id=relation_id257)
        return _t4915

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal('(')
        self.consume_literal('export')
        _t4916 = self.parse_export_csvconfig()
        config258 = _t4916
        self.consume_literal(')')
        _t4917 = transactions_pb2.Export(config258)
        return _t4917

    def parse_export_csvconfig(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal('(')
        self.consume_literal('export_csvconfig')
        path259 = self.consume_terminal('STRING')
        _t4918 = self.parse_export_csvcolumns()
        columns260 = _t4918
        _t4919 = self.parse_config_dict()
        config261 = _t4919
        self.consume_literal(')')
        return self.export_csv_config(path259, columns260, config261)

    def parse_export_csvcolumns(self) -> list[transactions_pb2.ExportCSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs262 = []
        cond263 = self.match_lookahead_literal('(', 0)
        while cond263:
            _t4920 = self.parse_export_csvcolumn()
            xs262.append(_t4920)
            cond263 = self.match_lookahead_literal('(', 0)
        columns264 = xs262
        self.consume_literal(')')
        return columns264

    def parse_export_csvcolumn(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        name265 = self.consume_terminal('STRING')
        _t4921 = self.parse_relation_id()
        relation_id266 = _t4921
        self.consume_literal(')')
        _t4922 = transactions_pb2.ExportCSVColumn(column_name=name265, column_data=relation_id266)
        return _t4922


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
