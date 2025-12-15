"""Python-specific parser code generation.

This module generates LL(k) recursive-descent parsers in Python from grammars.
Handles Python-specific code generation including:
- Prologue (imports, Token, Lexer, Parser class with helpers)
- Parse method generation
- Epilogue (parse function)
"""

import re
from typing import List, Optional, Set

from .grammar import Grammar, Nonterminal, get_literals
from .codegen_python import generate_python_def
from .parser_gen import generate_parse_functions


# Template for the generated parser prologue
PROLOGUE_TEMPLATE = '''\
"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.

{command_line_comment}"""

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
{token_specs}        ]

        whitespace_re = re.compile(r'\\s+')
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
                raise ParseError(f'Unexpected character at position {{{{self.pos}}}}: {{{{self.input[self.pos]!r}}}}')

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
            raise ValueError(f'Invalid decimal format: {{{{d}}}}')
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
        self.id_to_debuginfo = {{}}
        self._current_fragment_id = None
        self._relation_id_to_name = {{}}

    def lookahead(self, k: int = 0) -> Token:
        """Get lookahead token at offset k."""
        idx = self.pos + k
        return self.tokens[idx] if idx < len(self.tokens) else Token('$', '', -1)

    def consume_literal(self, expected: str) -> None:
        """Consume a literal token."""
        if not self.match_lookahead_literal(expected, 0):
            token = self.lookahead(0)
            raise ParseError(f'Expected literal {{expected!r}} but got {{token.type}}=`{{token.value!r}}` at position {{token.pos}}')
        self.pos += 1

    def consume_terminal(self, expected: str) -> Any:
        """Consume a terminal token and return parsed value."""
        if not self.match_lookahead_terminal(expected, 0):
            token = self.lookahead(0)
            raise ParseError(f'Expected terminal {{expected}} but got {{token.type}}=`{{token.value!r}}` at position {{token.pos}}')
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
        self._relation_id_to_name[(relation_id.id_low, relation_id.id_high)] = name

        return relation_id

    def construct_configure(self, config_dict: List[Tuple[str, logic_pb2.Value]]) -> Any:
        """Construct Configure from config dictionary."""
        # Build a dict from the list
        config = {{}}
        for k, v in config_dict:
            config[k] = v

        # Extract maintenance level
        maintenance_level_val = config.get('ivm.maintenance_level')
        if maintenance_level_val:
            if maintenance_level_val.HasField('string_value'):
                level_str = maintenance_level_val.string_value.upper()
                # Map short names to full enum names
                if level_str in ('OFF', 'AUTO', 'ALL'):
                    maintenance_level = f'MAINTENANCE_LEVEL_{{level_str}}'
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
        config = {{}}
        for k, v in config_dict:
            config[k] = v

        # Extract path string
        path_str = path

        # Build kwargs dict for optional fields
        kwargs = {{}}

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
                orig_name = self._relation_id_to_name.get((relation_id.id_low, relation_id.id_high))
                if orig_name:
                    ids.append(relation_id)
                    orig_names.append(orig_name)

            elif decl.HasField('algorithm'):
                # Extract global relation IDs from algorithm
                for relation_id in getattr(decl.algorithm, 'global'):
                    orig_name = self._relation_id_to_name.get((relation_id.id_low, relation_id.id_high))
                    if orig_name:
                        ids.append(relation_id)
                        orig_names.append(orig_name)


        # Create DebugInfo
        debug_info = fragments_pb2.DebugInfo(ids=ids, orig_names=orig_names)

        # Create and return Fragment
        return fragments_pb2.Fragment(id=fragment_id, declarations=declarations, debug_info=debug_info)
'''

EPILOGUE_TEMPLATE = '''

def parse(input_str: str) -> Any:
    """Parse input string and return parse tree."""
    lexer = Lexer(input_str)
    parser = Parser(lexer.tokens)
    result = parser.parse_{start_name}()
    # Check for unconsumed tokens (except EOF)
    if parser.pos < len(parser.tokens):
        remaining_token = parser.lookahead(0)
        if remaining_token.type != '$':
            raise ParseError(f"Unexpected token at end of input: {{remaining_token}}")
    return result
'''


def generate_parser_python(grammar: Grammar, reachable: Set[Nonterminal], command_line: Optional[str] = None, proto_messages=None) -> str:
    """Generate LL(k) recursive-descent parser in Python."""
    # Generate prologue (lexer, token, error, helper classes)
    prologue = _generate_prologue(grammar, command_line)

    # Create code generator with proto message info
    from .codegen_python import PythonCodeGenerator
    codegen = PythonCodeGenerator(proto_messages=proto_messages)

    # Generate parser methods as strings
    defns = generate_parse_functions(grammar)
    lines = []
    for defn in defns:
        lines.append("")
        lines.append(codegen.generate_def(defn, "    "))
    lines.append("")

    # Generate epilogue (parse function)
    epilogue = _generate_epilogue(grammar.start)

    return prologue + "\n".join(lines) + epilogue


def _generate_prologue(grammar: Grammar, command_line: Optional[str] = None) -> str:
    """Generate parser prologue with imports, token class, lexer, and parser class start."""
    # Build command line comment
    command_line_comment = f"\nCommand: {command_line}\n" if command_line else ""

    # Collect literals (sorted by length, longest first)
    literals = set()
    for rules_list in grammar.rules.values():
        for rule in rules_list:
            literals.update(get_literals(rule.rhs))
    sorted_literals = sorted(literals, key=lambda x: (-len(x.name), x.name))

    # Build token specs with literals first, then other tokens
    token_specs_lines = []

    # Add literals to token_specs
    for lit in sorted_literals:
        # Escape regex special characters in literal
        escaped = re.escape(lit.name)
        # Check if literal is alphanumeric (needs word boundary check)
        if lit.name[0].isalnum():
            # Add word boundary check to pattern
            pattern = f"{escaped}(?!\\w)"
        else:
            pattern = escaped
        token_specs_lines.append(
            f"            ('LITERAL', re.compile(r'{pattern}'), lambda x: x),"
        )

    # Add other tokens
    for token in grammar.tokens:
        token_specs_lines.append(
            f"            ('{token.name}', re.compile(r'{token.pattern}'), lambda x: Lexer.scan_{token.name.lower()}(x)),"
        )

    token_specs = "\n".join(token_specs_lines) + "\n" if token_specs_lines else ""

    return PROLOGUE_TEMPLATE.format(
        command_line_comment=command_line_comment,
        token_specs=token_specs,
    )


def _generate_epilogue(start: Nonterminal) -> str:
    """Generate parse function."""
    return EPILOGUE_TEMPLATE.format(start_name=start.name.lower())
