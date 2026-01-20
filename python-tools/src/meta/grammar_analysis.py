"""Grammar analysis functions.

This module provides functions for analyzing grammars including reachability,
nullable computation, FIRST/FOLLOW sets, and LL(k) checking.
"""

from dataclasses import dataclass, field
from functools import cached_property
from typing import Dict, Iterable, List, Mapping, Optional, Set, Tuple
from .grammar import Grammar, Rhs, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence, Terminal
from .target import BaseType
from .grammar_utils import get_nonterminals

# Type alias for terminal sequences used in FIRST_k and FOLLOW_k
TerminalSeq = Tuple[Terminal, ...]
TerminalSeqSet = Set[TerminalSeq]


@dataclass
class GrammarAnalysis:
    grammar: 'Grammar'

    # Analysis computations use a two-tier pattern:
    # 1. Static methods (compute_X_static) are pure functions for testing
    # 2. Instance properties (X) provide lazy-loaded cached results
    #
    # Properties: reachability, nullable, first, follow (cached via @cached_property)
    # Methods: compute_first_k(k), compute_follow_k(k) (not cached, vary by k)
    # Helpers: is_nullable(rhs), first_of(rhs), etc. (convenience wrappers)

    @cached_property
    def reachability(self) -> Set[Nonterminal]:
        """Compute set of reachable nonterminals from start symbol (cached via @cached_property)."""
        return GrammarAnalysis.compute_reachability_static(self.grammar)

    @cached_property
    def nullable(self) -> Dict[Nonterminal, bool]:
        """Compute nullable set for all nonterminals (cached via @cached_property)."""
        return GrammarAnalysis.compute_nullable_static(self.grammar)

    @cached_property
    def first(self) -> Dict[Nonterminal, Set[Terminal]]:
        """Compute FIRST sets for all nonterminals (cached via @cached_property)."""
        return GrammarAnalysis.compute_first_static(self.grammar, self.nullable)

    @cached_property
    def follow(self) -> Dict[Nonterminal, Set[Terminal]]:
        """Compute FOLLOW sets for all nonterminals (cached via @cached_property)."""
        return GrammarAnalysis.compute_follow_static(self.grammar, self.nullable, self.first)

    def compute_first_k(self, k: int = 2) -> Dict[Nonterminal, TerminalSeqSet]:
        """Compute FIRST_k sets for all nonterminals (not cached for k>1)."""
        return GrammarAnalysis.compute_first_k_static(self.grammar, k, self.nullable)

    def compute_follow_k(self, k: int = 2) -> Dict[Nonterminal, TerminalSeqSet]:
        """Compute FOLLOW_k sets for all nonterminals (not cached for k>1)."""
        return GrammarAnalysis.compute_follow_k_static(
            self.grammar, k, self.nullable, self.compute_first_k(k)
        )

    def is_nullable(self, rhs: 'Rhs') -> bool:
        """Check if an RHS is nullable."""
        return GrammarAnalysis.is_rhs_nullable(rhs, self.nullable)

    def first_of(self, rhs: 'Rhs') -> Set[Terminal]:
        """Compute FIRST set for an RHS."""
        return GrammarAnalysis.rhs_first(rhs, self.first, self.nullable)

    def first_k_of(self, k: int, rhs: 'Rhs') -> TerminalSeqSet:
        """Compute FIRST_k set for an RHS."""
        return GrammarAnalysis.rhs_first_k(rhs, self.compute_first_k(k), self.nullable, k)

    def follow_of(self, nt: Nonterminal) -> Set[Terminal]:
        """Compute FOLLOW set for a nonterminal."""
        return self.follow.get(nt, set())

    def follow_k_of(self, k: int, rhs: 'Rhs') -> TerminalSeqSet:
        """Compute FOLLOW_k set for an RHS."""
        if isinstance(rhs, Nonterminal):
            return self.compute_follow_k(k).get(rhs, set())
        elif isinstance(rhs, (Option, Star)):
            return self.follow_k_of(k, rhs.rhs)
        else:
            raise ValueError(f"Unexpected rhs {rhs}: follow_k unimplemented")

    def first_k_with_follow(self, k: int, following: 'Rhs', lhs: Nonterminal) -> TerminalSeqSet:
        """Compute FIRST_k(following) concatenated with FOLLOW_k(lhs).

        Used for Option and Star disambiguation.
        """
        first_of_following = self.first_k_of(k, following)
        if self.is_nullable(following):
            follow_of_lhs = self.follow_k_of(k, lhs)
            return GrammarAnalysis.concat_k(first_of_following, follow_of_lhs, k)
        return first_of_following



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
                for B in get_nonterminals(rule.rhs):
                    visit(B)

        visit(self.grammar.start)

        unreachable = sorted(
            [nt for nt in self.grammar.rules.keys() if nt not in visited],
            key=lambda nt: nt.name
        )

        return reachable, unreachable

    @staticmethod
    def compute_reachability_static(grammar: 'Grammar') -> Set[Nonterminal]:
        """Compute set of reachable nonterminals from start symbol.

        A nonterminal is reachable if there exists a derivation from the start symbol
        that includes that nonterminal.

        Args:
            grammar: Grammar to analyze

        Returns:
            Set of all nonterminals reachable from the grammar's start symbol.

        Example:
            For grammar with rules S -> A B, A -> "a", B -> C, C -> "c", D -> "d":
            - Reachable: {S, A, B, C}
            - Unreachable: {D}
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

    @staticmethod
    def is_rhs_nullable(rhs: 'Rhs', nullable: Mapping[Nonterminal, bool]) -> bool:
        """Check if an RHS is nullable given current nullable set.

        An RHS is nullable if it can derive the empty string.

        This is a pure checking function - it does not modify the nullable map.
        The nullable map is computed by compute_nullable_static() using fixed-point
        iteration, which repeatedly calls this function until no changes occur.

        Args:
            rhs: RHS element to check (Terminal, Nonterminal, Sequence, Star, or Option)
            nullable: Precomputed nullable information for nonterminals

        Returns:
            True if rhs can derive the empty string, False otherwise.

        Example:
            - Terminal: always False
            - Nonterminal: True if nonterminal is in nullable set
            - Sequence [A, B]: True if both A and B are nullable
            - Star A*: always True (can match zero times)
            - Option A?: always True (can be omitted)
        """
        if isinstance(rhs, Terminal):
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

        Uses fixed-point iteration: repeatedly checks each rule's RHS with
        is_rhs_nullable() and updates the nullable map until no changes occur.
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
        """Concatenate two terminal sequence sets, truncating to length k.

        Args:
            set1: First set of terminal sequences
            set2: Second set of terminal sequences
            k: Maximum length of result sequences

        Returns:
            Set of all concatenations of seq1+seq2 for seq1 in set1, seq2 in set2,
            truncated to length k. If seq1 already has length k or more, seq2 is ignored.

        Example:
            >>> t1, t2, t3 = LitTerminal('a'), LitTerminal('b'), LitTerminal('c')
            >>> set1 = {(t1,), (t1, t2)}
            >>> set2 = {(t1,), (t2,)}
            >>> result = concat_k(set1, set2, k=2)
            >>> # Result: {(t1, t1), (t1, t2)} from (t1,)+(t1,), (t1,)+(t2,); (t1,t2) already at k=2 length
        """
        result: TerminalSeqSet = set()
        for seq1 in set1:
            if len(seq1) >= k:
                result.add(seq1[:k])
                continue
            needed = k - len(seq1)
            for seq2 in set2:
                result.add(seq1 + seq2[:needed])
        return result

    @staticmethod
    def rhs_first_k(rhs: 'Rhs', first_k: Mapping[Nonterminal, Iterable[TerminalSeq]],
                    nullable: Mapping[Nonterminal, bool], k: int) -> TerminalSeqSet:
        """Compute FIRST_k set for an RHS element.

        Args:
            rhs: RHS element to analyze (Terminal, Nonterminal, Sequence, Star, or Option)
            first_k: Precomputed FIRST_k sets for nonterminals
            nullable: Precomputed nullable information for nonterminals
            k: Maximum lookahead length

        Returns:
            Set of terminal sequences of length up to k that can begin strings derived from rhs.

        Examples:
            Sequence A B where A is not nullable:
            - FIRST_k(A) = {(t1,), (t2, t3)}, FIRST_k(B) = {(t4,)}
            - FIRST_k(A B) = {(t1, t4), (t2, t3)} (B contributes only after A's sequences are full)

            Sequence A B where A is nullable:
            - FIRST_k(A) = {(t1,), ()}, FIRST_k(B) = {(t4,)}
            - FIRST_k(A B) = {(t1, t4), (t4,)} (includes sequences from B because A can derive ε)
        """
        if isinstance(rhs, Terminal):
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
                # Stop early if element is not nullable and all sequences are full.
                # We check nullable explicitly rather than checking if () is in elem_first because
                # during fixed-point iteration, () may not yet have propagated to elem_first even
                # though elem is nullable. The precomputed nullable mapping is always correct.
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

        Args:
            grammar: Grammar to analyze
            k: Maximum lookahead length (default 1)
            nullable: Precomputed nullable information (computed if not provided)

        Returns:
            Dictionary mapping each nonterminal to its FIRST_k set.

        Example:
            For grammar with rules A -> "x" B; B -> "y" | ε:
            - FIRST_1(A) = {("x",)}
            - FIRST_1(B) = {("y",), ()}
            - FIRST_2(A) = {("x", "y"), ("x",)}
            - k=1 is equivalent to traditional FIRST sets (wrapped in tuples)
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

        Convenience function for k=1 case, returning Set[Terminal] instead of
        Set[Tuple[Terminal, ...]]. Provides a simpler interface for the common
        single-token lookahead case.
        """
        if isinstance(rhs, Terminal):
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
                     follow_k: Dict[Nonterminal, TerminalSeqSet],
                     k: int) -> Dict[Nonterminal, TerminalSeqSet]:
        """Compute FOLLOW_k contributions from an RHS.

        Analyzes an RHS and determines what terminal sequences can follow each nonterminal
        appearing in that RHS.

        Args:
            rhs: RHS element to analyze
            lhs: Left-hand side nonterminal of the rule containing this RHS
            first_k: Precomputed FIRST_k sets for nonterminals
            nullable: Precomputed nullable information for nonterminals
            follow_k: Current FOLLOW_k sets (being computed iteratively)
            k: Maximum lookahead length

        Returns:
            Dictionary mapping nonterminals in rhs to sets of terminal sequences
            that can follow them.

        Example:
            For rule S -> A B C:
            - FOLLOW_k(A) includes FIRST_k(B C)
            - If B C is nullable, FOLLOW_k(A) also includes FOLLOW_k(S)
            - FOLLOW_k(B) includes FIRST_k(C)
            - If C is nullable, FOLLOW_k(B) also includes FOLLOW_k(S)
            - FOLLOW_k(C) includes FOLLOW_k(S)

        Note: FOLLOW_k(X) is the union of contributions from all rules where X appears
        in the RHS, computed iteratively until a fixed point is reached.
        """
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
            for nt in get_nonterminals(rhs.rhs):
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

        FOLLOW_k(A) is the set of terminal sequences of length up to k that can follow A
        in any derivation from the start symbol.

        Args:
            grammar: Grammar to analyze
            k: Maximum lookahead length (default 1)
            nullable: Precomputed nullable information (computed if not provided)
            first_k: Precomputed FIRST_k sets (computed if not provided)

        Returns:
            Dictionary mapping each nonterminal to its FOLLOW_k set.

        Example:
            For grammar with rules S -> A B $, A -> "a", B -> "b":
            - FOLLOW_1(A) = {("b",)}
            - FOLLOW_1(B) = {($,)}  where $ is EOF
            - FOLLOW_2(A) = {("b", $)}
            - k=1 is equivalent to traditional FOLLOW sets (wrapped in tuples)
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
        first_k: Dict[Nonterminal, TerminalSeqSet] = {nt: {(t,) for t in terms} for nt, terms in first.items()}
        follow_k: Dict[Nonterminal, TerminalSeqSet] = {nt: {(t,) for t in terms} for nt, terms in follow.items()}

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
        # Must include empty tuple () for nullable nonterminals
        first_k: Optional[Dict[Nonterminal, TerminalSeqSet]] = None
        if first is not None:
            first_k = {}
            for nt, terms in first.items():
                first_k[nt] = {(t,) for t in terms}
                if nullable.get(nt, False):
                    first_k[nt].add(())

        follow_k = GrammarAnalysis.compute_follow_k_static(grammar, k=1, nullable=nullable, first_k=first_k)
        return {nt: {seq[0] for seq in seqs if seq} for nt, seqs in follow_k.items()}
