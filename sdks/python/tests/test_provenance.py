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


def test_provenance_epoch():
    """The first epoch should be at path (1, 0)."""
    _, provenance = parse(SIMPLE_INPUT)
    # epochs = field 1, index 0
    key = (1, 0)
    assert key in provenance
    span = provenance[key]
    # The epoch starts at "(epoch" which is indented on line 2
    assert span.start.line == 2


def test_provenance_writes():
    """Writes section should be at path (1, 0, 1)."""
    _, provenance = parse(SIMPLE_INPUT)
    # epochs[0].writes = field 1 within Epoch
    key = (1, 0, 1)
    assert key in provenance
    span = provenance[key]
    assert span.start.line == 3


def test_provenance_reads():
    """Reads section should be at path (1, 0, 2)."""
    _, provenance = parse(SIMPLE_INPUT)
    # epochs[0].reads = field 2 within Epoch
    key = (1, 0, 2)
    assert key in provenance
    span = provenance[key]
    assert span.start.line == 4


def test_provenance_span_covers_correct_text():
    """Verify that spans map back to the correct substrings."""
    _, provenance = parse(SIMPLE_INPUT)

    # Root transaction span should cover from start
    root_span = provenance[()]
    assert root_span.start.offset == 0

    # Epoch span should start at the '(' of '(epoch'
    epoch_span = provenance[(1, 0)]
    text_at_epoch = SIMPLE_INPUT[epoch_span.start.offset :]
    assert text_at_epoch.startswith("(epoch")


def test_provenance_span_ordering():
    """Verify start <= end for all spans."""
    _, provenance = parse(SIMPLE_INPUT)
    for path, span in provenance.items():
        assert span.start.offset <= span.end.offset, f"Bad span at path {path}"
        assert span.start.line <= span.end.line, f"Bad line ordering at path {path}"


def test_provenance_multiple_epochs():
    """Multiple epochs should be indexed correctly."""
    input_str = """\
(transaction
  (epoch
    (writes)
    (reads))
  (epoch
    (writes)
    (reads)))
"""
    _, provenance = parse(input_str)

    # First epoch at (1, 0), second at (1, 1)
    assert (1, 0) in provenance
    assert (1, 1) in provenance

    # First epoch starts before second
    assert provenance[(1, 0)].start.offset < provenance[(1, 1)].start.offset


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
    """Verify Span has start and end Location."""
    _, provenance = parse(SIMPLE_INPUT)
    root_span = provenance[()]
    assert isinstance(root_span, Span)
    assert isinstance(root_span.start, Location)
    assert isinstance(root_span.end, Location)
