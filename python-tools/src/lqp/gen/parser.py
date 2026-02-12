"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.


Command: python -m meta.cli ../proto/relationalai/lqp/v1/fragments.proto ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto --grammar src/meta/grammar.y --parser python
"""

import ast
import bisect
import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple, Callable
from decimal import Decimal

from lqp.proto.v1 import logic_pb2, fragments_pb2, transactions_pb2


class ParseError(Exception):
    """Parse error exception."""
    pass


@dataclass(frozen=True)
class Location:
    """Source location with 1-based line and column."""
    line: int
    column: int
    offset: int


@dataclass(frozen=True)
class Span:
    """Source span from start to end location."""
    start: Location
    end: Location


class Token:
    """Token representation."""
    def __init__(self, type: str, value: str, start_pos: int, end_pos: int):
        self.type = type
        self.value = value
        self.start_pos = start_pos
        self.end_pos = end_pos

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value!r}, {self.start_pos})"


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
            ('LITERAL', re.compile(r':'), lambda x: x),
            ('LITERAL', re.compile(r'<'), lambda x: x),
            ('LITERAL', re.compile(r'='), lambda x: x),
            ('LITERAL', re.compile(r'>'), lambda x: x),
            ('LITERAL', re.compile(r'\['), lambda x: x),
            ('LITERAL', re.compile(r'\]'), lambda x: x),
            ('LITERAL', re.compile(r'\{'), lambda x: x),
            ('LITERAL', re.compile(r'\|'), lambda x: x),
            ('LITERAL', re.compile(r'\}'), lambda x: x),
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
            self.tokens.append(Token(token_type, action(value), self.pos, end_pos))
            self.pos = end_pos

        self.tokens.append(Token('$', '', self.pos, self.pos))

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
        return ast.literal_eval(s)

    @staticmethod
    def scan_int(n: str) -> int:
        """Parse INT token."""
        val = int(n)
        if val < -(1 << 63) or val >= (1 << 63):
            raise ParseError(f'Integer literal out of 64-bit range: {n}')
        return val

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
        if uint128_val < 0 or uint128_val >= (1 << 128):
            raise ParseError(f'UInt128 literal out of range: {u}')
        low = uint128_val & 0xFFFFFFFFFFFFFFFF
        high = (uint128_val >> 64) & 0xFFFFFFFFFFFFFFFF
        return logic_pb2.UInt128Value(low=low, high=high)

    @staticmethod
    def scan_int128(u: str) -> Any:
        """Parse INT128 token."""
        u = u[:-4]  # Remove the 'i128' suffix
        int128_val = int(u)
        if int128_val < -(1 << 127) or int128_val >= (1 << 127):
            raise ParseError(f'Int128 literal out of range: {u}')
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


def _compute_line_starts(text: str) -> List[int]:
    """Compute byte offsets where each line begins."""
    starts = [0]
    for i, ch in enumerate(text):
        if ch == '\n':
            starts.append(i + 1)
    return starts


class Parser:
    """LL(k) recursive-descent parser with backtracking."""
    def __init__(self, tokens: List[Token], input_str: str):
        self.tokens = tokens
        self.pos = 0
        self.id_to_debuginfo = {}
        self._current_fragment_id: bytes | None = None
        self._relation_id_to_name = {}
        self.provenance: Dict[Tuple[int, ...], Span] = {}
        self._path: List[int] = []
        self._input_str = input_str
        self._line_starts = _compute_line_starts(input_str)

    def lookahead(self, k: int = 0) -> Token:
        """Get lookahead token at offset k."""
        idx = self.pos + k
        return self.tokens[idx] if idx < len(self.tokens) else Token('$', '', -1, -1)

    def consume_literal(self, expected: str) -> None:
        """Consume a literal token."""
        if not self.match_lookahead_literal(expected, 0):
            token = self.lookahead(0)
            raise ParseError(f'Expected literal {expected!r} but got {token.type}=`{token.value!r}` at position {token.start_pos}')
        self.pos += 1

    def consume_terminal(self, expected: str) -> Any:
        """Consume a terminal token and return parsed value."""
        if not self.match_lookahead_terminal(expected, 0):
            token = self.lookahead(0)
            raise ParseError(f'Expected terminal {expected} but got {token.type}=`{token.value!r}` at position {token.start_pos}')
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

    def _push_path(self, n: int) -> None:
        self._path.append(n)

    def _pop_path(self) -> None:
        self._path.pop()

    def _span_start(self) -> int:
        return self.tokens[self.pos].start_pos

    def _record_span(self, start_offset: int) -> None:
        end_offset = self.tokens[self.pos - 1].end_pos
        span = Span(self._make_location(start_offset), self._make_location(end_offset))
        self.provenance[tuple(self._path)] = span

    def _make_location(self, offset: int) -> Location:
        line = bisect.bisect_right(self._line_starts, offset)
        column = offset - self._line_starts[line - 1] + 1
        return Location(line, column, offset)

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

    def relation_id_to_string(self, msg) -> str:
        """Stub: only used in pretty printer."""
        raise NotImplementedError("relation_id_to_string is only available in PrettyPrinter")

    def relation_id_to_uint128(self, msg):
        """Stub: only used in pretty printer."""
        raise NotImplementedError("relation_id_to_uint128 is only available in PrettyPrinter")

    # --- Helper functions ---

    def _extract_value_int32(self, value: Optional[logic_pb2.Value], default: int) -> int:
        
        if value is not None:
            assert value is not None
            _t1211 = value.HasField('int_value')
        else:
            _t1211 = False
        if _t1211:
            assert value is not None
            return int(value.int_value)
        return int(default)

    def _extract_value_int64(self, value: Optional[logic_pb2.Value], default: int) -> int:
        
        if value is not None:
            assert value is not None
            _t1212 = value.HasField('int_value')
        else:
            _t1212 = False
        if _t1212:
            assert value is not None
            return value.int_value
        return default

    def _extract_value_float64(self, value: Optional[logic_pb2.Value], default: float) -> float:
        
        if value is not None:
            assert value is not None
            _t1213 = value.HasField('float_value')
        else:
            _t1213 = False
        if _t1213:
            assert value is not None
            return value.float_value
        return default

    def _extract_value_string(self, value: Optional[logic_pb2.Value], default: str) -> str:
        
        if value is not None:
            assert value is not None
            _t1214 = value.HasField('string_value')
        else:
            _t1214 = False
        if _t1214:
            assert value is not None
            return value.string_value
        return default

    def _extract_value_boolean(self, value: Optional[logic_pb2.Value], default: bool) -> bool:
        
        if value is not None:
            assert value is not None
            _t1215 = value.HasField('boolean_value')
        else:
            _t1215 = False
        if _t1215:
            assert value is not None
            return value.boolean_value
        return default

    def _extract_value_bytes(self, value: Optional[logic_pb2.Value], default: bytes) -> bytes:
        
        if value is not None:
            assert value is not None
            _t1216 = value.HasField('string_value')
        else:
            _t1216 = False
        if _t1216:
            assert value is not None
            return value.string_value.encode()
        return default

    def _extract_value_uint128(self, value: Optional[logic_pb2.Value], default: logic_pb2.UInt128Value) -> logic_pb2.UInt128Value:
        
        if value is not None:
            assert value is not None
            _t1217 = value.HasField('uint128_value')
        else:
            _t1217 = False
        if _t1217:
            assert value is not None
            return value.uint128_value
        return default

    def _extract_value_string_list(self, value: Optional[logic_pb2.Value], default: Sequence[str]) -> Sequence[str]:
        
        if value is not None:
            assert value is not None
            _t1218 = value.HasField('string_value')
        else:
            _t1218 = False
        if _t1218:
            assert value is not None
            return [value.string_value]
        return default

    def _try_extract_value_int64(self, value: Optional[logic_pb2.Value]) -> Optional[int]:
        
        if value is not None:
            assert value is not None
            _t1219 = value.HasField('int_value')
        else:
            _t1219 = False
        if _t1219:
            assert value is not None
            return value.int_value
        return None

    def _try_extract_value_float64(self, value: Optional[logic_pb2.Value]) -> Optional[float]:
        
        if value is not None:
            assert value is not None
            _t1220 = value.HasField('float_value')
        else:
            _t1220 = False
        if _t1220:
            assert value is not None
            return value.float_value
        return None

    def _try_extract_value_string(self, value: Optional[logic_pb2.Value]) -> Optional[str]:
        
        if value is not None:
            assert value is not None
            _t1221 = value.HasField('string_value')
        else:
            _t1221 = False
        if _t1221:
            assert value is not None
            return value.string_value
        return None

    def _try_extract_value_bytes(self, value: Optional[logic_pb2.Value]) -> Optional[bytes]:
        
        if value is not None:
            assert value is not None
            _t1222 = value.HasField('string_value')
        else:
            _t1222 = False
        if _t1222:
            assert value is not None
            return value.string_value.encode()
        return None

    def _try_extract_value_uint128(self, value: Optional[logic_pb2.Value]) -> Optional[logic_pb2.UInt128Value]:
        
        if value is not None:
            assert value is not None
            _t1223 = value.HasField('uint128_value')
        else:
            _t1223 = False
        if _t1223:
            assert value is not None
            return value.uint128_value
        return None

    def _try_extract_value_string_list(self, value: Optional[logic_pb2.Value]) -> Optional[Sequence[str]]:
        
        if value is not None:
            assert value is not None
            _t1224 = value.HasField('string_value')
        else:
            _t1224 = False
        if _t1224:
            assert value is not None
            return [value.string_value]
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1225 = self._extract_value_int32(config.get('csv_header_row'), 1)
        header_row = _t1225
        _t1226 = self._extract_value_int64(config.get('csv_skip'), 0)
        skip = _t1226
        _t1227 = self._extract_value_string(config.get('csv_new_line'), '')
        new_line = _t1227
        _t1228 = self._extract_value_string(config.get('csv_delimiter'), ',')
        delimiter = _t1228
        _t1229 = self._extract_value_string(config.get('csv_quotechar'), '"')
        quotechar = _t1229
        _t1230 = self._extract_value_string(config.get('csv_escapechar'), '"')
        escapechar = _t1230
        _t1231 = self._extract_value_string(config.get('csv_comment'), '')
        comment = _t1231
        _t1232 = self._extract_value_string_list(config.get('csv_missing_strings'), [])
        missing_strings = _t1232
        _t1233 = self._extract_value_string(config.get('csv_decimal_separator'), '.')
        decimal_separator = _t1233
        _t1234 = self._extract_value_string(config.get('csv_encoding'), 'utf-8')
        encoding = _t1234
        _t1235 = self._extract_value_string(config.get('csv_compression'), 'auto')
        compression = _t1235
        _t1236 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t1236

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1237 = self._try_extract_value_float64(config.get('betree_config_epsilon'))
        epsilon = _t1237
        _t1238 = self._try_extract_value_int64(config.get('betree_config_max_pivots'))
        max_pivots = _t1238
        _t1239 = self._try_extract_value_int64(config.get('betree_config_max_deltas'))
        max_deltas = _t1239
        _t1240 = self._try_extract_value_int64(config.get('betree_config_max_leaf'))
        max_leaf = _t1240
        _t1241 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1241
        _t1242 = self._try_extract_value_uint128(config.get('betree_locator_root_pageid'))
        root_pageid = _t1242
        _t1243 = self._try_extract_value_bytes(config.get('betree_locator_inline_data'))
        inline_data = _t1243
        _t1244 = self._try_extract_value_int64(config.get('betree_locator_element_count'))
        element_count = _t1244
        _t1245 = self._try_extract_value_int64(config.get('betree_locator_tree_height'))
        tree_height = _t1245
        _t1246 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1246
        _t1247 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1247

    def default_configure(self) -> transactions_pb2.Configure:
        _t1248 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1248
        _t1249 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1249

    def construct_configure(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.Configure:
        config = dict(config_dict)
        maintenance_level_val = config.get('ivm.maintenance_level')
        maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
        if (maintenance_level_val is not None and maintenance_level_val.HasField('string_value')):
            if maintenance_level_val.string_value == 'off':
                maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
            else:
                if maintenance_level_val.string_value == 'auto':
                    maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
                else:
                    if maintenance_level_val.string_value == 'all':
                        maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
                    else:
                        maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
        _t1250 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1250
        _t1251 = self._extract_value_int64(config.get('semantics_version'), 0)
        semantics_version = _t1251
        _t1252 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1252

    def export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1253 = self._extract_value_int64(config.get('partition_size'), 0)
        partition_size = _t1253
        _t1254 = self._extract_value_string(config.get('compression'), '')
        compression = _t1254
        _t1255 = self._extract_value_boolean(config.get('syntax_header_row'), True)
        syntax_header_row = _t1255
        _t1256 = self._extract_value_string(config.get('syntax_missing_string'), '')
        syntax_missing_string = _t1256
        _t1257 = self._extract_value_string(config.get('syntax_delim'), ',')
        syntax_delim = _t1257
        _t1258 = self._extract_value_string(config.get('syntax_quotechar'), '"')
        syntax_quotechar = _t1258
        _t1259 = self._extract_value_string(config.get('syntax_escapechar'), '\\')
        syntax_escapechar = _t1259
        _t1260 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1260

    def _make_value_int32(self, v: int) -> logic_pb2.Value:
        _t1261 = logic_pb2.Value(int_value=int(v))
        return _t1261

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1262 = logic_pb2.Value(int_value=v)
        return _t1262

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1263 = logic_pb2.Value(float_value=v)
        return _t1263

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1264 = logic_pb2.Value(string_value=v)
        return _t1264

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1265 = logic_pb2.Value(boolean_value=v)
        return _t1265

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1266 = logic_pb2.Value(uint128_value=v)
        return _t1266

    def is_default_configure(self, cfg: transactions_pb2.Configure) -> bool:
        if cfg.semantics_version != 0:
            return False
        if cfg.ivm_config.level != transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
            return False
        return True

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1268 = self._make_value_string('auto')
            result.append(('ivm.maintenance_level', _t1268,))
            _t1267 = None
        else:
            
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1270 = self._make_value_string('all')
                result.append(('ivm.maintenance_level', _t1270,))
                _t1269 = None
            else:
                
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1272 = self._make_value_string('off')
                    result.append(('ivm.maintenance_level', _t1272,))
                    _t1271 = None
                else:
                    _t1271 = None
                _t1269 = _t1271
            _t1267 = _t1269
        _t1273 = self._make_value_int64(msg.semantics_version)
        result.append(('semantics_version', _t1273,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1274 = self._make_value_int32(msg.header_row)
        result.append(('csv_header_row', _t1274,))
        _t1275 = self._make_value_int64(msg.skip)
        result.append(('csv_skip', _t1275,))
        
        if msg.new_line != '':
            _t1277 = self._make_value_string(msg.new_line)
            result.append(('csv_new_line', _t1277,))
            _t1276 = None
        else:
            _t1276 = None
        _t1278 = self._make_value_string(msg.delimiter)
        result.append(('csv_delimiter', _t1278,))
        _t1279 = self._make_value_string(msg.quotechar)
        result.append(('csv_quotechar', _t1279,))
        _t1280 = self._make_value_string(msg.escapechar)
        result.append(('csv_escapechar', _t1280,))
        
        if msg.comment != '':
            _t1282 = self._make_value_string(msg.comment)
            result.append(('csv_comment', _t1282,))
            _t1281 = None
        else:
            _t1281 = None
        for missing_string in msg.missing_strings:
            _t1283 = self._make_value_string(missing_string)
            result.append(('csv_missing_strings', _t1283,))
        _t1284 = self._make_value_string(msg.decimal_separator)
        result.append(('csv_decimal_separator', _t1284,))
        _t1285 = self._make_value_string(msg.encoding)
        result.append(('csv_encoding', _t1285,))
        _t1286 = self._make_value_string(msg.compression)
        result.append(('csv_compression', _t1286,))
        return sorted(result)

    def _maybe_push_float64(self, result: list[tuple[str, logic_pb2.Value]], key: str, val: Optional[float]) -> None:
        
        if val is not None:
            assert val is not None
            _t1288 = self._make_value_float64(val)
            result.append((key, _t1288,))
            _t1287 = None
        else:
            _t1287 = None
        return None

    def _maybe_push_int64(self, result: list[tuple[str, logic_pb2.Value]], key: str, val: Optional[int]) -> None:
        
        if val is not None:
            assert val is not None
            _t1290 = self._make_value_int64(val)
            result.append((key, _t1290,))
            _t1289 = None
        else:
            _t1289 = None
        return None

    def _maybe_push_uint128(self, result: list[tuple[str, logic_pb2.Value]], key: str, val: Optional[logic_pb2.UInt128Value]) -> None:
        
        if val is not None:
            assert val is not None
            _t1292 = self._make_value_uint128(val)
            result.append((key, _t1292,))
            _t1291 = None
        else:
            _t1291 = None
        return None

    def _maybe_push_bytes_as_string(self, result: list[tuple[str, logic_pb2.Value]], key: str, val: Optional[bytes]) -> None:
        
        if val is not None:
            assert val is not None
            _t1294 = self._make_value_string(val.decode('utf-8'))
            result.append((key, _t1294,))
            _t1293 = None
        else:
            _t1293 = None
        return None

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1295 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(('betree_config_epsilon', _t1295,))
        _t1296 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(('betree_config_max_pivots', _t1296,))
        _t1297 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(('betree_config_max_deltas', _t1297,))
        _t1298 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(('betree_config_max_leaf', _t1298,))
        
        if msg.relation_locator.HasField('root_pageid'):
            _t1300 = self._maybe_push_uint128(result, 'betree_locator_root_pageid', msg.relation_locator.root_pageid)
            _t1299 = _t1300
        else:
            _t1299 = None
        
        if msg.relation_locator.HasField('inline_data'):
            _t1302 = self._maybe_push_bytes_as_string(result, 'betree_locator_inline_data', msg.relation_locator.inline_data)
            _t1301 = _t1302
        else:
            _t1301 = None
        _t1303 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(('betree_locator_element_count', _t1303,))
        _t1304 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(('betree_locator_tree_height', _t1304,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1306 = self._make_value_int64(msg.partition_size)
            result.append(('partition_size', _t1306,))
            _t1305 = None
        else:
            _t1305 = None
        
        if msg.compression is not None:
            assert msg.compression is not None
            _t1308 = self._make_value_string(msg.compression)
            result.append(('compression', _t1308,))
            _t1307 = None
        else:
            _t1307 = None
        
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1310 = self._make_value_boolean(msg.syntax_header_row)
            result.append(('syntax_header_row', _t1310,))
            _t1309 = None
        else:
            _t1309 = None
        
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1312 = self._make_value_string(msg.syntax_missing_string)
            result.append(('syntax_missing_string', _t1312,))
            _t1311 = None
        else:
            _t1311 = None
        
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1314 = self._make_value_string(msg.syntax_delim)
            result.append(('syntax_delim', _t1314,))
            _t1313 = None
        else:
            _t1313 = None
        
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1316 = self._make_value_string(msg.syntax_quotechar)
            result.append(('syntax_quotechar', _t1316,))
            _t1315 = None
        else:
            _t1315 = None
        
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1318 = self._make_value_string(msg.syntax_escapechar)
            result.append(('syntax_escapechar', _t1318,))
            _t1317 = None
        else:
            _t1317 = None
        return sorted(result)

    def deconstruct_relation_id_string(self, msg: logic_pb2.RelationId) -> Optional[str]:
        name = self.relation_id_to_string(msg)
        if name != '':
            return name
        return None

    def deconstruct_relation_id_uint128(self, msg: logic_pb2.RelationId) -> Optional[logic_pb2.UInt128Value]:
        name = self.relation_id_to_string(msg)
        if name == '':
            return self.relation_id_to_uint128(msg)
        return None

    def deconstruct_bindings(self, abs: logic_pb2.Abstraction) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        n = len(abs.vars)
        return (abs.vars[0:n], [],)

    def deconstruct_bindings_with_arity(self, abs: logic_pb2.Abstraction, value_arity: int) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        n = len(abs.vars)
        key_end = (n - value_arity)
        return (abs.vars[0:key_end], abs.vars[key_end:n],)

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start7 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('transaction')
        self._push_path(2)
        
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('configure', 1)):
            _t620 = self.parse_configure()
            _t619 = _t620
        else:
            _t619 = None
        configure0 = _t619
        self._pop_path()
        self._push_path(3)
        
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('sync', 1)):
            _t622 = self.parse_sync()
            _t621 = _t622
        else:
            _t621 = None
        sync1 = _t621
        self._pop_path()
        self._push_path(1)
        xs2 = []
        cond3 = self.match_lookahead_literal('(', 0)
        idx5 = 0
        while cond3:
            self._push_path(idx5)
            _t623 = self.parse_epoch()
            item4 = _t623
            self._pop_path()
            xs2.append(item4)
            idx5 = (idx5 + 1)
            cond3 = self.match_lookahead_literal('(', 0)
        self._pop_path()
        epochs6 = xs2
        self.consume_literal(')')
        _t624 = self.default_configure()
        _t625 = transactions_pb2.Transaction(epochs=epochs6, configure=(configure0 if configure0 is not None else _t624), sync=sync1)
        result8 = _t625
        self._record_span(span_start7)
        return result8

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start10 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('configure')
        _t626 = self.parse_config_dict()
        config_dict9 = _t626
        self.consume_literal(')')
        _t627 = self.construct_configure(config_dict9)
        result11 = _t627
        self._record_span(span_start10)
        return result11

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        span_start17 = self._span_start()
        self.consume_literal('{')
        xs12 = []
        cond13 = self.match_lookahead_literal(':', 0)
        idx15 = 0
        while cond13:
            self._push_path(idx15)
            _t628 = self.parse_config_key_value()
            item14 = _t628
            self._pop_path()
            xs12.append(item14)
            idx15 = (idx15 + 1)
            cond13 = self.match_lookahead_literal(':', 0)
        config_key_values16 = xs12
        self.consume_literal('}')
        result18 = config_key_values16
        self._record_span(span_start17)
        return result18

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        span_start21 = self._span_start()
        self.consume_literal(':')
        symbol19 = self.consume_terminal('SYMBOL')
        _t629 = self.parse_value()
        value20 = _t629
        result22 = (symbol19, value20,)
        self._record_span(span_start21)
        return result22

    def parse_value(self) -> logic_pb2.Value:
        span_start33 = self._span_start()
        
        if self.match_lookahead_literal('true', 0):
            _t630 = 9
        else:
            
            if self.match_lookahead_literal('missing', 0):
                _t631 = 8
            else:
                
                if self.match_lookahead_literal('false', 0):
                    _t632 = 9
                else:
                    
                    if self.match_lookahead_literal('(', 0):
                        
                        if self.match_lookahead_literal('datetime', 1):
                            _t634 = 1
                        else:
                            
                            if self.match_lookahead_literal('date', 1):
                                _t635 = 0
                            else:
                                _t635 = -1
                            _t634 = _t635
                        _t633 = _t634
                    else:
                        
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t636 = 5
                        else:
                            
                            if self.match_lookahead_terminal('STRING', 0):
                                _t637 = 2
                            else:
                                
                                if self.match_lookahead_terminal('INT128', 0):
                                    _t638 = 6
                                else:
                                    
                                    if self.match_lookahead_terminal('INT', 0):
                                        _t639 = 3
                                    else:
                                        
                                        if self.match_lookahead_terminal('FLOAT', 0):
                                            _t640 = 4
                                        else:
                                            
                                            if self.match_lookahead_terminal('DECIMAL', 0):
                                                _t641 = 7
                                            else:
                                                _t641 = -1
                                            _t640 = _t641
                                        _t639 = _t640
                                    _t638 = _t639
                                _t637 = _t638
                            _t636 = _t637
                        _t633 = _t636
                    _t632 = _t633
                _t631 = _t632
            _t630 = _t631
        prediction23 = _t630
        
        if prediction23 == 9:
            _t643 = self.parse_boolean_value()
            boolean_value32 = _t643
            _t644 = logic_pb2.Value(boolean_value=boolean_value32)
            _t642 = _t644
        else:
            
            if prediction23 == 8:
                self.consume_literal('missing')
                _t646 = logic_pb2.MissingValue()
                _t647 = logic_pb2.Value(missing_value=_t646)
                _t645 = _t647
            else:
                
                if prediction23 == 7:
                    decimal31 = self.consume_terminal('DECIMAL')
                    _t649 = logic_pb2.Value(decimal_value=decimal31)
                    _t648 = _t649
                else:
                    
                    if prediction23 == 6:
                        int12830 = self.consume_terminal('INT128')
                        _t651 = logic_pb2.Value(int128_value=int12830)
                        _t650 = _t651
                    else:
                        
                        if prediction23 == 5:
                            uint12829 = self.consume_terminal('UINT128')
                            _t653 = logic_pb2.Value(uint128_value=uint12829)
                            _t652 = _t653
                        else:
                            
                            if prediction23 == 4:
                                float28 = self.consume_terminal('FLOAT')
                                _t655 = logic_pb2.Value(float_value=float28)
                                _t654 = _t655
                            else:
                                
                                if prediction23 == 3:
                                    int27 = self.consume_terminal('INT')
                                    _t657 = logic_pb2.Value(int_value=int27)
                                    _t656 = _t657
                                else:
                                    
                                    if prediction23 == 2:
                                        string26 = self.consume_terminal('STRING')
                                        _t659 = logic_pb2.Value(string_value=string26)
                                        _t658 = _t659
                                    else:
                                        
                                        if prediction23 == 1:
                                            _t661 = self.parse_datetime()
                                            datetime25 = _t661
                                            _t662 = logic_pb2.Value(datetime_value=datetime25)
                                            _t660 = _t662
                                        else:
                                            
                                            if prediction23 == 0:
                                                _t664 = self.parse_date()
                                                date24 = _t664
                                                _t665 = logic_pb2.Value(date_value=date24)
                                                _t663 = _t665
                                            else:
                                                raise ParseError(f"{'Unexpected token in value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t660 = _t663
                                        _t658 = _t660
                                    _t656 = _t658
                                _t654 = _t656
                            _t652 = _t654
                        _t650 = _t652
                    _t648 = _t650
                _t645 = _t648
            _t642 = _t645
        result34 = _t642
        self._record_span(span_start33)
        return result34

    def parse_date(self) -> logic_pb2.DateValue:
        span_start38 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('date')
        self._push_path(1)
        int35 = self.consume_terminal('INT')
        self._pop_path()
        self._push_path(2)
        int_336 = self.consume_terminal('INT')
        self._pop_path()
        self._push_path(3)
        int_437 = self.consume_terminal('INT')
        self._pop_path()
        self.consume_literal(')')
        _t666 = logic_pb2.DateValue(year=int(int35), month=int(int_336), day=int(int_437))
        result39 = _t666
        self._record_span(span_start38)
        return result39

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start47 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('datetime')
        self._push_path(1)
        int40 = self.consume_terminal('INT')
        self._pop_path()
        self._push_path(2)
        int_341 = self.consume_terminal('INT')
        self._pop_path()
        self._push_path(3)
        int_442 = self.consume_terminal('INT')
        self._pop_path()
        self._push_path(4)
        int_543 = self.consume_terminal('INT')
        self._pop_path()
        self._push_path(5)
        int_644 = self.consume_terminal('INT')
        self._pop_path()
        self._push_path(6)
        int_745 = self.consume_terminal('INT')
        self._pop_path()
        
        if self.match_lookahead_terminal('INT', 0):
            _t667 = self.consume_terminal('INT')
        else:
            _t667 = None
        int_846 = _t667
        self.consume_literal(')')
        _t668 = logic_pb2.DateTimeValue(year=int(int40), month=int(int_341), day=int(int_442), hour=int(int_543), minute=int(int_644), second=int(int_745), microsecond=int((int_846 if int_846 is not None else 0)))
        result48 = _t668
        self._record_span(span_start47)
        return result48

    def parse_boolean_value(self) -> bool:
        span_start50 = self._span_start()
        
        if self.match_lookahead_literal('true', 0):
            _t669 = 0
        else:
            
            if self.match_lookahead_literal('false', 0):
                _t670 = 1
            else:
                _t670 = -1
            _t669 = _t670
        prediction49 = _t669
        
        if prediction49 == 1:
            self.consume_literal('false')
            _t671 = False
        else:
            
            if prediction49 == 0:
                self.consume_literal('true')
                _t672 = True
            else:
                raise ParseError(f"{'Unexpected token in boolean_value'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t671 = _t672
        result51 = _t671
        self._record_span(span_start50)
        return result51

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start57 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('sync')
        self._push_path(1)
        xs52 = []
        cond53 = self.match_lookahead_literal(':', 0)
        idx55 = 0
        while cond53:
            self._push_path(idx55)
            _t673 = self.parse_fragment_id()
            item54 = _t673
            self._pop_path()
            xs52.append(item54)
            idx55 = (idx55 + 1)
            cond53 = self.match_lookahead_literal(':', 0)
        self._pop_path()
        fragment_ids56 = xs52
        self.consume_literal(')')
        _t674 = transactions_pb2.Sync(fragments=fragment_ids56)
        result58 = _t674
        self._record_span(span_start57)
        return result58

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start60 = self._span_start()
        self.consume_literal(':')
        symbol59 = self.consume_terminal('SYMBOL')
        result61 = fragments_pb2.FragmentId(id=symbol59.encode())
        self._record_span(span_start60)
        return result61

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start64 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('epoch')
        self._push_path(1)
        
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('writes', 1)):
            _t676 = self.parse_epoch_writes()
            _t675 = _t676
        else:
            _t675 = None
        epoch_writes62 = _t675
        self._pop_path()
        self._push_path(2)
        
        if self.match_lookahead_literal('(', 0):
            _t678 = self.parse_epoch_reads()
            _t677 = _t678
        else:
            _t677 = None
        epoch_reads63 = _t677
        self._pop_path()
        self.consume_literal(')')
        _t679 = transactions_pb2.Epoch(writes=(epoch_writes62 if epoch_writes62 is not None else []), reads=(epoch_reads63 if epoch_reads63 is not None else []))
        result65 = _t679
        self._record_span(span_start64)
        return result65

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        span_start71 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('writes')
        xs66 = []
        cond67 = self.match_lookahead_literal('(', 0)
        idx69 = 0
        while cond67:
            self._push_path(idx69)
            _t680 = self.parse_write()
            item68 = _t680
            self._pop_path()
            xs66.append(item68)
            idx69 = (idx69 + 1)
            cond67 = self.match_lookahead_literal('(', 0)
        writes70 = xs66
        self.consume_literal(')')
        result72 = writes70
        self._record_span(span_start71)
        return result72

    def parse_write(self) -> transactions_pb2.Write:
        span_start77 = self._span_start()
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('undefine', 1):
                _t682 = 1
            else:
                
                if self.match_lookahead_literal('define', 1):
                    _t683 = 0
                else:
                    
                    if self.match_lookahead_literal('context', 1):
                        _t684 = 2
                    else:
                        _t684 = -1
                    _t683 = _t684
                _t682 = _t683
            _t681 = _t682
        else:
            _t681 = -1
        prediction73 = _t681
        
        if prediction73 == 2:
            _t686 = self.parse_context()
            context76 = _t686
            _t687 = transactions_pb2.Write(context=context76)
            _t685 = _t687
        else:
            
            if prediction73 == 1:
                _t689 = self.parse_undefine()
                undefine75 = _t689
                _t690 = transactions_pb2.Write(undefine=undefine75)
                _t688 = _t690
            else:
                
                if prediction73 == 0:
                    _t692 = self.parse_define()
                    define74 = _t692
                    _t693 = transactions_pb2.Write(define=define74)
                    _t691 = _t693
                else:
                    raise ParseError(f"{'Unexpected token in write'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t688 = _t691
            _t685 = _t688
        result78 = _t685
        self._record_span(span_start77)
        return result78

    def parse_define(self) -> transactions_pb2.Define:
        span_start80 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('define')
        self._push_path(1)
        _t694 = self.parse_fragment()
        fragment79 = _t694
        self._pop_path()
        self.consume_literal(')')
        _t695 = transactions_pb2.Define(fragment=fragment79)
        result81 = _t695
        self._record_span(span_start80)
        return result81

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start88 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('fragment')
        _t696 = self.parse_new_fragment_id()
        new_fragment_id82 = _t696
        xs83 = []
        cond84 = self.match_lookahead_literal('(', 0)
        idx86 = 0
        while cond84:
            self._push_path(idx86)
            _t697 = self.parse_declaration()
            item85 = _t697
            self._pop_path()
            xs83.append(item85)
            idx86 = (idx86 + 1)
            cond84 = self.match_lookahead_literal('(', 0)
        declarations87 = xs83
        self.consume_literal(')')
        result89 = self.construct_fragment(new_fragment_id82, declarations87)
        self._record_span(span_start88)
        return result89

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start91 = self._span_start()
        _t698 = self.parse_fragment_id()
        fragment_id90 = _t698
        self.start_fragment(fragment_id90)
        result92 = fragment_id90
        self._record_span(span_start91)
        return result92

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start98 = self._span_start()
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('rel_edb', 1):
                _t700 = 3
            else:
                
                if self.match_lookahead_literal('functional_dependency', 1):
                    _t701 = 2
                else:
                    
                    if self.match_lookahead_literal('def', 1):
                        _t702 = 0
                    else:
                        
                        if self.match_lookahead_literal('csv_data', 1):
                            _t703 = 3
                        else:
                            
                            if self.match_lookahead_literal('betree_relation', 1):
                                _t704 = 3
                            else:
                                
                                if self.match_lookahead_literal('algorithm', 1):
                                    _t705 = 1
                                else:
                                    _t705 = -1
                                _t704 = _t705
                            _t703 = _t704
                        _t702 = _t703
                    _t701 = _t702
                _t700 = _t701
            _t699 = _t700
        else:
            _t699 = -1
        prediction93 = _t699
        
        if prediction93 == 3:
            _t707 = self.parse_data()
            data97 = _t707
            _t708 = logic_pb2.Declaration(data=data97)
            _t706 = _t708
        else:
            
            if prediction93 == 2:
                _t710 = self.parse_constraint()
                constraint96 = _t710
                _t711 = logic_pb2.Declaration(constraint=constraint96)
                _t709 = _t711
            else:
                
                if prediction93 == 1:
                    _t713 = self.parse_algorithm()
                    algorithm95 = _t713
                    _t714 = logic_pb2.Declaration(algorithm=algorithm95)
                    _t712 = _t714
                else:
                    
                    if prediction93 == 0:
                        _t716 = self.parse_def()
                        def94 = _t716
                        _t717 = logic_pb2.Declaration()
                        getattr(_t717, 'def').CopyFrom(def94)
                        _t715 = _t717
                    else:
                        raise ParseError(f"{'Unexpected token in declaration'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t712 = _t715
                _t709 = _t712
            _t706 = _t709
        result99 = _t706
        self._record_span(span_start98)
        return result99

    def parse_def(self) -> logic_pb2.Def:
        span_start103 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('def')
        self._push_path(1)
        _t718 = self.parse_relation_id()
        relation_id100 = _t718
        self._pop_path()
        self._push_path(2)
        _t719 = self.parse_abstraction()
        abstraction101 = _t719
        self._pop_path()
        self._push_path(3)
        
        if self.match_lookahead_literal('(', 0):
            _t721 = self.parse_attrs()
            _t720 = _t721
        else:
            _t720 = None
        attrs102 = _t720
        self._pop_path()
        self.consume_literal(')')
        _t722 = logic_pb2.Def(name=relation_id100, body=abstraction101, attrs=(attrs102 if attrs102 is not None else []))
        result104 = _t722
        self._record_span(span_start103)
        return result104

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start108 = self._span_start()
        
        if self.match_lookahead_literal(':', 0):
            _t723 = 0
        else:
            
            if self.match_lookahead_terminal('UINT128', 0):
                _t724 = 1
            else:
                _t724 = -1
            _t723 = _t724
        prediction105 = _t723
        
        if prediction105 == 1:
            uint128107 = self.consume_terminal('UINT128')
            _t725 = logic_pb2.RelationId(id_low=uint128107.low, id_high=uint128107.high)
        else:
            
            if prediction105 == 0:
                self.consume_literal(':')
                symbol106 = self.consume_terminal('SYMBOL')
                _t726 = self.relation_id_from_string(symbol106)
            else:
                raise ParseError(f"{'Unexpected token in relation_id'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t725 = _t726
        result109 = _t725
        self._record_span(span_start108)
        return result109

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start112 = self._span_start()
        self.consume_literal('(')
        _t727 = self.parse_bindings()
        bindings110 = _t727
        self._push_path(2)
        _t728 = self.parse_formula()
        formula111 = _t728
        self._pop_path()
        self.consume_literal(')')
        _t729 = logic_pb2.Abstraction(vars=(list(bindings110[0]) + list(bindings110[1] if bindings110[1] is not None else [])), value=formula111)
        result113 = _t729
        self._record_span(span_start112)
        return result113

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        span_start120 = self._span_start()
        self.consume_literal('[')
        xs114 = []
        cond115 = self.match_lookahead_terminal('SYMBOL', 0)
        idx117 = 0
        while cond115:
            self._push_path(idx117)
            _t730 = self.parse_binding()
            item116 = _t730
            self._pop_path()
            xs114.append(item116)
            idx117 = (idx117 + 1)
            cond115 = self.match_lookahead_terminal('SYMBOL', 0)
        bindings118 = xs114
        
        if self.match_lookahead_literal('|', 0):
            _t732 = self.parse_value_bindings()
            _t731 = _t732
        else:
            _t731 = None
        value_bindings119 = _t731
        self.consume_literal(']')
        result121 = (bindings118, (value_bindings119 if value_bindings119 is not None else []),)
        self._record_span(span_start120)
        return result121

    def parse_binding(self) -> logic_pb2.Binding:
        span_start124 = self._span_start()
        symbol122 = self.consume_terminal('SYMBOL')
        self.consume_literal('::')
        self._push_path(2)
        _t733 = self.parse_type()
        type123 = _t733
        self._pop_path()
        _t734 = logic_pb2.Var(name=symbol122)
        _t735 = logic_pb2.Binding(var=_t734, type=type123)
        result125 = _t735
        self._record_span(span_start124)
        return result125

    def parse_type(self) -> logic_pb2.Type:
        span_start138 = self._span_start()
        
        if self.match_lookahead_literal('UNKNOWN', 0):
            _t736 = 0
        else:
            
            if self.match_lookahead_literal('UINT128', 0):
                _t737 = 4
            else:
                
                if self.match_lookahead_literal('STRING', 0):
                    _t738 = 1
                else:
                    
                    if self.match_lookahead_literal('MISSING', 0):
                        _t739 = 8
                    else:
                        
                        if self.match_lookahead_literal('INT128', 0):
                            _t740 = 5
                        else:
                            
                            if self.match_lookahead_literal('INT', 0):
                                _t741 = 2
                            else:
                                
                                if self.match_lookahead_literal('FLOAT', 0):
                                    _t742 = 3
                                else:
                                    
                                    if self.match_lookahead_literal('DATETIME', 0):
                                        _t743 = 7
                                    else:
                                        
                                        if self.match_lookahead_literal('DATE', 0):
                                            _t744 = 6
                                        else:
                                            
                                            if self.match_lookahead_literal('BOOLEAN', 0):
                                                _t745 = 10
                                            else:
                                                
                                                if self.match_lookahead_literal('(', 0):
                                                    _t746 = 9
                                                else:
                                                    _t746 = -1
                                                _t745 = _t746
                                            _t744 = _t745
                                        _t743 = _t744
                                    _t742 = _t743
                                _t741 = _t742
                            _t740 = _t741
                        _t739 = _t740
                    _t738 = _t739
                _t737 = _t738
            _t736 = _t737
        prediction126 = _t736
        
        if prediction126 == 10:
            _t748 = self.parse_boolean_type()
            boolean_type137 = _t748
            _t749 = logic_pb2.Type(boolean_type=boolean_type137)
            _t747 = _t749
        else:
            
            if prediction126 == 9:
                _t751 = self.parse_decimal_type()
                decimal_type136 = _t751
                _t752 = logic_pb2.Type(decimal_type=decimal_type136)
                _t750 = _t752
            else:
                
                if prediction126 == 8:
                    _t754 = self.parse_missing_type()
                    missing_type135 = _t754
                    _t755 = logic_pb2.Type(missing_type=missing_type135)
                    _t753 = _t755
                else:
                    
                    if prediction126 == 7:
                        _t757 = self.parse_datetime_type()
                        datetime_type134 = _t757
                        _t758 = logic_pb2.Type(datetime_type=datetime_type134)
                        _t756 = _t758
                    else:
                        
                        if prediction126 == 6:
                            _t760 = self.parse_date_type()
                            date_type133 = _t760
                            _t761 = logic_pb2.Type(date_type=date_type133)
                            _t759 = _t761
                        else:
                            
                            if prediction126 == 5:
                                _t763 = self.parse_int128_type()
                                int128_type132 = _t763
                                _t764 = logic_pb2.Type(int128_type=int128_type132)
                                _t762 = _t764
                            else:
                                
                                if prediction126 == 4:
                                    _t766 = self.parse_uint128_type()
                                    uint128_type131 = _t766
                                    _t767 = logic_pb2.Type(uint128_type=uint128_type131)
                                    _t765 = _t767
                                else:
                                    
                                    if prediction126 == 3:
                                        _t769 = self.parse_float_type()
                                        float_type130 = _t769
                                        _t770 = logic_pb2.Type(float_type=float_type130)
                                        _t768 = _t770
                                    else:
                                        
                                        if prediction126 == 2:
                                            _t772 = self.parse_int_type()
                                            int_type129 = _t772
                                            _t773 = logic_pb2.Type(int_type=int_type129)
                                            _t771 = _t773
                                        else:
                                            
                                            if prediction126 == 1:
                                                _t775 = self.parse_string_type()
                                                string_type128 = _t775
                                                _t776 = logic_pb2.Type(string_type=string_type128)
                                                _t774 = _t776
                                            else:
                                                
                                                if prediction126 == 0:
                                                    _t778 = self.parse_unspecified_type()
                                                    unspecified_type127 = _t778
                                                    _t779 = logic_pb2.Type(unspecified_type=unspecified_type127)
                                                    _t777 = _t779
                                                else:
                                                    raise ParseError(f"{'Unexpected token in type'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t774 = _t777
                                            _t771 = _t774
                                        _t768 = _t771
                                    _t765 = _t768
                                _t762 = _t765
                            _t759 = _t762
                        _t756 = _t759
                    _t753 = _t756
                _t750 = _t753
            _t747 = _t750
        result139 = _t747
        self._record_span(span_start138)
        return result139

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start140 = self._span_start()
        self.consume_literal('UNKNOWN')
        _t780 = logic_pb2.UnspecifiedType()
        result141 = _t780
        self._record_span(span_start140)
        return result141

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start142 = self._span_start()
        self.consume_literal('STRING')
        _t781 = logic_pb2.StringType()
        result143 = _t781
        self._record_span(span_start142)
        return result143

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start144 = self._span_start()
        self.consume_literal('INT')
        _t782 = logic_pb2.IntType()
        result145 = _t782
        self._record_span(span_start144)
        return result145

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start146 = self._span_start()
        self.consume_literal('FLOAT')
        _t783 = logic_pb2.FloatType()
        result147 = _t783
        self._record_span(span_start146)
        return result147

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start148 = self._span_start()
        self.consume_literal('UINT128')
        _t784 = logic_pb2.UInt128Type()
        result149 = _t784
        self._record_span(span_start148)
        return result149

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start150 = self._span_start()
        self.consume_literal('INT128')
        _t785 = logic_pb2.Int128Type()
        result151 = _t785
        self._record_span(span_start150)
        return result151

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start152 = self._span_start()
        self.consume_literal('DATE')
        _t786 = logic_pb2.DateType()
        result153 = _t786
        self._record_span(span_start152)
        return result153

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start154 = self._span_start()
        self.consume_literal('DATETIME')
        _t787 = logic_pb2.DateTimeType()
        result155 = _t787
        self._record_span(span_start154)
        return result155

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start156 = self._span_start()
        self.consume_literal('MISSING')
        _t788 = logic_pb2.MissingType()
        result157 = _t788
        self._record_span(span_start156)
        return result157

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start160 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('DECIMAL')
        self._push_path(1)
        int158 = self.consume_terminal('INT')
        self._pop_path()
        self._push_path(2)
        int_3159 = self.consume_terminal('INT')
        self._pop_path()
        self.consume_literal(')')
        _t789 = logic_pb2.DecimalType(precision=int(int158), scale=int(int_3159))
        result161 = _t789
        self._record_span(span_start160)
        return result161

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start162 = self._span_start()
        self.consume_literal('BOOLEAN')
        _t790 = logic_pb2.BooleanType()
        result163 = _t790
        self._record_span(span_start162)
        return result163

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        span_start169 = self._span_start()
        self.consume_literal('|')
        xs164 = []
        cond165 = self.match_lookahead_terminal('SYMBOL', 0)
        idx167 = 0
        while cond165:
            self._push_path(idx167)
            _t791 = self.parse_binding()
            item166 = _t791
            self._pop_path()
            xs164.append(item166)
            idx167 = (idx167 + 1)
            cond165 = self.match_lookahead_terminal('SYMBOL', 0)
        bindings168 = xs164
        result170 = bindings168
        self._record_span(span_start169)
        return result170

    def parse_formula(self) -> logic_pb2.Formula:
        span_start185 = self._span_start()
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('true', 1):
                _t793 = 0
            else:
                
                if self.match_lookahead_literal('relatom', 1):
                    _t794 = 11
                else:
                    
                    if self.match_lookahead_literal('reduce', 1):
                        _t795 = 3
                    else:
                        
                        if self.match_lookahead_literal('primitive', 1):
                            _t796 = 10
                        else:
                            
                            if self.match_lookahead_literal('pragma', 1):
                                _t797 = 9
                            else:
                                
                                if self.match_lookahead_literal('or', 1):
                                    _t798 = 5
                                else:
                                    
                                    if self.match_lookahead_literal('not', 1):
                                        _t799 = 6
                                    else:
                                        
                                        if self.match_lookahead_literal('ffi', 1):
                                            _t800 = 7
                                        else:
                                            
                                            if self.match_lookahead_literal('false', 1):
                                                _t801 = 1
                                            else:
                                                
                                                if self.match_lookahead_literal('exists', 1):
                                                    _t802 = 2
                                                else:
                                                    
                                                    if self.match_lookahead_literal('cast', 1):
                                                        _t803 = 12
                                                    else:
                                                        
                                                        if self.match_lookahead_literal('atom', 1):
                                                            _t804 = 8
                                                        else:
                                                            
                                                            if self.match_lookahead_literal('and', 1):
                                                                _t805 = 4
                                                            else:
                                                                
                                                                if self.match_lookahead_literal('>=', 1):
                                                                    _t806 = 10
                                                                else:
                                                                    
                                                                    if self.match_lookahead_literal('>', 1):
                                                                        _t807 = 10
                                                                    else:
                                                                        
                                                                        if self.match_lookahead_literal('=', 1):
                                                                            _t808 = 10
                                                                        else:
                                                                            
                                                                            if self.match_lookahead_literal('<=', 1):
                                                                                _t809 = 10
                                                                            else:
                                                                                
                                                                                if self.match_lookahead_literal('<', 1):
                                                                                    _t810 = 10
                                                                                else:
                                                                                    
                                                                                    if self.match_lookahead_literal('/', 1):
                                                                                        _t811 = 10
                                                                                    else:
                                                                                        
                                                                                        if self.match_lookahead_literal('-', 1):
                                                                                            _t812 = 10
                                                                                        else:
                                                                                            
                                                                                            if self.match_lookahead_literal('+', 1):
                                                                                                _t813 = 10
                                                                                            else:
                                                                                                
                                                                                                if self.match_lookahead_literal('*', 1):
                                                                                                    _t814 = 10
                                                                                                else:
                                                                                                    _t814 = -1
                                                                                                _t813 = _t814
                                                                                            _t812 = _t813
                                                                                        _t811 = _t812
                                                                                    _t810 = _t811
                                                                                _t809 = _t810
                                                                            _t808 = _t809
                                                                        _t807 = _t808
                                                                    _t806 = _t807
                                                                _t805 = _t806
                                                            _t804 = _t805
                                                        _t803 = _t804
                                                    _t802 = _t803
                                                _t801 = _t802
                                            _t800 = _t801
                                        _t799 = _t800
                                    _t798 = _t799
                                _t797 = _t798
                            _t796 = _t797
                        _t795 = _t796
                    _t794 = _t795
                _t793 = _t794
            _t792 = _t793
        else:
            _t792 = -1
        prediction171 = _t792
        
        if prediction171 == 12:
            _t816 = self.parse_cast()
            cast184 = _t816
            _t817 = logic_pb2.Formula(cast=cast184)
            _t815 = _t817
        else:
            
            if prediction171 == 11:
                _t819 = self.parse_rel_atom()
                rel_atom183 = _t819
                _t820 = logic_pb2.Formula(rel_atom=rel_atom183)
                _t818 = _t820
            else:
                
                if prediction171 == 10:
                    _t822 = self.parse_primitive()
                    primitive182 = _t822
                    _t823 = logic_pb2.Formula(primitive=primitive182)
                    _t821 = _t823
                else:
                    
                    if prediction171 == 9:
                        _t825 = self.parse_pragma()
                        pragma181 = _t825
                        _t826 = logic_pb2.Formula(pragma=pragma181)
                        _t824 = _t826
                    else:
                        
                        if prediction171 == 8:
                            _t828 = self.parse_atom()
                            atom180 = _t828
                            _t829 = logic_pb2.Formula(atom=atom180)
                            _t827 = _t829
                        else:
                            
                            if prediction171 == 7:
                                _t831 = self.parse_ffi()
                                ffi179 = _t831
                                _t832 = logic_pb2.Formula(ffi=ffi179)
                                _t830 = _t832
                            else:
                                
                                if prediction171 == 6:
                                    _t834 = self.parse_not()
                                    not178 = _t834
                                    _t835 = logic_pb2.Formula()
                                    getattr(_t835, 'not').CopyFrom(not178)
                                    _t833 = _t835
                                else:
                                    
                                    if prediction171 == 5:
                                        _t837 = self.parse_disjunction()
                                        disjunction177 = _t837
                                        _t838 = logic_pb2.Formula(disjunction=disjunction177)
                                        _t836 = _t838
                                    else:
                                        
                                        if prediction171 == 4:
                                            _t840 = self.parse_conjunction()
                                            conjunction176 = _t840
                                            _t841 = logic_pb2.Formula(conjunction=conjunction176)
                                            _t839 = _t841
                                        else:
                                            
                                            if prediction171 == 3:
                                                _t843 = self.parse_reduce()
                                                reduce175 = _t843
                                                _t844 = logic_pb2.Formula(reduce=reduce175)
                                                _t842 = _t844
                                            else:
                                                
                                                if prediction171 == 2:
                                                    _t846 = self.parse_exists()
                                                    exists174 = _t846
                                                    _t847 = logic_pb2.Formula(exists=exists174)
                                                    _t845 = _t847
                                                else:
                                                    
                                                    if prediction171 == 1:
                                                        _t849 = self.parse_false()
                                                        false173 = _t849
                                                        _t850 = logic_pb2.Formula(disjunction=false173)
                                                        _t848 = _t850
                                                    else:
                                                        
                                                        if prediction171 == 0:
                                                            _t852 = self.parse_true()
                                                            true172 = _t852
                                                            _t853 = logic_pb2.Formula(conjunction=true172)
                                                            _t851 = _t853
                                                        else:
                                                            raise ParseError(f"{'Unexpected token in formula'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t848 = _t851
                                                    _t845 = _t848
                                                _t842 = _t845
                                            _t839 = _t842
                                        _t836 = _t839
                                    _t833 = _t836
                                _t830 = _t833
                            _t827 = _t830
                        _t824 = _t827
                    _t821 = _t824
                _t818 = _t821
            _t815 = _t818
        result186 = _t815
        self._record_span(span_start185)
        return result186

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start187 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('true')
        self.consume_literal(')')
        _t854 = logic_pb2.Conjunction(args=[])
        result188 = _t854
        self._record_span(span_start187)
        return result188

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start189 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('false')
        self.consume_literal(')')
        _t855 = logic_pb2.Disjunction(args=[])
        result190 = _t855
        self._record_span(span_start189)
        return result190

    def parse_exists(self) -> logic_pb2.Exists:
        span_start193 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('exists')
        _t856 = self.parse_bindings()
        bindings191 = _t856
        _t857 = self.parse_formula()
        formula192 = _t857
        self.consume_literal(')')
        _t858 = logic_pb2.Abstraction(vars=(list(bindings191[0]) + list(bindings191[1] if bindings191[1] is not None else [])), value=formula192)
        _t859 = logic_pb2.Exists(body=_t858)
        result194 = _t859
        self._record_span(span_start193)
        return result194

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start198 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('reduce')
        self._push_path(1)
        _t860 = self.parse_abstraction()
        abstraction195 = _t860
        self._pop_path()
        self._push_path(2)
        _t861 = self.parse_abstraction()
        abstraction_3196 = _t861
        self._pop_path()
        self._push_path(3)
        _t862 = self.parse_terms()
        terms197 = _t862
        self._pop_path()
        self.consume_literal(')')
        _t863 = logic_pb2.Reduce(op=abstraction195, body=abstraction_3196, terms=terms197)
        result199 = _t863
        self._record_span(span_start198)
        return result199

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        span_start205 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('terms')
        xs200 = []
        cond201 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        idx203 = 0
        while cond201:
            self._push_path(idx203)
            _t864 = self.parse_term()
            item202 = _t864
            self._pop_path()
            xs200.append(item202)
            idx203 = (idx203 + 1)
            cond201 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        terms204 = xs200
        self.consume_literal(')')
        result206 = terms204
        self._record_span(span_start205)
        return result206

    def parse_term(self) -> logic_pb2.Term:
        span_start210 = self._span_start()
        
        if self.match_lookahead_literal('true', 0):
            _t865 = 1
        else:
            
            if self.match_lookahead_literal('missing', 0):
                _t866 = 1
            else:
                
                if self.match_lookahead_literal('false', 0):
                    _t867 = 1
                else:
                    
                    if self.match_lookahead_literal('(', 0):
                        _t868 = 1
                    else:
                        
                        if self.match_lookahead_terminal('UINT128', 0):
                            _t869 = 1
                        else:
                            
                            if self.match_lookahead_terminal('SYMBOL', 0):
                                _t870 = 0
                            else:
                                
                                if self.match_lookahead_terminal('STRING', 0):
                                    _t871 = 1
                                else:
                                    
                                    if self.match_lookahead_terminal('INT128', 0):
                                        _t872 = 1
                                    else:
                                        
                                        if self.match_lookahead_terminal('INT', 0):
                                            _t873 = 1
                                        else:
                                            
                                            if self.match_lookahead_terminal('FLOAT', 0):
                                                _t874 = 1
                                            else:
                                                
                                                if self.match_lookahead_terminal('DECIMAL', 0):
                                                    _t875 = 1
                                                else:
                                                    _t875 = -1
                                                _t874 = _t875
                                            _t873 = _t874
                                        _t872 = _t873
                                    _t871 = _t872
                                _t870 = _t871
                            _t869 = _t870
                        _t868 = _t869
                    _t867 = _t868
                _t866 = _t867
            _t865 = _t866
        prediction207 = _t865
        
        if prediction207 == 1:
            _t877 = self.parse_constant()
            constant209 = _t877
            _t878 = logic_pb2.Term(constant=constant209)
            _t876 = _t878
        else:
            
            if prediction207 == 0:
                _t880 = self.parse_var()
                var208 = _t880
                _t881 = logic_pb2.Term(var=var208)
                _t879 = _t881
            else:
                raise ParseError(f"{'Unexpected token in term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t876 = _t879
        result211 = _t876
        self._record_span(span_start210)
        return result211

    def parse_var(self) -> logic_pb2.Var:
        span_start213 = self._span_start()
        symbol212 = self.consume_terminal('SYMBOL')
        _t882 = logic_pb2.Var(name=symbol212)
        result214 = _t882
        self._record_span(span_start213)
        return result214

    def parse_constant(self) -> logic_pb2.Value:
        span_start216 = self._span_start()
        _t883 = self.parse_value()
        value215 = _t883
        result217 = value215
        self._record_span(span_start216)
        return result217

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start223 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('and')
        self._push_path(1)
        xs218 = []
        cond219 = self.match_lookahead_literal('(', 0)
        idx221 = 0
        while cond219:
            self._push_path(idx221)
            _t884 = self.parse_formula()
            item220 = _t884
            self._pop_path()
            xs218.append(item220)
            idx221 = (idx221 + 1)
            cond219 = self.match_lookahead_literal('(', 0)
        self._pop_path()
        formulas222 = xs218
        self.consume_literal(')')
        _t885 = logic_pb2.Conjunction(args=formulas222)
        result224 = _t885
        self._record_span(span_start223)
        return result224

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start230 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('or')
        self._push_path(1)
        xs225 = []
        cond226 = self.match_lookahead_literal('(', 0)
        idx228 = 0
        while cond226:
            self._push_path(idx228)
            _t886 = self.parse_formula()
            item227 = _t886
            self._pop_path()
            xs225.append(item227)
            idx228 = (idx228 + 1)
            cond226 = self.match_lookahead_literal('(', 0)
        self._pop_path()
        formulas229 = xs225
        self.consume_literal(')')
        _t887 = logic_pb2.Disjunction(args=formulas229)
        result231 = _t887
        self._record_span(span_start230)
        return result231

    def parse_not(self) -> logic_pb2.Not:
        span_start233 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('not')
        self._push_path(1)
        _t888 = self.parse_formula()
        formula232 = _t888
        self._pop_path()
        self.consume_literal(')')
        _t889 = logic_pb2.Not(arg=formula232)
        result234 = _t889
        self._record_span(span_start233)
        return result234

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start238 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('ffi')
        self._push_path(1)
        _t890 = self.parse_name()
        name235 = _t890
        self._pop_path()
        self._push_path(2)
        _t891 = self.parse_ffi_args()
        ffi_args236 = _t891
        self._pop_path()
        self._push_path(3)
        _t892 = self.parse_terms()
        terms237 = _t892
        self._pop_path()
        self.consume_literal(')')
        _t893 = logic_pb2.FFI(name=name235, args=ffi_args236, terms=terms237)
        result239 = _t893
        self._record_span(span_start238)
        return result239

    def parse_name(self) -> str:
        span_start241 = self._span_start()
        self.consume_literal(':')
        symbol240 = self.consume_terminal('SYMBOL')
        result242 = symbol240
        self._record_span(span_start241)
        return result242

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        span_start248 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('args')
        xs243 = []
        cond244 = self.match_lookahead_literal('(', 0)
        idx246 = 0
        while cond244:
            self._push_path(idx246)
            _t894 = self.parse_abstraction()
            item245 = _t894
            self._pop_path()
            xs243.append(item245)
            idx246 = (idx246 + 1)
            cond244 = self.match_lookahead_literal('(', 0)
        abstractions247 = xs243
        self.consume_literal(')')
        result249 = abstractions247
        self._record_span(span_start248)
        return result249

    def parse_atom(self) -> logic_pb2.Atom:
        span_start256 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('atom')
        self._push_path(1)
        _t895 = self.parse_relation_id()
        relation_id250 = _t895
        self._pop_path()
        self._push_path(2)
        xs251 = []
        cond252 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        idx254 = 0
        while cond252:
            self._push_path(idx254)
            _t896 = self.parse_term()
            item253 = _t896
            self._pop_path()
            xs251.append(item253)
            idx254 = (idx254 + 1)
            cond252 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        self._pop_path()
        terms255 = xs251
        self.consume_literal(')')
        _t897 = logic_pb2.Atom(name=relation_id250, terms=terms255)
        result257 = _t897
        self._record_span(span_start256)
        return result257

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start264 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('pragma')
        self._push_path(1)
        _t898 = self.parse_name()
        name258 = _t898
        self._pop_path()
        self._push_path(2)
        xs259 = []
        cond260 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        idx262 = 0
        while cond260:
            self._push_path(idx262)
            _t899 = self.parse_term()
            item261 = _t899
            self._pop_path()
            xs259.append(item261)
            idx262 = (idx262 + 1)
            cond260 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        self._pop_path()
        terms263 = xs259
        self.consume_literal(')')
        _t900 = logic_pb2.Pragma(name=name258, terms=terms263)
        result265 = _t900
        self._record_span(span_start264)
        return result265

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start282 = self._span_start()
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('primitive', 1):
                _t902 = 9
            else:
                
                if self.match_lookahead_literal('>=', 1):
                    _t903 = 4
                else:
                    
                    if self.match_lookahead_literal('>', 1):
                        _t904 = 3
                    else:
                        
                        if self.match_lookahead_literal('=', 1):
                            _t905 = 0
                        else:
                            
                            if self.match_lookahead_literal('<=', 1):
                                _t906 = 2
                            else:
                                
                                if self.match_lookahead_literal('<', 1):
                                    _t907 = 1
                                else:
                                    
                                    if self.match_lookahead_literal('/', 1):
                                        _t908 = 8
                                    else:
                                        
                                        if self.match_lookahead_literal('-', 1):
                                            _t909 = 6
                                        else:
                                            
                                            if self.match_lookahead_literal('+', 1):
                                                _t910 = 5
                                            else:
                                                
                                                if self.match_lookahead_literal('*', 1):
                                                    _t911 = 7
                                                else:
                                                    _t911 = -1
                                                _t910 = _t911
                                            _t909 = _t910
                                        _t908 = _t909
                                    _t907 = _t908
                                _t906 = _t907
                            _t905 = _t906
                        _t904 = _t905
                    _t903 = _t904
                _t902 = _t903
            _t901 = _t902
        else:
            _t901 = -1
        prediction266 = _t901
        
        if prediction266 == 9:
            self.consume_literal('(')
            self.consume_literal('primitive')
            self._push_path(1)
            _t913 = self.parse_name()
            name276 = _t913
            self._pop_path()
            self._push_path(2)
            xs277 = []
            cond278 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            idx280 = 0
            while cond278:
                self._push_path(idx280)
                _t914 = self.parse_rel_term()
                item279 = _t914
                self._pop_path()
                xs277.append(item279)
                idx280 = (idx280 + 1)
                cond278 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
            self._pop_path()
            rel_terms281 = xs277
            self.consume_literal(')')
            _t915 = logic_pb2.Primitive(name=name276, terms=rel_terms281)
            _t912 = _t915
        else:
            
            if prediction266 == 8:
                _t917 = self.parse_divide()
                divide275 = _t917
                _t916 = divide275
            else:
                
                if prediction266 == 7:
                    _t919 = self.parse_multiply()
                    multiply274 = _t919
                    _t918 = multiply274
                else:
                    
                    if prediction266 == 6:
                        _t921 = self.parse_minus()
                        minus273 = _t921
                        _t920 = minus273
                    else:
                        
                        if prediction266 == 5:
                            _t923 = self.parse_add()
                            add272 = _t923
                            _t922 = add272
                        else:
                            
                            if prediction266 == 4:
                                _t925 = self.parse_gt_eq()
                                gt_eq271 = _t925
                                _t924 = gt_eq271
                            else:
                                
                                if prediction266 == 3:
                                    _t927 = self.parse_gt()
                                    gt270 = _t927
                                    _t926 = gt270
                                else:
                                    
                                    if prediction266 == 2:
                                        _t929 = self.parse_lt_eq()
                                        lt_eq269 = _t929
                                        _t928 = lt_eq269
                                    else:
                                        
                                        if prediction266 == 1:
                                            _t931 = self.parse_lt()
                                            lt268 = _t931
                                            _t930 = lt268
                                        else:
                                            
                                            if prediction266 == 0:
                                                _t933 = self.parse_eq()
                                                eq267 = _t933
                                                _t932 = eq267
                                            else:
                                                raise ParseError(f"{'Unexpected token in primitive'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t930 = _t932
                                        _t928 = _t930
                                    _t926 = _t928
                                _t924 = _t926
                            _t922 = _t924
                        _t920 = _t922
                    _t918 = _t920
                _t916 = _t918
            _t912 = _t916
        result283 = _t912
        self._record_span(span_start282)
        return result283

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start286 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('=')
        _t934 = self.parse_term()
        term284 = _t934
        _t935 = self.parse_term()
        term_3285 = _t935
        self.consume_literal(')')
        _t936 = logic_pb2.RelTerm(term=term284)
        _t937 = logic_pb2.RelTerm(term=term_3285)
        _t938 = logic_pb2.Primitive(name='rel_primitive_eq', terms=[_t936, _t937])
        result287 = _t938
        self._record_span(span_start286)
        return result287

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start290 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('<')
        _t939 = self.parse_term()
        term288 = _t939
        _t940 = self.parse_term()
        term_3289 = _t940
        self.consume_literal(')')
        _t941 = logic_pb2.RelTerm(term=term288)
        _t942 = logic_pb2.RelTerm(term=term_3289)
        _t943 = logic_pb2.Primitive(name='rel_primitive_lt_monotype', terms=[_t941, _t942])
        result291 = _t943
        self._record_span(span_start290)
        return result291

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start294 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('<=')
        _t944 = self.parse_term()
        term292 = _t944
        _t945 = self.parse_term()
        term_3293 = _t945
        self.consume_literal(')')
        _t946 = logic_pb2.RelTerm(term=term292)
        _t947 = logic_pb2.RelTerm(term=term_3293)
        _t948 = logic_pb2.Primitive(name='rel_primitive_lt_eq_monotype', terms=[_t946, _t947])
        result295 = _t948
        self._record_span(span_start294)
        return result295

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start298 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('>')
        _t949 = self.parse_term()
        term296 = _t949
        _t950 = self.parse_term()
        term_3297 = _t950
        self.consume_literal(')')
        _t951 = logic_pb2.RelTerm(term=term296)
        _t952 = logic_pb2.RelTerm(term=term_3297)
        _t953 = logic_pb2.Primitive(name='rel_primitive_gt_monotype', terms=[_t951, _t952])
        result299 = _t953
        self._record_span(span_start298)
        return result299

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start302 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('>=')
        _t954 = self.parse_term()
        term300 = _t954
        _t955 = self.parse_term()
        term_3301 = _t955
        self.consume_literal(')')
        _t956 = logic_pb2.RelTerm(term=term300)
        _t957 = logic_pb2.RelTerm(term=term_3301)
        _t958 = logic_pb2.Primitive(name='rel_primitive_gt_eq_monotype', terms=[_t956, _t957])
        result303 = _t958
        self._record_span(span_start302)
        return result303

    def parse_add(self) -> logic_pb2.Primitive:
        span_start307 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('+')
        _t959 = self.parse_term()
        term304 = _t959
        _t960 = self.parse_term()
        term_3305 = _t960
        _t961 = self.parse_term()
        term_4306 = _t961
        self.consume_literal(')')
        _t962 = logic_pb2.RelTerm(term=term304)
        _t963 = logic_pb2.RelTerm(term=term_3305)
        _t964 = logic_pb2.RelTerm(term=term_4306)
        _t965 = logic_pb2.Primitive(name='rel_primitive_add_monotype', terms=[_t962, _t963, _t964])
        result308 = _t965
        self._record_span(span_start307)
        return result308

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start312 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('-')
        _t966 = self.parse_term()
        term309 = _t966
        _t967 = self.parse_term()
        term_3310 = _t967
        _t968 = self.parse_term()
        term_4311 = _t968
        self.consume_literal(')')
        _t969 = logic_pb2.RelTerm(term=term309)
        _t970 = logic_pb2.RelTerm(term=term_3310)
        _t971 = logic_pb2.RelTerm(term=term_4311)
        _t972 = logic_pb2.Primitive(name='rel_primitive_subtract_monotype', terms=[_t969, _t970, _t971])
        result313 = _t972
        self._record_span(span_start312)
        return result313

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start317 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('*')
        _t973 = self.parse_term()
        term314 = _t973
        _t974 = self.parse_term()
        term_3315 = _t974
        _t975 = self.parse_term()
        term_4316 = _t975
        self.consume_literal(')')
        _t976 = logic_pb2.RelTerm(term=term314)
        _t977 = logic_pb2.RelTerm(term=term_3315)
        _t978 = logic_pb2.RelTerm(term=term_4316)
        _t979 = logic_pb2.Primitive(name='rel_primitive_multiply_monotype', terms=[_t976, _t977, _t978])
        result318 = _t979
        self._record_span(span_start317)
        return result318

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start322 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('/')
        _t980 = self.parse_term()
        term319 = _t980
        _t981 = self.parse_term()
        term_3320 = _t981
        _t982 = self.parse_term()
        term_4321 = _t982
        self.consume_literal(')')
        _t983 = logic_pb2.RelTerm(term=term319)
        _t984 = logic_pb2.RelTerm(term=term_3320)
        _t985 = logic_pb2.RelTerm(term=term_4321)
        _t986 = logic_pb2.Primitive(name='rel_primitive_divide_monotype', terms=[_t983, _t984, _t985])
        result323 = _t986
        self._record_span(span_start322)
        return result323

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start327 = self._span_start()
        
        if self.match_lookahead_literal('true', 0):
            _t987 = 1
        else:
            
            if self.match_lookahead_literal('missing', 0):
                _t988 = 1
            else:
                
                if self.match_lookahead_literal('false', 0):
                    _t989 = 1
                else:
                    
                    if self.match_lookahead_literal('(', 0):
                        _t990 = 1
                    else:
                        
                        if self.match_lookahead_literal('#', 0):
                            _t991 = 0
                        else:
                            
                            if self.match_lookahead_terminal('UINT128', 0):
                                _t992 = 1
                            else:
                                
                                if self.match_lookahead_terminal('SYMBOL', 0):
                                    _t993 = 1
                                else:
                                    
                                    if self.match_lookahead_terminal('STRING', 0):
                                        _t994 = 1
                                    else:
                                        
                                        if self.match_lookahead_terminal('INT128', 0):
                                            _t995 = 1
                                        else:
                                            
                                            if self.match_lookahead_terminal('INT', 0):
                                                _t996 = 1
                                            else:
                                                
                                                if self.match_lookahead_terminal('FLOAT', 0):
                                                    _t997 = 1
                                                else:
                                                    
                                                    if self.match_lookahead_terminal('DECIMAL', 0):
                                                        _t998 = 1
                                                    else:
                                                        _t998 = -1
                                                    _t997 = _t998
                                                _t996 = _t997
                                            _t995 = _t996
                                        _t994 = _t995
                                    _t993 = _t994
                                _t992 = _t993
                            _t991 = _t992
                        _t990 = _t991
                    _t989 = _t990
                _t988 = _t989
            _t987 = _t988
        prediction324 = _t987
        
        if prediction324 == 1:
            _t1000 = self.parse_term()
            term326 = _t1000
            _t1001 = logic_pb2.RelTerm(term=term326)
            _t999 = _t1001
        else:
            
            if prediction324 == 0:
                _t1003 = self.parse_specialized_value()
                specialized_value325 = _t1003
                _t1004 = logic_pb2.RelTerm(specialized_value=specialized_value325)
                _t1002 = _t1004
            else:
                raise ParseError(f"{'Unexpected token in rel_term'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t999 = _t1002
        result328 = _t999
        self._record_span(span_start327)
        return result328

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start330 = self._span_start()
        self.consume_literal('#')
        _t1005 = self.parse_value()
        value329 = _t1005
        result331 = value329
        self._record_span(span_start330)
        return result331

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start338 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('relatom')
        self._push_path(3)
        _t1006 = self.parse_name()
        name332 = _t1006
        self._pop_path()
        self._push_path(2)
        xs333 = []
        cond334 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        idx336 = 0
        while cond334:
            self._push_path(idx336)
            _t1007 = self.parse_rel_term()
            item335 = _t1007
            self._pop_path()
            xs333.append(item335)
            idx336 = (idx336 + 1)
            cond334 = (((((((((((self.match_lookahead_literal('#', 0) or self.match_lookahead_literal('(', 0)) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('SYMBOL', 0)) or self.match_lookahead_terminal('UINT128', 0))
        self._pop_path()
        rel_terms337 = xs333
        self.consume_literal(')')
        _t1008 = logic_pb2.RelAtom(name=name332, terms=rel_terms337)
        result339 = _t1008
        self._record_span(span_start338)
        return result339

    def parse_cast(self) -> logic_pb2.Cast:
        span_start342 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('cast')
        self._push_path(2)
        _t1009 = self.parse_term()
        term340 = _t1009
        self._pop_path()
        self._push_path(3)
        _t1010 = self.parse_term()
        term_3341 = _t1010
        self._pop_path()
        self.consume_literal(')')
        _t1011 = logic_pb2.Cast(input=term340, result=term_3341)
        result343 = _t1011
        self._record_span(span_start342)
        return result343

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        span_start349 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('attrs')
        xs344 = []
        cond345 = self.match_lookahead_literal('(', 0)
        idx347 = 0
        while cond345:
            self._push_path(idx347)
            _t1012 = self.parse_attribute()
            item346 = _t1012
            self._pop_path()
            xs344.append(item346)
            idx347 = (idx347 + 1)
            cond345 = self.match_lookahead_literal('(', 0)
        attributes348 = xs344
        self.consume_literal(')')
        result350 = attributes348
        self._record_span(span_start349)
        return result350

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start357 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('attribute')
        self._push_path(1)
        _t1013 = self.parse_name()
        name351 = _t1013
        self._pop_path()
        self._push_path(2)
        xs352 = []
        cond353 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        idx355 = 0
        while cond353:
            self._push_path(idx355)
            _t1014 = self.parse_value()
            item354 = _t1014
            self._pop_path()
            xs352.append(item354)
            idx355 = (idx355 + 1)
            cond353 = (((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('false', 0)) or self.match_lookahead_literal('missing', 0)) or self.match_lookahead_literal('true', 0)) or self.match_lookahead_terminal('DECIMAL', 0)) or self.match_lookahead_terminal('FLOAT', 0)) or self.match_lookahead_terminal('INT', 0)) or self.match_lookahead_terminal('INT128', 0)) or self.match_lookahead_terminal('STRING', 0)) or self.match_lookahead_terminal('UINT128', 0))
        self._pop_path()
        values356 = xs352
        self.consume_literal(')')
        _t1015 = logic_pb2.Attribute(name=name351, args=values356)
        result358 = _t1015
        self._record_span(span_start357)
        return result358

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start365 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('algorithm')
        self._push_path(1)
        xs359 = []
        cond360 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('UINT128', 0))
        idx362 = 0
        while cond360:
            self._push_path(idx362)
            _t1016 = self.parse_relation_id()
            item361 = _t1016
            self._pop_path()
            xs359.append(item361)
            idx362 = (idx362 + 1)
            cond360 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('UINT128', 0))
        self._pop_path()
        relation_ids363 = xs359
        self._push_path(2)
        _t1017 = self.parse_script()
        script364 = _t1017
        self._pop_path()
        self.consume_literal(')')
        _t1018 = logic_pb2.Algorithm(body=script364)
        getattr(_t1018, 'global').extend(relation_ids363)
        result366 = _t1018
        self._record_span(span_start365)
        return result366

    def parse_script(self) -> logic_pb2.Script:
        span_start372 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('script')
        self._push_path(1)
        xs367 = []
        cond368 = self.match_lookahead_literal('(', 0)
        idx370 = 0
        while cond368:
            self._push_path(idx370)
            _t1019 = self.parse_construct()
            item369 = _t1019
            self._pop_path()
            xs367.append(item369)
            idx370 = (idx370 + 1)
            cond368 = self.match_lookahead_literal('(', 0)
        self._pop_path()
        constructs371 = xs367
        self.consume_literal(')')
        _t1020 = logic_pb2.Script(constructs=constructs371)
        result373 = _t1020
        self._record_span(span_start372)
        return result373

    def parse_construct(self) -> logic_pb2.Construct:
        span_start377 = self._span_start()
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('upsert', 1):
                _t1022 = 1
            else:
                
                if self.match_lookahead_literal('monus', 1):
                    _t1023 = 1
                else:
                    
                    if self.match_lookahead_literal('monoid', 1):
                        _t1024 = 1
                    else:
                        
                        if self.match_lookahead_literal('loop', 1):
                            _t1025 = 0
                        else:
                            
                            if self.match_lookahead_literal('break', 1):
                                _t1026 = 1
                            else:
                                
                                if self.match_lookahead_literal('assign', 1):
                                    _t1027 = 1
                                else:
                                    _t1027 = -1
                                _t1026 = _t1027
                            _t1025 = _t1026
                        _t1024 = _t1025
                    _t1023 = _t1024
                _t1022 = _t1023
            _t1021 = _t1022
        else:
            _t1021 = -1
        prediction374 = _t1021
        
        if prediction374 == 1:
            _t1029 = self.parse_instruction()
            instruction376 = _t1029
            _t1030 = logic_pb2.Construct(instruction=instruction376)
            _t1028 = _t1030
        else:
            
            if prediction374 == 0:
                _t1032 = self.parse_loop()
                loop375 = _t1032
                _t1033 = logic_pb2.Construct(loop=loop375)
                _t1031 = _t1033
            else:
                raise ParseError(f"{'Unexpected token in construct'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1028 = _t1031
        result378 = _t1028
        self._record_span(span_start377)
        return result378

    def parse_loop(self) -> logic_pb2.Loop:
        span_start381 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('loop')
        self._push_path(1)
        _t1034 = self.parse_init()
        init379 = _t1034
        self._pop_path()
        self._push_path(2)
        _t1035 = self.parse_script()
        script380 = _t1035
        self._pop_path()
        self.consume_literal(')')
        _t1036 = logic_pb2.Loop(init=init379, body=script380)
        result382 = _t1036
        self._record_span(span_start381)
        return result382

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        span_start388 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('init')
        xs383 = []
        cond384 = self.match_lookahead_literal('(', 0)
        idx386 = 0
        while cond384:
            self._push_path(idx386)
            _t1037 = self.parse_instruction()
            item385 = _t1037
            self._pop_path()
            xs383.append(item385)
            idx386 = (idx386 + 1)
            cond384 = self.match_lookahead_literal('(', 0)
        instructions387 = xs383
        self.consume_literal(')')
        result389 = instructions387
        self._record_span(span_start388)
        return result389

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start396 = self._span_start()
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('upsert', 1):
                _t1039 = 1
            else:
                
                if self.match_lookahead_literal('monus', 1):
                    _t1040 = 4
                else:
                    
                    if self.match_lookahead_literal('monoid', 1):
                        _t1041 = 3
                    else:
                        
                        if self.match_lookahead_literal('break', 1):
                            _t1042 = 2
                        else:
                            
                            if self.match_lookahead_literal('assign', 1):
                                _t1043 = 0
                            else:
                                _t1043 = -1
                            _t1042 = _t1043
                        _t1041 = _t1042
                    _t1040 = _t1041
                _t1039 = _t1040
            _t1038 = _t1039
        else:
            _t1038 = -1
        prediction390 = _t1038
        
        if prediction390 == 4:
            _t1045 = self.parse_monus_def()
            monus_def395 = _t1045
            _t1046 = logic_pb2.Instruction(monus_def=monus_def395)
            _t1044 = _t1046
        else:
            
            if prediction390 == 3:
                _t1048 = self.parse_monoid_def()
                monoid_def394 = _t1048
                _t1049 = logic_pb2.Instruction(monoid_def=monoid_def394)
                _t1047 = _t1049
            else:
                
                if prediction390 == 2:
                    _t1051 = self.parse_break()
                    break393 = _t1051
                    _t1052 = logic_pb2.Instruction()
                    getattr(_t1052, 'break').CopyFrom(break393)
                    _t1050 = _t1052
                else:
                    
                    if prediction390 == 1:
                        _t1054 = self.parse_upsert()
                        upsert392 = _t1054
                        _t1055 = logic_pb2.Instruction(upsert=upsert392)
                        _t1053 = _t1055
                    else:
                        
                        if prediction390 == 0:
                            _t1057 = self.parse_assign()
                            assign391 = _t1057
                            _t1058 = logic_pb2.Instruction(assign=assign391)
                            _t1056 = _t1058
                        else:
                            raise ParseError(f"{'Unexpected token in instruction'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1053 = _t1056
                    _t1050 = _t1053
                _t1047 = _t1050
            _t1044 = _t1047
        result397 = _t1044
        self._record_span(span_start396)
        return result397

    def parse_assign(self) -> logic_pb2.Assign:
        span_start401 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('assign')
        self._push_path(1)
        _t1059 = self.parse_relation_id()
        relation_id398 = _t1059
        self._pop_path()
        self._push_path(2)
        _t1060 = self.parse_abstraction()
        abstraction399 = _t1060
        self._pop_path()
        self._push_path(3)
        
        if self.match_lookahead_literal('(', 0):
            _t1062 = self.parse_attrs()
            _t1061 = _t1062
        else:
            _t1061 = None
        attrs400 = _t1061
        self._pop_path()
        self.consume_literal(')')
        _t1063 = logic_pb2.Assign(name=relation_id398, body=abstraction399, attrs=(attrs400 if attrs400 is not None else []))
        result402 = _t1063
        self._record_span(span_start401)
        return result402

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start406 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('upsert')
        self._push_path(1)
        _t1064 = self.parse_relation_id()
        relation_id403 = _t1064
        self._pop_path()
        _t1065 = self.parse_abstraction_with_arity()
        abstraction_with_arity404 = _t1065
        self._push_path(3)
        
        if self.match_lookahead_literal('(', 0):
            _t1067 = self.parse_attrs()
            _t1066 = _t1067
        else:
            _t1066 = None
        attrs405 = _t1066
        self._pop_path()
        self.consume_literal(')')
        _t1068 = logic_pb2.Upsert(name=relation_id403, body=abstraction_with_arity404[0], attrs=(attrs405 if attrs405 is not None else []), value_arity=abstraction_with_arity404[1])
        result407 = _t1068
        self._record_span(span_start406)
        return result407

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        span_start410 = self._span_start()
        self.consume_literal('(')
        _t1069 = self.parse_bindings()
        bindings408 = _t1069
        _t1070 = self.parse_formula()
        formula409 = _t1070
        self.consume_literal(')')
        _t1071 = logic_pb2.Abstraction(vars=(list(bindings408[0]) + list(bindings408[1] if bindings408[1] is not None else [])), value=formula409)
        result411 = (_t1071, len(bindings408[1]),)
        self._record_span(span_start410)
        return result411

    def parse_break(self) -> logic_pb2.Break:
        span_start415 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('break')
        self._push_path(1)
        _t1072 = self.parse_relation_id()
        relation_id412 = _t1072
        self._pop_path()
        self._push_path(2)
        _t1073 = self.parse_abstraction()
        abstraction413 = _t1073
        self._pop_path()
        self._push_path(3)
        
        if self.match_lookahead_literal('(', 0):
            _t1075 = self.parse_attrs()
            _t1074 = _t1075
        else:
            _t1074 = None
        attrs414 = _t1074
        self._pop_path()
        self.consume_literal(')')
        _t1076 = logic_pb2.Break(name=relation_id412, body=abstraction413, attrs=(attrs414 if attrs414 is not None else []))
        result416 = _t1076
        self._record_span(span_start415)
        return result416

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start421 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('monoid')
        self._push_path(1)
        _t1077 = self.parse_monoid()
        monoid417 = _t1077
        self._pop_path()
        self._push_path(2)
        _t1078 = self.parse_relation_id()
        relation_id418 = _t1078
        self._pop_path()
        _t1079 = self.parse_abstraction_with_arity()
        abstraction_with_arity419 = _t1079
        self._push_path(4)
        
        if self.match_lookahead_literal('(', 0):
            _t1081 = self.parse_attrs()
            _t1080 = _t1081
        else:
            _t1080 = None
        attrs420 = _t1080
        self._pop_path()
        self.consume_literal(')')
        _t1082 = logic_pb2.MonoidDef(monoid=monoid417, name=relation_id418, body=abstraction_with_arity419[0], attrs=(attrs420 if attrs420 is not None else []), value_arity=abstraction_with_arity419[1])
        result422 = _t1082
        self._record_span(span_start421)
        return result422

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start428 = self._span_start()
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('sum', 1):
                _t1084 = 3
            else:
                
                if self.match_lookahead_literal('or', 1):
                    _t1085 = 0
                else:
                    
                    if self.match_lookahead_literal('min', 1):
                        _t1086 = 1
                    else:
                        
                        if self.match_lookahead_literal('max', 1):
                            _t1087 = 2
                        else:
                            _t1087 = -1
                        _t1086 = _t1087
                    _t1085 = _t1086
                _t1084 = _t1085
            _t1083 = _t1084
        else:
            _t1083 = -1
        prediction423 = _t1083
        
        if prediction423 == 3:
            _t1089 = self.parse_sum_monoid()
            sum_monoid427 = _t1089
            _t1090 = logic_pb2.Monoid(sum_monoid=sum_monoid427)
            _t1088 = _t1090
        else:
            
            if prediction423 == 2:
                _t1092 = self.parse_max_monoid()
                max_monoid426 = _t1092
                _t1093 = logic_pb2.Monoid(max_monoid=max_monoid426)
                _t1091 = _t1093
            else:
                
                if prediction423 == 1:
                    _t1095 = self.parse_min_monoid()
                    min_monoid425 = _t1095
                    _t1096 = logic_pb2.Monoid(min_monoid=min_monoid425)
                    _t1094 = _t1096
                else:
                    
                    if prediction423 == 0:
                        _t1098 = self.parse_or_monoid()
                        or_monoid424 = _t1098
                        _t1099 = logic_pb2.Monoid(or_monoid=or_monoid424)
                        _t1097 = _t1099
                    else:
                        raise ParseError(f"{'Unexpected token in monoid'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1094 = _t1097
                _t1091 = _t1094
            _t1088 = _t1091
        result429 = _t1088
        self._record_span(span_start428)
        return result429

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start430 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('or')
        self.consume_literal(')')
        _t1100 = logic_pb2.OrMonoid()
        result431 = _t1100
        self._record_span(span_start430)
        return result431

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start433 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('min')
        self._push_path(1)
        _t1101 = self.parse_type()
        type432 = _t1101
        self._pop_path()
        self.consume_literal(')')
        _t1102 = logic_pb2.MinMonoid(type=type432)
        result434 = _t1102
        self._record_span(span_start433)
        return result434

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start436 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('max')
        self._push_path(1)
        _t1103 = self.parse_type()
        type435 = _t1103
        self._pop_path()
        self.consume_literal(')')
        _t1104 = logic_pb2.MaxMonoid(type=type435)
        result437 = _t1104
        self._record_span(span_start436)
        return result437

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start439 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('sum')
        self._push_path(1)
        _t1105 = self.parse_type()
        type438 = _t1105
        self._pop_path()
        self.consume_literal(')')
        _t1106 = logic_pb2.SumMonoid(type=type438)
        result440 = _t1106
        self._record_span(span_start439)
        return result440

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start445 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('monus')
        self._push_path(1)
        _t1107 = self.parse_monoid()
        monoid441 = _t1107
        self._pop_path()
        self._push_path(2)
        _t1108 = self.parse_relation_id()
        relation_id442 = _t1108
        self._pop_path()
        _t1109 = self.parse_abstraction_with_arity()
        abstraction_with_arity443 = _t1109
        self._push_path(4)
        
        if self.match_lookahead_literal('(', 0):
            _t1111 = self.parse_attrs()
            _t1110 = _t1111
        else:
            _t1110 = None
        attrs444 = _t1110
        self._pop_path()
        self.consume_literal(')')
        _t1112 = logic_pb2.MonusDef(monoid=monoid441, name=relation_id442, body=abstraction_with_arity443[0], attrs=(attrs444 if attrs444 is not None else []), value_arity=abstraction_with_arity443[1])
        result446 = _t1112
        self._record_span(span_start445)
        return result446

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start451 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('functional_dependency')
        self._push_path(2)
        _t1113 = self.parse_relation_id()
        relation_id447 = _t1113
        self._pop_path()
        _t1114 = self.parse_abstraction()
        abstraction448 = _t1114
        _t1115 = self.parse_functional_dependency_keys()
        functional_dependency_keys449 = _t1115
        _t1116 = self.parse_functional_dependency_values()
        functional_dependency_values450 = _t1116
        self.consume_literal(')')
        _t1117 = logic_pb2.FunctionalDependency(guard=abstraction448, keys=functional_dependency_keys449, values=functional_dependency_values450)
        _t1118 = logic_pb2.Constraint(name=relation_id447, functional_dependency=_t1117)
        result452 = _t1118
        self._record_span(span_start451)
        return result452

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        span_start458 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('keys')
        xs453 = []
        cond454 = self.match_lookahead_terminal('SYMBOL', 0)
        idx456 = 0
        while cond454:
            self._push_path(idx456)
            _t1119 = self.parse_var()
            item455 = _t1119
            self._pop_path()
            xs453.append(item455)
            idx456 = (idx456 + 1)
            cond454 = self.match_lookahead_terminal('SYMBOL', 0)
        vars457 = xs453
        self.consume_literal(')')
        result459 = vars457
        self._record_span(span_start458)
        return result459

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        span_start465 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('values')
        xs460 = []
        cond461 = self.match_lookahead_terminal('SYMBOL', 0)
        idx463 = 0
        while cond461:
            self._push_path(idx463)
            _t1120 = self.parse_var()
            item462 = _t1120
            self._pop_path()
            xs460.append(item462)
            idx463 = (idx463 + 1)
            cond461 = self.match_lookahead_terminal('SYMBOL', 0)
        vars464 = xs460
        self.consume_literal(')')
        result466 = vars464
        self._record_span(span_start465)
        return result466

    def parse_data(self) -> logic_pb2.Data:
        span_start471 = self._span_start()
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('rel_edb', 1):
                _t1122 = 0
            else:
                
                if self.match_lookahead_literal('csv_data', 1):
                    _t1123 = 2
                else:
                    
                    if self.match_lookahead_literal('betree_relation', 1):
                        _t1124 = 1
                    else:
                        _t1124 = -1
                    _t1123 = _t1124
                _t1122 = _t1123
            _t1121 = _t1122
        else:
            _t1121 = -1
        prediction467 = _t1121
        
        if prediction467 == 2:
            _t1126 = self.parse_csv_data()
            csv_data470 = _t1126
            _t1127 = logic_pb2.Data(csv_data=csv_data470)
            _t1125 = _t1127
        else:
            
            if prediction467 == 1:
                _t1129 = self.parse_betree_relation()
                betree_relation469 = _t1129
                _t1130 = logic_pb2.Data(betree_relation=betree_relation469)
                _t1128 = _t1130
            else:
                
                if prediction467 == 0:
                    _t1132 = self.parse_rel_edb()
                    rel_edb468 = _t1132
                    _t1133 = logic_pb2.Data(rel_edb=rel_edb468)
                    _t1131 = _t1133
                else:
                    raise ParseError(f"{'Unexpected token in data'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t1128 = _t1131
            _t1125 = _t1128
        result472 = _t1125
        self._record_span(span_start471)
        return result472

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        span_start476 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('rel_edb')
        self._push_path(1)
        _t1134 = self.parse_relation_id()
        relation_id473 = _t1134
        self._pop_path()
        self._push_path(2)
        _t1135 = self.parse_rel_edb_path()
        rel_edb_path474 = _t1135
        self._pop_path()
        self._push_path(3)
        _t1136 = self.parse_rel_edb_types()
        rel_edb_types475 = _t1136
        self._pop_path()
        self.consume_literal(')')
        _t1137 = logic_pb2.RelEDB(target_id=relation_id473, path=rel_edb_path474, types=rel_edb_types475)
        result477 = _t1137
        self._record_span(span_start476)
        return result477

    def parse_rel_edb_path(self) -> Sequence[str]:
        span_start483 = self._span_start()
        self.consume_literal('[')
        xs478 = []
        cond479 = self.match_lookahead_terminal('STRING', 0)
        idx481 = 0
        while cond479:
            self._push_path(idx481)
            item480 = self.consume_terminal('STRING')
            self._pop_path()
            xs478.append(item480)
            idx481 = (idx481 + 1)
            cond479 = self.match_lookahead_terminal('STRING', 0)
        strings482 = xs478
        self.consume_literal(']')
        result484 = strings482
        self._record_span(span_start483)
        return result484

    def parse_rel_edb_types(self) -> Sequence[logic_pb2.Type]:
        span_start490 = self._span_start()
        self.consume_literal('[')
        xs485 = []
        cond486 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        idx488 = 0
        while cond486:
            self._push_path(idx488)
            _t1138 = self.parse_type()
            item487 = _t1138
            self._pop_path()
            xs485.append(item487)
            idx488 = (idx488 + 1)
            cond486 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types489 = xs485
        self.consume_literal(']')
        result491 = types489
        self._record_span(span_start490)
        return result491

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start494 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('betree_relation')
        self._push_path(1)
        _t1139 = self.parse_relation_id()
        relation_id492 = _t1139
        self._pop_path()
        self._push_path(2)
        _t1140 = self.parse_betree_info()
        betree_info493 = _t1140
        self._pop_path()
        self.consume_literal(')')
        _t1141 = logic_pb2.BeTreeRelation(name=relation_id492, relation_info=betree_info493)
        result495 = _t1141
        self._record_span(span_start494)
        return result495

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start499 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('betree_info')
        _t1142 = self.parse_betree_info_key_types()
        betree_info_key_types496 = _t1142
        _t1143 = self.parse_betree_info_value_types()
        betree_info_value_types497 = _t1143
        _t1144 = self.parse_config_dict()
        config_dict498 = _t1144
        self.consume_literal(')')
        _t1145 = self.construct_betree_info(betree_info_key_types496, betree_info_value_types497, config_dict498)
        result500 = _t1145
        self._record_span(span_start499)
        return result500

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        span_start506 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('key_types')
        xs501 = []
        cond502 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        idx504 = 0
        while cond502:
            self._push_path(idx504)
            _t1146 = self.parse_type()
            item503 = _t1146
            self._pop_path()
            xs501.append(item503)
            idx504 = (idx504 + 1)
            cond502 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types505 = xs501
        self.consume_literal(')')
        result507 = types505
        self._record_span(span_start506)
        return result507

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        span_start513 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('value_types')
        xs508 = []
        cond509 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        idx511 = 0
        while cond509:
            self._push_path(idx511)
            _t1147 = self.parse_type()
            item510 = _t1147
            self._pop_path()
            xs508.append(item510)
            idx511 = (idx511 + 1)
            cond509 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        types512 = xs508
        self.consume_literal(')')
        result514 = types512
        self._record_span(span_start513)
        return result514

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start519 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('csv_data')
        self._push_path(1)
        _t1148 = self.parse_csvlocator()
        csvlocator515 = _t1148
        self._pop_path()
        self._push_path(2)
        _t1149 = self.parse_csv_config()
        csv_config516 = _t1149
        self._pop_path()
        self._push_path(3)
        _t1150 = self.parse_csv_columns()
        csv_columns517 = _t1150
        self._pop_path()
        self._push_path(4)
        _t1151 = self.parse_csv_asof()
        csv_asof518 = _t1151
        self._pop_path()
        self.consume_literal(')')
        _t1152 = logic_pb2.CSVData(locator=csvlocator515, config=csv_config516, columns=csv_columns517, asof=csv_asof518)
        result520 = _t1152
        self._record_span(span_start519)
        return result520

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start523 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('csv_locator')
        self._push_path(1)
        
        if (self.match_lookahead_literal('(', 0) and self.match_lookahead_literal('paths', 1)):
            _t1154 = self.parse_csv_locator_paths()
            _t1153 = _t1154
        else:
            _t1153 = None
        csv_locator_paths521 = _t1153
        self._pop_path()
        
        if self.match_lookahead_literal('(', 0):
            _t1156 = self.parse_csv_locator_inline_data()
            _t1155 = _t1156
        else:
            _t1155 = None
        csv_locator_inline_data522 = _t1155
        self.consume_literal(')')
        _t1157 = logic_pb2.CSVLocator(paths=(csv_locator_paths521 if csv_locator_paths521 is not None else []), inline_data=(csv_locator_inline_data522 if csv_locator_inline_data522 is not None else '').encode())
        result524 = _t1157
        self._record_span(span_start523)
        return result524

    def parse_csv_locator_paths(self) -> Sequence[str]:
        span_start530 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('paths')
        xs525 = []
        cond526 = self.match_lookahead_terminal('STRING', 0)
        idx528 = 0
        while cond526:
            self._push_path(idx528)
            item527 = self.consume_terminal('STRING')
            self._pop_path()
            xs525.append(item527)
            idx528 = (idx528 + 1)
            cond526 = self.match_lookahead_terminal('STRING', 0)
        strings529 = xs525
        self.consume_literal(')')
        result531 = strings529
        self._record_span(span_start530)
        return result531

    def parse_csv_locator_inline_data(self) -> str:
        span_start533 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('inline_data')
        string532 = self.consume_terminal('STRING')
        self.consume_literal(')')
        result534 = string532
        self._record_span(span_start533)
        return result534

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start536 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('csv_config')
        _t1158 = self.parse_config_dict()
        config_dict535 = _t1158
        self.consume_literal(')')
        _t1159 = self.construct_csv_config(config_dict535)
        result537 = _t1159
        self._record_span(span_start536)
        return result537

    def parse_csv_columns(self) -> Sequence[logic_pb2.CSVColumn]:
        span_start543 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('columns')
        xs538 = []
        cond539 = self.match_lookahead_literal('(', 0)
        idx541 = 0
        while cond539:
            self._push_path(idx541)
            _t1160 = self.parse_csv_column()
            item540 = _t1160
            self._pop_path()
            xs538.append(item540)
            idx541 = (idx541 + 1)
            cond539 = self.match_lookahead_literal('(', 0)
        csv_columns542 = xs538
        self.consume_literal(')')
        result544 = csv_columns542
        self._record_span(span_start543)
        return result544

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        span_start552 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('column')
        self._push_path(1)
        string545 = self.consume_terminal('STRING')
        self._pop_path()
        self._push_path(2)
        _t1161 = self.parse_relation_id()
        relation_id546 = _t1161
        self._pop_path()
        self.consume_literal('[')
        self._push_path(3)
        xs547 = []
        cond548 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        idx550 = 0
        while cond548:
            self._push_path(idx550)
            _t1162 = self.parse_type()
            item549 = _t1162
            self._pop_path()
            xs547.append(item549)
            idx550 = (idx550 + 1)
            cond548 = ((((((((((self.match_lookahead_literal('(', 0) or self.match_lookahead_literal('BOOLEAN', 0)) or self.match_lookahead_literal('DATE', 0)) or self.match_lookahead_literal('DATETIME', 0)) or self.match_lookahead_literal('FLOAT', 0)) or self.match_lookahead_literal('INT', 0)) or self.match_lookahead_literal('INT128', 0)) or self.match_lookahead_literal('MISSING', 0)) or self.match_lookahead_literal('STRING', 0)) or self.match_lookahead_literal('UINT128', 0)) or self.match_lookahead_literal('UNKNOWN', 0))
        self._pop_path()
        types551 = xs547
        self.consume_literal(']')
        self.consume_literal(')')
        _t1163 = logic_pb2.CSVColumn(column_name=string545, target_id=relation_id546, types=types551)
        result553 = _t1163
        self._record_span(span_start552)
        return result553

    def parse_csv_asof(self) -> str:
        span_start555 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('asof')
        string554 = self.consume_terminal('STRING')
        self.consume_literal(')')
        result556 = string554
        self._record_span(span_start555)
        return result556

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start558 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('undefine')
        self._push_path(1)
        _t1164 = self.parse_fragment_id()
        fragment_id557 = _t1164
        self._pop_path()
        self.consume_literal(')')
        _t1165 = transactions_pb2.Undefine(fragment_id=fragment_id557)
        result559 = _t1165
        self._record_span(span_start558)
        return result559

    def parse_context(self) -> transactions_pb2.Context:
        span_start565 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('context')
        self._push_path(1)
        xs560 = []
        cond561 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('UINT128', 0))
        idx563 = 0
        while cond561:
            self._push_path(idx563)
            _t1166 = self.parse_relation_id()
            item562 = _t1166
            self._pop_path()
            xs560.append(item562)
            idx563 = (idx563 + 1)
            cond561 = (self.match_lookahead_literal(':', 0) or self.match_lookahead_terminal('UINT128', 0))
        self._pop_path()
        relation_ids564 = xs560
        self.consume_literal(')')
        _t1167 = transactions_pb2.Context(relations=relation_ids564)
        result566 = _t1167
        self._record_span(span_start565)
        return result566

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        span_start572 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('reads')
        xs567 = []
        cond568 = self.match_lookahead_literal('(', 0)
        idx570 = 0
        while cond568:
            self._push_path(idx570)
            _t1168 = self.parse_read()
            item569 = _t1168
            self._pop_path()
            xs567.append(item569)
            idx570 = (idx570 + 1)
            cond568 = self.match_lookahead_literal('(', 0)
        reads571 = xs567
        self.consume_literal(')')
        result573 = reads571
        self._record_span(span_start572)
        return result573

    def parse_read(self) -> transactions_pb2.Read:
        span_start580 = self._span_start()
        
        if self.match_lookahead_literal('(', 0):
            
            if self.match_lookahead_literal('what_if', 1):
                _t1170 = 2
            else:
                
                if self.match_lookahead_literal('output', 1):
                    _t1171 = 1
                else:
                    
                    if self.match_lookahead_literal('export', 1):
                        _t1172 = 4
                    else:
                        
                        if self.match_lookahead_literal('demand', 1):
                            _t1173 = 0
                        else:
                            
                            if self.match_lookahead_literal('abort', 1):
                                _t1174 = 3
                            else:
                                _t1174 = -1
                            _t1173 = _t1174
                        _t1172 = _t1173
                    _t1171 = _t1172
                _t1170 = _t1171
            _t1169 = _t1170
        else:
            _t1169 = -1
        prediction574 = _t1169
        
        if prediction574 == 4:
            _t1176 = self.parse_export()
            export579 = _t1176
            _t1177 = transactions_pb2.Read(export=export579)
            _t1175 = _t1177
        else:
            
            if prediction574 == 3:
                _t1179 = self.parse_abort()
                abort578 = _t1179
                _t1180 = transactions_pb2.Read(abort=abort578)
                _t1178 = _t1180
            else:
                
                if prediction574 == 2:
                    _t1182 = self.parse_what_if()
                    what_if577 = _t1182
                    _t1183 = transactions_pb2.Read(what_if=what_if577)
                    _t1181 = _t1183
                else:
                    
                    if prediction574 == 1:
                        _t1185 = self.parse_output()
                        output576 = _t1185
                        _t1186 = transactions_pb2.Read(output=output576)
                        _t1184 = _t1186
                    else:
                        
                        if prediction574 == 0:
                            _t1188 = self.parse_demand()
                            demand575 = _t1188
                            _t1189 = transactions_pb2.Read(demand=demand575)
                            _t1187 = _t1189
                        else:
                            raise ParseError(f"{'Unexpected token in read'}: {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1184 = _t1187
                    _t1181 = _t1184
                _t1178 = _t1181
            _t1175 = _t1178
        result581 = _t1175
        self._record_span(span_start580)
        return result581

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start583 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('demand')
        self._push_path(1)
        _t1190 = self.parse_relation_id()
        relation_id582 = _t1190
        self._pop_path()
        self.consume_literal(')')
        _t1191 = transactions_pb2.Demand(relation_id=relation_id582)
        result584 = _t1191
        self._record_span(span_start583)
        return result584

    def parse_output(self) -> transactions_pb2.Output:
        span_start587 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('output')
        self._push_path(1)
        _t1192 = self.parse_name()
        name585 = _t1192
        self._pop_path()
        self._push_path(2)
        _t1193 = self.parse_relation_id()
        relation_id586 = _t1193
        self._pop_path()
        self.consume_literal(')')
        _t1194 = transactions_pb2.Output(name=name585, relation_id=relation_id586)
        result588 = _t1194
        self._record_span(span_start587)
        return result588

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start591 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('what_if')
        self._push_path(1)
        _t1195 = self.parse_name()
        name589 = _t1195
        self._pop_path()
        self._push_path(2)
        _t1196 = self.parse_epoch()
        epoch590 = _t1196
        self._pop_path()
        self.consume_literal(')')
        _t1197 = transactions_pb2.WhatIf(branch=name589, epoch=epoch590)
        result592 = _t1197
        self._record_span(span_start591)
        return result592

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start595 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('abort')
        self._push_path(1)
        
        if (self.match_lookahead_literal(':', 0) and self.match_lookahead_terminal('SYMBOL', 1)):
            _t1199 = self.parse_name()
            _t1198 = _t1199
        else:
            _t1198 = None
        name593 = _t1198
        self._pop_path()
        self._push_path(2)
        _t1200 = self.parse_relation_id()
        relation_id594 = _t1200
        self._pop_path()
        self.consume_literal(')')
        _t1201 = transactions_pb2.Abort(name=(name593 if name593 is not None else 'abort'), relation_id=relation_id594)
        result596 = _t1201
        self._record_span(span_start595)
        return result596

    def parse_export(self) -> transactions_pb2.Export:
        span_start598 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('export')
        self._push_path(1)
        _t1202 = self.parse_export_csv_config()
        export_csv_config597 = _t1202
        self._pop_path()
        self.consume_literal(')')
        _t1203 = transactions_pb2.Export(csv_config=export_csv_config597)
        result599 = _t1203
        self._record_span(span_start598)
        return result599

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start603 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('export_csv_config')
        _t1204 = self.parse_export_csv_path()
        export_csv_path600 = _t1204
        _t1205 = self.parse_export_csv_columns()
        export_csv_columns601 = _t1205
        _t1206 = self.parse_config_dict()
        config_dict602 = _t1206
        self.consume_literal(')')
        _t1207 = self.export_csv_config(export_csv_path600, export_csv_columns601, config_dict602)
        result604 = _t1207
        self._record_span(span_start603)
        return result604

    def parse_export_csv_path(self) -> str:
        span_start606 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('path')
        string605 = self.consume_terminal('STRING')
        self.consume_literal(')')
        result607 = string605
        self._record_span(span_start606)
        return result607

    def parse_export_csv_columns(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        span_start613 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('columns')
        xs608 = []
        cond609 = self.match_lookahead_literal('(', 0)
        idx611 = 0
        while cond609:
            self._push_path(idx611)
            _t1208 = self.parse_export_csv_column()
            item610 = _t1208
            self._pop_path()
            xs608.append(item610)
            idx611 = (idx611 + 1)
            cond609 = self.match_lookahead_literal('(', 0)
        export_csv_columns612 = xs608
        self.consume_literal(')')
        result614 = export_csv_columns612
        self._record_span(span_start613)
        return result614

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start617 = self._span_start()
        self.consume_literal('(')
        self.consume_literal('column')
        self._push_path(1)
        string615 = self.consume_terminal('STRING')
        self._pop_path()
        self._push_path(2)
        _t1209 = self.parse_relation_id()
        relation_id616 = _t1209
        self._pop_path()
        self.consume_literal(')')
        _t1210 = transactions_pb2.ExportCSVColumn(column_name=string615, column_data=relation_id616)
        result618 = _t1210
        self._record_span(span_start617)
        return result618


def parse(input_str: str) -> Tuple[Any, Dict[Tuple[int, ...], Span]]:
    """Parse input string and return (parse tree, provenance map)."""
    lexer = Lexer(input_str)
    parser = Parser(lexer.tokens, input_str)
    result = parser.parse_transaction()
    # Check for unconsumed tokens (except EOF)
    if parser.pos < len(parser.tokens):
        remaining_token = parser.lookahead(0)
        if remaining_token.type != '$':
            raise ParseError(f"Unexpected token at end of input: {remaining_token}")
    return result, parser.provenance
