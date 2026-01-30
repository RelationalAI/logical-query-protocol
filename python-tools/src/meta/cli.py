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
    --proto: Output the parsed protobuf specification
    --grammar: Output the generated grammar
    --parser {ir,python}: Output the generated parser (as IR or Python)
    -o, --output: Output file (stdout if not specified)

Example:
    $ python -m meta.cli proto/logic.proto proto/transactions.proto --grammar
    # Outputs the generated grammar showing all rules and semantic actions

    $ python -m meta.cli proto/logic.proto --parser python -o parser.py
    # Generates a Python parser and writes it to parser.py

    $ python -m meta.cli proto/logic.proto --parser ir
    # Outputs the parser intermediate representation

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
from .grammar_validator import GrammarValidator


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
        type=str,
        choices=["ir", "python"],
        help="Output the generated parser (ir or python)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the generated grammar against protobuf spec"
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

    if args.parser:
        generator = GrammarGenerator(proto_parser, verbose=True)
        grammar = generator.generate()

        check_unreachable_nonterminals(grammar, generator)

        if args.parser == "ir":
            from .parser_gen import generate_parse_functions
            parse_functions = generate_parse_functions(grammar)
            output_lines = []
            for defn in parse_functions:
                output_lines.append(str(defn))
                output_lines.append("")
            output_text = "\n".join(output_lines)
            write_output(output_text, args.output, f"Generated parser IR written to {args.output}")
        elif args.parser == "python":
            from .parser_gen_python import generate_parser_python
            command_line = " ".join(["python -m meta.cli"] + [str(f) for f in args.proto_files] + ["--parser", "python"])
            # Transform messages dict from {name: ProtoMessage} to {(module, name): ProtoMessage}
            proto_messages = {(msg.module, name): msg for name, msg in proto_parser.messages.items()}
            output_text = generate_parser_python(grammar, command_line, proto_messages)
            write_output(output_text, args.output, f"Generated parser written to {args.output}")

    if args.validate:
        generator = GrammarGenerator(proto_parser, verbose=False)
        grammar = generator.generate()

        validator = GrammarValidator(grammar, proto_parser)
        result = validator.validate()

        # Filter out expected unreachable nonterminals
        expected_unreachable = generator.expected_unreachable
        errors = [e for e in result.errors
                  if not (e.category == "unreachable" and
                          e.rule_name in expected_unreachable)]

        if errors:
            print("Validation errors:", file=sys.stderr)
            for error in errors:
                print(f"  [{error.category}] {error.message}", file=sys.stderr)
            return 1
        else:
            print("Validation passed.")

    return 0


def main():
    """Main entry point for protobuf parser."""
    return run(parse_args())


if __name__ == "__main__":
    exit(main())
