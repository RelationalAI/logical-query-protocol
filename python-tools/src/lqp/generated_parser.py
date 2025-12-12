"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.

Command: python-tools/src/meta/proto_tool.py proto/relationalai/lqp/v1/fragments.proto proto/relationalai/lqp/v1/logic.proto proto/relationalai/lqp/v1/transactions.proto --parser python -o python-tools/src/lqp/generated_parser.py
"""

import hashlib
import re
from typing import List, Optional, Any, Tuple
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
        return f"Token({{self.type}}, {{self.value!r}}, {{self.pos}})"


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
            'uint128_value',
            'missing_value',
            'int128_value',
            'transaction',
            'max_monoid',
            'sum_monoid',
            'min_monoid',
            'date_value',
            'debug_info',
            'attribute',
            'primitive',
            'ivmconfig',
            'algorithm',
            'configure',
            'or_monoid',
            'fragment',
            'DATETIME',
            'undefine',
            'datetime',
            'relatom',
            'missing',
            'columns',
            'BOOLEAN',
            'context',
            'DECIMAL',
            'what_if',
            'UINT128',
            'MISSING',
            'UNKNOWN',
            'demand',
            'values',
            'exists',
            'column',
            'assign',
            'monoid',
            'INT128',
            'STRING',
            'define',
            'writes',
            'reduce',
            'export',
            'output',
            'pragma',
            'upsert',
            'script',
            'false',
            'monus',
            'epoch',
            'abort',
            'reads',
            'break',
            'terms',
            'attrs',
            'FLOAT',
            'atom',
            'cast',
            'keys',
            'true',
            'init',
            'date',
            'DATE',
            'loop',
            'args',
            'sync',
            'def',
            'MAX',
            'not',
            'ffi',
            'ids',
            'and',
            'SUM',
            'INT',
            'MIN',
            'or',
            '>=',
            'OR',
            '::',
            '<=',
            '>',
            '+',
            '(',
            ':',
            ']',
            '#',
            '{',
            ')',
            '[',
            '*',
            '-',
            '=',
            '}',
            '<',
            '/',
            '|',
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
        return proto.UInt128Value(value=uint128_val, meta=None)

    @staticmethod
    def scan_int128(u: str) -> Any:
        """Parse INT128 token."""
        u = u[:-4]  # Remove the 'i128' suffix
        int128_val = int(u)
        return proto.Int128Value(value=int128_val, meta=None)

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
        return proto.DecimalValue(precision=precision, scale=scale, value=value, meta=None)


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
                maintenance_level = maintenance_level_val.string_value.upper()
            else:
                maintenance_level = 'OFF'
        else:
            maintenance_level = 'OFF'

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

        return transactions_pb2.ExportCsvConfig(path=path_str, data_columns=columns, **kwargs)

    def construct_fragment(self, fragment_id: fragments_pb2.FragmentId, declarations: List[logic_pb2.Declaration]) -> fragments_pb2.Fragment:
        """Construct Fragment from fragment_id, declarations, and debug info from parser state."""
        # Get the debug info dict for this fragment_id
        debug_info_dict = self.id_to_debuginfo.get(fragment_id, {})

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
        _t272 = transactions_pb2.Transaction(epochs4, (configure0 if configure0 is not None else self.construct_configure([])), sync1)
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
        if self.match_lookahead_literal('false', 0):
            _t276 = 10
        else:
            if self.match_lookahead_literal('true', 0):
                _t277 = 9
            else:
                if self.match_lookahead_literal('missing', 0):
                    _t278 = 8
                else:
                    if self.match_lookahead_terminal('DECIMAL', 0):
                        _t279 = 7
                    else:
                        if self.match_lookahead_terminal('INT128', 0):
                            _t280 = 6
                        else:
                            if self.match_lookahead_terminal('UINT128', 0):
                                _t281 = 5
                            else:
                                if self.match_lookahead_terminal('FLOAT', 0):
                                    _t282 = 4
                                else:
                                    if self.match_lookahead_terminal('INT', 0):
                                        _t283 = 3
                                    else:
                                        if self.match_lookahead_terminal('STRING', 0):
                                            _t284 = 2
                                        else:
                                            if self.match_lookahead_literal('(', 0):
                                                    if self.match_lookahead_literal('date', 1):
                                                        _t286 = 0
                                                    else:
                                                        _t286 = -1
                                                _t285 = (self.match_lookahead_literal('datetime', 1) or _t286)
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
            _t288 = logic_pb2.Value(boolean_value=False)
            _t287 = _t288
        else:
            if prediction11 == 9:
                self.consume_literal('true')
                _t290 = logic_pb2.Value(boolean_value=True)
                _t289 = _t290
            else:
                if prediction11 == 8:
                    self.consume_literal('missing')
                    _t292 = logic_pb2.MissingValue()
                    _t293 = logic_pb2.Value(missing_value=_t292)
                    _t291 = _t293
                else:
                    if prediction11 == 7:
                        value19 = self.consume_terminal('DECIMAL')
                        _t295 = logic_pb2.Value(decimal_value=value19)
                        _t294 = _t295
                    else:
                        if prediction11 == 6:
                            value18 = self.consume_terminal('INT128')
                            _t297 = logic_pb2.Value(int128_value=value18)
                            _t296 = _t297
                        else:
                            if prediction11 == 5:
                                value17 = self.consume_terminal('UINT128')
                                _t299 = logic_pb2.Value(uint128_value=value17)
                                _t298 = _t299
                            else:
                                if prediction11 == 4:
                                    value16 = self.consume_terminal('FLOAT')
                                    _t301 = logic_pb2.Value(float_value=value16)
                                    _t300 = _t301
                                else:
                                    if prediction11 == 3:
                                        value15 = self.consume_terminal('INT')
                                        _t303 = logic_pb2.Value(int_value=value15)
                                        _t302 = _t303
                                    else:
                                        if prediction11 == 2:
                                            value14 = self.consume_terminal('STRING')
                                            _t305 = logic_pb2.Value(string_value=value14)
                                            _t304 = _t305
                                        else:
                                            if prediction11 == 1:
                                                _t307 = self.parse_datetime()
                                                value13 = _t307
                                                _t308 = logic_pb2.Value(datetime_value=value13)
                                                _t306 = _t308
                                            else:
                                                if prediction11 == 0:
                                                    _t310 = self.parse_date()
                                                    value12 = _t310
                                                    _t311 = logic_pb2.Value(date_value=value12)
                                                    _t309 = _t311
                                                else:
                                                    raise ParseError('Unexpected token in value' + ": {self.lookahead(0)}")
                                                    _t309 = None
                                                _t306 = _t309
                                            _t304 = _t306
                                        _t302 = _t304
                                    _t300 = _t302
                                _t298 = _t300
                            _t296 = _t298
                        _t294 = _t296
                    _t291 = _t294
                _t289 = _t291
            _t287 = _t289
        return _t287

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal('(')
        self.consume_literal('date')
        year20 = self.consume_terminal('INT')
        month21 = self.consume_terminal('INT')
        day22 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t312 = logic_pb2.DateValue(year20, month21, day22)
        return _t312

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
            _t313 = self.consume_terminal('INT')
        else:
            _t313 = None
        microsecond29 = _t313
        self.consume_literal(')')
        if microsecond29 is None:
            _t314 = 0
        else:
            _t314 = microsecond29
        _t315 = logic_pb2.DateTimeValue(year23, month24, day25, hour26, minute27, second28, _t314)
        return _t315

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal('(')
        self.consume_literal('sync')
        xs30 = []
        cond31 = self.match_lookahead_literal(':', 0)
        while cond31:
            _t316 = self.parse_fragment_id()
            xs30.append(_t316)
            cond31 = self.match_lookahead_literal(':', 0)
        fragments32 = xs30
        self.consume_literal(')')
        _t317 = transactions_pb2.Sync(fragments32)
        return _t317

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        self.consume_literal(':')
        symbol33 = self.consume_terminal('SYMBOL')
        return proto.FragmentId(id=symbol33.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal('(')
        self.consume_literal('epoch')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('writes', 1)):
            _t319 = self.parse_epoch_writes()
            _t318 = _t319
        else:
            _t318 = None
        writes34 = _t318
        if self.match_lookahead_literal('(', 0):
            _t321 = self.parse_epoch_reads()
            _t320 = _t321
        else:
            _t320 = None
        reads35 = _t320
        self.consume_literal(')')
        _t322 = transactions_pb2.Epoch((writes34 if writes34 is not None else []), (reads35 if reads35 is not None else []))
        return _t322

    def parse_epoch_writes(self) -> list[transactions_pb2.Write]:
        self.consume_literal('(')
        self.consume_literal('writes')
        xs36 = []
        cond37 = self.match_lookahead_literal('(', 0)
        while cond37:
            _t323 = self.parse_write()
            xs36.append(_t323)
            cond37 = self.match_lookahead_literal('(', 0)
        value38 = xs36
        self.consume_literal(')')
        return value38

    def parse_write(self) -> transactions_pb2.Write:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('context', 1):
                _t325 = 2
            else:
                    if self.match_lookahead_literal('define', 1):
                        _t326 = 0
                    else:
                        _t326 = -1
                _t325 = (self.match_lookahead_literal('undefine', 1) or _t326)
            _t324 = _t325
        else:
            _t324 = -1
        prediction39 = _t324
        if prediction39 == 2:
            _t328 = self.parse_context()
            value42 = _t328
            _t329 = transactions_pb2.Write(context=value42)
            _t327 = _t329
        else:
            if prediction39 == 1:
                _t331 = self.parse_undefine()
                value41 = _t331
                _t332 = transactions_pb2.Write(undefine=value41)
                _t330 = _t332
            else:
                if prediction39 == 0:
                    _t334 = self.parse_define()
                    value40 = _t334
                    _t335 = transactions_pb2.Write(define=value40)
                    _t333 = _t335
                else:
                    raise ParseError('Unexpected token in write' + ": {self.lookahead(0)}")
                    _t333 = None
                _t330 = _t333
            _t327 = _t330
        return _t327

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal('(')
        self.consume_literal('define')
        _t336 = self.parse_fragment()
        fragment43 = _t336
        self.consume_literal(')')
        _t337 = transactions_pb2.Define(fragment43)
        return _t337

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal('(')
        self.consume_literal('fragment')
        _t338 = self.parse_fragment_id()
        fragment_id44 = _t338
        xs45 = []
        cond46 = self.match_lookahead_literal('(', 0)
        while cond46:
            _t339 = self.parse_declaration()
            xs45.append(_t339)
            cond46 = self.match_lookahead_literal('(', 0)
        declarations47 = xs45
        self.consume_literal(')')
        return self.construct_fragment(fragment_id44, declarations47)

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('functional_dependency', 1):
                _t341 = 2
            else:
                    if self.match_lookahead_literal('def', 1):
                        _t342 = 0
                    else:
                        _t342 = -1
                _t341 = (self.match_lookahead_literal('algorithm', 1) or _t342)
            _t340 = _t341
        else:
            _t340 = -1
        prediction48 = _t340
        if prediction48 == 2:
            _t344 = self.parse_constraint()
            value51 = _t344
            _t345 = logic_pb2.Declaration(constraint=value51)
            _t343 = _t345
        else:
            if prediction48 == 1:
                _t347 = self.parse_algorithm()
                value50 = _t347
                _t348 = logic_pb2.Declaration(algorithm=value50)
                _t346 = _t348
            else:
                if prediction48 == 0:
                    _t350 = self.parse_def()
                    value49 = _t350
                    _t351 = logic_pb2.Declaration(def=value49)
                    _t349 = _t351
                else:
                    raise ParseError('Unexpected token in declaration' + ": {self.lookahead(0)}")
                    _t349 = None
                _t346 = _t349
            _t343 = _t346
        return _t343

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal('(')
        self.consume_literal('def')
        _t352 = self.parse_relation_id()
        name52 = _t352
        _t353 = self.parse_abstraction()
        body53 = _t353
        if self.match_lookahead_literal('(', 0):
            _t355 = self.parse_attrs()
            _t354 = _t355
        else:
            _t354 = None
        attrs54 = _t354
        self.consume_literal(')')
        _t356 = logic_pb2.Def(name52, body53, (attrs54 if attrs54 is not None else []))
        return _t356

    def parse_relation_id(self) -> logic_pb2.RelationId:
            if self.match_lookahead_literal(':', 0):
                _t357 = 0
            else:
                _t357 = -1
        prediction55 = (self.match_lookahead_terminal('INT', 0) or _t357)
        if prediction55 == 1:
            INT57 = self.consume_terminal('INT')
            _t358 = proto.RelationId(id=INT57)
        else:
            if prediction55 == 0:
                self.consume_literal(':')
                symbol56 = self.consume_terminal('SYMBOL')
                _t359 = proto.RelationId(id=int(hashlib.sha256(symbol56.encode()).hexdigest()[:16], 16))
            else:
                raise ParseError('Unexpected token in relation_id' + ": {self.lookahead(0)}")
                _t359 = None
            _t358 = _t359
        return _t358

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal('(')
        _t360 = self.parse_bindings()
        bindings58 = _t360
        _t361 = self.parse_formula()
        formula59 = _t361
        self.consume_literal(')')
        _t362 = logic_pb2.Abstraction(bindings58[0] + bindings58[1], formula59)
        return _t362

    def parse_bindings(self) -> tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]:
        self.consume_literal('[')
        xs60 = []
        cond61 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond61:
            _t363 = self.parse_binding()
            xs60.append(_t363)
            cond61 = self.match_lookahead_terminal('SYMBOL', 0)
        keys62 = xs60
        if self.match_lookahead_literal('|', 0):
            _t365 = self.parse_value_bindings()
            _t364 = _t365
        else:
            _t364 = None
        values63 = _t364
        self.consume_literal(']')
        return (keys62, values63,)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol64 = self.consume_terminal('SYMBOL')
        self.consume_literal('::')
        _t366 = self.parse_type()
        type65 = _t366
        _t367 = logic_pb2.Var(symbol64)
        _t368 = logic_pb2.Binding(_t367, type65)
        return _t368

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal('BOOLEAN', 0):
            _t369 = 10
        else:
            if self.match_lookahead_literal('(', 0):
                _t370 = 9
            else:
                if self.match_lookahead_literal('MISSING', 0):
                    _t371 = 8
                else:
                    if self.match_lookahead_literal('DATE', 0):
                        _t372 = 6
                    else:
                        if self.match_lookahead_literal('INT128', 0):
                            _t373 = 5
                        else:
                            if self.match_lookahead_literal('FLOAT', 0):
                                _t374 = 3
                            else:
                                if self.match_lookahead_literal('INT', 0):
                                    _t375 = 2
                                else:
                                        if self.match_lookahead_literal('UNKNOWN', 0):
                                            _t376 = 0
                                        else:
                                            _t376 = -1
                                    _t375 = (self.match_lookahead_literal('STRING', 0) or _t376)
                                _t374 = _t375
                            _t373 = _t374
                        _t372 = _t373
                    _t371 = _t372
                _t370 = _t371
            _t369 = _t370
        prediction66 = _t369
        if prediction66 == 10:
            _t378 = self.parse_boolean_type()
            value77 = _t378
            _t379 = logic_pb2.Type(boolean_type=value77)
            _t377 = _t379
        else:
            if prediction66 == 9:
                _t381 = self.parse_decimal_type()
                value76 = _t381
                _t382 = logic_pb2.Type(decimal_type=value76)
                _t380 = _t382
            else:
                if prediction66 == 8:
                    _t384 = self.parse_missing_type()
                    value75 = _t384
                    _t385 = logic_pb2.Type(missing_type=value75)
                    _t383 = _t385
                else:
                    if prediction66 == 7:
                        _t387 = self.parse_datetime_type()
                        value74 = _t387
                        _t388 = logic_pb2.Type(datetime_type=value74)
                        _t386 = _t388
                    else:
                        if prediction66 == 6:
                            _t390 = self.parse_date_type()
                            value73 = _t390
                            _t391 = logic_pb2.Type(date_type=value73)
                            _t389 = _t391
                        else:
                            if prediction66 == 5:
                                _t393 = self.parse_int128_type()
                                value72 = _t393
                                _t394 = logic_pb2.Type(int128_type=value72)
                                _t392 = _t394
                            else:
                                if prediction66 == 4:
                                    _t396 = self.parse_uint128_type()
                                    value71 = _t396
                                    _t397 = logic_pb2.Type(uint128_type=value71)
                                    _t395 = _t397
                                else:
                                    if prediction66 == 3:
                                        _t399 = self.parse_float_type()
                                        value70 = _t399
                                        _t400 = logic_pb2.Type(float_type=value70)
                                        _t398 = _t400
                                    else:
                                        if prediction66 == 2:
                                            _t402 = self.parse_int_type()
                                            value69 = _t402
                                            _t403 = logic_pb2.Type(int_type=value69)
                                            _t401 = _t403
                                        else:
                                            if prediction66 == 1:
                                                _t405 = self.parse_string_type()
                                                value68 = _t405
                                                _t406 = logic_pb2.Type(string_type=value68)
                                                _t404 = _t406
                                            else:
                                                if prediction66 == 0:
                                                    _t408 = self.parse_unspecified_type()
                                                    value67 = _t408
                                                    _t409 = logic_pb2.Type(unspecified_type=value67)
                                                    _t407 = _t409
                                                else:
                                                    raise ParseError('Unexpected token in type' + ": {self.lookahead(0)}")
                                                    _t407 = None
                                                _t404 = _t407
                                            _t401 = _t404
                                        _t398 = _t401
                                    _t395 = _t398
                                _t392 = _t395
                            _t389 = _t392
                        _t386 = _t389
                    _t383 = _t386
                _t380 = _t383
            _t377 = _t380
        return _t377

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        self.consume_literal('UNKNOWN')
        _t410 = logic_pb2.UnspecifiedType()
        return _t410

    def parse_string_type(self) -> logic_pb2.StringType:
        self.consume_literal('STRING')
        _t411 = logic_pb2.StringType()
        return _t411

    def parse_int_type(self) -> logic_pb2.IntType:
        self.consume_literal('INT')
        _t412 = logic_pb2.IntType()
        return _t412

    def parse_float_type(self) -> logic_pb2.FloatType:
        self.consume_literal('FLOAT')
        _t413 = logic_pb2.FloatType()
        return _t413

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        self.consume_literal('INT128')
        _t414 = logic_pb2.Int128Type()
        return _t414

    def parse_date_type(self) -> logic_pb2.DateType:
        self.consume_literal('DATE')
        _t415 = logic_pb2.DateType()
        return _t415

    def parse_missing_type(self) -> logic_pb2.MissingType:
        self.consume_literal('MISSING')
        _t416 = logic_pb2.MissingType()
        return _t416

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        self.consume_literal('(')
        self.consume_literal('DECIMAL')
        precision78 = self.consume_terminal('INT')
        scale79 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t417 = logic_pb2.DecimalType(precision78, scale79)
        return _t417

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal('BOOLEAN')
        _t418 = logic_pb2.BooleanType()
        return _t418

    def parse_value_bindings(self) -> list[logic_pb2.Binding]:
        self.consume_literal('|')
        xs80 = []
        cond81 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond81:
            _t419 = self.parse_binding()
            xs80.append(_t419)
            cond81 = self.match_lookahead_terminal('SYMBOL', 0)
        values82 = xs80
        return values82

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('cast', 1):
                _t421 = 12
            else:
                if self.match_lookahead_literal('relatom', 1):
                    _t422 = 11
                else:
                    if self.match_lookahead_literal('+', 1):
                        _t423 = 10
                    else:
                        if self.match_lookahead_literal('*', 1):
                            _t424 = 10
                        else:
                            if self.match_lookahead_literal('<=', 1):
                                _t425 = 10
                            else:
                                if self.match_lookahead_literal('-', 1):
                                    _t426 = 10
                                else:
                                    if self.match_lookahead_literal('>=', 1):
                                        _t427 = 10
                                    else:
                                        if self.match_lookahead_literal('<', 1):
                                            _t428 = 10
                                        else:
                                            if self.match_lookahead_literal('/', 1):
                                                _t429 = 10
                                            else:
                                                if self.match_lookahead_literal('primitive', 1):
                                                    _t430 = 10
                                                else:
                                                    if self.match_lookahead_literal('=', 1):
                                                        _t431 = 10
                                                    else:
                                                        if self.match_lookahead_literal('>', 1):
                                                            _t432 = 10
                                                        else:
                                                            if self.match_lookahead_literal('pragma', 1):
                                                                _t433 = 9
                                                            else:
                                                                if self.match_lookahead_literal('atom', 1):
                                                                    _t434 = 8
                                                                else:
                                                                    if self.match_lookahead_literal('ffi', 1):
                                                                        _t435 = 7
                                                                    else:
                                                                        if self.match_lookahead_literal('not', 1):
                                                                            _t436 = 6
                                                                        else:
                                                                            if self.match_lookahead_literal('or', 1):
                                                                                _t437 = 5
                                                                            else:
                                                                                if self.match_lookahead_literal('and', 1):
                                                                                    _t438 = 4
                                                                                else:
                                                                                    if self.match_lookahead_literal('reduce', 1):
                                                                                        _t439 = 3
                                                                                    else:
                                                                                        if self.match_lookahead_literal('exists', 1):
                                                                                            _t440 = 2
                                                                                        else:
                                                                                                if self.match_lookahead_literal('true', 1):
                                                                                                    _t441 = 0
                                                                                                else:
                                                                                                    _t441 = -1
                                                                                            _t440 = (self.match_lookahead_literal('false', 1) or _t441)
                                                                                        _t439 = _t440
                                                                                    _t438 = _t439
                                                                                _t437 = _t438
                                                                            _t436 = _t437
                                                                        _t435 = _t436
                                                                    _t434 = _t435
                                                                _t433 = _t434
                                                            _t432 = _t433
                                                        _t431 = _t432
                                                    _t430 = _t431
                                                _t429 = _t430
                                            _t428 = _t429
                                        _t427 = _t428
                                    _t426 = _t427
                                _t425 = _t426
                            _t424 = _t425
                        _t423 = _t424
                    _t422 = _t423
                _t421 = _t422
            _t420 = _t421
        else:
            _t420 = -1
        prediction83 = _t420
        if prediction83 == 12:
            _t443 = self.parse_cast()
            value96 = _t443
            _t444 = logic_pb2.Formula(cast=value96)
            _t442 = _t444
        else:
            if prediction83 == 11:
                _t446 = self.parse_relatom()
                value95 = _t446
                _t447 = logic_pb2.Formula(rel_atom=value95)
                _t445 = _t447
            else:
                if prediction83 == 10:
                    _t449 = self.parse_primitive()
                    value94 = _t449
                    _t450 = logic_pb2.Formula(primitive=value94)
                    _t448 = _t450
                else:
                    if prediction83 == 9:
                        _t452 = self.parse_pragma()
                        value93 = _t452
                        _t453 = logic_pb2.Formula(pragma=value93)
                        _t451 = _t453
                    else:
                        if prediction83 == 8:
                            _t455 = self.parse_atom()
                            value92 = _t455
                            _t456 = logic_pb2.Formula(atom=value92)
                            _t454 = _t456
                        else:
                            if prediction83 == 7:
                                _t458 = self.parse_ffi()
                                value91 = _t458
                                _t459 = logic_pb2.Formula(ffi=value91)
                                _t457 = _t459
                            else:
                                if prediction83 == 6:
                                    _t461 = self.parse_not()
                                    value90 = _t461
                                    _t462 = logic_pb2.Formula(not=value90)
                                    _t460 = _t462
                                else:
                                    if prediction83 == 5:
                                        _t464 = self.parse_disjunction()
                                        value89 = _t464
                                        _t465 = logic_pb2.Formula(disjunction=value89)
                                        _t463 = _t465
                                    else:
                                        if prediction83 == 4:
                                            _t467 = self.parse_conjunction()
                                            value88 = _t467
                                            _t468 = logic_pb2.Formula(conjunction=value88)
                                            _t466 = _t468
                                        else:
                                            if prediction83 == 3:
                                                _t470 = self.parse_reduce()
                                                value87 = _t470
                                                _t471 = logic_pb2.Formula(reduce=value87)
                                                _t469 = _t471
                                            else:
                                                if prediction83 == 2:
                                                    _t473 = self.parse_exists()
                                                    value86 = _t473
                                                    _t474 = logic_pb2.Formula(exists=value86)
                                                    _t472 = _t474
                                                else:
                                                    if prediction83 == 1:
                                                        _t476 = self.parse_false()
                                                        value85 = _t476
                                                        _t477 = logic_pb2.Formula(false=value85)
                                                        _t475 = _t477
                                                    else:
                                                        if prediction83 == 0:
                                                            _t479 = self.parse_true()
                                                            value84 = _t479
                                                            _t480 = logic_pb2.Formula(true=value84)
                                                            _t478 = _t480
                                                        else:
                                                            raise ParseError('Unexpected token in formula' + ": {self.lookahead(0)}")
                                                            _t478 = None
                                                        _t475 = _t478
                                                    _t472 = _t475
                                                _t469 = _t472
                                            _t466 = _t469
                                        _t463 = _t466
                                    _t460 = _t463
                                _t457 = _t460
                            _t454 = _t457
                        _t451 = _t454
                    _t448 = _t451
                _t445 = _t448
            _t442 = _t445
        return _t442

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('true')
        self.consume_literal(')')
        _t481 = logic_pb2.Conjunction([])
        return _t481

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('false')
        self.consume_literal(')')
        _t482 = logic_pb2.Disjunction([])
        return _t482

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal('(')
        self.consume_literal('exists')
        _t483 = self.parse_bindings()
        bindings97 = _t483
        _t484 = self.parse_formula()
        formula98 = _t484
        self.consume_literal(')')
        _t485 = logic_pb2.Abstraction(bindings97[0] + bindings97[1], formula98)
        _t486 = logic_pb2.Exists(_t485)
        return _t486

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal('(')
        self.consume_literal('reduce')
        _t487 = self.parse_abstraction()
        op99 = _t487
        _t488 = self.parse_abstraction()
        body100 = _t488
        if self.match_lookahead_literal('(', 0):
            _t490 = self.parse_terms()
            _t489 = _t490
        else:
            _t489 = None
        terms101 = _t489
        self.consume_literal(')')
        _t491 = logic_pb2.Reduce(op99, body100, (terms101 if terms101 is not None else []))
        return _t491

    def parse_terms(self) -> list[logic_pb2.Term]:
        self.consume_literal('(')
        self.consume_literal('terms')
        xs102 = []
        cond103 = ((((((((((self.match_lookahead_literal('false', 0) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('FLOAT', 0))
        while cond103:
            _t492 = self.parse_term()
            xs102.append(_t492)
            cond103 = ((((((((((self.match_lookahead_literal('false', 0) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('FLOAT', 0))
        value104 = xs102
        self.consume_literal(')')
        return value104

    def parse_term(self) -> logic_pb2.Term:
                                                if self.match_lookahead_terminal('SYMBOL', 0):
                                                    _t493 = 0
                                                else:
                                                    _t493 = -1
        prediction105 = (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_literal('(', 0) or (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_literal('false', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or (self.match_lookahead_terminal('UINT128', 0) or (self.match_lookahead_literal('true', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_literal('missing', 0) or (self.match_lookahead_terminal('INT128', 0) or _t493))))))))))
        if prediction105 == 1:
            _t495 = self.parse_constant()
            value107 = _t495
            _t496 = logic_pb2.Term(constant=value107)
            _t494 = _t496
        else:
            if prediction105 == 0:
                _t498 = self.parse_var()
                value106 = _t498
                _t499 = logic_pb2.Term(var=value106)
                _t497 = _t499
            else:
                raise ParseError('Unexpected token in term' + ": {self.lookahead(0)}")
                _t497 = None
            _t494 = _t497
        return _t494

    def parse_var(self) -> logic_pb2.Var:
        symbol108 = self.consume_terminal('SYMBOL')
        _t500 = logic_pb2.Var(symbol108)
        return _t500

    def parse_constant(self) -> logic_pb2.Value:
        _t501 = self.parse_value()
        x109 = _t501
        return x109

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('and')
        xs110 = []
        cond111 = self.match_lookahead_literal('(', 0)
        while cond111:
            _t502 = self.parse_formula()
            xs110.append(_t502)
            cond111 = self.match_lookahead_literal('(', 0)
        args112 = xs110
        self.consume_literal(')')
        _t503 = logic_pb2.Conjunction(args112)
        return _t503

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('or')
        xs113 = []
        cond114 = self.match_lookahead_literal('(', 0)
        while cond114:
            _t504 = self.parse_formula()
            xs113.append(_t504)
            cond114 = self.match_lookahead_literal('(', 0)
        args115 = xs113
        self.consume_literal(')')
        _t505 = logic_pb2.Disjunction(args115)
        return _t505

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal('(')
        self.consume_literal('not')
        _t506 = self.parse_formula()
        arg116 = _t506
        self.consume_literal(')')
        _t507 = logic_pb2.Not(arg116)
        return _t507

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal('(')
        self.consume_literal('ffi')
        _t508 = self.parse_name()
        name117 = _t508
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('args', 1)):
            _t510 = self.parse_ffi_args()
            _t509 = _t510
        else:
            _t509 = None
        args118 = _t509
        if self.match_lookahead_literal('(', 0):
            _t512 = self.parse_terms()
            _t511 = _t512
        else:
            _t511 = None
        terms119 = _t511
        self.consume_literal(')')
        _t513 = logic_pb2.FFI(name117, (args118 if args118 is not None else []), (terms119 if terms119 is not None else []))
        return _t513

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
            _t514 = self.parse_abstraction()
            xs121.append(_t514)
            cond122 = self.match_lookahead_literal('(', 0)
        value123 = xs121
        self.consume_literal(')')
        return value123

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal('(')
        self.consume_literal('atom')
        _t515 = self.parse_relation_id()
        name124 = _t515
        xs125 = []
        cond126 = ((((((((((self.match_lookahead_literal('false', 0) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('FLOAT', 0))
        while cond126:
            _t516 = self.parse_term()
            xs125.append(_t516)
            cond126 = ((((((((((self.match_lookahead_literal('false', 0) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('FLOAT', 0))
        terms127 = xs125
        self.consume_literal(')')
        _t517 = logic_pb2.Atom(name124, terms127)
        return _t517

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal('(')
        self.consume_literal('pragma')
        _t518 = self.parse_name()
        name128 = _t518
        xs129 = []
        cond130 = ((((((((((self.match_lookahead_literal('false', 0) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('FLOAT', 0))
        while cond130:
            _t519 = self.parse_term()
            xs129.append(_t519)
            cond130 = ((((((((((self.match_lookahead_literal('false', 0) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('FLOAT', 0))
        terms131 = xs129
        self.consume_literal(')')
        _t520 = logic_pb2.Pragma(name128, terms131)
        return _t520

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('primitive', 1):
                _t522 = 9
            else:
                if self.match_lookahead_literal('/', 1):
                    _t523 = 8
                else:
                    if self.match_lookahead_literal('*', 1):
                        _t524 = 7
                    else:
                        if self.match_lookahead_literal('-', 1):
                            _t525 = 6
                        else:
                            if self.match_lookahead_literal('+', 1):
                                _t526 = 5
                            else:
                                if self.match_lookahead_literal('>=', 1):
                                    _t527 = 4
                                else:
                                    if self.match_lookahead_literal('>', 1):
                                        _t528 = 3
                                    else:
                                        if self.match_lookahead_literal('<=', 1):
                                            _t529 = 2
                                        else:
                                                if self.match_lookahead_literal('=', 1):
                                                    _t530 = 0
                                                else:
                                                    _t530 = -1
                                            _t529 = (self.match_lookahead_literal('<', 1) or _t530)
                                        _t528 = _t529
                                    _t527 = _t528
                                _t526 = _t527
                            _t525 = _t526
                        _t524 = _t525
                    _t523 = _t524
                _t522 = _t523
            _t521 = _t522
        else:
            _t521 = -1
        prediction132 = _t521
        if prediction132 == 9:
            self.consume_literal('(')
            self.consume_literal('primitive')
            _t532 = self.parse_name()
            name142 = _t532
            xs143 = []
            cond144 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('FLOAT', 0))
            while cond144:
                _t533 = self.parse_relterm()
                xs143.append(_t533)
                cond144 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('FLOAT', 0))
            terms145 = xs143
            self.consume_literal(')')
            _t534 = logic_pb2.Primitive(name142, terms145)
            _t531 = _t534
        else:
            if prediction132 == 8:
                _t536 = self.parse_divide()
                op141 = _t536
                _t535 = op141
            else:
                if prediction132 == 7:
                    _t538 = self.parse_multiply()
                    op140 = _t538
                    _t537 = op140
                else:
                    if prediction132 == 6:
                        _t540 = self.parse_minus()
                        op139 = _t540
                        _t539 = op139
                    else:
                        if prediction132 == 5:
                            _t542 = self.parse_add()
                            op138 = _t542
                            _t541 = op138
                        else:
                            if prediction132 == 4:
                                _t544 = self.parse_gt_eq()
                                op137 = _t544
                                _t543 = op137
                            else:
                                if prediction132 == 3:
                                    _t546 = self.parse_gt()
                                    op136 = _t546
                                    _t545 = op136
                                else:
                                    if prediction132 == 2:
                                        _t548 = self.parse_lt_eq()
                                        op135 = _t548
                                        _t547 = op135
                                    else:
                                        if prediction132 == 1:
                                            _t550 = self.parse_lt()
                                            op134 = _t550
                                            _t549 = op134
                                        else:
                                            if prediction132 == 0:
                                                _t552 = self.parse_eq()
                                                op133 = _t552
                                                _t551 = op133
                                            else:
                                                raise ParseError('Unexpected token in primitive' + ": {self.lookahead(0)}")
                                                _t551 = None
                                            _t549 = _t551
                                        _t547 = _t549
                                    _t545 = _t547
                                _t543 = _t545
                            _t541 = _t543
                        _t539 = _t541
                    _t537 = _t539
                _t535 = _t537
            _t531 = _t535
        return _t531

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('=')
        _t553 = self.parse_term()
        left146 = _t553
        _t554 = self.parse_term()
        right147 = _t554
        self.consume_literal(')')
        _t555 = logic_pb2.Primitive('rel_primitive_eq', left146, right147)
        return _t555

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<')
        _t556 = self.parse_term()
        left148 = _t556
        _t557 = self.parse_term()
        right149 = _t557
        self.consume_literal(')')
        _t558 = logic_pb2.Primitive('rel_primitive_lt', left148, right149)
        return _t558

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<=')
        _t559 = self.parse_term()
        left150 = _t559
        _t560 = self.parse_term()
        right151 = _t560
        self.consume_literal(')')
        _t561 = logic_pb2.Primitive('rel_primitive_lt_eq', left150, right151)
        return _t561

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>')
        _t562 = self.parse_term()
        left152 = _t562
        _t563 = self.parse_term()
        right153 = _t563
        self.consume_literal(')')
        _t564 = logic_pb2.Primitive('rel_primitive_gt', left152, right153)
        return _t564

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>=')
        _t565 = self.parse_term()
        left154 = _t565
        _t566 = self.parse_term()
        right155 = _t566
        self.consume_literal(')')
        _t567 = logic_pb2.Primitive('rel_primitive_gt_eq', left154, right155)
        return _t567

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('+')
        _t568 = self.parse_term()
        left156 = _t568
        _t569 = self.parse_term()
        right157 = _t569
        _t570 = self.parse_term()
        result158 = _t570
        self.consume_literal(')')
        _t571 = logic_pb2.Primitive('rel_primitive_add', left156, right157, result158)
        return _t571

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('-')
        _t572 = self.parse_term()
        left159 = _t572
        _t573 = self.parse_term()
        right160 = _t573
        _t574 = self.parse_term()
        result161 = _t574
        self.consume_literal(')')
        _t575 = logic_pb2.Primitive('rel_primitive_subtract', left159, right160, result161)
        return _t575

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('*')
        _t576 = self.parse_term()
        left162 = _t576
        _t577 = self.parse_term()
        right163 = _t577
        _t578 = self.parse_term()
        result164 = _t578
        self.consume_literal(')')
        _t579 = logic_pb2.Primitive('rel_primitive_multiply', left162, right163, result164)
        return _t579

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('/')
        _t580 = self.parse_term()
        left165 = _t580
        _t581 = self.parse_term()
        right166 = _t581
        _t582 = self.parse_term()
        result167 = _t582
        self.consume_literal(')')
        _t583 = logic_pb2.Primitive('rel_primitive_divide', left165, right166, result167)
        return _t583

    def parse_relterm(self) -> logic_pb2.RelTerm:
                                                    if self.match_lookahead_literal('#', 0):
                                                        _t584 = 0
                                                    else:
                                                        _t584 = -1
        prediction168 = (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_literal('(', 0) or (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_literal('false', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or (self.match_lookahead_terminal('UINT128', 0) or (self.match_lookahead_literal('true', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_literal('missing', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('SYMBOL', 0) or _t584)))))))))))
        if prediction168 == 1:
            _t586 = self.parse_term()
            value170 = _t586
            _t587 = logic_pb2.RelTerm(term=value170)
            _t585 = _t587
        else:
            if prediction168 == 0:
                _t589 = self.parse_specialized_value()
                value169 = _t589
                _t590 = logic_pb2.RelTerm(specialized_value=value169)
                _t588 = _t590
            else:
                raise ParseError('Unexpected token in relterm' + ": {self.lookahead(0)}")
                _t588 = None
            _t585 = _t588
        return _t585

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal('#')
        _t591 = self.parse_value()
        value171 = _t591
        return value171

    def parse_relatom(self) -> logic_pb2.RelAtom:
        self.consume_literal('(')
        self.consume_literal('relatom')
        _t592 = self.parse_name()
        name172 = _t592
        xs173 = []
        cond174 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('FLOAT', 0))
        while cond174:
            _t593 = self.parse_relterm()
            xs173.append(_t593)
            cond174 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('FLOAT', 0))
        terms175 = xs173
        self.consume_literal(')')
        _t594 = logic_pb2.RelAtom(name172, terms175)
        return _t594

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal('(')
        self.consume_literal('cast')
        _t595 = self.parse_term()
        input176 = _t595
        _t596 = self.parse_term()
        result177 = _t596
        self.consume_literal(')')
        _t597 = logic_pb2.Cast(input176, result177)
        return _t597

    def parse_attrs(self) -> list[logic_pb2.Attribute]:
        self.consume_literal('(')
        self.consume_literal('attrs')
        xs178 = []
        cond179 = self.match_lookahead_literal('(', 0)
        while cond179:
            _t598 = self.parse_attribute()
            xs178.append(_t598)
            cond179 = self.match_lookahead_literal('(', 0)
        value180 = xs178
        self.consume_literal(')')
        return value180

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal('(')
        self.consume_literal('attribute')
        _t599 = self.parse_name()
        name181 = _t599
        xs182 = []
        cond183 = (((((((((self.match_lookahead_literal('false', 0) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_terminal('FLOAT', 0))
        while cond183:
            _t600 = self.parse_value()
            xs182.append(_t600)
            cond183 = (((((((((self.match_lookahead_literal('false', 0) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_terminal('FLOAT', 0))
        args184 = xs182
        self.consume_literal(')')
        _t601 = logic_pb2.Attribute(name181, args184)
        return _t601

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal('(')
        self.consume_literal('algorithm')
        xs185 = []
        cond186 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        while cond186:
            _t602 = self.parse_relation_id()
            xs185.append(_t602)
            cond186 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        global187 = xs185
        _t603 = self.parse_script()
        body188 = _t603
        self.consume_literal(')')
        _t604 = logic_pb2.Algorithm(global187, body188)
        return _t604

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal('(')
        self.consume_literal('script')
        xs189 = []
        cond190 = self.match_lookahead_literal('(', 0)
        while cond190:
            _t605 = self.parse_construct()
            xs189.append(_t605)
            cond190 = self.match_lookahead_literal('(', 0)
        constructs191 = xs189
        self.consume_literal(')')
        _t606 = logic_pb2.Script(constructs191)
        return _t606

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal('(', 0):
                                if self.match_lookahead_literal('loop', 1):
                                    _t608 = 0
                                else:
                                    _t608 = -1
            _t607 = (self.match_lookahead_literal('assign', 1) or (self.match_lookahead_literal('monoid', 1) or (self.match_lookahead_literal('break', 1) or (self.match_lookahead_literal('monus', 1) or (self.match_lookahead_literal('upsert', 1) or _t608)))))
        else:
            _t607 = -1
        prediction192 = _t607
        if prediction192 == 1:
            _t610 = self.parse_instruction()
            value194 = _t610
            _t611 = logic_pb2.Construct(instruction=value194)
            _t609 = _t611
        else:
            if prediction192 == 0:
                _t613 = self.parse_loop()
                value193 = _t613
                _t614 = logic_pb2.Construct(loop=value193)
                _t612 = _t614
            else:
                raise ParseError('Unexpected token in construct' + ": {self.lookahead(0)}")
                _t612 = None
            _t609 = _t612
        return _t609

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal('(')
        self.consume_literal('loop')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('init', 1)):
            _t616 = self.parse_loop_init()
            _t615 = _t616
        else:
            _t615 = None
        init195 = _t615
        _t617 = self.parse_script()
        body196 = _t617
        self.consume_literal(')')
        _t618 = logic_pb2.Loop((init195 if init195 is not None else []), body196)
        return _t618

    def parse_loop_init(self) -> list[logic_pb2.Instruction]:
        self.consume_literal('(')
        self.consume_literal('init')
        xs197 = []
        cond198 = self.match_lookahead_literal('(', 0)
        while cond198:
            _t619 = self.parse_instruction()
            xs197.append(_t619)
            cond198 = self.match_lookahead_literal('(', 0)
        value199 = xs197
        self.consume_literal(')')
        return value199

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('monus', 1):
                _t621 = 4
            else:
                if self.match_lookahead_literal('monoid', 1):
                    _t622 = 3
                else:
                    if self.match_lookahead_literal('break', 1):
                        _t623 = 2
                    else:
                            if self.match_lookahead_literal('assign', 1):
                                _t624 = 0
                            else:
                                _t624 = -1
                        _t623 = (self.match_lookahead_literal('upsert', 1) or _t624)
                    _t622 = _t623
                _t621 = _t622
            _t620 = _t621
        else:
            _t620 = -1
        prediction200 = _t620
        if prediction200 == 4:
            _t626 = self.parse_monus_def()
            value205 = _t626
            _t627 = logic_pb2.Instruction(monus_def=value205)
            _t625 = _t627
        else:
            if prediction200 == 3:
                _t629 = self.parse_monoid_def()
                value204 = _t629
                _t630 = logic_pb2.Instruction(monoid_def=value204)
                _t628 = _t630
            else:
                if prediction200 == 2:
                    _t632 = self.parse_break()
                    value203 = _t632
                    _t633 = logic_pb2.Instruction(break=value203)
                    _t631 = _t633
                else:
                    if prediction200 == 1:
                        _t635 = self.parse_upsert()
                        value202 = _t635
                        _t636 = logic_pb2.Instruction(upsert=value202)
                        _t634 = _t636
                    else:
                        if prediction200 == 0:
                            _t638 = self.parse_assign()
                            value201 = _t638
                            _t639 = logic_pb2.Instruction(assign=value201)
                            _t637 = _t639
                        else:
                            raise ParseError('Unexpected token in instruction' + ": {self.lookahead(0)}")
                            _t637 = None
                        _t634 = _t637
                    _t631 = _t634
                _t628 = _t631
            _t625 = _t628
        return _t625

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal('(')
        self.consume_literal('assign')
        _t640 = self.parse_relation_id()
        name206 = _t640
        _t641 = self.parse_abstraction()
        body207 = _t641
        if self.match_lookahead_literal('(', 0):
            _t643 = self.parse_attrs()
            _t642 = _t643
        else:
            _t642 = None
        attrs208 = _t642
        self.consume_literal(')')
        _t644 = logic_pb2.Assign(name206, body207, (attrs208 if attrs208 is not None else []))
        return _t644

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal('(')
        self.consume_literal('upsert')
        _t645 = self.parse_relation_id()
        name209 = _t645
        _t646 = self.parse_abstraction_with_arity()
        body210 = _t646
        if self.match_lookahead_literal('(', 0):
            _t648 = self.parse_attrs()
            _t647 = _t648
        else:
            _t647 = None
        attrs211 = _t647
        self.consume_literal(')')
        _t649 = logic_pb2.Upsert(name209, body210[0], (attrs211 if attrs211 is not None else []), body210[1])
        return _t649

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal('(')
        _t650 = self.parse_bindings()
        bindings212 = _t650
        _t651 = self.parse_formula()
        formula213 = _t651
        self.consume_literal(')')
        _t652 = logic_pb2.Abstraction(bindings212[0] + bindings212[1], formula213)
        return (_t652, len(bindings212[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal('(')
        self.consume_literal('break')
        _t653 = self.parse_relation_id()
        name214 = _t653
        _t654 = self.parse_abstraction()
        body215 = _t654
        if self.match_lookahead_literal('(', 0):
            _t656 = self.parse_attrs()
            _t655 = _t656
        else:
            _t655 = None
        attrs216 = _t655
        self.consume_literal(')')
        _t657 = logic_pb2.Break(name214, body215, (attrs216 if attrs216 is not None else []))
        return _t657

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal('(')
        self.consume_literal('monoid')
        _t658 = self.parse_monoid()
        monoid217 = _t658
        _t659 = self.parse_relation_id()
        name218 = _t659
        _t660 = self.parse_abstraction_with_arity()
        body219 = _t660
        if self.match_lookahead_literal('(', 0):
            _t662 = self.parse_attrs()
            _t661 = _t662
        else:
            _t661 = None
        attrs220 = _t661
        self.consume_literal(')')
        _t663 = logic_pb2.MonoidDef(monoid217, name218, body219[0], (attrs220 if attrs220 is not None else []), body219[1])
        return _t663

    def parse_monoid(self) -> logic_pb2.Monoid:
        _t664 = self.parse_type()
        type221 = _t664
        self.consume_literal('::')
        _t665 = self.parse_monoid_op()
        op222 = _t665
        _t666 = op222(type221)
        return _t666

    def parse_monoid_op(self) -> Callable[[logic_pb2.Type], logic_pb2.Monoid]:
        if self.match_lookahead_literal('SUM', 0):
            _t667 = 3
        else:
            if self.match_lookahead_literal('MAX', 0):
                _t668 = 2
            else:
                    if self.match_lookahead_literal('OR', 0):
                        _t669 = 0
                    else:
                        _t669 = -1
                _t668 = (self.match_lookahead_literal('MIN', 0) or _t669)
            _t667 = _t668
        prediction223 = _t667
        if prediction223 == 3:
            self.consume_literal('SUM')
            def _t671(type):
                _t672 = logic_pb2.SumMonoid(type)
                _t673 = logic_pb2.Monoid(sum=_t672)
                return _t673
            _t670 = _t671
        else:
            if prediction223 == 2:
                self.consume_literal('MAX')
                def _t675(type):
                    _t676 = logic_pb2.MaxMonoid(type)
                    _t677 = logic_pb2.Monoid(max_monoid=_t676)
                    return _t677
                _t674 = _t675
            else:
                if prediction223 == 1:
                    self.consume_literal('MIN')
                    def _t679(type):
                        _t680 = logic_pb2.MinMonoid(type)
                        _t681 = logic_pb2.Monoid(min_monoid=_t680)
                        return _t681
                    _t678 = _t679
                else:
                    if prediction223 == 0:
                        self.consume_literal('OR')
                        def _t683(type):
                            _t684 = logic_pb2.OrMonoid()
                            _t685 = logic_pb2.Monoid(or_monoid=_t684)
                            return _t685
                        _t682 = _t683
                    else:
                        raise ParseError('Unexpected token in monoid_op' + ": {self.lookahead(0)}")
                        _t682 = None
                    _t678 = _t682
                _t674 = _t678
            _t670 = _t674
        return _t670

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal('(')
        self.consume_literal('monus')
        _t686 = self.parse_monoid()
        monoid224 = _t686
        _t687 = self.parse_relation_id()
        name225 = _t687
        _t688 = self.parse_abstraction_with_arity()
        body226 = _t688
        if self.match_lookahead_literal('(', 0):
            _t690 = self.parse_attrs()
            _t689 = _t690
        else:
            _t689 = None
        attrs227 = _t689
        self.consume_literal(')')
        _t691 = logic_pb2.MonusDef(monoid224, name225, body226[0], (attrs227 if attrs227 is not None else []), body226[1])
        return _t691

    def parse_constraint(self) -> logic_pb2.Constraint:
        _t692 = self.parse_functional_dependency()
        value228 = _t692
        _t693 = logic_pb2.Constraint(functional_dependency=value228)
        return _t693

    def parse_functional_dependency(self) -> logic_pb2.FunctionalDependency:
        self.consume_literal('(')
        self.consume_literal('functional_dependency')
        _t694 = self.parse_abstraction()
        guard229 = _t694
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('keys', 1)):
            _t696 = self.parse_functional_dependency_keys()
            _t695 = _t696
        else:
            _t695 = None
        keys230 = _t695
        if self.match_lookahead_literal('(', 0):
            _t698 = self.parse_functional_dependency_values()
            _t697 = _t698
        else:
            _t697 = None
        values231 = _t697
        self.consume_literal(')')
        _t699 = logic_pb2.FunctionalDependency(guard229, (keys230 if keys230 is not None else []), (values231 if values231 is not None else []))
        return _t699

    def parse_functional_dependency_keys(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('keys')
        xs232 = []
        cond233 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond233:
            _t700 = self.parse_var()
            xs232.append(_t700)
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
            _t701 = self.parse_var()
            xs235.append(_t701)
            cond236 = self.match_lookahead_terminal('SYMBOL', 0)
        value237 = xs235
        self.consume_literal(')')
        return value237

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal('(')
        self.consume_literal('undefine')
        _t702 = self.parse_fragment_id()
        fragment_id238 = _t702
        self.consume_literal(')')
        _t703 = transactions_pb2.Undefine(fragment_id238)
        return _t703

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal('(')
        self.consume_literal('context')
        xs239 = []
        cond240 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        while cond240:
            _t704 = self.parse_relation_id()
            xs239.append(_t704)
            cond240 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('INT', 0))
        relations241 = xs239
        self.consume_literal(')')
        _t705 = transactions_pb2.Context(relations241)
        return _t705

    def parse_epoch_reads(self) -> list[transactions_pb2.Read]:
        self.consume_literal('(')
        self.consume_literal('reads')
        xs242 = []
        cond243 = self.match_lookahead_literal('(', 0)
        while cond243:
            _t706 = self.parse_read()
            xs242.append(_t706)
            cond243 = self.match_lookahead_literal('(', 0)
        value244 = xs242
        self.consume_literal(')')
        return value244

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('export', 1):
                _t708 = 4
            else:
                if self.match_lookahead_literal('abort', 1):
                    _t709 = 3
                else:
                    if self.match_lookahead_literal('what_if', 1):
                        _t710 = 2
                    else:
                            if self.match_lookahead_literal('demand', 1):
                                _t711 = 0
                            else:
                                _t711 = -1
                        _t710 = (self.match_lookahead_literal('output', 1) or _t711)
                    _t709 = _t710
                _t708 = _t709
            _t707 = _t708
        else:
            _t707 = -1
        prediction245 = _t707
        if prediction245 == 4:
            _t713 = self.parse_export()
            value250 = _t713
            _t714 = transactions_pb2.Read(export=value250)
            _t712 = _t714
        else:
            if prediction245 == 3:
                _t716 = self.parse_abort()
                value249 = _t716
                _t717 = transactions_pb2.Read(abort=value249)
                _t715 = _t717
            else:
                if prediction245 == 2:
                    _t719 = self.parse_what_if()
                    value248 = _t719
                    _t720 = transactions_pb2.Read(what_if=value248)
                    _t718 = _t720
                else:
                    if prediction245 == 1:
                        _t722 = self.parse_output()
                        value247 = _t722
                        _t723 = transactions_pb2.Read(output=value247)
                        _t721 = _t723
                    else:
                        if prediction245 == 0:
                            _t725 = self.parse_demand()
                            value246 = _t725
                            _t726 = transactions_pb2.Read(demand=value246)
                            _t724 = _t726
                        else:
                            raise ParseError('Unexpected token in read' + ": {self.lookahead(0)}")
                            _t724 = None
                        _t721 = _t724
                    _t718 = _t721
                _t715 = _t718
            _t712 = _t715
        return _t712

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal('(')
        self.consume_literal('demand')
        _t727 = self.parse_relation_id()
        relation_id251 = _t727
        self.consume_literal(')')
        _t728 = transactions_pb2.Demand(relation_id251)
        return _t728

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal('(')
        self.consume_literal('output')
        if (self.match_lookahead_literal(':', 0) and self.match_lookahead_terminal('SYMBOL', 1)):
            _t730 = self.parse_name()
            _t729 = _t730
        else:
            _t729 = None
        name252 = _t729
        _t731 = self.parse_relation_id()
        relation_id253 = _t731
        self.consume_literal(')')
        _t732 = transactions_pb2.Output(name252, relation_id253)
        return _t732

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal('(')
        self.consume_literal('what_if')
        branch254 = self.consume_terminal('STRING')
        _t733 = self.parse_epoch()
        epoch255 = _t733
        self.consume_literal(')')
        _t734 = transactions_pb2.WhatIf(branch254, epoch255)
        return _t734

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal('(')
        self.consume_literal('abort')
        if (self.match_lookahead_literal(':', 0) and self.match_lookahead_terminal('SYMBOL', 1)):
            _t736 = self.parse_name()
            _t735 = _t736
        else:
            _t735 = None
        name256 = _t735
        _t737 = self.parse_relation_id()
        relation_id257 = _t737
        self.consume_literal(')')
        _t738 = transactions_pb2.Abort(name256, relation_id257)
        return _t738

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal('(')
        self.consume_literal('export')
        _t739 = self.parse_export_csvconfig()
        config258 = _t739
        self.consume_literal(')')
        _t740 = transactions_pb2.Export(config258)
        return _t740

    def parse_export_csvconfig(self) -> transactions_pb2.ExportCsvConfig:
        self.consume_literal('(')
        self.consume_literal('export_csvconfig')
        path259 = self.consume_terminal('STRING')
        _t741 = self.parse_export_csvcolumns()
        columns260 = _t741
        _t742 = self.parse_config_dict()
        config261 = _t742
        self.consume_literal(')')
        return self.export_csv_config(path259, columns260, config261)

    def parse_export_csvcolumns(self) -> list[transactions_pb2.ExportCsvColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs262 = []
        cond263 = self.match_lookahead_literal('(', 0)
        while cond263:
            _t743 = self.parse_export_csvcolumn()
            xs262.append(_t743)
            cond263 = self.match_lookahead_literal('(', 0)
        columns264 = xs262
        self.consume_literal(')')
        return columns264

    def parse_export_csvcolumn(self) -> transactions_pb2.ExportCsvColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        name265 = self.consume_terminal('STRING')
        _t744 = self.parse_relation_id()
        relation_id266 = _t744
        self.consume_literal(')')
        _t745 = transactions_pb2.ExportCsvColumn(name265, relation_id266)
        return _t745


def parse(input_str: str) -> Any:
    """Parse input string and return parse tree."""
    lexer = Lexer(input_str)
    parser = Parser(lexer.tokens)
    result = parser.parse_transaction()
    if parser.pos < len(parser.tokens):
        raise ParseError(f"Unexpected token at end of input: {parser.lookahead(0)}")
    return result
