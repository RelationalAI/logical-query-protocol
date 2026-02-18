"""Tests for the generated pretty printer (lqp.gen.pretty).

Tests the PrettyPrinter class and the top-level pretty() function,
verifying roundtrip correctness (parse -> pretty -> re-parse),
snapshot output stability, and internal formatting behavior.
"""

import os
from io import StringIO
from pathlib import Path

import pytest

from lqp.gen.parser import parse as generated_parse
from lqp.gen.pretty import PrettyPrinter, pretty
from lqp.proto.v1 import fragments_pb2, logic_pb2, transactions_pb2

from .utils import REPO_ROOT, TEST_INPUTS_DIR, get_bin_input_files, get_lqp_input_files

# ---------------------------------------------------------------------------
# Roundtrip tests: parse -> pretty -> re-parse, compare protobuf bytes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_roundtrip(input_file):
    """Pretty-printed output must re-parse to the same protobuf."""
    with open(input_file) as f:
        content = f.read()
    proto = generated_parse(content)
    printed = pretty(proto)
    re_proto = generated_parse(printed)
    assert proto.SerializeToString() == re_proto.SerializeToString(), (
        f"Roundtrip failed for {Path(input_file).name}:\n"
        f"Original proto:\n{proto}\n"
        f"Pretty output:\n{printed}\n"
        f"Re-parsed proto:\n{re_proto}"
    )


# ---------------------------------------------------------------------------
# Snapshot tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_pretty_snapshot(snapshot, input_file):
    """Pretty output must match saved snapshots."""
    with open(input_file) as f:
        content = f.read()
    proto = generated_parse(content)
    printed = pretty(proto)
    snapshot.snapshot_dir = str(REPO_ROOT / "tests" / "pretty")
    snapshot.assert_match(printed, os.path.basename(input_file))


# ---------------------------------------------------------------------------
# max_width tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_roundtrip_narrow(input_file):
    """Roundtrip still works with a very narrow max_width (forces multi-line)."""
    with open(input_file) as f:
        content = f.read()
    proto = generated_parse(content)
    printed = pretty(proto, max_width=40)
    re_proto = generated_parse(printed)
    assert proto.SerializeToString() == re_proto.SerializeToString()


@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_roundtrip_wide(input_file):
    """Roundtrip still works with a very wide max_width (forces flat where possible)."""
    with open(input_file) as f:
        content = f.read()
    proto = generated_parse(content)
    printed = pretty(proto, max_width=1000)
    re_proto = generated_parse(printed)
    assert proto.SerializeToString() == re_proto.SerializeToString()


def test_narrow_width_produces_more_lines():
    """A narrow width should produce at least as many lines as the default."""
    content = Path(TEST_INPUTS_DIR / "arithmetic.lqp").read_text()
    proto = generated_parse(content)
    default_output = pretty(proto)
    narrow_output = pretty(proto, max_width=40)
    assert narrow_output.count("\n") >= default_output.count("\n")


def test_wide_width_produces_fewer_lines():
    """A very wide width should produce at most as many lines as the default."""
    content = Path(TEST_INPUTS_DIR / "arithmetic.lqp").read_text()
    proto = generated_parse(content)
    default_output = pretty(proto)
    wide_output = pretty(proto, max_width=1000)
    assert wide_output.count("\n") <= default_output.count("\n")


# ---------------------------------------------------------------------------
# IO parameter tests
# ---------------------------------------------------------------------------


def test_pretty_writes_to_provided_io():
    """When an IO object is provided, pretty printer writes to it."""
    content = Path(TEST_INPUTS_DIR / "simple_relatom.lqp").read_text()
    proto = generated_parse(content)
    buf = StringIO()
    result = pretty(proto, io=buf)
    assert buf.getvalue() == result
    assert len(result) > 0


def test_pretty_returns_string_without_io():
    """Without an IO argument, pretty() returns the output as a string."""
    content = Path(TEST_INPUTS_DIR / "simple_relatom.lqp").read_text()
    proto = generated_parse(content)
    result = pretty(proto)
    assert isinstance(result, str)
    assert result.startswith("(transaction")


# ---------------------------------------------------------------------------
# PrettyPrinter unit tests
# ---------------------------------------------------------------------------


class TestPrettyPrinterWrite:
    def test_write_indentation(self):
        """indent() pushes the current column as the new indent level."""
        pp = PrettyPrinter()
        # Write '(' so column is 1, then indent pushes column 1
        pp.write("(")
        pp.indent()
        pp.newline()
        pp.write("hello")
        output = pp.get_output()
        assert output == "(\n hello"

    def test_write_no_indent_in_flat_mode(self):
        pp = PrettyPrinter()
        pp.separator = " "
        pp.at_line_start = False
        pp.indent()
        pp.newline()
        pp.write("hello")
        output = pp.get_output()
        assert output == " hello"

    def test_indent_sexp(self):
        """indent_sexp() pushes parent indent + 2."""
        pp = PrettyPrinter()
        pp.write("(keyword")
        pp.indent_sexp()
        pp.newline()
        pp.write("child")
        output = pp.get_output()
        assert output == "(keyword\n  child"

    def test_indent_dedent(self):
        pp = PrettyPrinter()
        pp.write("(")
        pp.indent()  # pushes column 1
        pp.newline()
        pp.write("(")
        pp.indent()  # pushes column 2
        pp.newline()
        pp.write("a")
        pp.dedent()
        pp.newline()
        pp.write("b")
        output = pp.get_output()
        assert output == "(\n (\n  a\n b"

    def test_dedent_does_not_go_below_initial(self):
        pp = PrettyPrinter()
        pp.dedent()
        pp.dedent()
        assert pp.indent_level == 0


class TestFormatHelpers:
    def test_format_string_value_plain(self):
        pp = PrettyPrinter()
        assert pp.format_string_value("hello") == '"hello"'

    def test_format_string_value_escapes(self):
        pp = PrettyPrinter()
        assert pp.format_string_value('a"b') == '"a\\"b"'
        assert pp.format_string_value("a\nb") == '"a\\nb"'
        assert pp.format_string_value("a\\b") == '"a\\\\b"'
        assert pp.format_string_value("a\tb") == '"a\\tb"'
        assert pp.format_string_value("a\rb") == '"a\\rb"'

    def test_format_int128_positive(self):
        pp = PrettyPrinter()
        msg = logic_pb2.Int128Value(low=42, high=0)
        assert pp.format_int128(msg) == "42i128"

    def test_format_int128_negative(self):
        pp = PrettyPrinter()
        # -1 in two's complement 128-bit: high=0xFFFFFFFFFFFFFFFF, low=0xFFFFFFFFFFFFFFFF
        msg = logic_pb2.Int128Value(
            low=0xFFFFFFFFFFFFFFFF,
            high=0xFFFFFFFFFFFFFFFF,
        )
        assert pp.format_int128(msg) == "-1i128"

    def test_format_int128_zero(self):
        pp = PrettyPrinter()
        msg = logic_pb2.Int128Value(low=0, high=0)
        assert pp.format_int128(msg) == "0i128"

    def test_format_uint128_zero(self):
        pp = PrettyPrinter()
        msg = logic_pb2.UInt128Value(low=0, high=0)
        assert pp.format_uint128(msg) == "0x0"

    def test_format_uint128_max(self):
        pp = PrettyPrinter()
        msg = logic_pb2.UInt128Value(
            low=0xFFFFFFFFFFFFFFFF,
            high=0xFFFFFFFFFFFFFFFF,
        )
        assert pp.format_uint128(msg) == "0xffffffffffffffffffffffffffffffff"

    def test_format_decimal_positive(self):
        pp = PrettyPrinter()
        # 123.456789 with precision 18, scale 6
        # unscaled value = 123456789
        msg = logic_pb2.DecimalValue(
            value=logic_pb2.Int128Value(low=123456789, high=0),
            precision=18,
            scale=6,
        )
        assert pp.format_decimal(msg) == "123.456789d18"

    def test_format_decimal_zero(self):
        pp = PrettyPrinter()
        msg = logic_pb2.DecimalValue(
            value=logic_pb2.Int128Value(low=0, high=0),
            precision=18,
            scale=6,
        )
        assert pp.format_decimal(msg) == "0.000000d18"

    def test_format_decimal_negative(self):
        pp = PrettyPrinter()
        # -123.456789 => unscaled -123456789
        # Two's complement 128-bit of -123456789
        val = (1 << 128) - 123456789
        low = val & 0xFFFFFFFFFFFFFFFF
        high = (val >> 64) & 0xFFFFFFFFFFFFFFFF
        msg = logic_pb2.DecimalValue(
            value=logic_pb2.Int128Value(low=low, high=high),
            precision=18,
            scale=6,
        )
        assert pp.format_decimal(msg) == "-123.456789d18"


class TestRelationIdLookup:
    def test_relation_id_to_string_with_debug_info(self):
        pp = PrettyPrinter()
        pp._debug_info[(42, 0)] = "my_relation"
        msg = logic_pb2.RelationId(id_low=42, id_high=0)
        assert pp.relation_id_to_string(msg) == "my_relation"

    def test_relation_id_to_string_without_debug_info(self):
        pp = PrettyPrinter()
        msg = logic_pb2.RelationId(id_low=42, id_high=0)
        assert pp.relation_id_to_string(msg) == ""

    def test_fragment_id_to_string(self):
        pp = PrettyPrinter()
        msg = fragments_pb2.FragmentId(id=b"my_fragment")
        assert pp.fragment_id_to_string(msg) == "my_fragment"

    def test_fragment_id_to_string_empty(self):
        pp = PrettyPrinter()
        msg = fragments_pb2.FragmentId(id=b"")
        assert pp.fragment_id_to_string(msg) == ""


class TestTryFlat:
    def test_flat_rendering_short_message(self):
        """A short conjunction should render flat when it fits."""
        content = Path(TEST_INPUTS_DIR / "simple_relatom.lqp").read_text()
        proto = generated_parse(content)
        wide = pretty(proto, max_width=1000)
        narrow = pretty(proto, max_width=20)
        assert narrow.count("\n") >= wide.count("\n")

    def test_memo_caching(self):
        """Flat representations should be memoized."""
        content = Path(TEST_INPUTS_DIR / "simple_relatom.lqp").read_text()
        proto = generated_parse(content)
        pp = PrettyPrinter(max_width=92)
        pp.pretty_transaction(proto)
        # After printing, memo should have entries
        assert len(pp._memo) > 0


class TestGetOutput:
    def test_get_output_with_stringio(self):
        pp = PrettyPrinter()
        pp.write("hello")
        assert pp.get_output() == "hello"

    def test_get_output_with_custom_io(self):
        buf = StringIO()
        pp = PrettyPrinter(io=buf)
        pp.write("hello")
        assert pp.get_output() == "hello"
        assert buf.getvalue() == "hello"


# ---------------------------------------------------------------------------
# Output content sanity checks
# ---------------------------------------------------------------------------


class TestOutputContent:
    def test_output_starts_with_transaction(self):
        content = Path(TEST_INPUTS_DIR / "simple_relatom.lqp").read_text()
        proto = generated_parse(content)
        output = pretty(proto)
        assert output.strip().startswith("(transaction")

    def test_output_ends_with_newline(self):
        content = Path(TEST_INPUTS_DIR / "simple_relatom.lqp").read_text()
        proto = generated_parse(content)
        output = pretty(proto)
        assert output.endswith("\n")

    def test_output_has_balanced_parens(self):
        for input_file in get_lqp_input_files():
            with open(input_file) as f:
                content = f.read()
            proto = generated_parse(content)
            output = pretty(proto)
            opens = output.count("(")
            closes = output.count(")")
            assert opens == closes, (
                f"Unbalanced parens in {Path(input_file).name}: "
                f"{opens} opens vs {closes} closes"
            )

    def test_output_has_balanced_brackets(self):
        for input_file in get_lqp_input_files():
            with open(input_file) as f:
                content = f.read()
            proto = generated_parse(content)
            output = pretty(proto)
            opens = output.count("[")
            closes = output.count("]")
            assert opens == closes, (
                f"Unbalanced brackets in {Path(input_file).name}: "
                f"{opens} opens vs {closes} closes"
            )

    def test_values_file_contains_expected_keywords(self):
        content = Path(TEST_INPUTS_DIR / "values.lqp").read_text()
        proto = generated_parse(content)
        output = pretty(proto)
        for kw in [
            "transaction",
            "epoch",
            "writes",
            "define",
            "fragment",
            "def",
            "reads",
            "output",
        ]:
            assert kw in output, f"Missing keyword '{kw}' in values output"

    def test_arithmetic_contains_operators(self):
        content = Path(TEST_INPUTS_DIR / "arithmetic.lqp").read_text()
        proto = generated_parse(content)
        output = pretty(proto)
        for op in ["(+", "(-", "(*", "(/"]:
            assert op in output, f"Missing operator '{op}' in arithmetic output"

    def test_no_trailing_whitespace(self):
        """No line should have trailing whitespace."""
        for input_file in get_lqp_input_files():
            with open(input_file) as f:
                content = f.read()
            proto = generated_parse(content)
            output = pretty(proto)
            for i, line in enumerate(output.split("\n"), 1):
                assert line == line.rstrip(), (
                    f"Trailing whitespace on line {i} of "
                    f"{Path(input_file).name}: {line!r}"
                )


# ---------------------------------------------------------------------------
# Binary input tests: decode protobuf binary, then pretty-print
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bin_file", get_bin_input_files())
def test_pretty_from_binary_snapshot(snapshot, bin_file):
    """Pretty-printing a decoded binary must match the saved snapshot."""
    with open(bin_file, "rb") as f:
        data = f.read()
    txn = transactions_pb2.Transaction()
    txn.ParseFromString(data)
    printed = pretty(txn)
    snapshot.snapshot_dir = str(REPO_ROOT / "tests" / "pretty")
    snapshot_filename = os.path.basename(bin_file).replace(".bin", ".lqp")
    snapshot.assert_match(printed, snapshot_filename)


@pytest.mark.parametrize("bin_file", get_bin_input_files())
def test_pretty_from_binary_roundtrip(bin_file):
    """Pretty-printed output from binary must re-parse to the same protobuf."""
    with open(bin_file, "rb") as f:
        data = f.read()
    txn = transactions_pb2.Transaction()
    txn.ParseFromString(data)
    printed = pretty(txn)
    re_proto = generated_parse(printed)
    assert txn.SerializeToString() == re_proto.SerializeToString(), (
        f"Binary roundtrip failed for {Path(bin_file).name}"
    )
