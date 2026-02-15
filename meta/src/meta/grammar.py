"""Grammar data structures for meta-language tools.

This module defines the data structures for representing context-free grammars
with semantic actions, including support for normalization and left-factoring.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

# Import action AST types
from .target import Lambda, TargetType, SequenceType, ListType, OptionType, TupleType, FunDef

# Use TYPE_CHECKING to avoid circular import: GrammarAnalysis imports Grammar,
# but we need GrammarAnalysis type hints here. These imports only exist during
# type checking, not at runtime.
if TYPE_CHECKING:
    from .grammar_analysis import GrammarAnalysis


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

    Any Rhs can be used except LitTerminal, since LitTerminal
    produces no value, making Star(LitTerminal) semantically meaningless.
    """
    rhs: Rhs

    def __str__(self) -> str:
        return f"{self.rhs}*"

    def target_type(self) -> TargetType:
        """Return sequence type of the element type."""
        return SequenceType(self.rhs.target_type())


@dataclass(frozen=True)
class Option(Rhs):
    """Optional element (?).

    Any Rhs can be used except LitTerminal, since LitTerminal
    produces no value, making Option(LitTerminal) semantically meaningless.
    """
    rhs: Rhs

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
        lhs -> rhs { constructor }

    The constructor is a Lambda that takes the values parsed from the
    non-literal RHS elements and constructs the result value. Literal terminals
    (like keywords) don't produce values and are skipped when binding parameters.

    Attributes:
        lhs: The nonterminal being defined
        rhs: The right-hand side pattern to match
        constructor: Lambda to construct result from parsed values
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
            constructor=Lambda(
                params=[Var("year", Int64), Var("month", Int64), Var("day", Int64)],
                return_type=MessageType("proto", "DateValue"),
                body=Call(Message("proto", "DateValue"), [year, month, day])
            )
        )
    """
    lhs: Nonterminal
    rhs: Rhs
    constructor: 'Lambda'
    deconstructor: Optional['Lambda'] = None  # Pretty-printer deconstruction action
    source_type: Optional[str] = None  # Track the protobuf type this rule came from

    def __str__(self):
        result = f"{self.lhs.name} -> {self.rhs} {{{{ {self.constructor} }}}}"
        return result

    def to_pattern(self, grammar: Optional['Grammar'] = None) -> str:
        """Convert RHS to pattern string."""
        return str(self.rhs)

    def __post_init__(self):
        from .grammar_utils import count_nonliteral_rhs_elements
        assert isinstance(self.rhs, Rhs)
        rhs_len = count_nonliteral_rhs_elements(self.rhs)
        action_params = len(self.constructor.params)
        assert action_params == rhs_len, (
            f"Action for {self.lhs.name} has {action_params} parameter(s) "
            f"but RHS has {rhs_len} non-literal element(s): {self.rhs}"
        )


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
    ignored_completeness: List[str] = field(default_factory=list)  # Message names to ignore in completeness checks
    function_defs: Dict[str, 'FunDef'] = field(default_factory=dict)  # User-defined functions with IR bodies

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
        """Add a rule to the grammar.

        The grammar must not have been analyzed yet. Once the .analysis property
        is accessed, the grammar is frozen and no more rules can be added.
        """
        assert self._analysis is None, "Grammar is already analyzed"

        lhs = rule.lhs
        if lhs not in self.rules:
            self.rules[lhs] = []
            # Set start symbol to first rule added if default
            if self.start.name == "start" and len(self.rules) == 0:
                self.start = lhs
        self.rules[lhs].append(rule)
        return None

    def get_rules(self, nt: Nonterminal) -> List[Rule]:
        """Get all rules with the given LHS name."""
        return self.rules.get(nt, [])

    def has_rule(self, name: Nonterminal) -> bool:
        """Check if any rule has the given LHS name."""
        return name in self.rules

    def get_unreachable_nonterminals(self) -> List[Nonterminal]:
        """Find all nonterminals that are unreachable from start symbol."""
        _, unreachable = self.analysis.partition_nonterminals_by_reachability()
        return unreachable

    def print_grammar_yacc(self, reachable_only: bool = True) -> str:
        """Convert to yacc-like grammar format.

        Returns the grammar in the yacc-like format that can be
        loaded with load_yacc_grammar().
        """
        from .target_print import type_to_str, expr_to_str

        lines = []
        lines.append("# Auto-generated grammar from protobuf specifications")
        lines.append("")

        reachable, unreachable = self.analysis.partition_nonterminals_by_reachability()
        rule_order = reachable if reachable_only else reachable + unreachable

        # Collect all named terminals from rules
        terminals: Dict[str, NamedTerminal] = {}
        for lhs in rule_order:
            for rule in self.rules[lhs]:
                for term in collect(rule.rhs, NamedTerminal):
                    if term.name not in terminals:
                        terminals[term.name] = term

        # Emit terminal declarations
        if terminals:
            for name in sorted(terminals.keys()):
                term = terminals[name]
                lines.append(f"%token {name} {type_to_str(term.type)}")
            lines.append("")

        # Emit nonterminal type declarations
        for lhs in rule_order:
            lines.append(f"%type {lhs.name} {type_to_str(lhs.type)}")
        lines.append("")

        # Emit ignored completeness directives
        for msg_name in self.ignored_completeness:
            lines.append(f"%validator_ignore_completeness {msg_name}")
        if self.ignored_completeness:
            lines.append("")

        lines.append("%%")
        lines.append("")

        # Emit rules
        for lhs in rule_order:
            rules_list = self.rules[lhs]
            lines.append(lhs.name)

            for i, rule in enumerate(rules_list):
                prefix = "    : " if i == 0 else "    | "
                rhs_str = self._rhs_to_str(rule.rhs)
                action_str = expr_to_str(rule.constructor.body)
                lines.append(f"{prefix}{rhs_str}")
                lines.append(f"      construct: {action_str}")
                if rule.deconstructor is not None:
                    decon_str = expr_to_str(rule.deconstructor.body)
                    lines.append(f"      deconstruct: {decon_str}")

            lines.append("")

        lines.append("%%")
        lines.append("")

        # Emit function definitions
        for name, func_def in self.function_defs.items():
            params_str = ", ".join(f"{p.name}: {type_to_str(p.type)}" for p in func_def.params)
            lines.append(f"def {name}({params_str}) -> {type_to_str(func_def.return_type)}:")
            if func_def.body is not None:
                lines.append(f"    return {expr_to_str(func_def.body)}")
            else:
                lines.append("    ...")
            lines.append("")

        return "\n".join(lines)

    def _rhs_to_str(self, rhs: Rhs) -> str:
        """Convert RHS to yacc-format string."""
        if isinstance(rhs, LitTerminal):
            return f'"{rhs.name}"'
        elif isinstance(rhs, NamedTerminal):
            return rhs.name
        elif isinstance(rhs, Nonterminal):
            return rhs.name
        elif isinstance(rhs, Star):
            return f"{self._rhs_to_str(rhs.rhs)}*"
        elif isinstance(rhs, Option):
            return f"{self._rhs_to_str(rhs.rhs)}?"
        elif isinstance(rhs, Sequence):
            return " ".join(self._rhs_to_str(e) for e in rhs.elements)
        else:
            return str(rhs)


@dataclass
class TerminalDef:
    """Definition of a terminal symbol with type and optional pattern."""
    type: TargetType
    pattern: Optional[str] = None  # Regex pattern or fixed string
    is_regex: bool = True  # True for r'...' patterns, False for '...' literals


@dataclass
class GrammarConfig:
    """Result of loading a grammar config file.

    This is a simpler representation than Grammar, used when loading
    grammar files before building the full Grammar object.
    """
    terminals: Dict[str, TargetType]
    start_symbol: str
    terminal_patterns: Dict[str, TerminalDef] = field(default_factory=dict)
    rules: Dict[Nonterminal, List[Rule]] = field(default_factory=dict)
    ignored_completeness: List[str] = field(default_factory=list)
    function_defs: Dict[str, FunDef] = field(default_factory=dict)


# Helper functions

# Import traversal utilities here to avoid circular imports
from .grammar_utils import collect  # noqa: E402


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
