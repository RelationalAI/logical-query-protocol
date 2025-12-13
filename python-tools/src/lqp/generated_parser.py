"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.


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
            ('LITERAL', re.compile(r'functional_dependency(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'export_csvconfig(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'datetime_value(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'decimal_value(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'missing_value(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'uint128_value(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'int128_value(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'transaction(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'date_value(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'debug_info(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'max_monoid(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'min_monoid(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'sum_monoid(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'algorithm(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'attribute(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'configure(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'ivmconfig(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'or_monoid(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'primitive(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'DATETIME(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'datetime(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'fragment(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'undefine(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'BOOLEAN(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'DECIMAL(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'MISSING(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'UINT128(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'UNKNOWN(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'columns(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'context(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'missing(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'relatom(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'what_if(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'INT128(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'STRING(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'assign(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'column(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'define(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'demand(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'exists(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'export(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'monoid(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'output(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'pragma(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'reduce(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'script(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'upsert(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'values(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'writes(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'FLOAT(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'abort(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'attrs(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'break(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'epoch(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'false(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'monus(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'reads(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'terms(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'DATE(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'args(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'atom(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'cast(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'date(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'init(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'keys(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'loop(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'sync(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'true(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'INT(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'MAX(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'MIN(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'SUM(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'and(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'def(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'ffi(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'ids(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'not(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'::'), lambda x: x),
            ('LITERAL', re.compile(r'<='), lambda x: x),
            ('LITERAL', re.compile(r'>='), lambda x: x),
            ('LITERAL', re.compile(r'OR(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'or(?!\w)'), lambda x: x),
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
        value = Lexer.scan_int128(parts[0].replace('.', ''))
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
            raise ParseError(f'Expected literal {{expected!r}} but got {{token.type}}={{token.value!r}} at position {{token.pos}}')
        self.pos += 1

    def consume_terminal(self, expected: str) -> Any:
        """Consume a terminal token and return parsed value."""
        if not self.match_lookahead_terminal(expected, 0):
            token = self.lookahead(0)
            raise ParseError(f'Expected terminal {expected} but got {token.type} ({token.value}) at position {token.pos}')
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

        # Store the mapping globally (using id_low as key since RelationId isn't hashable)
        self._relation_id_to_name[id_low] = name

        return relation_id

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
        # Extract relation IDs and names from declarations
        ids = []
        orig_names = []

        for decl in declarations:
            if decl.HasField('def'):
                relation_id = getattr(decl, 'def').name
                # Look up the original name from global mapping
                orig_name = self._relation_id_to_name.get(relation_id.id_low)
                if orig_name:
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
            _t265 = self.parse_configure()
            _t264 = _t265
        else:
            _t264 = None
        configure0 = _t264
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('sync', 1)):
            _t267 = self.parse_sync()
            _t266 = _t267
        else:
            _t266 = None
        sync1 = _t266
        xs2 = []
        cond3 = self.match_lookahead_literal('(', 0)
        while cond3:
            _t268 = self.parse_epoch()
            xs2.append(_t268)
            cond3 = self.match_lookahead_literal('(', 0)
        epochs4 = xs2
        self.consume_literal(')')
        _t269 = transactions_pb2.Transaction(epochs=epochs4, configure=(configure0 if configure0 is not None else self.construct_configure([])), sync=sync1)
        return _t269

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal('(')
        self.consume_literal('configure')
        _t270 = self.parse_config_dict()
        config_dict5 = _t270
        self.consume_literal(')')
        return self.construct_configure(config_dict5)

    def parse_config_dict(self) -> list[tuple[str, logic_pb2.Value]]:
        self.consume_literal('{')
        xs6 = []
        cond7 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond7:
            _t271 = self.parse_config_key_value()
            xs6.append(_t271)
            cond7 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        config_key_value8 = xs6
        self.consume_literal('}')
        return config_key_value8

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        symbol9 = self.consume_terminal('COLON_SYMBOL')
        _t272 = self.parse_value()
        value10 = _t272
        return (symbol9, value10,)

    def parse_value(self) -> logic_pb2.Value:
        if self.match_lookahead_terminal('UINT128', 0):
            _t273 = 5
        else:
            if self.match_lookahead_terminal('STRING', 0):
                _t274 = 2
            else:
                if self.match_lookahead_terminal('INT128', 0):
                    _t275 = 6
                else:
                    if self.match_lookahead_terminal('INT', 0):
                        _t276 = 3
                    else:
                        if self.match_lookahead_terminal('FLOAT', 0):
                            _t277 = 4
                        else:
                            if self.match_lookahead_terminal('DECIMAL', 0):
                                _t278 = 7
                            else:
                                if self.match_lookahead_literal('true', 0):
                                    _t279 = 9
                                else:
                                    if self.match_lookahead_literal('missing', 0):
                                        _t280 = 8
                                    else:
                                        if self.match_lookahead_literal('false', 0):
                                            _t281 = 10
                                        else:
                                            if self.match_lookahead_literal('(', 0):
                                                if self.match_lookahead_literal('datetime', 1):
                                                    _t284 = 1
                                                else:
                                                    if self.match_lookahead_literal('date', 1):
                                                        _t285 = 0
                                                    else:
                                                        _t285 = -1
                                                    _t284 = _t285
                                                _t282 = _t284
                                            else:
                                                _t282 = -1
                                            _t281 = _t282
                                        _t280 = _t281
                                    _t279 = _t280
                                _t278 = _t279
                            _t277 = _t278
                        _t276 = _t277
                    _t275 = _t276
                _t274 = _t275
            _t273 = _t274
        prediction11 = _t273
        if prediction11 == 10:
            self.consume_literal('false')
            _t287 = logic_pb2.Value(boolean_value=False)
            _t286 = _t287
        else:
            if prediction11 == 9:
                self.consume_literal('true')
                _t289 = logic_pb2.Value(boolean_value=True)
                _t288 = _t289
            else:
                if prediction11 == 8:
                    self.consume_literal('missing')
                    _t291 = logic_pb2.MissingValue()
                    _t292 = logic_pb2.Value(missing_value=_t291)
                    _t290 = _t292
                else:
                    if prediction11 == 7:
                        value19 = self.consume_terminal('DECIMAL')
                        _t294 = logic_pb2.Value(decimal_value=value19)
                        _t293 = _t294
                    else:
                        if prediction11 == 6:
                            value18 = self.consume_terminal('INT128')
                            _t296 = logic_pb2.Value(int128_value=value18)
                            _t295 = _t296
                        else:
                            if prediction11 == 5:
                                value17 = self.consume_terminal('UINT128')
                                _t298 = logic_pb2.Value(uint128_value=value17)
                                _t297 = _t298
                            else:
                                if prediction11 == 4:
                                    value16 = self.consume_terminal('FLOAT')
                                    _t300 = logic_pb2.Value(float_value=value16)
                                    _t299 = _t300
                                else:
                                    if prediction11 == 3:
                                        value15 = self.consume_terminal('INT')
                                        _t302 = logic_pb2.Value(int_value=value15)
                                        _t301 = _t302
                                    else:
                                        if prediction11 == 2:
                                            value14 = self.consume_terminal('STRING')
                                            _t304 = logic_pb2.Value(string_value=value14)
                                            _t303 = _t304
                                        else:
                                            if prediction11 == 1:
                                                _t306 = self.parse_datetime()
                                                value13 = _t306
                                                _t307 = logic_pb2.Value(datetime_value=value13)
                                                _t305 = _t307
                                            else:
                                                if prediction11 == 0:
                                                    _t309 = self.parse_date()
                                                    value12 = _t309
                                                    _t310 = logic_pb2.Value(date_value=value12)
                                                    _t308 = _t310
                                                else:
                                                    raise ParseError('Unexpected token in value' + f": {self.lookahead(0)}")
                                                    _t308 = None
                                                _t305 = _t308
                                            _t303 = _t305
                                        _t301 = _t303
                                    _t299 = _t301
                                _t297 = _t299
                            _t295 = _t297
                        _t293 = _t295
                    _t290 = _t293
                _t288 = _t290
            _t286 = _t288
        return _t286

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal('(')
        self.consume_literal('date')
        year20 = self.consume_terminal('INT')
        month21 = self.consume_terminal('INT')
        day22 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t311 = logic_pb2.DateValue(year=year20, month=month21, day=day22)
        return _t311

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
            _t312 = self.consume_terminal('INT')
        else:
            _t312 = None
        microsecond29 = _t312
        self.consume_literal(')')
        if microsecond29 is None:
            _t313 = 0
        else:
            _t313 = microsecond29
        _t314 = logic_pb2.DateTimeValue(year=year23, month=month24, day=day25, hour=hour26, minute=minute27, second=second28, microsecond=_t313)
        return _t314

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal('(')
        self.consume_literal('sync')
        xs30 = []
        cond31 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond31:
            _t315 = self.parse_fragment_id()
            xs30.append(_t315)
            cond31 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        fragments32 = xs30
        self.consume_literal(')')
        _t316 = transactions_pb2.Sync(fragments=fragments32)
        return _t316

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        return self.consume_terminal('COLON_SYMBOL')

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal('(')
        self.consume_literal('epoch')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('writes', 1)):
            _t318 = self.parse_epoch_writes()
            _t317 = _t318
        else:
            _t317 = None
        writes33 = _t317
        if self.match_lookahead_literal('(', 0):
            _t320 = self.parse_epoch_reads()
            _t319 = _t320
        else:
            _t319 = None
        reads34 = _t319
        self.consume_literal(')')
        _t321 = transactions_pb2.Epoch(writes=(writes33 if writes33 is not None else []), reads=(reads34 if reads34 is not None else []))
        return _t321

    def parse_epoch_writes(self) -> list[transactions_pb2.Write]:
        self.consume_literal('(')
        self.consume_literal('writes')
        xs35 = []
        cond36 = self.match_lookahead_literal('(', 0)
        while cond36:
            _t322 = self.parse_write()
            xs35.append(_t322)
            cond36 = self.match_lookahead_literal('(', 0)
        value37 = xs35
        self.consume_literal(')')
        return value37

    def parse_write(self) -> transactions_pb2.Write:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('undefine', 1):
                _t326 = 1
            else:
                if self.match_lookahead_literal('define', 1):
                    _t327 = 0
                else:
                    if self.match_lookahead_literal('context', 1):
                        _t328 = 2
                    else:
                        _t328 = -1
                    _t327 = _t328
                _t326 = _t327
            _t323 = _t326
        else:
            _t323 = -1
        prediction38 = _t323
        if prediction38 == 2:
            _t330 = self.parse_context()
            value41 = _t330
            _t331 = transactions_pb2.Write(context=value41)
            _t329 = _t331
        else:
            if prediction38 == 1:
                _t333 = self.parse_undefine()
                value40 = _t333
                _t334 = transactions_pb2.Write(undefine=value40)
                _t332 = _t334
            else:
                if prediction38 == 0:
                    _t336 = self.parse_define()
                    value39 = _t336
                    _t337 = transactions_pb2.Write(define=value39)
                    _t335 = _t337
                else:
                    raise ParseError('Unexpected token in write' + f": {self.lookahead(0)}")
                    _t335 = None
                _t332 = _t335
            _t329 = _t332
        return _t329

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal('(')
        self.consume_literal('define')
        _t338 = self.parse_fragment()
        fragment42 = _t338
        self.consume_literal(')')
        _t339 = transactions_pb2.Define(fragment=fragment42)
        return _t339

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal('(')
        self.consume_literal('fragment')
        _t340 = self.parse_fragment_id()
        fragment_id43 = _t340
        xs44 = []
        cond45 = self.match_lookahead_literal('(', 0)
        while cond45:
            _t341 = self.parse_declaration()
            xs44.append(_t341)
            cond45 = self.match_lookahead_literal('(', 0)
        declarations46 = xs44
        self.consume_literal(')')
        return self.construct_fragment(fragment_id43, declarations46)

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('functional_dependency', 1):
                _t343 = 2
            else:
                if self.match_lookahead_literal('def', 1):
                    _t344 = 0
                else:
                    _t344 = (self.match_lookahead_literal('algorithm', 1) or -1)
                _t343 = _t344
            _t342 = _t343
        else:
            _t342 = -1
        prediction47 = _t342
        if prediction47 == 2:
            _t346 = self.parse_constraint()
            value50 = _t346
            _t347 = logic_pb2.Declaration(constraint=value50)
            _t345 = _t347
        else:
            if prediction47 == 1:
                _t349 = self.parse_algorithm()
                value49 = _t349
                _t350 = logic_pb2.Declaration(algorithm=value49)
                _t348 = _t350
            else:
                if prediction47 == 0:
                    _t352 = self.parse_def()
                    value48 = _t352
                    _t353 = logic_pb2.Declaration(**{'def': value48})
                    _t351 = _t353
                else:
                    raise ParseError('Unexpected token in declaration' + f": {self.lookahead(0)}")
                    _t351 = None
                _t348 = _t351
            _t345 = _t348
        return _t345

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal('(')
        self.consume_literal('def')
        _t354 = self.parse_relation_id()
        name51 = _t354
        _t355 = self.parse_abstraction()
        body52 = _t355
        if self.match_lookahead_literal('(', 0):
            _t357 = self.parse_attrs()
            _t356 = _t357
        else:
            _t356 = None
        attrs53 = _t356
        self.consume_literal(')')
        _t358 = logic_pb2.Def(name=name51, body=body52, attrs=(attrs53 if attrs53 is not None else []))
        return _t358

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_terminal('INT', 0):
            _t360 = 1
        else:
            if self.match_lookahead_terminal('COLON_SYMBOL', 0):
                _t361 = 0
            else:
                _t361 = -1
            _t360 = _t361
        prediction54 = _t360
        if prediction54 == 1:
            INT55 = self.consume_terminal('INT')
            _t362 = logic_pb2.RelationId(id_low=INT55 & 0xFFFFFFFFFFFFFFFF, id_high=(INT55 >> 64) & 0xFFFFFFFFFFFFFFFF)
        else:
            if prediction54 == 0:
                _t363 = self.consume_terminal('COLON_SYMBOL')
            else:
                raise ParseError('Unexpected token in relation_id' + f": {self.lookahead(0)}")
                _t363 = None
            _t362 = _t363
        return _t362

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal('(')
        _t364 = self.parse_bindings()
        bindings56 = _t364
        _t365 = self.parse_formula()
        formula57 = _t365
        self.consume_literal(')')
        _t366 = logic_pb2.Abstraction(vars=(bindings56[0] + (bindings56[1] if bindings56[1] is not None else [])), value=formula57)
        return _t366

    def parse_bindings(self) -> tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]:
        self.consume_literal('[')
        xs58 = []
        cond59 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond59:
            _t367 = self.parse_binding()
            xs58.append(_t367)
            cond59 = self.match_lookahead_terminal('SYMBOL', 0)
        keys60 = xs58
        if self.match_lookahead_literal('|', 0):
            _t369 = self.parse_value_bindings()
            _t368 = _t369
        else:
            _t368 = None
        values61 = _t368
        self.consume_literal(']')
        return (keys60, (values61 if values61 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol62 = self.consume_terminal('SYMBOL')
        self.consume_literal('::')
        _t370 = self.parse_type()
        type63 = _t370
        _t371 = logic_pb2.Var(name=symbol62)
        _t372 = logic_pb2.Binding(var=_t371, type=type63)
        return _t372

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal('UNKNOWN', 0):
            _t373 = 0
        else:
            if self.match_lookahead_literal('UINT128', 0):
                _t374 = 4
            else:
                if self.match_lookahead_literal('STRING', 0):
                    _t383 = 1
                else:
                    if self.match_lookahead_literal('MISSING', 0):
                        _t384 = 8
                    else:
                        if self.match_lookahead_literal('INT128', 0):
                            _t385 = 5
                        else:
                            if self.match_lookahead_literal('INT', 0):
                                _t386 = 2
                            else:
                                if self.match_lookahead_literal('FLOAT', 0):
                                    _t387 = 3
                                else:
                                    if self.match_lookahead_literal('DATETIME', 0):
                                        _t388 = 7
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
                    _t383 = _t384
                _t374 = _t383
            _t373 = _t374
        prediction64 = _t373
        if prediction64 == 10:
            _t393 = self.parse_boolean_type()
            value75 = _t393
            _t394 = logic_pb2.Type(boolean_type=value75)
            _t392 = _t394
        else:
            if prediction64 == 9:
                _t396 = self.parse_decimal_type()
                value74 = _t396
                _t397 = logic_pb2.Type(decimal_type=value74)
                _t395 = _t397
            else:
                if prediction64 == 8:
                    _t399 = self.parse_missing_type()
                    value73 = _t399
                    _t400 = logic_pb2.Type(missing_type=value73)
                    _t398 = _t400
                else:
                    if prediction64 == 7:
                        _t402 = self.parse_datetime_type()
                        value72 = _t402
                        _t403 = logic_pb2.Type(datetime_type=value72)
                        _t401 = _t403
                    else:
                        if prediction64 == 6:
                            _t405 = self.parse_date_type()
                            value71 = _t405
                            _t406 = logic_pb2.Type(date_type=value71)
                            _t404 = _t406
                        else:
                            if prediction64 == 5:
                                _t408 = self.parse_int128_type()
                                value70 = _t408
                                _t409 = logic_pb2.Type(int128_type=value70)
                                _t407 = _t409
                            else:
                                if prediction64 == 4:
                                    _t411 = self.parse_uint128_type()
                                    value69 = _t411
                                    _t412 = logic_pb2.Type(uint128_type=value69)
                                    _t410 = _t412
                                else:
                                    if prediction64 == 3:
                                        _t414 = self.parse_float_type()
                                        value68 = _t414
                                        _t415 = logic_pb2.Type(float_type=value68)
                                        _t413 = _t415
                                    else:
                                        if prediction64 == 2:
                                            _t417 = self.parse_int_type()
                                            value67 = _t417
                                            _t418 = logic_pb2.Type(int_type=value67)
                                            _t416 = _t418
                                        else:
                                            if prediction64 == 1:
                                                _t420 = self.parse_string_type()
                                                value66 = _t420
                                                _t421 = logic_pb2.Type(string_type=value66)
                                                _t419 = _t421
                                            else:
                                                if prediction64 == 0:
                                                    _t423 = self.parse_unspecified_type()
                                                    value65 = _t423
                                                    _t424 = logic_pb2.Type(unspecified_type=value65)
                                                    _t422 = _t424
                                                else:
                                                    raise ParseError('Unexpected token in type' + f": {self.lookahead(0)}")
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

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        self.consume_literal('UINT128')
        _t429 = logic_pb2.UInt128Type()
        return _t429

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        self.consume_literal('INT128')
        _t430 = logic_pb2.Int128Type()
        return _t430

    def parse_date_type(self) -> logic_pb2.DateType:
        self.consume_literal('DATE')
        _t431 = logic_pb2.DateType()
        return _t431

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        self.consume_literal('DATETIME')
        _t432 = logic_pb2.DateTimeType()
        return _t432

    def parse_missing_type(self) -> logic_pb2.MissingType:
        self.consume_literal('MISSING')
        _t433 = logic_pb2.MissingType()
        return _t433

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        self.consume_literal('(')
        self.consume_literal('DECIMAL')
        precision76 = self.consume_terminal('INT')
        scale77 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t434 = logic_pb2.DecimalType(precision=precision76, scale=scale77)
        return _t434

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal('BOOLEAN')
        _t435 = logic_pb2.BooleanType()
        return _t435

    def parse_value_bindings(self) -> list[logic_pb2.Binding]:
        self.consume_literal('|')
        xs78 = []
        cond79 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond79:
            _t436 = self.parse_binding()
            xs78.append(_t436)
            cond79 = self.match_lookahead_terminal('SYMBOL', 0)
        values80 = xs78
        return values80

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('true', 1):
                _t438 = 0
            else:
                if self.match_lookahead_literal('relatom', 1):
                    _t439 = 11
                else:
                    if self.match_lookahead_literal('reduce', 1):
                        _t440 = 3
                    else:
                        if self.match_lookahead_literal('primitive', 1):
                            _t441 = 10
                        else:
                            if self.match_lookahead_literal('pragma', 1):
                                _t442 = 9
                            else:
                                if self.match_lookahead_literal('or', 1):
                                    _t443 = 5
                                else:
                                    if self.match_lookahead_literal('not', 1):
                                        _t444 = 6
                                    else:
                                        if self.match_lookahead_literal('ffi', 1):
                                            _t445 = 7
                                        else:
                                            if self.match_lookahead_literal('false', 1):
                                                _t459 = 1
                                            else:
                                                if self.match_lookahead_literal('exists', 1):
                                                    _t460 = 2
                                                else:
                                                    if self.match_lookahead_literal('cast', 1):
                                                        _t461 = 12
                                                    else:
                                                        if self.match_lookahead_literal('atom', 1):
                                                            _t462 = 8
                                                        else:
                                                            if self.match_lookahead_literal('and', 1):
                                                                _t463 = 4
                                                            else:
                                                                if self.match_lookahead_literal('>=', 1):
                                                                    _t464 = 10
                                                                else:
                                                                    if self.match_lookahead_literal('>', 1):
                                                                        _t465 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal('=', 1):
                                                                            _t466 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal('<=', 1):
                                                                                _t467 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal('<', 1):
                                                                                    _t468 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal('/', 1):
                                                                                        _t469 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal('-', 1):
                                                                                            _t470 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal('+', 1):
                                                                                                _t471 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal('*', 1):
                                                                                                    _t472 = 10
                                                                                                else:
                                                                                                    _t472 = -1
                                                                                                _t471 = _t472
                                                                                            _t470 = _t471
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
                                            _t445 = _t459
                                        _t444 = _t445
                                    _t443 = _t444
                                _t442 = _t443
                            _t441 = _t442
                        _t440 = _t441
                    _t439 = _t440
                _t438 = _t439
            _t437 = _t438
        else:
            _t437 = -1
        prediction81 = _t437
        if prediction81 == 12:
            _t474 = self.parse_cast()
            value94 = _t474
            _t475 = logic_pb2.Formula(cast=value94)
            _t473 = _t475
        else:
            if prediction81 == 11:
                _t477 = self.parse_relatom()
                value93 = _t477
                _t478 = logic_pb2.Formula(rel_atom=value93)
                _t476 = _t478
            else:
                if prediction81 == 10:
                    _t480 = self.parse_primitive()
                    value92 = _t480
                    _t481 = logic_pb2.Formula(primitive=value92)
                    _t479 = _t481
                else:
                    if prediction81 == 9:
                        _t483 = self.parse_pragma()
                        value91 = _t483
                        _t484 = logic_pb2.Formula(pragma=value91)
                        _t482 = _t484
                    else:
                        if prediction81 == 8:
                            _t486 = self.parse_atom()
                            value90 = _t486
                            _t487 = logic_pb2.Formula(atom=value90)
                            _t485 = _t487
                        else:
                            if prediction81 == 7:
                                _t489 = self.parse_ffi()
                                value89 = _t489
                                _t490 = logic_pb2.Formula(ffi=value89)
                                _t488 = _t490
                            else:
                                if prediction81 == 6:
                                    _t492 = self.parse_not()
                                    value88 = _t492
                                    _t493 = logic_pb2.Formula(**{'not': value88})
                                    _t491 = _t493
                                else:
                                    if prediction81 == 5:
                                        _t495 = self.parse_disjunction()
                                        value87 = _t495
                                        _t496 = logic_pb2.Formula(disjunction=value87)
                                        _t494 = _t496
                                    else:
                                        if prediction81 == 4:
                                            _t498 = self.parse_conjunction()
                                            value86 = _t498
                                            _t499 = logic_pb2.Formula(conjunction=value86)
                                            _t497 = _t499
                                        else:
                                            if prediction81 == 3:
                                                _t501 = self.parse_reduce()
                                                value85 = _t501
                                                _t502 = logic_pb2.Formula(reduce=value85)
                                                _t500 = _t502
                                            else:
                                                if prediction81 == 2:
                                                    _t504 = self.parse_exists()
                                                    value84 = _t504
                                                    _t505 = logic_pb2.Formula(exists=value84)
                                                    _t503 = _t505
                                                else:
                                                    if prediction81 == 1:
                                                        _t507 = self.parse_false()
                                                        value83 = _t507
                                                        _t508 = logic_pb2.Formula(false=value83)
                                                        _t506 = _t508
                                                    else:
                                                        if prediction81 == 0:
                                                            _t510 = self.parse_true()
                                                            value82 = _t510
                                                            _t511 = logic_pb2.Formula(true=value82)
                                                            _t509 = _t511
                                                        else:
                                                            raise ParseError('Unexpected token in formula' + f": {self.lookahead(0)}")
                                                            _t509 = None
                                                        _t506 = _t509
                                                    _t503 = _t506
                                                _t500 = _t503
                                            _t497 = _t500
                                        _t494 = _t497
                                    _t491 = _t494
                                _t488 = _t491
                            _t485 = _t488
                        _t482 = _t485
                    _t479 = _t482
                _t476 = _t479
            _t473 = _t476
        return _t473

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('true')
        self.consume_literal(')')
        _t512 = logic_pb2.Conjunction(args=[])
        return _t512

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('false')
        self.consume_literal(')')
        _t513 = logic_pb2.Disjunction(args=[])
        return _t513

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal('(')
        self.consume_literal('exists')
        _t514 = self.parse_bindings()
        bindings95 = _t514
        _t515 = self.parse_formula()
        formula96 = _t515
        self.consume_literal(')')
        _t516 = logic_pb2.Abstraction(vars=(bindings95[0] + (bindings95[1] if bindings95[1] is not None else [])), value=formula96)
        _t517 = logic_pb2.Exists(body=_t516)
        return _t517

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal('(')
        self.consume_literal('reduce')
        _t518 = self.parse_abstraction()
        op97 = _t518
        _t519 = self.parse_abstraction()
        body98 = _t519
        if self.match_lookahead_literal('(', 0):
            _t521 = self.parse_terms()
            _t520 = _t521
        else:
            _t520 = None
        terms99 = _t520
        self.consume_literal(')')
        _t522 = logic_pb2.Reduce(op=op97, body=body98, terms=(terms99 if terms99 is not None else []))
        return _t522

    def parse_terms(self) -> list[logic_pb2.Term]:
        self.consume_literal('(')
        self.consume_literal('terms')
        xs100 = []
        cond101 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond101:
            _t523 = self.parse_term()
            xs100.append(_t523)
            cond101 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        value102 = xs100
        self.consume_literal(')')
        return value102

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_terminal('UINT128', 0):
            _t525 = 1
        else:
            if self.match_lookahead_terminal('SYMBOL', 0):
                _t526 = 0
            else:
                _t526 = (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or (self.match_lookahead_literal('true', 0) or (self.match_lookahead_literal('missing', 0) or (self.match_lookahead_literal('false', 0) or (self.match_lookahead_literal('(', 0) or -1)))))))))
            _t525 = _t526
        prediction103 = _t525
        if prediction103 == 1:
            _t528 = self.parse_constant()
            value105 = _t528
            _t529 = logic_pb2.Term(constant=value105)
            _t527 = _t529
        else:
            if prediction103 == 0:
                _t531 = self.parse_var()
                value104 = _t531
                _t532 = logic_pb2.Term(var=value104)
                _t530 = _t532
            else:
                raise ParseError('Unexpected token in term' + f": {self.lookahead(0)}")
                _t530 = None
            _t527 = _t530
        return _t527

    def parse_var(self) -> logic_pb2.Var:
        symbol106 = self.consume_terminal('SYMBOL')
        _t533 = logic_pb2.Var(name=symbol106)
        return _t533

    def parse_constant(self) -> logic_pb2.Value:
        _t534 = self.parse_value()
        x107 = _t534
        return x107

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('and')
        xs108 = []
        cond109 = self.match_lookahead_literal('(', 0)
        while cond109:
            _t535 = self.parse_formula()
            xs108.append(_t535)
            cond109 = self.match_lookahead_literal('(', 0)
        args110 = xs108
        self.consume_literal(')')
        _t536 = logic_pb2.Conjunction(args=args110)
        return _t536

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('or')
        xs111 = []
        cond112 = self.match_lookahead_literal('(', 0)
        while cond112:
            _t537 = self.parse_formula()
            xs111.append(_t537)
            cond112 = self.match_lookahead_literal('(', 0)
        args113 = xs111
        self.consume_literal(')')
        _t538 = logic_pb2.Disjunction(args=args113)
        return _t538

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal('(')
        self.consume_literal('not')
        _t539 = self.parse_formula()
        arg114 = _t539
        self.consume_literal(')')
        _t540 = logic_pb2.Not(arg=arg114)
        return _t540

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal('(')
        self.consume_literal('ffi')
        _t541 = self.parse_name()
        name115 = _t541
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('args', 1)):
            _t543 = self.parse_ffi_args()
            _t542 = _t543
        else:
            _t542 = None
        args116 = _t542
        if self.match_lookahead_literal('(', 0):
            _t545 = self.parse_terms()
            _t544 = _t545
        else:
            _t544 = None
        terms117 = _t544
        self.consume_literal(')')
        _t546 = logic_pb2.FFI(name=name115, args=(args116 if args116 is not None else []), terms=(terms117 if terms117 is not None else []))
        return _t546

    def parse_name(self) -> str:
        return self.consume_terminal('COLON_SYMBOL')

    def parse_ffi_args(self) -> list[logic_pb2.Abstraction]:
        self.consume_literal('(')
        self.consume_literal('args')
        xs118 = []
        cond119 = self.match_lookahead_literal('(', 0)
        while cond119:
            _t547 = self.parse_abstraction()
            xs118.append(_t547)
            cond119 = self.match_lookahead_literal('(', 0)
        value120 = xs118
        self.consume_literal(')')
        return value120

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal('(')
        self.consume_literal('atom')
        _t548 = self.parse_relation_id()
        name121 = _t548
        xs122 = []
        cond123 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond123:
            _t549 = self.parse_term()
            xs122.append(_t549)
            cond123 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms124 = xs122
        self.consume_literal(')')
        _t550 = logic_pb2.Atom(name=name121, terms=terms124)
        return _t550

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal('(')
        self.consume_literal('pragma')
        _t551 = self.parse_name()
        name125 = _t551
        xs126 = []
        cond127 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond127:
            _t552 = self.parse_term()
            xs126.append(_t552)
            cond127 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms128 = xs126
        self.consume_literal(')')
        _t553 = logic_pb2.Pragma(name=name125, terms=terms128)
        return _t553

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('primitive', 1):
                _t555 = 9
            else:
                if self.match_lookahead_literal('>=', 1):
                    _t556 = 4
                else:
                    if self.match_lookahead_literal('>', 1):
                        _t557 = 3
                    else:
                        if self.match_lookahead_literal('=', 1):
                            _t558 = 0
                        else:
                            if self.match_lookahead_literal('<=', 1):
                                _t559 = 2
                            else:
                                if self.match_lookahead_literal('<', 1):
                                    _t564 = 1
                                else:
                                    if self.match_lookahead_literal('/', 1):
                                        _t565 = 8
                                    else:
                                        if self.match_lookahead_literal('-', 1):
                                            _t566 = 6
                                        else:
                                            if self.match_lookahead_literal('+', 1):
                                                _t567 = 5
                                            else:
                                                if self.match_lookahead_literal('*', 1):
                                                    _t568 = 7
                                                else:
                                                    _t568 = -1
                                                _t567 = _t568
                                            _t566 = _t567
                                        _t565 = _t566
                                    _t564 = _t565
                                _t559 = _t564
                            _t558 = _t559
                        _t557 = _t558
                    _t556 = _t557
                _t555 = _t556
            _t554 = _t555
        else:
            _t554 = -1
        prediction129 = _t554
        if prediction129 == 9:
            self.consume_literal('(')
            self.consume_literal('primitive')
            _t570 = self.parse_name()
            name139 = _t570
            xs140 = []
            cond141 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            while cond141:
                _t571 = self.parse_relterm()
                xs140.append(_t571)
                cond141 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            terms142 = xs140
            self.consume_literal(')')
            _t572 = logic_pb2.Primitive(name=name139, terms=terms142)
            _t569 = _t572
        else:
            if prediction129 == 8:
                _t574 = self.parse_divide()
                op138 = _t574
                _t573 = op138
            else:
                if prediction129 == 7:
                    _t576 = self.parse_multiply()
                    op137 = _t576
                    _t575 = op137
                else:
                    if prediction129 == 6:
                        _t578 = self.parse_minus()
                        op136 = _t578
                        _t577 = op136
                    else:
                        if prediction129 == 5:
                            _t580 = self.parse_add()
                            op135 = _t580
                            _t579 = op135
                        else:
                            if prediction129 == 4:
                                _t582 = self.parse_gt_eq()
                                op134 = _t582
                                _t581 = op134
                            else:
                                if prediction129 == 3:
                                    _t584 = self.parse_gt()
                                    op133 = _t584
                                    _t583 = op133
                                else:
                                    if prediction129 == 2:
                                        _t586 = self.parse_lt_eq()
                                        op132 = _t586
                                        _t585 = op132
                                    else:
                                        if prediction129 == 1:
                                            _t588 = self.parse_lt()
                                            op131 = _t588
                                            _t587 = op131
                                        else:
                                            if prediction129 == 0:
                                                _t590 = self.parse_eq()
                                                op130 = _t590
                                                _t589 = op130
                                            else:
                                                raise ParseError('Unexpected token in primitive' + f": {self.lookahead(0)}")
                                                _t589 = None
                                            _t587 = _t589
                                        _t585 = _t587
                                    _t583 = _t585
                                _t581 = _t583
                            _t579 = _t581
                        _t577 = _t579
                    _t575 = _t577
                _t573 = _t575
            _t569 = _t573
        return _t569

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('=')
        _t591 = self.parse_term()
        left143 = _t591
        _t592 = self.parse_term()
        right144 = _t592
        self.consume_literal(')')
        _t593 = logic_pb2.RelTerm(term=left143)
        _t594 = logic_pb2.RelTerm(term=right144)
        _t595 = logic_pb2.Primitive(name='rel_primitive_eq', terms=[_t593, _t594])
        return _t595

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<')
        _t596 = self.parse_term()
        left145 = _t596
        _t597 = self.parse_term()
        right146 = _t597
        self.consume_literal(')')
        _t598 = logic_pb2.RelTerm(term=left145)
        _t599 = logic_pb2.RelTerm(term=right146)
        _t600 = logic_pb2.Primitive(name='rel_primitive_lt', terms=[_t598, _t599])
        return _t600

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<=')
        _t601 = self.parse_term()
        left147 = _t601
        _t602 = self.parse_term()
        right148 = _t602
        self.consume_literal(')')
        _t603 = logic_pb2.RelTerm(term=left147)
        _t604 = logic_pb2.RelTerm(term=right148)
        _t605 = logic_pb2.Primitive(name='rel_primitive_lt_eq', terms=[_t603, _t604])
        return _t605

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>')
        _t606 = self.parse_term()
        left149 = _t606
        _t607 = self.parse_term()
        right150 = _t607
        self.consume_literal(')')
        _t608 = logic_pb2.RelTerm(term=left149)
        _t609 = logic_pb2.RelTerm(term=right150)
        _t610 = logic_pb2.Primitive(name='rel_primitive_gt', terms=[_t608, _t609])
        return _t610

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>=')
        _t611 = self.parse_term()
        left151 = _t611
        _t612 = self.parse_term()
        right152 = _t612
        self.consume_literal(')')
        _t613 = logic_pb2.RelTerm(term=left151)
        _t614 = logic_pb2.RelTerm(term=right152)
        _t615 = logic_pb2.Primitive(name='rel_primitive_gt_eq', terms=[_t613, _t614])
        return _t615

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('+')
        _t616 = self.parse_term()
        left153 = _t616
        _t617 = self.parse_term()
        right154 = _t617
        _t618 = self.parse_term()
        result155 = _t618
        self.consume_literal(')')
        _t619 = logic_pb2.RelTerm(term=left153)
        _t620 = logic_pb2.RelTerm(term=right154)
        _t621 = logic_pb2.RelTerm(term=result155)
        _t622 = logic_pb2.Primitive(name='rel_primitive_add_monotype', terms=[_t619, _t620, _t621])
        return _t622

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('-')
        _t623 = self.parse_term()
        left156 = _t623
        _t624 = self.parse_term()
        right157 = _t624
        _t625 = self.parse_term()
        result158 = _t625
        self.consume_literal(')')
        _t626 = logic_pb2.RelTerm(term=left156)
        _t627 = logic_pb2.RelTerm(term=right157)
        _t628 = logic_pb2.RelTerm(term=result158)
        _t629 = logic_pb2.Primitive(name='rel_primitive_subtract_monotype', terms=[_t626, _t627, _t628])
        return _t629

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('*')
        _t630 = self.parse_term()
        left159 = _t630
        _t631 = self.parse_term()
        right160 = _t631
        _t632 = self.parse_term()
        result161 = _t632
        self.consume_literal(')')
        _t633 = logic_pb2.RelTerm(term=left159)
        _t634 = logic_pb2.RelTerm(term=right160)
        _t635 = logic_pb2.RelTerm(term=result161)
        _t636 = logic_pb2.Primitive(name='rel_primitive_multiply_monotype', terms=[_t633, _t634, _t635])
        return _t636

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('/')
        _t637 = self.parse_term()
        left162 = _t637
        _t638 = self.parse_term()
        right163 = _t638
        _t639 = self.parse_term()
        result164 = _t639
        self.consume_literal(')')
        _t640 = logic_pb2.RelTerm(term=left162)
        _t641 = logic_pb2.RelTerm(term=right163)
        _t642 = logic_pb2.RelTerm(term=result164)
        _t643 = logic_pb2.Primitive(name='rel_primitive_divide_monotype', terms=[_t640, _t641, _t642])
        return _t643

    def parse_relterm(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_terminal('UINT128', 0):
            _t2691 = 1
        else:
            if self.match_lookahead_terminal('SYMBOL', 0):
                _t3715 = 1
            else:
                if self.match_lookahead_terminal('STRING', 0):
                    _t4227 = 1
                else:
                    if self.match_lookahead_terminal('INT128', 0):
                        _t4483 = 1
                    else:
                        if self.match_lookahead_terminal('INT', 0):
                            _t4611 = 1
                        else:
                            if self.match_lookahead_terminal('FLOAT', 0):
                                _t4675 = 1
                            else:
                                if self.match_lookahead_terminal('DECIMAL', 0):
                                    _t4707 = 1
                                else:
                                    if self.match_lookahead_literal('true', 0):
                                        _t4723 = 1
                                    else:
                                        if self.match_lookahead_literal('missing', 0):
                                            _t4731 = 1
                                        else:
                                            if self.match_lookahead_literal('false', 0):
                                                _t4735 = 1
                                            else:
                                                if self.match_lookahead_literal('(', 0):
                                                    _t4737 = 1
                                                else:
                                                    if self.match_lookahead_literal('#', 0):
                                                        _t4738 = 0
                                                    else:
                                                        _t4738 = -1
                                                    _t4737 = _t4738
                                                _t4735 = _t4737
                                            _t4731 = _t4735
                                        _t4723 = _t4731
                                    _t4707 = _t4723
                                _t4675 = _t4707
                            _t4611 = _t4675
                        _t4483 = _t4611
                    _t4227 = _t4483
                _t3715 = _t4227
            _t2691 = _t3715
        prediction165 = _t2691
        if prediction165 == 1:
            _t4740 = self.parse_term()
            value167 = _t4740
            _t4741 = logic_pb2.RelTerm(term=value167)
            _t4739 = _t4741
        else:
            if prediction165 == 0:
                _t4743 = self.parse_specialized_value()
                value166 = _t4743
                _t4744 = logic_pb2.RelTerm(specialized_value=value166)
                _t4742 = _t4744
            else:
                raise ParseError('Unexpected token in relterm' + f": {self.lookahead(0)}")
                _t4742 = None
            _t4739 = _t4742
        return _t4739

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal('#')
        _t4745 = self.parse_value()
        value168 = _t4745
        return value168

    def parse_relatom(self) -> logic_pb2.RelAtom:
        self.consume_literal('(')
        self.consume_literal('relatom')
        _t4746 = self.parse_name()
        name169 = _t4746
        xs170 = []
        cond171 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond171:
            _t4747 = self.parse_relterm()
            xs170.append(_t4747)
            cond171 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms172 = xs170
        self.consume_literal(')')
        _t4748 = logic_pb2.RelAtom(name=name169, terms=terms172)
        return _t4748

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal('(')
        self.consume_literal('cast')
        _t4749 = self.parse_term()
        input173 = _t4749
        _t4750 = self.parse_term()
        result174 = _t4750
        self.consume_literal(')')
        _t4751 = logic_pb2.Cast(input=input173, result=result174)
        return _t4751

    def parse_attrs(self) -> list[logic_pb2.Attribute]:
        self.consume_literal('(')
        self.consume_literal('attrs')
        xs175 = []
        cond176 = self.match_lookahead_literal('(', 0)
        while cond176:
            _t4752 = self.parse_attribute()
            xs175.append(_t4752)
            cond176 = self.match_lookahead_literal('(', 0)
        value177 = xs175
        self.consume_literal(')')
        return value177

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal('(')
        self.consume_literal('attribute')
        _t4753 = self.parse_name()
        name178 = _t4753
        xs179 = []
        cond180 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond180:
            _t4754 = self.parse_value()
            xs179.append(_t4754)
            cond180 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        args181 = xs179
        self.consume_literal(')')
        _t4755 = logic_pb2.Attribute(name=name178, args=args181)
        return _t4755

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal('(')
        self.consume_literal('algorithm')
        xs182 = []
        cond183 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        while cond183:
            _t4756 = self.parse_relation_id()
            xs182.append(_t4756)
            cond183 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        global184 = xs182
        _t4757 = self.parse_script()
        body185 = _t4757
        self.consume_literal(')')
        _t4758 = logic_pb2.Algorithm(global_=global184, body=body185)
        return _t4758

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal('(')
        self.consume_literal('script')
        xs186 = []
        cond187 = self.match_lookahead_literal('(', 0)
        while cond187:
            _t4759 = self.parse_construct()
            xs186.append(_t4759)
            cond187 = self.match_lookahead_literal('(', 0)
        constructs188 = xs186
        self.consume_literal(')')
        _t4760 = logic_pb2.Script(constructs=constructs188)
        return _t4760

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t4769 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t4773 = 1
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t4775 = 1
                    else:
                        if self.match_lookahead_literal('loop', 1):
                            _t4776 = 0
                        else:
                            _t4776 = (self.match_lookahead_literal('break', 1) or (self.match_lookahead_literal('assign', 1) or -1))
                        _t4775 = _t4776
                    _t4773 = _t4775
                _t4769 = _t4773
            _t4761 = _t4769
        else:
            _t4761 = -1
        prediction189 = _t4761
        if prediction189 == 1:
            _t4778 = self.parse_instruction()
            value191 = _t4778
            _t4779 = logic_pb2.Construct(instruction=value191)
            _t4777 = _t4779
        else:
            if prediction189 == 0:
                _t4781 = self.parse_loop()
                value190 = _t4781
                _t4782 = logic_pb2.Construct(loop=value190)
                _t4780 = _t4782
            else:
                raise ParseError('Unexpected token in construct' + f": {self.lookahead(0)}")
                _t4780 = None
            _t4777 = _t4780
        return _t4777

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal('(')
        self.consume_literal('loop')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('init', 1)):
            _t4784 = self.parse_loop_init()
            _t4783 = _t4784
        else:
            _t4783 = None
        init192 = _t4783
        _t4785 = self.parse_script()
        body193 = _t4785
        self.consume_literal(')')
        _t4786 = logic_pb2.Loop(init=(init192 if init192 is not None else []), body=body193)
        return _t4786

    def parse_loop_init(self) -> list[logic_pb2.Instruction]:
        self.consume_literal('(')
        self.consume_literal('init')
        xs194 = []
        cond195 = self.match_lookahead_literal('(', 0)
        while cond195:
            _t4787 = self.parse_instruction()
            xs194.append(_t4787)
            cond195 = self.match_lookahead_literal('(', 0)
        value196 = xs194
        self.consume_literal(')')
        return value196

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t4793 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t4794 = 4
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t4795 = 3
                    else:
                        if self.match_lookahead_literal('break', 1):
                            _t4796 = 2
                        else:
                            if self.match_lookahead_literal('assign', 1):
                                _t4797 = 0
                            else:
                                _t4797 = -1
                            _t4796 = _t4797
                        _t4795 = _t4796
                    _t4794 = _t4795
                _t4793 = _t4794
            _t4788 = _t4793
        else:
            _t4788 = -1
        prediction197 = _t4788
        if prediction197 == 4:
            _t4799 = self.parse_monus_def()
            value202 = _t4799
            _t4800 = logic_pb2.Instruction(monus_def=value202)
            _t4798 = _t4800
        else:
            if prediction197 == 3:
                _t4802 = self.parse_monoid_def()
                value201 = _t4802
                _t4803 = logic_pb2.Instruction(monoid_def=value201)
                _t4801 = _t4803
            else:
                if prediction197 == 2:
                    _t4805 = self.parse_break()
                    value200 = _t4805
                    _t4806 = logic_pb2.Instruction(**{'break': value200})
                    _t4804 = _t4806
                else:
                    if prediction197 == 1:
                        _t4808 = self.parse_upsert()
                        value199 = _t4808
                        _t4809 = logic_pb2.Instruction(upsert=value199)
                        _t4807 = _t4809
                    else:
                        if prediction197 == 0:
                            _t4811 = self.parse_assign()
                            value198 = _t4811
                            _t4812 = logic_pb2.Instruction(assign=value198)
                            _t4810 = _t4812
                        else:
                            raise ParseError('Unexpected token in instruction' + f": {self.lookahead(0)}")
                            _t4810 = None
                        _t4807 = _t4810
                    _t4804 = _t4807
                _t4801 = _t4804
            _t4798 = _t4801
        return _t4798

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal('(')
        self.consume_literal('assign')
        _t4813 = self.parse_relation_id()
        name203 = _t4813
        _t4814 = self.parse_abstraction()
        body204 = _t4814
        if self.match_lookahead_literal('(', 0):
            _t4816 = self.parse_attrs()
            _t4815 = _t4816
        else:
            _t4815 = None
        attrs205 = _t4815
        self.consume_literal(')')
        _t4817 = logic_pb2.Assign(name=name203, body=body204, attrs=(attrs205 if attrs205 is not None else []))
        return _t4817

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal('(')
        self.consume_literal('upsert')
        _t4818 = self.parse_relation_id()
        name206 = _t4818
        _t4819 = self.parse_abstraction_with_arity()
        body207 = _t4819
        if self.match_lookahead_literal('(', 0):
            _t4821 = self.parse_attrs()
            _t4820 = _t4821
        else:
            _t4820 = None
        attrs208 = _t4820
        self.consume_literal(')')
        _t4822 = logic_pb2.Upsert(name=name206, body=body207[0], attrs=(attrs208 if attrs208 is not None else []), value_arity=body207[1])
        return _t4822

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal('(')
        _t4823 = self.parse_bindings()
        bindings209 = _t4823
        _t4824 = self.parse_formula()
        formula210 = _t4824
        self.consume_literal(')')
        _t4825 = logic_pb2.Abstraction(vars=(bindings209[0] + (bindings209[1] if bindings209[1] is not None else [])), value=formula210)
        return (_t4825, len(bindings209[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal('(')
        self.consume_literal('break')
        _t4826 = self.parse_relation_id()
        name211 = _t4826
        _t4827 = self.parse_abstraction()
        body212 = _t4827
        if self.match_lookahead_literal('(', 0):
            _t4829 = self.parse_attrs()
            _t4828 = _t4829
        else:
            _t4828 = None
        attrs213 = _t4828
        self.consume_literal(')')
        _t4830 = logic_pb2.Break(name=name211, body=body212, attrs=(attrs213 if attrs213 is not None else []))
        return _t4830

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal('(')
        self.consume_literal('monoid')
        _t4831 = self.parse_monoid()
        monoid214 = _t4831
        _t4832 = self.parse_relation_id()
        name215 = _t4832
        _t4833 = self.parse_abstraction_with_arity()
        body216 = _t4833
        if self.match_lookahead_literal('(', 0):
            _t4835 = self.parse_attrs()
            _t4834 = _t4835
        else:
            _t4834 = None
        attrs217 = _t4834
        self.consume_literal(')')
        _t4836 = logic_pb2.MonoidDef(monoid=monoid214, name=name215, body=body216[0], attrs=(attrs217 if attrs217 is not None else []), value_arity=body216[1])
        return _t4836

    def parse_monoid(self) -> logic_pb2.Monoid:
        _t4837 = self.parse_type()
        type218 = _t4837
        self.consume_literal('::')
        _t4838 = self.parse_monoid_op()
        op219 = _t4838
        _t4839 = op219(type218)
        return _t4839

    def parse_monoid_op(self) -> Callable[[logic_pb2.Type], logic_pb2.Monoid]:
        if self.match_lookahead_literal('SUM', 0):
            _t4840 = 3
        else:
            if self.match_lookahead_literal('OR', 0):
                _t4841 = 0
            else:
                if self.match_lookahead_literal('MIN', 0):
                    _t4843 = 1
                else:
                    if self.match_lookahead_literal('MAX', 0):
                        _t4844 = 2
                    else:
                        _t4844 = -1
                    _t4843 = _t4844
                _t4841 = _t4843
            _t4840 = _t4841
        prediction220 = _t4840
        if prediction220 == 3:
            self.consume_literal('SUM')
            def _t4846(type):
                _t4847 = logic_pb2.SumMonoid(type=type)
                _t4848 = logic_pb2.Monoid(sum_monoid=_t4847)
                return _t4848
            _t4845 = _t4846
        else:
            if prediction220 == 2:
                self.consume_literal('MAX')
                def _t4850(type):
                    _t4851 = logic_pb2.MaxMonoid(type=type)
                    _t4852 = logic_pb2.Monoid(max_monoid=_t4851)
                    return _t4852
                _t4849 = _t4850
            else:
                if prediction220 == 1:
                    self.consume_literal('MIN')
                    def _t4854(type):
                        _t4855 = logic_pb2.MinMonoid(type=type)
                        _t4856 = logic_pb2.Monoid(min_monoid=_t4855)
                        return _t4856
                    _t4853 = _t4854
                else:
                    if prediction220 == 0:
                        self.consume_literal('OR')
                        def _t4858(type):
                            _t4859 = logic_pb2.OrMonoid()
                            _t4860 = logic_pb2.Monoid(or_monoid=_t4859)
                            return _t4860
                        _t4857 = _t4858
                    else:
                        raise ParseError('Unexpected token in monoid_op' + f": {self.lookahead(0)}")
                        _t4857 = None
                    _t4853 = _t4857
                _t4849 = _t4853
            _t4845 = _t4849
        return _t4845

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal('(')
        self.consume_literal('monus')
        _t4861 = self.parse_monoid()
        monoid221 = _t4861
        _t4862 = self.parse_relation_id()
        name222 = _t4862
        _t4863 = self.parse_abstraction_with_arity()
        body223 = _t4863
        if self.match_lookahead_literal('(', 0):
            _t4865 = self.parse_attrs()
            _t4864 = _t4865
        else:
            _t4864 = None
        attrs224 = _t4864
        self.consume_literal(')')
        _t4866 = logic_pb2.MonusDef(monoid=monoid221, name=name222, body=body223[0], attrs=(attrs224 if attrs224 is not None else []), value_arity=body223[1])
        return _t4866

    def parse_constraint(self) -> logic_pb2.Constraint:
        _t4867 = self.parse_functional_dependency()
        value225 = _t4867
        _t4868 = logic_pb2.Constraint(functional_dependency=value225)
        return _t4868

    def parse_functional_dependency(self) -> logic_pb2.FunctionalDependency:
        self.consume_literal('(')
        self.consume_literal('functional_dependency')
        _t4869 = self.parse_abstraction()
        guard226 = _t4869
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('keys', 1)):
            _t4871 = self.parse_functional_dependency_keys()
            _t4870 = _t4871
        else:
            _t4870 = None
        keys227 = _t4870
        if self.match_lookahead_literal('(', 0):
            _t4873 = self.parse_functional_dependency_values()
            _t4872 = _t4873
        else:
            _t4872 = None
        values228 = _t4872
        self.consume_literal(')')
        _t4874 = logic_pb2.FunctionalDependency(guard=guard226, keys=(keys227 if keys227 is not None else []), values=(values228 if values228 is not None else []))
        return _t4874

    def parse_functional_dependency_keys(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('keys')
        xs229 = []
        cond230 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond230:
            _t4875 = self.parse_var()
            xs229.append(_t4875)
            cond230 = self.match_lookahead_terminal('SYMBOL', 0)
        value231 = xs229
        self.consume_literal(')')
        return value231

    def parse_functional_dependency_values(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('values')
        xs232 = []
        cond233 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond233:
            _t4876 = self.parse_var()
            xs232.append(_t4876)
            cond233 = self.match_lookahead_terminal('SYMBOL', 0)
        value234 = xs232
        self.consume_literal(')')
        return value234

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal('(')
        self.consume_literal('undefine')
        _t4877 = self.parse_fragment_id()
        fragment_id235 = _t4877
        self.consume_literal(')')
        _t4878 = transactions_pb2.Undefine(fragment_id=fragment_id235)
        return _t4878

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal('(')
        self.consume_literal('context')
        xs236 = []
        cond237 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        while cond237:
            _t4879 = self.parse_relation_id()
            xs236.append(_t4879)
            cond237 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        relations238 = xs236
        self.consume_literal(')')
        _t4880 = transactions_pb2.Context(relations=relations238)
        return _t4880

    def parse_epoch_reads(self) -> list[transactions_pb2.Read]:
        self.consume_literal('(')
        self.consume_literal('reads')
        xs239 = []
        cond240 = self.match_lookahead_literal('(', 0)
        while cond240:
            _t4881 = self.parse_read()
            xs239.append(_t4881)
            cond240 = self.match_lookahead_literal('(', 0)
        value241 = xs239
        self.consume_literal(')')
        return value241

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('what_if', 1):
                _t4883 = 2
            else:
                if self.match_lookahead_literal('output', 1):
                    _t4887 = 1
                else:
                    if self.match_lookahead_literal('export', 1):
                        _t4888 = 4
                    else:
                        if self.match_lookahead_literal('demand', 1):
                            _t4889 = 0
                        else:
                            if self.match_lookahead_literal('abort', 1):
                                _t4890 = 3
                            else:
                                _t4890 = -1
                            _t4889 = _t4890
                        _t4888 = _t4889
                    _t4887 = _t4888
                _t4883 = _t4887
            _t4882 = _t4883
        else:
            _t4882 = -1
        prediction242 = _t4882
        if prediction242 == 4:
            _t4892 = self.parse_export()
            value247 = _t4892
            _t4893 = transactions_pb2.Read(export=value247)
            _t4891 = _t4893
        else:
            if prediction242 == 3:
                _t4895 = self.parse_abort()
                value246 = _t4895
                _t4896 = transactions_pb2.Read(abort=value246)
                _t4894 = _t4896
            else:
                if prediction242 == 2:
                    _t4898 = self.parse_what_if()
                    value245 = _t4898
                    _t4899 = transactions_pb2.Read(what_if=value245)
                    _t4897 = _t4899
                else:
                    if prediction242 == 1:
                        _t4901 = self.parse_output()
                        value244 = _t4901
                        _t4902 = transactions_pb2.Read(output=value244)
                        _t4900 = _t4902
                    else:
                        if prediction242 == 0:
                            _t4904 = self.parse_demand()
                            value243 = _t4904
                            _t4905 = transactions_pb2.Read(demand=value243)
                            _t4903 = _t4905
                        else:
                            raise ParseError('Unexpected token in read' + f": {self.lookahead(0)}")
                            _t4903 = None
                        _t4900 = _t4903
                    _t4897 = _t4900
                _t4894 = _t4897
            _t4891 = _t4894
        return _t4891

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal('(')
        self.consume_literal('demand')
        _t4906 = self.parse_relation_id()
        relation_id248 = _t4906
        self.consume_literal(')')
        _t4907 = transactions_pb2.Demand(relation_id=relation_id248)
        return _t4907

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal('(')
        self.consume_literal('output')
        if self.match_lookahead_terminal('COLON_SYMBOL', 0):
            _t4909 = self.parse_name()
            _t4908 = _t4909
        else:
            _t4908 = None
        name249 = _t4908
        _t4910 = self.parse_relation_id()
        relation_id250 = _t4910
        self.consume_literal(')')
        _t4911 = transactions_pb2.Output(name=name249, relation_id=relation_id250)
        return _t4911

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal('(')
        self.consume_literal('what_if')
        branch251 = self.consume_terminal('STRING')
        _t4912 = self.parse_epoch()
        epoch252 = _t4912
        self.consume_literal(')')
        _t4913 = transactions_pb2.WhatIf(branch=branch251, epoch=epoch252)
        return _t4913

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal('(')
        self.consume_literal('abort')
        if self.match_lookahead_terminal('COLON_SYMBOL', 0):
            _t4915 = self.parse_name()
            _t4914 = _t4915
        else:
            _t4914 = None
        name253 = _t4914
        _t4916 = self.parse_relation_id()
        relation_id254 = _t4916
        self.consume_literal(')')
        _t4917 = transactions_pb2.Abort(name=name253, relation_id=relation_id254)
        return _t4917

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal('(')
        self.consume_literal('export')
        _t4918 = self.parse_export_csvconfig()
        config255 = _t4918
        self.consume_literal(')')
        _t4919 = transactions_pb2.Export(config255)
        return _t4919

    def parse_export_csvconfig(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal('(')
        self.consume_literal('export_csvconfig')
        path256 = self.consume_terminal('STRING')
        _t4920 = self.parse_export_csvcolumns()
        columns257 = _t4920
        _t4921 = self.parse_config_dict()
        config258 = _t4921
        self.consume_literal(')')
        return self.export_csv_config(path256, columns257, config258)

    def parse_export_csvcolumns(self) -> list[transactions_pb2.ExportCSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs259 = []
        cond260 = self.match_lookahead_literal('(', 0)
        while cond260:
            _t4922 = self.parse_export_csvcolumn()
            xs259.append(_t4922)
            cond260 = self.match_lookahead_literal('(', 0)
        columns261 = xs259
        self.consume_literal(')')
        return columns261

    def parse_export_csvcolumn(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        name262 = self.consume_terminal('STRING')
        _t4923 = self.parse_relation_id()
        relation_id263 = _t4923
        self.consume_literal(')')
        _t4924 = transactions_pb2.ExportCSVColumn(column_name=name262, column_data=relation_id263)
        return _t4924


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
