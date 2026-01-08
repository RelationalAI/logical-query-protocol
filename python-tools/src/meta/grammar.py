"""Grammar data structures for meta-language tools.

This module defines the data structures for representing context-free grammars
with semantic actions, including support for normalization and left-factoring.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

# Import action AST types
from .target import TargetExpr, Var, Symbol, Call, Lambda, Lit, TargetType, ListType, OptionType, TupleType


# Grammar RHS (right-hand side) elements

@dataclass(frozen=True)
class Rhs:
    """Base class for right-hand sides of grammar rules."""

    def target_type(self) -> TargetType:
        """Return the target type for this RHS element."""
        raise NotImplementedError(f"target_type not implemented for {type(self).__name__}")

@dataclass(frozen=True)
class RhsSymbol(Rhs):
    """Base class for symbols occurring on the right-hand side of grammar rules."""
    pass

@dataclass(frozen=True)
class Terminal(RhsSymbol):
    """Base class for terminal symbols."""
    pass

@dataclass(frozen=True, unsafe_hash=True)
class LitTerminal(Terminal):
    """Literal terminal (quoted string in grammar)."""
    name: str

    def __str__(self) -> str:
        return f'"{self.name}"'

    def target_type(self) -> TargetType:
        """Literals don't produce values, return empty tuple type."""
        from .target import TupleType
        return TupleType([])


@dataclass(frozen=True, unsafe_hash=True)
class NamedTerminal(Terminal):
    """Token terminal (unquoted uppercase name like SYMBOL, INT)."""
    name: str
    type: TargetType

    def __str__(self) -> str:
        return self.name

    def target_type(self) -> TargetType:
        """Return the type for this terminal."""
        return self.type


@dataclass(frozen=True, unsafe_hash=True)
class Nonterminal(RhsSymbol):
    """Nonterminal (rule name)."""
    name: str
    type: TargetType

    def __str__(self) -> str:
        return self.name

    def target_type(self) -> TargetType:
        """Return the type for this nonterminal."""
        return self.type


@dataclass(frozen=True)
class Star(Rhs):
    """Zero or more repetitions (*)."""
    rhs: 'RhsSymbol'

    def __str__(self) -> str:
        return f"{self.rhs}*"

    def target_type(self) -> TargetType:
        """Return list type of the element type."""
        return ListType(self.rhs.target_type())


@dataclass(frozen=True)
class Option(Rhs):
    """Optional element (?)."""
    rhs: 'RhsSymbol'

    def __str__(self) -> str:
        return f"{self.rhs}?"

    def target_type(self) -> TargetType:
        """Return option type of the element type."""
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

    def target_type(self) -> TargetType:
        """Return tuple type of non-literal element types."""
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
    """Grammar rule (production).

    The construct_action takes the values from parsing the RHS elements and constructs
    the result message.
    """
    lhs: Nonterminal
    rhs: Rhs
    construct_action: 'Lambda'
    source_type: Optional[str] = None  # Track the protobuf type this rule came from

    def __str__(self):
        result = f"{self.lhs.name} -> {self.rhs} {{{{ {self.construct_action} }}}}"
        return result

    def to_pattern(self, grammar: Optional['Grammar'] = None) -> str:
        """Convert RHS to pattern string."""
        return str(self.rhs)

    def __post_init__(self):
        assert isinstance(self.rhs, Rhs)
        rhs_len = _count_nonliteral_rhs_elements(self.rhs)
        action_params = len(self.construct_action.params)
        assert action_params == rhs_len, \
            f"Action for {self.lhs.name} has {action_params} parameters but RHS has {rhs_len} non-literal element{'' if rhs_len == 1 else 's'}: {self.rhs}"

@dataclass(frozen=True)
class Token:
    """Token definition (terminal with regex pattern)."""
    name: str
    pattern: str
    type: TargetType

@dataclass
class Grammar:
    """Complete grammar specification with normalization and left-factoring support."""
    start: Nonterminal
    rules: Dict[Nonterminal, List[Rule]] = field(default_factory=dict)
    tokens: List[Token] = field(default_factory=list)

    def __post_init__(self):
        self.rules = {self.start: []}

    def add_rule(self, rule: Rule) -> None:
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


    def compute_reachability(self) -> Set[Nonterminal]:
        """Compute set of reachable nonterminals from start symbol."""
        if self.start not in self.rules:
            return set()

        reachable: Set[Nonterminal] = set([self.start])
        worklist = [self.start]

        while worklist:
            current = worklist.pop()
            if current in self.rules:
                for rule in self.rules[current]:
                    for nt in get_nonterminals(rule.rhs):
                        if nt not in reachable:
                            reachable.add(nt)
                            worklist.append(nt)

        return reachable

    def get_unreachable_nonterminals(self) -> List[Nonterminal]:
        """
        Find all nonterminals that are unreachable from start symbol.

        Returns list of nonterminal names that cannot be reached.
        """
        reachable = self.compute_reachability()
        unreachable = []
        for A in self.rules.keys():
            if A not in reachable:
                unreachable.append(A)
        return unreachable

    def print_grammar(self, reachable: Optional[Set[Nonterminal]] = None) -> str:
        """Convert to context-free grammar format with actions."""
        lines = []
        lines.append("// Auto-generated grammar from protobuf specifications")
        lines.append("")

        # Traverse rules in preorder
        rule_order = self.traverse_rules_preorder(reachable_only=(reachable is not None))
        for lhs in rule_order:
            if reachable is not None and lhs not in reachable:
                continue
            rules_list = self.rules[lhs]
            lines.append(f"{lhs}")
            for idx, rule in enumerate(rules_list):
                if idx == 0:
                    lines.append(f"  : {rule.to_pattern(self)}")
                else:
                    lines.append(f"  | {rule.to_pattern(self)}")

                if rule.construct_action:
                    lines.append(f"    +{{{{ {rule.construct_action} }}}}")

            lines.append("")

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

                if rule.construct_action:
                    lines.append(f"    {{{{ {rule.construct_action} }}}}")

            lines.append("")

        return "\n".join(lines)


# Helper functions

def get_nonterminals(rhs: Rhs) -> List[Nonterminal]:
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


def get_literals(rhs: Rhs) -> List[LitTerminal]:
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


def is_epsilon(rhs: Rhs) -> bool:
    """Check if rhs represents an epsilon production (empty sequence)."""
    return isinstance(rhs, Sequence) and len(rhs.elements) == 0


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
