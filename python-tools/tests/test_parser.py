import os
import re
import pytest
from pathlib import Path
from lqp.gen.parser import parse
from lqp.proto_validator import ValidationError, validate_proto
from pytest_snapshot.plugin import Snapshot
from .utils import get_lqp_input_files, BIN_SNAPSHOTS_DIR

@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_parse_lqp(snapshot: Snapshot, input_file):
    """Test that each input file can be parsed and matches its binary snapshot."""
    with open(input_file, "r") as f:
        content = f.read()

    txn = parse(content)
    assert txn is not None, f"Failed to parse {input_file}"
    binary_output = txn.SerializeToString()
    snapshot.snapshot_dir = BIN_SNAPSHOTS_DIR
    snapshot_filename = os.path.basename(input_file).replace(".lqp", ".bin")
    snapshot.assert_match(binary_output, snapshot_filename)

@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_validate_lqp_inputs(input_file):
    """Test that each input file passes validation."""
    with open(input_file, "r") as f:
        content = f.read()
    txn = parse(content)
    validate_proto(txn)

VALIDATOR_DIR = Path(__file__).parent / "validator"

def test_valid_validator_files():
    for validator_file in VALIDATOR_DIR.glob("valid_*.lqp"):
        with open(validator_file, "r") as f:
            content = f.read()
        txn = parse(content)
        assert txn is not None, f"Failed to parse {validator_file}"
        validate_proto(txn)

def strip_source_location(error_str: str) -> str:
    """Remove 'at <file>:<line>:<col>' from an error string."""
    return re.sub(r'\s+at\s+\S+:\d+:\d+', '', error_str)

def extract_expected_error(file_path):
    with open(file_path, "r") as f:
        content = f.read()
    error_match = re.search(r';;\s*ERROR:\s*(.+)(?:\n|\r\n?)', content)
    if error_match:
        return error_match.group(1).strip()
    return None

@pytest.mark.parametrize("validator_file", [f for f in os.listdir(VALIDATOR_DIR) if f.startswith("fail_")])
def test_validator_failure_files(validator_file):
    file_path = VALIDATOR_DIR / validator_file
    expected_error = extract_expected_error(file_path)
    if not expected_error:
        pytest.skip(f"No expected error comment found in {validator_file}")
        return
    with open(file_path, "r") as f:
        content = f.read()
    txn = parse(content)
    with pytest.raises(ValidationError) as exc_info:
        validate_proto(txn)
    error_message = str(exc_info.value)
    stripped_expected = strip_source_location(expected_error)
    assert stripped_expected in error_message, f"Expected '{stripped_expected}' in error message: {error_message}"
