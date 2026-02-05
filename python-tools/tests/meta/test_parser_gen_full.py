#!/usr/bin/env python3
"""Tests for parser generation on full protobuf specifications.

These tests verify that both Python and Julia parser generators can process
the complete LQP protobuf specification without errors.
"""

import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


# Paths to the actual proto and grammar files
PROTO_DIR = Path(__file__).parent.parent.parent.parent / "proto" / "relationalai" / "lqp" / "v1"
GRAMMAR_PATH = Path(__file__).parent.parent.parent / "src" / "meta" / "grammar.y"


def get_proto_files():
    """Get all proto files in the proto directory."""
    if not PROTO_DIR.exists():
        pytest.skip(f"Proto directory not found: {PROTO_DIR}")
    proto_files = list(PROTO_DIR.glob("*.proto"))
    if not proto_files:
        pytest.skip(f"No proto files found in {PROTO_DIR}")
    return proto_files


def load_grammar_and_protos():
    """Load grammar and proto specifications.

    Returns:
        tuple: (grammar, proto_messages)
    """
    from meta.proto_parser import ProtoParser
    from meta.yacc_parser import load_yacc_grammar_file
    from meta.grammar import Grammar, Token

    proto_files = get_proto_files()

    if not GRAMMAR_PATH.exists():
        pytest.skip(f"Grammar file not found: {GRAMMAR_PATH}")

    # Parse proto files
    proto_parser = ProtoParser()
    for proto_file in proto_files:
        proto_parser.parse_file(proto_file)

    # Load grammar config from file
    grammar_config = load_yacc_grammar_file(GRAMMAR_PATH)

    # Build Grammar object from config (same as cli.py does)
    start = None
    for nt in grammar_config.rules.keys():
        if nt.name == grammar_config.start_symbol:
            start = nt
            break
    if start is None:
        pytest.fail(f"Start symbol '{grammar_config.start_symbol}' has no rules")

    grammar = Grammar(
        start=start,
        ignored_completeness=grammar_config.ignored_completeness,
        function_defs=grammar_config.function_defs
    )
    for _, rules in grammar_config.rules.items():
        for rule in rules:
            grammar.add_rule(rule)

    # Add tokens with patterns from terminal declarations
    for terminal_name, terminal_def in grammar_config.terminal_patterns.items():
        if terminal_def.pattern is not None:
            grammar.tokens.append(Token(terminal_name, terminal_def.pattern, terminal_def.type))

    # Transform messages dict from {name: ProtoMessage} to {(module, name): ProtoMessage}
    proto_messages = {(msg.module, name): msg for name, msg in proto_parser.messages.items()}

    return grammar, proto_messages


class TestPythonParserGeneratorFull:
    """Test Python parser generator on full protobuf spec."""

    def test_generate_parser_python_completes(self):
        """Test that Python parser generation completes without error."""
        from meta.parser_gen_python import generate_parser_python

        grammar, proto_messages = load_grammar_and_protos()

        # Generate parser - should complete without error
        output = generate_parser_python(grammar, command_line="test", proto_messages=proto_messages)

        # Basic sanity checks on output
        assert output is not None
        assert len(output) > 0
        assert "class Parser" in output
        assert "def parse" in output

    def test_generated_python_has_valid_syntax(self):
        """Test that generated Python parser has valid syntax."""
        import ast
        from meta.parser_gen_python import generate_parser_python

        grammar, proto_messages = load_grammar_and_protos()

        output = generate_parser_python(grammar, command_line="test", proto_messages=proto_messages)

        # Parse the generated code to check syntax
        try:
            ast.parse(output)
        except SyntaxError as e:
            pytest.fail(f"Generated Python code has syntax error: {e}")


class TestJuliaParserGeneratorFull:
    """Test Julia parser generator on full protobuf spec."""

    def test_generate_parser_julia_completes(self):
        """Test that Julia parser generation completes without error."""
        from meta.parser_gen_julia import generate_parser_julia

        grammar, proto_messages = load_grammar_and_protos()

        # Generate parser - should complete without error
        output = generate_parser_julia(grammar, command_line="test", proto_messages=proto_messages)

        # Basic sanity checks on output
        assert output is not None
        assert len(output) > 0
        assert "struct Parser" in output
        assert "function parse(" in output

    def test_generated_julia_has_expected_structure(self):
        """Test that generated Julia parser has expected structure."""
        from meta.parser_gen_julia import generate_parser_julia

        grammar, proto_messages = load_grammar_and_protos()

        output = generate_parser_julia(grammar, command_line="test", proto_messages=proto_messages)

        # Check for expected Julia constructs
        assert "struct Token" in output
        assert "struct Lexer" in output or "mutable struct Lexer" in output
        assert "function tokenize!" in output
        assert "function lookahead" in output
        assert "function consume_literal!" in output
        assert "function consume_terminal!" in output


class TestParserGeneratorConsistency:
    """Test consistency between Python and Julia parser generators."""

    def test_both_generators_produce_same_parse_functions(self):
        """Test that both generators produce parse functions for the same nonterminals."""
        from meta.parser_gen_python import generate_parser_python
        from meta.parser_gen_julia import generate_parser_julia
        import re

        grammar, proto_messages = load_grammar_and_protos()

        python_output = generate_parser_python(grammar, command_line="test", proto_messages=proto_messages)
        julia_output = generate_parser_julia(grammar, command_line="test", proto_messages=proto_messages)

        # Extract parse function names from Python (def parse_xxx)
        python_parse_funcs = set(re.findall(r'def (parse_\w+)\(', python_output))

        # Extract parse function names from Julia (function parse_xxx)
        julia_parse_funcs = set(re.findall(r'function (parse_\w+)\(', julia_output))

        # Both should have the same parse functions (modulo the main 'parse' function)
        python_parse_funcs.discard('parse')
        julia_parse_funcs.discard('parse')

        assert python_parse_funcs == julia_parse_funcs, \
            f"Parse function mismatch:\nPython only: {python_parse_funcs - julia_parse_funcs}\nJulia only: {julia_parse_funcs - python_parse_funcs}"
