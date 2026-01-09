#!/usr/bin/env python3
"""CLI tool for generating grammar and code from protobuf specifications.

This module provides the main command-line entry point for the proto-to-tools
code generator.
"""

import argparse
import sys
from pathlib import Path

# Handle both script and module execution
if __name__ == "__main__" and __package__ is None:
    # Running as script - add parent to path and use absolute imports
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from meta.proto_parser import ProtoParser
    from meta.grammar_gen import GrammarGenerator
    from meta.parser_gen_python import generate_parser_python
else:
    # Running as module - use relative imports
    from .proto_parser import ProtoParser
    from .grammar_gen import GrammarGenerator
    from .parser_gen_python import generate_parser_python


def main():
    """Main entry point for proto-to-tools."""
    import sys
    command_line = " ".join(sys.argv)

    parser = argparse.ArgumentParser(
        description="Generate tools from protobuf specifications"
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
        help="Output file for generated code"
    )
    parser.add_argument(
        "--grammar",
        action="store_true",
        help="Output grammar"
    )
    parser.add_argument(
        "--parser",
        choices=["python", "ir"],
        help="Generate parser in specified language (or 'ir' to dump IR)"
    )
    args = parser.parse_args()

    if not any([args.grammar, args.parser]):
        print("Error: At least one of --grammar or --parser must be specified")
        return 1

    proto_parser = ProtoParser()
    for proto_file in args.proto_files:
        if not proto_file.exists():
            print(f"Error: File not found: {proto_file}")
            return 1
        proto_parser.parse_file(proto_file)

    generator = GrammarGenerator(proto_parser, verbose=True)
    grammar = generator.generate()

    reachable, unreachable = grammar.analysis.partition_nonterminals_by_reachability()
    reachable_set = set(reachable)
    unexpected_unreachable = [r for r in unreachable if r.name not in generator.expected_unreachable]
    if unexpected_unreachable:
        print("Warning: Unreachable rules detected:")
        for rule in unexpected_unreachable:
            print(f"  {rule.name}")
        print()

    outputs = []

    if args.grammar:
        grammar_text = grammar.print_grammar()
        outputs.append(("grammar", grammar_text))

    if args.parser:
        if args.parser == "python":
            # Build message map for code generation
            proto_messages = {}
            for msg_name, msg in proto_parser.messages.items():
                proto_messages[(msg.module, msg.name)] = msg
            parser_text = generate_parser_python(grammar, reachable_set, command_line, proto_messages)
            outputs.append((f"parser-{args.parser}", parser_text))
        elif args.parser == "ir":
            if __package__ is None:
                from meta.parser_gen import generate_parse_functions
            else:
                from .parser_gen import generate_parse_functions
            defns = generate_parse_functions(grammar)
            ir_text = "\n\n".join(str(defn) for defn in defns)
            outputs.append(("parser-ir", ir_text))

    if args.output:
        if len(outputs) == 1:
            args.output.write_text(outputs[0][1])
            print(f"Generated {outputs[0][0]} written to {args.output}")
        else:
            for output_type, output_text in outputs:
                output_path = args.output.parent / f"{args.output.stem}_{output_type}{args.output.suffix}"
                output_path.write_text(output_text)
                print(f"Generated {output_type} written to {output_path}")
    else:
        for output_type, output_text in outputs:
            print(f"# {output_type.upper()}")
            print(output_text)
            print()

    return 0


if __name__ == "__main__":
    exit(main())
