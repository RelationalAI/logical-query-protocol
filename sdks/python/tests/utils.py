import os
import re
from pathlib import Path

# Directory constants
PARENT_DIR = Path(__file__).parent
REPO_ROOT = PARENT_DIR.parent.parent.parent
TEST_INPUTS_DIR = REPO_ROOT / "tests" / "lqp"
BIN_SNAPSHOTS_DIR = REPO_ROOT / "tests" / "bin"
VALIDATOR_DIR = PARENT_DIR / "validator"


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


def get_bin_input_files():
    """Find all .bin files in the binary snapshots directory."""
    return get_all_files(BIN_SNAPSHOTS_DIR, ".bin")


def extract_expected_error(file_path) -> str | None:
    """Extract the expected error from a ;; ERROR: comment in the file."""
    with open(file_path) as f:
        content = f.read()
    error_match = re.search(r";;\s*ERROR:\s*(.+)(?:\n|\r\n?)", content)
    if error_match:
        return error_match.group(1).strip()
    return None
