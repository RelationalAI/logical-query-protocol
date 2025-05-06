import os
import re
import pytest
import sys
from pathlib import Path
from lqp.parser import parse_lqp
from lqp.emit import ir_to_proto
from lqp.validator import ValidationError, validate_lqp

TEST_INPUTS_DIR = Path(__file__).parent / "test_files" / "lqp_input"
TEST_OUTPUTS_DIR = Path(__file__).parent / "test_files" / "bin_output"

def get_all_input_files():
    """Find all .lqp files in the test inputs directory and subdirectories"""
    input_files = []

    for root, dirs, files in os.walk(TEST_INPUTS_DIR):
        for file in files:
            if file.endswith(".lqp"):
                input_files.append(os.path.join(root, file))

    return input_files

def get_output_file(input_file):
    """Get the corresponding output file for a given input file"""
    base_name = os.path.basename(input_file)
    output_file = os.path.join(TEST_OUTPUTS_DIR, base_name.replace(".lqp", ".bin"))
    return output_file

@pytest.mark.parametrize("input_file", get_all_input_files())
def test_parse_lqp(input_file):
    """Test that each input file can be successfully parsed"""
    try:
        with open(input_file, "r") as f:
            content = f.read()

        # Parse the file and check it returns a valid protobuf object
        result = ir_to_proto(parse_lqp(input_file, content))
        assert result is not None, f"Failed to parse {input_file}"

        # Log the successful parse for verbose output
        print(f"Successfully parsed {input_file}")

        # Check that the generated proto binary matches the expected output
        output_file = get_output_file(input_file)
        with open(output_file, "rb") as f:
            expected_output = f.read()
            assert result.SerializeToString() == expected_output, f"Output does not match for {input_file}"

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
    with pytest.raises(ValidationError) as exc_info:
        validate_lqp(result)
    error_message = str(exc_info.value)
    assert expected_error in error_message, f"Expected '{expected_error}' in error message: {error_message}"
