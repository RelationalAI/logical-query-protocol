"""S-expression parser.

This module provides a hand-written recursive descent parser for s-expressions.
It supports:
- Symbols: alphanumeric identifiers, operators, and special characters
- Integers: decimal numbers with optional sign
- Floats: decimal numbers with decimal point and optional exponent
- Quoted strings: "..." with escape sequences
- Lists: (elem1 elem2 ...)
- Comments: ; to end of line

Example:
    >>> from meta.sexp_parser import parse_sexp, parse_sexp_file
    >>> parse_sexp("(+ 1 2)")
    SList((SAtom('+'), SAtom(1), SAtom(2)))
    >>> parse_sexp_file("(foo) (bar)")
    [SList((SAtom('foo'),)), SList((SAtom('bar'),))]
"""

from dataclasses import dataclass
from typing import List

from .sexp import SAtom, SList, SExpr


@dataclass
class ParseError(Exception):
    """Error during s-expression parsing with location information."""
    message: str
    line: int
    column: int
    context: str = ""

    def __str__(self) -> str:
        loc = f"line {self.line}, column {self.column}"
        if self.context:
            return f"{self.message} at {loc}: {self.context}"
        return f"{self.message} at {loc}"


class SExprParser:
    """Recursive descent parser for s-expressions."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1

    def parse(self) -> SExpr:
        """Parse a single s-expression from the input."""
        self._skip_whitespace_and_comments()
        if self._at_end():
            raise self._error("Unexpected end of input")
        result = self._parse_expr()
        self._skip_whitespace_and_comments()
        return result

    def parse_all(self) -> List[SExpr]:
        """Parse all s-expressions from the input."""
        results: List[SExpr] = []
        self._skip_whitespace_and_comments()
        while not self._at_end():
            results.append(self._parse_expr())
            self._skip_whitespace_and_comments()
        return results

    def _parse_expr(self) -> SExpr:
        """Parse a single expression (atom or list)."""
        self._skip_whitespace_and_comments()
        ch = self._peek()
        if ch == '(':
            return self._parse_list()
        elif ch == '"':
            return self._parse_string()
        else:
            return self._parse_atom()

    def _parse_list(self) -> SList:
        """Parse a list: (elem1 elem2 ...)."""
        self._expect('(')
        elements: List[SExpr] = []
        self._skip_whitespace_and_comments()
        while not self._at_end() and self._peek() != ')':
            elements.append(self._parse_expr())
            self._skip_whitespace_and_comments()
        self._expect(')')
        return SList(tuple(elements))

    def _parse_string(self) -> SAtom:
        """Parse a quoted string: "..."."""
        self._expect('"')
        chars: List[str] = []
        while not self._at_end() and self._peek() != '"':
            ch = self._advance()
            if ch == '\\':
                if self._at_end():
                    raise self._error("Unterminated escape sequence in string")
                escape_ch = self._advance()
                if escape_ch == 'n':
                    chars.append('\n')
                elif escape_ch == 't':
                    chars.append('\t')
                elif escape_ch == 'r':
                    chars.append('\r')
                elif escape_ch == '\\':
                    chars.append('\\')
                elif escape_ch == '"':
                    chars.append('"')
                else:
                    chars.append('\\')
                    chars.append(escape_ch)
            else:
                chars.append(ch)
        if self._at_end():
            raise self._error("Unterminated string")
        self._expect('"')
        return SAtom(''.join(chars), quoted=True)

    def _parse_atom(self) -> SAtom:
        """Parse an atom: symbol, integer, or float."""
        start = self.pos

        # Collect characters that can be part of an atom
        while not self._at_end() and self._peek() not in '()";\t\n\r ':
            self._advance()

        if self.pos == start:
            ch = self._peek() if not self._at_end() else "EOF"
            raise self._error(f"Unexpected character: {ch!r}")

        token = self.text[start:self.pos]

        # Try to parse as boolean
        if token == "true":
            return SAtom(True)
        if token == "false":
            return SAtom(False)

        # Try to parse as integer
        try:
            return SAtom(int(token))
        except ValueError:
            pass

        # Try to parse as float
        try:
            return SAtom(float(token))
        except ValueError:
            pass

        # Otherwise it's a symbol
        return SAtom(token)

    def _skip_whitespace_and_comments(self) -> None:
        """Skip whitespace and comments."""
        while not self._at_end():
            ch = self._peek()
            if ch in ' \t\n\r':
                self._advance()
            elif ch == ';':
                # Skip to end of line
                while not self._at_end() and self._peek() != '\n':
                    self._advance()
            else:
                break

    def _peek(self, offset: int = 0) -> str:
        """Return the character at the current position + offset without advancing."""
        pos = self.pos + offset
        if pos >= len(self.text):
            return '\0'
        return self.text[pos]

    def _advance(self) -> str:
        """Advance one character and return it."""
        if self._at_end():
            return '\0'
        ch = self.text[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _expect(self, expected: str) -> None:
        """Expect and consume a specific character."""
        if self._at_end():
            raise self._error(f"Expected {expected!r}, got end of input")
        ch = self._peek()
        if ch != expected:
            raise self._error(f"Expected {expected!r}, got {ch!r}")
        self._advance()

    def _at_end(self) -> bool:
        """Check if we've reached the end of input."""
        return self.pos >= len(self.text)

    def _error(self, message: str) -> ParseError:
        """Create a parse error at the current position."""
        context = self._get_context()
        return ParseError(message, self.line, self.column, context)

    def _get_context(self, width: int = 20) -> str:
        """Get context around the current position for error messages."""
        start = max(0, self.pos - width // 2)
        end = min(len(self.text), self.pos + width // 2)
        return self.text[start:end].replace('\n', '\\n')


def parse_sexp(text: str) -> SExpr:
    """Parse a single s-expression from text."""
    return SExprParser(text).parse()


def parse_sexp_file(text: str) -> List[SExpr]:
    """Parse all s-expressions from text."""
    return SExprParser(text).parse_all()


__all__ = [
    'ParseError',
    'SExprParser',
    'parse_sexp',
    'parse_sexp_file',
]
