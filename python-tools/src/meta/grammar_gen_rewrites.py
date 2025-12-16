"""Grammar rule rewrites for transforming protobuf-generated rules.

These rewrites transform grammar rules generated from protobuf definitions
into forms more suitable for parsing S-expressions.

## When to Use Rule Rewrites

Rule rewrites are applied after auto-generation but before finalization. Use
rewrites when the auto-generated rule is structurally correct but needs
adjustment. Common scenarios:

1. **Token granularity mismatch**: Protobuf uses `string` fields that become
   STRING terminals, but the S-expression grammar parses structured names as
   `name` nonterminals (SYMBOL tokens). Rewrites replace STRING with name.

2. **Quantifier adjustments**: Protobuf `repeated` fields generate `terms?`
   (optional list) because the field can be absent, but S-expressions use `term*`
   (zero-or-more) for ergonomic parsing.

3. **Structure flattening**: A protobuf message may have a nested field, but
   the S-expression syntax parses the contents directly. For example, `exists`
   has an `abstraction` field, but we parse bindings and formula separately.

4. **Element combination**: Multiple grammar elements can be combined into
   composite nonterminals. For example, abstractions followed by arity
   become `abstraction_with_arity` to avoid lookahead issues.

## How Rewrites Work

A rewrite is a function `Callable[[Rule], Rule]` that takes a rule and returns
a transformed version. Rewrites should:

- Preserve the LHS nonterminal (the rule being defined)
- Modify the RHS (the symbols to match)
- Update the semantic action to match the new RHS structure
- Maintain type correctness (action parameter types must match RHS element types)

The `make_symbol_replacer()` helper creates rewrites that replace specific RHS
elements with alternatives and automatically updates action parameter types.

## Adding New Rewrites

To add a new rewrite:

1. Define the rewrite function of type `Rule -> Rule`
2. Add it to the dict returned by `get_rule_rewrites()` with the nonterminal name as key
3. The rewrite will be applied to all rules for that nonterminal

Example using `make_symbol_replacer()`:

```python
'pragma': make_symbol_replacer({
    NamedTerminal('STRING', BaseType('String')):
        Nonterminal('name', MessageType('logic', 'Name'))
})
```

## Common Rewrite Patterns

- **Symbol replacement**: Use `make_symbol_replacer()` for straightforward substitutions
- **Quantifier changes**: Replace Option with Star, or vice versa
- **Field flattening**: Replace nested message nonterminal with its constituent parts
- **Type unwrapping**: Remove Option wrappers or flatten List types in actions
- **Element merging**: Combine adjacent elements into composite nonterminals
"""

from typing import Callable, Dict, Optional

from .grammar import Rule, Rhs, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence
from .target import Lambda, Call, Var, Builtin, Message, BaseType, MessageType, ListType, TupleType, OptionType


def make_symbol_replacer(replacements: Dict[Rhs, Rhs]) -> Callable[[Rule], Rule]:
    """Create a rule rewriter that replaces symbols in the RHS.

    replacements is a dict mapping old Rhs elements to new Rhs elements.
    """
    def _rewrite_rhs(rhs: Rhs) -> Rhs:
        """Rewrite an RHS by applying replacements."""
        if rhs in replacements:
            return replacements[rhs]

        if isinstance(rhs, Sequence):
            new_elements = [_rewrite_rhs(elem) for elem in rhs.elements]
            return Sequence(tuple(new_elements))

        if isinstance(rhs, Star):
            new_element = _rewrite_rhs(rhs.rhs)
            assert isinstance(new_element, (Nonterminal, NamedTerminal)), f"Invalid rewrite: cannot rewrite {rhs.rhs} to {new_element}"
            return Star(new_element)

        if isinstance(rhs, Option):
            new_element = _rewrite_rhs(rhs.rhs)
            assert isinstance(new_element, (Nonterminal, NamedTerminal)), f"Invalid rewrite: cannot rewrite {rhs.rhs} to {new_element}"
            return Option(new_element)

        return rhs

    def _rewrite_action(old_rhs: Rhs, new_rhs: Rhs, action: Lambda) -> Lambda:
        """Rewrite action parameters to match new RHS types."""
        if isinstance(old_rhs, Sequence) and isinstance(new_rhs, Sequence) and len(old_rhs.elements) == len(new_rhs.elements):
            new_params = []
            param_idx = 0
            for old_elem, new_elem in zip(old_rhs.elements, new_rhs.elements):
                if isinstance(old_elem, LitTerminal):
                    continue

                old_type = old_elem.target_type()
                new_type = new_elem.target_type()

                if param_idx < len(action.params):
                    param = action.params[param_idx]
                    if old_type != new_type:
                        new_params.append(Var(param.name, new_type))
                    else:
                        new_params.append(param)
                    param_idx += 1

            if new_params and new_params != list(action.params):
                return Lambda(params=new_params, return_type=action.return_type, body=action.body)

        else:
            assert not isinstance(old_rhs, Sequence), f"Invalid rewrite: cannot rewrite sequence to non-sequence or sequence of a different length"
            assert not isinstance(new_rhs, Sequence), f"Invalid rewrite: cannot rewrite non-sequence to sequence"
            old_type = old_rhs.target_type()
            new_type = new_rhs.target_type()
            if old_type != new_type and len(action.params) > 0:
                new_params = [Var(action.params[0].name, new_type)]
                return Lambda(params=new_params, return_type=action.return_type, body=action.body)
            return action

        return action

    def rewrite(rule: Rule) -> Rule:
        new_rhs = _rewrite_rhs(rule.rhs)
        if new_rhs != rule.rhs:
            new_action = _rewrite_action(rule.rhs, new_rhs, rule.action)
            return Rule(lhs=rule.lhs, rhs=new_rhs, action=new_action, source_type=rule.source_type)
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

    Returns:
        A dict mapping nonterminal names to their rewrite functions.
    """
    # Common types
    string_type = BaseType('String')
    terms_type = ListType(MessageType('logic', 'Term'))

    # Common replacement patterns
    string_to_name: Dict[Rhs, Rhs] = {
        NamedTerminal('STRING', string_type): Nonterminal('name', string_type),
    }
    string_to_name_optional: Dict[Rhs, Rhs] = {
        NamedTerminal('STRING', string_type): Option(Nonterminal('name', string_type)),
    }
    terms_optional_to_star_term: Dict[Rhs, Rhs] = {
        Option(Nonterminal('terms', terms_type)): Star(Nonterminal('term', terms_type)),
    }
    terms_optional_to_star_relterm: Dict[Rhs, Rhs] = {
        Option(Nonterminal('terms', terms_type)): Star(Nonterminal('relterm', terms_type)),
    }
    args_optional_to_star_value: Dict[Rhs, Rhs] = {
        Option(Nonterminal('args', terms_type)): Star(Nonterminal('value', terms_type)),
    }
    term_star_to_relterm_star: Dict[Rhs, Rhs] = {
        Star(Nonterminal('term', terms_type)): Star(Nonterminal('relterm', terms_type)),
    }

    rewrite_string_to_name_optional = make_symbol_replacer(string_to_name_optional)
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
            return Rule(lhs=rule.lhs, rhs=Sequence(tuple(new_elements)), action=new_action, source_type=rule.source_type)
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
    tuple_type = TupleType([elem.target_type(), BaseType('Int64')])
    new_elements[abstraction_idx] = Nonterminal('abstraction_with_arity', tuple_type)
    new_elements.pop(int_idx)

    # Find the parameter index for the abstraction
    abstraction_param_idx = None
    param_idx = 0
    for i, elem in enumerate(rule.rhs.elements):
        if isinstance(elem, LitTerminal):
            continue
        if i == abstraction_idx:
            abstraction_param_idx = param_idx
            break
        param_idx += 1

    assert abstraction_param_idx is not None, "Abstraction parameter not found"

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
    return Rule(lhs=rule.lhs, rhs=Sequence(tuple(new_elements)), action=new_action, source_type=rule.source_type)
