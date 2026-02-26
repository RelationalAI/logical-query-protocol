import os

import pytest
from pytest_snapshot.plugin import Snapshot

from lqp.gen.parser import ParseError, parse, parse_fragment, parse_transaction
from lqp.proto.v1 import fragments_pb2, transactions_pb2

from .utils import BIN_SNAPSHOTS_DIR, get_lqp_input_files


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


_SIMPLE_TXN = "(transaction (epoch (writes) (reads)))"
_SIMPLE_FRAGMENT = "(fragment :test_frag (def :my_rel ([x::INT] (relatom :my_rel x))))"


def test_parse_transaction():
    result = parse_transaction(_SIMPLE_TXN)
    assert isinstance(result, transactions_pb2.Transaction)
    assert len(result.epochs) == 1


def test_parse_fragment():
    result = parse_fragment(_SIMPLE_FRAGMENT)
    assert isinstance(result, fragments_pb2.Fragment)


def test_parse_delegates_to_parse_transaction():
    assert parse(_SIMPLE_TXN) == parse_transaction(_SIMPLE_TXN)


def test_parse_fragment_rejects_transaction():
    with pytest.raises(ParseError):
        parse_fragment(_SIMPLE_TXN)


def test_parse_transaction_rejects_fragment():
    with pytest.raises(ParseError):
        parse_transaction(_SIMPLE_FRAGMENT)
