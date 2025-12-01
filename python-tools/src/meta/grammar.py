"""Grammar data structures for meta-language tools.

This module defines the data structures for representing context-free grammars
with semantic actions, including support for normalization and left-factoring.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

# Import action AST types
from .target import TargetExpr, Wildcard, Var, Symbol, Call, Lambda, Let


# Grammar RHS (right-hand side) elements

@dataclass
class Rhs:
    """Base class for right-hand sides of grammar rules."""
    pass


@dataclass
class Literal(Rhs):
    """Literal terminal (quoted string in grammar)."""
    name: str

    def __str__(self) -> str:
        return f'"{self.name}"'


@dataclass
class Terminal(Rhs):
    """Token terminal (unquoted uppercase name like SYMBOL, NUMBER)."""
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass
class Nonterminal(Rhs):
    """Nonterminal (rule name)."""
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass
class Sequence(Rhs):
    """Sequence of grammar symbols (concatenation)."""
    elements: List['Rhs'] = field(default_factory=list)

    def __str__(self) -> str:
        return " ".join(str(e) for e in self.elements)


@dataclass
class Star(Rhs):
    """Zero or more repetitions (*)."""
    rhs: 'Rhs'

    def __str__(self) -> str:
        if isinstance(self.rhs, Sequence):
            return f"({self.rhs})*"
        return f"{self.rhs}*"


@dataclass
class Plus(Rhs):
    """One or more repetitions (+)."""
    rhs: 'Rhs'

    def __str__(self) -> str:
        if isinstance(self.rhs, Sequence):
            return f"({self.rhs})+"
        return f"{self.rhs}+"


@dataclass
class Option(Rhs):
    """Optional element (?)."""
    rhs: 'Rhs'

    def __str__(self) -> str:
        if isinstance(self.rhs, Sequence):
            return f"({self.rhs})?"
        return f"{self.rhs}?"


# Grammar rules and tokens

@dataclass
class Rule:
    """Grammar rule (production)."""
    lhs: Nonterminal
    rhs: Rhs
    action: Optional['Lambda'] = None
    grammar: Optional['Grammar'] = field(default=None, repr=False, compare=False)
    source_type: Optional[str] = None  # Track the protobuf type this rule came from
    skip_validation: bool = False  # Skip action parameter validation (for normalized grammars)

    def to_pattern(self, grammar: Optional['Grammar'] = None) -> str:
        """Convert RHS to pattern string."""
        return str(self.rhs)

    def get_action(self) -> Optional['Lambda']:
        """Get action as Lambda."""
        return self.action


@dataclass
class Token:
    """Token definition (terminal with regex pattern)."""
    name: str
    pattern: str
    priority: Optional[int] = None


@dataclass
class Grammar:
    """Complete grammar specification with normalization and left-factoring support."""
    rules: Dict[str, List[Rule]] = field(default_factory=dict)
    rule_order: List[str] = field(default_factory=list)
    tokens: List[Token] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    ignores: List[str] = field(default_factory=list)

    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the grammar."""
        # Validate action parameters match RHS length
        # Skip validation if:
        # - Rule explicitly requests to skip validation
        # - Action uses Let-bindings (params=0, Let does the binding)
        # - Rule is a continuation (name contains '_cont_', receives prefix params)
        if rule.action and not rule.skip_validation:
            action_uses_let = isinstance(rule.action.body, Let) if rule.action.body else False
            is_continuation = '_cont_' in rule.lhs.name

            if not action_uses_let and not is_continuation:
                rhs_len = self._count_rhs_elements(rule.rhs)
                action_params = len(rule.action.params)
                assert action_params == rhs_len, \
                    f"Action for {rule.lhs.name} has {action_params} parameters but RHS has {rhs_len} elements"

        lhs_name = rule.lhs.name
        if lhs_name not in self.rules:
            self.rules[lhs_name] = []
            self.rule_order.append(lhs_name)
        self.rules[lhs_name].append(rule)

    def _count_rhs_elements(self, rhs: Rhs) -> int:
        """Count the number of elements in an RHS that produce action parameters.

        This counts all RHS elements, as each position (including literals, options,
        stars, etc.) corresponds to a parameter in the action lambda.
        """
        if isinstance(rhs, Sequence):
            return sum(1 for elem in rhs.elements if not isinstance(elem, Literal))
        elif isinstance(rhs, Literal):
            return 0
        else:
            return 1

    def get_rules(self, name: str) -> List[Rule]:
        """Get all rules with the given LHS name."""
        return self.rules.get(name, [])

    def has_rule(self, name: str) -> bool:
        """Check if any rule has the given LHS name."""
        return name in self.rules

    def has_token(self, name: str) -> bool:
        """Check if a token with the given name exists."""
        for token in self.tokens:
            if token.name == name:
                return True
        return False

    def normalize(self) -> 'Grammar':
        """
        Normalize grammar by eliminating *, +, and ? operators.

        Creates fresh nonterminals for each EBNF operator:
        - A* becomes A_star with rules: A_star -> A A_star | epsilon
        - A+ becomes A_plus with rules: A_plus -> A A_star
        - A? becomes A_opt with rules: A_opt -> A | epsilon

        Returns a new normalized Grammar instance.
        """
        from .normalize import normalize_grammar
        return normalize_grammar(self)

    def left_factor(self) -> 'Grammar':
        """
        Apply left-factoring to eliminate common prefixes.

        For rules with common prefixes:
          A -> α β₁ | α β₂
        Becomes:
          A -> α A'
          A' -> β₁ | β₂

        Semantic actions are updated to thread prefix results through.

        Returns a new left-factored Grammar instance.
        """
        from .left_factor import left_factor_grammar
        return left_factor_grammar(self)

    def check_reachability(self) -> Set[str]:
        """
        Compute set of reachable nonterminals from start symbol.

        Returns set of rule names that can be reached.
        """
        from .analysis import check_reachability
        return check_reachability(self)

    def get_unreachable_rules(self) -> List[str]:
        """
        Find all rules that are unreachable from start symbol.

        Returns list of rule names that cannot be reached.
        """
        from .analysis import get_unreachable_rules
        return get_unreachable_rules(self)

    def compute_nullable(self) -> Dict[str, bool]:
        """
        Compute nullable set for all nonterminals.

        A nonterminal is nullable if it can derive the empty string.
        Returns dict mapping nonterminal names to boolean.
        """
        from .analysis import compute_nullable
        return compute_nullable(self)

    def compute_first_k(self, k: int = 2, nullable: Optional[Dict[str, bool]] = None) -> Dict[str, Set[Tuple[str, ...]]]:
        """
        Compute FIRST_k sets for all nonterminals.

        FIRST_k(A) is the set of terminal sequences of length up to k that can begin strings derived from A.
        Returns dict mapping nonterminal names to sets of terminal tuples.
        """
        from .analysis import compute_first_k
        return compute_first_k(self, k, nullable)

    def compute_first(self, nullable: Optional[Dict[str, bool]] = None) -> Dict[str, Set[str]]:
        """
        Compute FIRST sets for all nonterminals.

        FIRST(A) is the set of terminals that can begin strings derived from A.
        Returns dict mapping nonterminal names to sets of terminal names.
        """
        from .analysis import compute_first
        return compute_first(self, nullable)

    def compute_follow(self, nullable: Optional[Dict[str, bool]] = None,
                       first: Optional[Dict[str, Set[str]]] = None) -> Dict[str, Set[str]]:
        """
        Compute FOLLOW sets for all nonterminals.

        FOLLOW(A) is the set of terminals that can immediately follow A in any derivation.
        Returns dict mapping nonterminal names to sets of terminal names.
        """
        from .analysis import compute_follow
        return compute_follow(self, nullable, first)

    def check_ll_k(self, k: int = 2) -> Tuple[bool, List[str]]:
        """
        Check if grammar is LL(k).

        Returns (is_ll_k, conflicts) where conflicts is a list of problematic nonterminals.
        """
        from .analysis import check_ll_k
        return check_ll_k(self, k)

    def print_grammar(self, reachable: Optional[Set[str]] = None) -> str:
        """Convert to Lark grammar format."""
        lines = []
        lines.append("// Auto-generated grammar from protobuf specifications")
        lines.append("")

        for lhs in self.rule_order:
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

        if self.rules and self.tokens:
            lines.append("")

        for token in self.tokens:
            if token.priority is not None:
                lines.append(f"{token.name}.{token.priority}: {token.pattern}")
            else:
                lines.append(f"{token.name}: {token.pattern}")

        if self.ignores:
            lines.append("")
            for ignore in self.ignores:
                lines.append(f"%ignore {ignore}")

        if self.imports:
            lines.append("")
            for imp in self.imports:
                lines.append(imp)

        return "\n".join(lines)

    def print_grammar_with_actions(self, reachable: Optional[Set[str]] = None) -> str:
        """Generate grammar with semantic actions in original form."""
        lines = []
        lines.append("# Grammar with semantic actions")
        lines.append("")

        for lhs in self.rule_order:
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

    def _rhs_to_name(self, rhs: Rhs) -> str:
        """Convert RHS to a short name for auxiliary rule generation."""
        if isinstance(rhs, Nonterminal):
            return rhs.name
        elif isinstance(rhs, Terminal):
            return rhs.name.lower()
        elif isinstance(rhs, Literal):
            return re.sub(r'[^a-zA-Z0-9]', '', rhs.name)
        else:
            return "aux"
