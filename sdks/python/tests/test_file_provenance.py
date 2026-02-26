"""Tests that parse LQP files from disk and verify provenance spans are correct."""

import os

import pytest

from lqp.gen.parser import parse

from .utils import get_lqp_input_files


def extract_text(content: str, span) -> str:
    """Extract the substring of content covered by a span (0-based offsets)."""
    return content[span.start.offset : span.stop.offset]


@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_provenance_spans_valid(input_file):
    """Every provenance span should have valid line/column/offset and start <= end."""
    with open(input_file) as f:
        content = f.read()

    _, provenance = parse(content)
    assert len(provenance) > 0, f"No provenance entries for {input_file}"

    lines = content.split("\n")

    for path, span in provenance.items():
        # start <= end
        assert span.start.offset <= span.stop.offset, (
            f"{os.path.basename(input_file)} path {path}: "
            f"start offset {span.start.offset} > end offset {span.stop.offset}"
        )
        assert span.start.line <= span.stop.line or (
            span.start.line == span.stop.line and span.start.column <= span.stop.column
        ), (
            f"{os.path.basename(input_file)} path {path}: "
            f"start {span.start.line}:{span.start.column} > "
            f"end {span.stop.line}:{span.stop.column}"
        )

        # offsets in range
        assert 0 <= span.start.offset <= len(content), (
            f"{os.path.basename(input_file)} path {path}: "
            f"start offset {span.start.offset} out of range"
        )
        assert 0 <= span.stop.offset <= len(content), (
            f"{os.path.basename(input_file)} path {path}: "
            f"end offset {span.stop.offset} out of range"
        )

        # lines are 1-based and valid
        assert 1 <= span.start.line <= len(lines), (
            f"{os.path.basename(input_file)} path {path}: "
            f"start line {span.start.line} out of range"
        )

        # columns are 1-based
        assert span.start.column >= 1, (
            f"{os.path.basename(input_file)} path {path}: "
            f"start column {span.start.column} < 1"
        )


@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_provenance_root_spans_file(input_file):
    """The root path () should start at the beginning of the transaction."""
    with open(input_file) as f:
        content = f.read()

    _, provenance = parse(content)
    assert () in provenance, f"No root provenance for {input_file}"

    root_span = provenance[()]
    text = extract_text(content, root_span)
    assert text.startswith("(transaction"), (
        f"{os.path.basename(input_file)}: root span text starts with "
        f"{text[:30]!r}, expected '(transaction'"
    )


@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_provenance_offsets_match_line_column(input_file):
    """Verify that offset is consistent with line and column."""
    with open(input_file) as f:
        content = f.read()

    _, provenance = parse(content)

    # Build a map from (line, col) -> offset using 1-based lines and columns
    line_offsets = [0]  # offset of start of line 1
    for i, ch in enumerate(content):
        if ch == "\n":
            line_offsets.append(i + 1)

    for path, span in provenance.items():
        loc = span.start
        if loc.line <= len(line_offsets):
            expected_offset = line_offsets[loc.line - 1] + (loc.column - 1)
            assert loc.offset == expected_offset, (
                f"{os.path.basename(input_file)} path {path}: "
                f"offset {loc.offset} != expected {expected_offset} "
                f"(line {loc.line}, col {loc.column})"
            )
