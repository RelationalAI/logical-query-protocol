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

    The deconstruct_action is the inverse - it takes a message of the LHS type and
    extracts the component values that would be needed to reconstruct it. This is
    used by the pretty-printer to deconstruct messages back into their components.
    """
    lhs: Nonterminal
    rhs: Rhs
    construct_action: 'Lambda'
    deconstruct_action: 'Lambda'
    source_type: Optional[str] = None  # Track the protobuf type this rule came from

    def __str__(self):
        result = f"{self.lhs.name} -> {self.rhs} {{{{ {self.construct_action} }}}}"
        result += f" [[ {self.deconstruct_action} ]]"
        return result

    def to_pattern(self, grammar: Optional['Grammar'] = None) -> str:
        """Convert RHS to pattern string."""
        return str(self.rhs)

    def __post_init__(self):
        from .target import OptionType, TupleType

        assert isinstance(self.rhs, Rhs)
        rhs_len = _count_nonliteral_rhs_elements(self.rhs)
        action_params = len(self.construct_action.params)
        assert action_params == rhs_len, \
            f"Action for {self.lhs.name} has {action_params} parameters but RHS has {rhs_len} non-literal element{'' if rhs_len == 1 else 's'}: {self.rhs}"

        # Check deconstruct_action has exactly one parameter with the LHS type
        assert len(self.deconstruct_action.params) == 1, \
            f"Deconstruct action for {self.lhs.name} must have exactly 1 parameter, has {len(self.deconstruct_action.params)}"

        deconstruct_param_type = self.deconstruct_action.params[0].type
        lhs_type = self.lhs.target_type()
        assert deconstruct_param_type == lhs_type, \
            f"Deconstruct action for {self.lhs.name} parameter type {deconstruct_param_type} must match LHS type {lhs_type}"

        # # Check deconstruct_action return type is OptionType of tuple of RHS types
        # assert isinstance(self.deconstruct_action.return_type, OptionType), \
        #     f"Deconstruct action for {self.lhs.name} return type must be OptionType, got {self.deconstruct_action.return_type}"

        # # Build expected tuple type from RHS
        # rhs_types = [elem.target_type() for elem in rhs_elements(self.rhs) if not isinstance(elem, LitTerminal)]
        # if len(rhs_types) == 0:
        #     # No non-literal elements - should return OptionType of empty tuple
        #     expected_inner_type = TupleType([])
        # elif len(rhs_types) == 1:
        #     # Single element - return that type directly, not a tuple
        #     expected_inner_type = rhs_types[0]
        # else:
        #     # Multiple elements - return tuple
        #     expected_inner_type = TupleType(rhs_types)

        # actual_inner_type = self.deconstruct_action.return_type.element_type
        # assert actual_inner_type == expected_inner_type, \
        #     f"Deconstruct action for {self.lhs.name} return type {self.deconstruct_action.return_type} must be OptionType[{expected_inner_type}]"

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

    # Lazily created analysis object (holds cached results)
    _analysis: Optional['GrammarAnalysis'] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        self.rules = {self.start: []}

    @property
    def analysis(self) -> 'GrammarAnalysis':
        """Get or create the grammar analysis object."""
        if self._analysis is None:
            from .grammar_analysis import GrammarAnalysis
            self._analysis = GrammarAnalysis(self)
        return self._analysis

    def add_rule(self, rule: Rule) -> None:
        assert self._analysis is None, "Grammar is already analyzed"

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


    def get_unreachable_rules(self) -> List[Nonterminal]:
        """
        Find all rules that are unreachable from start symbol.

        Returns list of rule names that cannot be reached.
        """
        reachable = self.analysis.compute_reachability()
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
                if rule.deconstruct_action:
                    lines.append(f"    -{{{{ {rule.deconstruct_action} }}}}")

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


# Helper functions - re-exported from analysis module
from .grammar_analysis import GrammarAnalysis
get_nonterminals = GrammarAnalysis.get_nonterminals
get_literals = GrammarAnalysis.get_literals
is_epsilon = GrammarAnalysis.is_epsilon


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


