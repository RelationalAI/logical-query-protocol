"""Common parser generation logic shared across all target languages.

Extracts the shared structure from parser_gen_python.py and parser_gen_julia.py:
generate parse functions, collect token specs, and format the template.
"""

import re
from pathlib import Path
from typing import Optional

from .codegen_base import CodeGenerator
from .grammar import Grammar
from .grammar_utils import get_literals
from .parser_gen import generate_parse_functions


def generate_parser(
    grammar: Grammar,
    codegen: CodeGenerator,
    template_path: Path,
    command_line: Optional[str] = None,
) -> str:
    """Generate a parser from a grammar using the given code generator and template.

    Args:
        grammar: The grammar to generate a parser for
        codegen: Language-specific code generator
        template_path: Path to the language-specific template file
        command_line: Optional command line string for the file header
    """
    template = template_path.read_text()
    indent = codegen.parse_def_indent

    defns = generate_parse_functions(grammar, indent=indent)
    lines = []
    for defn in defns:
        lines.append("")
        lines.append(codegen.generate_def(defn, defn.indent))
    lines.append("")
    parse_nonterminal_defns = "\n".join(lines)

    function_lines = []
    for fundef in grammar.function_defs.values():
        function_lines.append("")
        function_lines.append(codegen.generate_method_def(fundef, indent))
    named_function_defns = "\n".join(function_lines) if function_lines else ""

    command_line_comment = codegen.format_command_line_comment(command_line) if command_line else ""

    token_specs = _build_token_specs(grammar, codegen)

    return template.format(
        command_line_comment=command_line_comment,
        token_specs=token_specs,
        start_name=grammar.start.name.lower(),
        parse_nonterminal_defns=parse_nonterminal_defns,
        named_function_defns=named_function_defns,
    )


def _build_token_specs(grammar: Grammar, codegen: CodeGenerator) -> str:
    """Build token specification lines using codegen formatting methods."""
    literals = set()
    for rules_list in grammar.rules.values():
        for rule in rules_list:
            literals.update(get_literals(rule.rhs))
    sorted_literals = sorted(literals, key=lambda x: (-len(x.name), x.name))

    token_specs_lines = []

    for lit in sorted_literals:
        if lit.name[0].isalnum():
            continue
        escaped = re.escape(lit.name)
        token_specs_lines.append(codegen.format_literal_token_spec(escaped))

    for token in grammar.tokens:
        token_specs_lines.append(codegen.format_named_token_spec(token.name, token.pattern))

    if token_specs_lines:
        return "\n".join(token_specs_lines) + "\n"
    return ""
