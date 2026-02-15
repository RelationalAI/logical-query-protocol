"""Go-specific parser code generation."""

from pathlib import Path
from typing import Optional

from .codegen_go import GoCodeGenerator
from .grammar import Grammar
from .parser_gen_common import generate_parser


_TEMPLATE_PATH = Path(__file__).parent / "templates" / "parser.go.template"


def generate_parser_go(grammar: Grammar, command_line: Optional[str] = None, proto_messages=None) -> str:
    """Generate LL(k) recursive-descent parser in Go."""
    codegen = GoCodeGenerator(proto_messages=proto_messages)
    return generate_parser(grammar, codegen, _TEMPLATE_PATH, command_line)


__all__ = [
    'generate_parser_go',
]
