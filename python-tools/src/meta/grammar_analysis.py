"""Grammar analysis functions.

This module provides functions for analyzing grammars including reachability,
nullable computation, FIRST/FOLLOW sets, and LL(k) checking.
"""

from typing import Dict, List, Optional, Set, Tuple, TYPE_CHECKING, Mapping

if TYPE_CHECKING:
    from .grammar import Grammar, Rhs, Rule

from .grammar import LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence, Terminal
from .target import BaseType


def get_nonterminals(rhs: 'Rhs') -> List[Nonterminal]:
    """Return the list of all nonterminals referenced in a Rhs."""
    nonterminals = []

    if isinstance(rhs, Nonterminal):
        nonterminals.append(rhs)
    elif isinstance(rhs, Sequence):
        for elem in rhs.elements:
            nonterminals.extend(get_nonterminals(elem))
    elif isinstance(rhs, (Star, Option)):
        nonterminals.extend(get_nonterminals(rhs.rhs))

    return list(dict.fromkeys(nonterminals))


def get_literals(rhs: 'Rhs') -> List[LitTerminal]:
    """Return the list of all literals referenced in a Rhs."""
    literals = []

    if isinstance(rhs, LitTerminal):
        literals.append(rhs)
    elif isinstance(rhs, Sequence):
        for elem in rhs.elements:
            literals.extend(get_literals(elem))
    elif isinstance(rhs, (Star, Option)):
        literals.extend(get_literals(rhs.rhs))

    return list(dict.fromkeys(literals))


def is_epsilon(rhs: 'Rhs') -> bool:
    """Check if rhs represents an epsilon production (empty sequence)."""
    return isinstance(rhs, Sequence) and len(rhs.elements) == 0


def check_reachability(grammar: 'Grammar') -> Set[Nonterminal]:
    """Compute set of reachable nonterminals from start symbol."""
    if grammar.start not in grammar.rules:
        return set()

    reachable: Set[Nonterminal] = set([grammar.start])
    worklist = [grammar.start]

    while worklist:
        current = worklist.pop()
        if current in grammar.rules:
            for rule in grammar.rules[current]:
                for nt in get_nonterminals(rule.rhs):
                    if nt not in reachable:
                        reachable.add(nt)
                        worklist.append(nt)

    return reachable


def compute_nullable(grammar: 'Grammar') -> Dict[Nonterminal, bool]:
    """Compute nullable set for all nonterminals.

    A nonterminal is nullable if it can derive the empty string.
    """
    nullable: Dict[Nonterminal, bool] = {nt: False for nt in grammar.rules.keys()}

    changed = True
    while changed:
        changed = False
        for nt, rules_list in grammar.rules.items():
            if nullable[nt]:
                continue
            for rule in rules_list:
                if is_rhs_nullable(rule.rhs, nullable):
                    nullable[nt] = True
                    changed = True
                    break

    return nullable


def is_rhs_nullable(rhs: 'Rhs', nullable: Mapping[Nonterminal, bool]) -> bool:
    """Check if an RHS is nullable given current nullable set."""
    if isinstance(rhs, (LitTerminal, NamedTerminal)):
        return False
    elif isinstance(rhs, Nonterminal):
        return nullable.get(rhs, False)
    elif isinstance(rhs, Sequence):
        return all(is_rhs_nullable(elem, nullable) for elem in rhs.elements)
    elif isinstance(rhs, (Star, Option)):
        return True
    else:
        return False


# Type alias for terminal sequences used in FIRST_k and FOLLOW_k
TerminalSeq = Tuple[Terminal, ...]
TerminalSeqSet = Set[TerminalSeq]


def compute_first_k(grammar: 'Grammar', k: int = 1,
                    nullable: Optional[Dict[Nonterminal, bool]] = None) -> Dict[Nonterminal, TerminalSeqSet]:
    """Compute FIRST_k sets for all nonterminals.

    FIRST_k(A) is the set of terminal sequences of length up to k that can
    begin strings derived from A.

    When k=1, this is equivalent to traditional FIRST sets (wrapped in tuples).
    """
    if nullable is None:
        nullable = compute_nullable(grammar)

    first_k: Dict[Nonterminal, TerminalSeqSet] = {nt: set() for nt in grammar.rules.keys()}

    changed = True
    while changed:
        changed = False
        for nt, rules_list in grammar.rules.items():
            for rule in rules_list:
                new_sequences = rhs_first_k(rule.rhs, first_k, nullable, k)
                for seq in new_sequences:
                    if seq not in first_k[nt]:
                        first_k[nt].add(seq)
                        changed = True

    return first_k


def rhs_first_k(rhs: 'Rhs', first_k: Mapping[Nonterminal, TerminalSeqSet],
                nullable: Mapping[Nonterminal, bool], k: int) -> TerminalSeqSet:
    """Compute FIRST_k set for an RHS element."""
    if isinstance(rhs, (LitTerminal, NamedTerminal)):
        return {(rhs,)}
    elif isinstance(rhs, Nonterminal):
        return first_k.get(rhs, set()).copy()
    elif isinstance(rhs, Sequence):
        if not rhs.elements:
            return {()}
        # Concatenate FIRST_k of each element in sequence
        current: TerminalSeqSet = {()}
        for elem in rhs.elements:
            elem_first = rhs_first_k(elem, first_k, nullable, k)
            current = concat_k(current, elem_first, k)
            # Stop early if element is not nullable and all sequences are full
            if not is_rhs_nullable(elem, nullable) and all(len(seq) >= k for seq in current):
                break
        return current
    elif isinstance(rhs, (Star, Option)):
        result = rhs_first_k(rhs.rhs, first_k, nullable, k)
        result.add(())  # Can also derive empty
        return result
    else:
        return set()


def compute_first(grammar: 'Grammar',
                  nullable: Optional[Dict[Nonterminal, bool]] = None) -> Dict[Nonterminal, Set[Terminal]]:
    """Compute FIRST sets for all nonterminals.

    This is a convenience wrapper around compute_first_k with k=1,
    returning Set[Terminal] instead of Set[Tuple[Terminal, ...]].
    """
    first_k = compute_first_k(grammar, k=1, nullable=nullable)
    return {nt: {seq[0] for seq in seqs if seq} for nt, seqs in first_k.items()}


def rhs_first(rhs: 'Rhs', first: Mapping[Nonterminal, Set[Terminal]],
              nullable: Mapping[Nonterminal, bool]) -> Set[Terminal]:
    """Compute FIRST set for an RHS element.

    Convenience function for k=1 case, returning Set[Terminal].
    """
    if isinstance(rhs, (LitTerminal, NamedTerminal)):
        return {rhs}
    elif isinstance(rhs, Nonterminal):
        return first.get(rhs, set()).copy()
    elif isinstance(rhs, Sequence):
        result: Set[Terminal] = set()
        for elem in rhs.elements:
            result.update(rhs_first(elem, first, nullable))
            if not is_rhs_nullable(elem, nullable):
                break
        return result
    elif isinstance(rhs, (Star, Option)):
        return rhs_first(rhs.rhs, first, nullable)
    else:
        return set()


def compute_follow_k(grammar: 'Grammar', k: int = 1,
                     nullable: Optional[Dict[Nonterminal, bool]] = None,
                     first_k: Optional[Dict[Nonterminal, TerminalSeqSet]] = None) -> Dict[Nonterminal, TerminalSeqSet]:
    """Compute FOLLOW_k sets for all nonterminals.

    FOLLOW_k(A) is the set of terminal sequences of length up to k that can follow A.

    When k=1, this is equivalent to traditional FOLLOW sets (wrapped in tuples).
    """
    if nullable is None:
        nullable = compute_nullable(grammar)
    if first_k is None:
        first_k = compute_first_k(grammar, k, nullable)

    follow_k: Dict[Nonterminal, TerminalSeqSet] = {nt: set() for nt in grammar.rules.keys()}

    # Start symbol can be followed by EOF
    if grammar.start in grammar.rules:
        follow_k[grammar.start].add((NamedTerminal('$', BaseType('EOF')),))

    changed = True
    while changed:
        changed = False
        for nt, rules_list in grammar.rules.items():
            for rule in rules_list:
                updates = rhs_follow_k(rule.rhs, rule.lhs, first_k, nullable, follow_k, k)
                for follow_nt, sequences in updates.items():
                    if follow_nt not in follow_k:
                        follow_k[follow_nt] = set()
                    for seq in sequences:
                        if seq not in follow_k[follow_nt]:
                            follow_k[follow_nt].add(seq)
                            changed = True

    return follow_k


def rhs_follow_k(rhs: 'Rhs', lhs: Nonterminal,
                 first_k: Mapping[Nonterminal, TerminalSeqSet],
                 nullable: Mapping[Nonterminal, bool],
                 follow_k: Mapping[Nonterminal, TerminalSeqSet],
                 k: int) -> Dict[Nonterminal, TerminalSeqSet]:
    """Compute FOLLOW_k contributions from an RHS."""
    result: Dict[Nonterminal, TerminalSeqSet] = {}

    def add(nt: Nonterminal, sequences: TerminalSeqSet) -> None:
        if nt not in result:
            result[nt] = set()
        result[nt].update(sequences)

    if isinstance(rhs, Nonterminal):
        add(rhs, follow_k.get(lhs, set()))
    elif isinstance(rhs, Sequence):
        for i, elem in enumerate(rhs.elements):
            if isinstance(elem, Nonterminal):
                following = rhs.elements[i+1:] if i+1 < len(rhs.elements) else ()
                if following:
                    following_seq = Sequence(following)
                    first_of_following = rhs_first_k(following_seq, first_k, nullable, k)
                    add(elem, first_of_following)
                    if is_rhs_nullable(following_seq, nullable):
                        lhs_follow = follow_k.get(lhs, set())
                        combined = concat_k(first_of_following, lhs_follow, k)
                        add(elem, combined)
                else:
                    add(elem, follow_k.get(lhs, set()))
            elif isinstance(elem, (Sequence, Star, Option)):
                inner = rhs_follow_k(elem, lhs, first_k, nullable, follow_k, k)
                for nt, seqs in inner.items():
                    add(nt, seqs)
    elif isinstance(rhs, Star):
        inner = rhs_follow_k(rhs.rhs, lhs, first_k, nullable, follow_k, k)
        for nt, seqs in inner.items():
            add(nt, seqs)
        # Elements in Star can be followed by more elements
        first_of_inner = rhs_first_k(rhs.rhs, first_k, nullable, k)
        for nt in get_nonterminals(rhs.rhs):
            add(nt, first_of_inner)
    elif isinstance(rhs, Option):
        inner = rhs_follow_k(rhs.rhs, lhs, first_k, nullable, follow_k, k)
        for nt, seqs in inner.items():
            add(nt, seqs)

    return result


def rhs_follow(rhs: 'Rhs', lhs: Nonterminal,
               first: Mapping[Nonterminal, Set[Terminal]],
               nullable: Mapping[Nonterminal, bool],
               follow: Mapping[Nonterminal, Set[Terminal]]) -> Dict[Nonterminal, Set[Terminal]]:
    """Compute FOLLOW contributions from an RHS.

    Convenience function for k=1 case, returning Dict[Nonterminal, Set[Terminal]].
    """
    # Convert to k=1 format
    first_k = {nt: {(t,) for t in terms} for nt, terms in first.items()}
    follow_k = {nt: {(t,) for t in terms} for nt, terms in follow.items()}

    result_k = rhs_follow_k(rhs, lhs, first_k, nullable, follow_k, k=1)

    # Convert back to k=1 format
    return {nt: {seq[0] for seq in seqs if seq} for nt, seqs in result_k.items()}


def compute_follow(grammar: 'Grammar',
                   nullable: Optional[Dict[Nonterminal, bool]] = None,
                   first: Optional[Dict[Nonterminal, Set[Terminal]]] = None) -> Dict[Nonterminal, Set[Terminal]]:
    """Compute FOLLOW sets for all nonterminals.

    This is a convenience wrapper around compute_follow_k with k=1,
    returning Set[Terminal] instead of Set[Tuple[Terminal, ...]].
    """
    if nullable is None:
        nullable = compute_nullable(grammar)

    # Convert first to first_k format if provided
    first_k: Optional[Dict[Nonterminal, TerminalSeqSet]] = None
    if first is not None:
        first_k = {nt: {(t,) for t in terms} for nt, terms in first.items()}

    follow_k = compute_follow_k(grammar, k=1, nullable=nullable, first_k=first_k)
    return {nt: {seq[0] for seq in seqs if seq} for nt, seqs in follow_k.items()}


def concat_k(set1: Set[Tuple[Terminal, ...]], set2: Set[Tuple[Terminal, ...]], k: int) -> TerminalSeqSet:  # type: ignore
    """Concatenate two terminal sequence sets, truncating to length k."""
    result: TerminalSeqSet = set()
    for seq1 in set1:
        if len(seq1) >= k:
            result.add(seq1[:k])
        else:
            for seq2 in set2:
                combined = seq1 + seq2
                result.add(combined[:k])
    return result


# Legacy aliases for backwards compatibility
_is_rhs_elem_nullable = is_rhs_nullable
_compute_rhs_elem_first_k = rhs_first_k
_compute_rhs_elem_first = rhs_first
_compute_rhs_elem_follow = rhs_follow
_compute_rhs_elem_follow_k = rhs_follow_k
_concat_first_k_sets = concat_k
