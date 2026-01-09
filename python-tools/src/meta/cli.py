#!/usr/bin/env python3
"""CLI tool for generating tools from protobuf specifications.

This module provides the main command-line entry point for the proto-to-grammar
generator.
"""

import argparse
import sys
from pathlib import Path

from .proto_parser import ProtoParser
from .grammar_gen import GrammarGenerator
from .proto_print import format_message, format_enum


def main():
    """Main entry point for protobuf parser."""
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
    args = parser.parse_args()

    proto_parser = ProtoParser()
    for proto_file in args.proto_files:
        if not proto_file.exists():
            print(f"Error: File not found: {proto_file}", file=sys.stderr)
            return 1
        proto_parser.parse_file(proto_file)

    if args.proto:
        # Output parsed proto specification
        lines = []
        for msg_name, msg in sorted(proto_parser.messages.items()):
            lines.append(format_message(msg))
            lines.append("")

        for enum_name, enum in sorted(proto_parser.enums.items()):
            lines.append(format_enum(enum))
            lines.append("")

        output_text = "\n".join(lines)
        if args.output:
            args.output.write_text(output_text)
            print(f"Parsed proto specification written to {args.output}")
        else:
            print(output_text)
    elif args.grammar:
        generator = GrammarGenerator(proto_parser, verbose=True)
        grammar = generator.generate()

        _, unreachable = grammar.partition_nonterminals()
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

    return 0


if __name__ == "__main__":
    exit(main())
