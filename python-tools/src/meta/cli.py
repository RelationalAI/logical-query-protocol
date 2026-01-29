#!/usr/bin/env python3
"""CLI tool for generating parsers from protobuf specifications.

Loads a protobuf spec and a grammar file, validates the grammar file against
the protobuf spec, then generates a parser from the grammar.

Examples:
    # Validate grammar against protobuf specs
    python -m meta.cli --grammar grammar.sexp proto/logic.proto proto/transactions.proto --validate

    # Generate a Python parser
    python -m meta.cli --grammar grammar.sexp proto/logic.proto --parser python -o parser.py

    # Output parser intermediate representation
    python -m meta.cli --grammar grammar.sexp proto/logic.proto --parser ir

    # Output parsed protobuf specification
    python -m meta.cli --grammar grammar.sexp proto/logic.proto --proto
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
        "--proto",
        action="store_true",
        help="Output the parsed protobuf specification"
    )
    parser.add_argument(
        "--grammar",
        type=Path,
        required=True,
        help="Path to grammar file"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate grammar covers protobuf spec"
    )
    parser.add_argument(
        "--parser",
        type=str,
        choices=["ir", "python"],
        help="Output the generated parser (ir or python)"
    )
    return parser.parse_args()


def check_unreachable_nonterminals(grammar, expected_unreachable):
    """Check for unexpected unreachable nonterminals and report warnings.

    Args:
        grammar: The grammar to analyze
        expected_unreachable: Set of nonterminal names expected to be unreachable

    Prints warnings to stdout if unexpected unreachable nonterminals are found.
    """
    _, unreachable = grammar.analysis.partition_nonterminals_by_reachability()
    unexpected_unreachable = [r for r in unreachable if r.name not in expected_unreachable]
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
    grammar_path = args.grammar
    if not grammar_path.exists():
        print(f"Error: Grammar file not found: {grammar_path}", file=sys.stderr)
        return 1

    # Load grammar rules from file
    grammar_config = load_grammar_config_file(grammar_path)

    # Build Grammar object from loaded config
    start = Nonterminal('transaction', MessageType('transactions', 'Transaction'))
    grammar = Grammar(start=start)
    for _, rules in grammar_config.rules.items():
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

    if args.parser:
        check_unreachable_nonterminals(grammar, expected_unreachable)

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

    return 0


def main():
    """Main entry point for protobuf parser."""
    return run(parse_args())


if __name__ == "__main__":
    exit(main())
