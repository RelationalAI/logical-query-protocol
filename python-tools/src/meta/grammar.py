"""Grammar data structures for meta-language tools.

This module defines the data structures for representing context-free grammars
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

# Import action AST types
from .target import TargetExpr, Var, Symbol, Call, Lambda, Let, Lit, TargetType, TupleType, ListType, OptionType


# Grammar RHS (right-hand side) elements

@dataclass(frozen=True)
class Rhs:
    """Base class for right-hand sides of grammar rules.

    RHS elements represent the right-hand side of a grammar production.
    Each RHS element can be a terminal (literal or named token), nonterminal,
    or a compound element (sequence, repetition, or option).

    Example grammar rule: expr -> term "+" term
    - The RHS is a Sequence containing: [Nonterminal('term'), LitTerminal('+'), Nonterminal('term')]
    - Each element has a target type that determines what value it produces when parsed

    The target_type() method returns the type of value this RHS element produces
    during semantic analysis. For example:
    - LitTerminal produces empty tuple (no value)
    - NamedTerminal produces its declared type (e.g., String for SYMBOL)
    - Nonterminal produces the type of the nonterminal
    - Star produces a list of the element type
    - Option produces an optional of the element type
    - Sequence produces a tuple of non-literal element types
    """

    def target_type(self) -> TargetType:
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

    def target_type(self) -> TargetType:
        """Literals don't produce values, return empty tuple type."""
        return TupleType([])


@dataclass(frozen=True, unsafe_hash=True)
class NamedTerminal(Terminal):
    """Token terminal (unquoted uppercase name like SYMBOL, NUMBER)."""
    name: str
    type: TargetType

    def __str__(self) -> str:
        return self.name

    def target_type(self) -> TargetType:
        """Return the type for this terminal."""
        return self.type


@dataclass(frozen=True, unsafe_hash=True)
class Nonterminal(Rhs):
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
    rhs: 'Nonterminal | NamedTerminal'

    def __str__(self) -> str:
        return f"{self.rhs}*"

    def target_type(self) -> TargetType:
        """Return list type of the element type."""
        return ListType(self.rhs.target_type())


@dataclass(frozen=True)
class Option(Rhs):
    """Optional element (?)."""
    rhs: 'Nonterminal | NamedTerminal'

    def __str__(self) -> str:
        return f"{self.rhs}?"

    def target_type(self) -> TargetType:
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

    def target_type(self) -> TargetType:
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
    """Grammar rule (production).

    A Rule represents a single production in a context-free grammar with semantic actions.
    It consists of a left-hand side (nonterminal), a right-hand side (pattern to match),
    and a lambda expression that computes the semantic value.

    Example textual form:
        expr -> term "+" term {{ lambda t1 t2: (add t1 t2) }}

    This represents:
    - lhs: Nonterminal('expr', ExprType)
    - rhs: Sequence([Nonterminal('term', TermType), LitTerminal('+'), Nonterminal('term', TermType)])
    - action: Lambda with 2 parameters (t1, t2) returning a Call to 'add'

    The action lambda must have exactly one parameter for each non-literal element in the RHS.
    Literals like "+" don't produce values, so they don't get parameters.

    The to_pattern() method converts the RHS to a string pattern for display.
    The __post_init__ validates that the action parameters match the RHS structure
    and that types are consistent.
    """
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
        # Check that the action has a parameter for each non-literal on the RHS.
        rhs_len = _count_nonliteral_rhs_elements(self.rhs)
        action_params = len(self.action.params)
        assert action_params == rhs_len, \
            f"Action for {self.lhs.name} has {action_params} parameters but RHS has {rhs_len} non-literal element{'' if rhs_len == 1 else 's'}: {self.rhs}"

        # Check that RHS types match action parameter types
        rhs_types = _collect_nonliteral_rhs_types(self.rhs)
        for i, (rhs_type, param) in enumerate(zip(rhs_types, self.action.params)):
            assert rhs_type == param.type, \
                f"Rule {self.lhs.name}: parameter {i} type mismatch: RHS has {rhs_type} but action parameter '{param.name}' has {param.type}"

        # Check that action return type matches the LHS type
        assert self.action.return_type == self.lhs.type, \
            f"Rule {self.lhs.name}: action return type {self.action.return_type} does not match LHS type {self.lhs.type}"

@dataclass(frozen=True)
class Token:
    """Token definition (terminal with regex pattern).

    A Token defines a terminal symbol that matches a regular expression pattern.
    Tokens are the lexical elements of the grammar, matched by a lexer before parsing.

    Example:
        Token(name='SYMBOL', pattern=r'[a-zA-Z_][a-zA-Z0-9_]*', type=BaseType('String'))

    This defines a token named SYMBOL that matches identifiers and produces a String value.
    In grammar rules, this token is referenced as a NamedTerminal:
        expr -> SYMBOL

    The pattern is a regular expression string compatible with the parser generator.
    The type indicates what kind of value the token produces when matched.
    """
    name: str
    pattern: str
    type: TargetType

@dataclass
class Grammar:
    """Complete grammar specification."""
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
                for B in Grammar.get_nonterminals(rule.rhs):
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
        """
        Compute set of reachable nonterminals from start symbol.

        Returns set of nonterminal names that can be reached.
        """
        if self.start not in self.rules:
            return set()

        reachable: Set[Nonterminal] = set([self.start])
        worklist = [self.start]

        while worklist:
            current = worklist.pop()
            if current in self.rules:
                for rule in self.rules[current]:
                    for nt in Grammar.get_nonterminals(rule.rhs):
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
        for nt in self.rules.keys():
            if nt not in reachable:
                unreachable.append(nt)
        return unreachable



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


    @staticmethod
    def get_nonterminals(rhs: 'Rhs') -> List[Nonterminal]:
        """Return the list of all nonterminals referenced in a Rhs."""
        nonterminals = []

        if isinstance(rhs, Nonterminal):
            nonterminals.append(rhs)
        elif isinstance(rhs, Sequence):
            for elem in rhs.elements:
                nonterminals.extend(Grammar.get_nonterminals(elem))
        elif isinstance(rhs, (Star, Option)):
            nonterminals.extend(Grammar.get_nonterminals(rhs.rhs))

        return list(dict.fromkeys(nonterminals))

    @staticmethod
    def get_literals(rhs: 'Rhs') -> List[LitTerminal]:
        """Return the list of all literals referenced in a Rhs."""
        literals = []

        if isinstance(rhs, LitTerminal):
            literals.append(rhs)
        elif isinstance(rhs, Sequence):
            for elem in rhs.elements:
                literals.extend(Grammar.get_literals(elem))
        elif isinstance(rhs, (Star, Option)):
            literals.extend(Grammar.get_literals(rhs.rhs))

        return list(dict.fromkeys(literals))

    @staticmethod
    def is_epsilon(rhs: 'Rhs') -> bool:
        """Check if rhs represents an epsilon production (empty sequence)."""
        return isinstance(rhs, Sequence) and len(rhs.elements) == 0


# Helper functions - re-exported for backward compatibility
get_nonterminals = Grammar.get_nonterminals
get_literals = Grammar.get_literals
is_epsilon = Grammar.is_epsilon


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


def _collect_nonliteral_rhs_types(rhs: Rhs) -> List[TargetType]:
    """Collect types from RHS elements that produce action parameters (skipping LitTerminals)."""
    if isinstance(rhs, Sequence):
        types = []
        for elem in rhs.elements:
            types.extend(_collect_nonliteral_rhs_types(elem))
        return types
    elif isinstance(rhs, LitTerminal):
        return []
    else:
        return [rhs.target_type()]
