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
from lqp.proto.v1 import transactions_pb2
from lqp.proto_validator import validate_proto


def parse_input(filename: str, validate: bool = True):
    """Parse an input file (.lqp or .bin) and return a protobuf Transaction."""
    if filename.endswith(".bin"):
        with open(filename, "rb") as f:
            data = f.read()
        txn = transactions_pb2.Transaction()
        txn.ParseFromString(data)
    else:
        with open(filename) as f:
            lqp_text = f.read()
        txn = parse(lqp_text)

    if validate:
        validate_proto(txn)

    return txn


def output_path(filename: str, ext: str) -> str:
    """Return the output path for a file with the given extension."""
    base, _ = os.path.splitext(filename)
    return base + ext


FORMAT_TABLE: dict[str, tuple[str, bool]] = {
    "bin": (".bin", True),
    "json": (".json", False),
    "lqp": (".lqp", False),
}


def serialize(txn, fmt: str) -> str | bytes:
    """Serialize a transaction to the given format."""
    if fmt == "bin":
        return txn.SerializeToString()
    elif fmt == "json":
        return MessageToJson(txn, preserving_proto_field_name=True)
    elif fmt == "lqp":
        return pretty(txn)
    else:
        raise ValueError(f"Unknown format: {fmt}")


def process_file(filename: str, fmt: str, out: bool, validate: bool = True):
    """Process a single input file and produce requested output."""
    txn = parse_input(filename, validate)
    ext, is_binary = FORMAT_TABLE[fmt]
    data = serialize(txn, fmt)

    if out:
        if is_binary:
            assert isinstance(data, bytes)
            sys.stdout.buffer.write(data)
        else:
            assert isinstance(data, str)
            sys.stdout.write(data)
    else:
        dest = output_path(filename, ext)
        if is_binary:
            assert isinstance(data, bytes)
            with open(dest, "wb") as f:
                f.write(data)
        else:
            assert isinstance(data, str)
            with open(dest, "w") as f:
                f.write(data)
        print(f"Successfully wrote {filename} to {dest}")


def collect_input_files(path: str):
    """Collect .lqp and .bin files from a path (file or directory, recursive)."""
    if os.path.isfile(path):
        return [path]
    elif os.path.isdir(path):
        files = []
        for root, _, filenames in os.walk(path):
            for f in filenames:
                if f.endswith(".lqp") or f.endswith(".bin"):
                    files.append(os.path.join(root, f))
        return sorted(files)
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
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {get_package_version()}",
    )
    arg_parser.add_argument(
        "input",
        help=".lqp or .bin file, or a directory",
    )
    arg_parser.add_argument(
        "--no-validation",
        action="store_true",
        help="skip validation",
    )
    arg_parser.add_argument(
        "--out",
        action="store_true",
        help="write output to stdout",
    )

    fmt_group = arg_parser.add_mutually_exclusive_group()
    fmt_group.add_argument(
        "--bin",
        action="store_true",
        help="write protobuf binary output",
    )
    fmt_group.add_argument(
        "--json",
        action="store_true",
        help="write protobuf JSON output",
    )
    fmt_group.add_argument(
        "--lqp",
        action="store_true",
        help="pretty-print LQP output",
    )

    args = arg_parser.parse_args()
    validate = not args.no_validation

    fmt = None
    if args.bin:
        fmt = "bin"
    elif args.json:
        fmt = "json"
    elif args.lqp:
        fmt = "lqp"

    if os.path.isfile(args.input):
        filename = args.input
        if not (filename.endswith(".lqp") or filename.endswith(".bin")):
            arg_parser.error(f"Unsupported file type: {filename}")
        if fmt:
            process_file(filename, fmt, args.out, validate)
        else:
            parse_input(filename, validate)
            print(f"OK: {filename}")
    elif os.path.isdir(args.input):
        for filename in collect_input_files(args.input):
            if fmt:
                process_file(filename, fmt, args.out, validate)
            else:
                parse_input(filename, validate)
                print(f"OK: {filename}")
    else:
        arg_parser.error(f"Input is not a valid file or directory: {args.input}")


if __name__ == "__main__":
    main()
