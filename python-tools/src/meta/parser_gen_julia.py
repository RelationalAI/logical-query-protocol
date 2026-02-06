"""Julia-specific parser code generation.

This module generates LL(k) recursive-descent parsers in Julia from grammars.
Handles Julia-specific code generation including:
- Prologue (imports, Token, Lexer, Parser struct with helpers)
- Parse method generation
- Epilogue (parse function)
"""

import re
from pathlib import Path
from typing import Optional

from .grammar import Grammar
from .grammar_utils import get_literals
from .codegen_julia import JuliaCodeGenerator
from .parser_gen import generate_parse_functions


# Load template at module level
_TEMPLATE_PATH = Path(__file__).parent / "templates" / "parser.jl.template"
PROLOGUE_TEMPLATE = _TEMPLATE_PATH.read_text()


def generate_parser_julia(grammar: Grammar, command_line: Optional[str] = None, proto_messages=None) -> str:
    """Generate LL(k) recursive-descent parser in Julia."""
    # Create code generator with proto message info
    codegen = JuliaCodeGenerator(proto_messages=proto_messages)

    # Generate parser methods as strings
    defns = generate_parse_functions(grammar)
    lines = []
    for defn in defns:
        lines.append("")
        lines.append(codegen.generate_def(defn, ""))
    lines.append("")
    parse_nonterminal_defns = "\n".join(lines)

    # Generate user-defined function methods from function_defs
    function_lines = []
    for fundef in grammar.function_defs.values():
        function_lines.append("")
        function_lines.append(codegen._generate_builtin_method_def(fundef, ""))
    named_function_defns = "\n".join(function_lines) if function_lines else ""

    # Generate full parser from template
    return _generate_from_template(grammar, command_line, parse_nonterminal_defns, named_function_defns)


def _generate_from_template(
    grammar: Grammar,
    command_line: Optional[str] = None,
    parse_nonterminal_defns: str = "",
    named_function_defns: str = "",
) -> str:
    """Generate parser from template with imports, token struct, lexer, parser struct, and parse function."""
    # Build command line comment
    command_line_comment = f"\nCommand: {command_line}\n" if command_line else ""

    # Collect literals (sorted by length, longest first)
    literals = set()
    for rules_list in grammar.rules.values():
        for rule in rules_list:
            literals.update(get_literals(rule.rhs))
    sorted_literals = sorted(literals, key=lambda x: (-len(x.name), x.name))

    # Build token specs with literals first, then other tokens
    token_specs_lines = []

    # Add literals to token_specs
    # Only add non-alphanumeric literals (punctuation) as LITERAL tokens.
    # Alphanumeric keywords become "soft keywords" - they're lexed as SYMBOL
    # and matched by value in match_lookahead_literal.
    for lit in sorted_literals:
        # Skip alphanumeric literals - they'll be lexed as SYMBOL tokens
        if lit.name[0].isalnum():
            continue
        # Escape regex special characters in literal
        escaped = re.escape(lit.name)
        token_specs_lines.append(
            f'        ("LITERAL", r"{escaped}", identity),'
        )

    # Add other tokens
    for token in grammar.tokens:
        # Escape double quotes in the pattern for Julia raw strings
        escaped_pattern = token.pattern.replace('"', '\\"')
        token_specs_lines.append(
            f'        ("{token.name}", r"{escaped_pattern}", scan_{token.name.lower()}),'
        )

    token_specs = "\n".join(token_specs_lines) + "\n" if token_specs_lines else ""

    return PROLOGUE_TEMPLATE.format(
        command_line_comment=command_line_comment,
        token_specs=token_specs,
        start_name=grammar.start.name.lower(),
        parse_nonterminal_defns=parse_nonterminal_defns,
        named_function_defns=named_function_defns,
    )


__all__ = [
    'generate_parser_julia',
]
