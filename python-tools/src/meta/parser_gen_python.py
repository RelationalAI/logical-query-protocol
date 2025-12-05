"""Python-specific parser code generation.

This module generates LL(k) recursive-descent parsers in Python from grammars.
Handles Python-specific code generation including:
- Prologue (imports, Token, Lexer, Parser class with helpers)
- Parse method generation
- Epilogue (parse function)
"""

from typing import Dict, List, Optional, Set

from .grammar import Grammar, Rule, Rhs, LitTerminal, NamedTerminal, Nonterminal, Star, Option, get_literals
from .target import Lambda, Call
from .codegen_python import generate_python_lines, generate_python_def
from .parser_gen import  _generate_parse_rhs_ir, generate_rules


def generate_parser_python(grammar: Grammar, reachable: Set[Nonterminal], command_line: Optional[str] = None) -> str:
    """Generate LL(k) recursive-descent parser in Python."""
    is_ll2, conflicts = grammar.check_ll_k(2)

    # Generate prologue (lexer, token, error, helper classes)
    prologue = _generate_prologue(grammar, is_ll2, conflicts, command_line)

    defns = generate_rules(grammar)    # Generate parser methods as strings
    lines = []
    for defn in defns:
        lines.append("")
        lines.append(generate_python_def(defn, "    "))
    lines.append("")

    # Generate epilogue (parse function)
    epilogue = _generate_epilogue()

    return prologue + "\n".join(lines) + epilogue


def _generate_prologue(grammar: Grammar, is_ll2: bool, conflicts: List[str], command_line: Optional[str] = None) -> str:
    """Generate parser prologue with imports, token class, lexer, and parser class start."""
    lines = []
    lines.append('"""')
    lines.append("Auto-generated LL(k) recursive-descent parser.")
    lines.append("")
    lines.append("Generated from protobuf specifications.")
    if command_line:
        lines.append("")
        lines.append(f"Command: {command_line}")
    lines.append('"""')
    lines.append("")
    lines.append("import re")
    lines.append("from typing import List, Optional, Any, Tuple")
    lines.append("from decimal import Decimal")
    lines.append("")
    lines.append("import lqp.ir as ir")
    lines.append("")
    lines.append("")

    if not is_ll2:
        lines.append("# WARNING: Grammar is not LL(2). Conflicts detected:")
        for conflict in conflicts:
            for line in conflict.split("\n"):
                lines.append(f"# {line}")
        lines.append("")

    lines.append("class ParseError(Exception):")
    lines.append('    """Parse error exception."""')
    lines.append("    pass")
    lines.append("")
    lines.append("")
    lines.append("class Token:")
    lines.append('    """Token representation."""')
    lines.append("    def __init__(self, type: str, value: str, pos: int):")
    lines.append("        self.type = type")
    lines.append("        self.value = value")
    lines.append("        self.pos = pos")
    lines.append("")
    lines.append("    def __repr__(self) -> str:")
    lines.append('        return f"Token({self.type}, {self.value!r}, {self.pos})"')
    lines.append("")
    lines.append("")

    # Generate Lexer
    lines.extend(_generate_lexer(grammar))

    # Start Parser class
    lines.append("class Parser:")
    lines.append('    """LL(k) recursive-descent parser with backtracking."""')
    lines.append("    def __init__(self, tokens: List[Token]):")
    lines.append("        self.tokens = tokens")
    lines.append("        self.pos = 0")
    lines.append("")
    lines.append("    def lookahead(self, k: int = 0) -> Token:")
    lines.append('        """Get lookahead token at offset k."""')
    lines.append("        idx = self.pos + k")
    lines.append("        return self.tokens[idx] if idx < len(self.tokens) else Token('$', '', -1)")
    lines.append("")
    lines.append("    def current(self) -> Token:")
    lines.append('        """Get current token."""')
    lines.append("        return self.lookahead(0)")
    lines.append("")
    lines.append("    def consume_literal(self, expected: str) -> None:")
    lines.append('        """Consume a literal token."""')
    lines.append("        if not self.match_literal(expected):")
    lines.append("            token = self.current()")
    lines.append(f"            raise ParseError(f'Expected literal {{expected!r}} but got {{token.type}}={{token.value!r}} at position {{token.pos}}')")
    lines.append("        self.pos += 1")
    lines.append("")
    lines.append("    def consume_terminal(self, expected: str) -> Any:")
    lines.append('        """Consume a terminal token and return parsed value."""')
    lines.append("        if not self.match_terminal(expected):")
    lines.append("            token = self.current()")
    lines.append(f"            raise ParseError(f'Expected terminal {{expected}} but got {{token.type}} at position {{token.pos}}')")
    lines.append("        token = self.current()")
    lines.append("        self.pos += 1")
    lines.append("        return token.value")
    lines.append("")
    lines.append("    def match_literal(self, literal: str) -> bool:")
    lines.append('        """Check if current token matches literal."""')
    lines.append("        token = self.current()")
    lines.append("        return token.type == 'LITERAL' and token.value == literal")
    lines.append("")
    lines.append("    def match_terminal(self, terminal: str) -> bool:")
    lines.append('        """Check if current token matches terminal."""')
    lines.append("        token = self.current()")
    lines.append("        return token.type == terminal")
    lines.append("")
    lines.append("    def match_lookahead_literal(self, literal: str, k: int) -> bool:")
    lines.append('        """Check if lookahead token at position k matches literal."""')
    lines.append("        token = self.lookahead(k)")
    lines.append("        return token.type == 'LITERAL' and token.value == literal")
    lines.append("")
    lines.append("    def match_lookahead_terminal(self, terminal: str, k: int) -> bool:")
    lines.append('        """Check if lookahead token at position k matches terminal."""')
    lines.append("        token = self.lookahead(k)")
    lines.append("        return token.type == terminal")
    lines.append("")

    return "\n".join(lines)


def _generate_lexer(grammar: Grammar) -> List[str]:
    """Generate Lexer class."""
    lines = []
    lines.append("class Lexer:")
    lines.append('    """Tokenizer for the input."""')
    lines.append("    def __init__(self, input_str: str):")
    lines.append("        self.input = input_str")
    lines.append("        self.pos = 0")
    lines.append("        self.tokens: List[Token] = []")
    lines.append("        self._tokenize()")
    lines.append("")
    lines.append("    def _tokenize(self) -> None:")
    lines.append('        """Tokenize the input string."""')

    # It's important to preserve the order of the tokens from the grammar.
    lines.append("        token_specs = [")
    for token in grammar.tokens:
        lines.append(f"            ('{token.name}', r'{token.pattern}', lambda x: self.parse_{token.name.lower()}(x)),")
    lines.append("        ]")
    lines.append("")
    lines.append("        whitespace_re = re.compile(r'\\s+')")
    lines.append("        comment_re = re.compile(r';;.*')")
    lines.append("")
    lines.append("        while self.pos < len(self.input):")
    lines.append("            match = whitespace_re.match(self.input, self.pos)")
    lines.append("            if match:")
    lines.append("                self.pos = match.end()")
    lines.append("                continue")
    lines.append("")
    lines.append("            match = comment_re.match(self.input, self.pos)")
    lines.append("            if match:")
    lines.append("                self.pos = match.end()")
    lines.append("                continue")
    lines.append("")
    lines.append("            matched = False")
    lines.append("")
    lines.append("            # Scan for literals first since they should have priority over symbols")
    lines.append("            for literal in self._get_literals():")
    lines.append("                if self.input[self.pos:].startswith(literal):")
    lines.append("                    # Check word boundary for alphanumeric keywords")
    lines.append("                    if literal[0].isalnum():")
    lines.append("                        end_pos = self.pos + len(literal)")
    lines.append("                        if end_pos < len(self.input) and self.input[end_pos].isalnum():")
    lines.append("                            continue")
    lines.append("                    self.tokens.append(Token('LITERAL', literal, self.pos))")
    lines.append("                    self.pos += len(literal)")
    lines.append("                    matched = True")
    lines.append("                    break")
    lines.append("")
    lines.append("            # Scan for other tokens")
    lines.append("            if not matched:")
    lines.append("                for token_type, pattern, action in token_specs:")
    lines.append("                    regex = re.compile(pattern)")
    lines.append("                    match = regex.match(self.input, self.pos)")
    lines.append("                    if match:")
    lines.append("                        value = match.group(0)")
    lines.append("                        self.tokens.append(Token(token_type, action(value), self.pos))")
    lines.append("                        self.pos = match.end()")
    lines.append("                        matched = True")
    lines.append("                        break")
    lines.append("")
    lines.append("            if not matched:")
    lines.append(f"                raise ParseError(f'Unexpected character at position {{self.pos}}: {{self.input[self.pos]!r}}')")
    lines.append("")
    lines.append("        self.tokens.append(Token('$', '', self.pos))")
    lines.append("")
    lines.append("    def _get_literals(self) -> List[str]:")
    lines.append('        """Get all literal strings from the grammar."""')

    literals = set()
    for rules_list in grammar.rules.values():
        for rule in rules_list:
            literals.update(get_literals(rule.rhs))

    sorted_literals = sorted(literals, key=lambda x: len(x.name), reverse=True)
    lines.append("        return [")
    for lit in sorted_literals:
        lines.append(f"            '{lit.name}',")
    lines.append("        ]")
    lines.append("")

    # Add token parsing helper methods to Lexer
    lines.append("    @staticmethod")
    lines.append("    def parse_symbol(s: str) -> str:")
    lines.append('        """Parse SYMBOL token."""')
    lines.append("        return str(s)")
    lines.append("")
    lines.append("    @staticmethod")
    lines.append("    def parse_string(s: str) -> str:")
    lines.append('        """Parse STRING token."""')
    lines.append("        return s[1:-1].encode().decode('unicode_escape')  # Strip quotes and process escaping")
    lines.append("")
    lines.append("    @staticmethod")
    lines.append("    def parse_int(n: str) -> int:")
    lines.append('        """Parse INT token."""')
    lines.append("        return int(n)")
    lines.append("")
    lines.append("    @staticmethod")
    lines.append("    def parse_float(f: str) -> float:")
    lines.append('        """Parse FLOAT token."""')
    lines.append("        if f == 'inf':")
    lines.append("            return float('inf')")
    lines.append("        elif f == 'nan':")
    lines.append("            return float('nan')")
    lines.append("        return float(f)")
    lines.append("")
    lines.append("    @staticmethod")
    lines.append("    def parse_uint128(u: str) -> Any:")
    lines.append('        """Parse UINT128 token."""')
    lines.append("        uint128_val = int(u, 16)")
    lines.append("        return ir.UInt128Value(value=uint128_val, meta=None)")
    lines.append("")
    lines.append("    @staticmethod")
    lines.append("    def parse_int128(u: str) -> Any:")
    lines.append('        """Parse INT128 token."""')
    lines.append("        u = u[:-4]  # Remove the 'i128' suffix")
    lines.append("        int128_val = int(u)")
    lines.append("        return ir.Int128Value(value=int128_val, meta=None)")
    lines.append("")
    lines.append("    @staticmethod")
    lines.append("    def parse_decimal(d: str) -> Any:")
    lines.append('        """Parse DECIMAL token."""')
    lines.append("        # Decimal is a string like '123.456d12' where the last part after `d` is the")
    lines.append("        # precision, and the scale is the number of digits between the decimal point and `d`")
    lines.append("        parts = d.split('d')")
    lines.append("        if len(parts) != 2:")
    lines.append("            raise ValueError(f'Invalid decimal format: {d}')")
    lines.append("        scale = len(parts[0].split('.')[1])")
    lines.append("        precision = int(parts[1])")
    lines.append("        value = Decimal(parts[0])")
    lines.append("        return ir.DecimalValue(precision=precision, scale=scale, value=value, meta=None)")
    lines.append("")
    lines.append("")

    return lines


def _generate_epilogue() -> str:
    """Generate parse function."""
    lines = []
    lines.append("")
    lines.append("def parse(input_str: str) -> Any:")
    lines.append('    """Parse input string and return parse tree."""')
    lines.append("    lexer = Lexer(input_str)")
    lines.append("    parser = Parser(lexer.tokens)")
    lines.append("    return parser.parse_start()")
    lines.append("")
    return "\n".join(lines)
