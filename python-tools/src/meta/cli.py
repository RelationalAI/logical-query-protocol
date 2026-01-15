#!/usr/bin/env python3
"""CLI tool for validating grammar against protobuf specifications.

This module provides the main command-line entry point for loading and
validating a grammar file.

Usage:
    python -m meta.cli --grammar example.sexp example.proto --validate

Options:
    proto_files: One or more .proto files to parse
    --grammar: Path to grammar file (defaults to src/meta/grammar.sexp)
    --validate: Validate grammar covers protobuf spec
    -o, --output: Output file for writing the grammar in s-expression format (stdout if not specified)

Example:
    $ python -m meta.cli --grammar grammar.sexp proto/logic.proto proto/transactions.proto --validate
    # Validates the grammar against the protobuf specifications

    $ python -m meta.cli --grammar my_grammar.sexp proto/logic.proto --validate -o output.sexp
    # Validates a custom grammar file and outputs it

The tool performs the following steps:
1. Load grammar from the specified file (or default location)
2. Parse all .proto files using ProtoParser
3. Validate grammar against protobuf specification
4. Output the grammar if -o is specified
"""

import argparse
import sys
from pathlib import Path

from .proto_parser import ProtoParser
from .grammar_validator import validate_grammar
from .grammar import Grammar, Nonterminal
from .sexp_grammar import load_grammar_config_file
from .target import MessageType


def format_message(msg, indent=0):
    """Format a ProtoMessage for display."""
    prefix = "  " * indent
    lines = [f"{prefix}message {msg.name} {{"]

    for enum in msg.enums:
        lines.append(f"{prefix}  enum {enum.name} {{")
        for value_name, value_number in enum.values:
            lines.append(f"{prefix}    {value_name} = {value_number};")
        lines.append(f"{prefix}  }}")

    for oneof in msg.oneofs:
        lines.append(f"{prefix}  oneof {oneof.name} {{")
        for field in oneof.fields:
            lines.append(f"{prefix}    {field.type} {field.name} = {field.number};")
        lines.append(f"{prefix}  }}")

    for field in msg.fields:
        modifiers = []
        if field.is_repeated:
            modifiers.append("repeated")
        if field.is_optional:
            modifiers.append("optional")
        modifier_str = " ".join(modifiers) + " " if modifiers else ""
        lines.append(f"{prefix}  {modifier_str}{field.type} {field.name} = {field.number};")

    lines.append(f"{prefix}}}")
    return "\n".join(lines)


def format_enum(enum, indent=0):
    """Format a ProtoEnum for display."""
    prefix = "  " * indent
    lines = [f"{prefix}enum {enum.name} {{"]
    for value_name, value_number in enum.values:
        lines.append(f"{prefix}  {value_name} = {value_number};")
    lines.append(f"{prefix}}}")
    return "\n".join(lines)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Parse protobuf specifications and validate grammar"
    )
    parser.add_argument(
        "proto_files",
        nargs="+",
        type=Path,
        help="Protobuf files to parse"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file for grammar in s-expression format"
    )
    parser.add_argument(
        "--grammar",
        type=Path,
        help="Path to grammar file (defaults to src/meta/grammar.sexp)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate grammar covers protobuf spec"
    )
    return parser.parse_args()


def run(args) -> int:
    """Execute the CLI command specified by args."""
    # Determine grammar file path
    if args.grammar:
        grammar_path = args.grammar
    else:
        grammar_path = Path(__file__).parent / "grammar.sexp"

    if not grammar_path.exists():
        print(f"Error: Grammar file not found: {grammar_path}", file=sys.stderr)
        return 1

    # Load grammar rules from file
    grammar_config = load_grammar_config_file(grammar_path)

    # Build Grammar object from loaded config
    start = Nonterminal('transaction', MessageType('transactions', 'Transaction'))
    grammar = Grammar(start=start)
    for lhs, rules in grammar_config.items():
        for rule in rules:
            grammar.add_rule(rule)

    # Expected unreachable nonterminals (hardcoded from generator)
    expected_unreachable = {
        'debug_info',
        'debug_info_ids',
        'ivmconfig',
        'date_value',
        'datetime_value',
        'decimal_value',
        'int128_value',
        'missing_value',
        'uint128_value',
        'uint128_type',
        'datetime_type',
    }

    # Parse protobuf files for validation
    proto_parser = ProtoParser()
    for proto_file in args.proto_files:
        if not proto_file.exists():
            print(f"Error: File not found: {proto_file}", file=sys.stderr)
            return 1
        proto_parser.parse_file(proto_file)

    # Run validation (always run, but only print if requested or has errors)
    validation_result = validate_grammar(
        grammar,
        proto_parser,
        expected_unreachable,
    )

    if args.validate or not validation_result.is_valid:
        print(validation_result.summary())
        print()
        if not validation_result.is_valid:
            return 1

    # Output grammar if -o is specified
    if args.output:
        output_text = grammar.print_grammar_sexp()
        args.output.write_text(output_text)
        print(f"Grammar written to {args.output}")

    return 0


def main():
    """Main entry point for protobuf parser."""
    return run(parse_args())


if __name__ == "__main__":
    exit(main())
