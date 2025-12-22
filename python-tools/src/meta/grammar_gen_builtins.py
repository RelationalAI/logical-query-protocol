"""Builtin grammar rules that are manually specified.

These rules define the grammar for constructs that cannot be auto-generated
from protobuf definitions, such as value literals, date/datetime parsing,
configuration syntax, bindings, abstractions, type literals, and operators.
"""

from typing import Dict, List, Set, Tuple

from .grammar import Rule, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence
from .target import (
    Lambda, Call, Var, Symbol, Lit, Seq, IfElse, Builtin, Message, OneOf, ListExpr,
    BaseType, MessageType, OptionType, ListType, FunctionType, TupleType
)


def get_builtin_rules() -> Dict[Nonterminal, Tuple[List[Rule], bool]]:
    """Return dict mapping nonterminals to (rules, is_final).

    is_final=True means auto-generation should not add more rules for this nonterminal.
    """
    result: Dict[Nonterminal, Tuple[List[Rule], bool]] = {}

    def add_rule(rule: Rule, is_final: bool = True) -> None:
        lhs = rule.lhs
        if lhs not in result:
            result[lhs] = ([], is_final)
        rules_list, existing_final = result[lhs]
        rules_list.append(rule)
        # is_final is True if any rule marks it as final
        result[lhs] = (rules_list, existing_final or is_final)

    # Common types used throughout
    _config_type = ListType(TupleType([BaseType('String'), MessageType('logic', 'Value')]))
    _bindings_type = TupleType([ListType(MessageType('logic', 'Binding')), ListType(MessageType('logic', 'Binding'))])
    _abstraction_with_arity_type = TupleType([MessageType('logic', 'Abstraction'), BaseType('Int64')])
    _monoid_op_type = FunctionType([MessageType('logic', 'Type')], MessageType('logic', 'Monoid'))

    # Value literal rules
    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=Nonterminal('date', MessageType('logic', 'DateValue')),
        construct_action=Lambda(
            [Var('value', MessageType('logic', 'DateValue'))],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf('date_value'), [Var('value', MessageType('logic', 'DateValue'))])])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Value'))],
            OptionType(MessageType('logic', 'DateValue')),
            IfElse(
                Call(Builtin('equal'), [
                    Call(Builtin('WhichOneof'), [Var('msg', MessageType('logic', 'Value')), Lit('value_type')]),
                    Lit('date_value')
                ]),
                Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Value')), Lit('date_value')])]),
                Lit(None)
            )
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=Nonterminal('datetime', MessageType('logic', 'DateTimeValue')),
        construct_action=Lambda(
            [Var('value', MessageType('logic', 'DateTimeValue'))],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf('datetime_value'), [Var('value', MessageType('logic', 'DateTimeValue'))])])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Value'))],
            OptionType(MessageType('logic', 'DateTimeValue')),
            IfElse(
                Call(Builtin('equal'), [
                    Call(Builtin('WhichOneof'), [Var('msg', MessageType('logic', 'Value')), Lit('value_type')]),
                    Lit('datetime_value')
                ]),
                Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Value')), Lit('datetime_value')])]),
                Lit(None)
            )
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=NamedTerminal('STRING', BaseType('String')),
        construct_action=Lambda(
            [Var('value', BaseType('String'))],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf('string_value'), [Var('value', BaseType('String'))])])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Value'))],
            OptionType(BaseType('String')),
            IfElse(
                Call(Builtin('equal'), [
                    Call(Builtin('WhichOneof'), [Var('msg', MessageType('logic', 'Value')), Lit('value_type')]),
                    Lit('string_value')
                ]),
                Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Value')), Lit('string_value')])]),
                Lit(None)
            )
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=NamedTerminal('INT', BaseType('Int64')),
        construct_action=Lambda(
            [Var('value', BaseType('Int64'))],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf('int_value'), [Var('value', BaseType('Int64'))])])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Value'))],
            OptionType(BaseType('Int64')),
            IfElse(
                Call(Builtin('equal'), [
                    Call(Builtin('WhichOneof'), [Var('msg', MessageType('logic', 'Value')), Lit('value_type')]),
                    Lit('int_value')
                ]),
                Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Value')), Lit('int_value')])]),
                Lit(None)
            )
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=NamedTerminal('FLOAT', BaseType('Float64')),
        construct_action=Lambda(
            [Var('value', BaseType('Float64'))],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf('float_value'), [Var('value', BaseType('Float64'))])])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Value'))],
            OptionType(BaseType('Float64')),
            IfElse(
                Call(Builtin('equal'), [
                    Call(Builtin('WhichOneof'), [Var('msg', MessageType('logic', 'Value')), Lit('value_type')]),
                    Lit('float_value')
                ]),
                Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Value')), Lit('float_value')])]),
                Lit(None)
            )
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=NamedTerminal('UINT128', MessageType('logic', 'UInt128Value')),
        construct_action=Lambda(
            [Var('value', MessageType('logic', 'UInt128Value'))],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf('uint128_value'), [Var('value', MessageType('logic', 'UInt128Value'))])])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Value'))],
            OptionType(MessageType('logic', 'UInt128Value')),
            IfElse(
                Call(Builtin('equal'), [
                    Call(Builtin('WhichOneof'), [Var('msg', MessageType('logic', 'Value')), Lit('value_type')]),
                    Lit('uint128_value')
                ]),
                Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Value')), Lit('uint128_value')])]),
                Lit(None)
            )
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=NamedTerminal('INT128', MessageType('logic', 'Int128Value')),
        construct_action=Lambda(
            [Var('value', MessageType('logic', 'Int128Value'))],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf('int128_value'), [Var('value', MessageType('logic', 'Int128Value'))])])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Value'))],
            OptionType(MessageType('logic', 'Int128Value')),
            IfElse(
                Call(Builtin('equal'), [
                    Call(Builtin('WhichOneof'), [Var('msg', MessageType('logic', 'Value')), Lit('value_type')]),
                    Lit('int128_value')
                ]),
                Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Value')), Lit('int128_value')])]),
                Lit(None)
            )
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=NamedTerminal('DECIMAL', MessageType('logic', 'DecimalValue')),
        construct_action=Lambda(
            [Var('value', MessageType('logic', 'DecimalValue'))],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf('decimal_value'), [Var('value', MessageType('logic', 'DecimalValue'))])])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Value'))],
            OptionType(MessageType('logic', 'DecimalValue')),
            IfElse(
                Call(Builtin('equal'), [
                    Call(Builtin('WhichOneof'), [Var('msg', MessageType('logic', 'Value')), Lit('value_type')]),
                    Lit('decimal_value')
                ]),
                Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Value')), Lit('decimal_value')])]),
                Lit(None)
            )
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=LitTerminal('missing'),
        construct_action=Lambda(
            [],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf('missing_value'), [Call(Message('logic', 'MissingValue'), [])])])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Value'))],
            OptionType(TupleType([])),
            IfElse(
                Call(Builtin('equal'), [
                    Call(Builtin('WhichOneof'), [Var('msg', MessageType('logic', 'Value')), Lit('value_type')]),
                    Lit('missing_value')
                ]),
                Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])]),
                Lit(None)
            )
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('bool_value', BaseType('Bool')),
        rhs=LitTerminal('true'),
        construct_action=Lambda(
            [],
            BaseType('Bool'),
            Lit(True)
        ),
        deconstruct_action=Lambda(
            [Var('value', BaseType('Bool'))],
            OptionType(TupleType([])),
            IfElse(
                Call(Builtin('equal'), [Var('value', BaseType('Bool')), Lit(True)]),
                Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])]),
                Lit(None)
            )
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('bool_value', BaseType('Bool')),
        rhs=LitTerminal('false'),
        construct_action=Lambda(
            [],
            BaseType('Bool'),
            Lit(False)
        ),
        deconstruct_action=Lambda(
            [Var('value', BaseType('Bool'))],
            OptionType(TupleType([])),
            IfElse(
                Call(Builtin('equal'), [Var('value', BaseType('Bool')), Lit(False)]),
                Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])]),
                Lit(None)
            )
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=Nonterminal('bool_value', BaseType('Bool')),
        construct_action=Lambda(
            [Var('value', BaseType('Bool'))],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf('boolean_value'), [Var('value', BaseType('Bool'))])])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Value'))],
            OptionType(BaseType('Bool')),
            IfElse(
                Call(Builtin('equal'), [
                    Call(Builtin('WhichOneof'), [Var('msg', MessageType('logic', 'Value')), Lit('value_type')]),
                    Lit('boolean_value')
                ]),
                Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Value')), Lit('boolean_value')])]),
                Lit(None)
            )
        )
    ))

    # Date and datetime rules
    add_rule(Rule(
        lhs=Nonterminal('date', MessageType('logic', 'DateValue')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('date'),
            NamedTerminal('INT', BaseType('Int64')),
            NamedTerminal('INT', BaseType('Int64')),
            NamedTerminal('INT', BaseType('Int64')),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [Var('year', BaseType('Int64')), Var('month', BaseType('Int64')), Var('day', BaseType('Int64'))],
            MessageType('logic', 'DateValue'),
            Call(Message('logic', 'DateValue'), [
                Var('year', BaseType('Int64')),
                Var('month', BaseType('Int64')),
                Var('day', BaseType('Int64'))
            ])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'DateValue'))],
            OptionType(TupleType([BaseType('Int64'), BaseType('Int64'), BaseType('Int64')])),
            Call(Builtin('Some'), [
                Call(Builtin('make_tuple'), [
                    Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'DateValue')), Lit('year')]),
                    Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'DateValue')), Lit('month')]),
                    Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'DateValue')), Lit('day')])
                ])
            ])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('datetime', MessageType('logic', 'DateTimeValue')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('datetime'),
            NamedTerminal('INT', BaseType('Int64')),
            NamedTerminal('INT', BaseType('Int64')),
            NamedTerminal('INT', BaseType('Int64')),
            NamedTerminal('INT', BaseType('Int64')),
            NamedTerminal('INT', BaseType('Int64')),
            NamedTerminal('INT', BaseType('Int64')),
            Option(NamedTerminal('INT', BaseType('Int64'))),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [
                Var('year', BaseType('Int64')),
                Var('month', BaseType('Int64')),
                Var('day', BaseType('Int64')),
                Var('hour', BaseType('Int64')),
                Var('minute', BaseType('Int64')),
                Var('second', BaseType('Int64')),
                Var('microsecond', OptionType(BaseType('Int64')))
            ],
            MessageType('logic', 'DateTimeValue'),
            Call(Message('logic', 'DateTimeValue'), [
                Var('year', BaseType('Int64')),
                Var('month', BaseType('Int64')),
                Var('day', BaseType('Int64')),
                Var('hour', BaseType('Int64')),
                Var('minute', BaseType('Int64')),
                Var('second', BaseType('Int64')),
                IfElse(
                    Call(Builtin('is_none'), [Var('microsecond', OptionType(BaseType('Int64')))]),
                    Lit(0),
                    Call(Builtin('Some'), [Var('microsecond', OptionType(BaseType('Int64')))])
                )
            ])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'DateTimeValue'))],
            OptionType(TupleType([
                BaseType('Int64'), BaseType('Int64'), BaseType('Int64'),
                BaseType('Int64'), BaseType('Int64'), BaseType('Int64'),
                OptionType(BaseType('Int64'))
            ])),
            Call(Builtin('Some'), [
                Call(Builtin('make_tuple'), [
                    Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'DateTimeValue')), Lit('year')]),
                    Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'DateTimeValue')), Lit('month')]),
                    Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'DateTimeValue')), Lit('day')]),
                    Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'DateTimeValue')), Lit('hour')]),
                    Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'DateTimeValue')), Lit('minute')]),
                    Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'DateTimeValue')), Lit('second')]),
                    IfElse(
                        Call(Builtin('equal'), [
                            Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'DateTimeValue')), Lit('microsecond')]),
                            Lit(0)
                        ]),
                        Lit(None),
                        Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'DateTimeValue')), Lit('microsecond')])])
                    )
                ])
            ])
        )
    ))

    # Configuration rules
    add_rule(Rule(
        lhs=Nonterminal('config_dict', _config_type),
        rhs=Sequence((
            LitTerminal('{'),
            Star(Nonterminal('config_key_value', TupleType([BaseType('String'), MessageType('logic', 'Value')]))),
            LitTerminal('}')
        )),
        construct_action=Lambda(
            [Var('config_key_value', _config_type)],
            return_type=_config_type,
            body=Var('config_key_value', _config_type)
        ),
        deconstruct_action=Lambda(
            [Var('config', _config_type)],
            OptionType(_config_type),
            Call(Builtin('Some'), [Var('config', _config_type)])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('config_key_value', TupleType([BaseType('String'), MessageType('logic', 'Value')])),
        rhs=Sequence((
            NamedTerminal('COLON_SYMBOL', BaseType('String')),
            Nonterminal('value', MessageType('logic', 'Value'))
        )),
        construct_action=Lambda(
            [Var('symbol', BaseType('String')), Var('value', MessageType('logic', 'Value'))],
            TupleType([BaseType('String'), MessageType('logic', 'Value')]),
            Call(Builtin('make_tuple'), [Var('symbol', BaseType('String')), Var('value', MessageType('logic', 'Value'))])
        ),
        deconstruct_action=Lambda(
            [Var('tuple', TupleType([BaseType('String'), MessageType('logic', 'Value')]))],
            OptionType(TupleType([BaseType('String'), MessageType('logic', 'Value')])),
            Call(Builtin('Some'), [
                Call(Builtin('make_tuple'), [
                    Call(Builtin('fst'), [Var('tuple', TupleType([BaseType('String'), MessageType('logic', 'Value')]))]),
                    Call(Builtin('snd'), [Var('tuple', TupleType([BaseType('String'), MessageType('logic', 'Value')]))])
                ])
            ])
        )
    ))

    # Transaction rule
    add_rule(Rule(
        lhs=Nonterminal('transaction', MessageType('transactions', 'Transaction')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('transaction'),
            Option(Nonterminal('configure', MessageType('transactions', 'Configure'))),
            Option(Nonterminal('sync', MessageType('transactions', 'Sync'))),
            Star(Nonterminal('epoch', MessageType('transactions', 'Epoch'))),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [
                Var('configure', OptionType(MessageType('transactions', 'Configure'))),
                Var('sync', OptionType(MessageType('transactions', 'Sync'))),
                Var('epochs', ListType(MessageType('transactions', 'Epoch')))
            ],
            MessageType('transactions', 'Transaction'),
            Call(Message('transactions', 'Transaction'), [
                Var('epochs', ListType(MessageType('transactions', 'Epoch'))),
                Call(Builtin('unwrap_option_or'), [
                    Var('configure', OptionType(MessageType('transactions', 'Configure'))),
                    Call(Builtin('construct_configure'), [ListExpr([], TupleType([BaseType('String'), MessageType('logic', 'Value')]))])
                ]),
                Var('sync', OptionType(MessageType('transactions', 'Sync')))
            ])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('transactions', 'Transaction'))],
            OptionType(TupleType([
                OptionType(MessageType('transactions', 'Configure')),
                OptionType(MessageType('transactions', 'Sync')),
                ListType(MessageType('transactions', 'Epoch'))
            ])),
            Call(Builtin('Some'), [
                Call(Builtin('make_tuple'), [
                    Call(Builtin('deconstruct_configure'), [Call(Builtin('get_field'), [Var('msg', MessageType('transactions', 'Transaction')), Lit('configure')])]),
                    Call(Builtin('get_field'), [Var('msg', MessageType('transactions', 'Transaction')), Lit('sync')]),
                    Call(Builtin('get_field'), [Var('msg', MessageType('transactions', 'Transaction')), Lit('epochs')])
                ])
            ])
        )
    ))

    # Bindings rules
    add_rule(Rule(
        lhs=Nonterminal('bindings', _bindings_type),
        rhs=Sequence((
            LitTerminal('['),
            Star(Nonterminal('binding', MessageType('logic', 'Binding'))),
            Option(Nonterminal('value_bindings', ListType(MessageType('logic', 'Binding')))),
            LitTerminal(']')
        )),
        construct_action=Lambda(
            [
                Var('keys', ListType(MessageType('logic', 'Binding'))),
                Var('values', OptionType(ListType(MessageType('logic', 'Binding'))))
            ],
            _bindings_type,
            Call(Builtin('make_tuple'), [
                Var('keys', ListType(MessageType('logic', 'Binding'))),
                Call(Builtin('unwrap_option_or'), [
                    Var('values', OptionType(ListType(MessageType('logic', 'Binding')))),
                    ListExpr([], MessageType('logic', 'Binding'))
                ])
            ])
        ),
        deconstruct_action=Lambda(
            [Var('tuple', _bindings_type)],
            OptionType(TupleType([
                ListType(MessageType('logic', 'Binding')),
                OptionType(ListType(MessageType('logic', 'Binding')))
            ])),
            Call(Builtin('Some'), [
                Call(Builtin('make_tuple'), [
                    Call(Builtin('fst'), [Var('tuple', _bindings_type)]),
                    IfElse(
                        Call(Builtin('is_empty'), [Call(Builtin('snd'), [Var('tuple', _bindings_type)])]),
                        Lit(None),
                        Call(Builtin('Some'), [Call(Builtin('snd'), [Var('tuple', _bindings_type)])])
                    )
                ])
            ])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value_bindings', ListType(MessageType('logic', 'Binding'))),
        rhs=Sequence((
            LitTerminal('|'),
            Star(Nonterminal('binding', MessageType('logic', 'Binding')))
        )),
        construct_action=Lambda(
            [Var('values', ListType(MessageType('logic', 'Binding')))],
            ListType(MessageType('logic', 'Binding')),
            Var('values', ListType(MessageType('logic', 'Binding')))
        ),
        deconstruct_action=Lambda(
            [Var('values', ListType(MessageType('logic', 'Binding')))],
            OptionType(ListType(MessageType('logic', 'Binding'))),
            Call(Builtin('Some'), [Var('values', ListType(MessageType('logic', 'Binding')))])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('binding', MessageType('logic', 'Binding')),
        rhs=Sequence((
            NamedTerminal('SYMBOL', BaseType('String')),
            LitTerminal('::'),
            Nonterminal('type', MessageType('logic', 'Type'))
        )),
        construct_action=Lambda(
            [Var('symbol', BaseType('String')), Var('type', MessageType('logic', 'Type'))],
            MessageType('logic', 'Binding'),
            Call(Message('logic', 'Binding'), [
                Call(Message('logic', 'Var'), [Var('symbol', BaseType('String'))]),
                Var('type', MessageType('logic', 'Type'))
            ])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Binding'))],
            OptionType(TupleType([BaseType('String'), MessageType('logic', 'Type')])),
            Call(Builtin('Some'), [
                Call(Builtin('make_tuple'), [
                    Call(Builtin('get_field'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Binding')), Lit('var')]), Lit('symbol')]),
                    Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Binding')), Lit('type')])
                ])
            ])
        )
    ))

    # Abstraction rules
    add_rule(Rule(
        lhs=Nonterminal('abstraction_with_arity', _abstraction_with_arity_type),
        rhs=Sequence((
            LitTerminal('('),
            Nonterminal('bindings', _bindings_type),
            Nonterminal('formula', MessageType('logic', 'Formula')),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            params=[Var('bindings', _bindings_type), Var('formula', MessageType('logic', 'Formula'))],
            return_type=_abstraction_with_arity_type,
            body=Call(Builtin('make_tuple'), [
                Call(Message('logic', 'Abstraction'), [
                    Call(Builtin('list_concat'), [
                        Call(Builtin('fst'), [Var('bindings', _bindings_type)]),
                        Call(Builtin('snd'), [Var('bindings', _bindings_type)])
                    ]),
                    Var('formula', MessageType('logic', 'Formula'))
                ]),
                Call(Builtin('length'), [Call(Builtin('snd'), [Var('bindings', _bindings_type)])])
            ])
        ),
        deconstruct_action=Lambda(
            [Var('tuple', _abstraction_with_arity_type)],
            OptionType(TupleType([_bindings_type, MessageType('logic', 'Formula')])),
            Call(Builtin('Some'), [
                Call(Builtin('make_tuple'), [
                    Call(Builtin('split_bindings'), [
                        Call(Builtin('fst'), [Var('tuple', _abstraction_with_arity_type)]),
                        Call(Builtin('snd'), [Var('tuple', _abstraction_with_arity_type)])
                    ]),
                    Call(Builtin('get_field'), [Call(Builtin('fst'), [Var('tuple', _abstraction_with_arity_type)]), Lit('formula')])
                ])
            ])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('abstraction', MessageType('logic', 'Abstraction')),
        rhs=Sequence((
            LitTerminal('('),
            Nonterminal('bindings', _bindings_type),
            Nonterminal('formula', MessageType('logic', 'Formula')),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            params=[Var('bindings', _bindings_type), Var('formula', MessageType('logic', 'Formula'))],
            return_type=MessageType('logic', 'Abstraction'),
            body=Call(Message('logic', 'Abstraction'), [
                Call(Builtin('list_concat'), [
                    Call(Builtin('fst'), [Var('bindings', _bindings_type)]),
                    Call(Builtin('snd'), [Var('bindings', _bindings_type)])
                ]),
                Var('formula', MessageType('logic', 'Formula'))
            ])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Abstraction'))],
            OptionType(TupleType([_bindings_type, MessageType('logic', 'Formula')])),
            Call(Builtin('Some'), [
                Call(Builtin('make_tuple'), [
                    Call(Builtin('split_all_bindings'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Abstraction')), Lit('bindings')])]),
                    Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Abstraction')), Lit('formula')])
                ])
            ])
        )
    ))

    # Name rule
    add_rule(Rule(
        lhs=Nonterminal('name', BaseType('String')),
        rhs=NamedTerminal('COLON_SYMBOL', BaseType('String')),
        construct_action=Lambda(
            [Var('symbol', BaseType('String'))],
            BaseType('String'),
            Var('symbol', BaseType('String'))
        ),
        deconstruct_action=Lambda(
            [Var('symbol', BaseType('String'))],
            OptionType(BaseType('String')),
            Call(Builtin('Some'), [Var('symbol', BaseType('String'))])
        )
    ))

    # Monoid rules
    add_rule(Rule(
        lhs=Nonterminal('monoid', MessageType('logic', 'Monoid')),
        rhs=Sequence((
            Nonterminal('type', MessageType('logic', 'Type')),
            LitTerminal('::'),
            Nonterminal('monoid_op', _monoid_op_type)
        )),
        construct_action=Lambda(
            [Var('type', MessageType('logic', 'Type')), Var('op', _monoid_op_type)],
            return_type=MessageType('logic', 'Monoid'),
            body=Call(Var('op', _monoid_op_type), [Var('type', MessageType('logic', 'Type'))])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Monoid'))],
            OptionType(TupleType([MessageType('logic', 'Type'), _monoid_op_type])),
            Call(Builtin('deconstruct_monoid'), [Var('msg', MessageType('logic', 'Monoid'))])
        )
    ))

    def _make_monoid_op_rule(constructor: str, has_type: bool) -> Rule:
        op = constructor.removesuffix('Monoid')
        symbol = f'{op.lower()}_monoid'
        lit = op.upper()
        if has_type:
            body = Call(Message('logic', 'Monoid'), [
                Call(OneOf(symbol), [
                    Call(Message('logic', constructor), [Var('type', MessageType('logic', 'Type'))])
                ])
            ])
        else:
            body = Call(Message('logic', 'Monoid'), [
                Call(OneOf(symbol), [
                    Call(Message('logic', constructor), [])
                ])
            ])
        rhs = LitTerminal(lit)
        construct_action = Lambda(
            [],
            return_type=_monoid_op_type,
            body=Lambda([Var('type', MessageType('logic', 'Type'))], return_type=MessageType('logic', 'Monoid'), body=body)
        )
        from .grammar import generate_deconstruct_action
        deconstruct_action = generate_deconstruct_action(construct_action, rhs)
        return Rule(
            lhs=Nonterminal('monoid_op', _monoid_op_type),
            rhs=rhs,
            construct_action=construct_action,
            deconstruct_action=deconstruct_action
        )

    add_rule(_make_monoid_op_rule('OrMonoid', False))
    add_rule(_make_monoid_op_rule('MinMonoid', True))
    add_rule(_make_monoid_op_rule('MaxMonoid', True))
    add_rule(_make_monoid_op_rule('SumMonoid', True))

    # Configure rule
    add_rule(Rule(
        lhs=Nonterminal('configure', MessageType('transactions', 'Configure')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('configure'),
            Nonterminal('config_dict', _config_type),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [Var('config_dict', _config_type)],
            return_type=MessageType('transactions', 'Configure'),
            body=Call(Builtin('construct_configure'), [Var('config_dict', _config_type)])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('transactions', 'Configure'))],
            OptionType(_config_type),
            Call(Builtin('deconstruct_configure_to_dict'), [Var('msg', MessageType('transactions', 'Configure'))])
        )
    ))

    # True/false formula rules
    add_rule(Rule(
        lhs=Nonterminal('true', MessageType('logic', 'Conjunction')),
        rhs=Sequence((LitTerminal('('), LitTerminal('true'), LitTerminal(')'))),
        construct_action=Lambda([], MessageType('logic', 'Conjunction'), Call(Message('logic', 'Conjunction'), [ListExpr([], MessageType('logic', 'Formula'))])),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Conjunction'))],
            OptionType(TupleType([])),
            IfElse(
                Call(Builtin('is_empty'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Conjunction')), Lit('formulas')])]),
                Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])]),
                Lit(None)
            )
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('false', MessageType('logic', 'Disjunction')),
        rhs=Sequence((LitTerminal('('), LitTerminal('false'), LitTerminal(')'))),
        construct_action=Lambda([], MessageType('logic', 'Disjunction'), Call(Message('logic', 'Disjunction'), [ListExpr([], MessageType('logic', 'Formula'))])),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Disjunction'))],
            OptionType(TupleType([])),
            IfElse(
                Call(Builtin('is_empty'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Disjunction')), Lit('formulas')])]),
                Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])]),
                Lit(None)
            )
        )
    ))

    # Formula rules (not final - auto-generation can add more)
    # True formula: checks for empty Conjunction in the 'conjunction' oneof field
    add_rule(Rule(
        lhs=Nonterminal('formula', MessageType('logic', 'Formula')),
        rhs=Nonterminal('true', MessageType('logic', 'Conjunction')),
        construct_action=Lambda(
            [Var('value', MessageType('logic', 'Conjunction'))],
            MessageType('logic', 'Formula'),
            Call(Message('logic', 'Formula'), [Call(OneOf('true'), [Var('value', MessageType('logic', 'Conjunction'))])])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Formula'))],
            OptionType(MessageType('logic', 'Conjunction')),
            IfElse(
                Call(Builtin('equal'), [
                    Call(Builtin('WhichOneof'), [Var('msg', MessageType('logic', 'Formula')), Lit('formula_type')]),
                    Lit('conjunction')
                ]),
                IfElse(
                    Call(Builtin('is_empty'), [Call(Builtin('get_field'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Formula')), Lit('conjunction')]), Lit('formulas')])]),
                    Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Formula')), Lit('conjunction')])]),
                    Lit(None)
                ),
                Lit(None)
            )
        )
    ), is_final=False)

    # False formula: checks for empty Disjunction in the 'disjunction' oneof field
    add_rule(Rule(
        lhs=Nonterminal('formula', MessageType('logic', 'Formula')),
        rhs=Nonterminal('false', MessageType('logic', 'Disjunction')),
        construct_action=Lambda(
            [Var('value', MessageType('logic', 'Disjunction'))],
            MessageType('logic', 'Formula'),
            Call(Message('logic', 'Formula'), [Call(OneOf('false'), [Var('value', MessageType('logic', 'Disjunction'))])])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Formula'))],
            OptionType(MessageType('logic', 'Disjunction')),
            IfElse(
                Call(Builtin('equal'), [
                    Call(Builtin('WhichOneof'), [Var('msg', MessageType('logic', 'Formula')), Lit('formula_type')]),
                    Lit('disjunction')
                ]),
                IfElse(
                    Call(Builtin('is_empty'), [Call(Builtin('get_field'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Formula')), Lit('disjunction')]), Lit('formulas')])]),
                    Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Formula')), Lit('disjunction')])]),
                    Lit(None)
                ),
                Lit(None)
            )
        )
    ), is_final=False)

    # Export rules
    add_rule(Rule(
        lhs=Nonterminal('export', MessageType('transactions', 'Export')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('export'),
            Nonterminal('export_csv_config', MessageType('transactions', 'ExportCSVConfig')),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [Var('config', MessageType('transactions', 'ExportCSVConfig'))],
            MessageType('transactions', 'Export'),
            Call(Message('transactions', 'Export'), [Call(OneOf('csv_config'), [Var('config', MessageType('transactions', 'ExportCSVConfig'))])])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('transactions', 'Export'))],
            OptionType(MessageType('transactions', 'ExportCSVConfig')),
            IfElse(
                Call(Builtin('equal'), [
                    Call(Builtin('WhichOneof'), [Var('msg', MessageType('transactions', 'Export')), Lit('export_type')]),
                    Lit('csv_config')
                ]),
                Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType('transactions', 'Export')), Lit('csv_config')])]),
                Lit(None)
            )
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('export_csv_config', MessageType('transactions', 'ExportCSVConfig')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('export_csv_config'),
            LitTerminal('('), LitTerminal('path'), NamedTerminal('STRING', BaseType('String')), LitTerminal(')'),
            Nonterminal('export_csvcolumns', ListType(MessageType('transactions', 'ExportCSVColumn'))),
            Nonterminal('config_dict', _config_type),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [
                Var('path', BaseType('String')),
                Var('columns', ListType(MessageType('transactions', 'ExportCSVColumn'))),
                Var('config', _config_type)
            ],
            MessageType('transactions', 'ExportCSVConfig'),
            Call(Builtin('export_csv_config'), [
                Var('path', BaseType('String')),
                Var('columns', ListType(MessageType('transactions', 'ExportCSVColumn'))),
                Var('config', _config_type)
            ])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('transactions', 'ExportCSVConfig'))],
            OptionType(TupleType([
                BaseType('String'),
                ListType(MessageType('transactions', 'ExportCSVColumn')),
                _config_type
            ])),
            Call(Builtin('deconstruct_export_csv_config'), [Var('msg', MessageType('transactions', 'ExportCSVConfig'))])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('export_csvcolumns', ListType(MessageType('transactions', 'ExportCSVColumn'))),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('columns'),
            Star(Nonterminal('export_csvcolumn', MessageType('transactions', 'ExportCSVColumn'))),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [Var('columns', ListType(MessageType('transactions', 'ExportCSVColumn')))],
            ListType(MessageType('transactions', 'ExportCSVColumn')),
            Var('columns', ListType(MessageType('transactions', 'ExportCSVColumn')))
        ),
        deconstruct_action=Lambda(
            [Var('columns', ListType(MessageType('transactions', 'ExportCSVColumn')))],
            OptionType(ListType(MessageType('transactions', 'ExportCSVColumn'))),
            Call(Builtin('Some'), [Var('columns', ListType(MessageType('transactions', 'ExportCSVColumn')))])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('export_csvcolumn', MessageType('transactions', 'ExportCSVColumn')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('column'),
            NamedTerminal('STRING', BaseType('String')),
            Nonterminal('relation_id', MessageType('logic', 'RelationId')),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [Var('name', BaseType('String')), Var('relation_id', MessageType('logic', 'RelationId'))],
            MessageType('transactions', 'ExportCSVColumn'),
            Call(Message('transactions', 'ExportCSVColumn'), [
                Var('name', BaseType('String')),
                Var('relation_id', MessageType('logic', 'RelationId'))
            ])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('transactions', 'ExportCSVColumn'))],
            OptionType(TupleType([BaseType('String'), MessageType('logic', 'RelationId')])),
            Call(Builtin('Some'), [
                Call(Builtin('make_tuple'), [
                    Call(Builtin('get_field'), [Var('msg', MessageType('transactions', 'ExportCSVColumn')), Lit('name')]),
                    Call(Builtin('get_field'), [Var('msg', MessageType('transactions', 'ExportCSVColumn')), Lit('relation_id')])
                ])
            ])
        )
    ))

    # Var rule
    add_rule(Rule(
        lhs=Nonterminal('var', MessageType('logic', 'Var')),
        rhs=NamedTerminal('SYMBOL', BaseType('String')),
        construct_action=Lambda(
            [Var('symbol', BaseType('String'))],
            return_type=MessageType('logic', 'Var'),
            body=Call(Message('logic', 'Var'), [Var('symbol', BaseType('String'))])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Var'))],
            OptionType(BaseType('String')),
            Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Var')), Lit('symbol')])])
        )
    ))

    # ID rules
    add_rule(Rule(
        lhs=Nonterminal('fragment_id', MessageType('fragments', 'FragmentId')),
        rhs=NamedTerminal('COLON_SYMBOL', BaseType('String')),
        construct_action=Lambda(
            [Var('symbol', BaseType('String'))],
            return_type=MessageType('fragments', 'FragmentId'),
            body=Call(Builtin('fragment_id_from_string'), [Var('symbol', BaseType('String'))])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('fragments', 'FragmentId'))],
            OptionType(BaseType('String')),
            Call(Builtin('fragment_id_to_string'), [Var('msg', MessageType('fragments', 'FragmentId'))])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('relation_id', MessageType('logic', 'RelationId')),
        rhs=NamedTerminal('COLON_SYMBOL', BaseType('String')),
        construct_action=Lambda(
            [Var('symbol', BaseType('String'))],
            return_type=MessageType('logic', 'RelationId'),
            body=Call(Builtin('relation_id_from_string'), [Var('symbol', BaseType('String'))])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'RelationId'))],
            OptionType(BaseType('String')),
            Call(Builtin('relation_id_to_string'), [Var('msg', MessageType('logic', 'RelationId'))])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('relation_id', MessageType('logic', 'RelationId')),
        rhs=NamedTerminal('INT', BaseType('Int64')),
        construct_action=Lambda(
            [Var('INT', BaseType('Int64'))],
            return_type=MessageType('logic', 'RelationId'),
            body=Call(Builtin('relation_id_from_int'), [Var('INT', BaseType('Int64'))])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'RelationId'))],
            OptionType(BaseType('Int64')),
            Call(Builtin('relation_id_to_int'), [Var('msg', MessageType('logic', 'RelationId'))])
        )
    ))

    # Specialized value rule
    add_rule(Rule(
        lhs=Nonterminal('specialized_value', MessageType('logic', 'Value')),
        rhs=Sequence((LitTerminal('#'), Nonterminal('value', MessageType('logic', 'Value')))),
        construct_action=Lambda(
            [Var('value', MessageType('logic', 'Value'))],
            MessageType('logic', 'Value'),
            Var('value', MessageType('logic', 'Value'))
        ),
        deconstruct_action=Lambda(
            [Var('value', MessageType('logic', 'Value'))],
            OptionType(MessageType('logic', 'Value')),
            Call(Builtin('Some'), [Var('value', MessageType('logic', 'Value'))])
        )
    ))

    # Type rules
    _type_rules = [
        ('unspecified_type', MessageType('logic', 'UnspecifiedType'), LitTerminal('UNKNOWN'),
         Lambda([], MessageType('logic', 'UnspecifiedType'), Call(Message('logic', 'UnspecifiedType'), []))),
        ('string_type', MessageType('logic', 'StringType'), LitTerminal('STRING'),
         Lambda([], MessageType('logic', 'StringType'), Call(Message('logic', 'StringType'), []))),
        ('int_type', MessageType('logic', 'IntType'), LitTerminal('INT'),
         Lambda([], MessageType('logic', 'IntType'), Call(Message('logic', 'IntType'), []))),
        ('float_type', MessageType('logic', 'FloatType'), LitTerminal('FLOAT'),
         Lambda([], MessageType('logic', 'FloatType'), Call(Message('logic', 'FloatType'), []))),
        ('uint128_type', MessageType('logic', 'UInt128Type'), LitTerminal('UINT128'),
         Lambda([], MessageType('logic', 'UInt128Type'), Call(Message('logic', 'UInt128Type'), []))),
        ('int128_type', MessageType('logic', 'Int128Type'), LitTerminal('INT128'),
         Lambda([], MessageType('logic', 'Int128Type'), Call(Message('logic', 'Int128Type'), []))),
        ('boolean_type', MessageType('logic', 'BooleanType'), LitTerminal('BOOLEAN'),
         Lambda([], MessageType('logic', 'BooleanType'), Call(Message('logic', 'BooleanType'), []))),
        ('bool_type', MessageType('logic', 'BooleanType'), LitTerminal('BOOL'),
         Lambda([], MessageType('logic', 'BooleanType'), Call(Message('logic', 'BooleanType'), []))),
        ('date_type', MessageType('logic', 'DateType'), LitTerminal('DATE'),
         Lambda([], MessageType('logic', 'DateType'), Call(Message('logic', 'DateType'), []))),
        ('datetime_type', MessageType('logic', 'DateTimeType'), LitTerminal('DATETIME'),
         Lambda([], MessageType('logic', 'DateTimeType'), Call(Message('logic', 'DateTimeType'), []))),
        ('missing_type', MessageType('logic', 'MissingType'), LitTerminal('MISSING'),
         Lambda([], MessageType('logic', 'MissingType'), Call(Message('logic', 'MissingType'), []))),
        ('decimal_type', MessageType('logic', 'DecimalType'),
         Sequence((LitTerminal('('), LitTerminal('DECIMAL'), NamedTerminal('INT', BaseType('Int64')), NamedTerminal('INT', BaseType('Int64')), LitTerminal(')'))),
         Lambda(
             [Var('precision', BaseType('Int64')), Var('scale', BaseType('Int64'))],
             MessageType('logic', 'DecimalType'),
             Call(Message('logic', 'DecimalType'), [Var('precision', BaseType('Int64')), Var('scale', BaseType('Int64'))])
         )),
    ]
    for lhs_name, lhs_type, rhs, action in _type_rules:
        if lhs_name == 'decimal_type':
            # Decimal type has parameters
            add_rule(Rule(
                lhs=Nonterminal(lhs_name, lhs_type),
                rhs=rhs,
                construct_action=action,
                deconstruct_action=Lambda(
                    [Var('msg', lhs_type)],
                    OptionType(TupleType([BaseType('Int64'), BaseType('Int64')])),
                    Call(Builtin('Some'), [
                        Call(Builtin('make_tuple'), [
                            Call(Builtin('get_field'), [Var('msg', lhs_type), Lit('precision')]),
                            Call(Builtin('get_field'), [Var('msg', lhs_type), Lit('scale')])
                        ])
                    ])
                )
            ))
        else:
            # Other type rules have no parameters
            add_rule(Rule(
                lhs=Nonterminal(lhs_name, lhs_type),
                rhs=rhs,
                construct_action=action,
                deconstruct_action=Lambda(
                    [Var('msg', lhs_type)],
                    OptionType(TupleType([])),
                    Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])])
                )
            ))

    # Comparison operator rules
    _comparison_ops = [
        ('eq', '=', 'rel_primitive_eq'),
        ('lt', '<', 'rel_primitive_lt_monotype'),
        ('lt_eq', '<=', 'rel_primitive_lt_eq_monotype'),
        ('gt', '>', 'rel_primitive_gt_monotype'),
        ('gt_eq', '>=', 'rel_primitive_gt_eq_monotype'),
    ]
    for name, op, prim in _comparison_ops:
        add_rule(Rule(
            lhs=Nonterminal(name, MessageType('logic', 'Primitive')),
            rhs=Sequence((
                LitTerminal('('), LitTerminal(op),
                Nonterminal('term', MessageType('logic', 'Term')),
                Nonterminal('term', MessageType('logic', 'Term')),
                LitTerminal(')')
            )),
            construct_action=Lambda(
                [Var('left', MessageType('logic', 'Term')), Var('right', MessageType('logic', 'Term'))],
                MessageType('logic', 'Primitive'),
                Call(Message('logic', 'Primitive'), [
                    Lit(prim),
                    Call(Message('logic', 'RelTerm'), [Call(OneOf('term'), [Var('left', MessageType('logic', 'Term'))])]),
                    Call(Message('logic', 'RelTerm'), [Call(OneOf('term'), [Var('right', MessageType('logic', 'Term'))])])
                ])
            ),
            deconstruct_action=Lambda(
                [Var('msg', MessageType('logic', 'Primitive'))],
                OptionType(TupleType([MessageType('logic', 'Term'), MessageType('logic', 'Term')])),
                IfElse(
                    Call(Builtin('equal'), [
                        Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Primitive')), Lit('op')]),
                        Lit(prim)
                    ]),
                    Call(Builtin('Some'), [
                        Call(Builtin('make_tuple'), [
                            Call(Builtin('get_field'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Primitive')), Lit('arg0')]), Lit('term')]),
                            Call(Builtin('get_field'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Primitive')), Lit('arg1')]), Lit('term')])
                        ])
                    ]),
                    Lit(None)
                )
            )
        ))

    # Arithmetic operator rules
    _arithmetic_ops = [
        ('add', '+', 'rel_primitive_add_monotype'),
        ('minus', '-', 'rel_primitive_subtract_monotype'),
        ('multiply', '*', 'rel_primitive_multiply_monotype'),
        ('divide', '/', 'rel_primitive_divide_monotype'),
    ]
    for name, op, prim in _arithmetic_ops:
        add_rule(Rule(
            lhs=Nonterminal(name, MessageType('logic', 'Primitive')),
            rhs=Sequence((
                LitTerminal('('), LitTerminal(op),
                Nonterminal('term', MessageType('logic', 'Term')),
                Nonterminal('term', MessageType('logic', 'Term')),
                Nonterminal('term', MessageType('logic', 'Term')),
                LitTerminal(')')
            )),
            construct_action=Lambda(
                [
                    Var('left', MessageType('logic', 'Term')),
                    Var('right', MessageType('logic', 'Term')),
                    Var('result', MessageType('logic', 'Term'))
                ],
                MessageType('logic', 'Primitive'),
                Call(Message('logic', 'Primitive'), [
                    Lit(prim),
                    Call(Message('logic', 'RelTerm'), [Call(OneOf('term'), [Var('left', MessageType('logic', 'Term'))])]),
                    Call(Message('logic', 'RelTerm'), [Call(OneOf('term'), [Var('right', MessageType('logic', 'Term'))])]),
                    Call(Message('logic', 'RelTerm'), [Call(OneOf('term'), [Var('result', MessageType('logic', 'Term'))])])
                ])
            ),
            deconstruct_action=Lambda(
                [Var('msg', MessageType('logic', 'Primitive'))],
                OptionType(TupleType([MessageType('logic', 'Term'), MessageType('logic', 'Term'), MessageType('logic', 'Term')])),
                IfElse(
                    Call(Builtin('equal'), [
                        Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Primitive')), Lit('op')]),
                        Lit(prim)
                    ]),
                    Call(Builtin('Some'), [
                        Call(Builtin('make_tuple'), [
                            Call(Builtin('get_field'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Primitive')), Lit('arg0')]), Lit('term')]),
                            Call(Builtin('get_field'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Primitive')), Lit('arg1')]), Lit('term')]),
                            Call(Builtin('get_field'), [Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Primitive')), Lit('arg2')]), Lit('term')])
                        ])
                    ]),
                    Lit(None)
                )
            )
        ))

    # Primitive wrapper rules for operators (not final - auto-generation can add more)
    for name, _op, prim in _comparison_ops + _arithmetic_ops:
        add_rule(Rule(
            lhs=Nonterminal('primitive', MessageType('logic', 'Primitive')),
            rhs=Nonterminal(name, MessageType('logic', 'Primitive')),
            construct_action=Lambda(
                [Var('op', MessageType('logic', 'Primitive'))],
                MessageType('logic', 'Primitive'),
                Var('op', MessageType('logic', 'Primitive'))
            ),
            deconstruct_action=Lambda(
                [Var('msg', MessageType('logic', 'Primitive'))],
                OptionType(MessageType('logic', 'Primitive')),
                IfElse(
                    Call(Builtin('equal'), [
                        Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Primitive')), Lit('op')]),
                        Lit(prim)
                    ]),
                    Call(Builtin('Some'), [Var('msg', MessageType('logic', 'Primitive'))]),
                    Lit(None)
                )
            )
        ), is_final=False)

    add_rule(Rule(
        lhs=Nonterminal('new_fragment_id', MessageType('fragments', 'FragmentId')),
        rhs=Nonterminal('fragment_id', MessageType('fragments', 'FragmentId')),
        construct_action=Lambda(
            [
                Var('fragment_id', MessageType('fragments', 'FragmentId')),
            ],
            MessageType('fragments', 'FragmentId'),
            Seq([
                Call(Builtin('start_fragment'), [Var('fragment_id', MessageType('fragments', 'FragmentId'))]),
                Var('fragment_id', MessageType('fragments', 'FragmentId')),
            ])
        ),
        deconstruct_action=Lambda(
            [Var('fragment_id', MessageType('fragments', 'FragmentId'))],
            OptionType(MessageType('fragments', 'FragmentId')),
            Call(Builtin('Some'), [Var('fragment_id', MessageType('fragments', 'FragmentId'))])
        )
    ))

    # Fragment rule with debug_info construction
    add_rule(Rule(
        lhs=Nonterminal('fragment', MessageType('fragments', 'Fragment')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('fragment'),
            Nonterminal('new_fragment_id', MessageType('fragments', 'FragmentId')),
            Star(Nonterminal('declaration', MessageType('logic', 'Declaration'))),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [
                Var('fragment_id', MessageType('fragments', 'FragmentId')),
                Var('declarations', ListType(MessageType('logic', 'Declaration')))
            ],
            MessageType('fragments', 'Fragment'),
            Call(Builtin('construct_fragment'), [
                Var('fragment_id', MessageType('fragments', 'FragmentId')),
                Var('declarations', ListType(MessageType('logic', 'Declaration')))
            ])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('fragments', 'Fragment'))],
            OptionType(TupleType([
                MessageType('fragments', 'FragmentId'),
                ListType(MessageType('logic', 'Declaration'))
            ])),
            Call(Builtin('deconstruct_fragment'), [Var('msg', MessageType('fragments', 'Fragment'))])
        )
    ))

    # Manually-specified rules that replace auto-generated proto rules
    # These rules have been transformed for S-expression parsing
    # (STRING -> name, terms? -> term*, abstraction -> bindings+formula, etc.)

    # output: STRING -> name (optional)
    add_rule(Rule(
        lhs=Nonterminal('output', MessageType('transactions', 'Output')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('output'),
            Option(Nonterminal('name', BaseType('String'))),
            Nonterminal('relation_id', MessageType('logic', 'RelationId')),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [Var('name', BaseType('String')), Var('relation_id', MessageType('logic', 'RelationId'))],
            MessageType('transactions', 'Output'),
            Call(Message('transactions', 'Output'), [Var('name', BaseType('String')), Var('relation_id', MessageType('logic', 'RelationId'))])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('transactions', 'Output'))],
            OptionType(TupleType([BaseType('String'), MessageType('logic', 'RelationId')])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [
                Call(Builtin('get_field'), [Var('msg', MessageType('transactions', 'Output')), Lit('name')]),
                Call(Builtin('get_field'), [Var('msg', MessageType('transactions', 'Output')), Lit('relation_id')])
            ])])
        )
    ))

    # abort: STRING -> name (optional)
    add_rule(Rule(
        lhs=Nonterminal('abort', MessageType('transactions', 'Abort')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('abort'),
            Option(Nonterminal('name', BaseType('String'))),
            Nonterminal('relation_id', MessageType('logic', 'RelationId')),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [Var('name', BaseType('String')), Var('relation_id', MessageType('logic', 'RelationId'))],
            MessageType('transactions', 'Abort'),
            Call(Message('transactions', 'Abort'), [Var('name', BaseType('String')), Var('relation_id', MessageType('logic', 'RelationId'))])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('transactions', 'Abort'))],
            OptionType(TupleType([BaseType('String'), MessageType('logic', 'RelationId')])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [
                Call(Builtin('get_field'), [Var('msg', MessageType('transactions', 'Abort')), Lit('name')]),
                Call(Builtin('get_field'), [Var('msg', MessageType('transactions', 'Abort')), Lit('relation_id')])
            ])])
        )
    ))

    # ffi: STRING -> name, terms? -> term*
    add_rule(Rule(
        lhs=Nonterminal('ffi', MessageType('logic', 'FFI')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('ffi'),
            Nonterminal('name', BaseType('String')),
            Star(Nonterminal('abstraction', MessageType('logic', 'Abstraction'))),
            Star(Nonterminal('term', MessageType('logic', 'Term'))),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [
                Var('name', BaseType('String')),
                Var('args', ListType(MessageType('logic', 'Abstraction'))),
                Var('terms', ListType(MessageType('logic', 'Term')))
            ],
            MessageType('logic', 'FFI'),
            Call(Message('logic', 'FFI'), [Var('name', BaseType('String')), Var('args', ListType(MessageType('logic', 'Abstraction'))), Var('terms', ListType(MessageType('logic', 'Term')))])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'FFI'))],
            OptionType(TupleType([BaseType('String'), ListType(MessageType('logic', 'Abstraction')), ListType(MessageType('logic', 'Term'))])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'FFI')), Lit('name')]),
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'FFI')), Lit('args')]),
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'FFI')), Lit('terms')])
            ])])
        )
    ))

    # pragma: STRING -> name, terms? -> term*
    add_rule(Rule(
        lhs=Nonterminal('pragma', MessageType('logic', 'Pragma')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('pragma'),
            Nonterminal('name', BaseType('String')),
            Star(Nonterminal('term', MessageType('logic', 'Term'))),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [Var('name', BaseType('String')), Var('terms', ListType(MessageType('logic', 'Term')))],
            MessageType('logic', 'Pragma'),
            Call(Message('logic', 'Pragma'), [Var('name', BaseType('String')), Var('terms', ListType(MessageType('logic', 'Term')))])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Pragma'))],
            OptionType(TupleType([BaseType('String'), ListType(MessageType('logic', 'Term'))])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Pragma')), Lit('name')]),
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Pragma')), Lit('terms')])
            ])])
        )
    ))

    # atom: terms? -> term*
    add_rule(Rule(
        lhs=Nonterminal('atom', MessageType('logic', 'Atom')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('atom'),
            Nonterminal('relation_id', MessageType('logic', 'RelationId')),
            Star(Nonterminal('term', MessageType('logic', 'Term'))),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [Var('name', MessageType('logic', 'RelationId')), Var('terms', ListType(MessageType('logic', 'Term')))],
            MessageType('logic', 'Atom'),
            Call(Message('logic', 'Atom'), [Var('name', MessageType('logic', 'RelationId')), Var('terms', ListType(MessageType('logic', 'Term')))])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Atom'))],
            OptionType(TupleType([MessageType('logic', 'RelationId'), ListType(MessageType('logic', 'Term'))])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Atom')), Lit('name')]),
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Atom')), Lit('terms')])
            ])])
        )
    ))

    # rel_atom: STRING -> name, terms? -> relterm*
    add_rule(Rule(
        lhs=Nonterminal('rel_atom', MessageType('logic', 'RelAtom')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('rel_atom'),
            Nonterminal('name', BaseType('String')),
            Star(Nonterminal('relterm', MessageType('logic', 'RelTerm'))),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [Var('name', BaseType('String')), Var('terms', ListType(MessageType('logic', 'RelTerm')))],
            MessageType('logic', 'RelAtom'),
            Call(Message('logic', 'RelAtom'), [Var('name', BaseType('String')), Var('terms', ListType(MessageType('logic', 'RelTerm')))])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'RelAtom'))],
            OptionType(TupleType([BaseType('String'), ListType(MessageType('logic', 'RelTerm'))])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'RelAtom')), Lit('name')]),
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'RelAtom')), Lit('terms')])
            ])])
        )
    ))

    # primitive: STRING -> name, term* -> relterm*
    add_rule(Rule(
        lhs=Nonterminal('primitive', MessageType('logic', 'Primitive')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('primitive'),
            Nonterminal('name', BaseType('String')),
            Star(Nonterminal('relterm', MessageType('logic', 'RelTerm'))),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [Var('name', BaseType('String')), Var('terms', ListType(MessageType('logic', 'RelTerm')))],
            MessageType('logic', 'Primitive'),
            Call(Message('logic', 'Primitive'), [Var('name', BaseType('String')), Var('terms', ListType(MessageType('logic', 'RelTerm')))])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Primitive'))],
            OptionType(TupleType([BaseType('String'), ListType(MessageType('logic', 'RelTerm'))])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Primitive')), Lit('name')]),
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Primitive')), Lit('terms')])
            ])])
        )
    ))

    # attribute: STRING -> name, args? -> value*
    add_rule(Rule(
        lhs=Nonterminal('attribute', MessageType('logic', 'Attribute')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('attribute'),
            Nonterminal('name', BaseType('String')),
            Star(Nonterminal('value', MessageType('logic', 'Value'))),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [Var('name', BaseType('String')), Var('args', ListType(MessageType('logic', 'Value')))],
            MessageType('logic', 'Attribute'),
            Call(Message('logic', 'Attribute'), [Var('name', BaseType('String')), Var('args', ListType(MessageType('logic', 'Value')))])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Attribute'))],
            OptionType(TupleType([BaseType('String'), ListType(MessageType('logic', 'Value'))])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Attribute')), Lit('name')]),
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Attribute')), Lit('args')])
            ])])
        )
    ))

    # exists: abstraction -> (bindings formula)
    add_rule(Rule(
        lhs=Nonterminal('exists', MessageType('logic', 'Exists')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('exists'),
            Nonterminal('bindings', _bindings_type),
            Nonterminal('formula', MessageType('logic', 'Formula')),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [Var('bindings', _bindings_type), Var('formula', MessageType('logic', 'Formula'))],
            MessageType('logic', 'Exists'),
            Call(Message('logic', 'Exists'), [
                Call(Message('logic', 'Abstraction'), [
                    Call(Builtin('list_concat'), [
                        Call(Builtin('fst'), [Var('bindings', _bindings_type)]),
                        Call(Builtin('snd'), [Var('bindings', _bindings_type)])
                    ]),
                    Var('formula', MessageType('logic', 'Formula'))
                ])
            ])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Exists'))],
            OptionType(TupleType([_bindings_type, MessageType('logic', 'Formula')])),
            Call(Builtin('deconstruct_exists'), [Var('msg', MessageType('logic', 'Exists'))])
        )
    ))

    # upsert: abstraction INT -> abstraction_with_arity
    add_rule(Rule(
        lhs=Nonterminal('upsert', MessageType('logic', 'Upsert')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('upsert'),
            Nonterminal('relation_id', MessageType('logic', 'RelationId')),
            Nonterminal('abstraction_with_arity', _abstraction_with_arity_type),
            Star(Nonterminal('attribute', MessageType('logic', 'Attribute'))),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [
                Var('name', MessageType('logic', 'RelationId')),
                Var('body_with_arity', _abstraction_with_arity_type),
                Var('attrs', ListType(MessageType('logic', 'Attribute')))
            ],
            MessageType('logic', 'Upsert'),
            Call(Message('logic', 'Upsert'), [
                Var('name', MessageType('logic', 'RelationId')),
                Call(Builtin('fst'), [Var('body_with_arity', _abstraction_with_arity_type)]),
                Var('attrs', ListType(MessageType('logic', 'Attribute'))),
                Call(Builtin('snd'), [Var('body_with_arity', _abstraction_with_arity_type)])
            ])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Upsert'))],
            OptionType(TupleType([
                MessageType('logic', 'RelationId'),
                _abstraction_with_arity_type,
                ListType(MessageType('logic', 'Attribute'))
            ])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Upsert')), Lit('name')]),
                Call(Builtin('make_tuple'), [
                    Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Upsert')), Lit('body')]),
                    Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Upsert')), Lit('value_arity')])
                ]),
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'Upsert')), Lit('attrs')])
            ])])
        )
    ))

    # monoid_def: abstraction INT -> abstraction_with_arity
    add_rule(Rule(
        lhs=Nonterminal('monoid_def', MessageType('logic', 'MonoidDef')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('monoid'),
            Nonterminal('monoid', MessageType('logic', 'Monoid')),
            Nonterminal('relation_id', MessageType('logic', 'RelationId')),
            Nonterminal('abstraction_with_arity', _abstraction_with_arity_type),
            Star(Nonterminal('attribute', MessageType('logic', 'Attribute'))),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [
                Var('monoid', MessageType('logic', 'Monoid')),
                Var('name', MessageType('logic', 'RelationId')),
                Var('body_with_arity', _abstraction_with_arity_type),
                Var('attrs', ListType(MessageType('logic', 'Attribute')))
            ],
            MessageType('logic', 'MonoidDef'),
            Call(Message('logic', 'MonoidDef'), [
                Var('monoid', MessageType('logic', 'Monoid')),
                Var('name', MessageType('logic', 'RelationId')),
                Call(Builtin('fst'), [Var('body_with_arity', _abstraction_with_arity_type)]),
                Var('attrs', ListType(MessageType('logic', 'Attribute'))),
                Call(Builtin('snd'), [Var('body_with_arity', _abstraction_with_arity_type)])
            ])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'MonoidDef'))],
            OptionType(TupleType([
                MessageType('logic', 'Monoid'),
                MessageType('logic', 'RelationId'),
                _abstraction_with_arity_type,
                ListType(MessageType('logic', 'Attribute'))
            ])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'MonoidDef')), Lit('monoid')]),
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'MonoidDef')), Lit('name')]),
                Call(Builtin('make_tuple'), [
                    Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'MonoidDef')), Lit('body')]),
                    Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'MonoidDef')), Lit('value_arity')])
                ]),
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'MonoidDef')), Lit('attrs')])
            ])])
        )
    ))

    # monus_def: abstraction INT -> abstraction_with_arity
    add_rule(Rule(
        lhs=Nonterminal('monus_def', MessageType('logic', 'MonusDef')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('monus'),
            Nonterminal('monoid', MessageType('logic', 'Monoid')),
            Nonterminal('relation_id', MessageType('logic', 'RelationId')),
            Nonterminal('abstraction_with_arity', _abstraction_with_arity_type),
            Star(Nonterminal('attribute', MessageType('logic', 'Attribute'))),
            LitTerminal(')')
        )),
        construct_action=Lambda(
            [
                Var('monoid', MessageType('logic', 'Monoid')),
                Var('name', MessageType('logic', 'RelationId')),
                Var('body_with_arity', _abstraction_with_arity_type),
                Var('attrs', ListType(MessageType('logic', 'Attribute')))
            ],
            MessageType('logic', 'MonusDef'),
            Call(Message('logic', 'MonusDef'), [
                Var('monoid', MessageType('logic', 'Monoid')),
                Var('name', MessageType('logic', 'RelationId')),
                Call(Builtin('fst'), [Var('body_with_arity', _abstraction_with_arity_type)]),
                Var('attrs', ListType(MessageType('logic', 'Attribute'))),
                Call(Builtin('snd'), [Var('body_with_arity', _abstraction_with_arity_type)])
            ])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'MonusDef'))],
            OptionType(TupleType([
                MessageType('logic', 'Monoid'),
                MessageType('logic', 'RelationId'),
                _abstraction_with_arity_type,
                ListType(MessageType('logic', 'Attribute'))
            ])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'MonusDef')), Lit('monoid')]),
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'MonusDef')), Lit('name')]),
                Call(Builtin('make_tuple'), [
                    Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'MonusDef')), Lit('body')]),
                    Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'MonusDef')), Lit('value_arity')])
                ]),
                Call(Builtin('get_field'), [Var('msg', MessageType('logic', 'MonusDef')), Lit('attrs')])
            ])])
        )
    ))

    return result
