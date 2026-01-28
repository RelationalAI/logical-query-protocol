"""Tests for the s-expression parser."""

import pytest

from meta.sexp import SAtom, SList
from meta.sexp_parser import parse_sexp, parse_sexp_file, ParseError, SExprParser


class TestParseAtoms:
    """Tests for parsing atomic s-expressions."""

    def test_parse_symbol(self):
        result = parse_sexp("foo")
        assert result == SAtom("foo")
        assert isinstance(result, SAtom) and not result.quoted

    def test_parse_symbol_with_special_chars(self):
        result = parse_sexp("foo-bar")
        assert result == SAtom("foo-bar")

    def test_parse_symbol_with_underscores(self):
        result = parse_sexp("foo_bar_baz")
        assert result == SAtom("foo_bar_baz")

    def test_parse_symbol_with_numbers(self):
        result = parse_sexp("var123")
        assert result == SAtom("var123")

    def test_parse_operator_symbol(self):
        result = parse_sexp("+")
        assert result == SAtom("+")

    def test_parse_comparison_operator(self):
        result = parse_sexp("<=")
        assert result == SAtom("<=")

    def test_parse_integer_positive(self):
        result = parse_sexp("42")
        assert result == SAtom(42)
        assert isinstance(result, SAtom) and isinstance(result.value, int)

    def test_parse_integer_negative(self):
        result = parse_sexp("-17")
        assert result == SAtom(-17)

    def test_parse_integer_zero(self):
        result = parse_sexp("0")
        assert result == SAtom(0)

    def test_parse_float_simple(self):
        result = parse_sexp("3.14")
        assert result == SAtom(3.14)
        assert isinstance(result, SAtom) and isinstance(result.value, float)

    def test_parse_float_negative(self):
        result = parse_sexp("-2.5")
        assert result == SAtom(-2.5)

    def test_parse_float_scientific(self):
        result = parse_sexp("1e10")
        assert result == SAtom(1e10)

    def test_parse_float_scientific_negative_exp(self):
        result = parse_sexp("1.5e-3")
        assert result == SAtom(1.5e-3)

    def test_parse_boolean_true(self):
        # true is parsed as a symbol, not a boolean
        result = parse_sexp("true")
        assert result == SAtom("true")
        assert isinstance(result, SAtom) and result.value == "true"

    def test_parse_boolean_false(self):
        # false is parsed as a symbol, not a boolean
        result = parse_sexp("false")
        assert result == SAtom("false")
        assert isinstance(result, SAtom) and result.value == "false"

    def test_parse_string_simple(self):
        result = parse_sexp('"hello"')
        assert result == SAtom("hello", quoted=True)
        assert isinstance(result, SAtom) and result.quoted

    def test_parse_string_with_spaces(self):
        result = parse_sexp('"hello world"')
        assert result == SAtom("hello world", quoted=True)

    def test_parse_string_empty(self):
        result = parse_sexp('""')
        assert result == SAtom("", quoted=True)

    def test_parse_string_with_escaped_quote(self):
        result = parse_sexp(r'"say \"hello\""')
        assert result == SAtom('say "hello"', quoted=True)

    def test_parse_string_with_escaped_backslash(self):
        result = parse_sexp(r'"path\\to\\file"')
        assert result == SAtom('path\\to\\file', quoted=True)

    def test_parse_string_with_newline(self):
        result = parse_sexp(r'"line1\nline2"')
        assert result == SAtom('line1\nline2', quoted=True)

    def test_parse_string_with_tab(self):
        result = parse_sexp(r'"col1\tcol2"')
        assert result == SAtom('col1\tcol2', quoted=True)


class TestParseLists:
    """Tests for parsing list s-expressions."""

    def test_parse_empty_list(self):
        result = parse_sexp("()")
        assert result == SList(())
        assert isinstance(result, SList) and len(result) == 0

    def test_parse_single_element_list(self):
        result = parse_sexp("(foo)")
        assert result == SList((SAtom("foo"),))

    def test_parse_multiple_elements(self):
        result = parse_sexp("(foo bar baz)")
        assert result == SList((SAtom("foo"), SAtom("bar"), SAtom("baz")))

    def test_parse_mixed_types(self):
        result = parse_sexp('(foo 42 "hello")')
        assert result == SList((SAtom("foo"), SAtom(42), SAtom("hello", quoted=True)))

    def test_parse_nested_list(self):
        result = parse_sexp("(foo (bar baz))")
        assert result == SList((SAtom("foo"), SList((SAtom("bar"), SAtom("baz")))))

    def test_parse_deeply_nested(self):
        result = parse_sexp("(a (b (c (d))))")
        expected = SList((
            SAtom("a"),
            SList((
                SAtom("b"),
                SList((
                    SAtom("c"),
                    SList((SAtom("d"),))
                ))
            ))
        ))
        assert result == expected

    def test_parse_list_with_operators(self):
        result = parse_sexp("(+ 1 2)")
        assert result == SList((SAtom("+"), SAtom(1), SAtom(2)))

    def test_parse_complex_expression(self):
        result = parse_sexp("(define (square x) (* x x))")
        expected = SList((
            SAtom("define"),
            SList((SAtom("square"), SAtom("x"))),
            SList((SAtom("*"), SAtom("x"), SAtom("x")))
        ))
        assert result == expected


class TestWhitespaceHandling:
    """Tests for whitespace handling."""

    def test_leading_whitespace(self):
        result = parse_sexp("   foo")
        assert result == SAtom("foo")

    def test_trailing_whitespace(self):
        result = parse_sexp("foo   ")
        assert result == SAtom("foo")

    def test_whitespace_in_list(self):
        result = parse_sexp("(  foo   bar  )")
        assert result == SList((SAtom("foo"), SAtom("bar")))

    def test_newlines_in_list(self):
        result = parse_sexp("(\n  foo\n  bar\n)")
        assert result == SList((SAtom("foo"), SAtom("bar")))

    def test_tabs_in_list(self):
        result = parse_sexp("(\tfoo\tbar\t)")
        assert result == SList((SAtom("foo"), SAtom("bar")))

    def test_multiline_expression(self):
        text = """
        (rule value String
          "missing"
          (lambda () (lit true)))
        """
        result = parse_sexp(text)
        assert isinstance(result, SList)
        assert result[0] == SAtom("rule")


class TestComments:
    """Tests for comment handling."""

    def test_comment_at_start(self):
        result = parse_sexp("; comment\nfoo")
        assert result == SAtom("foo")

    def test_comment_at_end(self):
        result = parse_sexp("foo ; comment")
        assert result == SAtom("foo")

    def test_comment_in_list(self):
        result = parse_sexp("(foo ; comment\n bar)")
        assert result == SList((SAtom("foo"), SAtom("bar")))

    def test_multiple_comments(self):
        text = """
        ; First comment
        (foo ; inline comment
         ; another comment
         bar)
        ; trailing comment
        """
        result = parse_sexp(text)
        assert result == SList((SAtom("foo"), SAtom("bar")))

    def test_comment_only_lines(self):
        text = """
        ; comment 1
        ; comment 2
        foo
        ; comment 3
        """
        result = parse_sexp(text)
        assert result == SAtom("foo")


class TestParseFile:
    """Tests for parsing multiple s-expressions."""

    def test_parse_empty_file(self):
        result = parse_sexp_file("")
        assert result == []

    def test_parse_single_expression(self):
        result = parse_sexp_file("foo")
        assert result == [SAtom("foo")]

    def test_parse_multiple_expressions(self):
        result = parse_sexp_file("foo bar baz")
        assert result == [SAtom("foo"), SAtom("bar"), SAtom("baz")]

    def test_parse_multiple_lists(self):
        result = parse_sexp_file("(foo) (bar) (baz)")
        assert result == [
            SList((SAtom("foo"),)),
            SList((SAtom("bar"),)),
            SList((SAtom("baz"),))
        ]

    def test_parse_file_with_comments(self):
        text = """
        ; header comment
        (rule1)
        ; middle comment
        (rule2)
        ; footer comment
        """
        result = parse_sexp_file(text)
        assert len(result) == 2
        assert result[0] == SList((SAtom("rule1"),))
        assert result[1] == SList((SAtom("rule2"),))

    def test_parse_file_mixed_content(self):
        text = """
        (define x 10)
        (define y 20)
        (+ x y)
        """
        result = parse_sexp_file(text)
        assert len(result) == 3


class TestParseErrors:
    """Tests for parse error handling."""

    def test_empty_input_error(self):
        with pytest.raises(ParseError) as exc_info:
            parse_sexp("")
        assert "end of input" in str(exc_info.value).lower()

    def test_unclosed_list(self):
        with pytest.raises(ParseError) as exc_info:
            parse_sexp("(foo bar")
        assert ")" in str(exc_info.value)

    def test_extra_close_paren(self):
        # parse_sexp just returns the first expression and ignores trailing content
        result = parse_sexp("foo)")
        assert result == SAtom("foo")

    def test_unterminated_string(self):
        with pytest.raises(ParseError) as exc_info:
            parse_sexp('"hello')
        assert "unterminated" in str(exc_info.value).lower()

    def test_error_line_tracking(self):
        with pytest.raises(ParseError) as exc_info:
            parse_sexp("(\n\n\n\"unclosed")
        error = exc_info.value
        assert error.line == 4

    def test_unexpected_character(self):
        # A lone close paren at the start
        parser = SExprParser(")")
        with pytest.raises(ParseError):
            parser.parse()


class TestSListMethods:
    """Tests for SList helper methods."""

    def test_head_nonempty(self):
        slist = SList((SAtom("a"), SAtom("b"), SAtom("c")))
        assert slist.head() == SAtom("a")

    def test_head_empty(self):
        slist = SList(())
        assert slist.head() is None

    def test_tail_nonempty(self):
        slist = SList((SAtom("a"), SAtom("b"), SAtom("c")))
        assert slist.tail() == SList((SAtom("b"), SAtom("c")))

    def test_tail_single(self):
        slist = SList((SAtom("a"),))
        assert slist.tail() == SList(())

    def test_is_tagged_true(self):
        slist = SList((SAtom("rule"), SAtom("x")))
        assert slist.is_tagged("rule")

    def test_is_tagged_false_different_tag(self):
        slist = SList((SAtom("rule"), SAtom("x")))
        assert not slist.is_tagged("define")

    def test_is_tagged_false_empty(self):
        slist = SList(())
        assert not slist.is_tagged("rule")

    def test_is_tagged_false_not_symbol(self):
        slist = SList((SAtom(42), SAtom("x")))
        assert not slist.is_tagged("42")

    def test_indexing(self):
        slist = SList((SAtom("a"), SAtom("b"), SAtom("c")))
        assert slist[0] == SAtom("a")
        assert slist[1] == SAtom("b")
        assert slist[2] == SAtom("c")

    def test_iteration(self):
        slist = SList((SAtom("a"), SAtom("b"), SAtom("c")))
        assert list(slist) == [SAtom("a"), SAtom("b"), SAtom("c")]


class TestSAtomMethods:
    """Tests for SAtom helper methods."""

    def test_is_symbol_true(self):
        atom = SAtom("foo")
        assert atom.is_symbol("foo")

    def test_is_symbol_false_different_name(self):
        atom = SAtom("foo")
        assert not atom.is_symbol("bar")

    def test_is_symbol_false_quoted(self):
        atom = SAtom("foo", quoted=True)
        assert not atom.is_symbol("foo")

    def test_is_symbol_false_number(self):
        atom = SAtom(42)
        assert not atom.is_symbol("42")

    def test_str_symbol(self):
        atom = SAtom("foo")
        assert str(atom) == "foo"

    def test_str_quoted(self):
        atom = SAtom("hello", quoted=True)
        assert str(atom) == '"hello"'

    def test_str_int(self):
        atom = SAtom(42)
        assert str(atom) == "42"

    def test_str_float(self):
        atom = SAtom(3.14)
        assert str(atom) == "3.14"

    def test_str_bool_true(self):
        atom = SAtom(True)
        assert str(atom) == "true"

    def test_str_bool_false(self):
        atom = SAtom(False)
        assert str(atom) == "false"
