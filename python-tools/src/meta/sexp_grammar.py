"""S-expression visitors for grammar constructs.

This module provides functions to convert s-expressions into grammar
structures (Rhs, Rule) and to load grammar configuration files.

RHS syntax:
    "literal"                       -> LitTerminal("literal")
    (nonterm name Type)             -> Nonterminal(name, type)
    (term NAME Type)                -> NamedTerminal(NAME, type)
    (star rhs)                      -> Star(rhs)
    (option rhs)                    -> Option(rhs)
    (seq rhs1 rhs2 ...)             -> Sequence([rhs1, rhs2, ...])

Rule syntax:
    (rule (lhs lhs_name LhsType) (rhs rhs...) constructor)

Config file directives:
    (rule ...)                      -> add rule
    (mark-nonfinal nonterminal)     -> mark as non-final
"""

from pathlib import Path
from typing import Dict, List, Set, Tuple

from .sexp import SAtom, SList, SExpr
from .sexp_parser import parse_sexp_file
from .sexp_target import sexp_to_type, sexp_to_expr, type_to_sexp, expr_to_sexp, SExprConversionError
from .grammar import (
    Rhs, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence, Rule
)
from .target import Lambda


class GrammarConversionError(SExprConversionError):
    """Error during s-expression to grammar conversion."""
    pass


def sexp_to_rhs(sexp: SExpr) -> Rhs:
    """Convert an s-expression to an Rhs.

    Args:
        sexp: S-expression representing an RHS element

    Returns:
        Corresponding Rhs object

    Raises:
        GrammarConversionError: If the s-expression is not a valid RHS
    """
    if isinstance(sexp, SAtom):
        if sexp.quoted:
            return LitTerminal(str(sexp.value))
        raise GrammarConversionError(f"Unquoted atom in RHS must be wrapped: {sexp}")

    if not isinstance(sexp, SList) or len(sexp) == 0:
        raise GrammarConversionError(f"Invalid RHS expression: {sexp}")

    head = sexp.head()
    if not isinstance(head, SAtom) or head.quoted:
        raise GrammarConversionError(f"RHS expression must start with a symbol: {sexp}")

    tag = head.value

    if tag == "nonterm":
        if len(sexp) != 3:
            raise GrammarConversionError(f"nonterm requires name and type: {sexp}")
        name = _expect_symbol(sexp[1], "nonterminal name")
        typ = sexp_to_type(sexp[2])
        return Nonterminal(name, typ)

    elif tag == "term":
        if len(sexp) != 3:
            raise GrammarConversionError(f"term requires name and type: {sexp}")
        name = _expect_symbol(sexp[1], "terminal name")
        typ = sexp_to_type(sexp[2])
        return NamedTerminal(name, typ)

    elif tag == "star":
        if len(sexp) != 2:
            raise GrammarConversionError(f"star requires one RHS element: {sexp}")
        inner = sexp_to_rhs(sexp[1])
        if not isinstance(inner, (Nonterminal, NamedTerminal)):
            raise GrammarConversionError(f"star inner must be nonterm or term: {sexp}")
        return Star(inner)

    elif tag == "option":
        if len(sexp) != 2:
            raise GrammarConversionError(f"option requires one RHS element: {sexp}")
        inner = sexp_to_rhs(sexp[1])
        if not isinstance(inner, (Nonterminal, NamedTerminal)):
            raise GrammarConversionError(f"option inner must be nonterm or term: {sexp}")
        return Option(inner)

    elif tag == "seq":
        if len(sexp) < 2:
            raise GrammarConversionError(f"seq requires at least one element: {sexp}")
        elements = [sexp_to_rhs(e) for e in sexp.elements[1:]]
        return Sequence(tuple(elements))

    else:
        raise GrammarConversionError(f"Unknown RHS form: {tag}")


def sexp_to_rule(sexp: SExpr) -> Rule:
    """Convert an s-expression to a Rule.

    Args:
        sexp: S-expression of the form (rule (lhs name Type) (rhs rhs...) constructor)

    Returns:
        Corresponding Rule object

    Raises:
        GrammarConversionError: If the s-expression is not a valid rule
    """
    if not isinstance(sexp, SList) or len(sexp) != 4:
        raise GrammarConversionError(f"rule requires (lhs ...), (rhs ...), constructor: {sexp}")

    head = sexp.head()
    if not isinstance(head, SAtom) or head.value != "rule":
        raise GrammarConversionError(f"Expected rule, got: {head}")

    # Parse (lhs name Type)
    lhs_sexp = sexp[1]
    if not isinstance(lhs_sexp, SList) or len(lhs_sexp) != 3:
        raise GrammarConversionError(f"lhs requires name and type: {lhs_sexp}")
    lhs_head = lhs_sexp.head()
    if not isinstance(lhs_head, SAtom) or lhs_head.value != "lhs":
        raise GrammarConversionError(f"Expected (lhs ...), got: {lhs_sexp}")
    lhs_name = _expect_symbol(lhs_sexp[1], "rule LHS name")
    lhs_type = sexp_to_type(lhs_sexp[2])

    # Parse (rhs rhs...)
    rhs_sexp = sexp[2]
    if not isinstance(rhs_sexp, SList) or len(rhs_sexp) < 1:
        raise GrammarConversionError(f"rhs must be a list: {rhs_sexp}")
    rhs_head = rhs_sexp.head()
    if not isinstance(rhs_head, SAtom) or rhs_head.value != "rhs":
        raise GrammarConversionError(f"Expected (rhs ...), got: {rhs_sexp}")
    rhs_elements = [sexp_to_rhs(e) for e in rhs_sexp.elements[1:]]
    if len(rhs_elements) == 1:
        rhs = rhs_elements[0]
    else:
        rhs = Sequence(tuple(rhs_elements))

    constructor_expr = sexp_to_expr(sexp[3])

    if not isinstance(constructor_expr, Lambda):
        raise GrammarConversionError(f"Rule constructor must be a lambda: {constructor_expr}")

    lhs = Nonterminal(lhs_name, lhs_type)
    return Rule(lhs=lhs, rhs=rhs, constructor=constructor_expr)


def rhs_to_sexp(rhs: Rhs) -> SExpr:
    """Convert an Rhs to an s-expression.

    Args:
        rhs: Rhs to convert

    Returns:
        S-expression representation
    """
    if isinstance(rhs, LitTerminal):
        return SAtom(rhs.name, quoted=True)

    elif isinstance(rhs, NamedTerminal):
        return SList((SAtom("term"), SAtom(rhs.name), type_to_sexp(rhs.type)))

    elif isinstance(rhs, Nonterminal):
        return SList((SAtom("nonterm"), SAtom(rhs.name), type_to_sexp(rhs.type)))

    elif isinstance(rhs, Star):
        return SList((SAtom("star"), rhs_to_sexp(rhs.rhs)))

    elif isinstance(rhs, Option):
        return SList((SAtom("option"), rhs_to_sexp(rhs.rhs)))

    elif isinstance(rhs, Sequence):
        return SList((SAtom("seq"),) + tuple(rhs_to_sexp(e) for e in rhs.elements))

    else:
        raise GrammarConversionError(f"Unknown RHS type: {type(rhs).__name__}")


def rule_to_sexp(rule: Rule) -> SExpr:
    """Convert a Rule to an s-expression.

    Args:
        rule: Rule to convert

    Returns:
        S-expression of the form (rule (lhs name Type) (rhs rhs...) constructor)
    """
    lhs_sexp = SList((
        SAtom("lhs"),
        SAtom(rule.lhs.name),
        type_to_sexp(rule.lhs.type)
    ))

    # Flatten sequences into the rhs form
    if isinstance(rule.rhs, Sequence):
        rhs_elements = tuple(rhs_to_sexp(e) for e in rule.rhs.elements)
    else:
        rhs_elements = (rhs_to_sexp(rule.rhs),)
    rhs_sexp = SList((SAtom("rhs"),) + rhs_elements)

    return SList((
        SAtom("rule"),
        lhs_sexp,
        rhs_sexp,
        expr_to_sexp(rule.constructor)
    ))


def load_grammar_config(text: str) -> Dict[Nonterminal, Tuple[List[Rule], bool]]:
    """Load grammar rules from s-expression config text.

    The config file contains:
    - (rule ...) directives that define grammar rules
    - (mark-nonfinal nt_name) directives that mark nonterminals as non-final

    Args:
        text: Config file content as text

    Returns:
        Dict mapping nonterminals to (rules, is_final) tuples.
        is_final=True means auto-generation should not add more rules.
    """
    sexps = parse_sexp_file(text)

    result: Dict[Nonterminal, Tuple[List[Rule], bool]] = {}
    nonfinal_nonterminals: Set[str] = set()

    for sexp in sexps:
        if not isinstance(sexp, SList) or len(sexp) == 0:
            raise GrammarConversionError(f"Invalid config directive: {sexp}")

        head = sexp.head()
        if not isinstance(head, SAtom):
            raise GrammarConversionError(f"Config directive must start with symbol: {sexp}")

        if head.value == "rule":
            rule = sexp_to_rule(sexp)
            lhs = rule.lhs
            if lhs not in result:
                result[lhs] = ([], True)
            rules_list, _ = result[lhs]
            rules_list.append(rule)

        elif head.value == "mark-nonfinal":
            if len(sexp) != 2:
                raise GrammarConversionError(f"mark-nonfinal requires nonterminal name: {sexp}")
            nt_name = _expect_symbol(sexp[1], "nonterminal name")
            nonfinal_nonterminals.add(nt_name)

        else:
            raise GrammarConversionError(f"Unknown config directive: {head.value}")

    # Apply non-final markers
    for lhs, (rules, _) in result.items():
        is_final = lhs.name not in nonfinal_nonterminals
        result[lhs] = (rules, is_final)

    return result


def load_grammar_config_file(path: Path) -> Dict[Nonterminal, Tuple[List[Rule], bool]]:
    """Load grammar rules from an s-expression config file.

    Args:
        path: Path to the config file

    Returns:
        Dict mapping nonterminals to (rules, is_final) tuples.
    """
    return load_grammar_config(path.read_text())


def _expect_symbol(sexp: SExpr, context: str) -> str:
    """Expect an unquoted symbol and return its string value."""
    if not isinstance(sexp, SAtom):
        raise GrammarConversionError(f"{context} must be a symbol, got: {sexp}")
    if sexp.quoted:
        raise GrammarConversionError(f"{context} must be unquoted symbol, got string: {sexp}")
    # Handle booleans (true/false parsed as Python booleans)
    if isinstance(sexp.value, bool):
        return "true" if sexp.value else "false"
    if not isinstance(sexp.value, str):
        raise GrammarConversionError(f"{context} must be a symbol, got: {sexp}")
    return sexp.value


__all__ = [
    'GrammarConversionError',
    'sexp_to_rhs',
    'sexp_to_rule',
    'rhs_to_sexp',
    'rule_to_sexp',
    'load_grammar_config',
    'load_grammar_config_file',
]
