"""Grammar left-factoring to eliminate common prefixes.

This module provides functionality to apply left-factoring to grammars,
eliminating common prefixes in alternative productions using Let-bindings
in semantic actions.
"""

from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .grammar import Grammar, Rhs, TargetExpr

from .grammar import (
    Grammar, Literal, Terminal, Nonterminal, Sequence, Rule,
    Lambda, Let, Call, Var
)


def left_factor_grammar(grammar: 'Grammar') -> 'Grammar':
    """
    Apply left-factoring to eliminate common prefixes.

    For rules with common prefixes:
      A -> α β₁  with action f₁
      A -> α β₂  with action f₂

    Becomes:
      A -> α A'  with action: let x1 = parse_α1 in ... let xk = parse_αk in parse_A'(x1, ..., xk)
      A' -> β₁   with action: λ(x1, ..., xk). f₁(x1, ..., xk, parse_β₁)
      A' -> β₂   with action: λ(x1, ..., xk). f₂(x1, ..., xk, parse_β₂)

    Returns a new left-factored Grammar instance.
    """
    factored = Grammar()
    factored.tokens = grammar.tokens.copy()
    factored.imports = grammar.imports.copy()
    factored.ignores = grammar.ignores.copy()

    counter = [0]

    def fresh_continuation_name(base: str) -> str:
        name = f"{base}_cont_{counter[0]}"
        counter[0] += 1
        return name

    def fresh_var_name(base: str, idx: int) -> str:
        """Generate fresh variable name for Let-bindings."""
        return f"{base}_{idx}"

    def find_common_prefix(seqs: List[Sequence]) -> Tuple[List['Rhs'], List[List['Rhs']]]:
        """Find longest common prefix among sequences.

        Returns (prefix, suffixes) where prefix is the common prefix
        and suffixes are the remaining parts of each sequence.
        """
        if not seqs:
            return ([], [])

        min_len = min(len(seq.elements) for seq in seqs)
        prefix_len = 0

        for i in range(min_len):
            first_elem = seqs[0].elements[i]
            if all(_rhs_equal(seq.elements[i], first_elem) for seq in seqs):
                prefix_len += 1
            else:
                break

        if prefix_len == 0:
            return ([], [seq.elements for seq in seqs])

        prefix = seqs[0].elements[:prefix_len]
        suffixes = [seq.elements[prefix_len:] for seq in seqs]
        return (prefix, suffixes)

    def _rhs_equal(rhs1: 'Rhs', rhs2: 'Rhs') -> bool:
        """Check if two RHS elements are equal."""
        if type(rhs1) != type(rhs2):
            return False

        if isinstance(rhs1, Literal):
            return rhs1.name == rhs2.name
        elif isinstance(rhs1, Terminal):
            return rhs1.name == rhs2.name
        elif isinstance(rhs1, Nonterminal):
            return rhs1.name == rhs2.name
        elif isinstance(rhs1, Sequence):
            if len(rhs1.elements) != len(rhs2.elements):
                return False
            return all(_rhs_equal(e1, e2) for e1, e2 in zip(rhs1.elements, rhs2.elements))
        else:
            return False

    def build_continuation_action(original_action: Lambda, prefix_len: int, suffix_len: int) -> Lambda:
        """Build action for continuation rule: λ(x1, ..., xk, suffix_params). original_action(x1, ..., xk, suffix_params)

        The continuation receives the prefix variables as parameters, followed by
        the suffix variables from parsing the remainder.
        """
        if original_action is None:
            return None

        # Continuation params: prefix vars + suffix vars
        prefix_params = [f'x{i}' for i in range(prefix_len)]
        suffix_params = original_action.params[prefix_len:] if len(original_action.params) > prefix_len else []

        cont_params = prefix_params + suffix_params

        # Body: call original action with all params
        body = original_action.body

        return Lambda(params=cont_params, body=body)

    def build_let_action(prefix: List['Rhs'], cont_nt_name: str) -> 'TargetExpr':
        """Build Let-binding action for factored rule.

        Generates: let x1 = parse_α1 in ... let xk = parse_αk in parse_A'(x1, ..., xk)
        """
        prefix_vars = [f'x{i}' for i in range(len(prefix))]

        # Build the innermost expression: call to continuation with prefix vars
        # This represents: parse_A'(x1, ..., xk)
        innermost = Call(f'parse_{cont_nt_name}', [Var(v) for v in prefix_vars])

        # Build nested Let-bindings from right to left
        result = innermost
        for i in range(len(prefix) - 1, -1, -1):
            # Each Let binds: let xi = parse_αi in ...
            parse_call = Call(f'parse_{_rhs_to_name(prefix[i])}', [])
            result = Let(var=prefix_vars[i], expr1=parse_call, expr2=result)

        return result

    def _rhs_to_name(rhs: 'Rhs') -> str:
        """Convert RHS to method name for parsing."""
        if isinstance(rhs, Nonterminal):
            return rhs.name
        elif isinstance(rhs, Terminal):
            return rhs.name.lower()
        elif isinstance(rhs, Literal):
            return f'literal_{rhs.name}'
        else:
            return 'aux'

    for lhs_name in grammar.rule_order:
        rules_list = grammar.rules[lhs_name]

        if len(rules_list) == 1:
            # Single rule - no factoring needed
            factored.add_rule(rules_list[0])
            continue

        # Group rules by whether they're sequences
        sequence_rules = []
        other_rules = []

        for rule in rules_list:
            if isinstance(rule.rhs, Sequence):
                sequence_rules.append(rule)
            else:
                other_rules.append(rule)

        # Add non-sequence rules unchanged
        for rule in other_rules:
            factored.add_rule(rule)

        # Try to factor sequence rules
        if len(sequence_rules) > 1:
            sequences = [rule.rhs for rule in sequence_rules]
            prefix, suffixes = find_common_prefix(sequences)

            if len(prefix) > 0:
                # Create continuation nonterminal
                cont_name = fresh_continuation_name(lhs_name)
                cont_nt = Nonterminal(cont_name)

                # Create factored rule: A -> α A'
                # Action: let x1 = parse_α1 in ... let xk = parse_αk in parse_A'(x1, ..., xk)
                factored_rhs = Sequence(prefix + [cont_nt])
                let_action = build_let_action(prefix, cont_name)

                # Wrap in lambda with no parameters (actions are always functions)
                factored_action = Lambda(params=[], body=let_action)

                factored_rule = Rule(
                    lhs=Nonterminal(lhs_name),
                    rhs=factored_rhs,
                    action=factored_action,
                    grammar=factored,
                    source_type=rules_list[0].source_type if rules_list else None
                )
                factored.add_rule(factored_rule)

                # Create continuation rules: A' -> β₁ | β₂ | ...
                # Each with action: λ(x1, ..., xk, suffix_params). original_action(x1, ..., xk, suffix_params)
                for i, suffix in enumerate(suffixes):
                    suffix_seq = Sequence(suffix) if suffix else Sequence([])
                    original_action = sequence_rules[i].action

                    # Build continuation action
                    cont_action = build_continuation_action(
                        original_action,
                        prefix_len=len(prefix),
                        suffix_len=len(suffix)
                    )

                    cont_rule = Rule(
                        lhs=cont_nt,
                        rhs=suffix_seq,
                        action=cont_action,
                        grammar=factored,
                        source_type=sequence_rules[i].source_type
                    )
                    factored.add_rule(cont_rule)
            else:
                # No common prefix - add rules unchanged
                for rule in sequence_rules:
                    factored.add_rule(rule)
        else:
            # Single sequence or no sequences - add unchanged
            for rule in sequence_rules:
                factored.add_rule(rule)

    return factored
