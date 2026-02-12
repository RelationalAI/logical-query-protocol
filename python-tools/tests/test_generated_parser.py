"""Tests comparing the Lark parser and generated parser outputs.

These tests verify that the generated LL(k) parser produces identical
protobuf output to the reference Lark-based parser.
"""

import pytest
from pathlib import Path

from lqp.parser import parse_lqp
from lqp.emit import ir_to_proto
from lqp.gen.parser import parse as generated_parse

from .utils import get_lqp_input_files, get_all_files, PARENT_DIR


# Files that use unsupported features in the generated parser.
# When these start passing, remove them from this set.
KNOWN_UNSUPPORTED = {
    # (empty - all previously unsupported features are now supported)
}


def get_validator_files():
    """Find all .lqp files in the validator directory."""
    validator_dir = PARENT_DIR / "validator"
    return get_all_files(validator_dir, ".lqp")


def get_all_test_lqp_files():
    """Get all .lqp test files from both tests/lqp and validator directories."""
    files = get_lqp_input_files() + get_validator_files()
    return sorted(set(files))


@pytest.mark.parametrize("input_file", get_all_test_lqp_files())
def test_generated_parser_matches_lark_parser(input_file):
    """Test that generated parser produces same protobuf as Lark parser."""
    filename = Path(input_file).name
    if filename in KNOWN_UNSUPPORTED:
        pytest.xfail(f"{filename} uses unsupported features (functional_dependency)")

    with open(input_file, "r") as f:
        content = f.read()

    # Parse with Lark parser and convert to protobuf
    lark_ir = parse_lqp(input_file, content)
    lark_proto = ir_to_proto(lark_ir)
    lark_binary = lark_proto.SerializeToString()

    # Parse with generated parser (returns protobuf directly)
    generated_proto = generated_parse(content)
    generated_binary = generated_proto.SerializeToString()

    # Compare serialized protobufs
    assert lark_binary == generated_binary, (
        f"Parser outputs differ for {filename}:\n"
        f"Lark proto: {lark_proto}\n"
        f"Generated proto: {generated_proto}"
    )
