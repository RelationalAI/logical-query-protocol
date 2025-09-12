import os
import pytest
from pathlib import Path
from .utils import get_lqp_input_files, get_all_files, PARENT_DIR


def get_base_filename(filepath):
    """Get the base filename without extension from a file path."""
    return Path(filepath).stem


def check_output_files_have_corresponding_inputs():
    """Check that all output files have corresponding input files."""
    input_files = get_lqp_input_files()
    input_basenames = {get_base_filename(f) for f in input_files}

    missing_inputs = []

    output_files = [
        ("lqp_output", ".lqp"),
        ("lqp_debug_output", ".lqp"),
        ("lqp_pretty_output", ".lqp"),
        ("test_files/bin", ".bin"),
    ]

    for directory, file_extension in output_files:
        for output_file in get_all_files(PARENT_DIR / directory, file_extension):
            base_name = get_base_filename(output_file)
            if base_name not in input_basenames:
                missing_inputs.append(f"{directory}/{Path(output_file).name} -> missing input {base_name}.lqp")

    return missing_inputs


def test_all_output_files_have_corresponding_inputs():
    """Test that all output files have corresponding input files."""
    missing_inputs = check_output_files_have_corresponding_inputs()

    if missing_inputs:
        error_message = "Found output files without corresponding input files:\n" + "\n".join(missing_inputs)
        pytest.fail(error_message)
