"""Grammar analysis functions.

This module provides functions for analyzing grammars including reachability,
nullable computation, FIRST/FOLLOW sets, and LL(k) checking.
"""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Set, Tuple
from .grammar import Grammar, Rhs, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence, Terminal
from .target import BaseType

# Type alias for terminal sequences used in FIRST_k and FOLLOW_k
TerminalSeq = Tuple[Terminal, ...]
TerminalSeqSet = Set[TerminalSeq]


@dataclass
class GrammarAnalysis:
    grammar: 'Grammar'

    # Cached analysis results
    _reachable_cache: Optional[Set[Nonterminal]] = field(default=None, init=False, repr=False)
    _nullable_cache: Optional[Dict[Nonterminal, bool]] = field(default=None, init=False, repr=False)
    _first_cache: Optional[Dict[Nonterminal, Set[Terminal]]] = field(default=None, init=False, repr=False)
    _follow_cache: Optional[Dict[Nonterminal, Set[Terminal]]] = field(default=None, init=False, repr=False)

    # Instance methods that use caching and delegate to static methods

    def compute_reachability(self) -> Set[Nonterminal]:
        """Compute set of reachable nonterminals from start symbol (cached)."""
        if self._reachable_cache is None:
            self._reachable_cache = GrammarAnalysis.compute_reachability_static(self.grammar)
        return self._reachable_cache

    def compute_nullable(self) -> Dict[Nonterminal, bool]:
        """Compute nullable set for all nonterminals (cached)."""
        if self._nullable_cache is None:
            self._nullable_cache = GrammarAnalysis.compute_nullable_static(self.grammar)
        return self._nullable_cache

    def compute_first(self) -> Dict[Nonterminal, Set[Terminal]]:
        """Compute FIRST sets for all nonterminals (cached)."""
        if self._first_cache is None:
            self._first_cache = GrammarAnalysis.compute_first_static(self.grammar, self.compute_nullable())
        return self._first_cache

    def compute_follow(self) -> Dict[Nonterminal, Set[Terminal]]:
        """Compute FOLLOW sets for all nonterminals (cached)."""
        if self._follow_cache is None:
            self._follow_cache = GrammarAnalysis.compute_follow_static(
                self.grammar, self.compute_nullable(), self.compute_first()
            )
        return self._follow_cache

    def compute_first_k(self, k: int = 2) -> Dict[Nonterminal, TerminalSeqSet]:
        """Compute FIRST_k sets for all nonterminals (not cached for k>1)."""
        return GrammarAnalysis.compute_first_k_static(self.grammar, k, self.compute_nullable())

    def compute_follow_k(self, k: int = 2) -> Dict[Nonterminal, TerminalSeqSet]:
        """Compute FOLLOW_k sets for all nonterminals (not cached for k>1)."""
        return GrammarAnalysis.compute_follow_k_static(
            self.grammar, k, self.compute_nullable(), self.compute_first_k(k)
        )

    def nullable(self, rhs: 'Rhs') -> bool:
        """Check if an RHS is nullable."""
        return GrammarAnalysis.is_rhs_nullable(rhs, self.compute_nullable())

    def first(self, rhs: 'Rhs') -> Set[Terminal]:
        """Compute FIRST set for an RHS."""
        return GrammarAnalysis.rhs_first(rhs, self.compute_first(), self.compute_nullable())

    def first_k(self, k: int, rhs: 'Rhs') -> TerminalSeqSet:
        """Compute FIRST_k set for an RHS."""
        return GrammarAnalysis.rhs_first_k(rhs, self.compute_first_k(k), self.compute_nullable(), k)

    def follow(self, nt: Nonterminal) -> Set[Terminal]:
        """Compute FOLLOW set for a nonterminal."""
        return self.compute_follow().get(nt, set())

    def follow_k(self, k: int, rhs: 'Rhs') -> TerminalSeqSet:
        """Compute FOLLOW_k set for an RHS."""
        if isinstance(rhs, Nonterminal):
            return self.compute_follow_k(k).get(rhs, set())
        elif isinstance(rhs, (Option, Star)):
            return self.follow_k(k, rhs.rhs)
        else:
            raise ValueError(f"Unexpected rhs {rhs}: follow_k unimplemented")

    def first_k_with_follow(self, k: int, following: 'Rhs', lhs: Nonterminal) -> TerminalSeqSet:
        """Compute FIRST_k(following) concatenated with FOLLOW_k(lhs).

        Used for Option and Star disambiguation.
        """
        first_of_following = self.first_k(k, following)
        if self.nullable(following):
            follow_of_lhs = self.follow_k(k, lhs)
            return GrammarAnalysis.concat_k(first_of_following, follow_of_lhs, k)
        return first_of_following

    @staticmethod
    def get_nonterminals(rhs: 'Rhs') -> List[Nonterminal]:
        """Return the list of all nonterminals referenced in a Rhs."""
        nonterminals = []

        if isinstance(rhs, Nonterminal):
            nonterminals.append(rhs)
        elif isinstance(rhs, Sequence):
            for elem in rhs.elements:
                nonterminals.extend(GrammarAnalysis.get_nonterminals(elem))
        elif isinstance(rhs, (Star, Option)):
            nonterminals.extend(GrammarAnalysis.get_nonterminals(rhs.rhs))

        return list(dict.fromkeys(nonterminals))

    @staticmethod
    def get_literals(rhs: 'Rhs') -> List[LitTerminal]:
        """Return the list of all literals referenced in a Rhs."""
        literals = []

        if isinstance(rhs, LitTerminal):
            literals.append(rhs)
        elif isinstance(rhs, Sequence):
            for elem in rhs.elements:
                literals.extend(GrammarAnalysis.get_literals(elem))
        elif isinstance(rhs, (Star, Option)):
            literals.extend(GrammarAnalysis.get_literals(rhs.rhs))

        return list(dict.fromkeys(literals))

    @staticmethod
    def is_epsilon(rhs: 'Rhs') -> bool:
        """Check if rhs represents an epsilon production (empty sequence)."""
        return isinstance(rhs, Sequence) and len(rhs.elements) == 0

    def partition_nonterminals_by_reachability(self) -> Tuple[List[Nonterminal], List[Nonterminal]]:
        """Partition nonterminals into reachable and unreachable.

        Returns a tuple of:
            - reachable: List of reachable nonterminals in preorder traversal
            - unreachable: List of unreachable nonterminals (sorted by name)
        """
        visited: Set[Nonterminal] = set()
        reachable: List[Nonterminal] = []

        def visit(A: Nonterminal) -> None:
            """Visit nonterminal and its dependencies in preorder."""
            if A in visited or A not in self.grammar.rules:
                return
            visited.add(A)
            reachable.append(A)
            for rule in self.grammar.rules[A]:
                for B in GrammarAnalysis.get_nonterminals(rule.rhs):
                    visit(B)

        visit(self.grammar.start)

        unreachable = sorted(
            [nt for nt in self.grammar.rules.keys() if nt not in visited],
            key=lambda nt: nt.name
        )

        return reachable, unreachable

    @staticmethod
    def compute_reachability_static(grammar: 'Grammar') -> Set[Nonterminal]:
        """Compute set of reachable nonterminals from start symbol."""
        if grammar.start not in grammar.rules:
            return set()

        reachable: Set[Nonterminal] = set([grammar.start])
        worklist = [grammar.start]

        while worklist:
            current = worklist.pop()
            if current in grammar.rules:
                for rule in grammar.rules[current]:
                    for nt in GrammarAnalysis.get_nonterminals(rule.rhs):
                        if nt not in reachable:
                            reachable.add(nt)
                            worklist.append(nt)

        return reachable

    @staticmethod
    def is_rhs_nullable(rhs: 'Rhs', nullable: Mapping[Nonterminal, bool]) -> bool:
        """Check if an RHS is nullable given current nullable set."""
        if isinstance(rhs, (LitTerminal, NamedTerminal)):
            return False
        elif isinstance(rhs, Nonterminal):
            return nullable.get(rhs, False)
        elif isinstance(rhs, Sequence):
            return all(GrammarAnalysis.is_rhs_nullable(elem, nullable) for elem in rhs.elements)
        elif isinstance(rhs, (Star, Option)):
            return True
        else:
            return False

    @staticmethod
    def compute_nullable_static(grammar: 'Grammar') -> Dict[Nonterminal, bool]:
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
                    if GrammarAnalysis.is_rhs_nullable(rule.rhs, nullable):
                        nullable[nt] = True
                        changed = True
                        break

        return nullable

    @staticmethod
    def concat_k(set1: Iterable[Tuple[Terminal, ...]], set2: Iterable[Tuple[Terminal, ...]], k: int) -> TerminalSeqSet:
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

    @staticmethod
    def rhs_first_k(rhs: 'Rhs', first_k: Mapping[Nonterminal, Iterable[TerminalSeq]],
                    nullable: Mapping[Nonterminal, bool], k: int) -> TerminalSeqSet:
        """Compute FIRST_k set for an RHS element."""
        if isinstance(rhs, (LitTerminal, NamedTerminal)):
            return {(rhs,)}
        elif isinstance(rhs, Nonterminal):
            return set(first_k.get(rhs, set()))
        elif isinstance(rhs, Sequence):
            if not rhs.elements:
                return {()}
            # Concatenate FIRST_k of each element in sequence
            current: TerminalSeqSet = {()}
            for elem in rhs.elements:
                elem_first = GrammarAnalysis.rhs_first_k(elem, first_k, nullable, k)
                current = GrammarAnalysis.concat_k(current, elem_first, k)
                # Stop early if element is not nullable and all sequences are full
                if not GrammarAnalysis.is_rhs_nullable(elem, nullable) and all(len(seq) >= k for seq in current):
                    break
            return current
        elif isinstance(rhs, (Star, Option)):
            result = GrammarAnalysis.rhs_first_k(rhs.rhs, first_k, nullable, k)
            result.add(())  # Can also derive empty
            return result
        else:
            return set()

    @staticmethod
    def compute_first_k_static(grammar: 'Grammar', k: int = 1,
                               nullable: Optional[Dict[Nonterminal, bool]] = None) -> Dict[Nonterminal, TerminalSeqSet]:
        """Compute FIRST_k sets for all nonterminals.

        FIRST_k(A) is the set of terminal sequences of length up to k that can
        begin strings derived from A.

        When k=1, this is equivalent to traditional FIRST sets (wrapped in tuples).
        """
        if nullable is None:
            nullable = GrammarAnalysis.compute_nullable_static(grammar)

        first_k: Dict[Nonterminal, TerminalSeqSet] = {nt: set() for nt in grammar.rules.keys()}

        changed = True
        while changed:
            changed = False
            for nt, rules_list in grammar.rules.items():
                for rule in rules_list:
                    new_sequences = GrammarAnalysis.rhs_first_k(rule.rhs, first_k, nullable, k)
                    for seq in new_sequences:
                        if seq not in first_k[nt]:
                            first_k[nt].add(seq)
                            changed = True

        return first_k

    @staticmethod
    def rhs_first(rhs: 'Rhs', first: Mapping[Nonterminal, Iterable[Terminal]],
                  nullable: Mapping[Nonterminal, bool]) -> Set[Terminal]:
        """Compute FIRST set for an RHS element.

        Convenience function for k=1 case, returning Set[Terminal].
        """
        if isinstance(rhs, (LitTerminal, NamedTerminal)):
            return {rhs}
        elif isinstance(rhs, Nonterminal):
            return set(first.get(rhs, set()))
        elif isinstance(rhs, Sequence):
            result: Set[Terminal] = set()
            for elem in rhs.elements:
                result.update(GrammarAnalysis.rhs_first(elem, first, nullable))
                if not GrammarAnalysis.is_rhs_nullable(elem, nullable):
                    break
            return result
        elif isinstance(rhs, (Star, Option)):
            return GrammarAnalysis.rhs_first(rhs.rhs, first, nullable)
        else:
            return set()

    @staticmethod
    def compute_first_static(grammar: 'Grammar',
                             nullable: Optional[Dict[Nonterminal, bool]] = None) -> Dict[Nonterminal, Set[Terminal]]:
        """Compute FIRST sets for all nonterminals.

        This is a convenience wrapper around compute_first_k with k=1,
        returning Set[Terminal] instead of Set[Tuple[Terminal, ...]].
        """
        first_k = GrammarAnalysis.compute_first_k_static(grammar, k=1, nullable=nullable)
        return {nt: {seq[0] for seq in seqs if seq} for nt, seqs in first_k.items()}

    @staticmethod
    def rhs_follow_k(rhs: 'Rhs', lhs: Nonterminal,
                     first_k: Mapping[Nonterminal, Iterable[TerminalSeq]],
                     nullable: Mapping[Nonterminal, bool],
                     follow_k: Mapping[Nonterminal, Iterable[TerminalSeq]],
                     k: int) -> Dict[Nonterminal, TerminalSeqSet]:
        """Compute FOLLOW_k contributions from an RHS."""
        result: Dict[Nonterminal, TerminalSeqSet] = {}

        def add(nt: Nonterminal, sequences: Iterable[TerminalSeq]) -> None:
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
                        first_of_following = GrammarAnalysis.rhs_first_k(following_seq, first_k, nullable, k)
                        add(elem, first_of_following)
                        if GrammarAnalysis.is_rhs_nullable(following_seq, nullable):
                            lhs_follow = follow_k.get(lhs, set())
                            combined = GrammarAnalysis.concat_k(first_of_following, lhs_follow, k)
                            add(elem, combined)
                    else:
                        add(elem, follow_k.get(lhs, set()))
                elif isinstance(elem, (Sequence, Star, Option)):
                    inner = GrammarAnalysis.rhs_follow_k(elem, lhs, first_k, nullable, follow_k, k)
                    for nt, seqs in inner.items():
                        add(nt, seqs)
        elif isinstance(rhs, Star):
            inner = GrammarAnalysis.rhs_follow_k(rhs.rhs, lhs, first_k, nullable, follow_k, k)
            for nt, seqs in inner.items():
                add(nt, seqs)
            # Elements in Star can be followed by more elements
            first_of_inner = GrammarAnalysis.rhs_first_k(rhs.rhs, first_k, nullable, k)
            for nt in GrammarAnalysis.get_nonterminals(rhs.rhs):
                add(nt, first_of_inner)
        elif isinstance(rhs, Option):
            inner = GrammarAnalysis.rhs_follow_k(rhs.rhs, lhs, first_k, nullable, follow_k, k)
            for nt, seqs in inner.items():
                add(nt, seqs)

        return result

    @staticmethod
    def compute_follow_k_static(grammar: 'Grammar', k: int = 1,
                                nullable: Optional[Dict[Nonterminal, bool]] = None,
                                first_k: Optional[Dict[Nonterminal, TerminalSeqSet]] = None) -> Dict[Nonterminal, TerminalSeqSet]:
        """Compute FOLLOW_k sets for all nonterminals.

        FOLLOW_k(A) is the set of terminal sequences of length up to k that can follow A.

        When k=1, this is equivalent to traditional FOLLOW sets (wrapped in tuples).
        """
        if nullable is None:
            nullable = GrammarAnalysis.compute_nullable_static(grammar)
        if first_k is None:
            first_k = GrammarAnalysis.compute_first_k_static(grammar, k, nullable)

        follow_k: Dict[Nonterminal, TerminalSeqSet] = {nt: set() for nt in grammar.rules.keys()}

        # Start symbol can be followed by EOF
        if grammar.start in grammar.rules:
            follow_k[grammar.start].add((NamedTerminal('$', BaseType('EOF')),))

        changed = True
        while changed:
            changed = False
            for nt, rules_list in grammar.rules.items():
                for rule in rules_list:
                    updates: Dict[Nonterminal, TerminalSeqSet] = GrammarAnalysis.rhs_follow_k(rule.rhs, rule.lhs, first_k, nullable, follow_k, k)
                    for follow_nt, sequences in updates.items():
                        if follow_nt not in follow_k:
                            follow_k[follow_nt] = set()
                        for seq in sequences:
                            if seq not in follow_k[follow_nt]:
                                follow_k[follow_nt].add(seq)
                                changed = True

        return follow_k

    @staticmethod
    def rhs_follow(rhs: 'Rhs', lhs: Nonterminal,
                   first: Mapping[Nonterminal, Iterable[Terminal]],
                   nullable: Mapping[Nonterminal, bool],
                   follow: Mapping[Nonterminal, Iterable[Terminal]]) -> Dict[Nonterminal, Set[Terminal]]:
        """Compute FOLLOW contributions from an RHS.

        Convenience function for k=1 case, returning Dict[Nonterminal, Set[Terminal]].
        """
        # Convert to k=1 format
        first_k = {nt: {(t,) for t in terms} for nt, terms in first.items()}
        follow_k = {nt: {(t,) for t in terms} for nt, terms in follow.items()}

        result_k = GrammarAnalysis.rhs_follow_k(rhs, lhs, first_k, nullable, follow_k, k=1)

        # Convert back to k=1 format
        return {nt: {seq[0] for seq in seqs if seq} for nt, seqs in result_k.items()}

    @staticmethod
    def compute_follow_static(grammar: 'Grammar',
                              nullable: Optional[Dict[Nonterminal, bool]] = None,
                              first: Optional[Dict[Nonterminal, Set[Terminal]]] = None) -> Dict[Nonterminal, Set[Terminal]]:
        """Compute FOLLOW sets for all nonterminals.

        This is a convenience wrapper around compute_follow_k with k=1,
        returning Set[Terminal] instead of Set[Tuple[Terminal, ...]].
        """
        if nullable is None:
            nullable = GrammarAnalysis.compute_nullable_static(grammar)

        # Convert first to first_k format if provided
        first_k: Optional[Dict[Nonterminal, TerminalSeqSet]] = None
        if first is not None:
            first_k = {nt: {(t,) for t in terms} for nt, terms in first.items()}

        follow_k = GrammarAnalysis.compute_follow_k_static(grammar, k=1, nullable=nullable, first_k=first_k)
        return {nt: {seq[0] for seq in seqs if seq} for nt, seqs in follow_k.items()}
