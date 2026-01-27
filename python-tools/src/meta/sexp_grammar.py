"""S-expression visitors for grammar constructs.

This module provides functions to convert s-expressions into grammar
structures (Rhs, Rule) and to load grammar configuration files.

Terminal declarations (at top of file):
    (terminal NAME Type)            -> declare terminal NAME with type Type

RHS syntax (with context):
    "literal"                       -> LitTerminal("literal")
    NAME                            -> NamedTerminal (if NAME in terminals)
    name                            -> Nonterminal (if name in nonterminals)
    (star name)                     -> Star(rhs)
    (option name)                   -> Option(rhs)

Rule syntax:
    (rule (lhs lhs_name LhsType) (rhs rhs...) constructor)

Config file directives:
    (terminal NAME Type)            -> declare terminal type
    (rule ...)                      -> add rule
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .sexp import SAtom, SList, SExpr
from .sexp_parser import parse_sexp_file
from .sexp_target import sexp_to_type, sexp_to_expr, type_to_sexp, expr_to_sexp, SExprConversionError
from .grammar import (
    Rhs, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence, Rule
)
from .target import Lambda, TargetType


@dataclass
class TypeContext:
    """Context for looking up types of terminals and nonterminals."""
    terminals: Dict[str, TargetType]
    nonterminals: Dict[str, TargetType]


class GrammarConversionError(SExprConversionError):
    """Error during s-expression to grammar conversion."""
    pass


def sexp_to_rhs(sexp: SExpr, ctx: Optional[TypeContext] = None) -> Rhs:
    """Convert an s-expression to an Rhs.

    Args:
        sexp: S-expression representing an RHS element
        ctx: Optional type context for looking up terminal and nonterminal types.
             If provided, bare symbols are looked up as terminals or nonterminals.

    Returns:
        Corresponding Rhs object

    Raises:
        GrammarConversionError: If the s-expression is not a valid RHS
    """
    if isinstance(sexp, SAtom):
        if sexp.quoted:
            return LitTerminal(str(sexp.value))
        # Bare symbol - look up in context
        if ctx is not None:
            # Handle booleans (true/false parsed as Python booleans)
            if isinstance(sexp.value, bool):
                name = "true" if sexp.value else "false"
            elif isinstance(sexp.value, str):
                name = sexp.value
            else:
                raise GrammarConversionError(f"Unquoted atom must be symbol: {sexp}")
            if name in ctx.terminals:
                return NamedTerminal(name, ctx.terminals[name])
            if name in ctx.nonterminals:
                return Nonterminal(name, ctx.nonterminals[name])
            raise GrammarConversionError(f"unknown symbol in RHS: {name}")
        raise GrammarConversionError(f"Unquoted atom in RHS requires context: {sexp}")

    if not isinstance(sexp, SList) or len(sexp) == 0:
        raise GrammarConversionError(f"Invalid RHS expression: {sexp}")

    head = sexp.head()
    if not isinstance(head, SAtom) or head.quoted:
        raise GrammarConversionError(f"RHS expression must start with a symbol: {sexp}")

    tag = head.value

    if tag == "nonterm":
        if len(sexp) == 2:
            # New syntax: (nonterm name) - lookup type from context
            name = _expect_symbol(sexp[1], "nonterminal name")
            if ctx is None:
                raise GrammarConversionError(f"nonterm requires name and type: {sexp}")
            if name not in ctx.nonterminals:
                raise GrammarConversionError(f"unknown nonterminal: {name}")
            typ = ctx.nonterminals[name]
        elif len(sexp) == 3:
            # Old syntax: (nonterm name Type) - inline type
            name = _expect_symbol(sexp[1], "nonterminal name")
            typ = sexp_to_type(sexp[2])
        else:
            raise GrammarConversionError(f"nonterm requires name and optional type: {sexp}")
        return Nonterminal(name, typ)

    elif tag == "term":
        if len(sexp) == 2:
            # New syntax: (term NAME) - lookup type from context
            name = _expect_symbol(sexp[1], "terminal name")
            if ctx is None:
                raise GrammarConversionError(f"term requires name and type: {sexp}")
            if name not in ctx.terminals:
                raise GrammarConversionError(f"unknown terminal: {name}")
            typ = ctx.terminals[name]
        elif len(sexp) == 3:
            # Old syntax: (term NAME Type) - inline type (override)
            name = _expect_symbol(sexp[1], "terminal name")
            typ = sexp_to_type(sexp[2])
        else:
            raise GrammarConversionError(f"term requires name and optional type: {sexp}")
        return NamedTerminal(name, typ)

    elif tag == "star":
        if len(sexp) != 2:
            raise GrammarConversionError(f"star requires one RHS element: {sexp}")
        inner = sexp_to_rhs(sexp[1], ctx)
        if not isinstance(inner, (Nonterminal, NamedTerminal)):
            raise GrammarConversionError(f"star inner must be nonterm or term: {sexp}")
        return Star(inner)

    elif tag == "option":
        if len(sexp) != 2:
            raise GrammarConversionError(f"option requires one RHS element: {sexp}")
        inner = sexp_to_rhs(sexp[1], ctx)
        if not isinstance(inner, (Nonterminal, NamedTerminal)):
            raise GrammarConversionError(f"option inner must be nonterm or term: {sexp}")
        return Option(inner)

    elif tag == "seq":
        if len(sexp) < 2:
            raise GrammarConversionError(f"seq requires at least one element: {sexp}")
        elements = [sexp_to_rhs(e, ctx) for e in sexp.elements[1:]]
        return Sequence(tuple(elements))

    else:
        raise GrammarConversionError(f"Unknown RHS form: {tag}")


def sexp_to_rule(sexp: SExpr, ctx: Optional[TypeContext] = None) -> Rule:
    """Convert an s-expression to a Rule.

    Args:
        sexp: S-expression of the form (rule (lhs name Type) (rhs rhs...) constructor)
        ctx: Optional type context for looking up terminal and nonterminal types.
             If provided, types are looked up from context instead of being inline.

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
    rhs_elements = [sexp_to_rhs(e, ctx) for e in rhs_sexp.elements[1:]]
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

    Terminals and nonterminals are output as bare symbols.
    Types are declared separately via terminal declarations and rule LHS.

    Args:
        rhs: Rhs to convert

    Returns:
        S-expression representation
    """
    if isinstance(rhs, LitTerminal):
        return SAtom(rhs.name, quoted=True)

    elif isinstance(rhs, NamedTerminal):
        return SAtom(rhs.name)

    elif isinstance(rhs, Nonterminal):
        return SAtom(rhs.name)

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


@dataclass
class GrammarConfig:
    """Result of loading a grammar config file."""
    terminals: Dict[str, TargetType]
    rules: Dict[Nonterminal, List[Rule]]


def load_grammar_config(text: str) -> GrammarConfig:
    """Load grammar rules from s-expression config text.

    The config file contains:
    - (terminal NAME Type) directives that declare terminal types
    - (rule ...) directives that define grammar rules

    Two-pass parsing:
    1. First pass collects terminal declarations and nonterminal types from rule LHS
    2. Second pass parses rules with type context for lookups

    Args:
        text: Config file content as text

    Returns:
        GrammarConfig with terminals and rules.
    """
    sexps = parse_sexp_file(text)

    # First pass: collect terminal declarations and nonterminal types from rule LHS
    terminals: Dict[str, TargetType] = {}
    nonterminals: Dict[str, TargetType] = {}
    rule_sexps: List[SExpr] = []

    for sexp in sexps:
        if not isinstance(sexp, SList) or len(sexp) == 0:
            raise GrammarConversionError(f"Invalid config directive: {sexp}")

        head = sexp.head()
        if not isinstance(head, SAtom):
            raise GrammarConversionError(f"Config directive must start with symbol: {sexp}")

        if head.value == "terminal":
            if len(sexp) != 3:
                raise GrammarConversionError(f"terminal requires name and type: {sexp}")
            name = _expect_symbol(sexp[1], "terminal name")
            typ = sexp_to_type(sexp[2])
            if name in terminals:
                raise GrammarConversionError(f"duplicate terminal declaration: {name}")
            terminals[name] = typ

        elif head.value == "rule":
            rule_sexps.append(sexp)
            # Extract nonterminal type from LHS
            if len(sexp) < 2:
                raise GrammarConversionError(f"rule requires (lhs ...), (rhs ...), constructor: {sexp}")
            lhs_sexp = sexp[1]
            if isinstance(lhs_sexp, SList) and len(lhs_sexp) == 3:
                lhs_head = lhs_sexp.head()
                if isinstance(lhs_head, SAtom) and lhs_head.value == "lhs":
                    name = _expect_symbol(lhs_sexp[1], "rule LHS name")
                    typ = sexp_to_type(lhs_sexp[2])
                    if name in nonterminals and nonterminals[name] != typ:
                        raise GrammarConversionError(
                            f"conflicting types for nonterminal {name}: "
                            f"{nonterminals[name]} vs {typ}"
                        )
                    nonterminals[name] = typ

        else:
            raise GrammarConversionError(f"Unknown config directive: {head.value}")

    # Second pass: parse rules with type context
    ctx = TypeContext(terminals=terminals, nonterminals=nonterminals)
    result: Dict[Nonterminal, List[Rule]] = {}

    for sexp in rule_sexps:
        rule = sexp_to_rule(sexp, ctx)
        lhs = rule.lhs
        if lhs not in result:
            result[lhs] = []
        result[lhs].append(rule)

    return GrammarConfig(terminals=terminals, rules=result)


def load_grammar_config_file(path: Path) -> GrammarConfig:
    """Load grammar rules from an s-expression config file.

    Args:
        path: Path to the config file

    Returns:
        GrammarConfig with terminals and rules.
    """
    return load_grammar_config(path.read_text())


def terminal_to_sexp(name: str, typ: TargetType) -> SExpr:
    """Convert a terminal declaration to an s-expression.

    Args:
        name: Terminal name
        typ: Terminal type

    Returns:
        S-expression of the form (terminal NAME Type)
    """
    return SList((SAtom("terminal"), SAtom(name), type_to_sexp(typ)))


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
    'TypeContext',
    'GrammarConfig',
    'sexp_to_rhs',
    'sexp_to_rule',
    'rhs_to_sexp',
    'rule_to_sexp',
    'terminal_to_sexp',
    'load_grammar_config',
    'load_grammar_config_file',
]
