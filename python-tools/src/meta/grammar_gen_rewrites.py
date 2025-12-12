"""Grammar rule rewrites for transforming protobuf-generated rules.

These rewrites transform grammar rules generated from protobuf definitions
into forms more suitable for parsing S-expressions.
"""

from typing import Callable, Dict, Optional

from .grammar import Rule, Rhs, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence
from .target import Lambda, Call, Var, Builtin, Message, BaseType, MessageType, ListType, TupleType


def make_symbol_replacer(replacements: Dict[Rhs, Rhs]) -> Callable[[Rule], Rule]:
    """Create a rule rewriter that replaces symbols in the RHS.

    replacements is a dict mapping old Rhs elements to new Rhs elements.
    """
    def rewrite(rule: Rule) -> Rule:
        if isinstance(rule.rhs, Sequence):
            new_elements = [replacements.get(elem, elem) for elem in rule.rhs.elements]
            return Rule(lhs=rule.lhs, rhs=Sequence(new_elements), action=rule.action, source_type=rule.source_type)
        return rule
    return rewrite


def get_rule_rewrites() -> Dict[str, Callable[[Rule], Rule]]:
    """Return rule rewrite functions.

    These rewrites transform grammar rules generated from protobuf definitions
    into forms more suitable for parsing S-expressions. The rewrites address
    several concerns:

    1. **Token granularity**: Protobuf uses STRING tokens, but the S-expression
       grammar parses names as structured nonterminals (SYMBOL tokens). Rewrites
       like `rewrite_string_to_name` replace STRING terminals with `name` nonterminals.

    2. **Optional vs repeated**: Protobuf `repeated` fields generate `terms?`
       (optional list), but S-expressions use `term*` (zero-or-more). Rewrites
       like `rewrite_terms_optional_to_star_term` make this transformation.

    3. **Abstraction flattening**: The `exists` quantifier in protobuf has a
       nested `abstraction` field, but S-expressions parse bindings and formula
       separately. `rewrite_exists` flattens this structure.

    4. **Arity extraction**: Some constructs (upsert, monoid_def, monus_def)
       have an INT arity that follows an abstraction. `rewrite_compute_value_arity`
       combines these into a single `abstraction_with_arity` nonterminal that
       returns a tuple, avoiding lookahead issues.

    5. **Debug info removal**: Fragment debug_info is computed at parse time,
       not parsed from input. `rewrite_fragment_remove_debug_info` removes it.

    Returns:
        A dict mapping nonterminal names to their rewrite functions.
    """
    # Common types
    string_type = BaseType('String')
    terms_type = ListType(MessageType('Term'))

    # Common replacement patterns
    string_to_name = {
        NamedTerminal('STRING', string_type): Nonterminal('name', string_type),
    }
    string_to_name_optional = {
        NamedTerminal('STRING', string_type): Option(Nonterminal('name', string_type)),
    }
    terms_optional_to_star_term = {
        Option(Nonterminal('terms', terms_type)): Star(Nonterminal('term', terms_type)),
    }
    terms_optional_to_star_relterm = {
        Option(Nonterminal('terms', terms_type)): Star(Nonterminal('relterm', terms_type)),
    }
    args_optional_to_star_value = {
        Option(Nonterminal('args', terms_type)): Star(Nonterminal('value', terms_type)),
    }
    term_star_to_relterm_star = {
        Star(Nonterminal('term', terms_type)): Star(Nonterminal('relterm', terms_type)),
    }

    rewrite_string_to_name_optional = make_symbol_replacer(string_to_name_optional)
    rewrite_string_to_name = make_symbol_replacer(string_to_name)
    rewrite_terms_optional_to_star_term = make_symbol_replacer(terms_optional_to_star_term)

    rewrite_terms_optional_to_star_relterm = make_symbol_replacer(
        {**terms_optional_to_star_relterm, **string_to_name})

    rewrite_primitive_rule = make_symbol_replacer(
        {**string_to_name, **term_star_to_relterm_star})

    rewrite_relatom_rule = make_symbol_replacer(
        {**string_to_name, **terms_optional_to_star_relterm})

    rewrite_attribute_rule = make_symbol_replacer(
        {**string_to_name, **args_optional_to_star_value})

    rewrite_ffi_pragma = make_symbol_replacer(
        {**string_to_name, **terms_optional_to_star_term})

    return {
        'output': rewrite_string_to_name_optional,
        'abort': rewrite_string_to_name_optional,
        'ffi': rewrite_ffi_pragma,
        'pragma': rewrite_ffi_pragma,
        'fragment': _rewrite_fragment_remove_debug_info,
        'atom': rewrite_terms_optional_to_star_term,
        'rel_atom': rewrite_terms_optional_to_star_relterm,
        'primitive': rewrite_primitive_rule,
        'exists': _rewrite_exists,
        'upsert': _rewrite_compute_value_arity,
        'monoid_def': _rewrite_compute_value_arity,
        'monus_def': _rewrite_compute_value_arity,
        'relatom': rewrite_relatom_rule,
        'attribute': rewrite_attribute_rule,
    }


def _rewrite_fragment_remove_debug_info(rule: Rule) -> Rule:
    """Remove debug_info from fragment rules.

    Debug info is computed during parsing (from source positions and
    variable names), not parsed from input. This removes the debug_info
    field from the grammar and adjusts the action accordingly.
    """
    def remove_debug_info(elem: Rhs) -> Optional[Rhs]:
        if isinstance(elem, Option) and isinstance(elem.rhs, Nonterminal) and elem.rhs.name == 'debug_info':
            return None
        if isinstance(elem, Nonterminal) and elem.name == 'debug_info':
            return None
        return elem

    if isinstance(rule.rhs, Sequence):
        new_elements = [e for e in rule.rhs.elements if remove_debug_info(e) is not None]
        new_params = list(rule.action.params[:-1])
        new_action = Lambda(params=new_params, return_type=rule.action.return_type, body=rule.action.body)
        return Rule(lhs=rule.lhs, rhs=Sequence(new_elements), action=new_action, source_type=rule.source_type)
    return rule


def _rewrite_exists(rule: Rule) -> Rule:
    """Rewrite exists rule to use bindings and formula instead of abstraction.

    The protobuf schema has `exists` with a nested `abstraction` field
    containing bindings and a formula. But in S-expressions, we parse
    `(exists (bindings...) formula)` directly. This rewrite:
    1. Replaces the `abstraction` nonterminal with `bindings` and `formula`
    2. Updates the action to construct the Abstraction from these parts
    """
    if isinstance(rule.rhs, Sequence):
        new_elements = []
        abstraction_found = False
        for elem in rule.rhs.elements:
            if isinstance(elem, Nonterminal) and elem.name == 'abstraction':
                new_elements.append(Nonterminal('bindings', TupleType([ListType(MessageType('logic', 'Binding')), ListType(MessageType('logic', 'Binding'))])))
                new_elements.append(Nonterminal('formula', MessageType('logic', 'Formula')))
                abstraction_found = True
            else:
                new_elements.append(elem)
        if abstraction_found:
            # Update action to take bindings and formula instead of abstraction
            new_params = []
            for param in rule.action.params:
                if param.name not in ('abstraction', 'x', 'body'):
                    new_params.append(param)
                else:
                    new_params.append(Var('bindings', TupleType([ListType(MessageType('logic', 'Binding')), ListType(MessageType('logic', 'Binding'))])))
                    new_params.append(Var('formula', MessageType('logic', 'Formula')))
            bindings_type = TupleType([ListType(MessageType('logic', 'Binding')), ListType(MessageType('logic', 'Binding'))])
            abstraction_construction = Call(
                Message('logic', 'Abstraction'),
                [
                    Call(Builtin('list_concat'), [
                        Call(Builtin('fst'), [Var('bindings', bindings_type)]),
                        Call(Builtin('snd'), [Var('bindings', bindings_type)])
                    ]),
                    Var('formula', MessageType('logic', 'Formula'))
                ]
            )
            new_action = Lambda(
                params=new_params,
                return_type=rule.action.return_type,
                body=Call(Message('logic', 'Exists'), [abstraction_construction])
            )
            return Rule(lhs=rule.lhs, rhs=Sequence(new_elements), action=new_action, source_type=rule.source_type)
    return rule


def _rewrite_compute_value_arity(rule: Rule) -> Rule:
    """Rewrite `body ... INT` to `body_with_arity ...` where body is an Abstraction field.

    For upsert, monoid_def, and monus_def, the protobuf schema has an
    abstraction followed by an integer arity. Parsing these separately
    requires unbounded lookahead to know when the abstraction ends.

    This rewrite combines them into `abstraction_with_arity` which returns
    a tuple (Abstraction, Int64). The action is updated to extract the
    components using fst() and snd().
    """
    if not isinstance(rule.rhs, Sequence) or len(rule.rhs.elements) < 2:
        return rule

    new_elements = list(rule.rhs.elements)
    abstraction_idx = None
    int_idx = None

    for i, elem in enumerate(new_elements):
        if isinstance(elem, Nonterminal) and elem.name in ('abstraction', 'body'):
            abstraction_idx = i
        elif isinstance(elem, NamedTerminal) and elem.name in ('INT', 'NUMBER'):
            int_idx = i

    if abstraction_idx is None or int_idx is None:
        return rule

    elem = new_elements[abstraction_idx]
    tuple_type = TupleType([elem.type, BaseType('Int64')])
    new_elements[abstraction_idx] = Nonterminal('abstraction_with_arity', tuple_type)
    new_elements.pop(int_idx)

    # Find the parameter index for the abstraction
    abstraction_param_idx = None
    param_idx = 0
    for i, elem in enumerate(rule.rhs.elements):
        if not isinstance(elem, LitTerminal):
            if i == abstraction_idx:
                abstraction_param_idx = param_idx
                break
            param_idx += 1

    old_abstraction_param = rule.action.params[abstraction_param_idx]
    new_abstraction_param = Var(old_abstraction_param.name, tuple_type)

    new_params = []
    for i, param in enumerate(rule.action.params):
        if i == abstraction_param_idx:
            new_params.append(new_abstraction_param)
        elif i != len(rule.action.params) - 1:  # Skip the last param (value_arity)
            new_params.append(param)

    # Rewrite action body to replace old_abstraction_param with fst(new_abstraction_param)
    # and replace value_arity param with snd(new_abstraction_param)
    def replace_vars(expr):
        from .target import Let
        if isinstance(expr, Var):
            if expr.name == old_abstraction_param.name:
                return Call(Builtin('fst'), [new_abstraction_param])
            elif expr.name == rule.action.params[-1].name:
                return Call(Builtin('snd'), [new_abstraction_param])
            return expr
        elif isinstance(expr, Call):
            return Call(expr.func, [replace_vars(arg) for arg in expr.args])
        elif isinstance(expr, Let):
            return Let(expr.var, replace_vars(expr.init), replace_vars(expr.body))
        return expr

    new_body = replace_vars(rule.action.body)
    new_action = Lambda(params=new_params, return_type=rule.action.return_type, body=new_body)
    return Rule(lhs=rule.lhs, rhs=Sequence(new_elements), action=new_action, source_type=rule.source_type)
