"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.

Command: python-tools/src/meta/proto_tool.py proto/relationalai/lqp/v1/fragments.proto proto/relationalai/lqp/v1/logic.proto proto/relationalai/lqp/v1/transactions.proto --parser python -o python-tools/src/lqp/generated_parser.py
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
        return logic_pb2.UInt128Value(value=uint128_val, meta=None)

    @staticmethod
    def scan_int128(u: str) -> Any:
        """Parse INT128 token."""
        u = u[:-4]  # Remove the 'i128' suffix
        int128_val = int(u)
        return logic_pb2.Int128Value(value=int128_val, meta=None)

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
        return logic_pb2.DecimalValue(precision=precision, scale=scale, value=value, meta=None)


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

        return transactions_pb2.ExportCSVConfig(path=path_str, data_columns=columns, **kwargs)

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
        _t314 = logic_pb2.DateValue(year20, month21, day22)
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
        _t317 = logic_pb2.DateTimeValue(year23, month24, day25, hour26, minute27, second28, _t316)
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
        _t319 = transactions_pb2.Sync(fragments32)
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
        _t324 = transactions_pb2.Epoch((writes34 if writes34 is not None else []), (reads35 if reads35 is not None else []))
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
            if self.match_lookahead_literal('context', 1):
                _t327 = 2
            else:
                if self.match_lookahead_literal('undefine', 1):
                    _t329 = 1
                else:
                    if self.match_lookahead_literal('define', 1):
                        _t330 = 0
                    else:
                        _t330 = -1
                    _t329 = _t330
                _t327 = _t329
            _t326 = _t327
        else:
            _t326 = -1
        prediction39 = _t326
        if prediction39 == 2:
            _t332 = self.parse_context()
            value42 = _t332
            _t333 = transactions_pb2.Write(context=value42)
            _t331 = _t333
        else:
            if prediction39 == 1:
                _t335 = self.parse_undefine()
                value41 = _t335
                _t336 = transactions_pb2.Write(undefine=value41)
                _t334 = _t336
            else:
                if prediction39 == 0:
                    _t338 = self.parse_define()
                    value40 = _t338
                    _t339 = transactions_pb2.Write(define=value40)
                    _t337 = _t339
                else:
                    raise ParseError('Unexpected token in write' + ": {self.lookahead(0)}")
                    _t337 = None
                _t334 = _t337
            _t331 = _t334
        return _t331

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal('(')
        self.consume_literal('define')
        _t340 = self.parse_fragment()
        fragment43 = _t340
        self.consume_literal(')')
        _t341 = transactions_pb2.Define(fragment43)
        return _t341

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal('(')
        self.consume_literal('fragment')
        _t342 = self.parse_fragment_id()
        fragment_id44 = _t342
        xs45 = []
        cond46 = self.match_lookahead_literal('(', 0)
        while cond46:
            _t343 = self.parse_declaration()
            xs45.append(_t343)
            cond46 = self.match_lookahead_literal('(', 0)
        declarations47 = xs45
        self.consume_literal(')')
        return self.construct_fragment(fragment_id44, declarations47)

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('functional_dependency', 1):
                _t345 = 2
            else:
                if self.match_lookahead_literal('algorithm', 1):
                    _t347 = 1
                else:
                    if self.match_lookahead_literal('def', 1):
                        _t348 = 0
                    else:
                        _t348 = -1
                    _t347 = _t348
                _t345 = _t347
            _t344 = _t345
        else:
            _t344 = -1
        prediction48 = _t344
        if prediction48 == 2:
            _t350 = self.parse_constraint()
            value51 = _t350
            _t351 = logic_pb2.Declaration(constraint=value51)
            _t349 = _t351
        else:
            if prediction48 == 1:
                _t353 = self.parse_algorithm()
                value50 = _t353
                _t354 = logic_pb2.Declaration(algorithm=value50)
                _t352 = _t354
            else:
                if prediction48 == 0:
                    _t356 = self.parse_def()
                    value49 = _t356
                    _t357 = logic_pb2.Declaration(def_=value49)
                    _t355 = _t357
                else:
                    raise ParseError('Unexpected token in declaration' + ": {self.lookahead(0)}")
                    _t355 = None
                _t352 = _t355
            _t349 = _t352
        return _t349

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal('(')
        self.consume_literal('def')
        _t358 = self.parse_relation_id()
        name52 = _t358
        _t359 = self.parse_abstraction()
        body53 = _t359
        if self.match_lookahead_literal('(', 0):
            _t361 = self.parse_attrs()
            _t360 = _t361
        else:
            _t360 = None
        attrs54 = _t360
        self.consume_literal(')')
        _t362 = logic_pb2.Def(name52, body53, (attrs54 if attrs54 is not None else []))
        return _t362

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_terminal('INT', 0):
            _t364 = 1
        else:
            if self.match_lookahead_literal(':', 0):
                _t365 = 0
            else:
                _t365 = -1
            _t364 = _t365
        prediction55 = _t364
        if prediction55 == 1:
            INT57 = self.consume_terminal('INT')
            _t366 = logic_pb2.RelationId(id=INT57)
        else:
            if prediction55 == 0:
                self.consume_literal(':')
                symbol56 = self.consume_terminal('SYMBOL')
                _t367 = proto.RelationId(id=int(hashlib.sha256(symbol56.encode()).hexdigest()[:16], 16))
            else:
                raise ParseError('Unexpected token in relation_id' + ": {self.lookahead(0)}")
                _t367 = None
            _t366 = _t367
        return _t366

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal('(')
        _t368 = self.parse_bindings()
        bindings58 = _t368
        _t369 = self.parse_formula()
        formula59 = _t369
        self.consume_literal(')')
        _t370 = logic_pb2.Abstraction(bindings58[0] + bindings58[1], formula59)
        return _t370

    def parse_bindings(self) -> tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]:
        self.consume_literal('[')
        xs60 = []
        cond61 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond61:
            _t371 = self.parse_binding()
            xs60.append(_t371)
            cond61 = self.match_lookahead_terminal('SYMBOL', 0)
        keys62 = xs60
        if self.match_lookahead_literal('|', 0):
            _t373 = self.parse_value_bindings()
            _t372 = _t373
        else:
            _t372 = None
        values63 = _t372
        self.consume_literal(']')
        return (keys62, values63,)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol64 = self.consume_terminal('SYMBOL')
        self.consume_literal('::')
        _t374 = self.parse_type()
        type65 = _t374
        _t375 = logic_pb2.Var(symbol64)
        _t376 = logic_pb2.Binding(_t375, type65)
        return _t376

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal('BOOLEAN', 0):
            _t377 = 10
        else:
            if self.match_lookahead_literal('(', 0):
                _t378 = 9
            else:
                if self.match_lookahead_literal('MISSING', 0):
                    _t379 = 8
                else:
                    if self.match_lookahead_literal('DATE', 0):
                        _t380 = 6
                    else:
                        if self.match_lookahead_literal('INT128', 0):
                            _t381 = 5
                        else:
                            if self.match_lookahead_literal('FLOAT', 0):
                                _t382 = 3
                            else:
                                if self.match_lookahead_literal('INT', 0):
                                    _t383 = 2
                                else:
                                    if self.match_lookahead_literal('STRING', 0):
                                        _t385 = 1
                                    else:
                                        if self.match_lookahead_literal('UNKNOWN', 0):
                                            _t386 = 0
                                        else:
                                            _t386 = -1
                                        _t385 = _t386
                                    _t383 = _t385
                                _t382 = _t383
                            _t381 = _t382
                        _t380 = _t381
                    _t379 = _t380
                _t378 = _t379
            _t377 = _t378
        prediction66 = _t377
        if prediction66 == 10:
            _t388 = self.parse_boolean_type()
            value77 = _t388
            _t389 = logic_pb2.Type(boolean_type=value77)
            _t387 = _t389
        else:
            if prediction66 == 9:
                _t391 = self.parse_decimal_type()
                value76 = _t391
                _t392 = logic_pb2.Type(decimal_type=value76)
                _t390 = _t392
            else:
                if prediction66 == 8:
                    _t394 = self.parse_missing_type()
                    value75 = _t394
                    _t395 = logic_pb2.Type(missing_type=value75)
                    _t393 = _t395
                else:
                    if prediction66 == 7:
                        _t397 = self.parse_datetime_type()
                        value74 = _t397
                        _t398 = logic_pb2.Type(datetime_type=value74)
                        _t396 = _t398
                    else:
                        if prediction66 == 6:
                            _t400 = self.parse_date_type()
                            value73 = _t400
                            _t401 = logic_pb2.Type(date_type=value73)
                            _t399 = _t401
                        else:
                            if prediction66 == 5:
                                _t403 = self.parse_int128_type()
                                value72 = _t403
                                _t404 = logic_pb2.Type(int128_type=value72)
                                _t402 = _t404
                            else:
                                if prediction66 == 4:
                                    _t406 = self.parse_uint128_type()
                                    value71 = _t406
                                    _t407 = logic_pb2.Type(uint128_type=value71)
                                    _t405 = _t407
                                else:
                                    if prediction66 == 3:
                                        _t409 = self.parse_float_type()
                                        value70 = _t409
                                        _t410 = logic_pb2.Type(float_type=value70)
                                        _t408 = _t410
                                    else:
                                        if prediction66 == 2:
                                            _t412 = self.parse_int_type()
                                            value69 = _t412
                                            _t413 = logic_pb2.Type(int_type=value69)
                                            _t411 = _t413
                                        else:
                                            if prediction66 == 1:
                                                _t415 = self.parse_string_type()
                                                value68 = _t415
                                                _t416 = logic_pb2.Type(string_type=value68)
                                                _t414 = _t416
                                            else:
                                                if prediction66 == 0:
                                                    _t418 = self.parse_unspecified_type()
                                                    value67 = _t418
                                                    _t419 = logic_pb2.Type(unspecified_type=value67)
                                                    _t417 = _t419
                                                else:
                                                    raise ParseError('Unexpected token in type' + ": {self.lookahead(0)}")
                                                    _t417 = None
                                                _t414 = _t417
                                            _t411 = _t414
                                        _t408 = _t411
                                    _t405 = _t408
                                _t402 = _t405
                            _t399 = _t402
                        _t396 = _t399
                    _t393 = _t396
                _t390 = _t393
            _t387 = _t390
        return _t387

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        self.consume_literal('UNKNOWN')
        _t420 = logic_pb2.UnspecifiedType()
        return _t420

    def parse_string_type(self) -> logic_pb2.StringType:
        self.consume_literal('STRING')
        _t421 = logic_pb2.StringType()
        return _t421

    def parse_int_type(self) -> logic_pb2.IntType:
        self.consume_literal('INT')
        _t422 = logic_pb2.IntType()
        return _t422

    def parse_float_type(self) -> logic_pb2.FloatType:
        self.consume_literal('FLOAT')
        _t423 = logic_pb2.FloatType()
        return _t423

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        self.consume_literal('INT128')
        _t424 = logic_pb2.Int128Type()
        return _t424

    def parse_date_type(self) -> logic_pb2.DateType:
        self.consume_literal('DATE')
        _t425 = logic_pb2.DateType()
        return _t425

    def parse_missing_type(self) -> logic_pb2.MissingType:
        self.consume_literal('MISSING')
        _t426 = logic_pb2.MissingType()
        return _t426

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        self.consume_literal('(')
        self.consume_literal('DECIMAL')
        precision78 = self.consume_terminal('INT')
        scale79 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t427 = logic_pb2.DecimalType(precision78, scale79)
        return _t427

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal('BOOLEAN')
        _t428 = logic_pb2.BooleanType()
        return _t428

    def parse_value_bindings(self) -> list[logic_pb2.Binding]:
        self.consume_literal('|')
        xs80 = []
        cond81 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond81:
            _t429 = self.parse_binding()
            xs80.append(_t429)
            cond81 = self.match_lookahead_terminal('SYMBOL', 0)
        values82 = xs80
        return values82

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('cast', 1):
                _t431 = 12
            else:
                if self.match_lookahead_literal('relatom', 1):
                    _t432 = 11
                else:
                    if self.match_lookahead_literal('>=', 1):
                        _t433 = 10
                    else:
                        if self.match_lookahead_literal('>', 1):
                            _t434 = 10
                        else:
                            if self.match_lookahead_literal('primitive', 1):
                                _t435 = 10
                            else:
                                if self.match_lookahead_literal('=', 1):
                                    _t436 = 10
                                else:
                                    if self.match_lookahead_literal('<', 1):
                                        _t437 = 10
                                    else:
                                        if self.match_lookahead_literal('+', 1):
                                            _t438 = 10
                                        else:
                                            if self.match_lookahead_literal('/', 1):
                                                _t439 = 10
                                            else:
                                                if self.match_lookahead_literal('*', 1):
                                                    _t440 = 10
                                                else:
                                                    if self.match_lookahead_literal('<=', 1):
                                                        _t441 = 10
                                                    else:
                                                        if self.match_lookahead_literal('-', 1):
                                                            _t442 = 10
                                                        else:
                                                            if self.match_lookahead_literal('pragma', 1):
                                                                _t443 = 9
                                                            else:
                                                                if self.match_lookahead_literal('atom', 1):
                                                                    _t444 = 8
                                                                else:
                                                                    if self.match_lookahead_literal('ffi', 1):
                                                                        _t445 = 7
                                                                    else:
                                                                        if self.match_lookahead_literal('not', 1):
                                                                            _t446 = 6
                                                                        else:
                                                                            if self.match_lookahead_literal('or', 1):
                                                                                _t447 = 5
                                                                            else:
                                                                                if self.match_lookahead_literal('and', 1):
                                                                                    _t448 = 4
                                                                                else:
                                                                                    if self.match_lookahead_literal('reduce', 1):
                                                                                        _t449 = 3
                                                                                    else:
                                                                                        if self.match_lookahead_literal('exists', 1):
                                                                                            _t450 = 2
                                                                                        else:
                                                                                            if self.match_lookahead_literal('false', 1):
                                                                                                _t452 = 1
                                                                                            else:
                                                                                                if self.match_lookahead_literal('true', 1):
                                                                                                    _t453 = 0
                                                                                                else:
                                                                                                    _t453 = -1
                                                                                                _t452 = _t453
                                                                                            _t450 = _t452
                                                                                        _t449 = _t450
                                                                                    _t448 = _t449
                                                                                _t447 = _t448
                                                                            _t446 = _t447
                                                                        _t445 = _t446
                                                                    _t444 = _t445
                                                                _t443 = _t444
                                                            _t442 = _t443
                                                        _t441 = _t442
                                                    _t440 = _t441
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
        else:
            _t430 = -1
        prediction83 = _t430
        if prediction83 == 12:
            _t455 = self.parse_cast()
            value96 = _t455
            _t456 = logic_pb2.Formula(cast=value96)
            _t454 = _t456
        else:
            if prediction83 == 11:
                _t458 = self.parse_relatom()
                value95 = _t458
                _t459 = logic_pb2.Formula(rel_atom=value95)
                _t457 = _t459
            else:
                if prediction83 == 10:
                    _t461 = self.parse_primitive()
                    value94 = _t461
                    _t462 = logic_pb2.Formula(primitive=value94)
                    _t460 = _t462
                else:
                    if prediction83 == 9:
                        _t464 = self.parse_pragma()
                        value93 = _t464
                        _t465 = logic_pb2.Formula(pragma=value93)
                        _t463 = _t465
                    else:
                        if prediction83 == 8:
                            _t467 = self.parse_atom()
                            value92 = _t467
                            _t468 = logic_pb2.Formula(atom=value92)
                            _t466 = _t468
                        else:
                            if prediction83 == 7:
                                _t470 = self.parse_ffi()
                                value91 = _t470
                                _t471 = logic_pb2.Formula(ffi=value91)
                                _t469 = _t471
                            else:
                                if prediction83 == 6:
                                    _t473 = self.parse_not()
                                    value90 = _t473
                                    _t474 = logic_pb2.Formula(not_=value90)
                                    _t472 = _t474
                                else:
                                    if prediction83 == 5:
                                        _t476 = self.parse_disjunction()
                                        value89 = _t476
                                        _t477 = logic_pb2.Formula(disjunction=value89)
                                        _t475 = _t477
                                    else:
                                        if prediction83 == 4:
                                            _t479 = self.parse_conjunction()
                                            value88 = _t479
                                            _t480 = logic_pb2.Formula(conjunction=value88)
                                            _t478 = _t480
                                        else:
                                            if prediction83 == 3:
                                                _t482 = self.parse_reduce()
                                                value87 = _t482
                                                _t483 = logic_pb2.Formula(reduce=value87)
                                                _t481 = _t483
                                            else:
                                                if prediction83 == 2:
                                                    _t485 = self.parse_exists()
                                                    value86 = _t485
                                                    _t486 = logic_pb2.Formula(exists=value86)
                                                    _t484 = _t486
                                                else:
                                                    if prediction83 == 1:
                                                        _t488 = self.parse_false()
                                                        value85 = _t488
                                                        _t489 = logic_pb2.Formula(false=value85)
                                                        _t487 = _t489
                                                    else:
                                                        if prediction83 == 0:
                                                            _t491 = self.parse_true()
                                                            value84 = _t491
                                                            _t492 = logic_pb2.Formula(true=value84)
                                                            _t490 = _t492
                                                        else:
                                                            raise ParseError('Unexpected token in formula' + ": {self.lookahead(0)}")
                                                            _t490 = None
                                                        _t487 = _t490
                                                    _t484 = _t487
                                                _t481 = _t484
                                            _t478 = _t481
                                        _t475 = _t478
                                    _t472 = _t475
                                _t469 = _t472
                            _t466 = _t469
                        _t463 = _t466
                    _t460 = _t463
                _t457 = _t460
            _t454 = _t457
        return _t454

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('true')
        self.consume_literal(')')
        _t493 = logic_pb2.Conjunction([])
        return _t493

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('false')
        self.consume_literal(')')
        _t494 = logic_pb2.Disjunction([])
        return _t494

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal('(')
        self.consume_literal('exists')
        _t495 = self.parse_bindings()
        bindings97 = _t495
        _t496 = self.parse_formula()
        formula98 = _t496
        self.consume_literal(')')
        _t497 = logic_pb2.Abstraction(bindings97[0] + bindings97[1], formula98)
        _t498 = logic_pb2.Exists(_t497)
        return _t498

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal('(')
        self.consume_literal('reduce')
        _t499 = self.parse_abstraction()
        op99 = _t499
        _t500 = self.parse_abstraction()
        body100 = _t500
        if self.match_lookahead_literal('(', 0):
            _t502 = self.parse_terms()
            _t501 = _t502
        else:
            _t501 = None
        terms101 = _t501
        self.consume_literal(')')
        _t503 = logic_pb2.Reduce(op99, body100, (terms101 if terms101 is not None else []))
        return _t503

    def parse_terms(self) -> list[logic_pb2.Term]:
        self.consume_literal('(')
        self.consume_literal('terms')
        xs102 = []
        cond103 = ((((((((((self.match_lookahead_terminal('FLOAT', 0) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('STRING', 0))
        while cond103:
            _t504 = self.parse_term()
            xs102.append(_t504)
            cond103 = ((((((((((self.match_lookahead_terminal('FLOAT', 0) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('STRING', 0))
        value104 = xs102
        self.consume_literal(')')
        return value104

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_terminal('DECIMAL', 0):
            _t1528 = 1
        else:
            if self.match_lookahead_terminal('UINT128', 0):
                _t2040 = 1
            else:
                if self.match_lookahead_terminal('STRING', 0):
                    _t2296 = 1
                else:
                    if self.match_lookahead_terminal('INT', 0):
                        _t2424 = 1
                    else:
                        if self.match_lookahead_literal('(', 0):
                            _t2488 = 1
                        else:
                            if self.match_lookahead_terminal('INT128', 0):
                                _t2520 = 1
                            else:
                                if self.match_lookahead_literal('false', 0):
                                    _t2536 = 1
                                else:
                                    if self.match_lookahead_literal('true', 0):
                                        _t2544 = 1
                                    else:
                                        if self.match_lookahead_terminal('FLOAT', 0):
                                            _t2548 = 1
                                        else:
                                            if self.match_lookahead_literal('missing', 0):
                                                _t2550 = 1
                                            else:
                                                if self.match_lookahead_terminal('SYMBOL', 0):
                                                    _t2551 = 0
                                                else:
                                                    _t2551 = -1
                                                _t2550 = _t2551
                                            _t2548 = _t2550
                                        _t2544 = _t2548
                                    _t2536 = _t2544
                                _t2520 = _t2536
                            _t2488 = _t2520
                        _t2424 = _t2488
                    _t2296 = _t2424
                _t2040 = _t2296
            _t1528 = _t2040
        prediction105 = _t1528
        if prediction105 == 1:
            _t2553 = self.parse_constant()
            value107 = _t2553
            _t2554 = logic_pb2.Term(constant=value107)
            _t2552 = _t2554
        else:
            if prediction105 == 0:
                _t2556 = self.parse_var()
                value106 = _t2556
                _t2557 = logic_pb2.Term(var=value106)
                _t2555 = _t2557
            else:
                raise ParseError('Unexpected token in term' + ": {self.lookahead(0)}")
                _t2555 = None
            _t2552 = _t2555
        return _t2552

    def parse_var(self) -> logic_pb2.Var:
        symbol108 = self.consume_terminal('SYMBOL')
        _t2558 = logic_pb2.Var(symbol108)
        return _t2558

    def parse_constant(self) -> logic_pb2.Value:
        _t2559 = self.parse_value()
        x109 = _t2559
        return x109

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('and')
        xs110 = []
        cond111 = self.match_lookahead_literal('(', 0)
        while cond111:
            _t2560 = self.parse_formula()
            xs110.append(_t2560)
            cond111 = self.match_lookahead_literal('(', 0)
        args112 = xs110
        self.consume_literal(')')
        _t2561 = logic_pb2.Conjunction(args112)
        return _t2561

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('or')
        xs113 = []
        cond114 = self.match_lookahead_literal('(', 0)
        while cond114:
            _t2562 = self.parse_formula()
            xs113.append(_t2562)
            cond114 = self.match_lookahead_literal('(', 0)
        args115 = xs113
        self.consume_literal(')')
        _t2563 = logic_pb2.Disjunction(args115)
        return _t2563

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal('(')
        self.consume_literal('not')
        _t2564 = self.parse_formula()
        arg116 = _t2564
        self.consume_literal(')')
        _t2565 = logic_pb2.Not(arg116)
        return _t2565

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal('(')
        self.consume_literal('ffi')
        _t2566 = self.parse_name()
        name117 = _t2566
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('args', 1)):
            _t2568 = self.parse_ffi_args()
            _t2567 = _t2568
        else:
            _t2567 = None
        args118 = _t2567
        if self.match_lookahead_literal('(', 0):
            _t2570 = self.parse_terms()
            _t2569 = _t2570
        else:
            _t2569 = None
        terms119 = _t2569
        self.consume_literal(')')
        _t2571 = logic_pb2.FFI(name117, (args118 if args118 is not None else []), (terms119 if terms119 is not None else []))
        return _t2571

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
            _t2572 = self.parse_abstraction()
            xs121.append(_t2572)
            cond122 = self.match_lookahead_literal('(', 0)
        value123 = xs121
        self.consume_literal(')')
        return value123

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal('(')
        self.consume_literal('atom')
        _t2573 = self.parse_relation_id()
        name124 = _t2573
        xs125 = []
        cond126 = ((((((((((self.match_lookahead_terminal('FLOAT', 0) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('STRING', 0))
        while cond126:
            _t2574 = self.parse_term()
            xs125.append(_t2574)
            cond126 = ((((((((((self.match_lookahead_terminal('FLOAT', 0) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('STRING', 0))
        terms127 = xs125
        self.consume_literal(')')
        _t2575 = logic_pb2.Atom(name124, terms127)
        return _t2575

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal('(')
        self.consume_literal('pragma')
        _t2576 = self.parse_name()
        name128 = _t2576
        xs129 = []
        cond130 = ((((((((((self.match_lookahead_terminal('FLOAT', 0) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('STRING', 0))
        while cond130:
            _t2577 = self.parse_term()
            xs129.append(_t2577)
            cond130 = ((((((((((self.match_lookahead_terminal('FLOAT', 0) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('STRING', 0))
        terms131 = xs129
        self.consume_literal(')')
        _t2578 = logic_pb2.Pragma(name128, terms131)
        return _t2578

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('primitive', 1):
                _t2580 = 9
            else:
                if self.match_lookahead_literal('/', 1):
                    _t2581 = 8
                else:
                    if self.match_lookahead_literal('*', 1):
                        _t2582 = 7
                    else:
                        if self.match_lookahead_literal('-', 1):
                            _t2583 = 6
                        else:
                            if self.match_lookahead_literal('+', 1):
                                _t2584 = 5
                            else:
                                if self.match_lookahead_literal('>=', 1):
                                    _t2585 = 4
                                else:
                                    if self.match_lookahead_literal('>', 1):
                                        _t2586 = 3
                                    else:
                                        if self.match_lookahead_literal('<=', 1):
                                            _t2587 = 2
                                        else:
                                            if self.match_lookahead_literal('<', 1):
                                                _t2589 = 1
                                            else:
                                                if self.match_lookahead_literal('=', 1):
                                                    _t2590 = 0
                                                else:
                                                    _t2590 = -1
                                                _t2589 = _t2590
                                            _t2587 = _t2589
                                        _t2586 = _t2587
                                    _t2585 = _t2586
                                _t2584 = _t2585
                            _t2583 = _t2584
                        _t2582 = _t2583
                    _t2581 = _t2582
                _t2580 = _t2581
            _t2579 = _t2580
        else:
            _t2579 = -1
        prediction132 = _t2579
        if prediction132 == 9:
            self.consume_literal('(')
            self.consume_literal('primitive')
            _t2592 = self.parse_name()
            name142 = _t2592
            xs143 = []
            cond144 = (((((((((((self.match_lookahead_terminal('FLOAT', 0) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_literal('#', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('STRING', 0))
            while cond144:
                _t2593 = self.parse_relterm()
                xs143.append(_t2593)
                cond144 = (((((((((((self.match_lookahead_terminal('FLOAT', 0) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_literal('#', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('STRING', 0))
            terms145 = xs143
            self.consume_literal(')')
            _t2594 = logic_pb2.Primitive(name142, terms145)
            _t2591 = _t2594
        else:
            if prediction132 == 8:
                _t2596 = self.parse_divide()
                op141 = _t2596
                _t2595 = op141
            else:
                if prediction132 == 7:
                    _t2598 = self.parse_multiply()
                    op140 = _t2598
                    _t2597 = op140
                else:
                    if prediction132 == 6:
                        _t2600 = self.parse_minus()
                        op139 = _t2600
                        _t2599 = op139
                    else:
                        if prediction132 == 5:
                            _t2602 = self.parse_add()
                            op138 = _t2602
                            _t2601 = op138
                        else:
                            if prediction132 == 4:
                                _t2604 = self.parse_gt_eq()
                                op137 = _t2604
                                _t2603 = op137
                            else:
                                if prediction132 == 3:
                                    _t2606 = self.parse_gt()
                                    op136 = _t2606
                                    _t2605 = op136
                                else:
                                    if prediction132 == 2:
                                        _t2608 = self.parse_lt_eq()
                                        op135 = _t2608
                                        _t2607 = op135
                                    else:
                                        if prediction132 == 1:
                                            _t2610 = self.parse_lt()
                                            op134 = _t2610
                                            _t2609 = op134
                                        else:
                                            if prediction132 == 0:
                                                _t2612 = self.parse_eq()
                                                op133 = _t2612
                                                _t2611 = op133
                                            else:
                                                raise ParseError('Unexpected token in primitive' + ": {self.lookahead(0)}")
                                                _t2611 = None
                                            _t2609 = _t2611
                                        _t2607 = _t2609
                                    _t2605 = _t2607
                                _t2603 = _t2605
                            _t2601 = _t2603
                        _t2599 = _t2601
                    _t2597 = _t2599
                _t2595 = _t2597
            _t2591 = _t2595
        return _t2591

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('=')
        _t2613 = self.parse_term()
        left146 = _t2613
        _t2614 = self.parse_term()
        right147 = _t2614
        self.consume_literal(')')
        _t2615 = logic_pb2.Primitive('rel_primitive_eq', left146, right147)
        return _t2615

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<')
        _t2616 = self.parse_term()
        left148 = _t2616
        _t2617 = self.parse_term()
        right149 = _t2617
        self.consume_literal(')')
        _t2618 = logic_pb2.Primitive('rel_primitive_lt', left148, right149)
        return _t2618

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<=')
        _t2619 = self.parse_term()
        left150 = _t2619
        _t2620 = self.parse_term()
        right151 = _t2620
        self.consume_literal(')')
        _t2621 = logic_pb2.Primitive('rel_primitive_lt_eq', left150, right151)
        return _t2621

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>')
        _t2622 = self.parse_term()
        left152 = _t2622
        _t2623 = self.parse_term()
        right153 = _t2623
        self.consume_literal(')')
        _t2624 = logic_pb2.Primitive('rel_primitive_gt', left152, right153)
        return _t2624

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>=')
        _t2625 = self.parse_term()
        left154 = _t2625
        _t2626 = self.parse_term()
        right155 = _t2626
        self.consume_literal(')')
        _t2627 = logic_pb2.Primitive('rel_primitive_gt_eq', left154, right155)
        return _t2627

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('+')
        _t2628 = self.parse_term()
        left156 = _t2628
        _t2629 = self.parse_term()
        right157 = _t2629
        _t2630 = self.parse_term()
        result158 = _t2630
        self.consume_literal(')')
        _t2631 = logic_pb2.Primitive('rel_primitive_add', left156, right157, result158)
        return _t2631

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('-')
        _t2632 = self.parse_term()
        left159 = _t2632
        _t2633 = self.parse_term()
        right160 = _t2633
        _t2634 = self.parse_term()
        result161 = _t2634
        self.consume_literal(')')
        _t2635 = logic_pb2.Primitive('rel_primitive_subtract', left159, right160, result161)
        return _t2635

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('*')
        _t2636 = self.parse_term()
        left162 = _t2636
        _t2637 = self.parse_term()
        right163 = _t2637
        _t2638 = self.parse_term()
        result164 = _t2638
        self.consume_literal(')')
        _t2639 = logic_pb2.Primitive('rel_primitive_multiply', left162, right163, result164)
        return _t2639

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('/')
        _t2640 = self.parse_term()
        left165 = _t2640
        _t2641 = self.parse_term()
        right166 = _t2641
        _t2642 = self.parse_term()
        result167 = _t2642
        self.consume_literal(')')
        _t2643 = logic_pb2.Primitive('rel_primitive_divide', left165, right166, result167)
        return _t2643

    def parse_relterm(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_terminal('DECIMAL', 0):
            _t4691 = 1
        else:
            if self.match_lookahead_terminal('UINT128', 0):
                _t5715 = 1
            else:
                if self.match_lookahead_terminal('STRING', 0):
                    _t6227 = 1
                else:
                    if self.match_lookahead_terminal('INT', 0):
                        _t6483 = 1
                    else:
                        if self.match_lookahead_terminal('SYMBOL', 0):
                            _t6611 = 1
                        else:
                            if self.match_lookahead_literal('(', 0):
                                _t6675 = 1
                            else:
                                if self.match_lookahead_terminal('INT128', 0):
                                    _t6707 = 1
                                else:
                                    if self.match_lookahead_literal('false', 0):
                                        _t6723 = 1
                                    else:
                                        if self.match_lookahead_literal('true', 0):
                                            _t6731 = 1
                                        else:
                                            if self.match_lookahead_terminal('FLOAT', 0):
                                                _t6735 = 1
                                            else:
                                                if self.match_lookahead_literal('missing', 0):
                                                    _t6737 = 1
                                                else:
                                                    if self.match_lookahead_literal('#', 0):
                                                        _t6738 = 0
                                                    else:
                                                        _t6738 = -1
                                                    _t6737 = _t6738
                                                _t6735 = _t6737
                                            _t6731 = _t6735
                                        _t6723 = _t6731
                                    _t6707 = _t6723
                                _t6675 = _t6707
                            _t6611 = _t6675
                        _t6483 = _t6611
                    _t6227 = _t6483
                _t5715 = _t6227
            _t4691 = _t5715
        prediction168 = _t4691
        if prediction168 == 1:
            _t6740 = self.parse_term()
            value170 = _t6740
            _t6741 = logic_pb2.RelTerm(term=value170)
            _t6739 = _t6741
        else:
            if prediction168 == 0:
                _t6743 = self.parse_specialized_value()
                value169 = _t6743
                _t6744 = logic_pb2.RelTerm(specialized_value=value169)
                _t6742 = _t6744
            else:
                raise ParseError('Unexpected token in relterm' + ": {self.lookahead(0)}")
                _t6742 = None
            _t6739 = _t6742
        return _t6739

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal('#')
        _t6745 = self.parse_value()
        value171 = _t6745
        return value171

    def parse_relatom(self) -> logic_pb2.RelAtom:
        self.consume_literal('(')
        self.consume_literal('relatom')
        _t6746 = self.parse_name()
        name172 = _t6746
        xs173 = []
        cond174 = (((((((((((self.match_lookahead_terminal('FLOAT', 0) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_literal('#', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('STRING', 0))
        while cond174:
            _t6747 = self.parse_relterm()
            xs173.append(_t6747)
            cond174 = (((((((((((self.match_lookahead_terminal('FLOAT', 0) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_literal('#', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('STRING', 0))
        terms175 = xs173
        self.consume_literal(')')
        _t6748 = logic_pb2.RelAtom(name172, terms175)
        return _t6748

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal('(')
        self.consume_literal('cast')
        _t6749 = self.parse_term()
        input176 = _t6749
        _t6750 = self.parse_term()
        result177 = _t6750
        self.consume_literal(')')
        _t6751 = logic_pb2.Cast(input176, result177)
        return _t6751

    def parse_attrs(self) -> list[logic_pb2.Attribute]:
        self.consume_literal('(')
        self.consume_literal('attrs')
        xs178 = []
        cond179 = self.match_lookahead_literal('(', 0)
        while cond179:
            _t6752 = self.parse_attribute()
            xs178.append(_t6752)
            cond179 = self.match_lookahead_literal('(', 0)
        value180 = xs178
        self.consume_literal(')')
        return value180

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal('(')
        self.consume_literal('attribute')
        _t6753 = self.parse_name()
        name181 = _t6753
        xs182 = []
        cond183 = (((((((((self.match_lookahead_terminal('FLOAT', 0) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('STRING', 0))
        while cond183:
            _t6754 = self.parse_value()
            xs182.append(_t6754)
            cond183 = (((((((((self.match_lookahead_terminal('FLOAT', 0) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_terminal('UINT128', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('STRING', 0))
        args184 = xs182
        self.consume_literal(')')
        _t6755 = logic_pb2.Attribute(name181, args184)
        return _t6755

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal('(')
        self.consume_literal('algorithm')
        xs185 = []
        cond186 = (self.match_lookahead_terminal('INT', 0) or self.match_lookahead_literal(':', 0))
        while cond186:
            _t6756 = self.parse_relation_id()
            xs185.append(_t6756)
            cond186 = (self.match_lookahead_terminal('INT', 0) or self.match_lookahead_literal(':', 0))
        global187 = xs185
        _t6757 = self.parse_script()
        body188 = _t6757
        self.consume_literal(')')
        _t6758 = logic_pb2.Algorithm(global187, body188)
        return _t6758

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal('(')
        self.consume_literal('script')
        xs189 = []
        cond190 = self.match_lookahead_literal('(', 0)
        while cond190:
            _t6759 = self.parse_construct()
            xs189.append(_t6759)
            cond190 = self.match_lookahead_literal('(', 0)
        constructs191 = xs189
        self.consume_literal(')')
        _t6760 = logic_pb2.Script(constructs191)
        return _t6760

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('break', 1):
                _t6793 = 1
            else:
                if self.match_lookahead_literal('upsert', 1):
                    _t6809 = 1
                else:
                    if self.match_lookahead_literal('assign', 1):
                        _t6817 = 1
                    else:
                        if self.match_lookahead_literal('monus', 1):
                            _t6821 = 1
                        else:
                            if self.match_lookahead_literal('monoid', 1):
                                _t6823 = 1
                            else:
                                if self.match_lookahead_literal('loop', 1):
                                    _t6824 = 0
                                else:
                                    _t6824 = -1
                                _t6823 = _t6824
                            _t6821 = _t6823
                        _t6817 = _t6821
                    _t6809 = _t6817
                _t6793 = _t6809
            _t6761 = _t6793
        else:
            _t6761 = -1
        prediction192 = _t6761
        if prediction192 == 1:
            _t6826 = self.parse_instruction()
            value194 = _t6826
            _t6827 = logic_pb2.Construct(instruction=value194)
            _t6825 = _t6827
        else:
            if prediction192 == 0:
                _t6829 = self.parse_loop()
                value193 = _t6829
                _t6830 = logic_pb2.Construct(loop=value193)
                _t6828 = _t6830
            else:
                raise ParseError('Unexpected token in construct' + ": {self.lookahead(0)}")
                _t6828 = None
            _t6825 = _t6828
        return _t6825

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal('(')
        self.consume_literal('loop')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('init', 1)):
            _t6832 = self.parse_loop_init()
            _t6831 = _t6832
        else:
            _t6831 = None
        init195 = _t6831
        _t6833 = self.parse_script()
        body196 = _t6833
        self.consume_literal(')')
        _t6834 = logic_pb2.Loop((init195 if init195 is not None else []), body196)
        return _t6834

    def parse_loop_init(self) -> list[logic_pb2.Instruction]:
        self.consume_literal('(')
        self.consume_literal('init')
        xs197 = []
        cond198 = self.match_lookahead_literal('(', 0)
        while cond198:
            _t6835 = self.parse_instruction()
            xs197.append(_t6835)
            cond198 = self.match_lookahead_literal('(', 0)
        value199 = xs197
        self.consume_literal(')')
        return value199

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('monus', 1):
                _t6837 = 4
            else:
                if self.match_lookahead_literal('monoid', 1):
                    _t6838 = 3
                else:
                    if self.match_lookahead_literal('break', 1):
                        _t6839 = 2
                    else:
                        if self.match_lookahead_literal('upsert', 1):
                            _t6841 = 1
                        else:
                            if self.match_lookahead_literal('assign', 1):
                                _t6842 = 0
                            else:
                                _t6842 = -1
                            _t6841 = _t6842
                        _t6839 = _t6841
                    _t6838 = _t6839
                _t6837 = _t6838
            _t6836 = _t6837
        else:
            _t6836 = -1
        prediction200 = _t6836
        if prediction200 == 4:
            _t6844 = self.parse_monus_def()
            value205 = _t6844
            _t6845 = logic_pb2.Instruction(monus_def=value205)
            _t6843 = _t6845
        else:
            if prediction200 == 3:
                _t6847 = self.parse_monoid_def()
                value204 = _t6847
                _t6848 = logic_pb2.Instruction(monoid_def=value204)
                _t6846 = _t6848
            else:
                if prediction200 == 2:
                    _t6850 = self.parse_break()
                    value203 = _t6850
                    _t6851 = logic_pb2.Instruction(break_=value203)
                    _t6849 = _t6851
                else:
                    if prediction200 == 1:
                        _t6853 = self.parse_upsert()
                        value202 = _t6853
                        _t6854 = logic_pb2.Instruction(upsert=value202)
                        _t6852 = _t6854
                    else:
                        if prediction200 == 0:
                            _t6856 = self.parse_assign()
                            value201 = _t6856
                            _t6857 = logic_pb2.Instruction(assign=value201)
                            _t6855 = _t6857
                        else:
                            raise ParseError('Unexpected token in instruction' + ": {self.lookahead(0)}")
                            _t6855 = None
                        _t6852 = _t6855
                    _t6849 = _t6852
                _t6846 = _t6849
            _t6843 = _t6846
        return _t6843

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal('(')
        self.consume_literal('assign')
        _t6858 = self.parse_relation_id()
        name206 = _t6858
        _t6859 = self.parse_abstraction()
        body207 = _t6859
        if self.match_lookahead_literal('(', 0):
            _t6861 = self.parse_attrs()
            _t6860 = _t6861
        else:
            _t6860 = None
        attrs208 = _t6860
        self.consume_literal(')')
        _t6862 = logic_pb2.Assign(name206, body207, (attrs208 if attrs208 is not None else []))
        return _t6862

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal('(')
        self.consume_literal('upsert')
        _t6863 = self.parse_relation_id()
        name209 = _t6863
        _t6864 = self.parse_abstraction_with_arity()
        body210 = _t6864
        if self.match_lookahead_literal('(', 0):
            _t6866 = self.parse_attrs()
            _t6865 = _t6866
        else:
            _t6865 = None
        attrs211 = _t6865
        self.consume_literal(')')
        _t6867 = logic_pb2.Upsert(name209, body210[0], (attrs211 if attrs211 is not None else []), body210[1])
        return _t6867

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal('(')
        _t6868 = self.parse_bindings()
        bindings212 = _t6868
        _t6869 = self.parse_formula()
        formula213 = _t6869
        self.consume_literal(')')
        _t6870 = logic_pb2.Abstraction(bindings212[0] + bindings212[1], formula213)
        return (_t6870, len(bindings212[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal('(')
        self.consume_literal('break')
        _t6871 = self.parse_relation_id()
        name214 = _t6871
        _t6872 = self.parse_abstraction()
        body215 = _t6872
        if self.match_lookahead_literal('(', 0):
            _t6874 = self.parse_attrs()
            _t6873 = _t6874
        else:
            _t6873 = None
        attrs216 = _t6873
        self.consume_literal(')')
        _t6875 = logic_pb2.Break(name214, body215, (attrs216 if attrs216 is not None else []))
        return _t6875

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal('(')
        self.consume_literal('monoid')
        _t6876 = self.parse_monoid()
        monoid217 = _t6876
        _t6877 = self.parse_relation_id()
        name218 = _t6877
        _t6878 = self.parse_abstraction_with_arity()
        body219 = _t6878
        if self.match_lookahead_literal('(', 0):
            _t6880 = self.parse_attrs()
            _t6879 = _t6880
        else:
            _t6879 = None
        attrs220 = _t6879
        self.consume_literal(')')
        _t6881 = logic_pb2.MonoidDef(monoid217, name218, body219[0], (attrs220 if attrs220 is not None else []), body219[1])
        return _t6881

    def parse_monoid(self) -> logic_pb2.Monoid:
        _t6882 = self.parse_type()
        type221 = _t6882
        self.consume_literal('::')
        _t6883 = self.parse_monoid_op()
        op222 = _t6883
        _t6884 = op222(type221)
        return _t6884

    def parse_monoid_op(self) -> Callable[[logic_pb2.Type], logic_pb2.Monoid]:
        if self.match_lookahead_literal('SUM', 0):
            _t6885 = 3
        else:
            if self.match_lookahead_literal('MAX', 0):
                _t6886 = 2
            else:
                if self.match_lookahead_literal('MIN', 0):
                    _t6888 = 1
                else:
                    if self.match_lookahead_literal('OR', 0):
                        _t6889 = 0
                    else:
                        _t6889 = -1
                    _t6888 = _t6889
                _t6886 = _t6888
            _t6885 = _t6886
        prediction223 = _t6885
        if prediction223 == 3:
            self.consume_literal('SUM')
            def _t6891(type):
                _t6892 = logic_pb2.SumMonoid(type)
                _t6893 = logic_pb2.Monoid(sum=_t6892)
                return _t6893
            _t6890 = _t6891
        else:
            if prediction223 == 2:
                self.consume_literal('MAX')
                def _t6895(type):
                    _t6896 = logic_pb2.MaxMonoid(type)
                    _t6897 = logic_pb2.Monoid(max_monoid=_t6896)
                    return _t6897
                _t6894 = _t6895
            else:
                if prediction223 == 1:
                    self.consume_literal('MIN')
                    def _t6899(type):
                        _t6900 = logic_pb2.MinMonoid(type)
                        _t6901 = logic_pb2.Monoid(min_monoid=_t6900)
                        return _t6901
                    _t6898 = _t6899
                else:
                    if prediction223 == 0:
                        self.consume_literal('OR')
                        def _t6903(type):
                            _t6904 = logic_pb2.OrMonoid()
                            _t6905 = logic_pb2.Monoid(or_monoid=_t6904)
                            return _t6905
                        _t6902 = _t6903
                    else:
                        raise ParseError('Unexpected token in monoid_op' + ": {self.lookahead(0)}")
                        _t6902 = None
                    _t6898 = _t6902
                _t6894 = _t6898
            _t6890 = _t6894
        return _t6890

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal('(')
        self.consume_literal('monus')
        _t6906 = self.parse_monoid()
        monoid224 = _t6906
        _t6907 = self.parse_relation_id()
        name225 = _t6907
        _t6908 = self.parse_abstraction_with_arity()
        body226 = _t6908
        if self.match_lookahead_literal('(', 0):
            _t6910 = self.parse_attrs()
            _t6909 = _t6910
        else:
            _t6909 = None
        attrs227 = _t6909
        self.consume_literal(')')
        _t6911 = logic_pb2.MonusDef(monoid224, name225, body226[0], (attrs227 if attrs227 is not None else []), body226[1])
        return _t6911

    def parse_constraint(self) -> logic_pb2.Constraint:
        _t6912 = self.parse_functional_dependency()
        value228 = _t6912
        _t6913 = logic_pb2.Constraint(functional_dependency=value228)
        return _t6913

    def parse_functional_dependency(self) -> logic_pb2.FunctionalDependency:
        self.consume_literal('(')
        self.consume_literal('functional_dependency')
        _t6914 = self.parse_abstraction()
        guard229 = _t6914
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('keys', 1)):
            _t6916 = self.parse_functional_dependency_keys()
            _t6915 = _t6916
        else:
            _t6915 = None
        keys230 = _t6915
        if self.match_lookahead_literal('(', 0):
            _t6918 = self.parse_functional_dependency_values()
            _t6917 = _t6918
        else:
            _t6917 = None
        values231 = _t6917
        self.consume_literal(')')
        _t6919 = logic_pb2.FunctionalDependency(guard229, (keys230 if keys230 is not None else []), (values231 if values231 is not None else []))
        return _t6919

    def parse_functional_dependency_keys(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('keys')
        xs232 = []
        cond233 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond233:
            _t6920 = self.parse_var()
            xs232.append(_t6920)
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
            _t6921 = self.parse_var()
            xs235.append(_t6921)
            cond236 = self.match_lookahead_terminal('SYMBOL', 0)
        value237 = xs235
        self.consume_literal(')')
        return value237

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal('(')
        self.consume_literal('undefine')
        _t6922 = self.parse_fragment_id()
        fragment_id238 = _t6922
        self.consume_literal(')')
        _t6923 = transactions_pb2.Undefine(fragment_id238)
        return _t6923

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal('(')
        self.consume_literal('context')
        xs239 = []
        cond240 = (self.match_lookahead_terminal('INT', 0) or self.match_lookahead_literal(':', 0))
        while cond240:
            _t6924 = self.parse_relation_id()
            xs239.append(_t6924)
            cond240 = (self.match_lookahead_terminal('INT', 0) or self.match_lookahead_literal(':', 0))
        relations241 = xs239
        self.consume_literal(')')
        _t6925 = transactions_pb2.Context(relations241)
        return _t6925

    def parse_epoch_reads(self) -> list[transactions_pb2.Read]:
        self.consume_literal('(')
        self.consume_literal('reads')
        xs242 = []
        cond243 = self.match_lookahead_literal('(', 0)
        while cond243:
            _t6926 = self.parse_read()
            xs242.append(_t6926)
            cond243 = self.match_lookahead_literal('(', 0)
        value244 = xs242
        self.consume_literal(')')
        return value244

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('export', 1):
                _t6928 = 4
            else:
                if self.match_lookahead_literal('abort', 1):
                    _t6929 = 3
                else:
                    if self.match_lookahead_literal('what_if', 1):
                        _t6930 = 2
                    else:
                        if self.match_lookahead_literal('output', 1):
                            _t6932 = 1
                        else:
                            if self.match_lookahead_literal('demand', 1):
                                _t6933 = 0
                            else:
                                _t6933 = -1
                            _t6932 = _t6933
                        _t6930 = _t6932
                    _t6929 = _t6930
                _t6928 = _t6929
            _t6927 = _t6928
        else:
            _t6927 = -1
        prediction245 = _t6927
        if prediction245 == 4:
            _t6935 = self.parse_export()
            value250 = _t6935
            _t6936 = transactions_pb2.Read(export=value250)
            _t6934 = _t6936
        else:
            if prediction245 == 3:
                _t6938 = self.parse_abort()
                value249 = _t6938
                _t6939 = transactions_pb2.Read(abort=value249)
                _t6937 = _t6939
            else:
                if prediction245 == 2:
                    _t6941 = self.parse_what_if()
                    value248 = _t6941
                    _t6942 = transactions_pb2.Read(what_if=value248)
                    _t6940 = _t6942
                else:
                    if prediction245 == 1:
                        _t6944 = self.parse_output()
                        value247 = _t6944
                        _t6945 = transactions_pb2.Read(output=value247)
                        _t6943 = _t6945
                    else:
                        if prediction245 == 0:
                            _t6947 = self.parse_demand()
                            value246 = _t6947
                            _t6948 = transactions_pb2.Read(demand=value246)
                            _t6946 = _t6948
                        else:
                            raise ParseError('Unexpected token in read' + ": {self.lookahead(0)}")
                            _t6946 = None
                        _t6943 = _t6946
                    _t6940 = _t6943
                _t6937 = _t6940
            _t6934 = _t6937
        return _t6934

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal('(')
        self.consume_literal('demand')
        _t6949 = self.parse_relation_id()
        relation_id251 = _t6949
        self.consume_literal(')')
        _t6950 = transactions_pb2.Demand(relation_id251)
        return _t6950

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal('(')
        self.consume_literal('output')
        if (self.match_lookahead_literal(':', 0) and self.match_lookahead_terminal('SYMBOL', 1)):
            _t6952 = self.parse_name()
            _t6951 = _t6952
        else:
            _t6951 = None
        name252 = _t6951
        _t6953 = self.parse_relation_id()
        relation_id253 = _t6953
        self.consume_literal(')')
        _t6954 = transactions_pb2.Output(name252, relation_id253)
        return _t6954

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal('(')
        self.consume_literal('what_if')
        branch254 = self.consume_terminal('STRING')
        _t6955 = self.parse_epoch()
        epoch255 = _t6955
        self.consume_literal(')')
        _t6956 = transactions_pb2.WhatIf(branch254, epoch255)
        return _t6956

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal('(')
        self.consume_literal('abort')
        if (self.match_lookahead_literal(':', 0) and self.match_lookahead_terminal('SYMBOL', 1)):
            _t6958 = self.parse_name()
            _t6957 = _t6958
        else:
            _t6957 = None
        name256 = _t6957
        _t6959 = self.parse_relation_id()
        relation_id257 = _t6959
        self.consume_literal(')')
        _t6960 = transactions_pb2.Abort(name256, relation_id257)
        return _t6960

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal('(')
        self.consume_literal('export')
        _t6961 = self.parse_export_csvconfig()
        config258 = _t6961
        self.consume_literal(')')
        _t6962 = transactions_pb2.Export(config258)
        return _t6962

    def parse_export_csvconfig(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal('(')
        self.consume_literal('export_csvconfig')
        path259 = self.consume_terminal('STRING')
        _t6963 = self.parse_export_csvcolumns()
        columns260 = _t6963
        _t6964 = self.parse_config_dict()
        config261 = _t6964
        self.consume_literal(')')
        return self.export_csv_config(path259, columns260, config261)

    def parse_export_csvcolumns(self) -> list[transactions_pb2.ExportCSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs262 = []
        cond263 = self.match_lookahead_literal('(', 0)
        while cond263:
            _t6965 = self.parse_export_csvcolumn()
            xs262.append(_t6965)
            cond263 = self.match_lookahead_literal('(', 0)
        columns264 = xs262
        self.consume_literal(')')
        return columns264

    def parse_export_csvcolumn(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        name265 = self.consume_terminal('STRING')
        _t6966 = self.parse_relation_id()
        relation_id266 = _t6966
        self.consume_literal(')')
        _t6967 = transactions_pb2.ExportCSVColumn(name265, relation_id266)
        return _t6967


def parse(input_str: str) -> Any:
    """Parse input string and return parse tree."""
    lexer = Lexer(input_str)
    parser = Parser(lexer.tokens)
    result = parser.parse_transaction()
    if parser.pos < len(parser.tokens):
        raise ParseError(f"Unexpected token at end of input: {parser.lookahead(0)}")
    return result
