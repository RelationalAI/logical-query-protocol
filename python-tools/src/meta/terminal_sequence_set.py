"""Lazy terminal sequence sets for LL(k) lookahead computation.

This module provides classes for lazily computing sets of terminal sequences
used in LL(k) parser generation. These sets represent possible lookahead
tokens at various positions in the grammar.

Background
----------
In LL(k) parsing, we need FIRST_k and FOLLOW_k sets to decide which production
to use when multiple alternatives exist. Computing these sets for large k can
be expensive, but often we only need small lookahead (k=1 or k=2).

These classes compute sets lazily - only when needed and only for the specific
k value requested. Results are cached to avoid recomputation.

Class Hierarchy
---------------
TerminalSequenceSet (abstract base)
├── FollowSet  - FOLLOW_k(A): terminals that can follow nonterminal A
├── FirstSet   - FIRST_k(α): terminals that can start RHS α
└── ConcatSet  - Concatenation of two sets (for sequences)

Usage Example
-------------
When parsing a sequence "A B C", we need to know what can follow A to handle
optional elements or repetitions. The follow set for A is:

    FIRST(B C) ∘ FOLLOW(entire sequence)

This is computed as:

    ConcatSet(FirstSet(B C), parent_follow_set)

The ConcatSet chains lazily - it only computes what it needs from each
constituent set based on the requested k value.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Set, Tuple

if TYPE_CHECKING:
    from .grammar import Grammar, Nonterminal, Rhs, Terminal


class TerminalSequenceSet:
    """Abstract base for lazily-computed sets of terminal sequences.

    A terminal sequence set represents the possible k-length prefixes of
    terminal strings that can appear at a given position in the grammar.
    These are used for LL(k) parsing decisions.

    Subclasses implement different ways of computing these sets:
    - FollowSet: computes FOLLOW_k for a nonterminal
    - FirstSet: computes FIRST_k for an RHS element
    - ConcatSet: concatenates two sets (for computing FIRST of sequences)
    """

    def get(self, k: int) -> Set[Tuple['Terminal', ...]]:
        """Get sequences of length up to k, computing and caching if needed.

        Args:
            k: Maximum sequence length to compute.

        Returns:
            Set of terminal tuples, each of length at most k.
        """
        raise NotImplementedError


@dataclass
class FollowSet(TerminalSequenceSet):
    """Lazily computes FOLLOW_k sets for a nonterminal.

    FOLLOW_k(A) is the set of terminal sequences of length up to k that can
    immediately follow nonterminal A in any sentential form derived from the
    start symbol.

    For example, if the grammar has rules:
        S → A B
        B → 'x' | 'y'

    Then FOLLOW_1(A) = {'x', 'y'} because A is always followed by B,
    which can start with 'x' or 'y'.
    """

    grammar: 'Grammar'
    lhs: 'Nonterminal'
    _cache: Dict[int, Set[Tuple['Terminal', ...]]] = field(default_factory=dict)

    def get(self, k: int) -> Set[Tuple['Terminal', ...]]:
        """Get FOLLOW_k set for the nonterminal, computing and caching if needed."""
        if k not in self._cache:
            self._cache[k] = self.grammar.analysis.follow_k_of(k, self.lhs)
        return self._cache[k]


@dataclass
class FirstSet(TerminalSequenceSet):
    """Lazily computes FIRST_k sets for an RHS.

    FIRST_k(α) is the set of terminal sequences of length up to k that can
    begin strings derived from α. If α can derive ε (empty string), the
    set includes sequences shorter than k.

    For example, if:
        α = A B
        A → 'a' | ε
        B → 'b'

    Then FIRST_2(α) = {('a', 'b'), ('b',)} because:
    - A can produce 'a', then B produces 'b' → ('a', 'b')
    - A can produce ε, then B produces 'b' → ('b',)
    """

    grammar: 'Grammar'
    rhs: 'Rhs'
    _cache: Dict[int, Set[Tuple['Terminal', ...]]] = field(default_factory=dict)

    def get(self, k: int) -> Set[Tuple['Terminal', ...]]:
        """Get FIRST_k set for the RHS, computing and caching if needed."""
        if k not in self._cache:
            self._cache[k] = self.grammar.analysis.first_k_of(k, self.rhs)
        return self._cache[k]


@dataclass
class ConcatSet(TerminalSequenceSet):
    """Lazily concatenates two TerminalSequenceSets.

    Used when parsing sequences: if we're parsing "A B" and need to know
    what can follow A, it's FIRST(B) concatenated with FOLLOW(whole sequence).

    The concatenation is: {a ∘ b | a ∈ first, b ∈ second, |a ∘ b| ≤ k},
    where ∘ means concatenation truncated to length k.

    This handles the case where sequences in `first` are shorter than k
    (because the RHS can derive ε or short strings). In that case, we need
    to append tokens from `second` to reach length k.

    Optimization: We only fetch from `second` what we actually need. If all
    sequences in `first` are already length k, we don't need `second` at all.
    """

    first: TerminalSequenceSet
    second: TerminalSequenceSet
    _cache: Dict[int, Set[Tuple['Terminal', ...]]] = field(default_factory=dict)

    def get(self, k: int) -> Set[Tuple['Terminal', ...]]:
        """Get concatenation of first and second sets, truncated to length k."""
        if k in self._cache:
            return self._cache[k]

        first_set = self.first.get(k)

        # Optimization: only fetch from second what we actually need
        if first_set:
            min_len = min(len(seq) for seq in first_set)
            needed_second_k = k - min_len
            if needed_second_k <= 0:
                # All sequences in first are already max length
                result = first_set
            else:
                from .grammar_analysis import GrammarAnalysis
                second_set = self.second.get(needed_second_k)
                result = GrammarAnalysis.concat_k(first_set, second_set, k)
        else:
            result = self.second.get(k)

        self._cache[k] = result
        return result
