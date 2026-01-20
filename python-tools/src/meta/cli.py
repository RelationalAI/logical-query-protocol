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
from .parser_gen import generate_parse_functions
from .parser_gen_julia import generate_parser_julia


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
    parser.add_argument(
        "--parser",
        choices=["julia", "ir"],
        help="Generate a parser in the specified language (or 'ir' to dump target IR)"
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
    elif args.parser:
        generator = GrammarGenerator(proto_parser, verbose=True)
        grammar = generator.generate()

        if args.parser == "julia":
            reachable, _ = grammar.analysis.partition_nonterminals_by_reachability()
            reachable_set = set(reachable)
            # Build proto_messages dict for codegen keyword argument generation
            proto_messages = {}
            for _, msg in proto_parser.messages.items():
                proto_messages[(msg.module, msg.name)] = msg
            output_text = generate_parser_julia(grammar, reachable_set, proto_messages=proto_messages)
        elif args.parser == "ir":
            defns = generate_parse_functions(grammar)
            output_text = "\n\n".join(str(defn) for defn in defns)
        else:
            print(f"Error: Unknown parser language: {args.parser}", file=sys.stderr)
            return 1

        if args.output:
            args.output.write_text(output_text)
            print(f"Generated {args.parser} parser written to {args.output}")
        else:
            print(output_text)

    return 0


def main() -> int:
    """Main entry point."""
    args = parse_args()
    return run(args)


if __name__ == "__main__":
    exit(main())
