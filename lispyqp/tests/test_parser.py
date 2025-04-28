import os
import re
import pytest
import sys
from pathlib import Path
from llqp.parser import parse_lqp
from llqp.validator import ValidationError, validate_lqp

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
VALIDATOR_DIR = Path(__file__).parent / "validator"

def get_all_example_files():
    """Find all .llqp files in the examples directory and subdirectories"""
    example_files = []

    for root, dirs, files in os.walk(EXAMPLES_DIR):
        for file in files:
            if file.endswith(".llqp"):
                example_files.append(os.path.join(root, file))

    return example_files

def get_validator_files():
    """Find all .llqp files in the validator directory"""
    validator_files = []

    for file in os.listdir(VALIDATOR_DIR):
        if file.endswith(".llqp"):
            validator_files.append(os.path.join(VALIDATOR_DIR, file))

    return validator_files

@pytest.mark.parametrize("example_file", get_all_example_files())
def test_parse_example(example_file):
    """Test that each example file can be successfully parsed"""
    try:
        with open(example_file, "r") as f:
            content = f.read()

        # Parse the file and check it returns a valid protobuf object
        result = parse_lqp(content)
        assert result is not None, f"Failed to parse {example_file}"

        # Log the successful parse for verbose output
        print(f"Successfully parsed {example_file}")

    except Exception as e:
        pytest.fail(f"Failed to parse {example_file}: {str(e)}")

def test_basics_file_contents():
    """Test that the basics.llqp file has the expected structure"""
    basics_file = EXAMPLES_DIR / "basics.llqp"

    with open(basics_file, "r") as f:
        content = f.read()

    result = parse_lqp(content)

    assert hasattr(result, "id"), "Missing fragment ID"
    assert result.id.id == b'basics', f"Expected fragment ID 'basics' but got {result.id.id}"

    assert len(result.declarations) > 0, "No declarations found in basics.llqp"

def test_valid_validator_files():
    for validator_file in VALIDATOR_DIR.glob("valid_*.llqp"):
        with open(validator_file, "r") as f:
            content = f.read()
        try:
            result = parse_lqp(content)
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
    result = parse_lqp(content)
    with pytest.raises(ValidationError) as exc_info:
        validate_lqp(result)
    error_message = str(exc_info.value)
    assert expected_error in error_message, f"Expected '{expected_error}' in error message: {error_message}"
