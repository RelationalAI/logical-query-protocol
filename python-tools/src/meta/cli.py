#!/usr/bin/env python3
"""CLI tool for generating parsers from protobuf specifications.

Loads a protobuf spec and a grammar file, validates the grammar file against
the protobuf spec, then generates a parser from the grammar.

Examples:
    # Validate grammar against protobuf specs
    python -m meta.cli --grammar grammar.y proto/logic.proto proto/transactions.proto --validate

    # Generate a Python parser
    python -m meta.cli --grammar grammar.y proto/logic.proto --parser python -o parser.py

    # Output parser intermediate representation
    python -m meta.cli --grammar grammar.y proto/logic.proto --parser ir

    # Output parsed protobuf specification
    python -m meta.cli --grammar grammar.y proto/logic.proto --proto
"""

import argparse
import sys
from pathlib import Path

from .proto_parser import ProtoParser
from .grammar_validator import validate_grammar
from .grammar import Grammar
from .yacc_grammar import load_yacc_grammar_file
from .proto_print import format_message, format_enum


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
        "--grammar",
        type=Path,
        help="Path to grammar file (required for --validate or --parser)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate grammar covers protobuf spec"
    )

    output_group = parser.add_argument_group("output options")
    output_group.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file (default: stdout)"
    )
    output_group.add_argument(
        "--proto",
        action="store_true",
        help="Output the parsed protobuf specification"
    )
    output_group.add_argument(
        "--parser",
        type=str,
        choices=["ir", "python"],
        help="Output the generated parser (ir or python)"
    )
    output_group.add_argument(
        "--force",
        action="store_true",
        help="Generate parser even if validation fails"
    )

    args = parser.parse_args()

    # --grammar is required if --validate or --parser is given
    if (args.validate or args.parser) and not args.grammar:
        parser.error("--grammar is required when using --validate or --parser")

    return args


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
    # Parse protobuf files first (needed for --proto, validation, and parser gen)
    proto_parser = ProtoParser()
    for proto_file in args.proto_files:
        if not proto_file.exists():
            print(f"Error: File not found: {proto_file}", file=sys.stderr)
            return 1
        proto_parser.parse_file(proto_file)

    # Handle --proto: output parsed protobuf specification
    if args.proto:
        output_lines = []
        for msg in proto_parser.messages.values():
            output_lines.append(format_message(msg))
            output_lines.append("")
        for enum in proto_parser.enums.values():
            output_lines.append(format_enum(enum))
            output_lines.append("")
        output_text = "\n".join(output_lines)
        write_output(output_text, args.output, f"Protobuf specification written to {args.output}")
        return 0

    # From here on, --grammar is required (enforced by parse_args)
    grammar_path = args.grammar
    if not grammar_path or not grammar_path.exists():
        print(f"Error: Grammar file not found: {grammar_path}", file=sys.stderr)
        return 1

    # Load grammar rules from file (yacc format)
    grammar_config = load_yacc_grammar_file(grammar_path)

    # Build Grammar object from loaded config
    # Use the first nonterminal in the grammar as the start symbol
    if not grammar_config.rules:
        print("Error: Grammar file contains no rules", file=sys.stderr)
        return 1

    start = next(iter(grammar_config.rules.keys()))
    grammar = Grammar(
        start=start,
        ignored_completeness=grammar_config.ignored_completeness,
        function_defs=grammar_config.function_defs
    )
    for _, rules in grammar_config.rules.items():
        for rule in rules:
            grammar.add_rule(rule)

    # Add tokens with patterns from terminal declarations
    # Map terminal names to their regex patterns (from Lark grammar)
    from .grammar import Token
    default_patterns = {
        'SYMBOL': r'[a-zA-Z_][a-zA-Z0-9_.-]*',
        'COLON_SYMBOL': r':[a-zA-Z_][a-zA-Z0-9_.-]*',
        'STRING': r'"(?:[^"\\]|\\.)*"',  # ESCAPED_STRING pattern
        'INT': r'[-]?\d+',
        'INT128': r'[-]?\d+i128',
        'UINT128': r'0x[0-9a-fA-F]+',
        'FLOAT': r'[-]?\d+\.\d+|inf|nan',
        'DECIMAL': r'[-]?\d+\.\d+d\d+',
    }
    for terminal_name, terminal_type in grammar_config.terminals.items():
        pattern = default_patterns.get(terminal_name)
        if pattern:
            grammar.tokens.append(Token(terminal_name, pattern, terminal_type))

    # Run validation (always run, but only print if requested or has issues)
    validation_result = validate_grammar(grammar, proto_parser)

    if args.validate or validation_result.has_any_issues:
        print(validation_result.summary())
        print()

    # Block parser generation if there are validation errors (unless --force)
    if args.parser and not validation_result.is_valid and not args.force:
        print("Error: Cannot generate parser due to validation errors (use --force to override)", file=sys.stderr)
        return 1

    # Return error code if validation has errors (not just warnings), unless --force
    if not validation_result.is_valid and not args.force:
        return 1

    # Output grammar if -o is specified and not generating parser
    if args.output and not args.parser:
        output_text = grammar.print_grammar_yacc()
        args.output.write_text(output_text)
        print(f"Grammar written to {args.output}")

    if args.parser:
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
