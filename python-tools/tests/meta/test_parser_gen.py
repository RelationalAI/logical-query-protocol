#!/usr/bin/env python3
"""Tests for parser generation with left-factoring."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.grammar import (
    Grammar, Rule, Nonterminal, Sequence, LitTerminal, NamedTerminal
)
from meta.target import Lambda, Var, BaseType, MessageType
from meta.parser_gen_python import generate_parser_python

_int64_type = BaseType("Int64")


def test_parser_execution():
    """Test that generated parser can actually parse input.

    This test requires the LQP proto modules to be available.
    """
    import pytest
    pytest.skip("Test requires LQP proto modules to be available")
    # Use logic_pb2 module which is actually imported by the generated parser
    expr_type = MessageType("logic", "Expr")
    start = Nonterminal("expr", expr_type)
    grammar = Grammar(start=start)
    from meta.grammar import Token

    # Simple grammar: expr -> "(" "op" NUMBER ")"
    grammar.add_rule(Rule(
        lhs=Nonterminal("start", expr_type),
        rhs=Nonterminal("expr", expr_type),
        constructor=Lambda([Var('e', expr_type)], expr_type, Var('e', expr_type)),
    ))

    grammar.add_rule(Rule(
        lhs=Nonterminal("expr", expr_type),
        rhs=Sequence((
            LitTerminal("("),
            LitTerminal("op"),
            NamedTerminal("NUMBER", _int64_type),
            LitTerminal(")"),
        )),
        constructor=Lambda([Var('n', _int64_type)], expr_type, Var('n', _int64_type)),
    ))

    grammar.tokens.append(Token("NUMBER", r'\d+', _int64_type))

    parser_code = generate_parser_python(grammar, reachable=None)

    # Write to temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(parser_code)
        temp_path = f.name

    # Import and test
    import importlib.util
    spec = importlib.util.spec_from_file_location("test_parser", temp_path)
    assert spec is not None, "Failed to create module spec"
    test_parser = importlib.util.module_from_spec(spec)
    assert spec.loader is not None, "Module spec has no loader"
    spec.loader.exec_module(test_parser)

    # Parse valid input
    result = test_parser.parse("(op 42)")
    assert result is not None, "Parser returned None for valid input"

    # Test invalid input
    with pytest.raises(test_parser.ParseError):
        test_parser.parse("(invalid 42)")

    # Clean up
    Path(temp_path).unlink()
