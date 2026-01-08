"""Grammar rule rewrites for transforming protobuf-generated rules.

These rewrites transform grammar rules generated from protobuf definitions
into forms more suitable for parsing S-expressions.
"""

from typing import Callable, Dict, List, Optional

from .grammar import (
    NamedTerminal,
    LitTerminal,
    Nonterminal,
    Option,
    Rhs,
    Rule,
    Sequence,
    Star,
)

from .target import BaseType, Lambda, Call, OptionType, TupleType, MessageType, Let, Var, IfElse, Builtin, Lit
from .target_utils import apply_lambda
from .grammar_utils import rewrite_rule

def make_symbol_replacer(replacements: Dict[Rhs, Rhs]) -> Callable[[Rule], Optional[Rule]]:
    """Create a rule rewriter that replaces symbols in the RHS.

    Args:
        replacements: Dictionary mapping old RHS to new RHS.

    Returns:
        A rewrite function that replaces symbols according to the mapping.
    """
    def rewrite(rule: Rule) -> Optional[Rule]:
        """Rewrite rule by replacing symbols in RHS."""
        result = rewrite_rule(rule, replacements)
        return result if result is not rule else None

    return rewrite

def introduce_abstraction_with_arity(rule: Rule) -> Optional[Rule]:
    """For any rules with abstraction INT on the RHS, replace with abstraction_with_arity tuple."""

    if not isinstance(rule.rhs, Sequence):
        return None

    elems = rule.rhs.elements

    abstraction_idx = None
    arity_idx = None
    literals_before_abstraction = 0
    literals_before_arity = 0
    for i, elem in enumerate(elems):
        if isinstance(elem, LitTerminal):
            if abstraction_idx is None:
                literals_before_abstraction += 1
            if arity_idx is None:
                literals_before_arity += 1
        if elem == Nonterminal('abstraction', MessageType('logic', 'Abstraction')):
            abstraction_idx = i
        elif elem == NamedTerminal('INT', BaseType('Int64')):
            arity_idx = i

    if abstraction_idx is None or arity_idx is None:
        return None

    if abstraction_idx >= arity_idx:
        return None

    # Create new RHS: replace abstraction and INT with abstraction_with_arity
    abstraction_with_arity_type = TupleType([MessageType('logic', 'Abstraction'), BaseType('Int64')])
    new_elems = list(elems)
    new_elems[abstraction_idx] = Nonterminal('abstraction_with_arity', abstraction_with_arity_type)
    new_elems.pop(arity_idx)
    assert len(new_elems) == len(elems)-1
    new_rhs = Sequence(tuple(new_elems))

    # Now correct the indices to work with action parameters
    abstraction_param_idx = abstraction_idx - literals_before_abstraction
    arity_param_idx = arity_idx - literals_before_arity

    # Create new construct action: takes tuple parameter, unpacks it, calls original body
    new_params = list(rule.construct_action.params)
    tuple_param = Var('abstraction_with_arity', abstraction_with_arity_type)
    new_params[abstraction_param_idx] = tuple_param
    new_params.pop(arity_param_idx)

    abstraction_var = Var('abstraction', MessageType('logic', 'Abstraction'))
    arity_var = Var('arity', BaseType('Int64'))
    old_params_substituted = list(rule.construct_action.params)
    old_params_substituted[abstraction_param_idx] = abstraction_var
    old_params_substituted[arity_param_idx] = arity_var

    new_construct_body = Let(
        var=abstraction_var,
        init=Call(Builtin('get_tuple_element'), [tuple_param, Lit(0)]),
        body=Let(
            var=arity_var,
            init=Call(Builtin('get_tuple_element'), [tuple_param, Lit(1)]),
            body=apply_lambda(rule.construct_action, old_params_substituted)
        )
    )

    new_construct_action = Lambda(
        params=new_params,
        return_type=rule.construct_action.return_type,
        body=new_construct_body
    )

    return Rule(
        lhs=rule.lhs,
        rhs=new_rhs,
        construct_action=new_construct_action,
        source_type=rule.source_type
    )


def get_rule_rewrites() -> List[Callable[[Rule], Optional[Rule]]]:
    """Return rule rewrite functions.

    These rewrites transform grammar rules generated from protobuf definitions
    into forms more suitable for parsing S-expressions.

    Each rewrite function takes a Rule and returns either a rewritten Rule
    or None if the rewrite doesn't apply.

    Returns:
        A list of rewrite functions to apply to generated rules.
    """
    return [
        make_symbol_replacer({NamedTerminal("STRING", BaseType("String")): Nonterminal("name", BaseType("String"))}),
        introduce_abstraction_with_arity,
    ]
