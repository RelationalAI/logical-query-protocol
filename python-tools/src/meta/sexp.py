"""Generic s-expression data structures.

This module defines a simple, generic representation for s-expressions
that can be used as an intermediate format for parsing configuration
files, grammar definitions, and target expressions.

S-expressions consist of:
- Atoms: symbols, integers, floats, or quoted strings
- Lists: sequences of s-expressions enclosed in parentheses

Example s-expressions:
    foo                     ; symbol atom
    42                      ; integer atom
    3.14                    ; float atom
    "hello world"           ; quoted string atom
    (foo bar baz)           ; list of symbols
    (+ 1 2)                 ; nested structure
    (define (square x) (* x x))  ; deeply nested
"""

from dataclasses import dataclass
from typing import Optional, Union


@dataclass(frozen=True)
class SAtom:
    """Atomic s-expression: symbol, string, integer, or float.

    Attributes:
        value: The atomic value (str for symbols/strings, int, or float)
        quoted: True for string literals (e.g., "hello"), False for symbols
    """
    value: Union[str, int, float, bool]
    quoted: bool = False

    def __str__(self) -> str:
        if self.quoted:
            escaped = str(self.value).replace('\\', '\\\\').replace('"', '\\"')
            return f'"{escaped}"'
        if isinstance(self.value, bool):
            return "true" if self.value else "false"
        return str(self.value)

    def is_symbol(self, name: str) -> bool:
        """Check if this atom is an unquoted symbol with the given name."""
        return not self.quoted and isinstance(self.value, str) and self.value == name


@dataclass(frozen=True)
class SList:
    """List s-expression: (elem1 elem2 ...).

    Attributes:
        elements: Tuple of child s-expressions
    """
    elements: tuple['SExpr', ...]

    def __str__(self) -> str:
        if not self.elements:
            return "()"
        return "(" + " ".join(str(e) for e in self.elements) + ")"

    def __len__(self) -> int:
        return len(self.elements)

    def __getitem__(self, index: int) -> 'SExpr':
        return self.elements[index]

    def __iter__(self):
        return iter(self.elements)

    def head(self) -> Optional['SExpr']:
        """Return the first element, or None if empty."""
        return self.elements[0] if self.elements else None

    def tail(self) -> 'SList':
        """Return all elements except the first."""
        return SList(self.elements[1:])

    def is_tagged(self, tag: str) -> bool:
        """Check if this list starts with a symbol matching the given tag."""
        if not self.elements:
            return False
        head = self.elements[0]
        return isinstance(head, SAtom) and head.is_symbol(tag)


SExpr = Union[SAtom, SList]


def atom(value: Union[str, int, float, bool], quoted: bool = False) -> SAtom:
    """Create an atom s-expression."""
    return SAtom(value, quoted)


def symbol(name: str) -> SAtom:
    """Create a symbol atom."""
    return SAtom(name, quoted=False)


def string(value: str) -> SAtom:
    """Create a quoted string atom."""
    return SAtom(value, quoted=True)


def slist(*elements: SExpr) -> SList:
    """Create a list s-expression from the given elements."""
    return SList(tuple(elements))


__all__ = [
    'SAtom',
    'SList',
    'SExpr',
    'atom',
    'symbol',
    'string',
    'slist',
]
