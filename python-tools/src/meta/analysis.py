"""Grammar analysis functions.

This module provides functions for analyzing grammars including reachability,
nullable computation, FIRST/FOLLOW sets, and LL(k) checking.
"""

from typing import Dict, List, Optional, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .grammar import Grammar, Rhs, Rule

from .grammar import LitTerminal, NamedTerminal, Nonterminal, Star, Plus, Option, Sequence, Terminal, get_nonterminals


def check_reachability(grammar: 'Grammar') -> Set[Nonterminal]:
    """
    Compute set of reachable nonterminals from start symbol.

    Returns set of rule names that can be reached.
    """
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
    """
    Compute nullable set for all nonterminals.

    A nonterminal is nullable if it can derive the empty string.
    Returns dict mapping nonterminals to boolean.
    """
    nullable: Dict[Nonterminal, bool] = {}
    for nt in grammar.rules.keys():
        nullable[nt] = False

    changed = True
    while changed:
        changed = False
        for nt, rules_list in grammar.rules.items():
            if nullable[nt]:
                continue
            for rule in rules_list:
                if _is_rhs_elem_nullable(rule.rhs, nullable):
                    nullable[nt] = True
                    changed = True
                    break

    return nullable


def _is_rhs_elem_nullable(rhs: 'Rhs', nullable: Dict[Nonterminal, bool]) -> bool:
    """Check if an RHS is nullable given current nullable set."""
    if isinstance(rhs, LitTerminal) or isinstance(rhs, NamedTerminal):
        return False
    elif isinstance(rhs, Nonterminal):
        return nullable.get(rhs, False)
    elif isinstance(rhs, Sequence):
        return all(_is_rhs_elem_nullable(elem, nullable) for elem in rhs.elements)
    elif isinstance(rhs, Star) or isinstance(rhs, Option):
        return True
    elif isinstance(rhs, Plus):
        return _is_rhs_elem_nullable(rhs.rhs, nullable)
    else:
        return False


def compute_first_k(grammar: 'Grammar', k: int = 2, nullable: Optional[Dict[Nonterminal, bool]] = None) -> Dict[Nonterminal, Set[Tuple[Terminal, ...]]]:
    """
    Compute FIRST_k sets for all nonterminals.

    FIRST_k(A) is the set of terminal sequences of length up to k that can begin strings derived from A.
    Returns dict mapping nonterminals to sets of terminal tuples.
    """
    if nullable is None:
        nullable = compute_nullable(grammar)

    first_k: Dict[Nonterminal, Set[Tuple[Terminal, ...]]] = {}
    for nt in grammar.rules.keys():
        first_k[nt] = set()

    changed = True
    while changed:
        changed = False
        for nt, rules_list in grammar.rules.items():
            for rule in rules_list:
                new_sequences = _compute_rhs_elem_first_k(rule.rhs, first_k, nullable, k)
                for seq in new_sequences:
                    if seq not in first_k[nt]:
                        first_k[nt].add(seq)
                        changed = True

    return first_k


def _compute_rhs_elem_first_k(rhs: 'Rhs', first_k: Dict[Nonterminal, Set[Tuple[Terminal, ...]]],
                         nullable: Dict[Nonterminal, bool], k: int) -> Set[Tuple[Terminal, ...]]:
    """Compute FIRST_k set for an RHS."""
    result: Set[Tuple[Terminal, ...]] = set()

    if isinstance(rhs, LitTerminal):
        result.add((f'"{rhs.name}"',))
    elif isinstance(rhs, NamedTerminal):
        result.add((rhs.name,))
    elif isinstance(rhs, Nonterminal):
        result.update(first_k.get(rhs, set()))
    elif isinstance(rhs, Sequence):
        if not rhs.elements:
            result.add(())
        else:
            # Concatenate FIRST_k of each element in sequence
            current_sequences = {()}
            for elem in rhs.elements:
                elem_first = _compute_rhs_elem_first_k(elem, first_k, nullable, k)
                new_sequences = set()
                for prefix in current_sequences:
                    for suffix in elem_first:
                        combined = prefix + suffix
                        new_sequences.add(combined[:k])
                current_sequences = new_sequences
                # Only stop if all current sequences have reached length k
                if not _is_rhs_elem_nullable(elem, nullable):
                    # Check if all sequences are at length k
                    if all(len(seq) >= k for seq in current_sequences):
                        break
            result.update(current_sequences)
    elif isinstance(rhs, (Star, Option)):
        result.update(_compute_rhs_elem_first_k(rhs.rhs, first_k, nullable, k))
        result.add(())
    elif isinstance(rhs, Plus):
        result.update(_compute_rhs_elem_first_k(rhs.rhs, first_k, nullable, k))

    return result


def compute_first(grammar: 'Grammar', nullable: Optional[Dict[Nonterminal, bool]] = None) -> Dict[Nonterminal, Set[Terminal]]:
    """
    Compute FIRST sets for all nonterminals.

    FIRST(A) is the set of terminals that can begin strings derived from A.
    Returns dict mapping nonterminals to sets of Terminals.
    """
    if nullable is None:
        nullable = compute_nullable(grammar)

    first: Dict[Nonterminal, Set[Terminal]] = {}
    for nt in grammar.rules.keys():
        first[nt] = set()

    changed = True
    while changed:
        changed = False
        for nt, rules_list in grammar.rules.items():
            for rule in rules_list:
                new_terminals = _compute_rhs_elem_first(rule.rhs, first, nullable)
                for term in new_terminals:
                    if term not in first[nt]:
                        first[nt].add(term)
                        changed = True

    return first


def _compute_rhs_elem_first(rhs: 'Rhs', first: Dict[Nonterminal, Set[Terminal]], nullable: Dict[Nonterminal, bool]) -> Set[Terminal]:
    """Compute FIRST set for an RHS."""
    result: Set[Terminal] = set()
    if isinstance(rhs, LitTerminal):
        result.add(rhs)
    elif isinstance(rhs, NamedTerminal):
        result.add(rhs)
    elif isinstance(rhs, Nonterminal):
        result.update(first.get(rhs, set()))
    elif isinstance(rhs, Sequence):
        for elem in rhs.elements:
            result.update(_compute_rhs_elem_first(elem, first, nullable))
            if not _is_rhs_elem_nullable(elem, nullable):
                break
    elif isinstance(rhs, (Star, Option)):
        result.update(_compute_rhs_elem_first(rhs.rhs, first, nullable))
    elif isinstance(rhs, Plus):
        result.update(_compute_rhs_elem_first(rhs.rhs, first, nullable))
    return result


def compute_follow(grammar: 'Grammar', nullable: Optional[Dict[Nonterminal, bool]] = None,
                   first: Optional[Dict[Nonterminal, Set[Terminal]]] = None) -> Dict[Nonterminal, Set[Terminal]]:
    """
    Compute FOLLOW sets for all nonterminals.

    FOLLOW(A) is the set of terminals that can immediately follow A in any derivation.
    Returns dict mapping nonterminals to sets of Terminals.
    """
    if nullable is None:
        nullable = compute_nullable(grammar)
    if first is None:
        first = compute_first(grammar, nullable)

    follow: Dict[Nonterminal, Set[Terminal]] = {}
    for nt in grammar.rules.keys():
        follow[nt] = set()

    start_nt = Nonterminal('start')
    if start_nt in grammar.rules:
        follow[start_nt].add(NamedTerminal('$'))

    changed = True
    while changed:
        changed = False
        for nt, rules_list in grammar.rules.items():
            for rule in rules_list:
                new_follows = _compute_rhs_elem_follow(rule.rhs, rule.lhs, first, nullable, follow)
                for nt, terminals in new_follows.items():
                    if nt not in follow:
                        follow[nt] = set()
                    for term in terminals:
                        if term not in follow[nt]:
                            follow[nt].add(term)
                            changed = True

    return follow


def _compute_rhs_elem_follow(rhs: 'Rhs', lhs: Nonterminal,
                        first: Dict[Nonterminal, Set[Terminal]],
                        nullable: Dict[Nonterminal, bool],
                        follow: Dict[Nonterminal, Set[Terminal]]) -> Dict[Nonterminal, Set[Terminal]]:
    """Compute FOLLOW contributions from an RHS."""
    result: Dict[Nonterminal, Set[Terminal]] = {}

    def add_follow(nt: Nonterminal, terminals: Set[Terminal]) -> None:
        if nt not in result:
            result[nt] = set()
        result[nt].update(terminals)

    if isinstance(rhs, Nonterminal):
        add_follow(rhs, follow.get(lhs, set()))
    elif isinstance(rhs, Sequence):
        for i, elem in enumerate(rhs.elements):
            if isinstance(elem, Nonterminal):
                following = rhs.elements[i+1:] if i+1 < len(rhs.elements) else []
                if following:
                    first_of_following = _compute_rhs_elem_first(Sequence(following), first, nullable)
                    add_follow(elem, first_of_following)
                    if _is_rhs_elem_nullable(Sequence(following), nullable):
                        add_follow(elem, follow.get(lhs, set()))
                else:
                    add_follow(elem, follow.get(lhs, set()))
            elif isinstance(elem, Sequence):
                inner_follows = _compute_rhs_elem_follow(elem, lhs, first, nullable, follow)
                for nt, terminals in inner_follows.items():
                    add_follow(nt, terminals)
            elif isinstance(elem, (Star, Plus, Option)):
                inner_follows = _compute_rhs_elem_follow(elem, lhs, first, nullable, follow)
                for nt, terminals in inner_follows.items():
                    add_follow(nt, terminals)
    elif isinstance(rhs, (Star, Plus)):
        inner_follows = _compute_rhs_elem_follow(rhs.rhs, lhs, first, nullable, follow)
        for nt, terminals in inner_follows.items():
            add_follow(nt, terminals)
        first_of_inner = _compute_rhs_elem_first(rhs.rhs, first, nullable)
        inner_nts = get_nonterminals(rhs.rhs)
        for nt in inner_nts:
            add_follow(nt, first_of_inner)
    elif isinstance(rhs, Option):
        inner_follows = _compute_rhs_elem_follow(rhs.rhs, lhs, first, nullable, follow)
        for nt, terminals in inner_follows.items():
            add_follow(nt, terminals)

    return result


def check_ll_k(grammar: 'Grammar', k: int = 2) -> Tuple[bool, List[Nonterminal]]:
    """
    Check if grammar is LL(k).

    Returns (is_ll_k, conflicts) where conflicts is a list of problematic nonterminals.
    """
    nullable = grammar.compute_nullable()
    first_k = grammar.compute_first_k(k)

    conflicts = []

    for nt, rules_list in grammar.rules.items():
        if len(rules_list) <= 1:
            continue

        # Check if FIRST_k sets are disjoint
        seen_sequences: Dict[Tuple[Terminal, ...], Tuple[int, 'Rule']] = {}
        for rule_idx, rule in enumerate(rules_list):
            rule_first_k = _compute_rhs_elem_first_k(rule.rhs, first_k, nullable, k)

            for seq in rule_first_k:
                if seq in seen_sequences:
                    prev_idx, prev_rule = seen_sequences[seq]
                    conflicts.append(
                        f"{nt}: FIRST_{k} conflict on {seq}\n" +
                        f"  Rule {prev_idx}: {nt} -> {prev_rule.rhs}\n" +
                        f"  Rule {rule_idx}: {nt} -> {rule.rhs}"
                    )
                else:
                    seen_sequences[seq] = (rule_idx, rule)

    return (len(conflicts) == 0, conflicts)
