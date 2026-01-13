"""Grammar rule rewrites for transforming protobuf-generated rules.

These rewrites transform grammar rules generated from protobuf definitions
into forms more suitable for parsing S-expressions.

Rewrites are applied after rules are generated from protobuf but before
the grammar is finalized. Each rewrite is a function that takes a Rule
and returns either:
- A transformed Rule if the rewrite applies
- None if the rewrite doesn't apply (rule unchanged)

Current rewrites:
1. Symbol replacement: Replace STRING terminals with 'name' nonterminal
   for better grammar structure
2. Abstraction with arity: Combine abstraction + INT into a single tuple
   to simplify rules that use both together

Example rewrite:
    Before: expr -> '(' 'lambda' abstraction INT expr ')'
    After:  expr -> '(' 'lambda' abstraction_with_arity expr ')'
    Where abstraction_with_arity produces a (Abstraction, Int64) tuple.

Usage:
    >>> rewrites = get_rule_rewrites()
    >>> for rewrite in rewrites:
    ...     new_rule = rewrite(original_rule)
    ...     if new_rule:
    ...         original_rule = new_rule
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
    """For any rules with abstraction INT on the RHS, replace with abstraction_with_arity tuple.

    Many rules have both an abstraction and an INT (arity) elements.
    This rewrite combines them into a single nonterminal that produces a tuple,
    simplifying the rule structure.

    Args:
        rule: Rule to potentially rewrite

    Returns:
        Rewritten rule if abstraction + INT pattern found, None otherwise

    Example:
        Before: lambda_expr -> abstraction body INT
                { lambda abs, body, arity -> LambdaExpr(abs, arity, body) }
        After:  lambda_expr -> abstraction_with_arity body
                { lambda tup, body -> let abs = tup[0] in let arity = tup[1] in
                  LambdaExpr(abs, arity, body) }
    """

    if not isinstance(rule.rhs, Sequence):
        return None

    elems = rule.rhs.elements

    abstraction_idx: Optional[int] = None
    arity_idx: Optional[int] = None
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
    new_params = list(rule.constructor.params)
    tuple_param = Var('abstraction_with_arity', abstraction_with_arity_type)
    new_params[abstraction_param_idx] = tuple_param
    new_params.pop(arity_param_idx)

    abstraction_var = Var('abstraction', MessageType('logic', 'Abstraction'))
    arity_var = Var('arity', BaseType('Int64'))
    old_params_substituted = list(rule.constructor.params)
    old_params_substituted[abstraction_param_idx] = abstraction_var
    old_params_substituted[arity_param_idx] = arity_var

    new_construct_body = Let(
        var=abstraction_var,
        init=Call(Builtin('get_tuple_element'), [tuple_param, Lit(0)]),
        body=Let(
            var=arity_var,
            init=Call(Builtin('get_tuple_element'), [tuple_param, Lit(1)]),
            body=apply_lambda(rule.constructor, old_params_substituted)
        )
    )

    new_constructor = Lambda(
        params=new_params,
        return_type=rule.constructor.return_type,
        body=new_construct_body
    )

    return Rule(
        lhs=rule.lhs,
        rhs=new_rhs,
        constructor=new_constructor,
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
