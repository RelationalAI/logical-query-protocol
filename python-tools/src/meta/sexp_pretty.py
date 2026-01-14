"""S-expression pretty-printer.

This module provides formatting utilities for s-expressions, producing
readable output with intelligent line breaking and indentation.

Example:
    >>> from meta.sexp import slist, symbol, atom
    >>> from meta.sexp_pretty import pretty_print
    >>> expr = slist(symbol("define"), slist(symbol("f"), symbol("x")), slist(symbol("*"), symbol("x"), symbol("x")))
    >>> print(pretty_print(expr))
    (define (f x) (* x x))
"""

from .sexp import SAtom, SList, SExpr


def _estimate_width(sexp: SExpr) -> int:
    """Estimate the width of an s-expression when printed on one line."""
    if isinstance(sexp, SAtom):
        if sexp.quoted:
            return len(str(sexp.value)) + 2  # account for quotes
        return len(str(sexp.value))
    else:
        if not sexp.elements:
            return 2  # "()"
        return 2 + sum(_estimate_width(e) for e in sexp.elements) + len(sexp.elements) - 1


def _format_atom(atom: SAtom) -> str:
    """Format an atom."""
    if atom.quoted:
        escaped = str(atom.value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')
        return f'"{escaped}"'
    if isinstance(atom.value, bool):
        return "true" if atom.value else "false"
    return str(atom.value)


def pretty_print(sexp: SExpr, width: int = 80, indent: int = 0) -> str:
    """Pretty-print an s-expression with intelligent formatting.

    Short expressions are printed on one line. Long expressions are
    broken across multiple lines with proper indentation.

    Args:
        sexp: The s-expression to format
        width: Maximum line width before breaking
        indent: Current indentation level (used internally)

    Returns:
        Formatted string representation
    """
    if isinstance(sexp, SAtom):
        return _format_atom(sexp)

    # Empty list
    if not sexp.elements:
        return "()"

    # Try single-line format first
    single_line = "(" + " ".join(_format_atom(e) if isinstance(e, SAtom) else pretty_print(e, width, 0)
                                  for e in sexp.elements) + ")"
    if len(single_line) + indent <= width:
        return single_line

    # Multi-line format
    head = sexp.elements[0]
    head_str = _format_atom(head) if isinstance(head, SAtom) else pretty_print(head, width, indent + 1)

    # Special case: (tag args...) where tag is a short symbol
    if isinstance(head, SAtom) and not head.quoted and len(str(head.value)) <= 12 and len(sexp.elements) > 1:
        # Put head and first arg on same line if possible
        inner_indent = indent + len(head_str) + 2  # account for "(" and space after head
        lines = ["(" + head_str]

        for i, elem in enumerate(sexp.elements[1:], 1):
            elem_str = _format_atom(elem) if isinstance(elem, SAtom) else pretty_print(elem, width, inner_indent)
            if i == 1:
                # First element on same line as head
                test_line = lines[0] + " " + elem_str
                if len(test_line) <= width:
                    lines[0] = test_line
                else:
                    lines.append(" " * inner_indent + elem_str)
            else:
                lines.append(" " * inner_indent + elem_str)

        return "\n".join(lines) + ")"

    # General case: each element on its own line
    inner_indent = indent + 2
    lines = ["("]
    for elem in sexp.elements:
        elem_str = _format_atom(elem) if isinstance(elem, SAtom) else pretty_print(elem, width, inner_indent)
        lines.append(" " * inner_indent + elem_str)
    lines[-1] = lines[-1] + ")"
    return "\n".join(lines)


def compact_print(sexp: SExpr) -> str:
    """Print an s-expression on a single line."""
    if isinstance(sexp, SAtom):
        return _format_atom(sexp)
    if not sexp.elements:
        return "()"
    return "(" + " ".join(compact_print(e) for e in sexp.elements) + ")"


__all__ = [
    'pretty_print',
    'compact_print',
]
