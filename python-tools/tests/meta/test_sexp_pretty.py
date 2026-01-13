"""Tests for the s-expression pretty printer."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.sexp import SAtom, SList, slist, symbol, string, atom
from meta.sexp_pretty import pretty_print, compact_print
from meta.sexp_parser import parse_sexp


class TestCompactPrint:
    """Tests for compact (single-line) printing."""

    def test_atom_symbol(self):
        assert compact_print(SAtom("foo")) == "foo"

    def test_atom_integer(self):
        assert compact_print(SAtom(42)) == "42"

    def test_atom_float(self):
        assert compact_print(SAtom(3.14)) == "3.14"

    def test_atom_bool_true(self):
        assert compact_print(SAtom(True)) == "true"

    def test_atom_bool_false(self):
        assert compact_print(SAtom(False)) == "false"

    def test_atom_string(self):
        assert compact_print(SAtom("hello", quoted=True)) == '"hello"'

    def test_atom_string_with_quotes(self):
        result = compact_print(SAtom('say "hi"', quoted=True))
        assert result == '"say \\"hi\\""'

    def test_atom_string_with_newline(self):
        result = compact_print(SAtom("a\nb", quoted=True))
        assert result == '"a\\nb"'

    def test_empty_list(self):
        assert compact_print(SList(())) == "()"

    def test_single_element_list(self):
        assert compact_print(SList((SAtom("foo"),))) == "(foo)"

    def test_multiple_element_list(self):
        assert compact_print(SList((SAtom("a"), SAtom("b"), SAtom("c")))) == "(a b c)"

    def test_nested_list(self):
        expr = SList((SAtom("a"), SList((SAtom("b"), SAtom("c")))))
        assert compact_print(expr) == "(a (b c))"

    def test_complex_expression(self):
        expr = slist(symbol("define"), slist(symbol("f"), symbol("x")),
                     slist(symbol("*"), symbol("x"), symbol("x")))
        assert compact_print(expr) == "(define (f x) (* x x))"


class TestPrettyPrint:
    """Tests for pretty printing with formatting."""

    def test_atom_symbol(self):
        assert pretty_print(SAtom("foo")) == "foo"

    def test_atom_integer(self):
        assert pretty_print(SAtom(42)) == "42"

    def test_atom_string(self):
        assert pretty_print(SAtom("hello", quoted=True)) == '"hello"'

    def test_empty_list(self):
        assert pretty_print(SList(())) == "()"

    def test_short_list_single_line(self):
        expr = slist(symbol("foo"), symbol("bar"))
        result = pretty_print(expr, width=80)
        assert result == "(foo bar)"

    def test_long_list_multiline(self):
        # Create a list long enough to exceed width
        expr = slist(
            symbol("this_is_a_very_long_function_name"),
            symbol("argument1"),
            symbol("argument2"),
            symbol("argument3")
        )
        result = pretty_print(expr, width=40)
        assert "\n" in result
        assert "this_is_a_very_long_function_name" in result

    def test_nested_list_formatting(self):
        expr = slist(
            symbol("rule"),
            symbol("value"),
            slist(symbol("Message"), symbol("logic"), symbol("Value")),
            string("missing"),
            slist(symbol("lambda"), slist(), slist(symbol("lit"), atom(True)))
        )
        result = pretty_print(expr, width=60)
        # Should be formatted readably
        assert "rule" in result
        assert "value" in result

    def test_indentation_preserved(self):
        expr = slist(
            symbol("outer"),
            slist(symbol("inner1"), symbol("a"), symbol("b")),
            slist(symbol("inner2"), symbol("c"), symbol("d"))
        )
        result = pretty_print(expr, width=30)
        lines = result.split("\n")
        # Check that nested elements are indented
        if len(lines) > 1:
            # Inner lines should have some indentation
            for line in lines[1:]:
                if line.strip():
                    assert line.startswith(" ")

    def test_deeply_nested(self):
        expr = slist(
            symbol("a"),
            slist(
                symbol("b"),
                slist(
                    symbol("c"),
                    slist(symbol("d"), symbol("e"))
                )
            )
        )
        result = pretty_print(expr, width=20)
        # Should handle deep nesting gracefully
        assert "a" in result
        assert "b" in result
        assert "c" in result
        assert "d" in result

    def test_width_respected(self):
        expr = slist(symbol("x"), symbol("y"), symbol("z"))
        result = pretty_print(expr, width=5)
        # With width 5, should go multiline
        # "(x y z)" is 7 chars
        if len("(x y z)") > 5:
            assert "\n" in result


class TestRoundTrip:
    """Tests for parse -> print -> parse round-tripping."""

    def test_roundtrip_symbol(self):
        original = "foo"
        parsed = parse_sexp(original)
        printed = compact_print(parsed)
        reparsed = parse_sexp(printed)
        assert reparsed == parsed

    def test_roundtrip_integer(self):
        original = "42"
        parsed = parse_sexp(original)
        printed = compact_print(parsed)
        reparsed = parse_sexp(printed)
        assert reparsed == parsed

    def test_roundtrip_string(self):
        original = '"hello world"'
        parsed = parse_sexp(original)
        printed = compact_print(parsed)
        reparsed = parse_sexp(printed)
        assert reparsed == parsed

    def test_roundtrip_string_with_escapes(self):
        original = r'"line1\nline2"'
        parsed = parse_sexp(original)
        printed = compact_print(parsed)
        reparsed = parse_sexp(printed)
        assert reparsed == parsed

    def test_roundtrip_simple_list(self):
        original = "(foo bar baz)"
        parsed = parse_sexp(original)
        printed = compact_print(parsed)
        reparsed = parse_sexp(printed)
        assert reparsed == parsed

    def test_roundtrip_nested_list(self):
        original = "(define (square x) (* x x))"
        parsed = parse_sexp(original)
        printed = compact_print(parsed)
        reparsed = parse_sexp(printed)
        assert reparsed == parsed

    def test_roundtrip_complex_expression(self):
        original = """
        (rule value (Message logic Value)
          "missing"
          (lambda () (call (message logic Value) (call (oneof missing_value) (call (message logic MissingValue))))))
        """
        parsed = parse_sexp(original)
        printed = compact_print(parsed)
        reparsed = parse_sexp(printed)
        assert reparsed == parsed

    def test_roundtrip_with_pretty_print(self):
        original = "(define (factorial n) (if (= n 0) 1 (* n (factorial (- n 1)))))"
        parsed = parse_sexp(original)
        printed = pretty_print(parsed, width=80)
        reparsed = parse_sexp(printed)
        assert reparsed == parsed

    def test_roundtrip_boolean_true(self):
        original = "true"
        parsed = parse_sexp(original)
        printed = compact_print(parsed)
        reparsed = parse_sexp(printed)
        assert reparsed == parsed

    def test_roundtrip_boolean_false(self):
        original = "false"
        parsed = parse_sexp(original)
        printed = compact_print(parsed)
        reparsed = parse_sexp(printed)
        assert reparsed == parsed

    def test_roundtrip_mixed_types(self):
        original = '(foo 42 3.14 true "hello")'
        parsed = parse_sexp(original)
        printed = compact_print(parsed)
        reparsed = parse_sexp(printed)
        assert reparsed == parsed


class TestHelperFunctions:
    """Tests for helper constructor functions."""

    def test_symbol_creates_unquoted_atom(self):
        result = symbol("foo")
        assert result == SAtom("foo")
        assert not result.quoted

    def test_string_creates_quoted_atom(self):
        result = string("hello")
        assert result == SAtom("hello", quoted=True)
        assert result.quoted

    def test_atom_default_unquoted(self):
        result = atom("foo")
        assert result == SAtom("foo")
        assert not result.quoted

    def test_atom_explicit_quoted(self):
        result = atom("foo", quoted=True)
        assert result == SAtom("foo", quoted=True)
        assert result.quoted

    def test_slist_from_args(self):
        result = slist(symbol("a"), symbol("b"), symbol("c"))
        assert result == SList((SAtom("a"), SAtom("b"), SAtom("c")))

    def test_slist_empty(self):
        result = slist()
        assert result == SList(())
