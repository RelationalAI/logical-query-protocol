#!/usr/bin/env python3
"""Tests for grammar normalization."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.grammar import Grammar, Rule, Nonterminal, Literal, Terminal, Sequence, Star, Plus, Option


def test_normalize_star():
    """Test normalization of Star operator."""
    grammar = Grammar()

    rule = Rule(
        lhs=Nonterminal("A"),
        rhs=Sequence([Literal("("), Star(Terminal("X")), Literal(")")]),
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


def test_normalize_plus():
    """Test normalization of Plus operator."""
    grammar = Grammar()

    rule = Rule(
        lhs=Nonterminal("B"),
        rhs=Plus(Terminal("Y")),
        grammar=grammar
    )
    grammar.add_rule(rule)

    normalized = grammar.normalize()

    # Should create auxiliary rules for Y+
    aux_rules = [name for name in normalized.rules.keys() if '_plus_' in name or '_star_' in name]
    assert len(aux_rules) > 0, "Should create auxiliary plus/star rules"

    print("✓ Plus normalization works correctly")


def test_normalize_option():
    """Test normalization of Option operator."""
    grammar = Grammar()

    rule = Rule(
        lhs=Nonterminal("C"),
        rhs=Option(Terminal("Z")),
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
        rhs=Sequence([Terminal("A"), Terminal("B")]),
        grammar=grammar
    )
    rule2 = Rule(
        lhs=Nonterminal("E"),
        rhs=Terminal("C"),
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
    test_normalize_plus()
    test_normalize_option()
    test_normalize_preserves_other_rules()
    print("\n✓ All normalization tests passed")
