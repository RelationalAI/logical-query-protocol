"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.


Command: src/meta/proto_tool.py ../proto/relationalai/lqp/v1/fragments.proto ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto --parser python -o src/lqp/generated_parser.py
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
            _t269 = self.parse_configure()
            _t268 = _t269
        else:
            _t268 = None
        configure0 = _t268
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('sync', 1)):
            _t271 = self.parse_sync()
            _t270 = _t271
        else:
            _t270 = None
        sync1 = _t270
        xs2 = []
        cond3 = self.match_lookahead_literal('(', 0)
        while cond3:
            _t272 = self.parse_epoch()
            xs2.append(_t272)
            cond3 = self.match_lookahead_literal('(', 0)
        epochs4 = xs2
        self.consume_literal(')')
        _t273 = transactions_pb2.Transaction(epochs=epochs4, configure=(configure0 if configure0 is not None else self.construct_configure([])), sync=sync1)
        return _t273

    def parse_configure(self) -> transactions_pb2.Configure:
        self.consume_literal('(')
        self.consume_literal('configure')
        _t274 = self.parse_config_dict()
        config_dict5 = _t274
        self.consume_literal(')')
        return self.construct_configure(config_dict5)

    def parse_config_dict(self) -> list[tuple[str, logic_pb2.Value]]:
        self.consume_literal('{')
        xs6 = []
        cond7 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond7:
            _t275 = self.parse_config_key_value()
            xs6.append(_t275)
            cond7 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        config_key_value8 = xs6
        self.consume_literal('}')
        return config_key_value8

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        symbol9 = self.consume_terminal('COLON_SYMBOL')
        _t276 = self.parse_value()
        value10 = _t276
        return (symbol9, value10,)

    def parse_value(self) -> logic_pb2.Value:
        if self.match_lookahead_terminal('UINT128', 0):
            _t277 = 5
        else:
            if self.match_lookahead_terminal('STRING', 0):
                _t278 = 2
            else:
                if self.match_lookahead_terminal('INT128', 0):
                    _t279 = 6
                else:
                    if self.match_lookahead_terminal('INT', 0):
                        _t280 = 3
                    else:
                        if self.match_lookahead_terminal('FLOAT', 0):
                            _t281 = 4
                        else:
                            if self.match_lookahead_terminal('DECIMAL', 0):
                                _t282 = 7
                            else:
                                if self.match_lookahead_literal('true', 0):
                                    _t283 = 9
                                else:
                                    if self.match_lookahead_literal('missing', 0):
                                        _t284 = 8
                                    else:
                                        if self.match_lookahead_literal('false', 0):
                                            _t285 = 10
                                        else:
                                            if self.match_lookahead_literal('(', 0):
                                                if self.match_lookahead_literal('datetime', 1):
                                                    _t288 = 1
                                                else:
                                                    if self.match_lookahead_literal('date', 1):
                                                        _t289 = 0
                                                    else:
                                                        _t289 = -1
                                                    _t288 = _t289
                                                _t286 = _t288
                                            else:
                                                _t286 = -1
                                            _t285 = _t286
                                        _t284 = _t285
                                    _t283 = _t284
                                _t282 = _t283
                            _t281 = _t282
                        _t280 = _t281
                    _t279 = _t280
                _t278 = _t279
            _t277 = _t278
        prediction11 = _t277
        if prediction11 == 10:
            self.consume_literal('false')
            _t291 = logic_pb2.Value(boolean_value=False)
            _t290 = _t291
        else:
            if prediction11 == 9:
                self.consume_literal('true')
                _t293 = logic_pb2.Value(boolean_value=True)
                _t292 = _t293
            else:
                if prediction11 == 8:
                    self.consume_literal('missing')
                    _t295 = logic_pb2.MissingValue()
                    _t296 = logic_pb2.Value(missing_value=_t295)
                    _t294 = _t296
                else:
                    if prediction11 == 7:
                        value19 = self.consume_terminal('DECIMAL')
                        _t298 = logic_pb2.Value(decimal_value=value19)
                        _t297 = _t298
                    else:
                        if prediction11 == 6:
                            value18 = self.consume_terminal('INT128')
                            _t300 = logic_pb2.Value(int128_value=value18)
                            _t299 = _t300
                        else:
                            if prediction11 == 5:
                                value17 = self.consume_terminal('UINT128')
                                _t302 = logic_pb2.Value(uint128_value=value17)
                                _t301 = _t302
                            else:
                                if prediction11 == 4:
                                    value16 = self.consume_terminal('FLOAT')
                                    _t304 = logic_pb2.Value(float_value=value16)
                                    _t303 = _t304
                                else:
                                    if prediction11 == 3:
                                        value15 = self.consume_terminal('INT')
                                        _t306 = logic_pb2.Value(int_value=value15)
                                        _t305 = _t306
                                    else:
                                        if prediction11 == 2:
                                            value14 = self.consume_terminal('STRING')
                                            _t308 = logic_pb2.Value(string_value=value14)
                                            _t307 = _t308
                                        else:
                                            if prediction11 == 1:
                                                _t310 = self.parse_datetime()
                                                value13 = _t310
                                                _t311 = logic_pb2.Value(datetime_value=value13)
                                                _t309 = _t311
                                            else:
                                                if prediction11 == 0:
                                                    _t313 = self.parse_date()
                                                    value12 = _t313
                                                    _t314 = logic_pb2.Value(date_value=value12)
                                                    _t312 = _t314
                                                else:
                                                    raise ParseError('Unexpected token in value' + f": {{self.lookahead(0)}}")
                                                    _t312 = None
                                                _t309 = _t312
                                            _t307 = _t309
                                        _t305 = _t307
                                    _t303 = _t305
                                _t301 = _t303
                            _t299 = _t301
                        _t297 = _t299
                    _t294 = _t297
                _t292 = _t294
            _t290 = _t292
        return _t290

    def parse_date(self) -> logic_pb2.DateValue:
        self.consume_literal('(')
        self.consume_literal('date')
        year20 = self.consume_terminal('INT')
        month21 = self.consume_terminal('INT')
        day22 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t315 = logic_pb2.DateValue(year=year20, month=month21, day=day22)
        return _t315

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
            _t316 = self.consume_terminal('INT')
        else:
            _t316 = None
        microsecond29 = _t316
        self.consume_literal(')')
        if microsecond29 is None:
            _t317 = 0
        else:
            _t317 = microsecond29
        _t318 = logic_pb2.DateTimeValue(year=year23, month=month24, day=day25, hour=hour26, minute=minute27, second=second28, microsecond=_t317)
        return _t318

    def parse_sync(self) -> transactions_pb2.Sync:
        self.consume_literal('(')
        self.consume_literal('sync')
        xs30 = []
        cond31 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        while cond31:
            _t319 = self.parse_fragment_id()
            xs30.append(_t319)
            cond31 = self.match_lookahead_terminal('COLON_SYMBOL', 0)
        fragments32 = xs30
        self.consume_literal(')')
        _t320 = transactions_pb2.Sync(fragments=fragments32)
        return _t320

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        symbol33 = self.consume_terminal('COLON_SYMBOL')
        return fragments_pb2.FragmentId(id=symbol33.encode())

    def parse_epoch(self) -> transactions_pb2.Epoch:
        self.consume_literal('(')
        self.consume_literal('epoch')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('writes', 1)):
            _t322 = self.parse_epoch_writes()
            _t321 = _t322
        else:
            _t321 = None
        writes34 = _t321
        if self.match_lookahead_literal('(', 0):
            _t324 = self.parse_epoch_reads()
            _t323 = _t324
        else:
            _t323 = None
        reads35 = _t323
        self.consume_literal(')')
        _t325 = transactions_pb2.Epoch(writes=(writes34 if writes34 is not None else []), reads=(reads35 if reads35 is not None else []))
        return _t325

    def parse_epoch_writes(self) -> list[transactions_pb2.Write]:
        self.consume_literal('(')
        self.consume_literal('writes')
        xs36 = []
        cond37 = self.match_lookahead_literal('(', 0)
        while cond37:
            _t326 = self.parse_write()
            xs36.append(_t326)
            cond37 = self.match_lookahead_literal('(', 0)
        value38 = xs36
        self.consume_literal(')')
        return value38

    def parse_write(self) -> transactions_pb2.Write:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('undefine', 1):
                _t330 = 1
            else:
                if self.match_lookahead_literal('define', 1):
                    _t331 = 0
                else:
                    if self.match_lookahead_literal('context', 1):
                        _t332 = 2
                    else:
                        _t332 = -1
                    _t331 = _t332
                _t330 = _t331
            _t327 = _t330
        else:
            _t327 = -1
        prediction39 = _t327
        if prediction39 == 2:
            _t334 = self.parse_context()
            value42 = _t334
            _t335 = transactions_pb2.Write(context=value42)
            _t333 = _t335
        else:
            if prediction39 == 1:
                _t337 = self.parse_undefine()
                value41 = _t337
                _t338 = transactions_pb2.Write(undefine=value41)
                _t336 = _t338
            else:
                if prediction39 == 0:
                    _t340 = self.parse_define()
                    value40 = _t340
                    _t341 = transactions_pb2.Write(define=value40)
                    _t339 = _t341
                else:
                    raise ParseError('Unexpected token in write' + f": {{self.lookahead(0)}}")
                    _t339 = None
                _t336 = _t339
            _t333 = _t336
        return _t333

    def parse_define(self) -> transactions_pb2.Define:
        self.consume_literal('(')
        self.consume_literal('define')
        _t342 = self.parse_fragment()
        fragment43 = _t342
        self.consume_literal(')')
        _t343 = transactions_pb2.Define(fragment=fragment43)
        return _t343

    def parse_fragment(self) -> fragments_pb2.Fragment:
        self.consume_literal('(')
        self.consume_literal('fragment')
        _t344 = self.parse_new_fragment_id()
        fragment_id44 = _t344
        xs45 = []
        cond46 = self.match_lookahead_literal('(', 0)
        while cond46:
            _t345 = self.parse_declaration()
            xs45.append(_t345)
            cond46 = self.match_lookahead_literal('(', 0)
        declarations47 = xs45
        self.consume_literal(')')
        return self.construct_fragment(fragment_id44, declarations47)

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        _t346 = self.parse_fragment_id()
        fragment_id48 = _t346
        self.start_fragment(fragment_id48)
        return fragment_id48

    def parse_declaration(self) -> logic_pb2.Declaration:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('functional_dependency', 1):
                _t348 = 2
            else:
                if self.match_lookahead_literal('def', 1):
                    _t349 = 0
                else:
                    _t349 = (self.match_lookahead_literal('algorithm', 1) or -1)
                _t348 = _t349
            _t347 = _t348
        else:
            _t347 = -1
        prediction49 = _t347
        if prediction49 == 2:
            _t351 = self.parse_constraint()
            value52 = _t351
            _t352 = logic_pb2.Declaration(constraint=value52)
            _t350 = _t352
        else:
            if prediction49 == 1:
                _t354 = self.parse_algorithm()
                value51 = _t354
                _t355 = logic_pb2.Declaration(algorithm=value51)
                _t353 = _t355
            else:
                if prediction49 == 0:
                    _t357 = self.parse_def()
                    value50 = _t357
                    _t358 = logic_pb2.Declaration(**{'def': value50})
                    _t356 = _t358
                else:
                    raise ParseError('Unexpected token in declaration' + f": {{self.lookahead(0)}}")
                    _t356 = None
                _t353 = _t356
            _t350 = _t353
        return _t350

    def parse_def(self) -> logic_pb2.Def:
        self.consume_literal('(')
        self.consume_literal('def')
        _t359 = self.parse_relation_id()
        name53 = _t359
        _t360 = self.parse_abstraction()
        body54 = _t360
        if self.match_lookahead_literal('(', 0):
            _t362 = self.parse_attrs()
            _t361 = _t362
        else:
            _t361 = None
        attrs55 = _t361
        self.consume_literal(')')
        _t363 = logic_pb2.Def(name=name53, body=body54, attrs=(attrs55 if attrs55 is not None else []))
        return _t363

    def parse_relation_id(self) -> logic_pb2.RelationId:
        if self.match_lookahead_terminal('INT', 0):
            _t365 = 1
        else:
            if self.match_lookahead_terminal('COLON_SYMBOL', 0):
                _t366 = 0
            else:
                _t366 = -1
            _t365 = _t366
        prediction56 = _t365
        if prediction56 == 1:
            INT58 = self.consume_terminal('INT')
            _t367 = logic_pb2.RelationId(id_low=INT58 & 0xFFFFFFFFFFFFFFFF, id_high=(INT58 >> 64) & 0xFFFFFFFFFFFFFFFF)
        else:
            if prediction56 == 0:
                symbol57 = self.consume_terminal('COLON_SYMBOL')
                _t368 = self.relation_id_from_string(symbol57)
            else:
                raise ParseError('Unexpected token in relation_id' + f": {{self.lookahead(0)}}")
                _t368 = None
            _t367 = _t368
        return _t367

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        self.consume_literal('(')
        _t369 = self.parse_bindings()
        bindings59 = _t369
        _t370 = self.parse_formula()
        formula60 = _t370
        self.consume_literal(')')
        _t371 = logic_pb2.Abstraction(vars=(bindings59[0] + (bindings59[1] if bindings59[1] is not None else [])), value=formula60)
        return _t371

    def parse_bindings(self) -> tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]:
        self.consume_literal('[')
        xs61 = []
        cond62 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond62:
            _t372 = self.parse_binding()
            xs61.append(_t372)
            cond62 = self.match_lookahead_terminal('SYMBOL', 0)
        keys63 = xs61
        if self.match_lookahead_literal('|', 0):
            _t374 = self.parse_value_bindings()
            _t373 = _t374
        else:
            _t373 = None
        values64 = _t373
        self.consume_literal(']')
        return (keys63, (values64 if values64 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        symbol65 = self.consume_terminal('SYMBOL')
        self.consume_literal('::')
        _t375 = self.parse_type()
        type66 = _t375
        _t376 = logic_pb2.Var(name=symbol65)
        _t377 = logic_pb2.Binding(var=_t376, type=type66)
        return _t377

    def parse_type(self) -> logic_pb2.Type:
        if self.match_lookahead_literal('UNKNOWN', 0):
            _t378 = 0
        else:
            if self.match_lookahead_literal('UINT128', 0):
                _t379 = 4
            else:
                if self.match_lookahead_literal('STRING', 0):
                    _t388 = 1
                else:
                    if self.match_lookahead_literal('MISSING', 0):
                        _t389 = 8
                    else:
                        if self.match_lookahead_literal('INT128', 0):
                            _t390 = 5
                        else:
                            if self.match_lookahead_literal('INT', 0):
                                _t391 = 2
                            else:
                                if self.match_lookahead_literal('FLOAT', 0):
                                    _t392 = 3
                                else:
                                    if self.match_lookahead_literal('DATETIME', 0):
                                        _t393 = 7
                                    else:
                                        if self.match_lookahead_literal('DATE', 0):
                                            _t394 = 6
                                        else:
                                            if self.match_lookahead_literal('BOOLEAN', 0):
                                                _t395 = 10
                                            else:
                                                if self.match_lookahead_literal('(', 0):
                                                    _t396 = 9
                                                else:
                                                    _t396 = -1
                                                _t395 = _t396
                                            _t394 = _t395
                                        _t393 = _t394
                                    _t392 = _t393
                                _t391 = _t392
                            _t390 = _t391
                        _t389 = _t390
                    _t388 = _t389
                _t379 = _t388
            _t378 = _t379
        prediction67 = _t378
        if prediction67 == 10:
            _t398 = self.parse_boolean_type()
            value78 = _t398
            _t399 = logic_pb2.Type(boolean_type=value78)
            _t397 = _t399
        else:
            if prediction67 == 9:
                _t401 = self.parse_decimal_type()
                value77 = _t401
                _t402 = logic_pb2.Type(decimal_type=value77)
                _t400 = _t402
            else:
                if prediction67 == 8:
                    _t404 = self.parse_missing_type()
                    value76 = _t404
                    _t405 = logic_pb2.Type(missing_type=value76)
                    _t403 = _t405
                else:
                    if prediction67 == 7:
                        _t407 = self.parse_datetime_type()
                        value75 = _t407
                        _t408 = logic_pb2.Type(datetime_type=value75)
                        _t406 = _t408
                    else:
                        if prediction67 == 6:
                            _t410 = self.parse_date_type()
                            value74 = _t410
                            _t411 = logic_pb2.Type(date_type=value74)
                            _t409 = _t411
                        else:
                            if prediction67 == 5:
                                _t413 = self.parse_int128_type()
                                value73 = _t413
                                _t414 = logic_pb2.Type(int128_type=value73)
                                _t412 = _t414
                            else:
                                if prediction67 == 4:
                                    _t416 = self.parse_uint128_type()
                                    value72 = _t416
                                    _t417 = logic_pb2.Type(uint128_type=value72)
                                    _t415 = _t417
                                else:
                                    if prediction67 == 3:
                                        _t419 = self.parse_float_type()
                                        value71 = _t419
                                        _t420 = logic_pb2.Type(float_type=value71)
                                        _t418 = _t420
                                    else:
                                        if prediction67 == 2:
                                            _t422 = self.parse_int_type()
                                            value70 = _t422
                                            _t423 = logic_pb2.Type(int_type=value70)
                                            _t421 = _t423
                                        else:
                                            if prediction67 == 1:
                                                _t425 = self.parse_string_type()
                                                value69 = _t425
                                                _t426 = logic_pb2.Type(string_type=value69)
                                                _t424 = _t426
                                            else:
                                                if prediction67 == 0:
                                                    _t428 = self.parse_unspecified_type()
                                                    value68 = _t428
                                                    _t429 = logic_pb2.Type(unspecified_type=value68)
                                                    _t427 = _t429
                                                else:
                                                    raise ParseError('Unexpected token in type' + f": {{self.lookahead(0)}}")
                                                    _t427 = None
                                                _t424 = _t427
                                            _t421 = _t424
                                        _t418 = _t421
                                    _t415 = _t418
                                _t412 = _t415
                            _t409 = _t412
                        _t406 = _t409
                    _t403 = _t406
                _t400 = _t403
            _t397 = _t400
        return _t397

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        self.consume_literal('UNKNOWN')
        _t430 = logic_pb2.UnspecifiedType()
        return _t430

    def parse_string_type(self) -> logic_pb2.StringType:
        self.consume_literal('STRING')
        _t431 = logic_pb2.StringType()
        return _t431

    def parse_int_type(self) -> logic_pb2.IntType:
        self.consume_literal('INT')
        _t432 = logic_pb2.IntType()
        return _t432

    def parse_float_type(self) -> logic_pb2.FloatType:
        self.consume_literal('FLOAT')
        _t433 = logic_pb2.FloatType()
        return _t433

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        self.consume_literal('UINT128')
        _t434 = logic_pb2.UInt128Type()
        return _t434

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        self.consume_literal('INT128')
        _t435 = logic_pb2.Int128Type()
        return _t435

    def parse_date_type(self) -> logic_pb2.DateType:
        self.consume_literal('DATE')
        _t436 = logic_pb2.DateType()
        return _t436

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        self.consume_literal('DATETIME')
        _t437 = logic_pb2.DateTimeType()
        return _t437

    def parse_missing_type(self) -> logic_pb2.MissingType:
        self.consume_literal('MISSING')
        _t438 = logic_pb2.MissingType()
        return _t438

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        self.consume_literal('(')
        self.consume_literal('DECIMAL')
        precision79 = self.consume_terminal('INT')
        scale80 = self.consume_terminal('INT')
        self.consume_literal(')')
        _t439 = logic_pb2.DecimalType(precision=precision79, scale=scale80)
        return _t439

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        self.consume_literal('BOOLEAN')
        _t440 = logic_pb2.BooleanType()
        return _t440

    def parse_value_bindings(self) -> list[logic_pb2.Binding]:
        self.consume_literal('|')
        xs81 = []
        cond82 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond82:
            _t441 = self.parse_binding()
            xs81.append(_t441)
            cond82 = self.match_lookahead_terminal('SYMBOL', 0)
        values83 = xs81
        return values83

    def parse_formula(self) -> logic_pb2.Formula:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('true', 1):
                _t443 = 0
            else:
                if self.match_lookahead_literal('relatom', 1):
                    _t444 = 11
                else:
                    if self.match_lookahead_literal('reduce', 1):
                        _t445 = 3
                    else:
                        if self.match_lookahead_literal('primitive', 1):
                            _t446 = 10
                        else:
                            if self.match_lookahead_literal('pragma', 1):
                                _t447 = 9
                            else:
                                if self.match_lookahead_literal('or', 1):
                                    _t448 = 5
                                else:
                                    if self.match_lookahead_literal('not', 1):
                                        _t449 = 6
                                    else:
                                        if self.match_lookahead_literal('ffi', 1):
                                            _t450 = 7
                                        else:
                                            if self.match_lookahead_literal('false', 1):
                                                _t464 = 1
                                            else:
                                                if self.match_lookahead_literal('exists', 1):
                                                    _t465 = 2
                                                else:
                                                    if self.match_lookahead_literal('cast', 1):
                                                        _t466 = 12
                                                    else:
                                                        if self.match_lookahead_literal('atom', 1):
                                                            _t467 = 8
                                                        else:
                                                            if self.match_lookahead_literal('and', 1):
                                                                _t468 = 4
                                                            else:
                                                                if self.match_lookahead_literal('>=', 1):
                                                                    _t469 = 10
                                                                else:
                                                                    if self.match_lookahead_literal('>', 1):
                                                                        _t470 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal('=', 1):
                                                                            _t471 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal('<=', 1):
                                                                                _t472 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal('<', 1):
                                                                                    _t473 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal('/', 1):
                                                                                        _t474 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal('-', 1):
                                                                                            _t475 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal('+', 1):
                                                                                                _t476 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal('*', 1):
                                                                                                    _t477 = 10
                                                                                                else:
                                                                                                    _t477 = -1
                                                                                                _t476 = _t477
                                                                                            _t475 = _t476
                                                                                        _t474 = _t475
                                                                                    _t473 = _t474
                                                                                _t472 = _t473
                                                                            _t471 = _t472
                                                                        _t470 = _t471
                                                                    _t469 = _t470
                                                                _t468 = _t469
                                                            _t467 = _t468
                                                        _t466 = _t467
                                                    _t465 = _t466
                                                _t464 = _t465
                                            _t450 = _t464
                                        _t449 = _t450
                                    _t448 = _t449
                                _t447 = _t448
                            _t446 = _t447
                        _t445 = _t446
                    _t444 = _t445
                _t443 = _t444
            _t442 = _t443
        else:
            _t442 = -1
        prediction84 = _t442
        if prediction84 == 12:
            _t479 = self.parse_cast()
            value97 = _t479
            _t480 = logic_pb2.Formula(cast=value97)
            _t478 = _t480
        else:
            if prediction84 == 11:
                _t482 = self.parse_relatom()
                value96 = _t482
                _t483 = logic_pb2.Formula(rel_atom=value96)
                _t481 = _t483
            else:
                if prediction84 == 10:
                    _t485 = self.parse_primitive()
                    value95 = _t485
                    _t486 = logic_pb2.Formula(primitive=value95)
                    _t484 = _t486
                else:
                    if prediction84 == 9:
                        _t488 = self.parse_pragma()
                        value94 = _t488
                        _t489 = logic_pb2.Formula(pragma=value94)
                        _t487 = _t489
                    else:
                        if prediction84 == 8:
                            _t491 = self.parse_atom()
                            value93 = _t491
                            _t492 = logic_pb2.Formula(atom=value93)
                            _t490 = _t492
                        else:
                            if prediction84 == 7:
                                _t494 = self.parse_ffi()
                                value92 = _t494
                                _t495 = logic_pb2.Formula(ffi=value92)
                                _t493 = _t495
                            else:
                                if prediction84 == 6:
                                    _t497 = self.parse_not()
                                    value91 = _t497
                                    _t498 = logic_pb2.Formula(**{'not': value91})
                                    _t496 = _t498
                                else:
                                    if prediction84 == 5:
                                        _t500 = self.parse_disjunction()
                                        value90 = _t500
                                        _t501 = logic_pb2.Formula(disjunction=value90)
                                        _t499 = _t501
                                    else:
                                        if prediction84 == 4:
                                            _t503 = self.parse_conjunction()
                                            value89 = _t503
                                            _t504 = logic_pb2.Formula(conjunction=value89)
                                            _t502 = _t504
                                        else:
                                            if prediction84 == 3:
                                                _t506 = self.parse_reduce()
                                                value88 = _t506
                                                _t507 = logic_pb2.Formula(reduce=value88)
                                                _t505 = _t507
                                            else:
                                                if prediction84 == 2:
                                                    _t509 = self.parse_exists()
                                                    value87 = _t509
                                                    _t510 = logic_pb2.Formula(exists=value87)
                                                    _t508 = _t510
                                                else:
                                                    if prediction84 == 1:
                                                        _t512 = self.parse_false()
                                                        value86 = _t512
                                                        _t513 = logic_pb2.Formula(false=value86)
                                                        _t511 = _t513
                                                    else:
                                                        if prediction84 == 0:
                                                            _t515 = self.parse_true()
                                                            value85 = _t515
                                                            _t516 = logic_pb2.Formula(true=value85)
                                                            _t514 = _t516
                                                        else:
                                                            raise ParseError('Unexpected token in formula' + f": {{self.lookahead(0)}}")
                                                            _t514 = None
                                                        _t511 = _t514
                                                    _t508 = _t511
                                                _t505 = _t508
                                            _t502 = _t505
                                        _t499 = _t502
                                    _t496 = _t499
                                _t493 = _t496
                            _t490 = _t493
                        _t487 = _t490
                    _t484 = _t487
                _t481 = _t484
            _t478 = _t481
        return _t478

    def parse_true(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('true')
        self.consume_literal(')')
        _t517 = logic_pb2.Conjunction(args=[])
        return _t517

    def parse_false(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('false')
        self.consume_literal(')')
        _t518 = logic_pb2.Disjunction(args=[])
        return _t518

    def parse_exists(self) -> logic_pb2.Exists:
        self.consume_literal('(')
        self.consume_literal('exists')
        _t519 = self.parse_bindings()
        bindings98 = _t519
        _t520 = self.parse_formula()
        formula99 = _t520
        self.consume_literal(')')
        _t521 = logic_pb2.Abstraction(vars=(bindings98[0] + (bindings98[1] if bindings98[1] is not None else [])), value=formula99)
        _t522 = logic_pb2.Exists(body=_t521)
        return _t522

    def parse_reduce(self) -> logic_pb2.Reduce:
        self.consume_literal('(')
        self.consume_literal('reduce')
        _t523 = self.parse_abstraction()
        op100 = _t523
        _t524 = self.parse_abstraction()
        body101 = _t524
        if self.match_lookahead_literal('(', 0):
            _t526 = self.parse_terms()
            _t525 = _t526
        else:
            _t525 = None
        terms102 = _t525
        self.consume_literal(')')
        _t527 = logic_pb2.Reduce(op=op100, body=body101, terms=(terms102 if terms102 is not None else []))
        return _t527

    def parse_terms(self) -> list[logic_pb2.Term]:
        self.consume_literal('(')
        self.consume_literal('terms')
        xs103 = []
        cond104 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond104:
            _t528 = self.parse_term()
            xs103.append(_t528)
            cond104 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        value105 = xs103
        self.consume_literal(')')
        return value105

    def parse_term(self) -> logic_pb2.Term:
        if self.match_lookahead_terminal('UINT128', 0):
            _t530 = 1
        else:
            if self.match_lookahead_terminal('SYMBOL', 0):
                _t531 = 0
            else:
                _t531 = (self.match_lookahead_terminal('STRING', 0) or (self.match_lookahead_terminal('INT128', 0) or (self.match_lookahead_terminal('INT', 0) or (self.match_lookahead_terminal('FLOAT', 0) or (self.match_lookahead_terminal('DECIMAL', 0) or (self.match_lookahead_literal('true', 0) or (self.match_lookahead_literal('missing', 0) or (self.match_lookahead_literal('false', 0) or (self.match_lookahead_literal('(', 0) or -1)))))))))
            _t530 = _t531
        prediction106 = _t530
        if prediction106 == 1:
            _t533 = self.parse_constant()
            value108 = _t533
            _t534 = logic_pb2.Term(constant=value108)
            _t532 = _t534
        else:
            if prediction106 == 0:
                _t536 = self.parse_var()
                value107 = _t536
                _t537 = logic_pb2.Term(var=value107)
                _t535 = _t537
            else:
                raise ParseError('Unexpected token in term' + f": {{self.lookahead(0)}}")
                _t535 = None
            _t532 = _t535
        return _t532

    def parse_var(self) -> logic_pb2.Var:
        symbol109 = self.consume_terminal('SYMBOL')
        _t538 = logic_pb2.Var(name=symbol109)
        return _t538

    def parse_constant(self) -> logic_pb2.Value:
        _t539 = self.parse_value()
        x110 = _t539
        return x110

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        self.consume_literal('(')
        self.consume_literal('and')
        xs111 = []
        cond112 = self.match_lookahead_literal('(', 0)
        while cond112:
            _t540 = self.parse_formula()
            xs111.append(_t540)
            cond112 = self.match_lookahead_literal('(', 0)
        args113 = xs111
        self.consume_literal(')')
        _t541 = logic_pb2.Conjunction(args=args113)
        return _t541

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        self.consume_literal('(')
        self.consume_literal('or')
        xs114 = []
        cond115 = self.match_lookahead_literal('(', 0)
        while cond115:
            _t542 = self.parse_formula()
            xs114.append(_t542)
            cond115 = self.match_lookahead_literal('(', 0)
        args116 = xs114
        self.consume_literal(')')
        _t543 = logic_pb2.Disjunction(args=args116)
        return _t543

    def parse_not(self) -> logic_pb2.Not:
        self.consume_literal('(')
        self.consume_literal('not')
        _t544 = self.parse_formula()
        arg117 = _t544
        self.consume_literal(')')
        _t545 = logic_pb2.Not(arg=arg117)
        return _t545

    def parse_ffi(self) -> logic_pb2.FFI:
        self.consume_literal('(')
        self.consume_literal('ffi')
        _t546 = self.parse_name()
        name118 = _t546
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('args', 1)):
            _t548 = self.parse_ffi_args()
            _t547 = _t548
        else:
            _t547 = None
        args119 = _t547
        if self.match_lookahead_literal('(', 0):
            _t550 = self.parse_terms()
            _t549 = _t550
        else:
            _t549 = None
        terms120 = _t549
        self.consume_literal(')')
        _t551 = logic_pb2.FFI(name=name118, args=(args119 if args119 is not None else []), terms=(terms120 if terms120 is not None else []))
        return _t551

    def parse_name(self) -> str:
        symbol121 = self.consume_terminal('COLON_SYMBOL')
        return symbol121

    def parse_ffi_args(self) -> list[logic_pb2.Abstraction]:
        self.consume_literal('(')
        self.consume_literal('args')
        xs122 = []
        cond123 = self.match_lookahead_literal('(', 0)
        while cond123:
            _t552 = self.parse_abstraction()
            xs122.append(_t552)
            cond123 = self.match_lookahead_literal('(', 0)
        value124 = xs122
        self.consume_literal(')')
        return value124

    def parse_atom(self) -> logic_pb2.Atom:
        self.consume_literal('(')
        self.consume_literal('atom')
        _t553 = self.parse_relation_id()
        name125 = _t553
        xs126 = []
        cond127 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond127:
            _t554 = self.parse_term()
            xs126.append(_t554)
            cond127 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms128 = xs126
        self.consume_literal(')')
        _t555 = logic_pb2.Atom(name=name125, terms=terms128)
        return _t555

    def parse_pragma(self) -> logic_pb2.Pragma:
        self.consume_literal('(')
        self.consume_literal('pragma')
        _t556 = self.parse_name()
        name129 = _t556
        xs130 = []
        cond131 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond131:
            _t557 = self.parse_term()
            xs130.append(_t557)
            cond131 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms132 = xs130
        self.consume_literal(')')
        _t558 = logic_pb2.Pragma(name=name129, terms=terms132)
        return _t558

    def parse_primitive(self) -> logic_pb2.Primitive:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('primitive', 1):
                _t560 = 9
            else:
                if self.match_lookahead_literal('>=', 1):
                    _t561 = 4
                else:
                    if self.match_lookahead_literal('>', 1):
                        _t562 = 3
                    else:
                        if self.match_lookahead_literal('=', 1):
                            _t563 = 0
                        else:
                            if self.match_lookahead_literal('<=', 1):
                                _t564 = 2
                            else:
                                if self.match_lookahead_literal('<', 1):
                                    _t569 = 1
                                else:
                                    if self.match_lookahead_literal('/', 1):
                                        _t570 = 8
                                    else:
                                        if self.match_lookahead_literal('-', 1):
                                            _t571 = 6
                                        else:
                                            if self.match_lookahead_literal('+', 1):
                                                _t572 = 5
                                            else:
                                                if self.match_lookahead_literal('*', 1):
                                                    _t573 = 7
                                                else:
                                                    _t573 = -1
                                                _t572 = _t573
                                            _t571 = _t572
                                        _t570 = _t571
                                    _t569 = _t570
                                _t564 = _t569
                            _t563 = _t564
                        _t562 = _t563
                    _t561 = _t562
                _t560 = _t561
            _t559 = _t560
        else:
            _t559 = -1
        prediction133 = _t559
        if prediction133 == 9:
            self.consume_literal('(')
            self.consume_literal('primitive')
            _t575 = self.parse_name()
            name143 = _t575
            xs144 = []
            cond145 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            while cond145:
                _t576 = self.parse_relterm()
                xs144.append(_t576)
                cond145 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            terms146 = xs144
            self.consume_literal(')')
            _t577 = logic_pb2.Primitive(name=name143, terms=terms146)
            _t574 = _t577
        else:
            if prediction133 == 8:
                _t579 = self.parse_divide()
                op142 = _t579
                _t578 = op142
            else:
                if prediction133 == 7:
                    _t581 = self.parse_multiply()
                    op141 = _t581
                    _t580 = op141
                else:
                    if prediction133 == 6:
                        _t583 = self.parse_minus()
                        op140 = _t583
                        _t582 = op140
                    else:
                        if prediction133 == 5:
                            _t585 = self.parse_add()
                            op139 = _t585
                            _t584 = op139
                        else:
                            if prediction133 == 4:
                                _t587 = self.parse_gt_eq()
                                op138 = _t587
                                _t586 = op138
                            else:
                                if prediction133 == 3:
                                    _t589 = self.parse_gt()
                                    op137 = _t589
                                    _t588 = op137
                                else:
                                    if prediction133 == 2:
                                        _t591 = self.parse_lt_eq()
                                        op136 = _t591
                                        _t590 = op136
                                    else:
                                        if prediction133 == 1:
                                            _t593 = self.parse_lt()
                                            op135 = _t593
                                            _t592 = op135
                                        else:
                                            if prediction133 == 0:
                                                _t595 = self.parse_eq()
                                                op134 = _t595
                                                _t594 = op134
                                            else:
                                                raise ParseError('Unexpected token in primitive' + f": {{self.lookahead(0)}}")
                                                _t594 = None
                                            _t592 = _t594
                                        _t590 = _t592
                                    _t588 = _t590
                                _t586 = _t588
                            _t584 = _t586
                        _t582 = _t584
                    _t580 = _t582
                _t578 = _t580
            _t574 = _t578
        return _t574

    def parse_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('=')
        _t596 = self.parse_term()
        left147 = _t596
        _t597 = self.parse_term()
        right148 = _t597
        self.consume_literal(')')
        _t598 = logic_pb2.RelTerm(term=left147)
        _t599 = logic_pb2.RelTerm(term=right148)
        _t600 = logic_pb2.Primitive(name='rel_primitive_eq', terms=[_t598, _t599])
        return _t600

    def parse_lt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<')
        _t601 = self.parse_term()
        left149 = _t601
        _t602 = self.parse_term()
        right150 = _t602
        self.consume_literal(')')
        _t603 = logic_pb2.RelTerm(term=left149)
        _t604 = logic_pb2.RelTerm(term=right150)
        _t605 = logic_pb2.Primitive(name='rel_primitive_lt', terms=[_t603, _t604])
        return _t605

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('<=')
        _t606 = self.parse_term()
        left151 = _t606
        _t607 = self.parse_term()
        right152 = _t607
        self.consume_literal(')')
        _t608 = logic_pb2.RelTerm(term=left151)
        _t609 = logic_pb2.RelTerm(term=right152)
        _t610 = logic_pb2.Primitive(name='rel_primitive_lt_eq', terms=[_t608, _t609])
        return _t610

    def parse_gt(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>')
        _t611 = self.parse_term()
        left153 = _t611
        _t612 = self.parse_term()
        right154 = _t612
        self.consume_literal(')')
        _t613 = logic_pb2.RelTerm(term=left153)
        _t614 = logic_pb2.RelTerm(term=right154)
        _t615 = logic_pb2.Primitive(name='rel_primitive_gt', terms=[_t613, _t614])
        return _t615

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('>=')
        _t616 = self.parse_term()
        left155 = _t616
        _t617 = self.parse_term()
        right156 = _t617
        self.consume_literal(')')
        _t618 = logic_pb2.RelTerm(term=left155)
        _t619 = logic_pb2.RelTerm(term=right156)
        _t620 = logic_pb2.Primitive(name='rel_primitive_gt_eq', terms=[_t618, _t619])
        return _t620

    def parse_add(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('+')
        _t621 = self.parse_term()
        left157 = _t621
        _t622 = self.parse_term()
        right158 = _t622
        _t623 = self.parse_term()
        result159 = _t623
        self.consume_literal(')')
        _t624 = logic_pb2.RelTerm(term=left157)
        _t625 = logic_pb2.RelTerm(term=right158)
        _t626 = logic_pb2.RelTerm(term=result159)
        _t627 = logic_pb2.Primitive(name='rel_primitive_add_monotype', terms=[_t624, _t625, _t626])
        return _t627

    def parse_minus(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('-')
        _t628 = self.parse_term()
        left160 = _t628
        _t629 = self.parse_term()
        right161 = _t629
        _t630 = self.parse_term()
        result162 = _t630
        self.consume_literal(')')
        _t631 = logic_pb2.RelTerm(term=left160)
        _t632 = logic_pb2.RelTerm(term=right161)
        _t633 = logic_pb2.RelTerm(term=result162)
        _t634 = logic_pb2.Primitive(name='rel_primitive_subtract_monotype', terms=[_t631, _t632, _t633])
        return _t634

    def parse_multiply(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('*')
        _t635 = self.parse_term()
        left163 = _t635
        _t636 = self.parse_term()
        right164 = _t636
        _t637 = self.parse_term()
        result165 = _t637
        self.consume_literal(')')
        _t638 = logic_pb2.RelTerm(term=left163)
        _t639 = logic_pb2.RelTerm(term=right164)
        _t640 = logic_pb2.RelTerm(term=result165)
        _t641 = logic_pb2.Primitive(name='rel_primitive_multiply_monotype', terms=[_t638, _t639, _t640])
        return _t641

    def parse_divide(self) -> logic_pb2.Primitive:
        self.consume_literal('(')
        self.consume_literal('/')
        _t642 = self.parse_term()
        left166 = _t642
        _t643 = self.parse_term()
        right167 = _t643
        _t644 = self.parse_term()
        result168 = _t644
        self.consume_literal(')')
        _t645 = logic_pb2.RelTerm(term=left166)
        _t646 = logic_pb2.RelTerm(term=right167)
        _t647 = logic_pb2.RelTerm(term=result168)
        _t648 = logic_pb2.Primitive(name='rel_primitive_divide_monotype', terms=[_t645, _t646, _t647])
        return _t648

    def parse_relterm(self) -> logic_pb2.RelTerm:
        if self.match_lookahead_terminal('UINT128', 0):
            _t2696 = 1
        else:
            if self.match_lookahead_terminal('SYMBOL', 0):
                _t3720 = 1
            else:
                if self.match_lookahead_terminal('STRING', 0):
                    _t4232 = 1
                else:
                    if self.match_lookahead_terminal('INT128', 0):
                        _t4488 = 1
                    else:
                        if self.match_lookahead_terminal('INT', 0):
                            _t4616 = 1
                        else:
                            if self.match_lookahead_terminal('FLOAT', 0):
                                _t4680 = 1
                            else:
                                if self.match_lookahead_terminal('DECIMAL', 0):
                                    _t4712 = 1
                                else:
                                    if self.match_lookahead_literal('true', 0):
                                        _t4728 = 1
                                    else:
                                        if self.match_lookahead_literal('missing', 0):
                                            _t4736 = 1
                                        else:
                                            if self.match_lookahead_literal('false', 0):
                                                _t4740 = 1
                                            else:
                                                if self.match_lookahead_literal('(', 0):
                                                    _t4742 = 1
                                                else:
                                                    if self.match_lookahead_literal('#', 0):
                                                        _t4743 = 0
                                                    else:
                                                        _t4743 = -1
                                                    _t4742 = _t4743
                                                _t4740 = _t4742
                                            _t4736 = _t4740
                                        _t4728 = _t4736
                                    _t4712 = _t4728
                                _t4680 = _t4712
                            _t4616 = _t4680
                        _t4488 = _t4616
                    _t4232 = _t4488
                _t3720 = _t4232
            _t2696 = _t3720
        prediction169 = _t2696
        if prediction169 == 1:
            _t4745 = self.parse_term()
            value171 = _t4745
            _t4746 = logic_pb2.RelTerm(term=value171)
            _t4744 = _t4746
        else:
            if prediction169 == 0:
                _t4748 = self.parse_specialized_value()
                value170 = _t4748
                _t4749 = logic_pb2.RelTerm(specialized_value=value170)
                _t4747 = _t4749
            else:
                raise ParseError('Unexpected token in relterm' + f": {{self.lookahead(0)}}")
                _t4747 = None
            _t4744 = _t4747
        return _t4744

    def parse_specialized_value(self) -> logic_pb2.Value:
        self.consume_literal('#')
        _t4750 = self.parse_value()
        value172 = _t4750
        return value172

    def parse_relatom(self) -> logic_pb2.RelAtom:
        self.consume_literal('(')
        self.consume_literal('relatom')
        _t4751 = self.parse_name()
        name173 = _t4751
        xs174 = []
        cond175 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond175:
            _t4752 = self.parse_relterm()
            xs174.append(_t4752)
            cond175 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms176 = xs174
        self.consume_literal(')')
        _t4753 = logic_pb2.RelAtom(name=name173, terms=terms176)
        return _t4753

    def parse_cast(self) -> logic_pb2.Cast:
        self.consume_literal('(')
        self.consume_literal('cast')
        _t4754 = self.parse_term()
        input177 = _t4754
        _t4755 = self.parse_term()
        result178 = _t4755
        self.consume_literal(')')
        _t4756 = logic_pb2.Cast(input=input177, result=result178)
        return _t4756

    def parse_attrs(self) -> list[logic_pb2.Attribute]:
        self.consume_literal('(')
        self.consume_literal('attrs')
        xs179 = []
        cond180 = self.match_lookahead_literal('(', 0)
        while cond180:
            _t4757 = self.parse_attribute()
            xs179.append(_t4757)
            cond180 = self.match_lookahead_literal('(', 0)
        value181 = xs179
        self.consume_literal(')')
        return value181

    def parse_attribute(self) -> logic_pb2.Attribute:
        self.consume_literal('(')
        self.consume_literal('attribute')
        _t4758 = self.parse_name()
        name182 = _t4758
        xs183 = []
        cond184 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        while cond184:
            _t4759 = self.parse_value()
            xs183.append(_t4759)
            cond184 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        args185 = xs183
        self.consume_literal(')')
        _t4760 = logic_pb2.Attribute(name=name182, args=args185)
        return _t4760

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        self.consume_literal('(')
        self.consume_literal('algorithm')
        xs186 = []
        cond187 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        while cond187:
            _t4761 = self.parse_relation_id()
            xs186.append(_t4761)
            cond187 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        global188 = xs186
        _t4762 = self.parse_script()
        body189 = _t4762
        self.consume_literal(')')
        _t4763 = logic_pb2.Algorithm(**{'global': global188}, body=body189)
        return _t4763

    def parse_script(self) -> logic_pb2.Script:
        self.consume_literal('(')
        self.consume_literal('script')
        xs190 = []
        cond191 = self.match_lookahead_literal('(', 0)
        while cond191:
            _t4764 = self.parse_construct()
            xs190.append(_t4764)
            cond191 = self.match_lookahead_literal('(', 0)
        constructs192 = xs190
        self.consume_literal(')')
        _t4765 = logic_pb2.Script(constructs=constructs192)
        return _t4765

    def parse_construct(self) -> logic_pb2.Construct:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t4774 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t4778 = 1
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t4780 = 1
                    else:
                        if self.match_lookahead_literal('loop', 1):
                            _t4781 = 0
                        else:
                            _t4781 = (self.match_lookahead_literal('break', 1) or (self.match_lookahead_literal('assign', 1) or -1))
                        _t4780 = _t4781
                    _t4778 = _t4780
                _t4774 = _t4778
            _t4766 = _t4774
        else:
            _t4766 = -1
        prediction193 = _t4766
        if prediction193 == 1:
            _t4783 = self.parse_instruction()
            value195 = _t4783
            _t4784 = logic_pb2.Construct(instruction=value195)
            _t4782 = _t4784
        else:
            if prediction193 == 0:
                _t4786 = self.parse_loop()
                value194 = _t4786
                _t4787 = logic_pb2.Construct(loop=value194)
                _t4785 = _t4787
            else:
                raise ParseError('Unexpected token in construct' + f": {{self.lookahead(0)}}")
                _t4785 = None
            _t4782 = _t4785
        return _t4782

    def parse_loop(self) -> logic_pb2.Loop:
        self.consume_literal('(')
        self.consume_literal('loop')
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('init', 1)):
            _t4789 = self.parse_loop_init()
            _t4788 = _t4789
        else:
            _t4788 = None
        init196 = _t4788
        _t4790 = self.parse_script()
        body197 = _t4790
        self.consume_literal(')')
        _t4791 = logic_pb2.Loop(init=(init196 if init196 is not None else []), body=body197)
        return _t4791

    def parse_loop_init(self) -> list[logic_pb2.Instruction]:
        self.consume_literal('(')
        self.consume_literal('init')
        xs198 = []
        cond199 = self.match_lookahead_literal('(', 0)
        while cond199:
            _t4792 = self.parse_instruction()
            xs198.append(_t4792)
            cond199 = self.match_lookahead_literal('(', 0)
        value200 = xs198
        self.consume_literal(')')
        return value200

    def parse_instruction(self) -> logic_pb2.Instruction:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('upsert', 1):
                _t4798 = 1
            else:
                if self.match_lookahead_literal('monus', 1):
                    _t4799 = 4
                else:
                    if self.match_lookahead_literal('monoid', 1):
                        _t4800 = 3
                    else:
                        if self.match_lookahead_literal('break', 1):
                            _t4801 = 2
                        else:
                            if self.match_lookahead_literal('assign', 1):
                                _t4802 = 0
                            else:
                                _t4802 = -1
                            _t4801 = _t4802
                        _t4800 = _t4801
                    _t4799 = _t4800
                _t4798 = _t4799
            _t4793 = _t4798
        else:
            _t4793 = -1
        prediction201 = _t4793
        if prediction201 == 4:
            _t4804 = self.parse_monus_def()
            value206 = _t4804
            _t4805 = logic_pb2.Instruction(monus_def=value206)
            _t4803 = _t4805
        else:
            if prediction201 == 3:
                _t4807 = self.parse_monoid_def()
                value205 = _t4807
                _t4808 = logic_pb2.Instruction(monoid_def=value205)
                _t4806 = _t4808
            else:
                if prediction201 == 2:
                    _t4810 = self.parse_break()
                    value204 = _t4810
                    _t4811 = logic_pb2.Instruction(**{'break': value204})
                    _t4809 = _t4811
                else:
                    if prediction201 == 1:
                        _t4813 = self.parse_upsert()
                        value203 = _t4813
                        _t4814 = logic_pb2.Instruction(upsert=value203)
                        _t4812 = _t4814
                    else:
                        if prediction201 == 0:
                            _t4816 = self.parse_assign()
                            value202 = _t4816
                            _t4817 = logic_pb2.Instruction(assign=value202)
                            _t4815 = _t4817
                        else:
                            raise ParseError('Unexpected token in instruction' + f": {{self.lookahead(0)}}")
                            _t4815 = None
                        _t4812 = _t4815
                    _t4809 = _t4812
                _t4806 = _t4809
            _t4803 = _t4806
        return _t4803

    def parse_assign(self) -> logic_pb2.Assign:
        self.consume_literal('(')
        self.consume_literal('assign')
        _t4818 = self.parse_relation_id()
        name207 = _t4818
        _t4819 = self.parse_abstraction()
        body208 = _t4819
        if self.match_lookahead_literal('(', 0):
            _t4821 = self.parse_attrs()
            _t4820 = _t4821
        else:
            _t4820 = None
        attrs209 = _t4820
        self.consume_literal(')')
        _t4822 = logic_pb2.Assign(name=name207, body=body208, attrs=(attrs209 if attrs209 is not None else []))
        return _t4822

    def parse_upsert(self) -> logic_pb2.Upsert:
        self.consume_literal('(')
        self.consume_literal('upsert')
        _t4823 = self.parse_relation_id()
        name210 = _t4823
        _t4824 = self.parse_abstraction_with_arity()
        body211 = _t4824
        if self.match_lookahead_literal('(', 0):
            _t4826 = self.parse_attrs()
            _t4825 = _t4826
        else:
            _t4825 = None
        attrs212 = _t4825
        self.consume_literal(')')
        _t4827 = logic_pb2.Upsert(name=name210, body=body211[0], attrs=(attrs212 if attrs212 is not None else []), value_arity=body211[1])
        return _t4827

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal('(')
        _t4828 = self.parse_bindings()
        bindings213 = _t4828
        _t4829 = self.parse_formula()
        formula214 = _t4829
        self.consume_literal(')')
        _t4830 = logic_pb2.Abstraction(vars=(bindings213[0] + (bindings213[1] if bindings213[1] is not None else [])), value=formula214)
        return (_t4830, len(bindings213[1]),)

    def parse_break(self) -> logic_pb2.Break:
        self.consume_literal('(')
        self.consume_literal('break')
        _t4831 = self.parse_relation_id()
        name215 = _t4831
        _t4832 = self.parse_abstraction()
        body216 = _t4832
        if self.match_lookahead_literal('(', 0):
            _t4834 = self.parse_attrs()
            _t4833 = _t4834
        else:
            _t4833 = None
        attrs217 = _t4833
        self.consume_literal(')')
        _t4835 = logic_pb2.Break(name=name215, body=body216, attrs=(attrs217 if attrs217 is not None else []))
        return _t4835

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        self.consume_literal('(')
        self.consume_literal('monoid')
        _t4836 = self.parse_monoid()
        monoid218 = _t4836
        _t4837 = self.parse_relation_id()
        name219 = _t4837
        _t4838 = self.parse_abstraction_with_arity()
        body220 = _t4838
        if self.match_lookahead_literal('(', 0):
            _t4840 = self.parse_attrs()
            _t4839 = _t4840
        else:
            _t4839 = None
        attrs221 = _t4839
        self.consume_literal(')')
        _t4841 = logic_pb2.MonoidDef(monoid=monoid218, name=name219, body=body220[0], attrs=(attrs221 if attrs221 is not None else []), value_arity=body220[1])
        return _t4841

    def parse_monoid(self) -> logic_pb2.Monoid:
        _t4842 = self.parse_type()
        type222 = _t4842
        self.consume_literal('::')
        _t4843 = self.parse_monoid_op()
        op223 = _t4843
        _t4844 = op223(type222)
        return _t4844

    def parse_monoid_op(self) -> Callable[[logic_pb2.Type], logic_pb2.Monoid]:
        if self.match_lookahead_literal('SUM', 0):
            _t4845 = 3
        else:
            if self.match_lookahead_literal('OR', 0):
                _t4846 = 0
            else:
                if self.match_lookahead_literal('MIN', 0):
                    _t4848 = 1
                else:
                    if self.match_lookahead_literal('MAX', 0):
                        _t4849 = 2
                    else:
                        _t4849 = -1
                    _t4848 = _t4849
                _t4846 = _t4848
            _t4845 = _t4846
        prediction224 = _t4845
        if prediction224 == 3:
            self.consume_literal('SUM')
            def _t4851(type):
                _t4852 = logic_pb2.SumMonoid(type=type)
                _t4853 = logic_pb2.Monoid(sum_monoid=_t4852)
                return _t4853
            _t4850 = _t4851
        else:
            if prediction224 == 2:
                self.consume_literal('MAX')
                def _t4855(type):
                    _t4856 = logic_pb2.MaxMonoid(type=type)
                    _t4857 = logic_pb2.Monoid(max_monoid=_t4856)
                    return _t4857
                _t4854 = _t4855
            else:
                if prediction224 == 1:
                    self.consume_literal('MIN')
                    def _t4859(type):
                        _t4860 = logic_pb2.MinMonoid(type=type)
                        _t4861 = logic_pb2.Monoid(min_monoid=_t4860)
                        return _t4861
                    _t4858 = _t4859
                else:
                    if prediction224 == 0:
                        self.consume_literal('OR')
                        def _t4863(type):
                            _t4864 = logic_pb2.OrMonoid()
                            _t4865 = logic_pb2.Monoid(or_monoid=_t4864)
                            return _t4865
                        _t4862 = _t4863
                    else:
                        raise ParseError('Unexpected token in monoid_op' + f": {{self.lookahead(0)}}")
                        _t4862 = None
                    _t4858 = _t4862
                _t4854 = _t4858
            _t4850 = _t4854
        return _t4850

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        self.consume_literal('(')
        self.consume_literal('monus')
        _t4866 = self.parse_monoid()
        monoid225 = _t4866
        _t4867 = self.parse_relation_id()
        name226 = _t4867
        _t4868 = self.parse_abstraction_with_arity()
        body227 = _t4868
        if self.match_lookahead_literal('(', 0):
            _t4870 = self.parse_attrs()
            _t4869 = _t4870
        else:
            _t4869 = None
        attrs228 = _t4869
        self.consume_literal(')')
        _t4871 = logic_pb2.MonusDef(monoid=monoid225, name=name226, body=body227[0], attrs=(attrs228 if attrs228 is not None else []), value_arity=body227[1])
        return _t4871

    def parse_constraint(self) -> logic_pb2.Constraint:
        _t4872 = self.parse_functional_dependency()
        value229 = _t4872
        _t4873 = logic_pb2.Constraint(functional_dependency=value229)
        return _t4873

    def parse_functional_dependency(self) -> logic_pb2.FunctionalDependency:
        self.consume_literal('(')
        self.consume_literal('functional_dependency')
        _t4874 = self.parse_abstraction()
        guard230 = _t4874
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('keys', 1)):
            _t4876 = self.parse_functional_dependency_keys()
            _t4875 = _t4876
        else:
            _t4875 = None
        keys231 = _t4875
        if self.match_lookahead_literal('(', 0):
            _t4878 = self.parse_functional_dependency_values()
            _t4877 = _t4878
        else:
            _t4877 = None
        values232 = _t4877
        self.consume_literal(')')
        _t4879 = logic_pb2.FunctionalDependency(guard=guard230, keys=(keys231 if keys231 is not None else []), values=(values232 if values232 is not None else []))
        return _t4879

    def parse_functional_dependency_keys(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('keys')
        xs233 = []
        cond234 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond234:
            _t4880 = self.parse_var()
            xs233.append(_t4880)
            cond234 = self.match_lookahead_terminal('SYMBOL', 0)
        value235 = xs233
        self.consume_literal(')')
        return value235

    def parse_functional_dependency_values(self) -> list[logic_pb2.Var]:
        self.consume_literal('(')
        self.consume_literal('values')
        xs236 = []
        cond237 = self.match_lookahead_terminal('SYMBOL', 0)
        while cond237:
            _t4881 = self.parse_var()
            xs236.append(_t4881)
            cond237 = self.match_lookahead_terminal('SYMBOL', 0)
        value238 = xs236
        self.consume_literal(')')
        return value238

    def parse_undefine(self) -> transactions_pb2.Undefine:
        self.consume_literal('(')
        self.consume_literal('undefine')
        _t4882 = self.parse_fragment_id()
        fragment_id239 = _t4882
        self.consume_literal(')')
        _t4883 = transactions_pb2.Undefine(fragment_id=fragment_id239)
        return _t4883

    def parse_context(self) -> transactions_pb2.Context:
        self.consume_literal('(')
        self.consume_literal('context')
        xs240 = []
        cond241 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        while cond241:
            _t4884 = self.parse_relation_id()
            xs240.append(_t4884)
            cond241 = (self.match_lookahead_terminal('COLON_SYMBOL', 0) or self.match_lookahead_terminal('INT', 0))
        relations242 = xs240
        self.consume_literal(')')
        _t4885 = transactions_pb2.Context(relations=relations242)
        return _t4885

    def parse_epoch_reads(self) -> list[transactions_pb2.Read]:
        self.consume_literal('(')
        self.consume_literal('reads')
        xs243 = []
        cond244 = self.match_lookahead_literal('(', 0)
        while cond244:
            _t4886 = self.parse_read()
            xs243.append(_t4886)
            cond244 = self.match_lookahead_literal('(', 0)
        value245 = xs243
        self.consume_literal(')')
        return value245

    def parse_read(self) -> transactions_pb2.Read:
        if self.match_lookahead_literal('(', 0):
            if self.match_lookahead_literal('what_if', 1):
                _t4888 = 2
            else:
                if self.match_lookahead_literal('output', 1):
                    _t4892 = 1
                else:
                    if self.match_lookahead_literal('export', 1):
                        _t4893 = 4
                    else:
                        if self.match_lookahead_literal('demand', 1):
                            _t4894 = 0
                        else:
                            if self.match_lookahead_literal('abort', 1):
                                _t4895 = 3
                            else:
                                _t4895 = -1
                            _t4894 = _t4895
                        _t4893 = _t4894
                    _t4892 = _t4893
                _t4888 = _t4892
            _t4887 = _t4888
        else:
            _t4887 = -1
        prediction246 = _t4887
        if prediction246 == 4:
            _t4897 = self.parse_export()
            value251 = _t4897
            _t4898 = transactions_pb2.Read(export=value251)
            _t4896 = _t4898
        else:
            if prediction246 == 3:
                _t4900 = self.parse_abort()
                value250 = _t4900
                _t4901 = transactions_pb2.Read(abort=value250)
                _t4899 = _t4901
            else:
                if prediction246 == 2:
                    _t4903 = self.parse_what_if()
                    value249 = _t4903
                    _t4904 = transactions_pb2.Read(what_if=value249)
                    _t4902 = _t4904
                else:
                    if prediction246 == 1:
                        _t4906 = self.parse_output()
                        value248 = _t4906
                        _t4907 = transactions_pb2.Read(output=value248)
                        _t4905 = _t4907
                    else:
                        if prediction246 == 0:
                            _t4909 = self.parse_demand()
                            value247 = _t4909
                            _t4910 = transactions_pb2.Read(demand=value247)
                            _t4908 = _t4910
                        else:
                            raise ParseError('Unexpected token in read' + f": {{self.lookahead(0)}}")
                            _t4908 = None
                        _t4905 = _t4908
                    _t4902 = _t4905
                _t4899 = _t4902
            _t4896 = _t4899
        return _t4896

    def parse_demand(self) -> transactions_pb2.Demand:
        self.consume_literal('(')
        self.consume_literal('demand')
        _t4911 = self.parse_relation_id()
        relation_id252 = _t4911
        self.consume_literal(')')
        _t4912 = transactions_pb2.Demand(relation_id=relation_id252)
        return _t4912

    def parse_output(self) -> transactions_pb2.Output:
        self.consume_literal('(')
        self.consume_literal('output')
        if self.match_lookahead_terminal('COLON_SYMBOL', 0):
            _t4914 = self.parse_name()
            _t4913 = _t4914
        else:
            _t4913 = None
        name253 = _t4913
        _t4915 = self.parse_relation_id()
        relation_id254 = _t4915
        self.consume_literal(')')
        _t4916 = transactions_pb2.Output(name=name253, relation_id=relation_id254)
        return _t4916

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        self.consume_literal('(')
        self.consume_literal('what_if')
        branch255 = self.consume_terminal('STRING')
        _t4917 = self.parse_epoch()
        epoch256 = _t4917
        self.consume_literal(')')
        _t4918 = transactions_pb2.WhatIf(branch=branch255, epoch=epoch256)
        return _t4918

    def parse_abort(self) -> transactions_pb2.Abort:
        self.consume_literal('(')
        self.consume_literal('abort')
        if self.match_lookahead_terminal('COLON_SYMBOL', 0):
            _t4920 = self.parse_name()
            _t4919 = _t4920
        else:
            _t4919 = None
        name257 = _t4919
        _t4921 = self.parse_relation_id()
        relation_id258 = _t4921
        self.consume_literal(')')
        _t4922 = transactions_pb2.Abort(name=name257, relation_id=relation_id258)
        return _t4922

    def parse_export(self) -> transactions_pb2.Export:
        self.consume_literal('(')
        self.consume_literal('export')
        _t4923 = self.parse_export_csv_config()
        config259 = _t4923
        self.consume_literal(')')
        _t4924 = transactions_pb2.Export(csv_config=config259)
        return _t4924

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        self.consume_literal('(')
        self.consume_literal('export_csv_config')
        self.consume_literal('(')
        self.consume_literal('path')
        path260 = self.consume_terminal('STRING')
        self.consume_literal(')')
        _t4925 = self.parse_export_csvcolumns()
        columns261 = _t4925
        _t4926 = self.parse_config_dict()
        config262 = _t4926
        self.consume_literal(')')
        return self.export_csv_config(path260, columns261, config262)

    def parse_export_csvcolumns(self) -> list[transactions_pb2.ExportCSVColumn]:
        self.consume_literal('(')
        self.consume_literal('columns')
        xs263 = []
        cond264 = self.match_lookahead_literal('(', 0)
        while cond264:
            _t4927 = self.parse_export_csvcolumn()
            xs263.append(_t4927)
            cond264 = self.match_lookahead_literal('(', 0)
        columns265 = xs263
        self.consume_literal(')')
        return columns265

    def parse_export_csvcolumn(self) -> transactions_pb2.ExportCSVColumn:
        self.consume_literal('(')
        self.consume_literal('column')
        name266 = self.consume_terminal('STRING')
        _t4928 = self.parse_relation_id()
        relation_id267 = _t4928
        self.consume_literal(')')
        _t4929 = transactions_pb2.ExportCSVColumn(column_name=name266, column_data=relation_id267)
        return _t4929


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
