"""Python-specific parser code generation."""

import subprocess
from pathlib import Path
from typing import Optional

from .codegen_python import PythonCodeGenerator
from .grammar import Grammar
from .parser_gen_common import generate_parser


_TEMPLATE_PATH = Path(__file__).parent / "templates" / "parser.py.template"


def _ruff_format(source: str) -> str:
    """Run ruff format on source code string. Returns formatted source, or original on failure."""
    try:
        result = subprocess.run(
            ["ruff", "format", "--stdin-filename", "parser.py"],
            input=source,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout
    except FileNotFoundError:
        pass
    return source


def generate_parser_python(grammar: Grammar, command_line: Optional[str] = None, proto_messages=None) -> str:
    """Generate LL(k) recursive-descent parser in Python."""
    codegen = PythonCodeGenerator(proto_messages=proto_messages)
    source = generate_parser(grammar, codegen, _TEMPLATE_PATH, command_line)
    return _ruff_format(source)
