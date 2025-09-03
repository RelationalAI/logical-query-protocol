import os
from pathlib import Path

# Directory constants
TEST_FILES_DIR = Path(__file__).parent / "test_files"
TEST_INPUTS_DIR = TEST_FILES_DIR / "lqp_input"
LQP_OUTPUT_DIR = Path(__file__).parent / "lqp_output"
LQP_DEBUG_OUTPUT_DIR = Path(__file__).parent / "lqp_debug_output"
LQP_PRETTY_OUTPUT_DIR = Path(__file__).parent / "lqp_pretty_output"
BIN_OUTPUT_DIR = TEST_FILES_DIR / "bin_output"

def get_all_files(dir, file_extension):
    """Recursively find all files in a directory."""
    all_files = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.endswith(file_extension):
                all_files.append(os.path.join(root, file))
    return all_files

def get_lqp_input_files():
    """Find all .lqp files in the test inputs directory."""
    return get_all_files(TEST_INPUTS_DIR, ".lqp")

def get_lqp_output_files():
    """Find all files in the lqp_output directory."""
    return get_all_files(LQP_OUTPUT_DIR, ".lqp")

def get_lqp_debug_output_files():
    """Find all files in the lqp_debug_output directory."""
    return get_all_files(LQP_DEBUG_OUTPUT_DIR, ".lqp")

def get_lqp_pretty_output_files():
    """Find all files in the lqp_pretty_output directory."""
    return get_all_files(LQP_PRETTY_OUTPUT_DIR, ".lqp")

def get_bin_output_files():
    """Find all .bin files in the bin_output directory."""
    return get_all_files(BIN_OUTPUT_DIR, ".bin")
