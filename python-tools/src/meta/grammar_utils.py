"""Utility functions for grammar manipulation."""

from typing import Dict, List, Optional, Type, TypeVar, Union, cast
from .grammar import Sequence, Star, Option, Rhs, Nonterminal, NamedTerminal, LitTerminal, Rule

T = TypeVar('T', bound=Rhs)


def collect(rhs: Rhs, target_type: Type[T]) -> List[T]:
    """Collect all instances of target_type from the Rhs tree.

    Traverses the Rhs structure and returns a deduplicated list of all
    nodes matching the given type, preserving first-occurrence order.
    """
    results: List[T] = []

    if isinstance(rhs, target_type):
        results.append(rhs)
    if isinstance(rhs, Sequence):
        for elem in rhs.elements:
            results.extend(collect(elem, target_type))
    elif isinstance(rhs, (Star, Option)):
        results.extend(collect(rhs.rhs, target_type))

    return list(dict.fromkeys(results))


def get_nonterminals(rhs: Rhs) -> List[Nonterminal]:
    """Return the list of all nonterminals referenced in a Rhs."""
    return collect(rhs, Nonterminal)


def get_literals(rhs: Rhs) -> List[LitTerminal]:
    """Return the list of all literals referenced in a Rhs."""
    return collect(rhs, LitTerminal)


def is_epsilon(rhs: Rhs) -> bool:
    """Check if rhs represents an epsilon production (empty sequence)."""
    return isinstance(rhs, Sequence) and len(rhs.elements) == 0


def rhs_elements(rhs: Rhs) -> tuple:
    """Return elements of rhs. For Sequence, returns rhs.elements; otherwise returns (rhs,)."""
    if isinstance(rhs, Sequence):
        return rhs.elements
    return (rhs,)


def count_nonliteral_rhs_elements(rhs: Rhs) -> int:
    """Count the number of elements in an RHS that produce action parameters.

    This counts all RHS elements except literals, as each non-literal position
    corresponds to a parameter in the action lambda.
    """
    if isinstance(rhs, Sequence):
        return sum(count_nonliteral_rhs_elements(elem) for elem in rhs.elements)
    elif isinstance(rhs, LitTerminal):
        return 0
    else:
        assert isinstance(rhs, (NamedTerminal, Nonterminal, Option, Star)), f"found {type(rhs)}"
        return 1


def _rewrite_rhs(rhs: Rhs, replacements: Dict[Rhs, Rhs]) -> Optional[Rhs]:
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
            new_elem = _rewrite_rhs(elem, replacements)
            if new_elem is not None:
                new_elements.append(new_elem)
                changed = True
            else:
                new_elements.append(elem)
        if changed:
            return Sequence(tuple(new_elements))
        return None
    elif isinstance(rhs, Star):
        new_inner = _rewrite_rhs(rhs.rhs, replacements)
        if new_inner is not None:
            return Star(cast(Union[Nonterminal, NamedTerminal], new_inner))
        return None
    elif isinstance(rhs, Option):
        new_inner = _rewrite_rhs(rhs.rhs, replacements)
        if new_inner is not None:
            return Option(cast(Union[Nonterminal, NamedTerminal], new_inner))
        return None
    else:
        return None


def rewrite_rule(rule: Rule, replacements: Dict[Rhs, Rhs]) -> Rule:
    """Rewrite rule by replacing symbols in RHS.

    Returns the rewritten rule, or the original if no replacements matched.
    """
    new_rhs = _rewrite_rhs(rule.rhs, replacements)
    if new_rhs is not None:
        return Rule(
            lhs=rule.lhs,
            rhs=new_rhs,
            constructor=rule.constructor,
            deconstructor=rule.deconstructor,
            source_type=rule.source_type
        )
    return rule
