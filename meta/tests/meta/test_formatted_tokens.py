#!/usr/bin/env python3
"""Tests for formatted tokens and token aliases.

Token aliases (e.g., FORMATTED_INT aliasing INT) allow the grammar to
distinguish between literal values that should go through a formatting hook
(formatted tokens, used in formula fragments) and those that should be printed
directly (raw tokens, used in config relations and attributes).

For parsing, aliases behave identically to their base token.
For pretty-printing, they dispatch to different format builtins.
"""

from textwrap import dedent

import pytest

from meta.codegen_base import PRINTER_CONFIG
from meta.codegen_julia import JuliaCodeGenerator
from meta.codegen_python import PythonCodeGenerator
from meta.gensym import reset as reset_gensym
from meta.grammar import Grammar, NamedTerminal
from meta.pretty_gen import _format_terminal, generate_pretty_functions
from meta.target import BaseType, Builtin, Call, MessageType, TargetExpr, Var
from meta.target_builtins import make_builtin
from meta.target_visitor import TargetExprVisitor
from meta.yacc_action_parser import YaccGrammarError
from meta.yacc_parser import load_yacc_grammar

# ---------------------------------------------------------------------------
# Yacc parser: %token_alias directive
# ---------------------------------------------------------------------------


class TestTokenAliasDirectiveParsing:
    """Tests for parsing %token_alias directives."""

    def test_basic_alias(self):
        """A token alias inherits the type of its base token."""
        config = load_yacc_grammar(
            dedent("""\
            %token INT Int64 r'[0-9]+'
            %token_alias FORMATTED_INT INT
            %nonterm start Int64
            %start start
            %%
            start
                : INT
            %%
        """)
        )
        assert "FORMATTED_INT" in config.terminals
        assert config.terminals["FORMATTED_INT"] == config.terminals["INT"]
        assert config.token_aliases == {"FORMATTED_INT": "INT"}

    def test_multiple_aliases(self):
        """Multiple aliases can reference different base tokens."""
        config = load_yacc_grammar(
            dedent("""\
            %token INT Int64 r'[0-9]+'
            %token STRING String r'"[^"]*"'
            %token_alias FORMATTED_INT INT
            %token_alias FORMATTED_STRING STRING
            %nonterm start Int64
            %start start
            %%
            start
                : INT
            %%
        """)
        )
        assert config.token_aliases == {
            "FORMATTED_INT": "INT",
            "FORMATTED_STRING": "STRING",
        }
        assert config.terminals["FORMATTED_INT"] == BaseType("Int64")
        assert config.terminals["FORMATTED_STRING"] == BaseType("String")

    def test_alias_unknown_base_raises(self):
        """Aliasing a non-existent base token is an error."""
        with pytest.raises(YaccGrammarError, match="not a declared %token"):
            load_yacc_grammar(
                dedent("""\
                %token INT Int64 r'[0-9]+'
                %token_alias FORMATTED_FLOAT FLOAT
                %nonterm start Int64
                %start start
                %%
                start
                    : INT
                %%
            """)
            )

    def test_alias_duplicate_name_raises(self):
        """An alias name that collides with an existing token is an error."""
        with pytest.raises(YaccGrammarError, match="Duplicate token"):
            load_yacc_grammar(
                dedent("""\
                %token INT Int64 r'[0-9]+'
                %token_alias INT INT
                %nonterm start Int64
                %start start
                %%
                start
                    : INT
                %%
            """)
            )


# ---------------------------------------------------------------------------
# Grammar: aliases usable in rules
# ---------------------------------------------------------------------------


class TestTokenAliasInRules:
    """Token aliases can be used in grammar rules just like regular tokens."""

    def test_alias_in_rhs(self):
        """An alias token can appear on the RHS of a rule."""
        config = load_yacc_grammar(
            dedent("""\
            %token INT Int64 r'[0-9]+'
            %token_alias FORMATTED_INT INT
            %nonterm start Int64
            %start start
            %%
            start
                : FORMATTED_INT
            %%
        """)
        )
        rules = list(config.rules.values())
        assert len(rules) == 1
        rule = rules[0][0]
        assert isinstance(rule.rhs, NamedTerminal)
        assert rule.rhs.name == "FORMATTED_INT"
        assert rule.rhs.type == BaseType("Int64")

    def test_alias_and_base_in_different_rules(self):
        """Both a base token and its alias can appear in separate rules."""
        config = load_yacc_grammar(
            dedent("""\
            %token INT Int64 r'[0-9]+'
            %token STRING String r'"[^"]*"'
            %token_alias FORMATTED_INT INT
            %token_alias FORMATTED_STRING STRING
            %nonterm value test.Value
            %nonterm raw_value test.Value
            %nonterm start test.Value
            %start start
            %%
            start
                : value

            value
                : FORMATTED_INT
                  construct: $$ = test.Value(int_value=$1)
                  deconstruct:
                    $1: Int64 = $$.int_value
                | FORMATTED_STRING
                  construct: $$ = test.Value(string_value=$1)
                  deconstruct:
                    $1: String = $$.string_value

            raw_value
                : INT
                  construct: $$ = test.Value(int_value=$1)
                  deconstruct:
                    $1: Int64 = $$.int_value
                | STRING
                  construct: $$ = test.Value(string_value=$1)
                  deconstruct:
                    $1: String = $$.string_value
            %%
        """)
        )
        value_rules = None
        raw_value_rules = None
        for nt, rules in config.rules.items():
            if nt.name == "value":
                value_rules = rules
            elif nt.name == "raw_value":
                raw_value_rules = rules

        assert value_rules is not None
        assert raw_value_rules is not None

        # value rules use FORMATTED_* tokens
        value_token_names = []
        for rule in value_rules:
            assert isinstance(rule.rhs, NamedTerminal)
            value_token_names.append(rule.rhs.name)
        assert "FORMATTED_INT" in value_token_names
        assert "FORMATTED_STRING" in value_token_names

        # raw_value rules use base tokens
        raw_token_names = []
        for rule in raw_value_rules:
            assert isinstance(rule.rhs, NamedTerminal)
            raw_token_names.append(rule.rhs.name)
        assert "INT" in raw_token_names
        assert "STRING" in raw_token_names


# ---------------------------------------------------------------------------
# Pretty-gen IR: formatted vs unformatted builtins
# ---------------------------------------------------------------------------


def _get_format_builtin_name(
    terminal_name: str, terminal_type: BaseType | MessageType
) -> str:
    """Get the builtin name used by _format_terminal for a given terminal."""
    terminal = NamedTerminal(terminal_name, terminal_type)
    var = Var("v", terminal_type)
    result = _format_terminal(terminal, var)
    assert isinstance(result, Call)
    assert isinstance(result.func, Builtin)
    return result.func.name


class TestPrettyGenFormattedTerminals:
    """Formatted terminals dispatch to _formatted builtins in the pretty-printer IR."""

    @pytest.mark.parametrize(
        "base,formatted,type_name",
        [
            ("INT", "FORMATTED_INT", "Int64"),
            ("STRING", "FORMATTED_STRING", "String"),
            ("FLOAT", "FORMATTED_FLOAT", "Float64"),
            ("INT32", "FORMATTED_INT32", "Int32"),
            ("FLOAT32", "FORMATTED_FLOAT32", "Float32"),
            ("DECIMAL", "FORMATTED_DECIMAL", "DecimalValue"),
            ("INT128", "FORMATTED_INT128", "Int128Value"),
            ("UINT128", "FORMATTED_UINT128", "UInt128Value"),
        ],
    )
    def test_formatted_uses_different_builtin(self, base, formatted, type_name):
        """Formatted token dispatches to a different builtin than the base token."""
        if type_name in ("DecimalValue", "Int128Value", "UInt128Value"):
            tp = MessageType("logic", type_name)
        else:
            tp = BaseType(type_name)
        base_builtin = _get_format_builtin_name(base, tp)
        formatted_builtin = _get_format_builtin_name(formatted, tp)
        assert base_builtin != formatted_builtin
        assert formatted_builtin.endswith("_formatted")
        assert not base_builtin.endswith("_formatted")

    @pytest.mark.parametrize(
        "token_name,expected_builtin",
        [
            ("INT", "format_int64"),
            ("FORMATTED_INT", "format_int64_formatted"),
            ("STRING", "format_string"),
            ("FORMATTED_STRING", "format_string_formatted"),
            ("FLOAT", "format_float64"),
            ("FORMATTED_FLOAT", "format_float64_formatted"),
        ],
    )
    def test_specific_builtin_names(self, token_name, expected_builtin):
        """Each token maps to the expected builtin name."""
        tp = BaseType("String")  # type doesn't matter for the lookup
        actual = _get_format_builtin_name(token_name, tp)
        assert actual == expected_builtin


# ---------------------------------------------------------------------------
# Codegen: Julia formatted builtins go through constant_formatter hook
# ---------------------------------------------------------------------------


class TestJuliaFormattedCodegen:
    """In Julia, formatted builtins go through pp.constant_formatter,
    while unformatted builtins either use string() directly or
    DEFAULT_CONSTANT_FORMATTER."""

    def _gen_julia(self, builtin_name: str, arg: str = "v") -> str:
        gen = JuliaCodeGenerator(config=PRINTER_CONFIG)
        reset_gensym()
        lines = []
        expr = Call(make_builtin(builtin_name), [Var(arg, BaseType("Any"))])
        result = gen.generate_lines(expr, lines, "")
        assert result is not None
        return result

    def test_format_int64_unformatted_is_direct(self):
        """Unformatted int64 uses string() directly, no hook."""
        result = self._gen_julia("format_int64")
        assert result == "string(v)"

    def test_format_int64_formatted_uses_hook(self):
        """Formatted int64 goes through format_int(pp, v)."""
        result = self._gen_julia("format_int64_formatted")
        assert result == "format_int(pp, v)"

    def test_format_string_unformatted_uses_default_formatter(self):
        """Unformatted string uses DEFAULT_CONSTANT_FORMATTER explicitly."""
        result = self._gen_julia("format_string")
        assert "DEFAULT_CONSTANT_FORMATTER" in result
        assert "pp" in result

    def test_format_string_formatted_uses_hook(self):
        """Formatted string goes through format_string(pp, v)."""
        result = self._gen_julia("format_string_formatted")
        assert result == "format_string(pp, v)"
        assert "DEFAULT_CONSTANT_FORMATTER" not in result

    def test_format_float64_unformatted_is_direct(self):
        """Unformatted float64 uses lowercase(string(v)) directly."""
        result = self._gen_julia("format_float64")
        assert result == "lowercase(string(v))"

    def test_format_float64_formatted_uses_hook(self):
        """Formatted float64 goes through format_float(pp, v)."""
        result = self._gen_julia("format_float64_formatted")
        assert result == "format_float(pp, v)"


class TestPythonFormattedCodegen:
    """In Python, formatted builtins produce the same output as unformatted."""

    def _gen_python(self, builtin_name: str, arg: str = "v") -> str:
        gen = PythonCodeGenerator()
        reset_gensym()
        lines = []
        expr = Call(make_builtin(builtin_name), [Var(arg, BaseType("Any"))])
        result = gen.generate_lines(expr, lines, "")
        assert result is not None
        return result

    def test_format_int64_same(self):
        """Python formatted and unformatted int64 produce the same code."""
        assert self._gen_python("format_int64") == self._gen_python(
            "format_int64_formatted"
        )

    def test_format_string_same(self):
        """Python formatted and unformatted string produce the same code."""
        assert self._gen_python("format_string") == self._gen_python(
            "format_string_formatted"
        )


# ---------------------------------------------------------------------------
# End-to-end: pretty-gen with a grammar containing both value and raw_value
# ---------------------------------------------------------------------------


def _build_grammar(text):
    """Parse a grammar string and build a Grammar object."""
    config = load_yacc_grammar(dedent(text).lstrip())
    start = None
    for nt in config.rules:
        if nt.name == config.start_symbol:
            start = nt
            break
    assert start is not None
    grammar = Grammar(
        start=start,
        function_defs=config.function_defs,
        token_aliases=config.token_aliases,
    )
    for rules in config.rules.values():
        for rule in rules:
            grammar.add_rule(rule)
    return grammar


class _BuiltinCollector(TargetExprVisitor):
    """Collect builtin call names from a target IR tree."""

    def __init__(self):
        super().__init__()
        self.names: set[str] = set()

    def visit_Call(self, expr: Call) -> None:
        if isinstance(expr.func, Builtin):
            self.names.add(expr.func.name)
        self.visit_children(expr)


def _collect_builtin_names(expr: TargetExpr) -> set[str]:
    """Collect all Builtin names from an IR tree."""
    collector = _BuiltinCollector()
    collector.visit(expr)
    return collector.names


class TestPrettyGenEndToEnd:
    """Generate pretty-printer IR for a grammar with both formatted and raw
    value nonterminals, and verify the correct builtins are used."""

    GRAMMAR = """\
        %token INT Int64 r'[0-9]+'
        %token STRING String r'"[^"]*"'
        %token_alias FORMATTED_INT INT
        %token_alias FORMATTED_STRING STRING
        %nonterm value test.Value
        %nonterm raw_value test.Value
        %nonterm start test.Start
        %start start
        %%
        start
            : "(" "start" value raw_value ")"
              construct: $$ = test.Start(value=$3, raw_value=$4)
              deconstruct:
                $3: test.Value = $$.value
                $4: test.Value = $$.raw_value

        value
            : FORMATTED_INT
              construct: $$ = test.Value(int_value=$1)
              deconstruct:
                $1: Int64 = $$.int_value
            | FORMATTED_STRING
              construct: $$ = test.Value(string_value=$1)
              deconstruct:
                $1: String = $$.string_value

        raw_value
            : INT
              construct: $$ = test.Value(int_value=$1)
              deconstruct:
                $1: Int64 = $$.int_value
            | STRING
              construct: $$ = test.Value(string_value=$1)
              deconstruct:
                $1: String = $$.string_value
        %%
    """

    def test_value_uses_formatted_builtins(self):
        """The 'value' nonterminal should use format_*_formatted builtins."""
        grammar = _build_grammar(self.GRAMMAR)
        defs = generate_pretty_functions(grammar)
        value_def = [d for d in defs if d.nonterminal.name == "value"]
        assert len(value_def) == 1
        builtins = _collect_builtin_names(value_def[0].body)
        format_builtins = {b for b in builtins if b.startswith("format_")}
        assert any(b.endswith("_formatted") for b in format_builtins), (
            f"Expected _formatted builtins in value, got: {format_builtins}"
        )

    def test_raw_value_uses_unformatted_builtins(self):
        """The 'raw_value' nonterminal should use base (unformatted) builtins."""
        grammar = _build_grammar(self.GRAMMAR)
        defs = generate_pretty_functions(grammar)
        raw_def = [d for d in defs if d.nonterminal.name == "raw_value"]
        assert len(raw_def) == 1
        builtins = _collect_builtin_names(raw_def[0].body)
        format_builtins = {b for b in builtins if b.startswith("format_")}
        assert not any(b.endswith("_formatted") for b in format_builtins), (
            f"Expected no _formatted builtins in raw_value, got: {format_builtins}"
        )
