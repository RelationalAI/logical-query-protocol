import math
import os

import pytest
from pytest_snapshot.plugin import Snapshot

from lqp.gen.parser import (
    Lexer,
    ParseError,
    Parser,
    parse,
    parse_fragment,
    parse_transaction,
)
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


def _csv_fragment(header_row: str) -> str:
    # Wrap a `csv_config` (whose `:csv_header_row` is an int32 field) in a
    # minimal fragment so we can exercise int32 config extraction end-to-end.
    return (
        '(fragment :f (csv_data (csv_locator (paths "x.csv")) '
        f"(csv_config {{ :csv_header_row {header_row} }}) "
        '(columns (column "c" :c [INT])) (asof "2025-01-01T00:00:00Z")))'
    )


def _header_row_of(fragment: str) -> int:
    result, _provenance = parse_fragment(fragment)
    return result.declarations[0].data.csv_data.config.header_row


def test_int32_config_requires_i32_suffix():
    # A properly-typed int32 value parses.
    assert _header_row_of(_csv_fragment("2i32")) == 2

    # A bare int on an int32 config field errors loudly rather than silently
    # falling back to the default.
    with pytest.raises(ParseError):
        parse_fragment(_csv_fragment("2"))

    # Omitting the field entirely still yields the default (1).
    empty_fragment = (
        '(fragment :f (csv_data (csv_locator (paths "x.csv")) (csv_config {}) '
        '(columns (column "c" :c [INT])) (asof "2025-01-01T00:00:00Z")))'
    )
    assert _header_row_of(empty_fragment) == 1


def _relations_fragment(keys_clause: str) -> str:
    # Minimal fragment exercising the generalized `(relations ...)` loading form
    # with a configurable `(keys ...)` clause.
    return (
        '(fragment :f (csv_data (csv_locator (paths "x.csv")) (csv_config {}) '
        f'(relations {keys_clause} (relation :r (column "v" INT))) '
        '(asof "2025-01-01T00:00:00Z")))'
    )


def _relations_of(fragment: str):
    result, _provenance = parse_fragment(fragment)
    return result.declarations[0].data.csv_data.relations


def test_synthetic_key_marker():
    # `(keys synthetic)` sets the synthetic_key flag and leaves keys empty.
    relations = _relations_of(_relations_fragment("(keys synthetic)"))
    assert relations.synthetic_key is True
    assert list(relations.keys) == []

    # Explicit key columns leave synthetic_key unset.
    relations = _relations_of(_relations_fragment('(keys (column "id" INT))'))
    assert relations.synthetic_key is False
    assert [c.name for c in relations.keys] == ["id"]


def test_synthetic_key_with_unary_keyless_relation():
    # A synthetic key with a single relation that has no value columns: the
    # relation holds just the (synthetic) key.
    fragment = (
        '(fragment :f (csv_data (csv_locator (paths "x.csv")) (csv_config {}) '
        "(relations (keys synthetic) (relation :keys)) "
        '(asof "2025-01-01T00:00:00Z")))'
    )
    relations = _relations_of(fragment)
    assert relations.synthetic_key is True
    assert list(relations.keys) == []
    assert len(relations.plain.targets) == 1
    assert list(relations.plain.targets[0].values) == []


def test_synthetic_key_rejects_unknown_marker():
    # Only the `synthetic` marker is accepted; anything else is a hard error.
    with pytest.raises(ParseError):
        parse_fragment(_relations_fragment("(keys bogus)"))


class TestSymbolLexing:
    """Tests for SYMBOL token regex — hyphen must be literal, not a range."""

    def test_hyphenated_symbol(self):
        tokens = Lexer("my-relation").tokens
        assert tokens[0].type == "SYMBOL"
        assert tokens[0].value == "my-relation"

    def test_symbol_with_hash_and_slash(self):
        tokens = Lexer("base/#output").tokens
        assert tokens[0].type == "SYMBOL"
        assert tokens[0].value == "base/#output"

    def test_dollar_is_not_part_of_symbol(self):
        # '$' is not a valid SYMBOL character — the lexer should fail on it
        with pytest.raises(ParseError):
            Lexer("foo$bar")


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
        value = tokens[0].value
        assert isinstance(value, float)
        assert math.isinf(value)

    def test_tokenize_nan32(self):
        tokens = Lexer("nan32").tokens
        assert tokens[0].type == "FLOAT32"
        value = tokens[0].value
        assert isinstance(value, float)
        assert math.isnan(value)

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
