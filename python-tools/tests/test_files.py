import os
import pytest
from pathlib import Path
from .utils import (
    get_lqp_input_files, 
    get_lqp_output_files, 
    get_lqp_debug_output_files, 
    get_lqp_pretty_output_files, 
    get_bin_output_files
)


def get_base_filename(filepath):
    """Get the base filename without extension from a file path."""
    return Path(filepath).stem


def check_output_files_have_corresponding_inputs():
    """Check that all output files have corresponding input files."""
    input_files = get_lqp_input_files()
    input_basenames = {get_base_filename(f) for f in input_files}
    
    missing_inputs = []
    
    # Check lqp output files
    for output_file in get_lqp_output_files():
        base_name = get_base_filename(output_file)
        if base_name not in input_basenames:
            missing_inputs.append(f"lqp_output/{Path(output_file).name} -> missing input {base_name}.lqp")
    
    # Check debug output files
    for output_file in get_lqp_debug_output_files():
        base_name = get_base_filename(output_file)
        if base_name not in input_basenames:
            missing_inputs.append(f"lqp_debug_output/{Path(output_file).name} -> missing input {base_name}.lqp")
    
    # Check pretty output files
    for output_file in get_lqp_pretty_output_files():
        base_name = get_base_filename(output_file)
        if base_name not in input_basenames:
            missing_inputs.append(f"lqp_pretty_output/{Path(output_file).name} -> missing input {base_name}.lqp")
    
    # Check binary output files (these have .bin extension but correspond to .lqp inputs)
    for output_file in get_bin_output_files():
        base_name = get_base_filename(output_file)
        if base_name not in input_basenames:
            missing_inputs.append(f"bin_output/{Path(output_file).name} -> missing input {base_name}.lqp")
    
    return missing_inputs


def test_all_output_files_have_corresponding_inputs():
    """Test that all output files have corresponding input files."""
    missing_inputs = check_output_files_have_corresponding_inputs()
    
    if missing_inputs:
        error_message = "Found output files without corresponding input files:\n" + "\n".join(missing_inputs)
        pytest.fail(error_message)
    