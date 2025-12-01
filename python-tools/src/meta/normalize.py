"""Grammar normalization to eliminate EBNF operators.

This module provides functionality to normalize grammars by eliminating *, +, and ?
operators, replacing them with auxiliary nonterminals.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .grammar import Grammar, Rhs

from .grammar import (
    Grammar, Literal, Terminal, Nonterminal, Sequence, Star, Plus, Option,
    Rule, Lambda, Call, Var
)


def normalize_grammar(grammar: 'Grammar') -> 'Grammar':
    """
    Normalize grammar by eliminating *, +, and ? operators.

    Creates fresh nonterminals for each EBNF operator:
    - A* becomes A_star with rules: A_star -> A A_star | epsilon
    - A+ becomes A_plus with rules: A_plus -> A A_star
    - A? becomes A_opt with rules: A_opt -> A | epsilon

    Returns a new normalized Grammar instance.
    """
    normalized = Grammar()
    normalized.tokens = grammar.tokens.copy()
    normalized.imports = grammar.imports.copy()
    normalized.ignores = grammar.ignores.copy()

    # Track created auxiliary nonterminals to avoid duplicates
    created_aux: dict[str, Nonterminal] = {}

    def normalize_rhs(rhs: 'Rhs') -> 'Rhs':
        """Recursively normalize an RHS, generating auxiliary rules."""
        if isinstance(rhs, (Literal, Terminal, Nonterminal)):
            return rhs
        elif isinstance(rhs, Sequence):
            normalized_elements = [normalize_rhs(elem) for elem in rhs.elements]
            return Sequence(normalized_elements)
        elif isinstance(rhs, Star):
            inner = normalize_rhs(rhs.rhs)
            star_name = f"{grammar._rhs_to_name(inner)}_star"

            # Reuse existing nonterminal if already created
            if star_name in created_aux:
                return created_aux[star_name]

            star_nt = Nonterminal(star_name)
            created_aux[star_name] = star_nt

            normalized.add_rule(Rule(
                lhs=star_nt,
                rhs=Sequence([inner, star_nt]),
                action=Lambda(params=['x', 'xs'], body=Call('Cons', [Var('x'), Var('xs')])),
                grammar=normalized
            ))
            normalized.add_rule(Rule(
                lhs=star_nt,
                rhs=Sequence([]),
                action=Lambda(params=[], body=Call('List', [])),
                grammar=normalized
            ))
            return star_nt
        elif isinstance(rhs, Plus):
            inner = normalize_rhs(rhs.rhs)
            plus_name = f"{grammar._rhs_to_name(inner)}_plus"
            star_name = f"{grammar._rhs_to_name(inner)}_star"

            # Reuse existing nonterminal if already created
            if plus_name in created_aux:
                return created_aux[plus_name]

            plus_nt = Nonterminal(plus_name)
            created_aux[plus_name] = plus_nt

            # Create or reuse star nonterminal
            if star_name not in created_aux:
                star_nt = Nonterminal(star_name)
                created_aux[star_name] = star_nt
                normalized.add_rule(Rule(
                    lhs=star_nt,
                    rhs=Sequence([inner, star_nt]),
                    action=Lambda(params=['x', 'xs'], body=Call('Cons', [Var('x'), Var('xs')])),
                    grammar=normalized
                ))
                normalized.add_rule(Rule(
                    lhs=star_nt,
                    rhs=Sequence([]),
                    action=Lambda(params=[], body=Call('List', [])),
                    grammar=normalized
                ))
            else:
                star_nt = created_aux[star_name]

            normalized.add_rule(Rule(
                lhs=plus_nt,
                rhs=Sequence([inner, star_nt]),
                action=Lambda(params=['x', 'xs'], body=Call('Cons', [Var('x'), Var('xs')])),
                grammar=normalized
            ))
            return plus_nt
        elif isinstance(rhs, Option):
            inner = normalize_rhs(rhs.rhs)
            opt_name = f"{grammar._rhs_to_name(inner)}_opt"

            # Reuse existing nonterminal if already created
            if opt_name in created_aux:
                return created_aux[opt_name]

            opt_nt = Nonterminal(opt_name)
            created_aux[opt_name] = opt_nt

            # Count elements in inner RHS for action parameters
            if isinstance(inner, Sequence):
                elements = [element for element in inner.elements if not isinstance(element, Literal)]
                num_params = len(elements)
                params = [f'x{i}' for i in range(num_params)]
                # Return tuple if multiple elements
                if num_params > 1:
                    tuple_elems = ', '.join(params)
                    action_body = Var(f'({tuple_elems})')
                else:
                    action_body = Var(params[0])
            else:
                params = ['x']
                action_body = Var('x')

            normalized.add_rule(Rule(
                lhs=opt_nt,
                rhs=inner,
                action=Lambda(params=params, body=action_body),
                grammar=normalized
            ))
            normalized.add_rule(Rule(
                lhs=opt_nt,
                rhs=Sequence([]),
                action=Lambda(params=[], body=Var('None')),
                grammar=normalized
            ))
            return opt_nt
        else:
            return rhs

    for lhs_name in grammar.rule_order:
        for rule in grammar.rules[lhs_name]:
            normalized_rhs = normalize_rhs(rule.rhs)
            new_rule = Rule(
                lhs=Nonterminal(lhs_name),
                rhs=normalized_rhs,
                action=rule.action,
                grammar=normalized,
                source_type=rule.source_type,
                skip_validation=True
            )
            normalized.add_rule(new_rule)

    return normalized
