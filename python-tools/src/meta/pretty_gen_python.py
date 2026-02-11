"""Python-specific pretty printer code generation.

Generates pretty printers in Python from grammars. Handles Python-specific
code generation including prologue (imports, PrettyPrinter class), pretty
print method generation, and epilogue.
"""

from pathlib import Path
from typing import Optional

from .grammar import Grammar
from .codegen_python import PythonCodeGenerator
from .pretty_gen import generate_pretty_functions


_TEMPLATE_PATH = Path(__file__).parent / "templates" / "pretty_printer.py.template"


def generate_pretty_printer_python(grammar: Grammar, command_line: Optional[str] = None,
                                   proto_messages=None) -> str:
    """Generate pretty printer in Python."""
    template = _TEMPLATE_PATH.read_text()

    codegen = PythonCodeGenerator(proto_messages=proto_messages)
    indent = "    "

    defns = generate_pretty_functions(grammar, proto_messages)
    lines = []
    for defn in defns:
        lines.append("")
        lines.append(codegen.generate_def(defn, indent))
    lines.append("")
    pretty_nonterminal_defns = "\n".join(lines)

    function_lines = []
    for fundef in grammar.function_defs.values():
        function_lines.append("")
        function_lines.append(codegen.generate_method_def(fundef, indent))
    named_function_defns = "\n".join(function_lines) if function_lines else ""

    command_line_comment = f"\nCommand: {command_line}\n" if command_line else ""

    return template.format(
        command_line_comment=command_line_comment,
        start_name=grammar.start.name.lower(),
        pretty_nonterminal_defns=pretty_nonterminal_defns,
        named_function_defns=named_function_defns,
    )
