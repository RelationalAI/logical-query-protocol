#!/usr/bin/env python3
"""Tests for grammar normalization."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.grammar import Grammar, Rule, Nonterminal, LitTerminal, NamedTerminal, Sequence, Star, Option


def test_normalize_star():
    """Test normalization of Star operator."""
    grammar = Grammar()

    rule = Rule(
        lhs=Nonterminal("A"),
        rhs=Sequence([LitTerminal("("), Star(NamedTerminal("X")), LitTerminal(")")]),
        grammar=grammar
    )
    grammar.add_rule(rule)

    normalized = grammar.normalize()

    # Should create auxiliary rule for X*
    aux_rules = [name for name in normalized.rules.keys() if '_star_' in name]
    assert len(aux_rules) > 0, "Should create auxiliary star rule"

    # Auxiliary rule should have two alternatives (recursive and epsilon)
    star_rule = aux_rules[0]
    assert len(normalized.rules[star_rule]) == 2, "Star rule should have 2 alternatives"

    print("✓ Star normalization works correctly")


def test_normalize_option():
    """Test normalization of Option operator."""
    grammar = Grammar()

    rule = Rule(
        lhs=Nonterminal("C"),
        rhs=Option(NamedTerminal("Z")),
        grammar=grammar
    )
    grammar.add_rule(rule)

    normalized = grammar.normalize()

    # Should create auxiliary rule for Z?
    aux_rules = [name for name in normalized.rules.keys() if '_opt_' in name]
    assert len(aux_rules) > 0, "Should create auxiliary option rule"

    # Option rule should have two alternatives (Z and epsilon)
    opt_rule = aux_rules[0]
    assert len(normalized.rules[opt_rule]) == 2, "Option rule should have 2 alternatives"

    print("✓ Option normalization works correctly")


def test_normalize_preserves_other_rules():
    """Test that normalization preserves non-EBNF rules."""
    grammar = Grammar()

    rule1 = Rule(
        lhs=Nonterminal("D"),
        rhs=Sequence([NamedTerminal("A"), NamedTerminal("B")]),
        grammar=grammar
    )
    rule2 = Rule(
        lhs=Nonterminal("E"),
        rhs=NamedTerminal("C"),
        grammar=grammar
    )

    grammar.add_rule(rule1)
    grammar.add_rule(rule2)

    normalized = grammar.normalize()

    assert "D" in normalized.rules, "Should preserve rule D"
    assert "E" in normalized.rules, "Should preserve rule E"

    print("✓ Normalization preserves non-EBNF rules")


if __name__ == "__main__":
    test_normalize_star()
    test_normalize_option()
    test_normalize_preserves_other_rules()
    print("\n✓ All normalization tests passed")
