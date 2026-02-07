"""Julia-specific parser code generation."""

from pathlib import Path
from typing import Optional

from .codegen_julia import JuliaCodeGenerator
from .grammar import Grammar
from .parser_gen_common import generate_parser


_TEMPLATE_PATH = Path(__file__).parent / "templates" / "parser.jl.template"


def generate_parser_julia(grammar: Grammar, command_line: Optional[str] = None, proto_messages=None) -> str:
    """Generate LL(k) recursive-descent parser in Julia."""
    codegen = JuliaCodeGenerator(proto_messages=proto_messages)
    return generate_parser(grammar, codegen, _TEMPLATE_PATH, command_line)


__all__ = [
    'generate_parser_julia',
]
