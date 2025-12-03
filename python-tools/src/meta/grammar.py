"""Grammar data structures for meta-language tools.

This module defines the data structures for representing context-free grammars
with semantic actions, including support for normalization and left-factoring.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

# Import action AST types
from .target import TargetExpr, Var, Symbol, Call, Lambda, Let, Lit


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
class Star(Rhs):
    """Zero or more repetitions (*)."""
    rhs: 'Rhs'

    def __post_init__(self):
        assert isinstance(self.rhs, Nonterminal) or isinstance(self.rhs, Terminal), \
            f"Star child must be Nonterminal or Terminal, got {type(self.rhs).__name__}"

    def __str__(self) -> str:
        return f"{self.rhs}*"


@dataclass
class Plus(Rhs):
    """One or more repetitions (+)."""
    rhs: 'Rhs'

    def __post_init__(self):
        assert isinstance(self.rhs, Nonterminal) or isinstance(self.rhs, Terminal), \
            f"Plus child must be Nonterminal, got {type(self.rhs).__name__}"

    def __str__(self) -> str:
        return f"{self.rhs}+"


@dataclass
class Option(Rhs):
    """Optional element (?)."""
    rhs: 'Rhs'

    def __post_init__(self):
        assert isinstance(self.rhs, Nonterminal) or isinstance(self.rhs, Terminal), \
            f"Option child must be Nonterminal, got {type(self.rhs).__name__}"

    def __str__(self) -> str:
        return f"{self.rhs}?"


# Grammar rules and tokens

@dataclass
class Rule:
    """Grammar rule (production)."""
    lhs: Nonterminal
    rhs: List[Rhs]
    action: Optional['Lambda'] = None
    source_type: Optional[str] = None  # Track the protobuf type this rule came from
    skip_validation: bool = False  # Skip action parameter validation (for normalized grammars)

    def to_pattern(self, grammar: Optional['Grammar'] = None) -> str:
        """Convert RHS to pattern string."""
        return ' '.join(str(elem) for elem in self.rhs)

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
    tokens: List[Token] = field(default_factory=list)
    start: Optional[str] = None  # Start nonterminal name

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
            # Set start symbol to first rule added if not already set
            if self.start is None:
                self.start = lhs_name
        self.rules[lhs_name].append(rule)

    def _count_rhs_elements(self, rhs: List[Rhs]) -> int:
        """Count the number of elements in an RHS that produce action parameters.

        This counts all RHS elements, as each position (including literals, options,
        stars, etc.) corresponds to a parameter in the action lambda.
        """
        return sum(1 for elem in rhs if not isinstance(elem, Literal))

    def traverse_rules_preorder(self, start: Optional[str] = None, reachable_only: bool = True) -> List[str]:
        """Traverse rules in preorder starting from start symbol.

        Returns list of nonterminal names in the order they should be printed.
        If reachable_only is True, only includes reachable nonterminals.
        """
        if start is None:
            start = self.start
        if start is None:
            # No start symbol, return all rules in arbitrary order
            return sorted(self.rules.keys())

        visited = set()
        result = []

        def collect_nonterminals_from_elem(rhs: Rhs) -> List[str]:
            """Collect all nonterminals referenced in RHS."""
            nts = []
            if isinstance(rhs, Nonterminal):
                nts.append(rhs.name)
            elif isinstance(rhs, (Star, Plus, Option)):
                nts.extend(collect_nonterminals_from_elem(rhs.rhs))
            return nts

        def collect_nonterminals(rhs: List[Rhs]) -> List[str]:
            """Collect all nonterminals referenced in RHS."""
            nts = []
            for elem in rhs:
                nts.extend(collect_nonterminals_from_elem(elem))
            return nts

        def visit(nt_name: str) -> None:
            """Visit nonterminal and its dependencies in preorder."""
            if nt_name in visited or nt_name not in self.rules:
                return
            visited.add(nt_name)
            result.append(nt_name)

            # Visit all nonterminals referenced in this rule's RHS
            for rule in self.rules[nt_name]:
                for ref_nt in collect_nonterminals(rule.rhs):
                    visit(ref_nt)

        visit(start)

        # If not reachable_only, add any remaining rules
        if not reachable_only:
            for nt_name in sorted(self.rules.keys()):
                if nt_name not in visited:
                    visit(nt_name)

        return result

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
            if token.priority is not None:
                lines.append(f"{token.name}.{token.priority}: {token.pattern}")
            else:
                lines.append(f"{token.name}: {token.pattern}")

        return "\n".join(lines)

    def print_grammar_with_actions(self, reachable: Optional[Set[str]] = None) -> str:
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

    def _rhs_to_name(self, rhs: List[Rhs]) -> str:
        parts = [self._rhs_elem_to_name(elem) for elem in rhs]
        return '_'.join(parts)

    def _rhs_elem_to_name(self, rhs: Rhs) -> str:
        """Convert RHS to a short name for auxiliary rule generation."""
        if isinstance(rhs, Nonterminal):
            return rhs.name
        elif isinstance(rhs, Terminal):
            return rhs.name.lower()
        elif isinstance(rhs, Literal):
            name = rhs.name
            name = name.replace(' ', '_')
            name = name.replace('|', '_bar')
            name = name.replace(':', '_colon')
            name = name.replace('.', '_dot')
            name = name.replace(',', '_comma')
            name = name.replace(';', '_semi')
            name = name.replace('!', '_bang')
            name = name.replace('*', '_star')
            name = name.replace('/', '_slash')
            name = name.replace('&', '_amp')
            name = name.replace('<', '_lt')
            name = name.replace('>', '_gt')
            name = name.replace('$', '_dollar')
            name = name.replace('#', '_hash')
            name = name.replace('(', '_lp')
            name = name.replace(')', '_rp')
            name = name.replace('[', '_lb')
            name = name.replace(']', '_rb')
            name = name.replace('{', '_lc')
            name = name.replace('}', '_rc')
            name = name.replace('-', '-')
            name = re.sub(r'[^a-zA-Z0-9_]', '_X', name)
            name = f'lit{name}'
            return name
        elif isinstance(rhs, Option):
            return f"{self._rhs_elem_to_name(rhs.rhs)}_opt"
        elif isinstance(rhs, Star):
            return f"{self._rhs_elem_to_name(rhs.rhs)}_star"
        elif isinstance(rhs, Plus):
            return f"{self._rhs_elem_to_name(rhs.rhs)}_plus"
        else:
            assert False
