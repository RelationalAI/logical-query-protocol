#!/usr/bin/env python3
"""Tests for Let-bindings in left-factored semantic actions."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.grammar import (
    Grammar, Rule, Nonterminal, Literal, Sequence,
    Lambda, Var, Call, Let
)
from meta.target import BaseType

_any_type = BaseType("Any")


def test_let_binding_structure():
    """Test that left-factoring creates proper Let-binding structure."""
    grammar = Grammar()

    # Create rules: A -> "(" "foo" B | "(" "foo" C
    rule1 = Rule(
        lhs=Nonterminal("A"),
        rhs=Sequence([Literal("("), Literal("foo"), Nonterminal("B")]),
        action=Lambda(params=['_', '_', 'b'], body=Call('MakeA1', [Var('b', _any_type)])),
        grammar=grammar
    )

    rule2 = Rule(
        lhs=Nonterminal("A"),
        rhs=Sequence([Literal("("), Literal("foo"), Nonterminal("C")]),
        action=Lambda(params=['_', '_', 'c'], body=Call('MakeA2', [Var('c', _any_type)])),
        grammar=grammar
    )

    grammar.add_rule(rule1)
    grammar.add_rule(rule2)

    factored = grammar.left_factor()

    # Check that factored rule uses Let
    a_rules = factored.rules.get("A", [])
    assert len(a_rules) == 1, "Should have single factored A rule"

    rule = a_rules[0]
    assert rule.action is not None, "Factored rule should have action"
    assert isinstance(rule.action.body, Let), "Action should use Let-binding"

    # Check Let structure
    let_expr = rule.action.body
    assert isinstance(let_expr, Let), "Should be a Let expression"
    assert let_expr.var == "x0", "First Let should bind x0"

    # Should have nested Lets for each prefix element
    inner_let = let_expr.body
    assert isinstance(inner_let, Let), "Should have nested Let for second prefix element"
    assert inner_let.var == "x1", "Second Let should bind x1"

    print("✓ Let-binding structure is correct")


def test_continuation_receives_prefix_params():
    """Test that continuation rules receive prefix variables as parameters."""
    grammar = Grammar()

    rule1 = Rule(
        lhs=Nonterminal("B"),
        rhs=Sequence([Literal("("), Literal("op"), Nonterminal("X")]),
        action=Lambda(params=['_', '_', 'x'], body=Call('OpX', [Var('x', _any_type)])),
        grammar=grammar
    )

    rule2 = Rule(
        lhs=Nonterminal("B"),
        rhs=Sequence([Literal("("), Literal("op"), Nonterminal("Y")]),
        action=Lambda(params=['_', '_', 'y'], body=Call('OpY', [Var('y', _any_type)])),
        grammar=grammar
    )

    grammar.add_rule(rule1)
    grammar.add_rule(rule2)

    factored = grammar.left_factor()

    # Check continuation rules
    cont_rules = [name for name in factored.rules.keys() if '_cont_' in name]
    assert len(cont_rules) == 1, "Should have one continuation nonterminal"

    cont_name = cont_rules[0]
    cont_alts = factored.rules[cont_name]
    assert len(cont_alts) == 2, "Continuation should have 2 alternatives"

    # Each continuation receives prefix params (x0, x1) plus suffix params
    for alt in cont_alts:
        assert alt.action is not None, "Continuation should have action"
        # Prefix params (x0, x1) + suffix param (x or y) = 3 params
        assert len(alt.action.params) == 3, f"Continuation should have 3 params, got {len(alt.action.params)}"
        assert alt.action.params[0] == 'x0', "First param should be x0"
        assert alt.action.params[1] == 'x1', "Second param should be x1"

    print("✓ Continuation parameters are correct")


def test_let_with_no_common_prefix():
    """Test that rules without common prefix don't get Let-bindings."""
    grammar = Grammar()

    rule1 = Rule(
        lhs=Nonterminal("C"),
        rhs=Sequence([Literal("x"), Nonterminal("A")]),
        action=Lambda(params=['_', 'a'], body=Call('MakeC1', [Var('a', _any_type)])),
        grammar=grammar
    )

    rule2 = Rule(
        lhs=Nonterminal("C"),
        rhs=Sequence([Literal("y"), Nonterminal("B")]),
        action=Lambda(params=['_', 'b'], body=Call('MakeC2', [Var('b', _any_type)])),
        grammar=grammar
    )

    grammar.add_rule(rule1)
    grammar.add_rule(rule2)

    factored = grammar.left_factor()

    # Should have 2 rules unchanged (no common prefix)
    c_rules = factored.rules.get("C", [])
    assert len(c_rules) == 2, "Should have 2 rules (no factoring)"

    # Neither should use Let
    for rule in c_rules:
        if rule.action:
            assert not isinstance(rule.action.body, Let), "Should not use Let without factoring"

    print("✓ No Let-bindings for rules without common prefix")


def test_let_bindings_preserve_semantics():
    """Test that Let-bindings preserve the semantic structure."""
    grammar = Grammar()

    # Rule: D -> "(" "add" N N
    rule = Rule(
        lhs=Nonterminal("D"),
        rhs=Sequence([Literal("("), Literal("add"), Nonterminal("N"), Nonterminal("N")]),
        action=Lambda(params=['_', '_', 'n1', 'n2'], body=Call('Add', [Var('n1', _any_type), Var('n2', _any_type)])),
        grammar=grammar
    )

    # Another rule with different op but same structure
    rule2 = Rule(
        lhs=Nonterminal("D"),
        rhs=Sequence([Literal("("), Literal("sub"), Nonterminal("N"), Nonterminal("N")]),
        action=Lambda(params=['_', '_', 'n1', 'n2'], body=Call('Sub', [Var('n1', _any_type), Var('n2', _any_type)])),
        grammar=grammar
    )

    grammar.add_rule(rule)
    grammar.add_rule(rule2)

    factored = grammar.left_factor()

    # Factored rule should have Let-binding for "("
    d_rules = factored.rules.get("D", [])
    assert len(d_rules) == 1, "Should have factored D rule"

    factored_rule = d_rules[0]
    assert isinstance(factored_rule.action.body, Let), "Should use Let-binding"

    # The innermost expression should be a call to the continuation
    let_expr = factored_rule.action.body
    # Navigate to innermost expression
    while isinstance(let_expr, Let):
        let_expr = let_expr.body

    assert isinstance(let_expr, Call), "Innermost expression should be continuation call"

    print("✓ Let-bindings preserve semantic structure")


if __name__ == "__main__":
    test_let_binding_structure()
    test_continuation_receives_prefix_params()
    test_let_with_no_common_prefix()
    test_let_bindings_preserve_semantics()
    print("\n✓ All Let-binding tests passed")
