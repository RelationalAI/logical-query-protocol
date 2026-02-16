import os
import re

import pytest

from lqp.gen.parser import parse
from lqp.gen.pretty import pretty

from .utils import get_lqp_input_files

PRETTY_SNAPSHOTS_DIR = os.path.join(os.path.dirname(__file__), "lqp_pretty_output")


def _normalize_primitives(s: str) -> str:
    """Normalize shorthand primitive syntax to verbose form."""
    s = re.sub(r"\(\s*=\s+", "(primitive :rel_primitive_eq ", s)
    s = re.sub(r"\(\s*<=\s+", "(primitive :rel_primitive_lt_eq_monotype ", s)
    s = re.sub(r"\(\s*>=\s+", "(primitive :rel_primitive_gt_eq_monotype ", s)
    s = re.sub(r"\(\s*<\s+", "(primitive :rel_primitive_lt_monotype ", s)
    s = re.sub(r"\(\s*>\s+", "(primitive :rel_primitive_gt_monotype ", s)
    s = re.sub(r"\(\s*\+\s+", "(primitive :rel_primitive_add_monotype ", s)
    s = re.sub(r"\(\s*-\s+", "(primitive :rel_primitive_subtract_monotype ", s)
    s = re.sub(r"\(\s*\*\s+", "(primitive :rel_primitive_multiply_monotype ", s)
    s = re.sub(r"\(\s*/\s+", "(primitive :rel_primitive_divide_monotype ", s)
    return s


def _normalize_formulas(s: str) -> str:
    """Normalize (true) to (and) and (false) to (or)."""
    s = re.sub(r"\(\s*true\s*\)", "(and)", s)
    s = re.sub(r"\(\s*false\s*\)", "(or)", s)
    return s


def _normalize_header_row(s: str) -> str:
    """Normalize :syntax_header_row bool/int differences."""
    s = re.sub(r":syntax_header_row\s+1\b", ":syntax_header_row true", s)
    s = re.sub(r":syntax_header_row\s+0\b", ":syntax_header_row false", s)
    return s


def _normalize_ws(s: str) -> str:
    """Collapse all whitespace sequences to a single space, strip spaces before closing brackets."""
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s+([)\]}])", r"\1", s)
    return s


def _normalize(s: str) -> str:
    """Apply all normalizations."""
    s = _normalize_primitives(s)
    s = _normalize_formulas(s)
    s = _normalize_header_row(s)
    s = _normalize_ws(s)
    return s


@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_pretty_print_roundtrip(input_file):
    """Test that pretty-printing then re-parsing produces the same binary."""
    with open(input_file) as f:
        original_text = f.read()

    txn = parse(original_text)
    original_binary = txn.SerializeToString()

    printed = pretty(txn)
    re_parsed = parse(printed)
    re_parsed_binary = re_parsed.SerializeToString()

    assert original_binary == re_parsed_binary, f"Round-trip mismatch for {input_file}"


@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_pretty_print_snapshot(input_file):
    """Test that pretty-printed output matches snapshots (with normalization)."""
    with open(input_file) as f:
        content = f.read()

    txn = parse(content)
    printed = pretty(txn)

    snapshot_file = os.path.join(PRETTY_SNAPSHOTS_DIR, os.path.basename(input_file))
    with open(snapshot_file) as f:
        expected = f.read()

    assert _normalize(printed) == _normalize(expected), (
        f"Snapshot mismatch for {input_file}.\n"
        f"=== Generated ===\n{printed}\n"
        f"=== Snapshot ===\n{expected}"
    )
