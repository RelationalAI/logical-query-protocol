"""Tests for provenance (source location tracking) in the generated parser."""

from lqp.gen.parser import Location, Span, parse

SIMPLE_INPUT = """\
(transaction
  (epoch
    (writes)
    (reads)))
"""


def test_provenance_root_transaction():
    """The root path () should span the entire input."""
    _, provenance = parse(SIMPLE_INPUT)
    assert () in provenance
    span = provenance[()]
    # Transaction starts at offset 0 (the opening paren)
    assert span.start.offset == 0
    assert span.start.line == 1
    assert span.start.column == 1


def test_provenance_span_ordering():
    """Verify start <= end for all spans."""
    _, provenance = parse(SIMPLE_INPUT)
    for path, span in provenance.items():
        assert span.start.offset <= span.stop.offset, f"Bad span at path {path}"
        assert span.start.line <= span.stop.line, f"Bad line ordering at path {path}"


def test_provenance_location_fields():
    """Verify Location has correct line, column, offset fields."""
    _, provenance = parse(SIMPLE_INPUT)
    root_span = provenance[()]
    loc = root_span.start
    assert isinstance(loc, Location)
    assert isinstance(loc.line, int)
    assert isinstance(loc.column, int)
    assert isinstance(loc.offset, int)


def test_provenance_span_fields():
    """Verify Span has start and stop Location."""
    _, provenance = parse(SIMPLE_INPUT)
    root_span = provenance[()]
    assert isinstance(root_span, Span)
    assert isinstance(root_span.start, Location)
    assert isinstance(root_span.stop, Location)
