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
from .parser_gen_python import generate_parser_python
from .parser_gen_go import generate_parser_go
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
        "--grammar",
        action="store_true",
        help="Output the grammar"
    )
    parser.add_argument(
        "--proto",
        action="store_true",
        help="Output the parsed protobuf specification"
    )
    parser.add_argument(
        "--parser",
        choices=["python", "go", "julia", "ir"],
        help="Generate a parser in the specified language (or 'ir' to dump target IR)"
    )
    args = parser.parse_args()


def run(args) -> int:
    """Execute the CLI command specified by args."""
    proto_parser = ProtoParser()
    for proto_file in args.proto_files:
        if not proto_file.exists():
            print(f"Error: File not found: {proto_file}", file=sys.stderr)
            return 1
        proto_parser.parse_file(proto_file)

    if args.proto:
        # Output parsed proto specification
        output_text = print_proto_spec(proto_parser)
        if args.output:
            args.output.write_text(output_text)
            print(f"Parsed proto specification written to {args.output}")
        else:
            print(output_text)

    if args.grammar:
        generator = GrammarGenerator(proto_parser, verbose=True)
        grammar = generator.generate()

        _, unreachable = grammar.analysis.partition_nonterminals_by_reachability()
        unexpected_unreachable = [r for r in unreachable if r.name not in generator.expected_unreachable]
        if unexpected_unreachable:
            print("Warning: Unreachable nonterminals detected:")
            for rule in unexpected_unreachable:
                print(f"  {rule.name}")
            print()

        output_text = grammar.print_grammar()
        if args.output:
            args.output.write_text(output_text)
            print(f"Generated grammar written to {args.output}")
        else:
            print(output_text)
    elif args.parser:
        generator = GrammarGenerator(proto_parser, verbose=True)
        grammar = generator.generate()

        if args.parser == "python":
            reachable, _ = grammar.analysis.partition_nonterminals_by_reachability()
            reachable_set = set(reachable)
            # Build proto_messages dict for codegen keyword argument generation
            proto_messages = {}
            for msg_name, msg in proto_parser.messages.items():
                proto_messages[(msg.module, msg.name)] = msg
            output_text = generate_parser_python(grammar, reachable_set, proto_messages=proto_messages)
        elif args.parser == "go":
            output_text = generate_parser_go(grammar)
        elif args.parser == "julia":
            output_text = generate_parser_julia(grammar)
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


if __name__ == "__main__":
    exit(main())
