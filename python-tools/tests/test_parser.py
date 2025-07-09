import os
import re
import pytest
import sys
import lqp.ir as ir
from pathlib import Path
from lqp.parser import parse_lqp
from lqp.emit import ir_to_proto
from lqp.validator import ValidationError, validate_lqp
from pytest_snapshot.plugin import Snapshot

TEST_INPUTS_DIR = Path(__file__).parent / "test_files" / "lqp_input"

def get_all_input_files():
    """Find all .lqp files in the test inputs directory and subdirectories"""
    input_files = []

    for root, dirs, files in os.walk(TEST_INPUTS_DIR):
        for file in files:
            if file.endswith(".lqp"):
                input_files.append(os.path.join(root, file))

    return input_files

@pytest.mark.parametrize("input_file", get_all_input_files())
def test_parse_lqp(snapshot: Snapshot, input_file):
    """Test that each input file can be successfully parsed and matches its binary snapshot"""
    try:
        with open(input_file, "r") as f:
            content = f.read()

        # Parse the file and convert to protobuf
        parsed_lqp = parse_lqp(input_file, content)
        assert parsed_lqp is not None, f"Failed to parse {input_file}"
        proto_result = ir_to_proto(parsed_lqp)
        assert proto_result is not None, f"Failed to convert IR to Proto for {input_file}"
        binary_output = proto_result.SerializeToString()
        snapshot.snapshot_dir = Path(__file__).parent / "test_files" / "bin_output"
        snapshot_filename = os.path.basename(input_file).replace(".lqp", ".bin")
        snapshot.assert_match(binary_output, snapshot_filename)
        print(f"Successfully parsed and snapshotted {input_file}")

    except Exception as e:
        pytest.fail(f"Failed checking {input_file}: {str(e)}")

VALIDATOR_DIR = Path(__file__).parent / "validator"

def test_valid_validator_files():
    for validator_file in VALIDATOR_DIR.glob("valid_*.lqp"):
        with open(validator_file, "r") as f:
            content = f.read()
        try:
            result = parse_lqp(validator_file, content)
            assert result is not None, f"Failed to parse {validator_file}"
            print(f"Successfully validated {validator_file}")
        except Exception as e:
            pytest.fail(f"Failed to parse valid validator file {validator_file}: {str(e)}")

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
    result = parse_lqp(validator_file, content)
    assert isinstance(result, ir.Transaction), f"{validator_file} does not contain a transaction"
    with pytest.raises(ValidationError) as exc_info:
        validate_lqp(result)
    error_message = str(exc_info.value)
    assert expected_error in error_message, f"Expected '{expected_error}' in error message: {error_message}"
