"""Tests for provenance (source location tracking) in the generated parser."""

from lqp.gen.parser import Location, Span, parse

SIMPLE_INPUT = """\
(transaction
  (epoch
    (writes)
    (reads)))
"""


def _find_span(provenance, type_name):
    """Find the first span with the given type_name."""
    for span in provenance.values():
        if span.type_name == type_name:
            return span
    return None


def test_provenance_root_transaction():
    """The root transaction should have a span starting at offset 0."""
    _, provenance = parse(SIMPLE_INPUT)
    span = _find_span(provenance, "Transaction")
    assert span is not None
    assert span.start.offset == 0
    assert span.start.line == 1
    assert span.start.column == 1


def test_provenance_span_ordering():
    """Verify start <= end for all spans."""
    _, provenance = parse(SIMPLE_INPUT)
    for offset, span in provenance.items():
        assert span.start.offset <= span.stop.offset, f"Bad span at offset {offset}"
        assert span.start.line <= span.stop.line, (
            f"Bad line ordering at offset {offset}"
        )


def test_provenance_location_fields():
    """Verify Location has correct line, column, offset fields."""
    _, provenance = parse(SIMPLE_INPUT)
    root_span = _find_span(provenance, "Transaction")
    assert root_span is not None
    loc = root_span.start
    assert isinstance(loc, Location)
    assert isinstance(loc.line, int)
    assert isinstance(loc.column, int)
    assert isinstance(loc.offset, int)


def test_provenance_span_fields():
    """Verify Span has start and stop Location."""
    _, provenance = parse(SIMPLE_INPUT)
    root_span = _find_span(provenance, "Transaction")
    assert root_span is not None
    assert isinstance(root_span, Span)
    assert isinstance(root_span.start, Location)
    assert isinstance(root_span.stop, Location)
