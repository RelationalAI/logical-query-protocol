import os
from pathlib import Path

# Directory constants
PARENT_DIR = Path(__file__).parent
TEST_INPUTS_DIR = PARENT_DIR / "test_files" / "lqp"


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
