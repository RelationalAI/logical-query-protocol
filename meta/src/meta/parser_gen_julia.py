"""Julia-specific parser code generation."""

from pathlib import Path

from .codegen_base import PARSER_CONFIG
from .codegen_julia import JuliaCodeGenerator
from .grammar import Grammar
from .parser_gen_common import generate_parser

_TEMPLATE_PATH = Path(__file__).parent / "templates" / "parser.jl.template"


def generate_parser_julia(
    grammar: Grammar, command_line: str | None = None, proto_messages=None
) -> str:
    """Generate LL(k) recursive-descent parser in Julia."""
    codegen = JuliaCodeGenerator(proto_messages=proto_messages, config=PARSER_CONFIG)
    return generate_parser(
        grammar, codegen, _TEMPLATE_PATH, command_line, proto_messages
    )


__all__ = [
    "generate_parser_julia",
]
