#!/usr/bin/env python3
"""Tests for grammar analysis functions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.grammar import (
    Grammar,
    LitTerminal,
    NamedTerminal,
    Nonterminal,
    Option,
    Rule,
    Sequence,
    Star,
)
from meta.grammar_analysis import GrammarAnalysis
from meta.target import BaseType, Lambda, MessageType, Var


def _rule(lhs, *rhs_symbols):
    """Build a Rule with a dummy constructor for analysis tests.

    The constructor body is irrelevant for grammar analysis (FIRST, FOLLOW,
    nullable, etc.), so this helper auto-generates a minimal Lambda.
    """
    params = []
    for i, sym in enumerate(rhs_symbols):
        if isinstance(sym, (Nonterminal, NamedTerminal)):
            params.append(Var(f"p{i}", sym.type))
    body = params[0] if params else Var("_", lhs.type)
    constructor = Lambda(params, lhs.type, body)

    if len(rhs_symbols) == 0:
        rhs = Sequence(())
    elif len(rhs_symbols) == 1:
        rhs = rhs_symbols[0]
    else:
        rhs = Sequence(tuple(rhs_symbols))

    return Rule(lhs, rhs, constructor)


_str_type = BaseType("String")


def _tokenize_rhs(text):
    """Split an RHS string into tokens, handling quoted strings."""
    tokens = []
    i = 0
    while i < len(text):
        if text[i].isspace():
            i += 1
        elif text[i] == '"':
            j = text.index('"', i + 1)
            tokens.append(text[i : j + 1])
            i = j + 1
        else:
            j = i
            while j < len(text) and not text[j].isspace():
                j += 1
            tokens.append(text[i:j])
            i = j
    return tokens


def _grammar(text):
    """Parse a BNF grammar for analysis tests.

    Nonterminals: words appearing on the left of ->.
    Named terminals: non-quoted words that are not nonterminals.
    Literal terminals: quoted strings.
    Epsilon: 'eps' as the sole symbol of an alternative.
    All types default to BaseType("String").

    Returns (Grammar, nonterminals dict, named terminals dict).
    """
    lines = [ln.strip() for ln in text.strip().split("\n") if ln.strip()]

    nt_names = set()
    for line in lines:
        lhs, _ = line.split("->", 1)
        nt_names.add(lhs.strip())

    nts = {name: Nonterminal(name, _str_type) for name in nt_names}
    named_terms = {}
    all_rules = []
    start = None

    for line in lines:
        lhs_str, rhs_str = line.split("->", 1)
        lhs = nts[lhs_str.strip()]
        if start is None:
            start = lhs

        for alt in rhs_str.split("|"):
            alt = alt.strip()
            if alt == "eps":
                all_rules.append(_rule(lhs))
                continue

            symbols = []
            for tok in _tokenize_rhs(alt):
                if tok.startswith('"') and tok.endswith('"'):
                    symbols.append(LitTerminal(tok[1:-1]))
                elif tok in nts:
                    symbols.append(nts[tok])
                else:
                    if tok not in named_terms:
                        named_terms[tok] = NamedTerminal(tok, _str_type)
                    symbols.append(named_terms[tok])

            all_rules.append(_rule(lhs, *symbols))

    assert start is not None, "Grammar must have at least one rule"
    grammar = Grammar(start)
    for rule in all_rules:
        grammar.add_rule(rule)

    return grammar, nts, named_terms


def make_simple_grammar():
    """Create a simple test grammar.

    S -> A B
    A -> "a"
    B -> "b"
    """
    s = Nonterminal("S", MessageType("proto", "S"))
    a = Nonterminal("A", MessageType("proto", "A"))
    b = Nonterminal("B", MessageType("proto", "B"))
    lit_a = LitTerminal("a")
    lit_b = LitTerminal("b")

    grammar = Grammar(s)

    # S -> A B
    param_a = Var("x", MessageType("proto", "A"))
    param_b = Var("y", MessageType("proto", "B"))
    constructor_s = Lambda([param_a, param_b], MessageType("proto", "S"), param_a)
    grammar.add_rule(Rule(s, Sequence((a, b)), constructor_s))

    # A -> "a"
    constructor_a = Lambda(
        [], MessageType("proto", "A"), Var("x", MessageType("proto", "A"))
    )
    grammar.add_rule(Rule(a, lit_a, constructor_a))

    # B -> "b"
    constructor_b = Lambda(
        [], MessageType("proto", "B"), Var("y", MessageType("proto", "B"))
    )
    grammar.add_rule(Rule(b, lit_b, constructor_b))

    return grammar, s, a, b, lit_a, lit_b


def make_nullable_grammar():
    """Create a grammar with nullable productions.

    S -> A B
    A -> "a" | epsilon
    B -> "b"
    """
    s = Nonterminal("S", MessageType("proto", "S"))
    a = Nonterminal("A", MessageType("proto", "A"))
    b = Nonterminal("B", MessageType("proto", "B"))
    lit_a = LitTerminal("a")
    lit_b = LitTerminal("b")

    grammar = Grammar(s)

    # S -> A B
    param_a = Var("x", MessageType("proto", "A"))
    param_b = Var("y", MessageType("proto", "B"))
    constructor_s = Lambda([param_a, param_b], MessageType("proto", "S"), param_a)
    grammar.add_rule(Rule(s, Sequence((a, b)), constructor_s))

    # A -> "a"
    constructor_a1 = Lambda(
        [], MessageType("proto", "A"), Var("x", MessageType("proto", "A"))
    )
    grammar.add_rule(Rule(a, lit_a, constructor_a1))

    # A -> epsilon
    constructor_a2 = Lambda(
        [], MessageType("proto", "A"), Var("x", MessageType("proto", "A"))
    )
    grammar.add_rule(Rule(a, Sequence(()), constructor_a2))

    # B -> "b"
    constructor_b = Lambda(
        [], MessageType("proto", "B"), Var("y", MessageType("proto", "B"))
    )
    grammar.add_rule(Rule(b, lit_b, constructor_b))

    return grammar, s, a, b


def make_left_recursive_grammar():
    """Create a left-recursive grammar.

    S -> S "+" T | T
    T -> "num"
    """
    s = Nonterminal("S", MessageType("proto", "S"))
    t = Nonterminal("T", MessageType("proto", "T"))
    plus = LitTerminal("+")
    num = NamedTerminal("NUM", BaseType("Int64"))

    grammar = Grammar(s)

    # S -> S "+" T
    param_s = Var("x", MessageType("proto", "S"))
    param_t1 = Var("y", MessageType("proto", "T"))
    constructor_s1 = Lambda([param_s, param_t1], MessageType("proto", "S"), param_s)
    grammar.add_rule(Rule(s, Sequence((s, plus, t)), constructor_s1))

    # S -> T
    param_t2 = Var("z", MessageType("proto", "T"))
    constructor_s2 = Lambda([param_t2], MessageType("proto", "S"), param_t2)
    grammar.add_rule(Rule(s, t, constructor_s2))

    # T -> NUM
    param_num = Var("n", BaseType("Int64"))
    constructor_t = Lambda([param_num], MessageType("proto", "T"), param_num)
    grammar.add_rule(Rule(t, num, constructor_t))

    return grammar, s, t, num


def make_unreachable_grammar():
    """Create a grammar with unreachable nonterminals.

    S -> A
    A -> "a"
    B -> "b"  (unreachable)
    """
    s = Nonterminal("S", MessageType("proto", "S"))
    a = Nonterminal("A", MessageType("proto", "A"))
    b = Nonterminal("B", MessageType("proto", "B"))
    lit_a = LitTerminal("a")
    lit_b = LitTerminal("b")

    grammar = Grammar(s)

    # S -> A
    param_a = Var("x", MessageType("proto", "A"))
    constructor_s = Lambda([param_a], MessageType("proto", "S"), param_a)
    grammar.add_rule(Rule(s, a, constructor_s))

    # A -> "a"
    constructor_a = Lambda(
        [], MessageType("proto", "A"), Var("y", MessageType("proto", "A"))
    )
    grammar.add_rule(Rule(a, lit_a, constructor_a))

    # B -> "b" (unreachable)
    constructor_b = Lambda(
        [], MessageType("proto", "B"), Var("z", MessageType("proto", "B"))
    )
    grammar.add_rule(Rule(b, lit_b, constructor_b))

    return grammar, s, a, b


class TestCheckReachability:
    """Tests for check_reachability."""

    def test_simple_grammar_all_reachable(self):
        """Test reachability in simple grammar where all nonterminals are reachable."""
        grammar, s, a, b, _, _ = make_simple_grammar()
        reachable = grammar.analysis.reachability
        assert s in reachable
        assert a in reachable
        assert b in reachable
        assert len(reachable) == 3

    def test_unreachable_nonterminal(self):
        """Test reachability with unreachable nonterminal."""
        grammar, s, a, b = make_unreachable_grammar()
        reachable = grammar.analysis.reachability
        assert s in reachable
        assert a in reachable
        assert b not in reachable
        assert len(reachable) == 2

    def test_empty_grammar(self):
        """Test reachability with grammar that has no rules for start."""
        s = Nonterminal("S", MessageType("proto", "S"))
        grammar = Grammar(s)
        reachable = grammar.analysis.reachability
        # Start is always added to rules dict by Grammar constructor
        assert len(reachable) == 1
        assert s in reachable

    def test_single_rule(self):
        """Test reachability with single rule."""
        s = Nonterminal("S", MessageType("proto", "S"))
        lit = LitTerminal("a")
        grammar = Grammar(s)
        constructor = Lambda(
            [], MessageType("proto", "S"), Var("x", MessageType("proto", "S"))
        )
        grammar.add_rule(Rule(s, lit, constructor))
        reachable = grammar.analysis.reachability
        assert s in reachable
        assert len(reachable) == 1

    def test_indirect_reachability(self):
        """Test indirect reachability through multiple nonterminals."""
        s = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        c = Nonterminal("C", MessageType("proto", "C"))

        grammar = Grammar(s)

        # S -> A, A -> B, B -> C
        param_a = Var("x", MessageType("proto", "A"))
        param_b = Var("y", MessageType("proto", "B"))
        param_c = Var("z", MessageType("proto", "C"))
        constructor_s = Lambda([param_a], MessageType("proto", "S"), param_a)
        constructor_a = Lambda([param_b], MessageType("proto", "A"), param_b)
        constructor_b = Lambda([param_c], MessageType("proto", "B"), param_c)
        constructor_c = Lambda([param_c], MessageType("proto", "C"), param_c)

        grammar.add_rule(Rule(s, a, constructor_s))
        grammar.add_rule(Rule(a, b, constructor_a))
        grammar.add_rule(Rule(b, c, constructor_b))
        grammar.add_rule(Rule(c, c, constructor_c))

        reachable = grammar.analysis.reachability
        assert len(reachable) == 4
        assert s in reachable
        assert a in reachable
        assert b in reachable
        assert c in reachable


class TestComputeNullable:
    """Tests for compute_nullable."""

    def test_simple_grammar_no_nullable(self):
        """Test nullable computation with no nullable nonterminals."""
        grammar, s, a, b, _, _ = make_simple_grammar()
        nullable = grammar.analysis.nullable
        assert not nullable[s]
        assert not nullable[a]
        assert not nullable[b]

    def test_nullable_grammar(self):
        """Test nullable computation with nullable nonterminal."""
        grammar, s, a, b = make_nullable_grammar()
        nullable = grammar.analysis.nullable
        assert nullable[a]
        assert not nullable[b]
        assert not nullable[s]

    def test_star_makes_nullable(self):
        """Test that star makes sequence nullable."""
        s = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        star_a = Star(a)

        grammar = Grammar(s)
        param = Var("x", MessageType("proto", "S"))
        constructor = Lambda([param], MessageType("proto", "S"), param)
        grammar.add_rule(Rule(s, star_a, constructor))

        nullable = grammar.analysis.nullable
        assert nullable[s]

    def test_option_makes_nullable(self):
        """Test that option makes nonterminal nullable."""
        s = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        opt_a = Option(a)

        grammar = Grammar(s)
        param = Var("x", MessageType("proto", "S"))
        constructor = Lambda([param], MessageType("proto", "S"), param)
        grammar.add_rule(Rule(s, opt_a, constructor))

        nullable = grammar.analysis.nullable
        assert nullable[s]

    def test_empty_sequence_makes_nullable(self):
        """Test that empty sequence makes nonterminal nullable."""
        s = Nonterminal("S", MessageType("proto", "S"))
        grammar = Grammar(s)
        constructor = Lambda(
            [], MessageType("proto", "S"), Var("x", MessageType("proto", "S"))
        )
        grammar.add_rule(Rule(s, Sequence(()), constructor))

        nullable = grammar.analysis.nullable
        assert nullable[s]

    def test_transitive_nullable(self):
        """Test transitive nullable through multiple nonterminals."""
        s = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))

        grammar = Grammar(s)

        # S -> A, A -> B, B -> epsilon
        param_a = Var("x", MessageType("proto", "A"))
        param_b = Var("y", MessageType("proto", "B"))
        constructor_s = Lambda([param_a], MessageType("proto", "S"), param_a)
        constructor_a = Lambda([param_b], MessageType("proto", "A"), param_b)
        constructor_b = Lambda(
            [], MessageType("proto", "B"), Var("z", MessageType("proto", "B"))
        )

        grammar.add_rule(Rule(s, a, constructor_s))
        grammar.add_rule(Rule(a, b, constructor_a))
        grammar.add_rule(Rule(b, Sequence(()), constructor_b))

        nullable = grammar.analysis.nullable
        assert nullable[s]
        assert nullable[a]
        assert nullable[b]


class TestIsRhsElemNullable:
    """Tests for GrammarAnalysis.is_rhs_nullable."""

    def test_literal_not_nullable(self):
        """Test that literal is not nullable."""
        lit = LitTerminal("a")
        nullable = {}
        assert not GrammarAnalysis.is_rhs_nullable(lit, nullable)

    def test_terminal_not_nullable(self):
        """Test that terminal is not nullable."""
        term = NamedTerminal("TOK", BaseType("String"))
        nullable = {}
        assert not GrammarAnalysis.is_rhs_nullable(term, nullable)

    def test_nonterminal_nullable(self):
        """Test nonterminal nullable when in nullable set."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        nullable = {nt: True}
        assert GrammarAnalysis.is_rhs_nullable(nt, nullable)

    def test_nonterminal_not_nullable(self):
        """Test nonterminal not nullable when not in set."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        nullable = {nt: False}
        assert not GrammarAnalysis.is_rhs_nullable(nt, nullable)

    def test_star_nullable(self):
        """Test that star is always nullable."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        star = Star(nt)
        nullable = {nt: False}
        assert GrammarAnalysis.is_rhs_nullable(star, nullable)

    def test_option_nullable(self):
        """Test that option is always nullable."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        opt = Option(nt)
        nullable = {nt: False}
        assert GrammarAnalysis.is_rhs_nullable(opt, nullable)

    def test_empty_sequence_nullable(self):
        """Test that empty sequence is nullable."""
        seq = Sequence(())
        nullable = {}
        assert GrammarAnalysis.is_rhs_nullable(seq, nullable)

    def test_sequence_all_nullable(self):
        """Test sequence is nullable when all elements are nullable."""
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        seq = Sequence((a, b))
        nullable = {a: True, b: True}
        assert GrammarAnalysis.is_rhs_nullable(seq, nullable)

    def test_sequence_one_not_nullable(self):
        """Test sequence is not nullable when one element is not nullable."""
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        seq = Sequence((a, b))
        nullable = {a: True, b: False}
        assert not GrammarAnalysis.is_rhs_nullable(seq, nullable)


class TestComputeFirst:
    """Tests for compute_first."""

    def test_simple_grammar(self):
        """Test FIRST computation for simple grammar."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        first = grammar.analysis.first

        assert lit_a in first[a]
        assert lit_b in first[b]
        assert lit_a in first[s]

    def test_nullable_grammar(self):
        """Test FIRST with nullable nonterminal."""
        grammar, s, a, b = make_nullable_grammar()
        first = grammar.analysis.first

        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")

        # A can start with "a"
        assert lit_a in first[a]
        # B starts with "b"
        assert lit_b in first[b]
        # S can start with "a" or "b" (because A is nullable)
        assert lit_a in first[s]
        assert lit_b in first[s]

    def test_left_recursive_grammar(self):
        """Test FIRST with left recursion."""
        grammar, s, t, num = make_left_recursive_grammar()
        first = grammar.analysis.first

        # Both S and T start with NUM
        assert num in first[s]
        assert num in first[t]


class TestComputeRhsElemFirst:
    """Tests for GrammarAnalysis.rhs_first."""

    def test_literal(self):
        """Test FIRST of literal."""
        lit = LitTerminal("a")
        first = {}
        nullable = {}
        result = GrammarAnalysis.rhs_first(lit, first, nullable)
        assert lit in result

    def test_terminal(self):
        """Test FIRST of terminal."""
        term = NamedTerminal("NUM", BaseType("Int64"))
        first = {}
        nullable = {}
        result = GrammarAnalysis.rhs_first(term, first, nullable)
        assert term in result

    def test_nonterminal(self):
        """Test FIRST of nonterminal."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        lit = LitTerminal("a")
        first = {nt: {lit}}
        nullable = {nt: False}
        result = GrammarAnalysis.rhs_first(nt, first, nullable)
        assert lit in result

    def test_sequence_all_first(self):
        """Test FIRST of sequence where first element is not nullable."""
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        seq = Sequence((a, b))

        first = {a: {lit_a}, b: {lit_b}}
        nullable = {a: False, b: False}
        result = GrammarAnalysis.rhs_first(seq, first, nullable)
        assert lit_a in result
        assert lit_b not in result

    def test_sequence_nullable_first(self):
        """Test FIRST of sequence where first element is nullable."""
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        seq = Sequence((a, b))

        first = {a: {lit_a}, b: {lit_b}}
        nullable = {a: True, b: False}
        result = GrammarAnalysis.rhs_first(seq, first, nullable)
        assert lit_a in result
        assert lit_b in result


class TestComputeFirstK:
    """Tests for compute_first_k."""

    def test_simple_grammar_k2(self):
        """Test FIRST_2 for simple grammar."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        first_k = grammar.analysis.compute_first_k(k=2)

        # S -> A B, so FIRST_2(S) = {("a", "b")}
        assert (lit_a, lit_b) in first_k[s]

    def test_k1_matches_first(self):
        """Test that FIRST_1 matches regular FIRST."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        first = grammar.analysis.first
        first_k = grammar.analysis.compute_first_k(k=1)

        for nt in [s, a, b]:
            first_set = {(t,) for t in first[nt]}
            assert first_set == first_k[nt]

    def test_empty_sequence_gives_empty_tuple(self):
        """Test that empty production gives empty tuple."""
        s = Nonterminal("S", MessageType("proto", "S"))
        grammar = Grammar(s)
        constructor = Lambda(
            [], MessageType("proto", "S"), Var("x", MessageType("proto", "S"))
        )
        grammar.add_rule(Rule(s, Sequence(()), constructor))

        first_k = grammar.analysis.compute_first_k(k=2)
        assert () in first_k[s]


class TestComputeRhsElemFirstK:
    """Tests for GrammarAnalysis.rhs_first_k."""

    def test_literal_k2(self):
        """Test FIRST_k of literal."""
        lit = LitTerminal("a")
        first_k = {}
        nullable = {}
        result = GrammarAnalysis.rhs_first_k(lit, first_k, nullable, k=2)
        assert (lit,) in result

    def test_terminal_k2(self):
        """Test FIRST_k of terminal."""
        term = NamedTerminal("NUM", BaseType("Int64"))
        first_k = {}
        nullable = {}
        result = GrammarAnalysis.rhs_first_k(term, first_k, nullable, k=2)
        assert (term,) in result

    def test_nonterminal_k2(self):
        """Test FIRST_k of nonterminal."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        lit = LitTerminal("a")
        first_k = {nt: {(lit,)}}
        nullable = {nt: False}
        result = GrammarAnalysis.rhs_first_k(nt, first_k, nullable, k=2)
        assert (lit,) in result

    def test_sequence_concatenation_k2(self):
        """Test FIRST_k of sequence concatenates."""
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        seq = Sequence((a, b))

        first_k = {a: {(lit_a,)}, b: {(lit_b,)}}
        nullable = {a: False, b: False}
        result = GrammarAnalysis.rhs_first_k(seq, first_k, nullable, k=2)
        assert (lit_a, lit_b) in result

    def test_sequence_truncates_to_k(self):
        """Test FIRST_k truncates sequences to k."""
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        c = Nonterminal("C", MessageType("proto", "C"))
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        lit_c = LitTerminal("c")
        seq = Sequence((a, b, c))

        first_k = {a: {(lit_a,)}, b: {(lit_b,)}, c: {(lit_c,)}}
        nullable = {a: False, b: False, c: False}
        result = GrammarAnalysis.rhs_first_k(seq, first_k, nullable, k=2)
        assert (lit_a, lit_b) in result
        assert (lit_a, lit_b, lit_c) not in result

    def test_empty_sequence_gives_empty_tuple(self):
        """Test empty sequence gives empty tuple."""
        seq = Sequence(())
        first_k = {}
        nullable = {}
        result = GrammarAnalysis.rhs_first_k(seq, first_k, nullable, k=2)
        assert () in result

    def test_star_includes_empty(self):
        """Test that star includes empty tuple."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        lit = LitTerminal("a")
        star = Star(nt)

        first_k = {nt: {(lit,)}}
        nullable = {nt: False}
        result = GrammarAnalysis.rhs_first_k(star, first_k, nullable, k=2)
        assert (lit,) in result
        assert () in result

    def test_option_includes_empty(self):
        """Test that option includes empty tuple."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        lit = LitTerminal("a")
        opt = Option(nt)

        first_k = {nt: {(lit,)}}
        nullable = {nt: False}
        result = GrammarAnalysis.rhs_first_k(opt, first_k, nullable, k=2)
        assert (lit,) in result
        assert () in result


class TestComputeFollow:
    """Tests for compute_follow."""

    def test_simple_grammar(self):
        """Test FOLLOW for simple grammar."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        follow = grammar.analysis.follow

        # FOLLOW(A) includes FIRST(B) = {"b"}
        assert lit_b in follow[a]
        # FOLLOW(S) includes EOF
        eof = NamedTerminal("$", BaseType("EOF"))
        assert eof in follow[s]

    def test_nullable_propagates_follow(self):
        """Test that nullable nonterminal propagates FOLLOW."""
        s = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        lit_b = LitTerminal("b")

        grammar = Grammar(s)

        # S -> A B
        param_a = Var("x", MessageType("proto", "A"))
        param_b = Var("y", MessageType("proto", "B"))
        constructor_s = Lambda([param_a, param_b], MessageType("proto", "S"), param_a)
        grammar.add_rule(Rule(s, Sequence((a, b)), constructor_s))

        # A -> epsilon
        constructor_a = Lambda(
            [], MessageType("proto", "A"), Var("z", MessageType("proto", "A"))
        )
        grammar.add_rule(Rule(a, Sequence(()), constructor_a))

        # B -> "b"
        constructor_b = Lambda(
            [], MessageType("proto", "B"), Var("w", MessageType("proto", "B"))
        )
        grammar.add_rule(Rule(b, lit_b, constructor_b))

        follow = grammar.analysis.follow

        # FOLLOW(A) includes FIRST(B) = {"b"}
        assert lit_b in follow[a]
        # FOLLOW(A) also includes FOLLOW(S) because B might be nullable
        # But in this case B is not nullable, so just {"b"}


class TestComputeRhsElemFollow:
    """Tests for GrammarAnalysis.rhs_follow."""

    def test_nonterminal_at_end(self):
        """Test FOLLOW for nonterminal at end of production."""
        lhs = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        lit_a = LitTerminal("a")

        first = {a: {lit_a}}
        nullable = {a: False}
        follow = {lhs: {lit_a}}

        result = GrammarAnalysis.rhs_follow(a, lhs, first, nullable, follow)
        assert a in result
        assert lit_a in result[a]

    def test_nonterminal_followed_by_terminal(self):
        """Test FOLLOW for nonterminal followed by terminal."""
        lhs = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        lit_b = LitTerminal("b")

        seq = Sequence((a, lit_b))
        first = {a: set(), b: set()}
        nullable = {a: False, b: False}
        follow = {lhs: set()}

        result = GrammarAnalysis.rhs_follow(seq, lhs, first, nullable, follow)
        assert a in result
        assert lit_b in result[a]


class TestComputeFollowK:
    """Tests for compute_follow_k."""

    def test_simple_grammar_k2(self):
        """Test FOLLOW_2 for simple grammar."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        follow_k = grammar.analysis.compute_follow_k(k=2)

        # FOLLOW_2(A) includes FIRST_2(B) = {("b",)}
        assert (lit_b,) in follow_k[a]

        # FOLLOW_2(S) includes {("$",)}
        eof = NamedTerminal("$", BaseType("EOF"))
        assert (eof,) in follow_k[s]

    def test_k1_matches_follow(self):
        """Test that FOLLOW_1 matches regular FOLLOW."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        follow = grammar.analysis.follow
        follow_k = grammar.analysis.compute_follow_k(k=1)

        for nt in [s, a, b]:
            follow_set = {(t,) for t in follow[nt]}
            assert follow_set == follow_k[nt]


class TestConcatFirstKSets:
    """Tests for GrammarAnalysis.concat_k."""

    def test_concatenate_two_single_element_sets(self):
        """Test concatenating two single-element sets."""
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        set1 = {(lit_a,)}
        set2 = {(lit_b,)}

        result = GrammarAnalysis.concat_k(set1, set2, k=2)
        assert (lit_a, lit_b) in result

    def test_truncate_to_k(self):
        """Test that concatenation truncates to k."""
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        lit_c = LitTerminal("c")
        set1 = {(lit_a,)}
        set2 = {(lit_b, lit_c)}

        result = GrammarAnalysis.concat_k(set1, set2, k=2)
        assert (lit_a, lit_b) in result
        assert (lit_a, lit_b, lit_c) not in result

    def test_already_at_k_length(self):
        """Test sequences already at k length."""
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        lit_c = LitTerminal("c")
        set1 = {(lit_a, lit_b)}
        set2 = {(lit_c,)}

        result = GrammarAnalysis.concat_k(set1, set2, k=2)
        assert (lit_a, lit_b) in result

    def test_empty_tuple_concatenation(self):
        """Test concatenation with empty tuple."""
        lit_a = LitTerminal("a")
        set1 = {()}
        set2 = {(lit_a,)}

        result = GrammarAnalysis.concat_k(set1, set2, k=2)
        assert (lit_a,) in result

    def test_multiple_sequences(self):
        """Test concatenation with multiple sequences."""
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        lit_c = LitTerminal("c")
        set1 = {(lit_a,), (lit_b,)}
        set2 = {(lit_c,)}

        result = GrammarAnalysis.concat_k(set1, set2, k=2)
        assert (lit_a, lit_c) in result
        assert (lit_b, lit_c) in result


class TestDragonBookExamples:
    """Tests based on examples from the Dragon Book."""

    def test_dragon_book_example_4_28(self):
        """Test grammar from Dragon Book Example 4.28.

        E -> T Ep, Ep -> + T Ep | eps, T -> F Tp,
        Tp -> * F Tp | eps, F -> ( E ) | id
        """
        grammar, nt, tok = _grammar("""
            E -> T Ep
            Ep -> "+" T Ep | eps
            T -> F Tp
            Tp -> "*" F Tp | eps
            F -> "(" E ")" | id
        """)
        e, ep = nt["E"], nt["Ep"]
        t, tp = nt["T"], nt["Tp"]
        f = nt["F"]
        id_tok = tok["id"]
        plus, star = LitTerminal("+"), LitTerminal("*")
        lparen, rparen = LitTerminal("("), LitTerminal(")")

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert nullable[ep]
        assert nullable[tp]
        assert not nullable[e]
        assert not nullable[t]
        assert not nullable[f]

        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        assert lparen in first[e]
        assert id_tok in first[e]
        assert lparen in first[t]
        assert id_tok in first[t]
        assert lparen in first[f]
        assert id_tok in first[f]
        assert plus in first[ep]
        assert star in first[tp]

        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)
        eof = NamedTerminal("$", BaseType("EOF"))
        assert eof in follow[e]
        assert rparen in follow[e]
        assert eof in follow[ep]
        assert rparen in follow[ep]
        assert plus in follow[t]
        assert plus in follow[tp]
        assert star in follow[f]

    def test_dragon_book_example_4_31(self):
        """Test grammar from Dragon Book Example 4.31.

        S -> if E then S Sp | a, Sp -> else S | eps, E -> b
        """
        grammar, nt, _ = _grammar("""
            S -> "if" E "then" S Sp | "a"
            Sp -> "else" S | eps
            E -> "b"
        """)
        s, sp, e = nt["S"], nt["Sp"], nt["E"]
        if_tok = LitTerminal("if")
        a_tok = LitTerminal("a")
        else_tok = LitTerminal("else")
        then_tok = LitTerminal("then")
        b_tok = LitTerminal("b")

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert nullable[sp]
        assert not nullable[s]
        assert not nullable[e]

        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        assert if_tok in first[s]
        assert a_tok in first[s]
        assert else_tok in first[sp]
        assert b_tok in first[e]

        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)
        eof = NamedTerminal("$", BaseType("EOF"))
        assert eof in follow[s]
        assert else_tok in follow[s]
        assert eof in follow[sp]
        assert else_tok in follow[sp]
        assert then_tok in follow[e]

    def test_dragon_book_list_grammar(self):
        """Test simple list grammar: L -> L + D | D, D -> 0 | 1."""
        grammar, nt, _ = _grammar("""
            L -> L "+" D | D
            D -> "0" | "1"
        """)
        list_nt, d = nt["L"], nt["D"]
        plus = LitTerminal("+")
        zero, one = LitTerminal("0"), LitTerminal("1")

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert not nullable[list_nt]
        assert not nullable[d]

        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        assert zero in first[list_nt]
        assert one in first[list_nt]
        assert zero in first[d]
        assert one in first[d]

        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)
        eof = NamedTerminal("$", BaseType("EOF"))
        assert eof in follow[list_nt]
        assert plus in follow[list_nt]
        assert eof in follow[d]
        assert plus in follow[d]

    def test_dragon_book_nullable_propagation(self):
        """Test nullable propagation: S -> A B C, A -> a | eps, B -> b | eps, C -> c."""
        grammar, nt, _ = _grammar("""
            S -> A B C
            A -> "a" | eps
            B -> "b" | eps
            C -> "c"
        """)
        s, a, b, c = nt["S"], nt["A"], nt["B"], nt["C"]
        lit_a, lit_b, lit_c = LitTerminal("a"), LitTerminal("b"), LitTerminal("c")

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert nullable[a]
        assert nullable[b]
        assert not nullable[c]
        assert not nullable[s]

        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        assert lit_a in first[s]
        assert lit_b in first[s]
        assert lit_c in first[s]

        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)
        assert lit_b in follow[a]
        assert lit_c in follow[b]

    def test_dragon_book_first_k_example(self):
        """Test FIRST_k for grammar requiring lookahead k>1.

        S -> a A a | b A b, A -> a | b
        """
        grammar, nt, _ = _grammar("""
            S -> "a" A "a" | "b" A "b"
            A -> "a" | "b"
        """)
        s, _a = nt["S"], nt["A"]
        lit_a, lit_b = LitTerminal("a"), LitTerminal("b")

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        assert lit_a in first[s]
        assert lit_b in first[s]

        first_k = GrammarAnalysis.compute_first_k_static(
            grammar, k=3, nullable=nullable
        )
        assert (lit_a, lit_a, lit_a) in first_k[s]
        assert (lit_a, lit_b, lit_a) in first_k[s]
        assert (lit_b, lit_a, lit_b) in first_k[s]
        assert (lit_b, lit_b, lit_b) in first_k[s]

    def test_dragon_book_dangling_else_with_follow_k(self):
        """Test dangling else ambiguity with FOLLOW_k.

        S -> if E then S Sp | other, Sp -> else S | eps, E -> expr
        """
        grammar, nt, _ = _grammar("""
            S -> "if" E "then" S Sp | "other"
            Sp -> "else" S | eps
            E -> "expr"
        """)
        sp = nt["Sp"]
        if_tok = LitTerminal("if")
        else_tok = LitTerminal("else")
        other_tok = LitTerminal("other")

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        first_k = GrammarAnalysis.compute_first_k_static(
            grammar, k=2, nullable=nullable
        )
        follow_k = GrammarAnalysis.compute_follow_k_static(
            grammar, k=2, nullable=nullable, first_k=first_k
        )

        eof = NamedTerminal("$", BaseType("EOF"))
        assert (eof,) in follow_k[sp]
        assert (else_tok, if_tok) in follow_k[sp]
        assert (else_tok, other_tok) in follow_k[sp]


class TestIntegration:
    """Integration tests combining multiple analysis functions."""

    def test_grammar_methods_cache_results(self):
        """Test that Grammar.analysis methods properly cache results."""
        grammar, _, _, _, _, _ = make_simple_grammar()

        # First call should compute
        nullable1 = grammar.analysis.nullable
        # Second call should return cached value
        nullable2 = grammar.analysis.nullable
        assert nullable1 is nullable2

        # Same for FIRST
        first1 = grammar.analysis.first
        first2 = grammar.analysis.first
        assert first1 is first2

        # Same for FOLLOW
        follow1 = grammar.analysis.follow
        follow2 = grammar.analysis.follow
        assert follow1 is follow2

    def test_complete_analysis_pipeline(self):
        """Test complete analysis pipeline."""
        grammar, s, a, _, lit_a, lit_b = make_simple_grammar()

        # Check reachability
        reachable = grammar.analysis.reachability
        assert len(reachable) == 3

        # Compute nullable
        nullable = grammar.analysis.nullable
        assert not any(nullable.values())

        # Compute FIRST
        first = grammar.analysis.first
        assert lit_a in first[s]

        # Compute FOLLOW
        follow = grammar.analysis.follow
        assert lit_b in follow[a]

    def test_complex_grammar_analysis(self):
        """Test analysis on more complex grammar."""
        s = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")

        grammar = Grammar(s)

        # S -> A B | B
        param_a = Var("x", MessageType("proto", "A"))
        param_b = Var("y", MessageType("proto", "B"))
        constructor1 = Lambda([param_a, param_b], MessageType("proto", "S"), param_a)
        grammar.add_rule(Rule(s, Sequence((a, b)), constructor1))

        param_b2 = Var("z", MessageType("proto", "B"))
        constructor2 = Lambda([param_b2], MessageType("proto", "S"), param_b2)
        grammar.add_rule(Rule(s, b, constructor2))

        # A -> "a"
        constructor3 = Lambda(
            [], MessageType("proto", "A"), Var("w", MessageType("proto", "A"))
        )
        grammar.add_rule(Rule(a, lit_a, constructor3))

        # B -> "b"
        constructor4 = Lambda(
            [], MessageType("proto", "B"), Var("v", MessageType("proto", "B"))
        )
        grammar.add_rule(Rule(b, lit_b, constructor4))

        # Check everything works together
        reachable = grammar.analysis.reachability
        grammar.analysis.nullable  # ensure it runs
        first = grammar.analysis.first
        grammar.analysis.follow  # ensure it runs

        assert len(reachable) == 3
        assert lit_a in first[s]
        assert lit_b in first[s]


class TestAppelChapter3Examples:
    """Tests based on examples from Appel's Modern Compiler Implementation, Chapter 3."""

    def test_grammar_3_12_nullable_first_follow(self):
        """Test Grammar 3.12 (page 48).

        Z -> d | X Y Z, Y -> eps | c, X -> Y | a
        """
        grammar, nt, _ = _grammar("""
            Z -> "d" | X Y Z
            Y -> eps | "c"
            X -> Y | "a"
        """)
        z, y, x = nt["Z"], nt["Y"], nt["X"]
        lit_a, lit_c, lit_d = LitTerminal("a"), LitTerminal("c"), LitTerminal("d")

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert nullable[x], "X should be nullable (X -> Y -> epsilon)"
        assert nullable[y], "Y should be nullable (Y -> epsilon)"
        assert not nullable[z], "Z should not be nullable"

        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        assert first[x] == {lit_a, lit_c}, f"FIRST(X) should be {{a, c}}, got {first[x]}"
        assert first[y] == {lit_c}, f"FIRST(Y) should be {{c}}, got {first[y]}"
        assert first[z] == {lit_a, lit_c, lit_d}, f"FIRST(Z) should be {{a, c, d}}, got {first[z]}"

        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)
        eof = NamedTerminal("$", BaseType("EOF"))
        assert lit_a in follow[x]
        assert lit_c in follow[x]
        assert lit_d in follow[x]
        assert lit_a in follow[y]
        assert lit_c in follow[y]
        assert lit_d in follow[y]
        assert eof in follow[z]

    def test_grammar_3_1_straight_line(self):
        """Test simplified straight-line grammar from Grammar 3.1 (page 41).

        S -> id := E Sp | print ( L ) Sp, Sp -> ; S | eps,
        E -> id Ep | num Ep, Ep -> + E | eps,
        L -> E Lp, Lp -> , E Lp | eps
        """
        grammar, nt, tok = _grammar("""
            S -> id ":=" E Sp | "print" "(" L ")" Sp
            Sp -> ";" S | eps
            E -> id Ep | num Ep
            Ep -> "+" E | eps
            L -> E Lp
            Lp -> "," E Lp | eps
        """)
        s, sp = nt["S"], nt["Sp"]
        e, ep = nt["E"], nt["Ep"]
        l_nt, lp = nt["L"], nt["Lp"]
        id_tok, num_tok = tok["id"], tok["num"]
        semi = LitTerminal(";")
        plus = LitTerminal("+")
        comma = LitTerminal(",")
        print_tok = LitTerminal("print")

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert nullable[sp]
        assert nullable[ep]
        assert nullable[lp]
        assert not nullable[s]
        assert not nullable[e]
        assert not nullable[l_nt]

        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        assert id_tok in first[s]
        assert print_tok in first[s]
        assert id_tok in first[e]
        assert num_tok in first[e]
        assert semi in first[sp]
        assert plus in first[ep]
        assert comma in first[lp]

    def test_grammar_3_8_expression_precedence(self):
        """Test expression grammar from Grammar 3.8 (page 45).

        E -> T Ep, Ep -> + T Ep | eps, T -> F Tp, Tp -> * F Tp | eps,
        F -> id | ( E )
        """
        grammar, nt, tok = _grammar("""
            E -> T Ep
            Ep -> "+" T Ep | eps
            T -> F Tp
            Tp -> "*" F Tp | eps
            F -> id | "(" E ")"
        """)
        e, ep = nt["E"], nt["Ep"]
        t, tp = nt["T"], nt["Tp"]
        f = nt["F"]
        id_tok = tok["id"]
        plus, star = LitTerminal("+"), LitTerminal("*")
        lparen, rparen = LitTerminal("("), LitTerminal(")")

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert nullable[ep]
        assert nullable[tp]
        assert not nullable[e]
        assert not nullable[t]
        assert not nullable[f]

        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        assert first[f] == {id_tok, lparen}
        assert id_tok in first[t]
        assert lparen in first[t]
        assert id_tok in first[e]
        assert lparen in first[e]
        assert first[ep] == {plus}
        assert first[tp] == {star}

        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)
        eof = NamedTerminal("$", BaseType("EOF"))
        assert eof in follow[e]
        assert rparen in follow[e]
        assert eof in follow[ep]
        assert rparen in follow[ep]
        assert plus in follow[t]
        assert eof in follow[t]
        assert rparen in follow[t]
        assert plus in follow[tp]
        assert star in follow[f]

    def test_grammar_3_20_sexp(self):
        """Test S-expression grammar from Grammar 3.20 (page 62).

        S -> ( L ) | x, L -> S Lp, Lp -> S Lp | eps
        """
        grammar, nt, _ = _grammar("""
            S -> "(" L ")" | "x"
            L -> S Lp
            Lp -> S Lp | eps
        """)
        s, l_nt, lp = nt["S"], nt["L"], nt["Lp"]
        lparen, rparen = LitTerminal("("), LitTerminal(")")
        x_tok = LitTerminal("x")

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert nullable[lp]
        assert not nullable[s]
        assert not nullable[l_nt]

        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        assert first[s] == {lparen, x_tok}
        assert first[l_nt] == {lparen, x_tok}
        assert first[lp] == {lparen, x_tok}

        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)
        eof = NamedTerminal("$", BaseType("EOF"))
        assert eof in follow[s]
        assert rparen in follow[s]
        assert rparen in follow[l_nt]
        assert rparen in follow[lp]

    def test_exercise_3_5_grammar(self):
        """Test grammar from Exercise 3.5: S -> a S a | a a."""
        grammar, nt, _ = _grammar("""
            S -> "a" S "a" | "a" "a"
        """)
        s = nt["S"]
        lit_a = LitTerminal("a")

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert not nullable[s]

        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        assert first[s] == {lit_a}

        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)
        eof = NamedTerminal("$", BaseType("EOF"))
        assert lit_a in follow[s]
        assert eof in follow[s]

    def test_first_k_grammar_3_12(self):
        """Test FIRST_k for Grammar 3.12 with k=2.

        Z -> d | X Y Z, Y -> eps | c, X -> Y | a
        """
        grammar, nt, _ = _grammar("""
            Z -> "d" | X Y Z
            Y -> eps | "c"
            X -> Y | "a"
        """)
        z, y, x = nt["Z"], nt["Y"], nt["X"]
        lit_a, lit_c, lit_d = LitTerminal("a"), LitTerminal("c"), LitTerminal("d")

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        first_k = GrammarAnalysis.compute_first_k_static(
            grammar, k=2, nullable=nullable
        )

        assert (lit_a,) in first_k[x]
        assert (lit_c,) in first_k[x]
        assert () in first_k[x]
        assert (lit_c,) in first_k[y]
        assert () in first_k[y]
        assert (lit_d,) in first_k[z]
        assert (lit_a, lit_a) in first_k[z]
        assert (lit_a, lit_c) in first_k[z]
        assert (lit_a, lit_d) in first_k[z]
        assert (lit_c, lit_a) in first_k[z]
        assert (lit_c, lit_c) in first_k[z]
        assert (lit_c, lit_d) in first_k[z]
