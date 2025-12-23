"""Utility functions for grammar manipulation."""

from typing import Dict, TypeVar, Optional, cast
from .grammar import Nonterminal, Sequence, Star, Option, Rhs, RhsSymbol, Rule

SomeRhs = TypeVar('SomeRhs', bound=Rhs)

def rename_in_rhs(rhs: SomeRhs, rename_map: Dict[Nonterminal, Nonterminal]) -> SomeRhs:
    """Recursively rename nonterminals in RHS, returning new Rhs."""
    if isinstance(rhs, Nonterminal):
        if rhs in rename_map:
            return rename_map[rhs]
        return rhs
    elif isinstance(rhs, Sequence):
        new_elements = tuple(rename_in_rhs(elem, rename_map) for elem in rhs.elements)
        return cast(SomeRhs, Sequence(new_elements))
    elif isinstance(rhs, Star):
        return cast(SomeRhs, Star(rename_in_rhs(rhs.rhs, rename_map)))
    elif isinstance(rhs, Option):
        return cast(SomeRhs, Option(rename_in_rhs(rhs.rhs, rename_map)))
    else:
        return rhs


def rewrite_rhs_with_replacements(rhs: Rhs, replacements: Dict[Rhs, Rhs]) -> Optional[Rhs]:
    """Rewrite RHS by replacing symbols according to the mapping.

    Returns new_rhs if changed, None otherwise.
    """
    if rhs in replacements:
        assert replacements[rhs].target_type() == rhs.target_type()
        return replacements[rhs]
    elif isinstance(rhs, Sequence):
        new_elements = []
        changed = False
        for elem in rhs.elements:
            new_elem = rewrite_rhs_with_replacements(elem, replacements)
            if new_elem is not None:
                new_elements.append(new_elem)
                changed = True
            else:
                new_elements.append(elem)
        if changed:
            return Sequence(tuple(new_elements))
        return None
    elif isinstance(rhs, Star):
        new_inner = rewrite_rhs_with_replacements(rhs.rhs, replacements)
        if new_inner is not None:
            return Star(cast(RhsSymbol, new_inner))
        return None
    elif isinstance(rhs, Option):
        new_inner = rewrite_rhs_with_replacements(rhs.rhs, replacements)
        if new_inner is not None:
            return Option(cast(RhsSymbol, new_inner))
        return None
    else:
        return None


def rewrite_rule_with_replacements(rule: Rule, replacements: Dict[Rhs, Rhs]) -> Optional[Rule]:
    """Rewrite rule by replacing symbols in RHS."""
    new_rhs = rewrite_rhs_with_replacements(rule.rhs, replacements)
    if new_rhs is not None:
        return Rule(
            lhs=rule.lhs,
            rhs=new_rhs,
            construct_action=rule.construct_action,
            deconstruct_action=rule.deconstruct_action,
            source_type=rule.source_type
        )
    return None
