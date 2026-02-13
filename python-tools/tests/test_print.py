import pytest
import os

from lqp.gen.parser import parse
from lqp.gen.pretty import pretty
from .utils import get_lqp_input_files

PRETTY_SNAPSHOTS_DIR = "tests/lqp_pretty_output"

@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_pretty_print_roundtrip(input_file):
    """Test that pretty-printing then re-parsing produces the same binary."""
    with open(input_file, "r") as f:
        original_text = f.read()

    txn = parse(original_text)
    original_binary = txn.SerializeToString()

    printed = pretty(txn)
    re_parsed = parse(printed)
    re_parsed_binary = re_parsed.SerializeToString()

    assert original_binary == re_parsed_binary, (
        f"Round-trip mismatch for {input_file}"
    )

@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_pretty_print_snapshot(snapshot, input_file):
    """Test that pretty-printed output matches snapshots."""
    with open(input_file, "r") as f:
        content = f.read()

    txn = parse(content)
    printed = pretty(txn)

    snapshot.snapshot_dir = PRETTY_SNAPSHOTS_DIR
    snapshot.assert_match(printed, os.path.basename(input_file))
