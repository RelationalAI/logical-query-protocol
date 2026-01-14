"""Builtin grammar rules loaded from s-expression configuration.

This module loads grammar rules from the builtin_rules.sexp configuration file.
These rules define constructs that cannot be auto-generated from protobuf
definitions, such as value literals, date/datetime parsing, configuration
syntax, bindings, abstractions, type literals, and operators.
"""

from pathlib import Path
from typing import Dict, List, Tuple

from .grammar import Nonterminal, Rule
from .sexp_grammar import load_grammar_config_file


def get_builtin_rules() -> Dict[Nonterminal, Tuple[List[Rule], bool]]:
    """Return dict mapping nonterminals to (rules, is_final).

    is_final=True means auto-generation should not add more rules for this nonterminal.

    Loads rules from the builtin_rules.sexp configuration file.
    """
    config_path = Path(__file__).parent / "builtin_rules.sexp"
    return load_grammar_config_file(config_path)


class BuiltinRules:
    """Wrapper class for backward compatibility with existing code."""

    def get_builtin_rules(self) -> Dict[Nonterminal, Tuple[List[Rule], bool]]:
        """Return dict mapping nonterminals to (rules, is_final)."""
        return get_builtin_rules()
