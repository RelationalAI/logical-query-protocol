import os

import pytest
from pytest_snapshot.plugin import Snapshot

from lqp.gen.parser import Parser, parse

from .utils import BIN_SNAPSHOTS_DIR, get_lqp_input_files


def test_relation_id_from_string():
    """All SDKs must produce the same id for the same string."""
    parser = Parser([])
    rid = parser.relation_id_from_string("my_relation")
    assert rid.id_low == 0x5D33996702404F85
    assert rid.id_high == 0x3B9AF8E72AF633F8


@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_parse_lqp(snapshot: Snapshot, input_file):
    """Test that each input file can be parsed and matches its binary snapshot."""
    with open(input_file) as f:
        content = f.read()

    txn = parse(content)
    assert txn is not None, f"Failed to parse {input_file}"
    binary_output = txn.SerializeToString()
    snapshot.snapshot_dir = BIN_SNAPSHOTS_DIR
    snapshot_filename = os.path.basename(input_file).replace(".lqp", ".bin")
    snapshot.assert_match(binary_output, snapshot_filename)
