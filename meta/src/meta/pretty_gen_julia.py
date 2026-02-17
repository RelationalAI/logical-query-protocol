"""Julia-specific pretty printer code generation."""

from pathlib import Path

from .codegen_base import PRINTER_MODE
from .codegen_julia import JuliaCodeGenerator
from .grammar import Grammar
from .pretty_gen_common import generate_pretty_printer

_TEMPLATE_PATH = Path(__file__).parent / "templates" / "pretty_printer.jl.template"


def generate_pretty_printer_julia(
    grammar: Grammar, command_line: str | None = None, proto_messages=None
) -> str:
    """Generate pretty printer in Julia."""
    codegen = JuliaCodeGenerator(proto_messages=proto_messages, config=PRINTER_MODE)
    return generate_pretty_printer(grammar, codegen, _TEMPLATE_PATH, command_line)
