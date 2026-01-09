"""Grammar data structures for meta-language tools.

This module defines the data structures for representing context-free grammars
with semantic actions, including support for normalization and left-factoring.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

# Import action AST types
from .target import TargetExpr, Var, Symbol, Call, Lambda, Let, Lit, Type, MessageType


# Grammar RHS (right-hand side) elements

@dataclass(frozen=True)
class Rhs:
    """Base class for right-hand sides of grammar rules."""

    def target_type(self) -> Type:
        """Return the target type for this RHS element."""
        raise NotImplementedError(f"target_type not implemented for {type(self).__name__}")

@dataclass(frozen=True)
class Terminal(Rhs):
    """Base class for terminal symbols."""
    pass

@dataclass(frozen=True, unsafe_hash=True)
class LitTerminal(Terminal):
    """Literal terminal (quoted string in grammar)."""
    name: str

    def __str__(self) -> str:
        return f'"{self.name}"'

    def target_type(self) -> Type:
        """Literals don't produce values, return empty tuple type."""
        from .target import TupleType
        return TupleType([])


@dataclass(frozen=True, unsafe_hash=True)
class NamedTerminal(Terminal):
    """Token terminal (unquoted uppercase name like SYMBOL, NUMBER)."""
    name: str
    type: Type

    def __str__(self) -> str:
        return self.name

    def target_type(self) -> Type:
        """Return the type for this terminal."""
        return self.type


@dataclass(frozen=True, unsafe_hash=True)
class Nonterminal(Rhs):
    """Nonterminal (rule name)."""
    name: str
    type: Type

    def __str__(self) -> str:
        return self.name

    def target_type(self) -> Type:
        """Return the type for this nonterminal."""
        return self.type


@dataclass(frozen=True)
class Star(Rhs):
    """Zero or more repetitions (*)."""
    rhs: 'Rhs'

    def __post_init__(self):
        assert isinstance(self.rhs, Nonterminal) or isinstance(self.rhs, NamedTerminal), \
            f"Star child must be Nonterminal or NamedTerminal, got {type(self.rhs).__name__}"

    def __str__(self) -> str:
        return f"{self.rhs}*"

    def target_type(self) -> Type:
        """Return list type of the element type."""
        from .target import ListType
        return ListType(self.rhs.target_type())


@dataclass(frozen=True)
class Option(Rhs):
    """Optional element (?)."""
    rhs: 'Rhs'

    def __post_init__(self):
        assert isinstance(self.rhs, Nonterminal) or isinstance(self.rhs, NamedTerminal), \
            f"Option child must be Nonterminal, got {type(self.rhs).__name__}"

    def __str__(self) -> str:
        return f"{self.rhs}?"

    def target_type(self) -> Type:
        """Return option type of the element type."""
        from .target import OptionType
        return OptionType(self.rhs.target_type())


@dataclass(frozen=True)
class Sequence(Rhs):
    """Sequence of grammar symbols (concatenation)."""
    elements: Tuple['Rhs', ...] = field(default_factory=tuple)

    def __post_init__(self):
        for elem in self.elements:
            assert not isinstance(elem, Sequence), \
                f"Sequence elements cannot be Sequence nodes, got {type(elem).__name__}"

    def __str__(self) -> str:
        return " ".join(str(e) for e in self.elements)

    def target_type(self) -> Type:
        """Return tuple type of non-literal element types."""
        from .target import TupleType
        element_types = []
        for elem in self.elements:
            if not isinstance(elem, LitTerminal):
                element_types.append(elem.target_type())
        if len(element_types) == 1:
            return element_types[0]
        return TupleType(element_types)


# Grammar rules and tokens

@dataclass(frozen=True)
class Rule:
    """Grammar rule (production)."""
    lhs: Nonterminal
    rhs: Rhs
    action: 'Lambda'
    source_type: Optional[str] = None  # Track the protobuf type this rule came from

    def __str__(self):
        return f"{self.lhs.name} -> {self.rhs} {{{{ {self.action} }}}}"

    def to_pattern(self, grammar: Optional['Grammar'] = None) -> str:
        """Convert RHS to pattern string."""
        return str(self.rhs)

    def __post_init__(self):
        assert isinstance(self.rhs, Rhs)
        rhs_len = _count_nonliteral_rhs_elements(self.rhs)
        action_params = len(self.action.params)
        assert action_params == rhs_len, \
            f"Action for {self.lhs.name} has {action_params} parameters but RHS has {rhs_len} non-literal element{'' if rhs_len == 1 else 's'}: {self.rhs}"

@dataclass(frozen=True)
class Token:
    """Token definition (terminal with regex pattern)."""
    name: str
    pattern: str
    type: Type

@dataclass
class Grammar:
    """Complete grammar specification with normalization and left-factoring support."""
    start: Nonterminal
    rules: Dict[Nonterminal, List[Rule]] = field(default_factory=dict)
    tokens: List[Token] = field(default_factory=list)

    # Cached analysis results
    _reachable_cache: Optional[Set[Nonterminal]] = field(default=None, init=False, repr=False)
    _nullable_cache: Optional[Dict[Nonterminal, bool]] = field(default=None, init=False, repr=False)
    _first_cache: Optional[Dict[Nonterminal, Set[Terminal]]] = field(default=None, init=False, repr=False)
    _follow_cache: Optional[Dict[Nonterminal, Set[Terminal]]] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        self.rules = {self.start: []}

    def add_rule(self, rule: Rule) -> None:
        assert self._reachable_cache is None, "Grammar is already analyzed"
        assert self._nullable_cache is None, "Grammar is already analyzed"
        assert self._first_cache is None, "Grammar is already analyzed"
        assert self._follow_cache is None, "Grammar is already analyzed"

        lhs = rule.lhs
        if lhs not in self.rules:
            self.rules[lhs] = []
            # Set start symbol to first rule added if default
            if self.start.name == "start" and len(self.rules) == 0:
                self.start = lhs
        self.rules[lhs].append(rule)

    def traverse_rules_preorder(self, reachable_only: bool = True) -> List[Nonterminal]:
        """Traverse rules in preorder starting from start symbol.

        Returns list of nonterminal names in the order they should be printed.
        If reachable_only is True, only includes reachable nonterminals.
        """
        start = self.start

        visited = set()
        result = []

        def visit(A: Nonterminal) -> None:
            """Visit nonterminal and its dependencies in preorder."""
            if A in visited or A not in self.rules:
                # Skip visited nonterminals and those that do not appear in the grammar.
                return
            visited.add(A)
            result.append(A)

            # Visit all nonterminals referenced in this rule's RHS
            for rule in self.rules[A]:
                for B in get_nonterminals(rule.rhs):
                    visit(B)

        visit(self.start)

        # If not reachable_only, add any remaining rules
        if not reachable_only:
            for nt_name in sorted(self.rules.keys(), key=lambda nt: nt.name):
                if nt_name not in visited:
                    visit(nt_name)

        return result

    def get_rules(self, nt: Nonterminal) -> List[Rule]:
        """Get all rules with the given LHS name."""
        return self.rules.get(nt, [])

    def has_rule(self, name: Nonterminal) -> bool:
        """Check if any rule has the given LHS name."""
        return name in self.rules


    def check_reachability(self) -> Set[Nonterminal]:
        """
        Compute set of reachable nonterminals from start symbol.

        Returns set of nonterminal names that can be reached.
        """
        if self._reachable_cache is None:
            from .grammar_analysis import check_reachability
            reachable_names = check_reachability(self)
            self._reachable_cache = reachable_names
        return self._reachable_cache

    def get_unreachable_rules(self) -> List[Nonterminal]:
        """
        Find all rules that are unreachable from start symbol.

        Returns list of rule names that cannot be reached.
        """
        reachable = self.check_reachability()
        unreachable = []
        for A in self.rules.keys():
            if A not in reachable:
                unreachable.append(A)
        return unreachable


    def compute_nullable(self) -> Dict[Nonterminal, bool]:
        """
        Compute nullable set for all nonterminals.

        A nonterminal is nullable if it can derive the empty string.
        Returns dict mapping nonterminals to boolean.
        """
        if self._nullable_cache is None:
            from .grammar_analysis import compute_nullable
            self._nullable_cache = compute_nullable(self)
        return self._nullable_cache

    def compute_first_k(self, k: int = 2) -> Dict[Nonterminal, Set[Tuple[Terminal, ...]]]:
        """
        Compute FIRST_k sets for all nonterminals.

        FIRST_k(A) is the set of terminal sequences of length up to k that can begin strings derived from A.
        Returns dict mapping nonterminals to sets of terminal tuples.
        """
        from .grammar_analysis import compute_first_k
        return compute_first_k(self, k, self.compute_nullable())

    def compute_first(self) -> Dict[Nonterminal, Set[Terminal]]:
        """
        Compute FIRST sets for all nonterminals.

        FIRST(A) is the set of terminals that can begin strings derived from A.
        Returns dict mapping nonterminals to sets of Terminals.
        """
        if self._first_cache is None:
            from .grammar_analysis import compute_first
            self._first_cache = compute_first(self, self.compute_nullable())
        return self._first_cache

    def compute_follow(self) -> Dict[Nonterminal, Set[Terminal]]:
        """
        Compute FOLLOW sets for all nonterminals.

        FOLLOW(A) is the set of terminals that can immediately follow A in any derivation.
        Returns dict mapping nonterminals to sets of Terminals.
        """
        if self._follow_cache is None:
            from .grammar_analysis import compute_follow
            self._follow_cache = compute_follow(self, self.compute_nullable(), self.compute_first())
        return self._follow_cache

    def compute_follow_k(self, k: int = 2) -> Dict[Nonterminal, Set[Tuple[Terminal, ...]]]:
        """
        Compute FOLLOW_k sets for all nonterminals.

        FOLLOW_k(A) is the set of terminal sequences of length up to k that can follow A.
        Returns dict mapping nonterminals to sets of terminal tuples.
        """
        from .grammar_analysis import compute_follow_k
        return compute_follow_k(self, k, self.compute_nullable(), self.compute_first_k(k))

    def nullable(self, rhs: Rhs) -> bool:
        """
        Check if an RHS is nullable.

        An RHS is nullable if it can derive the empty string.
        Uses cached nullable information for nonterminals.
        """

        if isinstance(rhs, LitTerminal) or isinstance(rhs, NamedTerminal):
            return False
        elif isinstance(rhs, Nonterminal):
            nullable_dict = self.compute_nullable()
            return nullable_dict.get(rhs, False)
        elif isinstance(rhs, Sequence):
            return all(self.nullable(elem) for elem in rhs.elements)
        elif isinstance(rhs, Star) or isinstance(rhs, Option):
            return True
        else:
            return False

    def first(self, rhs: Rhs) -> Set[Terminal]:
        """
        Compute FIRST set for an RHS.

        FIRST(rhs) is the set of terminals that can begin strings derived from rhs.
        Uses cached FIRST information for nonterminals.
        """
        first_dict = self.compute_first()

        result: Set[Terminal] = set()

        if isinstance(rhs, LitTerminal):
            result.add(rhs)
        elif isinstance(rhs, NamedTerminal):
            result.add(rhs)
        elif isinstance(rhs, Nonterminal):
            # first_dict maps Nonterminal -> Set[Terminal], need to extract names
            terminals = first_dict.get(rhs, set())
            result.update(terminals)
        elif isinstance(rhs, Sequence):
            for elem in rhs.elements:
                result.update(self.first(elem))
                if not self.nullable(elem):
                    break
        elif isinstance(rhs, Star) or isinstance(rhs, Option):
            result.update(self.first(rhs.rhs))

        return result

    def first_k(self, k: int, rhs: Rhs) -> Set[Tuple[Terminal, ...]]:
        """
        Compute FIRST_k set for an RHS.

        FIRST_k(rhs) is the set of terminal sequences of length up to k that can begin strings derived from rhs.
        Uses cached FIRST information for nonterminals.
        """
        # Special case: k=1 for Nonterminal can use the cached FIRST sets
        if k == 1 and isinstance(rhs, Nonterminal):
            first_set = self.first(rhs)
            # Convert Set[Terminal] to Set[Tuple[Terminal, ...]]
            return {(t,) for t in first_set}

        from .grammar_analysis import rhs_first_k

        # Compute first_k sets for all nonterminals if not already cached
        first_k_dict = self.compute_first_k(k)
        nullable_dict = self.compute_nullable()

        return rhs_first_k(rhs, first_k_dict, nullable_dict, k)

    def follow(self, nt: Nonterminal) -> Set[Terminal]:
        """
        Compute FOLLOW set for a nonterminal.

        FOLLOW(A) is the set of terminals that can immediately follow A in any derivation.
        Uses cached FOLLOW information for nonterminals.
        """
        follow_dict = self.compute_follow()
        return follow_dict.get(nt, set())

    def follow_k(self, k: int, rhs: Rhs) -> Set[Tuple[Terminal, ...]]:
        """
        Compute FOLLOW_k set for a nonterminal.

        FOLLOW_k(A) is the set of terminal sequences of length up to k that can follow A.
        Uses cached FOLLOW_k information for nonterminals.
        """
        # Special case: k=1 can use the cached FOLLOW sets
        if isinstance(rhs, Nonterminal):
            if k == 1:
                follow_set = self.follow(rhs)
                # Convert Set[Terminal] to Set[Tuple[Terminal, ...]]
                return {(t,) for t in follow_set}

            follow_k_dict = self.compute_follow_k(k)
            return follow_k_dict.get(rhs, set())
        elif isinstance(rhs, Option):
            return self.follow_k(k, rhs.rhs)
        elif isinstance(rhs, Star):
            return self.follow_k(k, rhs.rhs)
        else:
            assert False, f"Unexpected rhs {rhs}: follow_k unimplemented"

    def first_k_with_follow(self, k: int, following: Rhs, lhs: Nonterminal) -> Set[Tuple[Terminal, ...]]:
        """
        Compute FIRST_k(following) concatenated with FOLLOW_k(lhs).

        This is used for Option and Star disambiguation: when exiting an Option or Star,
        the tokens that can follow are FIRST_k(following) if following is present,
        or FOLLOW_k(lhs) if at the end of the rule, or both if following is nullable.
        """
        from .grammar_analysis import concat_k

        first_of_following = self.first_k(k, following)
        if self.nullable(following):
            follow_of_lhs = self.follow_k(k, lhs)
            return concat_k(first_of_following, follow_of_lhs, k)
        else:
            return first_of_following

    def print_grammar(self, reachable: Optional[Set[str]] = None) -> str:
        """Convert to context-free grammar format."""
        lines = []
        lines.append("// Auto-generated grammar from protobuf specifications")
        lines.append("")

        # Traverse rules in preorder
        rule_order = self.traverse_rules_preorder(reachable_only=(reachable is not None))
        for lhs in rule_order:
            if reachable is not None and lhs not in reachable:
                continue
            rules_list = self.rules[lhs]
            if len(rules_list) == 1:
                lines.append(f"{lhs}: {rules_list[0].to_pattern(self)}")
            else:
                alternatives = [rule.to_pattern(self) for rule in rules_list]
                lines.append(f"{lhs}: {alternatives[0]}")
                for alt in alternatives[1:]:
                    lines.append(f"    | {alt}")

        # Print tokens at the end
        if self.rules and self.tokens:
            lines.append("")

        for token in self.tokens:
            lines.append(f"{token.name}: {token.pattern}")

        return "\n".join(lines)

    def print_grammar_with_actions(self, reachable: Optional[Set[Nonterminal]] = None) -> str:
        """Generate grammar with semantic actions in original form."""
        lines = []
        lines.append("# Grammar with semantic actions")
        lines.append("")

        # Traverse rules in preorder
        rule_order = self.traverse_rules_preorder(reachable_only=(reachable is not None))
        for lhs in rule_order:
            if reachable is not None and lhs not in reachable:
                continue
            rules_list = self.rules[lhs]

            for idx, rule in enumerate(rules_list):
                if len(rules_list) == 1:
                    lines.append(f"{lhs}: {rule.rhs}")
                else:
                    if idx == 0:
                        lines.append(f"{lhs}: {rule.rhs}")
                    else:
                        lines.append(f"    | {rule.rhs}")

                if rule.action:
                    lines.append(f"    {{{{ {rule.action} }}}}")

            lines.append("")

        return "\n".join(lines)


# Helper functions - re-exported from analysis module
from .grammar_analysis import get_nonterminals, get_literals, is_epsilon


def rhs_elements(rhs: Rhs) -> Tuple[Rhs, ...]:
    """Return elements of rhs. For Sequence, returns rhs.elements; otherwise returns (rhs,)."""
    if isinstance(rhs, Sequence):
        return rhs.elements
    return (rhs,)


def _count_nonliteral_rhs_elements(rhs: Rhs) -> int:
    """Count the number of elements in an RHS that produce action parameters.

    This counts all RHS elements, as each position (including literals, options,
    stars, etc.) corresponds to a parameter in the action lambda.
    """
    if isinstance(rhs, Sequence):
        return sum(_count_nonliteral_rhs_elements(elem) for elem in rhs.elements)
    elif isinstance(rhs, LitTerminal):
        return 0
    else:
        assert isinstance(rhs, (NamedTerminal, Nonterminal, Option, Star)), f"found {type(rhs)}"
        return 1
