#!/usr/bin/env python3
"""CLI tool for generating grammar from protobuf specifications.

This module provides the main command-line entry point for the proto-to-grammar
generator.
"""

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from .proto_parser import ProtoParser
from .grammar_gen import GrammarGenerator, generate_semantic_actions

def main():
    """Main entry point for proto-to-grammar."""
    parser = argparse.ArgumentParser(
        description="Generate grammar from protobuf specifications"
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
        help="Output file for generated grammar"
    )
    parser.add_argument(
        "--grammar",
        action="store_true",
        help="Output the grammar"
    )
    args = parser.parse_args()

    proto_parser = ProtoParser()
    for proto_file in args.proto_files:
        if not proto_file.exists():
            print(f"Error: File not found: {proto_file}")
            return 1
        proto_parser.parse_file(proto_file)

    generator = GrammarGenerator(proto_parser, verbose=True)
    grammar = generator.generate()

    unreachable = grammar.get_unreachable_nonterminals()
    unexpected_unreachable = [r for r in unreachable if r.name not in generator.expected_unreachable]
    if unexpected_unreachable:
        print("Warning: Unreachable nonterminals detected:")
        for rule in unexpected_unreachable:
            print(f"  {rule.name}")
        print()

    if args.grammar:
        output_text = grammar.print_grammar(grammar.compute_reachability())
    else:
        output_text = generate_semantic_actions(grammar, grammar.compute_reachability())

    if args.output:
        args.output.write_text(output_text)
        print(f"Generated grammar written to {args.output}")
    else:
        print(output_text)

    return 0


if __name__ == "__main__":
    exit(main())
