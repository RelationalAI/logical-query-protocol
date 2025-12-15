"""Builtin grammar rules that are manually specified.

These rules define the grammar for constructs that cannot be auto-generated
from protobuf definitions, such as value literals, date/datetime parsing,
configuration syntax, bindings, abstractions, type literals, and operators.
"""

from typing import Dict, List, Tuple

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
        rhs=Sequence((Nonterminal('date', MessageType('logic', 'DateValue')),)),
        action=Lambda(
            [Var('value', MessageType('logic', 'DateValue'))],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf(Symbol('date_value')), [Var('value', MessageType('logic', 'DateValue'))])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=Sequence((Nonterminal('datetime', MessageType('logic', 'DateTimeValue')),)),
        action=Lambda(
            [Var('value', MessageType('logic', 'DateTimeValue'))],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf(Symbol('datetime_value')), [Var('value', MessageType('logic', 'DateTimeValue'))])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=Sequence((NamedTerminal('STRING', BaseType('String')),)),
        action=Lambda(
            [Var('value', BaseType('String'))],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf(Symbol('string_value')), [Var('value', BaseType('String'))])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=Sequence((NamedTerminal('INT', BaseType('Int64')),)),
        action=Lambda(
            [Var('value', BaseType('Int64'))],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf(Symbol('int_value')), [Var('value', BaseType('Int64'))])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=Sequence((NamedTerminal('FLOAT', BaseType('Float64')),)),
        action=Lambda(
            [Var('value', BaseType('Float64'))],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf(Symbol('float_value')), [Var('value', BaseType('Float64'))])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=Sequence((NamedTerminal('UINT128', MessageType('logic', 'UInt128Value')),)),
        action=Lambda(
            [Var('value', MessageType('logic', 'UInt128Value'))],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf(Symbol('uint128_value')), [Var('value', MessageType('logic', 'UInt128Value'))])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=Sequence((NamedTerminal('INT128', MessageType('logic', 'Int128Value')),)),
        action=Lambda(
            [Var('value', MessageType('logic', 'Int128Value'))],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf(Symbol('int128_value')), [Var('value', MessageType('logic', 'Int128Value'))])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=Sequence((NamedTerminal('DECIMAL', MessageType('logic', 'DecimalValue')),)),
        action=Lambda(
            [Var('value', MessageType('logic', 'DecimalValue'))],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf(Symbol('decimal_value')), [Var('value', MessageType('logic', 'DecimalValue'))])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=Sequence((LitTerminal('missing'),)),
        action=Lambda(
            [],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf(Symbol('missing_value')), [Call(Message('logic', 'MissingValue'), [])])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=Sequence((LitTerminal('true'),)),
        action=Lambda(
            [],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf(Symbol('boolean_value')), [Lit(True)])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('logic', 'Value')),
        rhs=Sequence((LitTerminal('false'),)),
        action=Lambda(
            [],
            MessageType('logic', 'Value'),
            Call(Message('logic', 'Value'), [Call(OneOf(Symbol('boolean_value')), [Lit(False)])])
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
        action=Lambda(
            [Var('year', BaseType('Int64')), Var('month', BaseType('Int64')), Var('day', BaseType('Int64'))],
            MessageType('logic', 'DateValue'),
            Call(Message('logic', 'DateValue'), [
                Var('year', BaseType('Int64')),
                Var('month', BaseType('Int64')),
                Var('day', BaseType('Int64'))
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
        action=Lambda(
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
                    Call(Builtin('some'), [Var('microsecond', OptionType(BaseType('Int64')))])
                )
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
        action=Lambda(
            [Var('config_key_value', _config_type)],
            return_type=_config_type,
            body=Var('config_key_value', _config_type)
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('config_key_value', TupleType([BaseType('String'), MessageType('logic', 'Value')])),
        rhs=Sequence((
            NamedTerminal('COLON_SYMBOL', BaseType('String')),
            Nonterminal('value', MessageType('logic', 'Value'))
        )),
        action=Lambda(
            [Var('symbol', BaseType('String')), Var('value', MessageType('logic', 'Value'))],
            TupleType([BaseType('String'), MessageType('logic', 'Value')]),
            Call(Builtin('make_tuple'), [Var('symbol', BaseType('String')), Var('value', MessageType('logic', 'Value'))])
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
        action=Lambda(
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
        action=Lambda(
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
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value_bindings', ListType(MessageType('logic', 'Binding'))),
        rhs=Sequence((
            LitTerminal('|'),
            Star(Nonterminal('binding', MessageType('logic', 'Binding')))
        )),
        action=Lambda(
            [Var('values', ListType(MessageType('logic', 'Binding')))],
            ListType(MessageType('logic', 'Binding')),
            Var('values', ListType(MessageType('logic', 'Binding')))
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('binding', MessageType('logic', 'Binding')),
        rhs=Sequence((
            NamedTerminal('SYMBOL', BaseType('String')),
            LitTerminal('::'),
            Nonterminal('type', MessageType('logic', 'Type'))
        )),
        action=Lambda(
            [Var('symbol', BaseType('String')), Var('type', MessageType('logic', 'Type'))],
            MessageType('logic', 'Binding'),
            Call(Message('logic', 'Binding'), [
                Call(Message('logic', 'Var'), [Var('symbol', BaseType('String'))]),
                Var('type', MessageType('logic', 'Type'))
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
        action=Lambda(
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
        action=Lambda(
            params=[Var('bindings', _bindings_type), Var('formula', MessageType('logic', 'Formula'))],
            return_type=MessageType('logic', 'Abstraction'),
            body=Call(Message('logic', 'Abstraction'), [
                Call(Builtin('list_concat'), [
                    Call(Builtin('fst'), [Var('bindings', _bindings_type)]),
                    Call(Builtin('snd'), [Var('bindings', _bindings_type)])
                ]),
                Var('formula', MessageType('logic', 'Formula'))
            ])
        )
    ))

    # Name rule
    add_rule(Rule(
        lhs=Nonterminal('name', BaseType('String')),
        rhs=NamedTerminal('COLON_SYMBOL', BaseType('String')),
        action=Lambda(
            [Var('symbol', BaseType('String'))],
            BaseType('String'),
            Var('symbol', BaseType('String'))
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
        action=Lambda(
            [Var('type', MessageType('logic', 'Type')), Var('op', _monoid_op_type)],
            return_type=MessageType('logic', 'Monoid'),
            body=Call(Var('op', _monoid_op_type), [Var('type', MessageType('logic', 'Type'))])
        )
    ))

    def _make_monoid_op_rule(constructor: str, has_type: bool) -> Rule:
        op = constructor.removesuffix('Monoid')
        symbol = f'{op.lower()}_monoid'
        lit = op.upper()
        if has_type:
            body = Call(Message('logic', 'Monoid'), [
                Call(OneOf(Symbol(symbol)), [
                    Call(Message('logic', constructor), [Var('type', MessageType('logic', 'Type'))])
                ])
            ])
        else:
            body = Call(Message('logic', 'Monoid'), [
                Call(OneOf(Symbol(symbol)), [
                    Call(Message('logic', constructor), [])
                ])
            ])
        return Rule(
            lhs=Nonterminal('monoid_op', _monoid_op_type),
            rhs=LitTerminal(lit),
            action=Lambda(
                [],
                return_type=_monoid_op_type,
                body=Lambda([Var('type', MessageType('logic', 'Type'))], return_type=MessageType('logic', 'Monoid'), body=body)
            )
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
        action=Lambda(
            [Var('config_dict', _config_type)],
            return_type=MessageType('transactions', 'Configure'),
            body=Call(Builtin('construct_configure'), [Var('config_dict', _config_type)])
        )
    ))

    # True/false formula rules
    add_rule(Rule(
        lhs=Nonterminal('true', MessageType('logic', 'Conjunction')),
        rhs=Sequence((LitTerminal('('), LitTerminal('true'), LitTerminal(')'))),
        action=Lambda([], MessageType('logic', 'Conjunction'), Call(Message('logic', 'Conjunction'), [ListExpr([], MessageType('logic', 'Formula'))]))
    ))

    add_rule(Rule(
        lhs=Nonterminal('false', MessageType('logic', 'Disjunction')),
        rhs=Sequence((LitTerminal('('), LitTerminal('false'), LitTerminal(')'))),
        action=Lambda([], MessageType('logic', 'Disjunction'), Call(Message('logic', 'Disjunction'), [ListExpr([], MessageType('logic', 'Formula'))]))
    ))

    # Formula rules (not final - auto-generation can add more)
    add_rule(Rule(
        lhs=Nonterminal('formula', MessageType('logic', 'Formula')),
        rhs=Sequence((Nonterminal('true', MessageType('logic', 'Conjunction')),)),
        action=Lambda(
            [Var('value', MessageType('logic', 'Conjunction'))],
            MessageType('logic', 'Formula'),
            Call(Message('logic', 'Formula'), [Call(OneOf(Symbol('true')), [Var('value', MessageType('logic', 'Conjunction'))])])
        )
    ), is_final=False)

    add_rule(Rule(
        lhs=Nonterminal('formula', MessageType('logic', 'Formula')),
        rhs=Sequence((Nonterminal('false', MessageType('logic', 'Disjunction')),)),
        action=Lambda(
            [Var('value', MessageType('logic', 'Disjunction'))],
            MessageType('logic', 'Formula'),
            Call(Message('logic', 'Formula'), [Call(OneOf(Symbol('false')), [Var('value', MessageType('logic', 'Disjunction'))])])
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
        action=Lambda(
            [Var('config', MessageType('transactions', 'ExportCSVConfig'))],
            MessageType('transactions', 'Export'),
            Call(Message('transactions', 'Export'), [Call(OneOf(Symbol('csv_config')), [Var('config', MessageType('transactions', 'ExportCSVConfig'))])])
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
        action=Lambda(
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
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('export_csvcolumns', ListType(MessageType('transactions', 'ExportCSVColumn'))),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('columns'),
            Star(Nonterminal('export_csvcolumn', MessageType('transactions', 'ExportCSVColumn'))),
            LitTerminal(')')
        )),
        action=Lambda(
            [Var('columns', ListType(MessageType('transactions', 'ExportCSVColumn')))],
            ListType(MessageType('transactions', 'ExportCSVColumn')),
            Var('columns', ListType(MessageType('transactions', 'ExportCSVColumn')))
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
        action=Lambda(
            [Var('name', BaseType('String')), Var('relation_id', MessageType('logic', 'RelationId'))],
            MessageType('transactions', 'ExportCSVColumn'),
            Call(Message('transactions', 'ExportCSVColumn'), [
                Var('name', BaseType('String')),
                Var('relation_id', MessageType('logic', 'RelationId'))
            ])
        )
    ))

    # Var rule
    add_rule(Rule(
        lhs=Nonterminal('var', MessageType('logic', 'Var')),
        rhs=Sequence((NamedTerminal('SYMBOL', BaseType('String')),)),
        action=Lambda(
            [Var('symbol', BaseType('String'))],
            return_type=MessageType('logic', 'Var'),
            body=Call(Message('logic', 'Var'), [Var('symbol', BaseType('String'))])
        )
    ))

    # ID rules
    add_rule(Rule(
        lhs=Nonterminal('fragment_id', MessageType('fragments', 'FragmentId')),
        rhs=NamedTerminal('COLON_SYMBOL', BaseType('String')),
        action=Lambda(
            [Var('symbol', BaseType('String'))],
            return_type=MessageType('fragments', 'FragmentId'),
            body=Call(Builtin('fragment_id_from_string'), [Var('symbol', BaseType('String'))])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('relation_id', MessageType('logic', 'RelationId')),
        rhs=NamedTerminal('COLON_SYMBOL', BaseType('String')),
        action=Lambda(
            [Var('symbol', BaseType('String'))],
            return_type=MessageType('logic', 'RelationId'),
            body=Call(Builtin('relation_id_from_string'), [Var('symbol', BaseType('String'))])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('relation_id', MessageType('logic', 'RelationId')),
        rhs=Sequence((NamedTerminal('INT', BaseType('Int64')),)),
        action=Lambda(
            [Var('INT', BaseType('Int64'))],
            return_type=MessageType('logic', 'RelationId'),
            body=Call(Builtin('relation_id_from_int'), [Var('INT', BaseType('Int64'))])
        )
    ))

    # Specialized value rule
    add_rule(Rule(
        lhs=Nonterminal('specialized_value', MessageType('logic', 'Value')),
        rhs=Sequence((LitTerminal('#'), Nonterminal('value', MessageType('logic', 'Value')))),
        action=Lambda(
            [Var('value', MessageType('logic', 'Value'))],
            MessageType('logic', 'Value'),
            Var('value', MessageType('logic', 'Value'))
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
        ('boolean_type', MessageType('logic', 'BooleanType'), LitTerminal('BOOL'), # HACK: BOOL is only used in or_monoid
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
        add_rule(Rule(lhs=Nonterminal(lhs_name, lhs_type), rhs=rhs, action=action))

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
            action=Lambda(
                [Var('left', MessageType('logic', 'Term')), Var('right', MessageType('logic', 'Term'))],
                MessageType('logic', 'Primitive'),
                Call(Message('logic', 'Primitive'), [
                    Lit(prim),
                    Call(Message('logic', 'RelTerm'), [Call(OneOf(Symbol('term')), [Var('left', MessageType('logic', 'Term'))])]),
                    Call(Message('logic', 'RelTerm'), [Call(OneOf(Symbol('term')), [Var('right', MessageType('logic', 'Term'))])])
                ])
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
            action=Lambda(
                [
                    Var('left', MessageType('logic', 'Term')),
                    Var('right', MessageType('logic', 'Term')),
                    Var('result', MessageType('logic', 'Term'))
                ],
                MessageType('logic', 'Primitive'),
                Call(Message('logic', 'Primitive'), [
                    Lit(prim),
                    Call(Message('logic', 'RelTerm'), [Call(OneOf(Symbol('term')), [Var('left', MessageType('logic', 'Term'))])]),
                    Call(Message('logic', 'RelTerm'), [Call(OneOf(Symbol('term')), [Var('right', MessageType('logic', 'Term'))])]),
                    Call(Message('logic', 'RelTerm'), [Call(OneOf(Symbol('term')), [Var('result', MessageType('logic', 'Term'))])])
                ])
            )
        ))

    # Primitive wrapper rules for operators (not final - auto-generation can add more)
    for name, _op, _prim in _comparison_ops + _arithmetic_ops:
        add_rule(Rule(
            lhs=Nonterminal('primitive', MessageType('logic', 'Primitive')),
            rhs=Sequence((Nonterminal(name, MessageType('logic', 'Primitive')),)),
            action=Lambda(
                [Var('op', MessageType('logic', 'Primitive'))],
                MessageType('logic', 'Primitive'),
                Var('op', MessageType('logic', 'Primitive'))
            )
        ), is_final=False)

    add_rule(Rule(
        lhs=Nonterminal('new_fragment_id', MessageType('fragments', 'FragmentId')),
        rhs=Nonterminal('fragment_id', MessageType('fragments', 'FragmentId')),
        action=Lambda(
            [
                Var('fragment_id', MessageType('fragments', 'FragmentId')),
            ],
            MessageType('fragments', 'FragmentId'),
            Seq([
                Call(Builtin('start_fragment'), [Var('fragment_id', MessageType('fragments', 'FragmentId'))]),
                Var('fragment_id', MessageType('fragments', 'FragmentId')),
            ])
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
        action=Lambda(
            [
                Var('fragment_id', MessageType('fragments', 'FragmentId')),
                Var('declarations', ListType(MessageType('logic', 'Declaration')))
            ],
            MessageType('fragments', 'Fragment'),
            Call(Builtin('construct_fragment'), [
                Var('fragment_id', MessageType('fragments', 'FragmentId')),
                Var('declarations', ListType(MessageType('logic', 'Declaration')))
            ])
        )
    ))

    return result
