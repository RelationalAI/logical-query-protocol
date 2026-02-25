import os

import pytest
from pytest_snapshot.plugin import Snapshot

from lqp.gen.parser import parse

from .utils import BIN_SNAPSHOTS_DIR, get_lqp_input_files


@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_parse_lqp(snapshot: Snapshot, input_file):
    """Test that each input file can be parsed and matches its binary snapshot."""
    with open(input_file) as f:
        content = f.read()

    txn, _provenance = parse(content)
    assert txn is not None, f"Failed to parse {input_file}"
    binary_output = txn.SerializeToString()
    snapshot.snapshot_dir = BIN_SNAPSHOTS_DIR
    snapshot_filename = os.path.basename(input_file).replace(".lqp", ".bin")
    snapshot.assert_match(binary_output, snapshot_filename)
