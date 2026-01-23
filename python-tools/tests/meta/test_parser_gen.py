#!/usr/bin/env python3
"""Tests for parser generation IR."""

import sys
from pathlib import Path
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.grammar import Grammar, Rule, Nonterminal, LitTerminal, NamedTerminal, Option, Star, Sequence
from meta.target import Lambda, Var, MessageType, VisitNonterminalDef, BaseType, ListType
from meta.parser_gen import generate_parse_functions, GrammarConflictError, AmbiguousGrammarError


def test_generate_parse_functions_simple():
    """Test that generate_parse_functions produces VisitNonterminalDef for each nonterminal."""
    # Create a simple grammar: S -> "a"
    s_type = MessageType("test", "S")
    s = Nonterminal("S", s_type)
    lit_a = LitTerminal("a")

    grammar = Grammar(start=s)
    action = Lambda([], s_type, Var("result", s_type))
    grammar.add_rule(Rule(s, lit_a, action))

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
    grammar.add_rule(Rule(s, lit_a, action))
    grammar.add_rule(Rule(s, lit_b, action))

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
    grammar.add_rule(Rule(s, a, action_s))
    grammar.add_rule(Rule(a, lit_a, action_a))

    defs = generate_parse_functions(grammar)

    # Should have definitions for both S and A
    assert len(defs) == 2
    nonterminal_names = {d.nonterminal.name for d in defs}
    assert nonterminal_names == {"S", "A"}


def test_generate_parse_functions_with_option():
    """Test parser generation with Option operator."""
    # Grammar: S -> "a" A? where A -> "b"
    s_type = MessageType("test", "S")
    a_type = MessageType("test", "A")
    s = Nonterminal("S", s_type)
    a = Nonterminal("A", a_type)
    lit_a = LitTerminal("a")
    lit_b = LitTerminal("b")

    grammar = Grammar(start=s)
    action_a = Lambda([], a_type, Var("result", a_type))
    grammar.add_rule(Rule(a, lit_b, action_a))

    # S -> "a" A?
    rhs = Sequence((lit_a, Option(a)))
    action_s = Lambda([Var("opt", a_type)], s_type, Var("opt", a_type))
    grammar.add_rule(Rule(s, rhs, action_s))

    defs = generate_parse_functions(grammar)

    assert len(defs) == 2
    nonterminal_names = {d.nonterminal.name for d in defs}
    assert nonterminal_names == {"S", "A"}


def test_generate_parse_functions_with_star():
    """Test parser generation with Star operator."""
    # Grammar: S -> A* where A -> "a"
    s_type = MessageType("test", "S")
    a_type = MessageType("test", "A")
    s = Nonterminal("S", s_type)
    a = Nonterminal("A", a_type)
    lit_a = LitTerminal("a")

    grammar = Grammar(start=s)
    action_a = Lambda([], a_type, Var("result", a_type))
    grammar.add_rule(Rule(a, lit_a, action_a))

    # S -> A*
    rhs = Star(a)
    list_type = ListType(a_type)
    action_s = Lambda([Var("list", list_type)], s_type, Var("list", list_type))
    grammar.add_rule(Rule(s, rhs, action_s))

    defs = generate_parse_functions(grammar)

    assert len(defs) == 2
    nonterminal_names = {d.nonterminal.name for d in defs}
    assert nonterminal_names == {"S", "A"}


def test_generate_parse_functions_ll2():
    """Test parser generation requiring LL(2) lookahead."""
    # Grammar: S -> "a" "b" | "a" "c"
    # Requires lookahead of 2 to distinguish alternatives
    s_type = MessageType("test", "S")
    s = Nonterminal("S", s_type)
    lit_a = LitTerminal("a")
    lit_b = LitTerminal("b")
    lit_c = LitTerminal("c")

    grammar = Grammar(start=s)
    action = Lambda([], s_type, Var("result", s_type))

    # S -> "a" "b"
    rhs1 = Sequence((lit_a, lit_b))
    grammar.add_rule(Rule(s, rhs1, action))

    # S -> "a" "c"
    rhs2 = Sequence((lit_a, lit_c))
    grammar.add_rule(Rule(s, rhs2, action))

    defs = generate_parse_functions(grammar)

    assert len(defs) == 1
    assert defs[0].nonterminal == s


def test_generate_parse_functions_ll3():
    """Test parser generation requiring LL(3) lookahead."""
    # Grammar: S -> "a" "b" "c" | "a" "b" "d"
    # Requires lookahead of 3 to distinguish alternatives
    s_type = MessageType("test", "S")
    s = Nonterminal("S", s_type)
    lit_a = LitTerminal("a")
    lit_b = LitTerminal("b")
    lit_c = LitTerminal("c")
    lit_d = LitTerminal("d")

    grammar = Grammar(start=s)
    action = Lambda([], s_type, Var("result", s_type))

    # S -> "a" "b" "c"
    rhs1 = Sequence((lit_a, lit_b, lit_c))
    grammar.add_rule(Rule(s, rhs1, action))

    # S -> "a" "b" "d"
    rhs2 = Sequence((lit_a, lit_b, lit_d))
    grammar.add_rule(Rule(s, rhs2, action))

    defs = generate_parse_functions(grammar)

    assert len(defs) == 1
    assert defs[0].nonterminal == s


def test_generate_parse_functions_with_epsilon():
    """Test parser generation with epsilon production."""
    # Grammar: S -> "a" | ε
    s_type = MessageType("test", "S")
    s = Nonterminal("S", s_type)
    lit_a = LitTerminal("a")

    grammar = Grammar(start=s)
    action = Lambda([], s_type, Var("result", s_type))

    # S -> "a"
    grammar.add_rule(Rule(s, lit_a, action))

    # S -> ε
    epsilon = Sequence(())
    grammar.add_rule(Rule(s, epsilon, action))

    defs = generate_parse_functions(grammar)

    assert len(defs) == 1
    assert defs[0].nonterminal == s


def test_generate_parse_functions_with_named_terminal():
    """Test parser generation with named terminals."""
    # Grammar: S -> ID where ID is a named terminal
    s_type = MessageType("test", "S")
    s = Nonterminal("S", s_type)
    id_terminal = NamedTerminal("ID", BaseType("String"))

    grammar = Grammar(start=s)
    action = Lambda([Var("id", BaseType("String"))], s_type, Var("id", BaseType("String")))
    grammar.add_rule(Rule(s, id_terminal, action))

    defs = generate_parse_functions(grammar)

    assert len(defs) == 1
    assert defs[0].nonterminal == s


def test_generate_parse_functions_unreachable_nonterminal():
    """Test that unreachable nonterminals are not included."""
    # Grammar: S -> "a", B -> "b" (B is unreachable)
    s_type = MessageType("test", "S")
    b_type = MessageType("test", "B")
    s = Nonterminal("S", s_type)
    b = Nonterminal("B", b_type)
    lit_a = LitTerminal("a")
    lit_b = LitTerminal("b")

    grammar = Grammar(start=s)
    action_s = Lambda([], s_type, Var("result", s_type))
    action_b = Lambda([], b_type, Var("result", b_type))
    grammar.add_rule(Rule(s, lit_a, action_s))
    grammar.add_rule(Rule(b, lit_b, action_b))

    defs = generate_parse_functions(grammar)

    # Only S should be generated (B is unreachable)
    assert len(defs) == 1
    assert defs[0].nonterminal == s


def test_ll4_conflict_detection():
    """Test that LL(k) conflicts beyond MAX_LOOKAHEAD are detected."""
    # Grammar that requires LL(4): S -> "a" "a" "a" "b" | "a" "a" "a" "c"
    # This should fail if MAX_LOOKAHEAD is 3
    s_type = MessageType("test", "S")
    s = Nonterminal("S", s_type)
    lit_a = LitTerminal("a")
    lit_b = LitTerminal("b")
    lit_c = LitTerminal("c")

    grammar = Grammar(start=s)
    action = Lambda([], s_type, Var("result", s_type))

    # S -> "a" "a" "a" "b"
    rhs1 = Sequence((lit_a, lit_a, lit_a, lit_b))
    grammar.add_rule(Rule(s, rhs1, action))

    # S -> "a" "a" "a" "c"
    rhs2 = Sequence((lit_a, lit_a, lit_a, lit_c))
    grammar.add_rule(Rule(s, rhs2, action))

    # This should raise a GrammarConflictError
    with pytest.raises(GrammarConflictError, match="Grammar conflict"):
        generate_parse_functions(grammar)


def test_complex_star_sequence():
    """Test Star in a complex sequence."""
    # Grammar: S -> "(" A* ")" where A -> "a"
    s_type = MessageType("test", "S")
    a_type = MessageType("test", "A")
    s = Nonterminal("S", s_type)
    a = Nonterminal("A", a_type)
    lit_lparen = LitTerminal("(")
    lit_rparen = LitTerminal(")")
    lit_a = LitTerminal("a")

    grammar = Grammar(start=s)
    action_a = Lambda([], a_type, Var("result", a_type))
    grammar.add_rule(Rule(a, lit_a, action_a))

    # S -> "(" A* ")"
    rhs = Sequence((lit_lparen, Star(a), lit_rparen))
    action_s = Lambda([Var("list", ListType(a_type))], s_type, Var("list", ListType(a_type)))
    grammar.add_rule(Rule(s, rhs, action_s))

    # Should generate successfully since ")" provides clear boundary
    defs = generate_parse_functions(grammar)
    assert len(defs) == 2


if __name__ == "__main__":
    test_generate_parse_functions_simple()
    test_generate_parse_functions_multiple_alternatives()
    test_generate_parse_functions_with_nonterminal()
    test_generate_parse_functions_with_option()
    test_generate_parse_functions_with_star()
    test_generate_parse_functions_ll2()
    test_generate_parse_functions_ll3()
    test_generate_parse_functions_with_epsilon()
    test_generate_parse_functions_with_named_terminal()
    test_generate_parse_functions_unreachable_nonterminal()
    test_ll4_conflict_detection()
    test_complex_star_sequence()
    print("\n✓ All parser generation IR tests passed")
