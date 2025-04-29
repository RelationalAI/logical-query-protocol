import os
import re
import pytest
import sys
from pathlib import Path
from llqp.parser import parse_lqp

TEST_INPUTS_DIR = Path(__file__).parent / "test_files" / "lqp_input"
TEST_OUTPUTS_DIR = Path(__file__).parent / "test_files" / "bin_output"

def get_all_input_files():
    """Find all .llqp files in the test inputs directory and subdirectories"""
    input_files = []

    for root, dirs, files in os.walk(TEST_INPUTS_DIR):
        for file in files:
            if file.endswith(".llqp"):
                input_files.append(os.path.join(root, file))

    return input_files

def get_output_file(input_file):
    """Get the corresponding output file for a given input file"""
    base_name = os.path.basename(input_file)
    output_file = os.path.join(TEST_OUTPUTS_DIR, base_name.replace(".llqp", ".bin"))
    return output_file

@pytest.mark.parametrize("input_file", get_all_input_files())
def test_parse_lqp(input_file):
    """Test that each input file can be successfully parsed"""
    try:
        with open(input_file, "r") as f:
            content = f.read()

        # Parse the file and check it returns a valid protobuf object
        result = parse_lqp(content)
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
