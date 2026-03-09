import math
import os

import pytest
from pytest_snapshot.plugin import Snapshot

from lqp.gen.parser import Lexer, ParseError, Parser, parse, parse_fragment, parse_transaction
from lqp.proto.v1 import fragments_pb2, transactions_pb2

from .utils import BIN_SNAPSHOTS_DIR, get_lqp_input_files


def test_relation_id_from_string():
    """All SDKs must produce the same id for the same string."""
    parser = Parser([], "")
    rid = parser.relation_id_from_string("my_relation")
    assert rid.id_low == 0xF2FC83EC57CF8FBC
    assert rid.id_high == 0x503F7DC862F367B7


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


_SIMPLE_TXN = "(transaction (epoch (writes) (reads)))"
_SIMPLE_FRAGMENT = "(fragment :test_frag (def :my_rel ([x::INT] (relatom :my_rel x))))"


def test_parse_transaction():
    result, _provenance = parse_transaction(_SIMPLE_TXN)
    assert isinstance(result, transactions_pb2.Transaction)
    assert len(result.epochs) == 1


def test_parse_fragment():
    result, _provenance = parse_fragment(_SIMPLE_FRAGMENT)
    assert isinstance(result, fragments_pb2.Fragment)


def test_parse_delegates_to_parse_transaction():
    assert parse(_SIMPLE_TXN) == parse_transaction(_SIMPLE_TXN)


def test_parse_fragment_rejects_transaction():
    with pytest.raises(ParseError):
        parse_fragment(_SIMPLE_TXN)


def test_parse_transaction_rejects_fragment():
    with pytest.raises(ParseError):
        parse_transaction(_SIMPLE_FRAGMENT)


class TestScanFloat32:
    """Tests for parsing float32 literals including inf32 and nan32."""

    def test_numeric(self):
        assert Lexer.scan_float32("3.14f32") == pytest.approx(3.14, abs=1e-5)

    def test_negative(self):
        assert Lexer.scan_float32("-1.5f32") == pytest.approx(-1.5)

    def test_zero(self):
        assert Lexer.scan_float32("0.0f32") == 0.0

    def test_inf32(self):
        assert math.isinf(Lexer.scan_float32("inf32"))
        assert Lexer.scan_float32("inf32") > 0

    def test_nan32(self):
        assert math.isnan(Lexer.scan_float32("nan32"))

    def test_tokenize_inf32(self):
        tokens = Lexer("inf32").tokens
        assert tokens[0].type == "FLOAT32"
        assert math.isinf(tokens[0].value)

    def test_tokenize_nan32(self):
        tokens = Lexer("nan32").tokens
        assert tokens[0].type == "FLOAT32"
        assert math.isnan(tokens[0].value)

    def test_round_trip_inf32(self):
        lqp = """(transaction (epoch (writes (define (fragment :f1
            (def :foo ([v::FLOAT32] (= v inf32)))))) (reads (output :foo :foo))))"""
        txn, _ = parse(lqp)
        assert txn is not None

    def test_round_trip_nan32(self):
        lqp = """(transaction (epoch (writes (define (fragment :f1
            (def :foo ([v::FLOAT32] (= v nan32)))))) (reads (output :foo :foo))))"""
        txn, _ = parse(lqp)
        assert txn is not None
