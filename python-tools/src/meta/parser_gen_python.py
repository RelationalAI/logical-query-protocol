"""Python-specific parser code generation.

This module generates LL(k) recursive-descent parsers in Python from grammars.
Handles Python-specific code generation including:
- Prologue (imports, Token, Lexer, Parser class with helpers)
- Parse method generation
- Epilogue (parse function)
"""

from typing import Dict, List, Optional, Set

from .grammar import Grammar, Rule, Rhs, Literal, Terminal, Nonterminal, Star, Plus, Option
from .target import Lambda, Call
from .analysis import _compute_rhs_first_k
from .codegen_python import generate_python
from .parser_gen import prepare_grammar, _generate_parse_rhs_ir, generate_rules


def generate_parser_python(grammar: Grammar, reachable: Set[str]) -> str:
    """Generate LL(k) recursive-descent parser in Python."""
    # Prepare grammar
    reachable, is_ll2, conflicts, nullable, first, first_2, follow = prepare_grammar(grammar)

    # Generate prologue (lexer, token, error, helper classes)
    prologue = _generate_prologue(grammar, is_ll2, conflicts)

    rules = generate_rules(grammar)    # Generate parser methods as strings
    lines = []
    for rule in rules:
        lines.append(generate_python(rule, "    "))

    # Generate epilogue (parse function)
    epilogue = _generate_epilogue()

    return prologue + "\n".join(lines) + epilogue


def _generate_prologue(grammar: Grammar, is_ll2: bool, conflicts: List[str]) -> str:
    """Generate parser prologue with imports, token class, lexer, and parser class start."""
    lines = []
    lines.append('"""')
    lines.append("Auto-generated LL(k) recursive-descent parser.")
    lines.append("")
    lines.append("Generated from protobuf specifications.")
    lines.append('"""')
    lines.append("")
    lines.append("import re")
    lines.append("from typing import List, Optional, Any, Tuple")
    lines.append("")
    lines.append("import lqp.ir as ir")
    lines.append("")
    lines.append("")

    if not is_ll2:
        lines.append("# WARNING: Grammar is not LL(2). Conflicts detected:")
        for conflict in conflicts:
            for line in conflict.split('\n'):
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
    lines.append("    def save_position(self) -> int:")
    lines.append('        """Save current position for backtracking."""')
    lines.append("        return self.pos")
    lines.append("")
    lines.append("    def restore_position(self, pos: int) -> None:")
    lines.append('        """Restore position for backtracking."""')
    lines.append("        self.pos = pos")
    lines.append("")
    lines.append("    def consume_literal(self, expected: str) -> None:")
    lines.append('        """Consume a literal token."""')
    lines.append("        if not self.match_literal(expected):")
    lines.append("            token = self.current()")
    lines.append(f"            raise ParseError(f'Expected literal {{expected!r}} but got {{token.type}}={{token.value!r}} at position {{token.pos}}')")
    lines.append("        self.pos += 1")
    lines.append("")
    lines.append("    def consume_terminal(self, expected: str) -> str:")
    lines.append('        """Consume a terminal token and return its value."""')
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

    token_patterns = []
    for token in grammar.tokens:
        pattern = token.pattern
        if pattern.startswith('/') and pattern.endswith('/'):
            pattern = pattern[1:-1]
        token_patterns.append((token.name, pattern))

    lines.append("        token_specs = [")
    for name, pattern in token_patterns:
        lines.append(f"            ('{name}', r'{pattern}'),")
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
    lines.append("            for token_type, pattern in token_specs:")
    lines.append("                regex = re.compile(pattern)")
    lines.append("                match = regex.match(self.input, self.pos)")
    lines.append("                if match:")
    lines.append("                    value = match.group(0)")
    lines.append("                    self.tokens.append(Token(token_type, value, self.pos))")
    lines.append("                    self.pos = match.end()")
    lines.append("                    matched = True")
    lines.append("                    break")
    lines.append("")
    lines.append("            if not matched:")
    lines.append("                for literal in self._get_literals():")
    lines.append("                    if self.input[self.pos:].startswith(literal):")
    lines.append("                        # Check word boundary for alphanumeric keywords")
    lines.append("                        if literal[0].isalnum():")
    lines.append("                            end_pos = self.pos + len(literal)")
    lines.append("                            if end_pos < len(self.input) and self.input[end_pos].isalnum():")
    lines.append("                                continue")
    lines.append("                        self.tokens.append(Token('LITERAL', literal, self.pos))")
    lines.append("                        self.pos += len(literal)")
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
    def extract_literals(rhs: List[Rhs]) -> None:
        for elem in rhs:
            extract_literals_from_elem(elem)

    def extract_literals_from_elem(rhs: Rhs) -> None:
        if isinstance(rhs, Literal):
            literals.add(rhs.name)
        elif isinstance(rhs, (Star, Plus, Option)):
            extract_literals_from_elem(rhs.rhs)

    for rules_list in grammar.rules.values():
        for rule in rules_list:
            extract_literals(rule.rhs)

    sorted_literals = sorted(literals, key=len, reverse=True)
    lines.append("        return [")
    for lit in sorted_literals:
        lines.append(f"            '{lit}',")
    lines.append("        ]")
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
