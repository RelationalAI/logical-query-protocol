"""Go-specific pretty printer code generation."""

from pathlib import Path

from .codegen_go import GoCodeGenerator
from .grammar import Grammar
from .pretty_gen_common import generate_pretty_printer

_TEMPLATE_PATH = Path(__file__).parent / "templates" / "pretty_printer.go.template"


def generate_pretty_printer_go(
    grammar: Grammar, command_line: str | None = None, proto_messages=None
) -> str:
    """Generate pretty printer in Go."""
    codegen = GoCodeGenerator(proto_messages=proto_messages)
    return generate_pretty_printer(grammar, codegen, _TEMPLATE_PATH, command_line)
