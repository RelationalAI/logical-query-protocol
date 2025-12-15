"""
CLI entry point for LQP validator and translation.

This module provides file processing and command-line interface functionality.
"""

import argparse
import os
import shutil
import sys
from importlib.metadata import version
from google.protobuf.json_format import MessageToJson

from lqp.parser import parse_lqp
from lqp.emit import ir_to_proto
from lqp.validator import validate_lqp
import lqp.ir as ir


def process_file(filename, bin, json, validate=True):
    """Process a single LQP file and output binary and/or JSON."""
    with open(filename, "r") as f:
        lqp_text = f.read()

    lqp = parse_lqp(filename, lqp_text)
    if validate and isinstance(lqp, ir.Transaction):
        validate_lqp(lqp)
    lqp_proto = ir_to_proto(lqp)

    # Write binary output to the configured directories, using the same filename.
    if bin:
        lqp_bin = lqp_proto.SerializeToString()
        if bin == "-":
            sys.stdout.buffer.write(lqp_bin)
        else:
            with open(bin, "wb") as f:
                f.write(lqp_bin)
            print(f"Successfully wrote {filename} to bin at {bin}")

    # Write JSON output
    if json:
        lqp_json = MessageToJson(lqp_proto, preserving_proto_field_name=True)
        if json == "-":
            sys.stdout.write(lqp_json)
        else:
            with open(json, "w") as f:
                f.write(lqp_json)
            print(f"Successfully wrote {filename} to JSON at {json}")


def process_directory(lqp_directory, bin, json, validate=True):
    """Process all LQP files in a directory."""
    # Create bin directory at parent level if needed
    bin_dir = None
    if bin:
        parent_dir = os.path.dirname(lqp_directory)
        bin_dir = os.path.join(parent_dir, "bin")
        os.makedirs(bin_dir, exist_ok=True)

    # Create json directory at parent level if needed
    json_dir = None
    if json:
        parent_dir = os.path.dirname(lqp_directory)
        json_dir = os.path.join(parent_dir, "json")
        os.makedirs(json_dir, exist_ok=True)

    # Process each LQP file in the directory
    for file in os.listdir(lqp_directory):
        if not file.endswith(".lqp"):
            continue

        filename = os.path.join(lqp_directory, file)
        basename = os.path.splitext(file)[0]

        bin_output = os.path.join(bin_dir, basename + ".bin") if bin_dir else None
        json_output = os.path.join(json_dir, basename + ".json") if json_dir else None

        process_file(filename, bin_output, json_output, validate)


def look_for_lqp_directory(directory):
    """Find or create an 'lqp' directory within the given directory."""
    for root, dirs, _ in os.walk(directory):
        if "lqp" in dirs:
            return os.path.join(root, "lqp")

    # If we didn't find a 'lqp' directory, create one
    lqp_dir = os.path.join(directory, "lqp")
    os.makedirs(lqp_dir, exist_ok=True)
    print(f"LQP home directory not found, created one at {directory}")
    return lqp_dir


def get_lqp_files(directory):
    """Get all .lqp files in a directory."""
    lqp_files = []
    for file in os.listdir(directory):
        if file.endswith(".lqp"):
            lqp_files.append(os.path.join(directory, file))
    return lqp_files


def get_package_version():
    """Get the version of the installed `lqp` package."""
    return version("lqp")


def main():
    """Main entry point for the lqp CLI."""
    arg_parser = argparse.ArgumentParser(description="Parse LQP S-expression into Protobuf binary and JSON files.")
    arg_parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {get_package_version()}", help="show program's version number and exit")
    arg_parser.add_argument("input", help="directory holding .lqp files, or a single .lqp file")
    arg_parser.add_argument("--no-validation", action="store_true", help="don't validate parsed LQP")
    arg_parser.add_argument("--bin", action="store_true", help="encode emitted ProtoBuf into binary")
    arg_parser.add_argument("--json", action="store_true", help="encode emitted ProtoBuf into JSON")
    arg_parser.add_argument("--out", action="store_true", help="write emitted binary or JSON to stdout")

    args = arg_parser.parse_args()

    validate = not args.no_validation
    bin = args.bin
    json = args.json

    if os.path.isfile(args.input):
        filename = args.input
        assert filename.endswith(".lqp") and os.path.isfile(filename), \
            f"The input {filename} does not seem to be an LQP file"

        if args.out:
            assert not (args.bin and args.json), "Cannot specify both --bin and --json with --out option"

        basename = os.path.splitext(filename)[0]

        bin_name = None
        json_name = None

        if args.bin:
            bin_name = "-" if args.out else basename + ".bin"

        if args.json:
            json_name = "-" if args.out else basename + ".json"

        process_file(filename, bin_name, json_name, validate)
    elif os.path.isdir(args.input):
        lqp_directory = look_for_lqp_directory(args.input)
        lqp_files = get_lqp_files(args.input)
        for file in lqp_files:
            shutil.move(file, lqp_directory)

        process_directory(lqp_directory, bin, json, validate)
    else:
        print("Input is not a valid file nor directory")


if __name__ == "__main__":
    main()
