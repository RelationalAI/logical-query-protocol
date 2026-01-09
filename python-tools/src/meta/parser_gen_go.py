"""Go-specific parser code generation.

This module generates LL(k) recursive-descent parsers in Go from grammars.
Handles Go-specific code generation including:
- Prologue (imports, Token, Lexer, Parser struct with helpers)
- Parse method generation
- Epilogue (parse function)
"""

from typing import Optional, Set

from .grammar import Grammar, Nonterminal
from .codegen_go import generate_go_def
from .parser_gen import generate_parse_functions


def generate_parser_go(grammar: Grammar, command_line: Optional[str] = None) -> str:
    """Generate LL(k) recursive-descent parser in Go."""
    prologue = _generate_prologue(grammar, command_line)

    defns = generate_parse_functions(grammar)
    lines = []
    for defn in defns:
        lines.append("")
        lines.append(generate_go_def(defn))
    lines.append("")

    epilogue = _generate_epilogue(grammar.start)

    return prologue + "\n".join(lines) + epilogue


def _generate_prologue(grammar: Grammar, command_line: Optional[str] = None) -> str:
    """Generate parser prologue with imports, token struct, lexer, and parser struct."""
    lines = []
    lines.append("// Auto-generated LL(k) recursive-descent parser.")
    lines.append("//")
    lines.append("// Generated from protobuf specifications.")
    if command_line:
        lines.append("//")
        lines.append(f"// Command: {command_line}")
    lines.append("")
    lines.append("package parser")
    lines.append("")
    lines.append("// TODO: Implement Go parser prologue")
    lines.append("// - Token struct")
    lines.append("// - Lexer struct and methods")
    lines.append("// - Parser struct and helper methods")
    lines.append("")
    return "\n".join(lines)


def _generate_epilogue(start: Nonterminal) -> str:
    """Generate parser epilogue with main parse function."""
    func_name = f"parse{start.name.title().replace('_', '')}"
    lines = []
    lines.append("")
    lines.append("// TODO: Implement Go parser epilogue")
    lines.append(f"// - Parse function that calls {func_name}")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    'generate_parser_go',
]
