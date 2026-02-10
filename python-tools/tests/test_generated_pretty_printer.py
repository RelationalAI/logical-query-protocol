"""Tests for the generated pretty printer.

Three test suites:
1. Roundtrip (idempotency): parse → print → parse → print → compare the two prints.
2. Comparison: generated pretty printer output vs old IR-based pretty printer output.
3. Bin roundtrip: parse .bin → print → re-parse → compare protobuf with original.
"""

import re
import pytest
from pathlib import Path

from lqp.parser import parse_lqp
from lqp.emit import ir_to_proto
from lqp.generated_pretty_printer import pretty
from lqp.generated_parser import parse as generated_parse
from lqp.cli import read_bin_to_proto
import lqp.print as lqp_print

from .utils import get_lqp_input_files, get_all_files, PARENT_DIR


BIN_DIR = PARENT_DIR / "test_files" / "bin"


def get_bin_input_files():
    """Find all .bin files in the test inputs directory."""
    return get_all_files(BIN_DIR, ".bin")


def _stem(path: str) -> str:
    return Path(path).stem


def _parse_and_pretty(input_file: str) -> str:
    """Parse an .lqp file through IR → protobuf → generated pretty printer."""
    with open(input_file, "r") as f:
        content = f.read()
    ir_node = parse_lqp(input_file, content)
    proto = ir_to_proto(ir_node)
    return pretty(proto)


def _normalize_ws(s: str) -> str:
    """Collapse all whitespace sequences to a single space."""
    return re.sub(r'\s+', ' ', s).strip()


def _clear_debug_info(proto):
    """Clear debug_info from all fragments in a Transaction."""
    for epoch in proto.epochs:
        for write in epoch.writes:
            if write.HasField('define'):
                write.define.fragment.ClearField('debug_info')


@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_roundtrip_idempotent(input_file):
    """Parse → print → parse → print, then compare the two printed outputs."""
    stem = _stem(input_file)

    # First pass: .lqp → IR → proto → pretty-print
    text1 = _parse_and_pretty(input_file)

    # Second pass: parse printed output → proto → pretty-print again
    proto2 = generated_parse(text1)
    text2 = pretty(proto2)

    assert text1 == text2, (
        f"Pretty printer is not idempotent for {stem}.\n"
        f"=== First print ===\n{text1}\n"
        f"=== Second print ===\n{text2}"
    )


@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_matches_old_pretty_printer(input_file):
    """Compare generated pretty printer output to old IR-based pretty printer."""
    stem = _stem(input_file)

    with open(input_file, "r") as f:
        content = f.read()

    # Generated pretty printer: IR → proto → pretty
    ir_node = parse_lqp(input_file, content)
    proto = ir_to_proto(ir_node)
    generated_output = pretty(proto)

    # Old pretty printer: IR → string (with names, no debug info)
    options = lqp_print.ugly_config.copy()
    options[str(lqp_print.PrettyOptions.PRINT_NAMES)] = True
    options[str(lqp_print.PrettyOptions.PRINT_DEBUG)] = False
    old_output = lqp_print.to_string(ir_node, options)

    assert _normalize_ws(generated_output) == _normalize_ws(old_output), (
        f"Outputs differ for {stem}.\n"
        f"=== Generated ===\n{generated_output}\n"
        f"=== Old (PRINT_NAMES) ===\n{old_output}"
    )


@pytest.mark.parametrize("input_file", get_bin_input_files())
def test_bin_roundtrip(input_file):
    """Parse .bin → print → re-parse → compare protobuf with original."""
    stem = _stem(input_file)

    # Parse binary protobuf
    proto1 = read_bin_to_proto(input_file)

    # Pretty-print → re-parse
    text = pretty(proto1)
    proto2 = generated_parse(text)

    # Clear debug info before comparison since pretty printer
    # consumes but does not output debug info
    _clear_debug_info(proto1)
    _clear_debug_info(proto2)

    # Compare serialized protobufs
    binary1 = proto1.SerializeToString()
    binary2 = proto2.SerializeToString()

    assert binary1 == binary2, (
        f"Bin roundtrip failed for {stem}.\n"
        f"=== Pretty-printed ===\n{text}"
    )
