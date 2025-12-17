#!/usr/bin/env python3
"""Tests for parser generation with left-factoring."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.grammar import (
    Grammar, Rule, Nonterminal, Sequence, LitTerminal, NamedTerminal
)
from meta.target import Lambda, Var, Call, Builtin, BaseType, MessageType
from meta.parser_gen_python import generate_parser_python

_int64_type = BaseType("Int64")


def test_parser_execution():
    """Test that generated parser can actually parse input."""
    start = Nonterminal("expr", MessageType("proto", "Expr"))
    grammar = Grammar(start=start)
    from meta.grammar import Token

    # Simple grammar: expr -> "(" "op" NUMBER ")"
    grammar.add_rule(Rule(
        lhs=Nonterminal("start", MessageType("proto", "Expr")),
        rhs=Nonterminal("expr", MessageType("proto", "Expr")),
        action=Lambda([Var('e', MessageType("proto", "Expr"))], MessageType("proto", "Expr"), Var('e', MessageType("proto", "Expr"))),
    ))

    grammar.add_rule(Rule(
        lhs=Nonterminal("expr", MessageType("proto", "Expr")),
        rhs=Sequence((
            LitTerminal("("),
            LitTerminal("op"),
            NamedTerminal("NUMBER", _int64_type),
            LitTerminal(")")
        )),
        action=Lambda([Var('n', _int64_type)], MessageType("proto", "Expr"), Var('n', _int64_type)),
    ))

    grammar.tokens.append(Token("NUMBER", r'\d+', _int64_type))

    print("\nGenerating and testing parser execution...")

    try:
        parser_code = generate_parser_python(grammar, reachable=set())

        # Write to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(parser_code)
            temp_path = f.name

        # Import and test
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_parser", temp_path)
        if spec is None or spec.loader is None:
            print("✗ Failed to load parser module")
            return False
        test_parser = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_parser)

        # Parse valid input
        result = test_parser.parse("(op 42)")
        print(f"✓ Successfully parsed '(op 42)': {result}")

        # Test invalid input
        try:
            test_parser.parse("(invalid 42)")
            print("✗ Should have rejected invalid input")
            return False
        except test_parser.ParseError:
            print("✓ Correctly rejects invalid input")

        # Clean up
        Path(temp_path).unlink()

        return True

    except Exception as e:
        print(f"✗ Error in parser execution test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = True

    if not test_parser_execution():
        success = False

    if success:
        print("\n✓ All parser generation tests passed")
    else:
        print("\n✗ Some parser generation tests failed")
        sys.exit(1)
