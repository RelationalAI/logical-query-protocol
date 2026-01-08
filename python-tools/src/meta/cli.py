#!/usr/bin/env python3
<<<<<<< HEAD
"""CLI tool for generating grammar from protobuf specifications.

This module provides the main command-line entry point for the proto-to-grammar
generator.
=======
"""CLI tool for parsing protobuf specifications.

This module provides the main command-line entry point for the protobuf parser.
>>>>>>> origin/main
"""

import argparse
import sys
from pathlib import Path
<<<<<<< HEAD
from typing import TYPE_CHECKING

from .proto_parser import ProtoParser
from .grammar_gen import GrammarGenerator, generate_semantic_actions

def main():
    """Main entry point for proto-to-grammar."""
    parser = argparse.ArgumentParser(
        description="Generate grammar from protobuf specifications"
=======

from .proto_parser import ProtoParser


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


def main():
    """Main entry point for protobuf parser."""
    parser = argparse.ArgumentParser(
        description="Parse protobuf specifications"
>>>>>>> origin/main
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
<<<<<<< HEAD
        help="Output file for generated grammar"
    )
    parser.add_argument(
        "--grammar",
        action="store_true",
        help="Output the grammar"
=======
        help="Output file for parsed protobuf specifications"
>>>>>>> origin/main
    )
    args = parser.parse_args()

    proto_parser = ProtoParser()
    for proto_file in args.proto_files:
        if not proto_file.exists():
<<<<<<< HEAD
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
=======
            print(f"Error: File not found: {proto_file}", file=sys.stderr)
            return 1
        proto_parser.parse_file(proto_file)

    output_lines = []
    for msg in proto_parser.messages.values():
        output_lines.append(format_message(msg))
        output_lines.append("")

    for enum in proto_parser.enums.values():
        output_lines.append(format_enum(enum))
        output_lines.append("")

    output = "\n".join(output_lines)

    if args.output:
        args.output.write_text(output)
        print(f"Parsed protobuf written to {args.output}", file=sys.stderr)
    else:
        print(output)
>>>>>>> origin/main

    return 0


if __name__ == "__main__":
    exit(main())
