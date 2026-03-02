"""Python-specific parser code generation."""

from pathlib import Path

from .codegen_python import PythonCodeGenerator
from .grammar import Grammar
from .parser_gen_common import generate_parser

_TEMPLATE_PATH = Path(__file__).parent / "templates" / "parser.py.template"


def generate_parser_python(
    grammar: Grammar, command_line: str | None = None, proto_messages=None
) -> str:
    """Generate LL(k) recursive-descent parser in Python."""
    codegen = PythonCodeGenerator(proto_messages=proto_messages)
    return generate_parser(
        grammar, codegen, _TEMPLATE_PATH, command_line, proto_messages
    )
