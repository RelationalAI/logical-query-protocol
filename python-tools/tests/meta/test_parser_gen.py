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
from meta.parser_python import generate_parser_python

_int64_type = BaseType("Int64")


def test_parser_with_left_factoring():
    """Test that parser generation works with left-factored grammar."""
    start = Nonterminal("start", MessageType("Transaction"))
    grammar = Grammar(start=start)

    # Add start rule
    grammar.add_rule(Rule(
        lhs=Nonterminal("start", MessageType("Expr")),
        rhs=Nonterminal("expr", MessageType("Expr")),
        action=Lambda([Var('e', MessageType("Expr"))], MessageType("Expr"), Var('e', MessageType("Expr"))),
        grammar=grammar
    ))

    # Create rules with common prefix
    rule1 = Rule(
        lhs=Nonterminal("expr", MessageType("Expr")),
        rhs=Sequence([
            LitTerminal("("),
            LitTerminal("add"),
            Nonterminal("term", MessageType("Term")),
            Nonterminal("term", MessageType("Term")),
            LitTerminal(")")
        ]),
        action=Lambda(
            [Var('t1', MessageType("Term")), Var('t2', MessageType("Term"))],
            MessageType("Expr"),
            Call('Add', [Var('t1', MessageType("Term")), Var('t2', MessageType("Term"))])
        ),
        grammar=grammar
    )

    rule2 = Rule(
        lhs=Nonterminal("expr", MessageType("Expr")),
        rhs=Sequence([
            LitTerminal("("),
            LitTerminal("sub"),
            Nonterminal("term", MessageType("Term")),
            Nonterminal("term", MessageType("Term")),
            LitTerminal(")")
        ]),
        action=Lambda(
            [Var('t1', MessageType("Term")), Var('t2', MessageType("Term"))],
            MessageType("Expr"),
            Call('Sub', [Var('t1', MessageType("Term")), Var('t2', MessageType("Term"))])
        ),
        grammar=grammar
    )

    grammar.add_rule(rule1)
    grammar.add_rule(rule2)

    # Add term rule
    grammar.add_rule(Rule(
        lhs=Nonterminal("term", MessageType("Term")),
        rhs=NamedTerminal("NUMBER", _int64_type),
        action=Lambda([Var('n', _int64_type)], MessageType("Term"), Var('n', _int64_type)),
        grammar=grammar
    ))

    # Add tokens
    from meta.grammar import Token
    grammar.tokens.append(Token("NUMBER", r'\d+', Lambda([Var('lexeme', _int64_type)], _int64_type, Call(Builtin('parse_number'), [Var('lexeme', _int64_type)]))))

    print("Generating parser...")

    try:
        parser_code = generate_parser_python(grammar, reachable=None)

        # Check for key features
        assert "def parse_expr_cont_" in parser_code, "Should generate continuation method"
        assert "prefix_results" in parser_code, "Should have prefix results parameter"
        assert "Parse common prefix" in parser_code, "Should have prefix parsing comment"

        # Save for inspection
        output_path = Path("/tmp/test_generated_parser.py")
        output_path.write_text(parser_code)

        print(f"✓ Parser generated successfully")
        print(f"  Output saved to {output_path}")

        return True

    except Exception as e:
        print(f"✗ Error generating parser: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parser_execution():
    """Test that generated parser can actually parse input."""
    start = Nonterminal("expr", MessageType("Expr"))
    grammar = Grammar(start=start)
    from meta.grammar import Token

    # Simple grammar: expr -> "(" "op" NUMBER ")"
    grammar.add_rule(Rule(
        lhs=Nonterminal("start", MessageType("Expr")),
        rhs=Nonterminal("expr", MessageType("Expr")),
        action=Lambda([Var('e', MessageType("Expr"))], MessageType("Expr"), Var('e', MessageType("Expr"))),
        grammar=grammar
    ))

    grammar.add_rule(Rule(
        lhs=Nonterminal("expr", MessageType("Expr")),
        rhs=Sequence([
            LitTerminal("("),
            LitTerminal("op"),
            NamedTerminal("NUMBER", _int64_type),
            LitTerminal(")")
        ]),
        action=Lambda([Var('n', _int64_type)], MessageType("Expr"), Var('n', _int64_type)),
        grammar=grammar
    ))

    grammar.tokens.append(Token("NUMBER", r'\d+', Lambda([Var('lexeme', _int64_type)], _int64_type, Call(Builtin('parse_number'), [Var('lexeme', _int64_type)]))))

    print("\nGenerating and testing parser execution...")

    try:
        parser_code = generate_parser_python(grammar, reachable=None)

        # Write to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(parser_code)
            temp_path = f.name

        # Import and test
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_parser", temp_path)
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

    if not test_parser_with_left_factoring():
        success = False

    if not test_parser_execution():
        success = False

    if success:
        print("\n✓ All parser generation tests passed")
    else:
        print("\n✗ Some parser generation tests failed")
        sys.exit(1)
