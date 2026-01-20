#!/usr/bin/env python3
"""Tests for parser generation IR."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.grammar import Grammar, Rule, Nonterminal, LitTerminal
from meta.target import Lambda, Var, MessageType, VisitNonterminalDef
from meta.parser_gen import generate_parse_functions


def test_generate_parse_functions_simple():
    """Test that generate_parse_functions produces VisitNonterminalDef for each nonterminal."""
    # Create a simple grammar: S -> "a"
    s_type = MessageType("test", "S")
    s = Nonterminal("S", s_type)
    lit_a = LitTerminal("a")

    grammar = Grammar(start=s)
    action = Lambda([], s_type, Var("result", s_type))
    grammar.add_rule(Rule(s, lit_a, action, action))

    # Generate parse functions
    defs = generate_parse_functions(grammar)

    # Should have one definition for S
    assert len(defs) == 1
    assert isinstance(defs[0], VisitNonterminalDef)
    assert defs[0].nonterminal == s


def test_generate_parse_functions_multiple_alternatives():
    """Test parser generation with multiple alternatives."""
    # Grammar: S -> "a" | "b"
    s_type = MessageType("test", "S")
    s = Nonterminal("S", s_type)
    lit_a = LitTerminal("a")
    lit_b = LitTerminal("b")

    grammar = Grammar(start=s)
    action = Lambda([], s_type, Var("result", s_type))
    grammar.add_rule(Rule(s, lit_a, action, action))
    grammar.add_rule(Rule(s, lit_b, action, action))

    defs = generate_parse_functions(grammar)

    assert len(defs) == 1
    assert defs[0].nonterminal == s


def test_generate_parse_functions_with_nonterminal():
    """Test parser generation when RHS contains a nonterminal."""
    # Grammar: S -> A, A -> "a"
    s_type = MessageType("test", "S")
    a_type = MessageType("test", "A")
    s = Nonterminal("S", s_type)
    a = Nonterminal("A", a_type)
    lit_a = LitTerminal("a")

    grammar = Grammar(start=s)
    action_s = Lambda([Var("x", a_type)], s_type, Var("x", a_type))
    action_a = Lambda([], a_type, Var("result", a_type))
    grammar.add_rule(Rule(s, a, action_s, action_s))
    grammar.add_rule(Rule(a, lit_a, action_a, action_a))

    defs = generate_parse_functions(grammar)

    # Should have definitions for both S and A
    assert len(defs) == 2
    nonterminal_names = {d.nonterminal.name for d in defs}
    assert nonterminal_names == {"S", "A"}


if __name__ == "__main__":
    test_generate_parse_functions_simple()
    test_generate_parse_functions_multiple_alternatives()
    test_generate_parse_functions_with_nonterminal()
    print("\n✓ All parser generation IR tests passed")
