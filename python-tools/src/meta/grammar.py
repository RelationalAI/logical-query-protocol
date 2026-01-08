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
    """Base class for right-hand sides of grammar rules.

    Rhs nodes represent the right-hand side of a grammar production rule.
    They form a tree structure that describes the syntax pattern to match.

    Subclasses:
        - Terminal: Base class for terminal symbols
            - LitTerminal: Literal keywords like "if", "("
            - NamedTerminal: Token types like SYMBOL, INT
        - Nonterminal: References to other grammar rules
        - Star: Zero-or-more repetition (e.g., expr*)
        - Option: Optional element (e.g., expr?)
        - Sequence: Concatenation of multiple Rhs elements

    The target_type() method returns the type of value produced when parsing
    this Rhs element. For example:
        - LitTerminal("if") produces no value (empty tuple type)
        - NamedTerminal("INT", Int64) produces Int64
        - Star(expr) produces List[expr.target_type()]
        - Option(expr) produces Option[expr.target_type()]

    Example:
        # Grammar rule: expr -> "(" SYMBOL expr* ")"
        rhs = Sequence((
            LitTerminal("("),
            NamedTerminal("SYMBOL", BaseType("String")),
            Star(Nonterminal("expr", MessageType("proto", "Expr"))),
            LitTerminal(")")
        ))
        # rhs.target_type() returns TupleType([String, List[proto.Expr]])
    """

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
    """Zero or more repetitions (*).

    Only Nonterminal and NamedTerminal are allowed since LitTerminal
    produces no value, making Star(LitTerminal) semantically meaningless.
    """
    rhs: 'Nonterminal | NamedTerminal'

    def __str__(self) -> str:
        return f"{self.rhs}*"

    def target_type(self) -> TargetType:
        """Return list type of the element type."""
        return ListType(self.rhs.target_type())


@dataclass(frozen=True)
class Option(Rhs):
    """Optional element (?).

    Only Nonterminal and NamedTerminal are allowed since LitTerminal
    produces no value, making Option(LitTerminal) semantically meaningless.
    """
    rhs: 'Nonterminal | NamedTerminal'

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

    A Rule represents a grammar production of the form:
        lhs -> rhs { construct_action }

    The construct_action is a Lambda that takes the values parsed from the
    non-literal RHS elements and constructs the result value. Literal terminals
    (like keywords) don't produce values and are skipped when binding parameters.

    Attributes:
        lhs: The nonterminal being defined
        rhs: The right-hand side pattern to match
        construct_action: Lambda to construct result from parsed values
        source_type: Optional protobuf type name this rule was generated from

    Example:
        # Rule: value -> "(" "date" INT INT INT ")"
        # Parses: (date 2024 1 15) -> DateValue(year=2024, month=1, day=15)
        rule = Rule(
            lhs=Nonterminal("value", MessageType("proto", "DateValue")),
            rhs=Sequence((
                LitTerminal("("), LitTerminal("date"),
                NamedTerminal("INT", BaseType("Int64")),  # year
                NamedTerminal("INT", BaseType("Int64")),  # month
                NamedTerminal("INT", BaseType("Int64")),  # day
                LitTerminal(")")
            )),
            construct_action=Lambda(
                params=[Var("year", Int64), Var("month", Int64), Var("day", Int64)],
                return_type=MessageType("proto", "DateValue"),
                body=Call(Message("proto", "DateValue"), [year, month, day])
            )
        )
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
    """Token definition (terminal with regex pattern).

    A Token defines a lexical token that can be recognized by the lexer.
    It maps a regex pattern to a named terminal with an associated type.

    Attributes:
        name: The token name (e.g., "INT", "SYMBOL", "STRING")
        pattern: Regex pattern to match the token
        type: The type of value produced when this token is scanned

    Example:
        # Define tokens for a simple expression language
        int_token = Token("INT", r'[-]?\\d+', BaseType("Int64"))
        symbol_token = Token("SYMBOL", r'[a-zA-Z_][a-zA-Z0-9_]*', BaseType("String"))
        string_token = Token("STRING", r'"[^"]*"', BaseType("String"))
    """
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

    def partition_nonterminals(self) -> Tuple[List[Nonterminal], List[Nonterminal]]:
        """Partition nonterminals into reachable and unreachable.

        Returns a tuple of:
            - reachable: List of reachable nonterminals in preorder traversal
            - unreachable: List of unreachable nonterminals (sorted by name)
        """
        visited: Set[Nonterminal] = set()
        reachable: List[Nonterminal] = []

        def visit(A: Nonterminal) -> None:
            """Visit nonterminal and its dependencies in preorder."""
            if A in visited or A not in self.rules:
                return
            visited.add(A)
            reachable.append(A)
            for rule in self.rules[A]:
                for B in get_nonterminals(rule.rhs):
                    visit(B)

        visit(self.start)

        unreachable = sorted(
            [nt for nt in self.rules.keys() if nt not in visited],
            key=lambda nt: nt.name
        )

        return reachable, unreachable

    def get_rules(self, nt: Nonterminal) -> List[Rule]:
        """Get all rules with the given LHS name."""
        return self.rules.get(nt, [])

    def has_rule(self, name: Nonterminal) -> bool:
        """Check if any rule has the given LHS name."""
        return name in self.rules

    def print_grammar(self, reachable_only: bool = True) -> str:
        """Convert to context-free grammar format with actions."""
        lines = []
        lines.append("// Auto-generated grammar from protobuf specifications")
        lines.append("")

        reachable, unreachable = self.partition_nonterminals()
        rule_order = reachable if reachable_only else reachable + unreachable

        for lhs in rule_order:
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


# Helper functions

# Import traversal utilities here to avoid circular imports
from .grammar_utils import get_nonterminals, get_literals, collect  # noqa: E402


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
