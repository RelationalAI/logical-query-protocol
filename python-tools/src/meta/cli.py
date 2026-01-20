#!/usr/bin/env python3
"""CLI tool for generating tools from protobuf specifications.

This module provides the main command-line entry point for the proto-to-grammar
generator.

The CLI parses one or more .proto files and generates a context-free grammar
with semantic actions. The grammar can be used to generate parsers and pretty
printers for the protobuf-defined message types.

Usage:
    python -m meta.cli example.proto --grammar -o output.txt

Options:
    proto_files: One or more .proto files to parse
    --grammar: Output the generated grammar
    -o, --output: Output file (stdout if not specified)

Example:
    $ python -m meta.cli proto/logic.proto proto/transactions.proto --grammar
    # Outputs the generated grammar showing all rules and semantic actions

The tool performs the following steps:
1. Parse all .proto files using ProtoParser
2. Generate grammar rules using GrammarGenerator
3. Detect and warn about unexpected unreachable nonterminals
4. Output the grammar in a readable format
"""

import argparse
import sys
from pathlib import Path

from .proto_parser import ProtoParser
from .grammar_gen import GrammarGenerator
from .proto_print import print_proto_spec


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Parse protobuf specifications and generate tools"
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
        help="Output file"
    )
    parser.add_argument(
        "--proto",
        action="store_true",
        help="Output the parsed protobuf specification"
    )
    parser.add_argument(
        "--grammar",
        action="store_true",
        help="Output the grammar"
    )
    return parser.parse_args()


def check_unreachable_nonterminals(grammar, generator):
    """Check for unexpected unreachable nonterminals and report warnings.

    Args:
        grammar: The generated grammar to analyze
        generator: The GrammarGenerator used to create the grammar

    Prints warnings to stdout if unexpected unreachable nonterminals are found.
    """
    _, unreachable = grammar.analysis.partition_nonterminals_by_reachability()
    unexpected_unreachable = [r for r in unreachable if r.name not in generator.expected_unreachable]
    if unexpected_unreachable:
        print("Warning: Unreachable nonterminals detected:")
        for rule in unexpected_unreachable:
            print(f"  {rule.name}")
        print()


def write_output(text, output_path, success_msg):
    """Write text to output file or stdout.

    Args:
        text: The text content to write
        output_path: Path object for output file, or None for stdout
        success_msg: Message to print on successful file write
    """
    if output_path:
        output_path.write_text(text)
        print(success_msg)
    else:
        print(text)


def run(args) -> int:
    """Execute the CLI command specified by args."""
    proto_parser = ProtoParser()
    for proto_file in args.proto_files:
        if not proto_file.exists():
            print(f"Error: File not found: {proto_file}", file=sys.stderr)
            return 1
        proto_parser.parse_file(proto_file)

    if args.proto:
        output_text = print_proto_spec(proto_parser)
        write_output(output_text, args.output, f"Protobuf spec written to {args.output}")

    if args.grammar:
        generator = GrammarGenerator(proto_parser, verbose=True)
        grammar = generator.generate()

        check_unreachable_nonterminals(grammar, generator)

        output_text = grammar.print_grammar()
        write_output(output_text, args.output, f"Generated grammar written to {args.output}")

    return 0


def main():
    """Main entry point for protobuf parser."""
    return run(parse_args())


if __name__ == "__main__":
    exit(main())
