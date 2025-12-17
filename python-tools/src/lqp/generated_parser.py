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
            ('LITERAL', re.compile(r'export_csv_config(?!\w)'), lambda x: x),
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
            ('LITERAL', re.compile(r'BOOL(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'DATE(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'args(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'atom(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'cast(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'date(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'init(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'keys(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'loop(?!\w)'), lambda x: x),
            ('LITERAL', re.compile(r'path(?!\w)'), lambda x: x),
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

        # Store the mapping for the current fragment if we're inside one
        if self._current_fragment_id is not None:
            if self._current_fragment_id not in self.id_to_debuginfo:
                self.id_to_debuginfo[self._current_fragment_id] = {}
            self.id_to_debuginfo[self._current_fragment_id][(relation_id.id_low, relation_id.id_high)] = name

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
        else:
            kwargs['partition_size'] = 0

        compression_val = config.get('compression')
        if compression_val and compression_val.HasField('string_value'):
            kwargs['compression'] = compression_val.string_value
        else:
            kwargs['compression'] = ''

        header_val = config.get('syntax_header_row')
        if header_val and header_val.HasField('boolean_value'):
            kwargs['syntax_header_row'] = header_val.boolean_value
        else:
            kwargs['syntax_header_row'] = True

        missing_val = config.get('syntax_missing_string')
        if missing_val and missing_val.HasField('string_value'):
            kwargs['syntax_missing_string'] = missing_val.string_value
        else:
            kwargs['syntax_missing_string'] = ''

        delim_val = config.get('syntax_delim')
        if delim_val and delim_val.HasField('string_value'):
            kwargs['syntax_delim'] = delim_val.string_value
        else:
            kwargs['syntax_delim'] = ','

        quote_val = config.get('syntax_quotechar')
        if quote_val and quote_val.HasField('string_value'):
            kwargs['syntax_quotechar'] = quote_val.string_value
        else:
            kwargs['syntax_quotechar'] = '"'

        escape_val = config.get('syntax_escapechar')
        if escape_val and escape_val.HasField('string_value'):
            kwargs['syntax_escapechar'] = escape_val.string_value
        else:
            kwargs['syntax_escapechar'] = '\\'

        return transactions_pb2.ExportCSVConfig(path=path_str, data_columns=columns, **kwargs)

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
            _t270 = self.parse_configure()
            _t269 = _t270
        else:
            _t269 = None
        configure0 = _t269
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('sync', 1)):
            _t272 = self.parse_sync()
            _t271 = _t272
        else:
            _t271 = None
        sync1 = _t271
        xs2 = []
        cond3 = self.match_lookahead_literal('(', 0)
        while cond3:
            _t273 = self.parse_epoch()
            xs2.append(_t273)
            cond3 = self.match_lookahead_literal('(', 0)
        epochs4 = xs2
        self.consume_literal(')')
        _t274 = transactions_pb2.Transaction(epochs=epochs4, configure=(configure0 if configure0 is not None else self.construct_configure([])), sync=sync1)
        return _t274

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal('(')
        self.consume_literal('configure')
        _t275 = self.parse_config_dict()
        config_dict5 = _t275
        self.consume_literal(')')
        return self.construct_configure(config_dict5)

    def parse_config_dict(self) -> list[tuple[str, logic_pb2.Value]]:
        self.consume_literal('{')
        xs6 = []
        cond7 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond7:
            _t276 = self.parse_config_key_value()
            xs6.append(_t276)
            cond7 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        config_key_value8 = xs6
        self.consume_literal('}')
        return config_key_value8

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        symbol9 = self.consume_terminal('COLON_SYMBOL')
        _t277 = self.parse_value()
        value10 = _t277
        return (symbol9, value10,)

    def parse_value(self) -> logic_pb2.Value:
        if self.match_lookahead_terminal('UINT128', 0):
            _t278 = 5
        else:
            if self.match_lookahead_terminal('STRING', 0):
                _t279 = 2
            else:
                if self.match_lookahead_terminal('INT128', 0):
                    _t280 = 6
                else:
                    if self.match_lookahead_terminal('INT', 0):
                        _t281 = 3
                    else:
                        if self.match_lookahead_terminal('FLOAT', 0):
                            _t282 = 4
                        else:
                            if self.match_lookahead_terminal('DECIMAL', 0):
                                _t283 = 7
                            else:
                                if self.match_lookahead_literal('true', 0):
                                    _t284 = 9
                                else:
                                    if self.match_lookahead_literal('missing', 0):
                                        _t285 = 8
                                    else:
                                        if self.match_lookahead_literal('false', 0):
                                            _t286 = 10
                                        else:
                                            if self.match_lookahead_literal('(', 0):
                                                if self.match_lookahead_literal('datetime', 1):
                                                    _t289 = 1
                                                else:
                                                    if self.match_lookahead_literal('date', 1):
                                                        _t290 = 0
                                                    else:
                                                        _t290 = -1
                                                    _t289 = _t290
                                                _t287 = _t289
                                            else:
                                                _t287 = -1
                                            _t286 = _t287
                                        _t285 = _t286
                                    _t284 = _t285
                                _t283 = _t284
                            _t282 = _t283
                        _t281 = _t282
                    _t280 = _t281
                _t279 = _t280
            _t278 = _t279
        prediction11 = _t278
        if prediction11 == 10:
            self.consume_literal('false')
            _t292 = logic_pb2.Value(boolean_value=False)
            _t291 = _t292
        else:
            if prediction11 == 9:
                self.consume_literal('true')
                _t294 = logic_pb2.Value(boolean_value=True)
                _t293 = _t294
            else:
                if prediction11 == 8:
                    self.consume_literal('missing')
                    _t296 = logic_pb2.MissingValue()
                    _t297 = logic_pb2.Value(missing_value=_t296)
                    _t295 = _t297
                else:
                    if prediction11 == 7:
                        value19 = self.consume_terminal('DECIMAL')
                        _t299 = logic_pb2.Value(decimal_value=value19)
                        _t298 = _t299
                    else:
                        if prediction11 == 6:
                            value18 = self.consume_terminal('INT128')
                            _t301 = logic_pb2.Value(int128_value=value18)
                            _t300 = _t301
                        else:
                            if prediction11 == 5:
                                value17 = self.consume_terminal('UINT128')
                                _t303 = logic_pb2.Value(uint128_value=value17)
                                _t302 = _t303
                            else:
                                if prediction11 == 4:
                                    value16 = self.consume_terminal('FLOAT')
                                    _t305 = logic_pb2.Value(float_value=value16)
                                    _t304 = _t305
                                else:
                                    if prediction11 == 3:
                                        value15 = self.consume_terminal('INT')
                                        _t307 = logic_pb2.Value(int_value=value15)
                                        _t306 = _t307
                                    else:
                                        if prediction11 == 2:
                                            value14 = self.consume_terminal('STRING')
                                            _t309 = logic_pb2.Value(string_value=value14)
                                            _t308 = _t309
                                        else:
                                            if prediction11 == 1:
                                                _t311 = self.parse_datetime()
                                                value13 = _t311
                                                _t312 = logic_pb2.Value(datetime_value=value13)
                                                _t310 = _t312
                                            else:
                                                if prediction11 == 0:
                                                    _t314 = self.parse_date()
                                                    value12 = _t314
                                                    _t315 = logic_pb2.Value(date_value=value12)
                                                    _t313 = _t315
                                                else:
                                                    raise ParseError(f"{'Unexpected token in value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                    _t313 = None
                                                _t310 = _t313
                                            _t308 = _t310
                                        _t306 = _t308
                                    _t304 = _t306
                                _t302 = _t304
                            _t300 = _t302
                        _t298 = _t300
                    _t295 = _t298
                _t293 = _t295
            _t291 = _t293
        return _t291

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal('(')
        self.consume_literal('date')
        year20 = self.consume_terminal('INT')
        month21 = self.consume_terminal('INT')
        day22 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t316 = logic_pb2.DateValue(year=year20, month=month21, day=day22)
        return _t316

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
            _t317 = self.consume_terminal('INT')
        else:
            _t317 = None
        microsecond29 = _t317
        self.consume_literal(')')
        if microsecond29 is None:
            _t318 = 0
        else:
            _t318 = microsecond29
        _t319 = logic_pb2.DateTimeValue(year=year23, month=month24, day=day25, hour=hour26, minute=minute27, second=second28, microsecond=_t318)
        return _t319

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal('(')
        self.consume_literal('sync')
        xs30 = []
        cond31 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond31:
            _t320 = self.parse_fragment_id()
            xs30.append(_t320)
            cond31 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        fragments32 = xs30
        self.consume_literal(')')
        _t321 = transactions_pb2.Sync(fragments=fragments32)
        return _t321

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        symbol33 = self.consume_terminal('COLON_SYMBOL')
        return fragments_pb2.FragmentId(id=symbol33.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal('(')
        self.consume_literal('epoch')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('writes', 1)):
            _t323 = self.parse_epoch_writes()
            _t322 = _t323
        else:
            _t322 = None
        writes34 = _t322
        if self.match_lookahead_literal('(', 0):
            _t325 = self.parse_epoch_reads()
            _t324 = _t325
        else:
            _t324 = None
        reads35 = _t324
        self.consume_literal(')')
        _t326 = transactions_pb2.Epoch(writes=(writes34 if writes34 is not None else []), reads=(reads35 if reads35 is not None else []))
        return _t326

    def parse_epoch_writes(self) -> list[transactions_pb2.Write]:
        self.consume_literal('(')
        self.consume_literal('writes')
        xs36 = []
        cond37 = self.match_lookahead_literal('(', 0)
        while cond37:
            _t327 = self.parse_write()
            xs36.append(_t327)
            cond37 = self.match_lookahead_literal('(', 0)
        value38 = xs36
        self.consume_literal(')')
        return value38

    def parse_write(self) -> transactions_pb2.Write:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('undefine', 1):
                _t331 = 1
            else:
                if self.match_lookahead_literal('define', 1):
                    _t332 = 0
                else:
                    if self.match_lookahead_literal('context', 1):
                        _t333 = 2
                    else:
                        _t333 = -1
                    _t332 = _t333
                _t331 = _t332
            _t328 = _t331
        else:
            _t328 = -1
        prediction39 = _t328
        if prediction39 == 2:
            _t335 = self.parse_context()
            value42 = _t335
            _t336 = transactions_pb2.Write(context=value42)
            _t334 = _t336
        else:
            if prediction39 == 1:
                _t338 = self.parse_undefine()
                value41 = _t338
                _t339 = transactions_pb2.Write(undefine=value41)
                _t337 = _t339
            else:
                if prediction39 == 0:
                    _t341 = self.parse_define()
                    value40 = _t341
                    _t342 = transactions_pb2.Write(define=value40)
                    _t340 = _t342
                else:
                    raise ParseError(f"{'Unexpected token in write'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t340 = None
                _t337 = _t340
            _t334 = _t337
        return _t334

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal('(')
        self.consume_literal('define')
        _t343 = self.parse_fragment()
        fragment43 = _t343
        self.consume_literal(')')
        _t344 = transactions_pb2.Define(fragment=fragment43)
        return _t344

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal('(')
        self.consume_literal('fragment')
        _t345 = self.parse_new_fragment_id()
        fragment_id44 = _t345
        xs45 = []
        cond46 = self.match_lookahead_literal('(', 0)
        while cond46:
            _t346 = self.parse_declaration()
            xs45.append(_t346)
            cond46 = self.match_lookahead_literal('(', 0)
        declarations47 = xs45
        self.consume_literal(')')
        return self.construct_fragment(fragment_id44, declarations47)

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        _t347 = self.parse_fragment_id()
        fragment_id48 = _t347
        self.start_fragment(fragment_id48)
        return fragment_id48

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('functional_dependency', 1):
                _t349 = 2
            else:
                if self.match_lookahead_literal('def', 1):
                    _t350 = 0
                else:
                    _t350 = (self.match_lookahead_literal('algorithm', 1) or -1)
                _t349 = _t350
            _t348 = _t349
        else:
            _t348 = -1
        prediction49 = _t348
        if prediction49 == 2:
            _t352 = self.parse_constraint()
            value52 = _t352
            _t353 = logic_pb2.Declaration(constraint=value52)
            _t351 = _t353
        else:
            if prediction49 == 1:
                _t355 = self.parse_algorithm()
                value51 = _t355
                _t356 = logic_pb2.Declaration(algorithm=value51)
                _t354 = _t356
            else:
                if prediction49 == 0:
                    _t358 = self.parse_def()
                    value50 = _t358
                    _t359 = logic_pb2.Declaration(**{'def': value50})  # type: ignore
                    _t357 = _t359
                else:
                    raise ParseError(f"{'Unexpected token in declaration'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t357 = None
                _t354 = _t357
            _t351 = _t354
        return _t351

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal('(')
        self.consume_literal('def')
        _t360 = self.parse_relation_id()
        name53 = _t360
        _t361 = self.parse_abstraction()
        body54 = _t361
        if self.match_lookahead_literal('(', 0):
            _t363 = self.parse_attrs()
            _t362 = _t363
        else:
            _t362 = None
        attrs55 = _t362
        self.consume_literal(')')
        _t364 = logic_pb2.Def(name=name53, body=body54, attrs=(attrs55 if attrs55 is not None else []))
        return _t364

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_terminal('INT', 0):
            _t366 = 1
        else:
            if self.match_lookahead_terminal('COLON_SYMBOL', 0):
                _t367 = 0
            else:
                _t367 = -1
            _t366 = _t367
        prediction56 = _t366
        if prediction56 == 1:
            INT58 = self.consume_terminal('INT')
            _t368 = logic_pb2.RelationId(id_low=INT58 & 0xFFFFFFFFFFFFFFFF, id_high=(INT58 >> 64) & 0xFFFFFFFFFFFFFFFF)
        else:
            if prediction56 == 0:
                symbol57 = self.consume_terminal('COLON_SYMBOL')
                _t369 = self.relation_id_from_string(symbol57)
            else:
                raise ParseError(f"{'Unexpected token in relation_id'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t369 = None
            _t368 = _t369
        return _t368

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal('(')
        _t370 = self.parse_bindings()
        bindings59 = _t370
        _t371 = self.parse_formula()
        formula60 = _t371
        self.consume_literal(')')
        _t372 = logic_pb2.Abstraction(vars=(bindings59[0] + (bindings59[1] if bindings59[1] is not None else [])), value=formula60)
        return _t372

    def parse_bindings(self) -> tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]:
        self.consume_literal('[')
        xs61 = []
        cond62 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond62:
            _t373 = self.parse_binding()
            xs61.append(_t373)
            cond62 = self.match_lookahead_terminal('SYMBOL', 0)
        keys63 = xs61
        if self.match_lookahead_literal('|', 0):
            _t375 = self.parse_value_bindings()
            _t374 = _t375
        else:
            _t374 = None
        values64 = _t374
        self.consume_literal(']')
        return (keys63, (values64 if values64 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol65 = self.consume_terminal('SYMBOL')
        self.consume_literal('::')
        _t376 = self.parse_type()
        type66 = _t376
        _t377 = logic_pb2.Var(name=symbol65)
        _t378 = logic_pb2.Binding(var=_t377, type=type66)
        return _t378

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal('UNKNOWN', 0):
            _t379 = 0
        else:
            if self.match_lookahead_literal('UINT128', 0):
                _t380 = 4
            else:
                if self.match_lookahead_literal('STRING', 0):
                    _t390 = 1
                else:
                    if self.match_lookahead_literal('MISSING', 0):
                        _t391 = 8
                    else:
                        if self.match_lookahead_literal('INT128', 0):
                            _t392 = 5
                        else:
                            if self.match_lookahead_literal('INT', 0):
                                _t393 = 2
                            else:
                                if self.match_lookahead_literal('FLOAT', 0):
                                    _t394 = 3
                                else:
                                    if self.match_lookahead_literal('DATETIME', 0):
                                        _t395 = 7
                                    else:
                                        if self.match_lookahead_literal('DATE', 0):
                                            _t396 = 6
                                        else:
                                            if self.match_lookahead_literal('BOOLEAN', 0):
                                                _t397 = 10
                                            else:
                                                if self.match_lookahead_literal('BOOL', 0):
                                                    _t398 = 10
                                                else:
                                                    if self.match_lookahead_literal('(', 0):
                                                        _t399 = 9
                                                    else:
                                                        _t399 = -1
                                                    _t398 = _t399
                                                _t397 = _t398
                                            _t396 = _t397
                                        _t395 = _t396
                                    _t394 = _t395
                                _t393 = _t394
                            _t392 = _t393
                        _t391 = _t392
                    _t390 = _t391
                _t380 = _t390
            _t379 = _t380
        prediction67 = _t379
        if prediction67 == 10:
            _t401 = self.parse_boolean_type()
            value78 = _t401
            _t402 = logic_pb2.Type(boolean_type=value78)
            _t400 = _t402
        else:
            if prediction67 == 9:
                _t404 = self.parse_decimal_type()
                value77 = _t404
                _t405 = logic_pb2.Type(decimal_type=value77)
                _t403 = _t405
            else:
                if prediction67 == 8:
                    _t407 = self.parse_missing_type()
                    value76 = _t407
                    _t408 = logic_pb2.Type(missing_type=value76)
                    _t406 = _t408
                else:
                    if prediction67 == 7:
                        _t410 = self.parse_datetime_type()
                        value75 = _t410
                        _t411 = logic_pb2.Type(datetime_type=value75)
                        _t409 = _t411
                    else:
                        if prediction67 == 6:
                            _t413 = self.parse_date_type()
                            value74 = _t413
                            _t414 = logic_pb2.Type(date_type=value74)
                            _t412 = _t414
                        else:
                            if prediction67 == 5:
                                _t416 = self.parse_int128_type()
                                value73 = _t416
                                _t417 = logic_pb2.Type(int128_type=value73)
                                _t415 = _t417
                            else:
                                if prediction67 == 4:
                                    _t419 = self.parse_uint128_type()
                                    value72 = _t419
                                    _t420 = logic_pb2.Type(uint128_type=value72)
                                    _t418 = _t420
                                else:
                                    if prediction67 == 3:
                                        _t422 = self.parse_float_type()
                                        value71 = _t422
                                        _t423 = logic_pb2.Type(float_type=value71)
                                        _t421 = _t423
                                    else:
                                        if prediction67 == 2:
                                            _t425 = self.parse_int_type()
                                            value70 = _t425
                                            _t426 = logic_pb2.Type(int_type=value70)
                                            _t424 = _t426
                                        else:
                                            if prediction67 == 1:
                                                _t428 = self.parse_string_type()
                                                value69 = _t428
                                                _t429 = logic_pb2.Type(string_type=value69)
                                                _t427 = _t429
                                            else:
                                                if prediction67 == 0:
                                                    _t431 = self.parse_unspecified_type()
                                                    value68 = _t431
                                                    _t432 = logic_pb2.Type(unspecified_type=value68)
                                                    _t430 = _t432
                                                else:
                                                    raise ParseError(f"{'Unexpected token in type'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                    _t430 = None
                                                _t427 = _t430
                                            _t424 = _t427
                                        _t421 = _t424
                                    _t418 = _t421
                                _t415 = _t418
                            _t412 = _t415
                        _t409 = _t412
                    _t406 = _t409
                _t403 = _t406
            _t400 = _t403
        return _t400

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        self.consume_literal('UNKNOWN')
        _t433 = logic_pb2.UnspecifiedType()
        return _t433

    def parse_string_type(self) -> logic_pb2.StringType:
        self.consume_literal('STRING')
        _t434 = logic_pb2.StringType()
        return _t434

    def parse_int_type(self) -> logic_pb2.IntType:
        self.consume_literal('INT')
        _t435 = logic_pb2.IntType()
        return _t435

    def parse_float_type(self) -> logic_pb2.FloatType:
        self.consume_literal('FLOAT')
        _t436 = logic_pb2.FloatType()
        return _t436

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        self.consume_literal('UINT128')
        _t437 = logic_pb2.UInt128Type()
        return _t437

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        self.consume_literal('INT128')
        _t438 = logic_pb2.Int128Type()
        return _t438

    def parse_date_type(self) -> logic_pb2.DateType:
        self.consume_literal('DATE')
        _t439 = logic_pb2.DateType()
        return _t439

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        self.consume_literal('DATETIME')
        _t440 = logic_pb2.DateTimeType()
        return _t440

    def parse_missing_type(self) -> logic_pb2.MissingType:
        self.consume_literal('MISSING')
        _t441 = logic_pb2.MissingType()
        return _t441

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        self.consume_literal('(')
        self.consume_literal('DECIMAL')
        precision79 = self.consume_terminal('INT')
        scale80 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t442 = logic_pb2.DecimalType(precision=precision79, scale=scale80)
        return _t442

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        if self.match_lookahead_literal('BOOLEAN', 0):
            _t443 = 0
        else:
            _t443 = (self.match_lookahead_literal('BOOL', 0) or -1)
        prediction81 = _t443
        if prediction81 == 1:
            self.consume_literal('BOOL')
            _t445 = logic_pb2.BooleanType()
            _t444 = _t445
        else:
            if prediction81 == 0:
                self.consume_literal('BOOLEAN')
                _t447 = logic_pb2.BooleanType()
                _t446 = _t447
            else:
                raise ParseError(f"{'Unexpected token in boolean_type'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t446 = None
            _t444 = _t446
        return _t444

    def parse_value_bindings(self) -> list[logic_pb2.Binding]:
        self.consume_literal('|')
        xs82 = []
        cond83 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond83:
            _t448 = self.parse_binding()
            xs82.append(_t448)
            cond83 = self.match_lookahead_terminal('SYMBOL', 0)
        values84 = xs82
        return values84

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('true', 1):
                _t450 = 0
            else:
                if self.match_lookahead_literal('relatom', 1):
                    _t451 = 11
                else:
                    if self.match_lookahead_literal('reduce', 1):
                        _t452 = 3
                    else:
                        if self.match_lookahead_literal('primitive', 1):
                            _t453 = 10
                        else:
                            if self.match_lookahead_literal('pragma', 1):
                                _t454 = 9
                            else:
                                if self.match_lookahead_literal('or', 1):
                                    _t455 = 5
                                else:
                                    if self.match_lookahead_literal('not', 1):
                                        _t456 = 6
                                    else:
                                        if self.match_lookahead_literal('ffi', 1):
                                            _t457 = 7
                                        else:
                                            if self.match_lookahead_literal('false', 1):
                                                _t471 = 1
                                            else:
                                                if self.match_lookahead_literal('exists', 1):
                                                    _t472 = 2
                                                else:
                                                    if self.match_lookahead_literal('cast', 1):
                                                        _t473 = 12
                                                    else:
                                                        if self.match_lookahead_literal('atom', 1):
                                                            _t474 = 8
                                                        else:
                                                            if self.match_lookahead_literal('and', 1):
                                                                _t475 = 4
                                                            else:
                                                                if self.match_lookahead_literal('>=', 1):
                                                                    _t476 = 10
                                                                else:
                                                                    if self.match_lookahead_literal('>', 1):
                                                                        _t477 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal('=', 1):
                                                                            _t478 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal('<=', 1):
                                                                                _t479 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal('<', 1):
                                                                                    _t480 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal('/', 1):
                                                                                        _t481 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal('-', 1):
                                                                                            _t482 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal('+', 1):
                                                                                                _t483 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal('*', 1):
                                                                                                    _t484 = 10
                                                                                                else:
                                                                                                    _t484 = -1
                                                                                                _t483 = _t484
                                                                                            _t482 = _t483
                                                                                        _t481 = _t482
                                                                                    _t480 = _t481
                                                                                _t479 = _t480
                                                                            _t478 = _t479
                                                                        _t477 = _t478
                                                                    _t476 = _t477
                                                                _t475 = _t476
                                                            _t474 = _t475
                                                        _t473 = _t474
                                                    _t472 = _t473
                                                _t471 = _t472
                                            _t457 = _t471
                                        _t456 = _t457
                                    _t455 = _t456
                                _t454 = _t455
                            _t453 = _t454
                        _t452 = _t453
                    _t451 = _t452
                _t450 = _t451
            _t449 = _t450
        else:
            _t449 = -1
        prediction85 = _t449
        if prediction85 == 12:
            _t486 = self.parse_cast()
            value98 = _t486
            _t487 = logic_pb2.Formula(cast=value98)
            _t485 = _t487
        else:
            if prediction85 == 11:
                _t489 = self.parse_relatom()
                value97 = _t489
                _t490 = logic_pb2.Formula(rel_atom=value97)
                _t488 = _t490
            else:
                if prediction85 == 10:
                    _t492 = self.parse_primitive()
                    value96 = _t492
                    _t493 = logic_pb2.Formula(primitive=value96)
                    _t491 = _t493
                else:
                    if prediction85 == 9:
                        _t495 = self.parse_pragma()
                        value95 = _t495
                        _t496 = logic_pb2.Formula(pragma=value95)
                        _t494 = _t496
                    else:
                        if prediction85 == 8:
                            _t498 = self.parse_atom()
                            value94 = _t498
                            _t499 = logic_pb2.Formula(atom=value94)
                            _t497 = _t499
                        else:
                            if prediction85 == 7:
                                _t501 = self.parse_ffi()
                                value93 = _t501
                                _t502 = logic_pb2.Formula(ffi=value93)
                                _t500 = _t502
                            else:
                                if prediction85 == 6:
                                    _t504 = self.parse_not()
                                    value92 = _t504
                                    _t505 = logic_pb2.Formula(**{'not': value92})  # type: ignore
                                    _t503 = _t505
                                else:
                                    if prediction85 == 5:
                                        _t507 = self.parse_disjunction()
                                        value91 = _t507
                                        _t508 = logic_pb2.Formula(disjunction=value91)
                                        _t506 = _t508
                                    else:
                                        if prediction85 == 4:
                                            _t510 = self.parse_conjunction()
                                            value90 = _t510
                                            _t511 = logic_pb2.Formula(conjunction=value90)
                                            _t509 = _t511
                                        else:
                                            if prediction85 == 3:
                                                _t513 = self.parse_reduce()
                                                value89 = _t513
                                                _t514 = logic_pb2.Formula(reduce=value89)
                                                _t512 = _t514
                                            else:
                                                if prediction85 == 2:
                                                    _t516 = self.parse_exists()
                                                    value88 = _t516
                                                    _t517 = logic_pb2.Formula(exists=value88)
                                                    _t515 = _t517
                                                else:
                                                    if prediction85 == 1:
                                                        _t519 = self.parse_false()
                                                        value87 = _t519
                                                        _t520 = logic_pb2.Formula(false=value87)
                                                        _t518 = _t520
                                                    else:
                                                        if prediction85 == 0:
                                                            _t522 = self.parse_true()
                                                            value86 = _t522
                                                            _t523 = logic_pb2.Formula(true=value86)
                                                            _t521 = _t523
                                                        else:
                                                            raise ParseError(f"{'Unexpected token in formula'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t521 = None
                                                        _t518 = _t521
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
            _t485 = _t488
        return _t485

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('true')
        self.consume_literal(')')
        _t524 = logic_pb2.Conjunction(args=[])
        return _t524

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('false')
        self.consume_literal(')')
        _t525 = logic_pb2.Disjunction(args=[])
        return _t525

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal('(')
        self.consume_literal('exists')
        _t526 = self.parse_bindings()
        bindings99 = _t526
        _t527 = self.parse_formula()
        formula100 = _t527
        self.consume_literal(')')
        _t528 = logic_pb2.Abstraction(vars=(bindings99[0] + (bindings99[1] if bindings99[1] is not None else [])), value=formula100)
        _t529 = logic_pb2.Exists(body=_t528)
        return _t529

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal('(')
        self.consume_literal('reduce')
        _t530 = self.parse_abstraction()
        op101 = _t530
        _t531 = self.parse_abstraction()
        body102 = _t531
        if self.match_lookahead_literal('(', 0):
            _t533 = self.parse_terms()
            _t532 = _t533
        else:
            _t532 = None
        terms103 = _t532
        self.consume_literal(')')
        _t534 = logic_pb2.Reduce(op=op101, body=body102, terms=(terms103 if terms103 is not None else []))
        return _t534

    def parse_terms(self) -> list[logic_pb2.Term]:
        self.consume_literal('(')
        self.consume_literal('terms')
        xs104 = []
        cond105 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond105:
            _t535 = self.parse_term()
            xs104.append(_t535)
            cond105 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        value106 = xs104
        self.consume_literal(')')
        return value106

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_terminal('UINT128', 0):
            _t537 = 1
        else:
            if self.match_lookahead_terminal('SYMBOL', 0):
                _t538 = 0
            else:
                _t538 = (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or (self.match_lookahead_literal('true', 0) or (self.match_lookahead_literal('missing', 0) or (self.match_lookahead_literal('false', 0) or (self.match_lookahead_literal('(', 0) or -1)))))))))
            _t537 = _t538
        prediction107 = _t537
        if prediction107 == 1:
            _t540 = self.parse_constant()
            value109 = _t540
            _t541 = logic_pb2.Term(constant=value109)
            _t539 = _t541
        else:
            if prediction107 == 0:
                _t543 = self.parse_var()
                value108 = _t543
                _t544 = logic_pb2.Term(var=value108)
                _t542 = _t544
            else:
                raise ParseError(f"{'Unexpected token in term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t542 = None
            _t539 = _t542
        return _t539

    def parse_var(self) -> logic_pb2.Var:
        symbol110 = self.consume_terminal('SYMBOL')
        _t545 = logic_pb2.Var(name=symbol110)
        return _t545

    def parse_constant(self) -> logic_pb2.Value:
        _t546 = self.parse_value()
        x111 = _t546
        return x111

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('and')
        xs112 = []
        cond113 = self.match_lookahead_literal('(', 0)
        while cond113:
            _t547 = self.parse_formula()
            xs112.append(_t547)
            cond113 = self.match_lookahead_literal('(', 0)
        args114 = xs112
        self.consume_literal(')')
        _t548 = logic_pb2.Conjunction(args=args114)
        return _t548

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('or')
        xs115 = []
        cond116 = self.match_lookahead_literal('(', 0)
        while cond116:
            _t549 = self.parse_formula()
            xs115.append(_t549)
            cond116 = self.match_lookahead_literal('(', 0)
        args117 = xs115
        self.consume_literal(')')
        _t550 = logic_pb2.Disjunction(args=args117)
        return _t550

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal('(')
        self.consume_literal('not')
        _t551 = self.parse_formula()
        arg118 = _t551
        self.consume_literal(')')
        _t552 = logic_pb2.Not(arg=arg118)
        return _t552

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal('(')
        self.consume_literal('ffi')
        _t553 = self.parse_name()
        name119 = _t553
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('args', 1)):
            _t555 = self.parse_ffi_args()
            _t554 = _t555
        else:
            _t554 = None
        args120 = _t554
        if self.match_lookahead_literal('(', 0):
            _t557 = self.parse_terms()
            _t556 = _t557
        else:
            _t556 = None
        terms121 = _t556
        self.consume_literal(')')
        _t558 = logic_pb2.FFI(name=name119, args=(args120 if args120 is not None else []), terms=(terms121 if terms121 is not None else []))
        return _t558

    def parse_name(self) -> str:
        symbol122 = self.consume_terminal('COLON_SYMBOL')
        return symbol122

    def parse_ffi_args(self) -> list[logic_pb2.Abstraction]:
        self.consume_literal('(')
        self.consume_literal('args')
        xs123 = []
        cond124 = self.match_lookahead_literal('(', 0)
        while cond124:
            _t559 = self.parse_abstraction()
            xs123.append(_t559)
            cond124 = self.match_lookahead_literal('(', 0)
        value125 = xs123
        self.consume_literal(')')
        return value125

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal('(')
        self.consume_literal('atom')
        _t560 = self.parse_relation_id()
        name126 = _t560
        xs127 = []
        cond128 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond128:
            _t561 = self.parse_term()
            xs127.append(_t561)
            cond128 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms129 = xs127
        self.consume_literal(')')
        _t562 = logic_pb2.Atom(name=name126, terms=terms129)
        return _t562

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal('(')
        self.consume_literal('pragma')
        _t563 = self.parse_name()
        name130 = _t563
        xs131 = []
        cond132 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond132:
            _t564 = self.parse_term()
            xs131.append(_t564)
            cond132 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms133 = xs131
        self.consume_literal(')')
        _t565 = logic_pb2.Pragma(name=name130, terms=terms133)
        return _t565

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('primitive', 1):
                _t567 = 9
            else:
                if self.match_lookahead_literal('>=', 1):
                    _t568 = 4
                else:
                    if self.match_lookahead_literal('>', 1):
                        _t569 = 3
                    else:
                        if self.match_lookahead_literal('=', 1):
                            _t570 = 0
                        else:
                            if self.match_lookahead_literal('<=', 1):
                                _t571 = 2
                            else:
                                if self.match_lookahead_literal('<', 1):
                                    _t576 = 1
                                else:
                                    if self.match_lookahead_literal('/', 1):
                                        _t577 = 8
                                    else:
                                        if self.match_lookahead_literal('-', 1):
                                            _t578 = 6
                                        else:
                                            if self.match_lookahead_literal('+', 1):
                                                _t579 = 5
                                            else:
                                                if self.match_lookahead_literal('*', 1):
                                                    _t580 = 7
                                                else:
                                                    _t580 = -1
                                                _t579 = _t580
                                            _t578 = _t579
                                        _t577 = _t578
                                    _t576 = _t577
                                _t571 = _t576
                            _t570 = _t571
                        _t569 = _t570
                    _t568 = _t569
                _t567 = _t568
            _t566 = _t567
        else:
            _t566 = -1
        prediction134 = _t566
        if prediction134 == 9:
            self.consume_literal('(')
            self.consume_literal('primitive')
            _t582 = self.parse_name()
            name144 = _t582
            xs145 = []
            cond146 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            while cond146:
                _t583 = self.parse_relterm()
                xs145.append(_t583)
                cond146 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            terms147 = xs145
            self.consume_literal(')')
            _t584 = logic_pb2.Primitive(name=name144, terms=terms147)
            _t581 = _t584
        else:
            if prediction134 == 8:
                _t586 = self.parse_divide()
                op143 = _t586
                _t585 = op143
            else:
                if prediction134 == 7:
                    _t588 = self.parse_multiply()
                    op142 = _t588
                    _t587 = op142
                else:
                    if prediction134 == 6:
                        _t590 = self.parse_minus()
                        op141 = _t590
                        _t589 = op141
                    else:
                        if prediction134 == 5:
                            _t592 = self.parse_add()
                            op140 = _t592
                            _t591 = op140
                        else:
                            if prediction134 == 4:
                                _t594 = self.parse_gt_eq()
                                op139 = _t594
                                _t593 = op139
                            else:
                                if prediction134 == 3:
                                    _t596 = self.parse_gt()
                                    op138 = _t596
                                    _t595 = op138
                                else:
                                    if prediction134 == 2:
                                        _t598 = self.parse_lt_eq()
                                        op137 = _t598
                                        _t597 = op137
                                    else:
                                        if prediction134 == 1:
                                            _t600 = self.parse_lt()
                                            op136 = _t600
                                            _t599 = op136
                                        else:
                                            if prediction134 == 0:
                                                _t602 = self.parse_eq()
                                                op135 = _t602
                                                _t601 = op135
                                            else:
                                                raise ParseError(f"{'Unexpected token in primitive'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t601 = None
                                            _t599 = _t601
                                        _t597 = _t599
                                    _t595 = _t597
                                _t593 = _t595
                            _t591 = _t593
                        _t589 = _t591
                    _t587 = _t589
                _t585 = _t587
            _t581 = _t585
        return _t581

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('=')
        _t603 = self.parse_term()
        left148 = _t603
        _t604 = self.parse_term()
        right149 = _t604
        self.consume_literal(')')
        _t605 = logic_pb2.RelTerm(term=left148)
        _t606 = logic_pb2.RelTerm(term=right149)
        _t607 = logic_pb2.Primitive(name='rel_primitive_eq', terms=[_t605, _t606])
        return _t607

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<')
        _t608 = self.parse_term()
        left150 = _t608
        _t609 = self.parse_term()
        right151 = _t609
        self.consume_literal(')')
        _t610 = logic_pb2.RelTerm(term=left150)
        _t611 = logic_pb2.RelTerm(term=right151)
        _t612 = logic_pb2.Primitive(name='rel_primitive_lt_monotype', terms=[_t610, _t611])
        return _t612

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<=')
        _t613 = self.parse_term()
        left152 = _t613
        _t614 = self.parse_term()
        right153 = _t614
        self.consume_literal(')')
        _t615 = logic_pb2.RelTerm(term=left152)
        _t616 = logic_pb2.RelTerm(term=right153)
        _t617 = logic_pb2.Primitive(name='rel_primitive_lt_eq_monotype', terms=[_t615, _t616])
        return _t617

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>')
        _t618 = self.parse_term()
        left154 = _t618
        _t619 = self.parse_term()
        right155 = _t619
        self.consume_literal(')')
        _t620 = logic_pb2.RelTerm(term=left154)
        _t621 = logic_pb2.RelTerm(term=right155)
        _t622 = logic_pb2.Primitive(name='rel_primitive_gt_monotype', terms=[_t620, _t621])
        return _t622

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>=')
        _t623 = self.parse_term()
        left156 = _t623
        _t624 = self.parse_term()
        right157 = _t624
        self.consume_literal(')')
        _t625 = logic_pb2.RelTerm(term=left156)
        _t626 = logic_pb2.RelTerm(term=right157)
        _t627 = logic_pb2.Primitive(name='rel_primitive_gt_eq_monotype', terms=[_t625, _t626])
        return _t627

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('+')
        _t628 = self.parse_term()
        left158 = _t628
        _t629 = self.parse_term()
        right159 = _t629
        _t630 = self.parse_term()
        result160 = _t630
        self.consume_literal(')')
        _t631 = logic_pb2.RelTerm(term=left158)
        _t632 = logic_pb2.RelTerm(term=right159)
        _t633 = logic_pb2.RelTerm(term=result160)
        _t634 = logic_pb2.Primitive(name='rel_primitive_add_monotype', terms=[_t631, _t632, _t633])
        return _t634

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('-')
        _t635 = self.parse_term()
        left161 = _t635
        _t636 = self.parse_term()
        right162 = _t636
        _t637 = self.parse_term()
        result163 = _t637
        self.consume_literal(')')
        _t638 = logic_pb2.RelTerm(term=left161)
        _t639 = logic_pb2.RelTerm(term=right162)
        _t640 = logic_pb2.RelTerm(term=result163)
        _t641 = logic_pb2.Primitive(name='rel_primitive_subtract_monotype', terms=[_t638, _t639, _t640])
        return _t641

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('*')
        _t642 = self.parse_term()
        left164 = _t642
        _t643 = self.parse_term()
        right165 = _t643
        _t644 = self.parse_term()
        result166 = _t644
        self.consume_literal(')')
        _t645 = logic_pb2.RelTerm(term=left164)
        _t646 = logic_pb2.RelTerm(term=right165)
        _t647 = logic_pb2.RelTerm(term=result166)
        _t648 = logic_pb2.Primitive(name='rel_primitive_multiply_monotype', terms=[_t645, _t646, _t647])
        return _t648

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('/')
        _t649 = self.parse_term()
        left167 = _t649
        _t650 = self.parse_term()
        right168 = _t650
        _t651 = self.parse_term()
        result169 = _t651
        self.consume_literal(')')
        _t652 = logic_pb2.RelTerm(term=left167)
        _t653 = logic_pb2.RelTerm(term=right168)
        _t654 = logic_pb2.RelTerm(term=result169)
        _t655 = logic_pb2.Primitive(name='rel_primitive_divide_monotype', terms=[_t652, _t653, _t654])
        return _t655

    def parse_relterm(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_terminal('UINT128', 0):
            _t2703 = 1
        else:
            if self.match_lookahead_terminal('SYMBOL', 0):
                _t3727 = 1
            else:
                if self.match_lookahead_terminal('STRING', 0):
                    _t4239 = 1
                else:
                    if self.match_lookahead_terminal('INT128', 0):
                        _t4495 = 1
                    else:
                        if self.match_lookahead_terminal('INT', 0):
                            _t4623 = 1
                        else:
                            if self.match_lookahead_terminal('FLOAT', 0):
                                _t4687 = 1
                            else:
                                if self.match_lookahead_terminal('DECIMAL', 0):
                                    _t4719 = 1
                                else:
                                    if self.match_lookahead_literal('true', 0):
                                        _t4735 = 1
                                    else:
                                        if self.match_lookahead_literal('missing', 0):
                                            _t4743 = 1
                                        else:
                                            if self.match_lookahead_literal('false', 0):
                                                _t4747 = 1
                                            else:
                                                if self.match_lookahead_literal('(', 0):
                                                    _t4749 = 1
                                                else:
                                                    if self.match_lookahead_literal('#', 0):
                                                        _t4750 = 0
                                                    else:
                                                        _t4750 = -1
                                                    _t4749 = _t4750
                                                _t4747 = _t4749
                                            _t4743 = _t4747
                                        _t4735 = _t4743
                                    _t4719 = _t4735
                                _t4687 = _t4719
                            _t4623 = _t4687
                        _t4495 = _t4623
                    _t4239 = _t4495
                _t3727 = _t4239
            _t2703 = _t3727
        prediction170 = _t2703
        if prediction170 == 1:
            _t4752 = self.parse_term()
            value172 = _t4752
            _t4753 = logic_pb2.RelTerm(term=value172)
            _t4751 = _t4753
        else:
            if prediction170 == 0:
                _t4755 = self.parse_specialized_value()
                value171 = _t4755
                _t4756 = logic_pb2.RelTerm(specialized_value=value171)
                _t4754 = _t4756
            else:
                raise ParseError(f"{'Unexpected token in relterm'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t4754 = None
            _t4751 = _t4754
        return _t4751

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal('#')
        _t4757 = self.parse_value()
        value173 = _t4757
        return value173

    def parse_relatom(self) -> logic_pb2.RelAtom:
        self.consume_literal('(')
        self.consume_literal('relatom')
        _t4758 = self.parse_name()
        name174 = _t4758
        xs175 = []
        cond176 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond176:
            _t4759 = self.parse_relterm()
            xs175.append(_t4759)
            cond176 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms177 = xs175
        self.consume_literal(')')
        _t4760 = logic_pb2.RelAtom(name=name174, terms=terms177)
        return _t4760

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal('(')
        self.consume_literal('cast')
        _t4761 = self.parse_term()
        input178 = _t4761
        _t4762 = self.parse_term()
        result179 = _t4762
        self.consume_literal(')')
        _t4763 = logic_pb2.Cast(input=input178, result=result179)
        return _t4763

    def parse_attrs(self) -> list[logic_pb2.Attribute]:
        self.consume_literal('(')
        self.consume_literal('attrs')
        xs180 = []
        cond181 = self.match_lookahead_literal('(', 0)
        while cond181:
            _t4764 = self.parse_attribute()
            xs180.append(_t4764)
            cond181 = self.match_lookahead_literal('(', 0)
        value182 = xs180
        self.consume_literal(')')
        return value182

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal('(')
        self.consume_literal('attribute')
        _t4765 = self.parse_name()
        name183 = _t4765
        xs184 = []
        cond185 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond185:
            _t4766 = self.parse_value()
            xs184.append(_t4766)
            cond185 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        args186 = xs184
        self.consume_literal(')')
        _t4767 = logic_pb2.Attribute(name=name183, args=args186)
        return _t4767

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal('(')
        self.consume_literal('algorithm')
        xs187 = []
        cond188 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        while cond188:
            _t4768 = self.parse_relation_id()
            xs187.append(_t4768)
            cond188 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        global189 = xs187
        _t4769 = self.parse_script()
        body190 = _t4769
        self.consume_literal(')')
        _t4770 = logic_pb2.Algorithm(**{'global': global189}, body=body190)  # type: ignore
        return _t4770

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal('(')
        self.consume_literal('script')
        xs191 = []
        cond192 = self.match_lookahead_literal('(', 0)
        while cond192:
            _t4771 = self.parse_construct()
            xs191.append(_t4771)
            cond192 = self.match_lookahead_literal('(', 0)
        constructs193 = xs191
        self.consume_literal(')')
        _t4772 = logic_pb2.Script(constructs=constructs193)
        return _t4772

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t4781 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t4785 = 1
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t4787 = 1
                    else:
                        if self.match_lookahead_literal('loop', 1):
                            _t4788 = 0
                        else:
                            _t4788 = (self.match_lookahead_literal('break', 1) or (self.match_lookahead_literal('assign', 1) or -1))
                        _t4787 = _t4788
                    _t4785 = _t4787
                _t4781 = _t4785
            _t4773 = _t4781
        else:
            _t4773 = -1
        prediction194 = _t4773
        if prediction194 == 1:
            _t4790 = self.parse_instruction()
            value196 = _t4790
            _t4791 = logic_pb2.Construct(instruction=value196)
            _t4789 = _t4791
        else:
            if prediction194 == 0:
                _t4793 = self.parse_loop()
                value195 = _t4793
                _t4794 = logic_pb2.Construct(loop=value195)
                _t4792 = _t4794
            else:
                raise ParseError(f"{'Unexpected token in construct'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t4792 = None
            _t4789 = _t4792
        return _t4789

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal('(')
        self.consume_literal('loop')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('init', 1)):
            _t4796 = self.parse_loop_init()
            _t4795 = _t4796
        else:
            _t4795 = None
        init197 = _t4795
        _t4797 = self.parse_script()
        body198 = _t4797
        self.consume_literal(')')
        _t4798 = logic_pb2.Loop(init=(init197 if init197 is not None else []), body=body198)
        return _t4798

    def parse_loop_init(self) -> list[logic_pb2.Instruction]:
        self.consume_literal('(')
        self.consume_literal('init')
        xs199 = []
        cond200 = self.match_lookahead_literal('(', 0)
        while cond200:
            _t4799 = self.parse_instruction()
            xs199.append(_t4799)
            cond200 = self.match_lookahead_literal('(', 0)
        value201 = xs199
        self.consume_literal(')')
        return value201

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t4805 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t4806 = 4
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t4807 = 3
                    else:
                        if self.match_lookahead_literal('break', 1):
                            _t4808 = 2
                        else:
                            if self.match_lookahead_literal('assign', 1):
                                _t4809 = 0
                            else:
                                _t4809 = -1
                            _t4808 = _t4809
                        _t4807 = _t4808
                    _t4806 = _t4807
                _t4805 = _t4806
            _t4800 = _t4805
        else:
            _t4800 = -1
        prediction202 = _t4800
        if prediction202 == 4:
            _t4811 = self.parse_monus_def()
            value207 = _t4811
            _t4812 = logic_pb2.Instruction(monus_def=value207)
            _t4810 = _t4812
        else:
            if prediction202 == 3:
                _t4814 = self.parse_monoid_def()
                value206 = _t4814
                _t4815 = logic_pb2.Instruction(monoid_def=value206)
                _t4813 = _t4815
            else:
                if prediction202 == 2:
                    _t4817 = self.parse_break()
                    value205 = _t4817
                    _t4818 = logic_pb2.Instruction(**{'break': value205})  # type: ignore
                    _t4816 = _t4818
                else:
                    if prediction202 == 1:
                        _t4820 = self.parse_upsert()
                        value204 = _t4820
                        _t4821 = logic_pb2.Instruction(upsert=value204)
                        _t4819 = _t4821
                    else:
                        if prediction202 == 0:
                            _t4823 = self.parse_assign()
                            value203 = _t4823
                            _t4824 = logic_pb2.Instruction(assign=value203)
                            _t4822 = _t4824
                        else:
                            raise ParseError(f"{'Unexpected token in instruction'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t4822 = None
                        _t4819 = _t4822
                    _t4816 = _t4819
                _t4813 = _t4816
            _t4810 = _t4813
        return _t4810

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal('(')
        self.consume_literal('assign')
        _t4825 = self.parse_relation_id()
        name208 = _t4825
        _t4826 = self.parse_abstraction()
        body209 = _t4826
        if self.match_lookahead_literal('(', 0):
            _t4828 = self.parse_attrs()
            _t4827 = _t4828
        else:
            _t4827 = None
        attrs210 = _t4827
        self.consume_literal(')')
        _t4829 = logic_pb2.Assign(name=name208, body=body209, attrs=(attrs210 if attrs210 is not None else []))
        return _t4829

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal('(')
        self.consume_literal('upsert')
        _t4830 = self.parse_relation_id()
        name211 = _t4830
        _t4831 = self.parse_abstraction_with_arity()
        body212 = _t4831
        if self.match_lookahead_literal('(', 0):
            _t4833 = self.parse_attrs()
            _t4832 = _t4833
        else:
            _t4832 = None
        attrs213 = _t4832
        self.consume_literal(')')
        _t4834 = logic_pb2.Upsert(name=name211, body=body212[0], attrs=(attrs213 if attrs213 is not None else []), value_arity=body212[1])
        return _t4834

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal('(')
        _t4835 = self.parse_bindings()
        bindings214 = _t4835
        _t4836 = self.parse_formula()
        formula215 = _t4836
        self.consume_literal(')')
        _t4837 = logic_pb2.Abstraction(vars=(bindings214[0] + (bindings214[1] if bindings214[1] is not None else [])), value=formula215)
        return (_t4837, len(bindings214[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal('(')
        self.consume_literal('break')
        _t4838 = self.parse_relation_id()
        name216 = _t4838
        _t4839 = self.parse_abstraction()
        body217 = _t4839
        if self.match_lookahead_literal('(', 0):
            _t4841 = self.parse_attrs()
            _t4840 = _t4841
        else:
            _t4840 = None
        attrs218 = _t4840
        self.consume_literal(')')
        _t4842 = logic_pb2.Break(name=name216, body=body217, attrs=(attrs218 if attrs218 is not None else []))
        return _t4842

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal('(')
        self.consume_literal('monoid')
        _t4843 = self.parse_monoid()
        monoid219 = _t4843
        _t4844 = self.parse_relation_id()
        name220 = _t4844
        _t4845 = self.parse_abstraction_with_arity()
        body221 = _t4845
        if self.match_lookahead_literal('(', 0):
            _t4847 = self.parse_attrs()
            _t4846 = _t4847
        else:
            _t4846 = None
        attrs222 = _t4846
        self.consume_literal(')')
        _t4848 = logic_pb2.MonoidDef(monoid=monoid219, name=name220, body=body221[0], attrs=(attrs222 if attrs222 is not None else []), value_arity=body221[1])
        return _t4848

    def parse_monoid(self) -> logic_pb2.Monoid:
        _t4849 = self.parse_type()
        type223 = _t4849
        self.consume_literal('::')
        _t4850 = self.parse_monoid_op()
        op224 = _t4850
        _t4851 = op224(type223)
        return _t4851

    def parse_monoid_op(self) -> Callable[[logic_pb2.Type], logic_pb2.Monoid]:
        if self.match_lookahead_literal('SUM', 0):
            _t4852 = 3
        else:
            if self.match_lookahead_literal('OR', 0):
                _t4853 = 0
            else:
                if self.match_lookahead_literal('MIN', 0):
                    _t4855 = 1
                else:
                    if self.match_lookahead_literal('MAX', 0):
                        _t4856 = 2
                    else:
                        _t4856 = -1
                    _t4855 = _t4856
                _t4853 = _t4855
            _t4852 = _t4853
        prediction225 = _t4852
        if prediction225 == 3:
            self.consume_literal('SUM')
            def _t4858(type):
                _t4859 = logic_pb2.SumMonoid(type=type)
                _t4860 = logic_pb2.Monoid(sum_monoid=_t4859)
                return _t4860
            _t4857 = _t4858
        else:
            if prediction225 == 2:
                self.consume_literal('MAX')
                def _t4862(type):
                    _t4863 = logic_pb2.MaxMonoid(type=type)
                    _t4864 = logic_pb2.Monoid(max_monoid=_t4863)
                    return _t4864
                _t4861 = _t4862
            else:
                if prediction225 == 1:
                    self.consume_literal('MIN')
                    def _t4866(type):
                        _t4867 = logic_pb2.MinMonoid(type=type)
                        _t4868 = logic_pb2.Monoid(min_monoid=_t4867)
                        return _t4868
                    _t4865 = _t4866
                else:
                    if prediction225 == 0:
                        self.consume_literal('OR')
                        def _t4870(type):
                            _t4871 = logic_pb2.OrMonoid()
                            _t4872 = logic_pb2.Monoid(or_monoid=_t4871)
                            return _t4872
                        _t4869 = _t4870
                    else:
                        raise ParseError(f"{'Unexpected token in monoid_op'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t4869 = None
                    _t4865 = _t4869
                _t4861 = _t4865
            _t4857 = _t4861
        return _t4857

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal('(')
        self.consume_literal('monus')
        _t4873 = self.parse_monoid()
        monoid226 = _t4873
        _t4874 = self.parse_relation_id()
        name227 = _t4874
        _t4875 = self.parse_abstraction_with_arity()
        body228 = _t4875
        if self.match_lookahead_literal('(', 0):
            _t4877 = self.parse_attrs()
            _t4876 = _t4877
        else:
            _t4876 = None
        attrs229 = _t4876
        self.consume_literal(')')
        _t4878 = logic_pb2.MonusDef(monoid=monoid226, name=name227, body=body228[0], attrs=(attrs229 if attrs229 is not None else []), value_arity=body228[1])
        return _t4878

    def parse_constraint(self) -> logic_pb2.Constraint:
        _t4879 = self.parse_functional_dependency()
        value230 = _t4879
        _t4880 = logic_pb2.Constraint(functional_dependency=value230)
        return _t4880

    def parse_functional_dependency(self) -> logic_pb2.FunctionalDependency:
        self.consume_literal('(')
        self.consume_literal('functional_dependency')
        _t4881 = self.parse_abstraction()
        guard231 = _t4881
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('keys', 1)):
            _t4883 = self.parse_functional_dependency_keys()
            _t4882 = _t4883
        else:
            _t4882 = None
        keys232 = _t4882
        if self.match_lookahead_literal('(', 0):
            _t4885 = self.parse_functional_dependency_values()
            _t4884 = _t4885
        else:
            _t4884 = None
        values233 = _t4884
        self.consume_literal(')')
        _t4886 = logic_pb2.FunctionalDependency(guard=guard231, keys=(keys232 if keys232 is not None else []), values=(values233 if values233 is not None else []))
        return _t4886

    def parse_functional_dependency_keys(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('keys')
        xs234 = []
        cond235 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond235:
            _t4887 = self.parse_var()
            xs234.append(_t4887)
            cond235 = self.match_lookahead_terminal('SYMBOL', 0)
        value236 = xs234
        self.consume_literal(')')
        return value236

    def parse_functional_dependency_values(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('values')
        xs237 = []
        cond238 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond238:
            _t4888 = self.parse_var()
            xs237.append(_t4888)
            cond238 = self.match_lookahead_terminal('SYMBOL', 0)
        value239 = xs237
        self.consume_literal(')')
        return value239

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal('(')
        self.consume_literal('undefine')
        _t4889 = self.parse_fragment_id()
        fragment_id240 = _t4889
        self.consume_literal(')')
        _t4890 = transactions_pb2.Undefine(fragment_id=fragment_id240)
        return _t4890

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal('(')
        self.consume_literal('context')
        xs241 = []
        cond242 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        while cond242:
            _t4891 = self.parse_relation_id()
            xs241.append(_t4891)
            cond242 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        relations243 = xs241
        self.consume_literal(')')
        _t4892 = transactions_pb2.Context(relations=relations243)
        return _t4892

    def parse_epoch_reads(self) -> list[transactions_pb2.Read]:
        self.consume_literal('(')
        self.consume_literal('reads')
        xs244 = []
        cond245 = self.match_lookahead_literal('(', 0)
        while cond245:
            _t4893 = self.parse_read()
            xs244.append(_t4893)
            cond245 = self.match_lookahead_literal('(', 0)
        value246 = xs244
        self.consume_literal(')')
        return value246

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('what_if', 1):
                _t4895 = 2
            else:
                if self.match_lookahead_literal('output', 1):
                    _t4899 = 1
                else:
                    if self.match_lookahead_literal('export', 1):
                        _t4900 = 4
                    else:
                        if self.match_lookahead_literal('demand', 1):
                            _t4901 = 0
                        else:
                            if self.match_lookahead_literal('abort', 1):
                                _t4902 = 3
                            else:
                                _t4902 = -1
                            _t4901 = _t4902
                        _t4900 = _t4901
                    _t4899 = _t4900
                _t4895 = _t4899
            _t4894 = _t4895
        else:
            _t4894 = -1
        prediction247 = _t4894
        if prediction247 == 4:
            _t4904 = self.parse_export()
            value252 = _t4904
            _t4905 = transactions_pb2.Read(export=value252)
            _t4903 = _t4905
        else:
            if prediction247 == 3:
                _t4907 = self.parse_abort()
                value251 = _t4907
                _t4908 = transactions_pb2.Read(abort=value251)
                _t4906 = _t4908
            else:
                if prediction247 == 2:
                    _t4910 = self.parse_what_if()
                    value250 = _t4910
                    _t4911 = transactions_pb2.Read(what_if=value250)
                    _t4909 = _t4911
                else:
                    if prediction247 == 1:
                        _t4913 = self.parse_output()
                        value249 = _t4913
                        _t4914 = transactions_pb2.Read(output=value249)
                        _t4912 = _t4914
                    else:
                        if prediction247 == 0:
                            _t4916 = self.parse_demand()
                            value248 = _t4916
                            _t4917 = transactions_pb2.Read(demand=value248)
                            _t4915 = _t4917
                        else:
                            raise ParseError(f"{'Unexpected token in read'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t4915 = None
                        _t4912 = _t4915
                    _t4909 = _t4912
                _t4906 = _t4909
            _t4903 = _t4906
        return _t4903

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal('(')
        self.consume_literal('demand')
        _t4918 = self.parse_relation_id()
        relation_id253 = _t4918
        self.consume_literal(')')
        _t4919 = transactions_pb2.Demand(relation_id=relation_id253)
        return _t4919

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal('(')
        self.consume_literal('output')
        if self.match_lookahead_terminal('COLON_SYMBOL', 0):
            _t4921 = self.parse_name()
            _t4920 = _t4921
        else:
            _t4920 = None
        name254 = _t4920
        _t4922 = self.parse_relation_id()
        relation_id255 = _t4922
        self.consume_literal(')')
        _t4923 = transactions_pb2.Output(name=name254, relation_id=relation_id255)
        return _t4923

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal('(')
        self.consume_literal('what_if')
        branch256 = self.consume_terminal('STRING')
        _t4924 = self.parse_epoch()
        epoch257 = _t4924
        self.consume_literal(')')
        _t4925 = transactions_pb2.WhatIf(branch=branch256, epoch=epoch257)
        return _t4925

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal('(')
        self.consume_literal('abort')
        if self.match_lookahead_terminal('COLON_SYMBOL', 0):
            _t4927 = self.parse_name()
            _t4926 = _t4927
        else:
            _t4926 = None
        name258 = _t4926
        _t4928 = self.parse_relation_id()
        relation_id259 = _t4928
        self.consume_literal(')')
        _t4929 = transactions_pb2.Abort(name=name258, relation_id=relation_id259)
        return _t4929

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal('(')
        self.consume_literal('export')
        _t4930 = self.parse_export_csv_config()
        config260 = _t4930
        self.consume_literal(')')
        _t4931 = transactions_pb2.Export(csv_config=config260)
        return _t4931

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal('(')
        self.consume_literal('export_csv_config')
        self.consume_literal('(')
        self.consume_literal('path')
        path261 = self.consume_terminal('STRING')
        self.consume_literal(')')
        _t4932 = self.parse_export_csvcolumns()
        columns262 = _t4932
        _t4933 = self.parse_config_dict()
        config263 = _t4933
        self.consume_literal(')')
        return self.export_csv_config(path261, columns262, config263)

    def parse_export_csvcolumns(self) -> list[transactions_pb2.ExportCSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs264 = []
        cond265 = self.match_lookahead_literal('(', 0)
        while cond265:
            _t4934 = self.parse_export_csvcolumn()
            xs264.append(_t4934)
            cond265 = self.match_lookahead_literal('(', 0)
        columns266 = xs264
        self.consume_literal(')')
        return columns266

    def parse_export_csvcolumn(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        name267 = self.consume_terminal('STRING')
        _t4935 = self.parse_relation_id()
        relation_id268 = _t4935
        self.consume_literal(')')
        _t4936 = transactions_pb2.ExportCSVColumn(column_name=name267, column_data=relation_id268)
        return _t4936


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
