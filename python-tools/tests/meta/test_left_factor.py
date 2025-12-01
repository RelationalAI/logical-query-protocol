#!/usr/bin/env python3
"""Tests for grammar left-factoring."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.grammar import (
    Grammar, Rule, Nonterminal, Literal, Terminal, Sequence,
    Function, Var, Call
)


def test_simple_left_factor():
    """Test basic left-factoring of two rules with common prefix."""
    grammar = Grammar()

    # Create rules: A -> "(" "foo" B | "(" "foo" C
    rule1 = Rule(
        lhs=Nonterminal("A"),
        rhs=Sequence([Literal("("), Literal("foo"), Nonterminal("B")]),
        action=Lambda(params=['_', '_', 'b'], body=Call('MakeA1', [Var('b')])),
        grammar=grammar
    )

    rule2 = Rule(
        lhs=Nonterminal("A"),
        rhs=Sequence([Literal("("), Literal("foo"), Nonterminal("C")]),
        action=Lambda(params=['_', '_', 'c'], body=Call('MakeA2', [Var('c')])),
        grammar=grammar
    )

    grammar.add_rule(rule1)
    grammar.add_rule(rule2)

    factored = grammar.left_factor()

    # Check that we have a factored rule
    a_rules = factored.rules.get("A", [])
    assert len(a_rules) == 1, "Should have single factored A rule"

    # Check for continuation rules
    cont_rules = [name for name in factored.rules.keys() if name.startswith("A_cont_")]
    assert len(cont_rules) == 1, "Should have one continuation rule"

    cont_name = cont_rules[0]
    assert len(factored.rules[cont_name]) == 2, "Continuation should have 2 alternatives"

    print("✓ Simple left-factoring works correctly")


def test_no_common_prefix():
    """Test that rules with no common prefix are not factored."""
    grammar = Grammar()

    rule1 = Rule(
        lhs=Nonterminal("B"),
        rhs=Sequence([Literal("x"), Terminal("NUMBER")]),
        grammar=grammar
    )

    rule2 = Rule(
        lhs=Nonterminal("B"),
        rhs=Sequence([Literal("y"), Terminal("STRING")]),
        grammar=grammar
    )

    grammar.add_rule(rule1)
    grammar.add_rule(rule2)

    factored = grammar.left_factor()

    b_rules = factored.rules.get("B", [])
    assert len(b_rules) == 2, "Rules without common prefix should not be factored"

    print("✓ Rules without common prefix remain unchanged")


def test_normalize_then_factor():
    """Test normalization followed by left-factoring."""
    from meta.grammar import Star

    grammar = Grammar()

    # Rule with repetition: C -> "(" "list" D* ")"
    rule = Rule(
        lhs=Nonterminal("C"),
        rhs=Sequence([Literal("("), Literal("list"), Star(Nonterminal("D")), Literal(")")]),
        grammar=grammar
    )

    grammar.add_rule(rule)

    # Normalize first
    normalized = grammar.normalize()
    assert len(normalized.rules) > 1, "Normalization should create auxiliary rules"

    # Then left-factor
    factored = normalized.left_factor()
    assert factored is not None, "Left-factoring should succeed"

    print("✓ Normalize then left-factor pipeline works")


def test_action_preservation():
    """Test that semantic actions are preserved through left-factoring."""
    grammar = Grammar()

    rule1 = Rule(
        lhs=Nonterminal("D"),
        rhs=Sequence([Literal("("), Literal("add"), Terminal("X")]),
        action=Lambda(params=['_', '_', 'x'], body=Call('Add', [Var('x')])),
        grammar=grammar
    )

    rule2 = Rule(
        lhs=Nonterminal("D"),
        rhs=Sequence([Literal("("), Literal("sub"), Terminal("Y")]),
        action=Lambda(params=['_', '_', 'y'], body=Call('Sub', [Var('y')])),
        grammar=grammar
    )

    grammar.add_rule(rule1)
    grammar.add_rule(rule2)

    factored = grammar.left_factor()

    # Check that factored rule has metadata
    d_rules = factored.rules.get("D", [])
    assert len(d_rules) == 1, "Should have factored D rule"
    assert hasattr(d_rules[0], 'original_rules'), "Should store original rules"

    # Check continuation rules preserve actions
    cont_rules = [name for name in factored.rules.keys() if '_cont_' in name]
    assert len(cont_rules) > 0, "Should have continuation rules"

    cont_name = cont_rules[0]
    for rule in factored.rules[cont_name]:
        assert hasattr(rule, 'original_action'), "Should preserve original action"

    print("✓ Semantic actions preserved through left-factoring")


if __name__ == "__main__":
    test_simple_left_factor()
    test_no_common_prefix()
    test_normalize_then_factor()
    test_action_preservation()
    print("\n✓ All left-factoring tests passed")
