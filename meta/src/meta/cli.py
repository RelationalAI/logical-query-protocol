#!/usr/bin/env python3
"""CLI tool for generating parsers from protobuf specifications.

Loads a protobuf spec and a grammar file, validates the grammar file against
the protobuf spec, then generates a parser from the grammar.

Examples:
    # Validate grammar against protobuf specs (--grammar implies validation)
    python -m meta.cli --grammar grammar.y proto/logic.proto proto/transactions.proto

    # Generate a Python parser (validates first)
    python -m meta.cli --grammar grammar.y proto/logic.proto --parser python -o parser.py

    # Output parser intermediate representation
    python -m meta.cli --grammar grammar.y proto/logic.proto --parser ir

    # Output parsed protobuf specification (no grammar needed)
    python -m meta.cli proto/logic.proto --proto

    # Skip validation when generating parser
    python -m meta.cli --grammar grammar.y proto/logic.proto --parser python --no-validate
"""

import argparse
import sys
from pathlib import Path

from .grammar import Grammar
from .grammar_validator import validate_grammar
from .proto_parser import ProtoParser
from .proto_print import format_enum, format_message
from .yacc_parser import load_yacc_grammar_file


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Parse protobuf specifications and validate grammar"
    )
    parser.add_argument(
        "proto_files", nargs="+", type=Path, help="Protobuf files to parse"
    )
    parser.add_argument(
        "--grammar", type=Path, help="Path to grammar file (required for --parser)"
    )
    parser.add_argument(
        "--no-validate", action="store_true", help="Skip grammar validation"
    )
    output_group = parser.add_argument_group("output options")
    output_group.add_argument(
        "-o", "--output", type=Path, help="Output file (default: stdout)"
    )
    output_group.add_argument(
        "--proto", action="store_true", help="Output the parsed protobuf specification"
    )
    output_group.add_argument(
        "--parser",
        type=str,
        choices=["ir", "python", "julia", "go"],
        help="Output the generated parser (ir, python, julia, or go)",
    )
    output_group.add_argument(
        "--printer",
        type=str,
        choices=["ir", "python", "julia"],
        help="Output the generated pretty printer (ir, python, or julia)",
    )

    args = parser.parse_args()

    # --grammar is required for --parser and --printer
    if args.parser and not args.grammar:
        parser.error("--grammar is required when using --parser")
    if args.printer and not args.grammar:
        parser.error("--grammar is required when using --printer")

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
        write_output(
            output_text, args.output, f"Protobuf specification written to {args.output}"
        )
        return 0

    # If no --grammar provided and not --proto, nothing to do
    if not args.grammar:
        print(
            "Nothing to do. Use --grammar to validate or --proto to output protobuf spec.",
            file=sys.stderr,
        )
        return 0

    grammar_path = args.grammar
    if not grammar_path.exists():
        print(f"Error: Grammar file not found: {grammar_path}", file=sys.stderr)
        return 1

    # Transform messages dict from {name: ProtoMessage} to {(module, name): ProtoMessage}
    proto_messages = {
        (msg.module, name): msg for name, msg in proto_parser.messages.items()
    }

    # Load grammar rules from file (yacc format)
    grammar_config = load_yacc_grammar_file(
        grammar_path, proto_messages, proto_parser.enums
    )

    # Build Grammar object from loaded config
    if not grammar_config.rules:
        print("Error: Grammar file contains no rules", file=sys.stderr)
        return 1

    # Find the start nonterminal
    start = None
    for nt in grammar_config.rules.keys():
        if nt.name == grammar_config.start_symbol:
            start = nt
            break
    if start is None:
        print(
            f"Error: Start symbol '{grammar_config.start_symbol}' has no rules",
            file=sys.stderr,
        )
        return 1
    grammar = Grammar(
        start=start,
        ignored_completeness=grammar_config.ignored_completeness,
        function_defs=grammar_config.function_defs,
    )
    for _, rules in grammar_config.rules.items():
        for rule in rules:
            grammar.add_rule(rule)

    # Add tokens with patterns from terminal declarations in grammar file
    from .grammar import Token

    for terminal_name, terminal_def in grammar_config.terminal_patterns.items():
        if terminal_def.pattern is not None:
            grammar.tokens.append(
                Token(terminal_name, terminal_def.pattern, terminal_def.type)
            )

    # Run validation if --grammar is provided (unless --no-validate)
    if args.grammar and not args.no_validate:
        validation_result = validate_grammar(grammar, proto_parser)

        if not validation_result.is_valid:
            print(validation_result.summary())
            print()

            # Block code generation if there are validation errors
            if args.parser or args.printer:
                print(
                    "Error: Cannot generate code due to validation errors (use --no-validate to skip)",
                    file=sys.stderr,
                )

            return 1

    # Output grammar if -o is specified and not generating parser or printer
    if args.output and not args.parser and not args.printer:
        output_text = grammar.print_grammar_yacc()
        args.output.write_text(output_text)
        print(f"Grammar written to {args.output}")
        return 0

    # Run target IR type checker when generating code
    if (args.parser or args.printer) and not args.no_validate:
        from .target_typer import typecheck_ir

        parse_functions = []
        pretty_functions = []
        if args.parser:
            from .parser_gen import generate_parse_functions

            parse_functions = generate_parse_functions(grammar)
        if args.printer:
            from .pretty_gen import generate_pretty_functions

            pretty_functions = generate_pretty_functions(grammar)
        errors = typecheck_ir(
            parse_functions, pretty_functions, list(grammar.function_defs.values())
        )
        if errors:
            for e in errors:
                print(f"typecheck: {e}", file=sys.stderr)
            print(
                f"\nError: {len(errors)} type error(s) in generated IR",
                file=sys.stderr,
            )
            return 1

    if args.parser:
        if args.parser == "ir":
            from .parser_gen import generate_parse_functions as gen_parse

            parse_functions = gen_parse(grammar)
            output_lines = []
            for defn in parse_functions:
                output_lines.append(str(defn))
                output_lines.append("")
            output_text = "\n".join(output_lines)
            write_output(
                output_text,
                args.output,
                f"Generated parser IR written to {args.output}",
            )
        elif args.parser in ("python", "julia", "go"):
            proto_messages = {
                (msg.module, name): msg for name, msg in proto_parser.messages.items()
            }
            command_line = " ".join(
                ["python -m meta.cli"]
                + [str(f) for f in args.proto_files]
                + ["--grammar", str(args.grammar)]
                + ["--parser", args.parser]
            )
            if args.parser == "python":
                from .parser_gen_python import generate_parser_python

                output_text = generate_parser_python(
                    grammar, command_line, proto_messages
                )
            elif args.parser == "julia":
                from .parser_gen_julia import generate_parser_julia

                output_text = generate_parser_julia(
                    grammar, command_line, proto_messages
                )
            else:
                from .parser_gen_go import generate_parser_go

                output_text = generate_parser_go(grammar, command_line, proto_messages)
            write_output(
                output_text, args.output, f"Generated parser written to {args.output}"
            )

    if args.printer:
        if args.printer == "ir":
            from .pretty_gen import generate_pretty_functions as gen_pretty

            pretty_functions = gen_pretty(grammar)
            output_lines = []
            for defn in pretty_functions:
                output_lines.append(str(defn))
                output_lines.append("")
            output_text = "\n".join(output_lines)
            write_output(
                output_text,
                args.output,
                f"Generated printer IR written to {args.output}",
            )
        elif args.printer in ("python", "julia"):
            proto_messages = {
                (msg.module, name): msg for name, msg in proto_parser.messages.items()
            }
            command_line = " ".join(
                ["python -m meta.cli"]
                + [str(f) for f in args.proto_files]
                + ["--grammar", str(args.grammar)]
                + ["--printer", args.printer]
            )
            if args.printer == "python":
                from .pretty_gen_python import generate_pretty_printer_python

                output_text = generate_pretty_printer_python(
                    grammar, command_line, proto_messages
                )
            elif args.printer == "julia":
                from .pretty_gen_julia import generate_pretty_printer_julia

                output_text = generate_pretty_printer_julia(
                    grammar, command_line, proto_messages
                )
            else:
                assert False
            write_output(
                output_text,
                args.output,
                f"Generated pretty printer written to {args.output}",
            )

    return 0


def main() -> int:
    """Main entry point."""
    args = parse_args()
    return run(args)


if __name__ == "__main__":
    exit(main())
