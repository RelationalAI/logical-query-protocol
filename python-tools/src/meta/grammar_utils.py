"""Utility functions for grammar manipulation."""

from typing import Dict, TypeVar, Optional, cast
from .grammar import Nonterminal, Sequence, Star, Option, Rhs, RhsSymbol, Rule

SomeRhs = TypeVar('SomeRhs', bound=Rhs)

def rewrite_rule(rule: Rule, rename_map: Dict[Rhs, Rhs]) -> Rule:
    """Recursively rename nonterminals in RHS, returning new Rhs."""
    result = rewrite_rule_with_replacements(rule, rename_map)
    if result is not None:
        return result
    return rule

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
