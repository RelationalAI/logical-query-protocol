"""Grammar analysis functions.

This module provides functions for analyzing grammars including reachability,
nullable computation, FIRST/FOLLOW sets, and LL(k) checking.
"""

from typing import Dict, List, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .grammar import Grammar, Rhs

from .grammar import Literal, Terminal, Nonterminal, Sequence, Star, Plus, Option


def check_reachability(grammar: 'Grammar') -> Set[str]:
    """
    Compute set of reachable nonterminals from start symbol.

    Returns set of rule names that can be reached.
    """
    if 'start' not in grammar.rules:
        return set()

    reachable: Set[str] = set(['start'])
    worklist = ['start']

    def extract_nonterminals(rhs: 'Rhs') -> List[str]:
        """Extract all nonterminal names from an RHS."""
        if isinstance(rhs, Nonterminal):
            return [rhs.name]
        elif isinstance(rhs, Sequence):
            result = []
            for elem in rhs.elements:
                result.extend(extract_nonterminals(elem))
            return result
        elif isinstance(rhs, (Star, Plus, Option)):
            return extract_nonterminals(rhs.rhs)
        else:
            return []

    while worklist:
        current = worklist.pop()
        if current in grammar.rules:
            for rule in grammar.rules[current]:
                nonterminals = extract_nonterminals(rule.rhs)
                for nt in nonterminals:
                    if nt not in reachable:
                        reachable.add(nt)
                        worklist.append(nt)

    return reachable


def get_unreachable_rules(grammar: 'Grammar') -> List[str]:
    """
    Find all rules that are unreachable from start symbol.

    Returns list of rule names that cannot be reached.
    """
    reachable = check_reachability(grammar)
    unreachable = []
    for rule_name in grammar.rule_order:
        if rule_name not in reachable:
            unreachable.append(rule_name)
    return unreachable


def compute_nullable(grammar: 'Grammar') -> Dict[str, bool]:
    """
    Compute nullable set for all nonterminals.

    A nonterminal is nullable if it can derive the empty string.
    Returns dict mapping nonterminal names to boolean.
    """
    nullable: Dict[str, bool] = {}
    for nt in grammar.rules.keys():
        nullable[nt] = False

    changed = True
    while changed:
        changed = False
        for nt_name, rules_list in grammar.rules.items():
            if nullable[nt_name]:
                continue
            for rule in rules_list:
                if _is_rhs_nullable(rule.rhs, nullable):
                    nullable[nt_name] = True
                    changed = True
                    break

    return nullable


def _is_rhs_nullable(rhs: 'Rhs', nullable: Dict[str, bool]) -> bool:
    """Check if an RHS is nullable given current nullable set."""
    if isinstance(rhs, Literal) or isinstance(rhs, Terminal):
        return False
    elif isinstance(rhs, Nonterminal):
        return nullable.get(rhs.name, False)
    elif isinstance(rhs, Sequence):
        return all(_is_rhs_nullable(elem, nullable) for elem in rhs.elements)
    elif isinstance(rhs, Star) or isinstance(rhs, Option):
        return True
    elif isinstance(rhs, Plus):
        return _is_rhs_nullable(rhs.rhs, nullable)
    else:
        return False


def compute_first_k(grammar: 'Grammar', k: int = 2, nullable: Dict[str, bool] = None) -> Dict[str, Set[Tuple[str, ...]]]:
    """
    Compute FIRST_k sets for all nonterminals.

    FIRST_k(A) is the set of terminal sequences of length up to k that can begin strings derived from A.
    Returns dict mapping nonterminal names to sets of terminal tuples.
    """
    if nullable is None:
        nullable = compute_nullable(grammar)

    first_k: Dict[str, Set[Tuple[str, ...]]] = {}
    for nt in grammar.rules.keys():
        first_k[nt] = set()

    changed = True
    while changed:
        changed = False
        for nt_name, rules_list in grammar.rules.items():
            for rule in rules_list:
                new_sequences = _compute_rhs_first_k(rule.rhs, first_k, nullable, k)
                for seq in new_sequences:
                    if seq not in first_k[nt_name]:
                        first_k[nt_name].add(seq)
                        changed = True

    return first_k


def _compute_rhs_first_k(rhs: 'Rhs', first_k: Dict[str, Set[Tuple[str, ...]]],
                         nullable: Dict[str, bool], k: int) -> Set[Tuple[str, ...]]:
    """Compute FIRST_k set for an RHS."""
    result: Set[Tuple[str, ...]] = set()

    if isinstance(rhs, Literal):
        result.add((f'"{rhs.name}"',))
    elif isinstance(rhs, Terminal):
        result.add((rhs.name,))
    elif isinstance(rhs, Nonterminal):
        result.update(first_k.get(rhs.name, set()))
    elif isinstance(rhs, Sequence):
        if not rhs.elements:
            result.add(())
        else:
            # Concatenate FIRST_k of each element in sequence
            current_sequences = {()}
            for elem in rhs.elements:
                elem_first = _compute_rhs_first_k(elem, first_k, nullable, k)
                new_sequences = set()
                for prefix in current_sequences:
                    for suffix in elem_first:
                        combined = prefix + suffix
                        new_sequences.add(combined[:k])
                current_sequences = new_sequences
                # Only stop if all current sequences have reached length k
                if not _is_rhs_nullable(elem, nullable):
                    # Check if all sequences are at length k
                    if all(len(seq) >= k for seq in current_sequences):
                        break
            result.update(current_sequences)
    elif isinstance(rhs, (Star, Option)):
        result.update(_compute_rhs_first_k(rhs.rhs, first_k, nullable, k))
        result.add(())
    elif isinstance(rhs, Plus):
        result.update(_compute_rhs_first_k(rhs.rhs, first_k, nullable, k))

    return result


def compute_first(grammar: 'Grammar', nullable: Dict[str, bool] = None) -> Dict[str, Set[str]]:
    """
    Compute FIRST sets for all nonterminals.

    FIRST(A) is the set of terminals that can begin strings derived from A.
    Returns dict mapping nonterminal names to sets of terminal names.
    """
    if nullable is None:
        nullable = compute_nullable(grammar)

    first: Dict[str, Set[str]] = {}
    for nt in grammar.rules.keys():
        first[nt] = set()

    changed = True
    while changed:
        changed = False
        for nt_name, rules_list in grammar.rules.items():
            for rule in rules_list:
                new_terminals = _compute_rhs_first(rule.rhs, first, nullable)
                for term in new_terminals:
                    if term not in first[nt_name]:
                        first[nt_name].add(term)
                        changed = True

    return first


def _compute_rhs_first(rhs: 'Rhs', first: Dict[str, Set[str]], nullable: Dict[str, bool]) -> Set[str]:
    """Compute FIRST set for an RHS."""
    result: Set[str] = set()
    if isinstance(rhs, Literal):
        result.add(f'"{rhs.name}"')
    elif isinstance(rhs, Terminal):
        result.add(rhs.name)
    elif isinstance(rhs, Nonterminal):
        result.update(first.get(rhs.name, set()))
    elif isinstance(rhs, Sequence):
        for elem in rhs.elements:
            result.update(_compute_rhs_first(elem, first, nullable))
            if not _is_rhs_nullable(elem, nullable):
                break
    elif isinstance(rhs, (Star, Option)):
        result.update(_compute_rhs_first(rhs.rhs, first, nullable))
    elif isinstance(rhs, Plus):
        result.update(_compute_rhs_first(rhs.rhs, first, nullable))
    return result


def compute_follow(grammar: 'Grammar', nullable: Dict[str, bool] = None,
                   first: Dict[str, Set[str]] = None) -> Dict[str, Set[str]]:
    """
    Compute FOLLOW sets for all nonterminals.

    FOLLOW(A) is the set of terminals that can immediately follow A in any derivation.
    Returns dict mapping nonterminal names to sets of terminal names.
    """
    if nullable is None:
        nullable = compute_nullable(grammar)
    if first is None:
        first = compute_first(grammar, nullable)

    follow: Dict[str, Set[str]] = {}
    for nt in grammar.rules.keys():
        follow[nt] = set()

    if 'start' in grammar.rules:
        follow['start'].add('$')

    changed = True
    while changed:
        changed = False
        for nt_name, rules_list in grammar.rules.items():
            for rule in rules_list:
                new_follows = _compute_rhs_follow(rule.rhs, rule.lhs.name, first, nullable, follow)
                for nt, terminals in new_follows.items():
                    for term in terminals:
                        if term not in follow[nt]:
                            follow[nt].add(term)
                            changed = True

    return follow


def _compute_rhs_follow(rhs: 'Rhs', lhs_name: str,
                        first: Dict[str, Set[str]],
                        nullable: Dict[str, bool],
                        follow: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    """Compute FOLLOW contributions from an RHS."""
    result: Dict[str, Set[str]] = {}

    def add_follow(nt: str, terminals: Set[str]) -> None:
        if nt not in result:
            result[nt] = set()
        result[nt].update(terminals)

    if isinstance(rhs, Sequence):
        for i, elem in enumerate(rhs.elements):
            if isinstance(elem, Nonterminal):
                following = Sequence(rhs.elements[i+1:]) if i+1 < len(rhs.elements) else Sequence([])
                if following.elements:
                    first_of_following = _compute_rhs_first(following, first, nullable)
                    add_follow(elem.name, first_of_following)
                    if _is_rhs_nullable(following, nullable):
                        add_follow(elem.name, follow.get(lhs_name, set()))
                else:
                    add_follow(elem.name, follow.get(lhs_name, set()))
            elif isinstance(elem, (Star, Plus, Option)):
                inner_follows = _compute_rhs_follow(elem, lhs_name, first, nullable, follow)
                for nt, terminals in inner_follows.items():
                    add_follow(nt, terminals)

    elif isinstance(rhs, Nonterminal):
        add_follow(rhs.name, follow.get(lhs_name, set()))
    elif isinstance(rhs, (Star, Plus)):
        inner_follows = _compute_rhs_follow(rhs.rhs, lhs_name, first, nullable, follow)
        for nt, terminals in inner_follows.items():
            add_follow(nt, terminals)
        first_of_inner = _compute_rhs_first(rhs.rhs, first, nullable)
        inner_nts = _extract_nonterminals_from_rhs(rhs.rhs)
        for nt in inner_nts:
            add_follow(nt, first_of_inner)
    elif isinstance(rhs, Option):
        inner_follows = _compute_rhs_follow(rhs.rhs, lhs_name, first, nullable, follow)
        for nt, terminals in inner_follows.items():
            add_follow(nt, terminals)

    return result


def _extract_nonterminals_from_rhs(rhs: 'Rhs') -> List[str]:
    """Extract all nonterminal names from an RHS."""
    if isinstance(rhs, Nonterminal):
        return [rhs.name]
    elif isinstance(rhs, Sequence):
        result = []
        for elem in rhs.elements:
            result.extend(_extract_nonterminals_from_rhs(elem))
        return result
    elif isinstance(rhs, (Star, Plus, Option)):
        return _extract_nonterminals_from_rhs(rhs.rhs)
    else:
        return []


def check_ll_k(grammar: 'Grammar', k: int = 2) -> Tuple[bool, List[str]]:
    """
    Check if grammar is LL(k).

    Returns (is_ll_k, conflicts) where conflicts is a list of problematic nonterminals.
    """
    nullable = compute_nullable(grammar)
    first_k = compute_first_k(grammar, k, nullable)

    conflicts = []

    for nt_name, rules_list in grammar.rules.items():
        if len(rules_list) <= 1:
            continue

        # Check if FIRST_k sets are disjoint
        seen_sequences: Dict[Tuple[str, ...], Tuple[int, 'Rule']] = {}
        for rule_idx, rule in enumerate(rules_list):
            rule_first_k = _compute_rhs_first_k(rule.rhs, first_k, nullable, k)

            for seq in rule_first_k:
                if seq in seen_sequences:
                    prev_idx, prev_rule = seen_sequences[seq]
                    conflicts.append(
                        f"{nt_name}: FIRST_{k} conflict on {seq}\n" +
                        f"  Rule {prev_idx}: {nt_name} -> {prev_rule.rhs}\n" +
                        f"  Rule {rule_idx}: {nt_name} -> {rule.rhs}"
                    )
                else:
                    seen_sequences[seq] = (rule_idx, rule)

    return (len(conflicts) == 0, conflicts)
