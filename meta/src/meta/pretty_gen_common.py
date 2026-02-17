"""Common pretty printer generation logic shared across all target languages."""

from pathlib import Path

from .codegen_base import CodeGenerator
from .dead_functions import live_functions
from .grammar import Grammar
from .pretty_gen import generate_pretty_functions


def generate_pretty_printer(
    grammar: Grammar,
    codegen: CodeGenerator,
    template_path: Path,
    command_line: str | None = None,
) -> str:
    """Generate a pretty printer from a grammar using the given code generator and template."""
    template = template_path.read_text()
    indent = codegen.parse_def_indent

    defns = generate_pretty_functions(grammar)
    lines = []
    for defn in defns:
        lines.append("")
        lines.append(codegen.generate_def(defn, indent))
    lines.append("")
    pretty_nonterminal_defns = "\n".join(lines)

    live_funs = live_functions(
        [defn.body for defn in defns],
        grammar.function_defs,
    )

    function_lines = []
    for fundef in live_funs.values():
        function_lines.append("")
        function_lines.append(codegen.generate_method_def(fundef, indent))
    named_function_defns = "\n".join(function_lines) if function_lines else ""

    command_line_comment = (
        codegen.format_command_line_comment(command_line) if command_line else ""
    )

    return template.format(
        command_line_comment=command_line_comment,
        start_name=grammar.start.name.lower(),
        pretty_nonterminal_defns=pretty_nonterminal_defns,
        named_function_defns=named_function_defns,
    )
