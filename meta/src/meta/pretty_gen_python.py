"""Python-specific pretty printer code generation."""

from pathlib import Path

from .codegen_python import PythonCodeGenerator
from .grammar import Grammar
from .pretty_gen_common import generate_pretty_printer

_TEMPLATE_PATH = Path(__file__).parent / "templates" / "pretty_printer.py.template"


def generate_pretty_printer_python(
    grammar: Grammar,
    command_line: str | None = None,
    proto_messages=None,
    proto_enums=None,
) -> str:
    """Generate pretty printer in Python."""
    codegen = PythonCodeGenerator(proto_messages=proto_messages)
    return generate_pretty_printer(
        grammar,
        codegen,
        _TEMPLATE_PATH,
        command_line,
        proto_messages=proto_messages,
        proto_enums=proto_enums,
    )
