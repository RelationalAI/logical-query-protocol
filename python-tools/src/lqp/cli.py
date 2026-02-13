"""
CLI entry point for LQP validator and translation.
"""

import argparse
import os
import sys
from importlib.metadata import version
from google.protobuf.json_format import MessageToJson

from lqp.gen.parser import parse
from lqp.gen.pretty import pretty
from lqp.proto_validator import validate_proto
from lqp.proto.v1 import transactions_pb2


def parse_input(filename: str, validate: bool = True):
    """Parse an input file (.lqp or .bin) and return a protobuf Transaction."""
    if filename.endswith(".bin"):
        with open(filename, "rb") as f:
            data = f.read()
        txn = transactions_pb2.Transaction()
        txn.ParseFromString(data)
    else:
        with open(filename, "r") as f:
            lqp_text = f.read()
        txn = parse(lqp_text)

    if validate:
        validate_proto(txn)

    return txn


def process_file(filename: str, bin_out, json_out, pretty_print: bool, validate: bool = True):
    """Process a single input file and produce requested outputs."""
    txn = parse_input(filename, validate)

    if bin_out:
        data = txn.SerializeToString()
        if bin_out == "-":
            sys.stdout.buffer.write(data)
        else:
            with open(bin_out, "wb") as f:
                f.write(data)
            print(f"Successfully wrote {filename} to bin at {bin_out}")

    if json_out:
        json_str = MessageToJson(txn, preserving_proto_field_name=True)
        if json_out == "-":
            sys.stdout.write(json_str)
        else:
            with open(json_out, "w") as f:
                f.write(json_str)
            print(f"Successfully wrote {filename} to JSON at {json_out}")

    if pretty_print:
        sys.stdout.write(pretty(txn))


def collect_input_files(path: str):
    """Collect input files from a path (file or directory)."""
    if os.path.isfile(path):
        return [path]
    elif os.path.isdir(path):
        files = []
        for f in sorted(os.listdir(path)):
            if f.endswith(".lqp") or f.endswith(".bin"):
                files.append(os.path.join(path, f))
        return files
    else:
        return []


def get_package_version():
    """Get the version of the installed `lqp` package."""
    return version("lqp")


def main():
    """Main entry point for the lqp CLI."""
    arg_parser = argparse.ArgumentParser(
        description="Parse, validate, and translate LQP files."
    )
    arg_parser.add_argument(
        "-v", "--version", action="version",
        version=f"%(prog)s {get_package_version()}",
    )
    arg_parser.add_argument(
        "input", nargs="+",
        help="one or more .lqp or .bin files, or directories",
    )
    arg_parser.add_argument(
        "--no-validation", action="store_true",
        help="skip validation",
    )
    arg_parser.add_argument(
        "--bin", metavar="FILE",
        help="write protobuf binary output (- for stdout)",
    )
    arg_parser.add_argument(
        "--json", metavar="FILE",
        help="write protobuf JSON output (- for stdout)",
    )
    arg_parser.add_argument(
        "--pretty", action="store_true",
        help="pretty-print to stdout",
    )

    args = arg_parser.parse_args()
    validate = not args.no_validation

    input_files = []
    for path in args.input:
        found = collect_input_files(path)
        if not found:
            arg_parser.error(f"No .lqp or .bin files found at {path}")
        input_files.extend(found)

    for filename in input_files:
        if not (filename.endswith(".lqp") or filename.endswith(".bin")):
            arg_parser.error(f"Unsupported file type: {filename}")

        process_file(filename, args.bin, args.json, args.pretty, validate)


if __name__ == "__main__":
    main()
