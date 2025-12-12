"""Builtin grammar rules that are manually specified.

These rules define the grammar for constructs that cannot be auto-generated
from protobuf definitions, such as value literals, date/datetime parsing,
configuration syntax, bindings, abstractions, type literals, and operators.
"""

from typing import Dict, List, Tuple

from .grammar import Rule, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence
from .target import (
    Lambda, Call, Var, Symbol, Lit, IfElse, Builtin, Message,
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
    _config_type = ListType(TupleType([BaseType('String'), MessageType('Value')]))
    _bindings_type = TupleType([ListType(MessageType('Binding')), ListType(MessageType('Binding'))])
    _abstraction_with_arity_type = TupleType([MessageType('Abstraction'), BaseType('Int64')])
    _monoid_op_type = FunctionType([MessageType('Type')], MessageType('Monoid'))

    # Value literal rules
    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('Value')),
        rhs=Sequence((Nonterminal('date', MessageType('DateValue')),)),
        action=Lambda(
            [Var('value', MessageType('DateValue'))],
            MessageType('Value'),
            Call(Message('Value'), [Call(Message('OneOf'), [Symbol('date_value'), Var('value', MessageType('DateValue'))])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('Value')),
        rhs=Sequence((Nonterminal('datetime', MessageType('DateTimeValue')),)),
        action=Lambda(
            [Var('value', MessageType('DateTimeValue'))],
            MessageType('Value'),
            Call(Message('Value'), [Call(Message('OneOf'), [Symbol('datetime_value'), Var('value', MessageType('DateTimeValue'))])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('Value')),
        rhs=Sequence((NamedTerminal('STRING', BaseType('String')),)),
        action=Lambda(
            [Var('value', BaseType('String'))],
            MessageType('Value'),
            Call(Message('Value'), [Call(Message('OneOf'), [Symbol('string_value'), Var('value', BaseType('String'))])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('Value')),
        rhs=Sequence((NamedTerminal('INT', BaseType('Int64')),)),
        action=Lambda(
            [Var('value', BaseType('Int64'))],
            MessageType('Value'),
            Call(Message('Value'), [Call(Message('OneOf'), [Symbol('int_value'), Var('value', BaseType('Int64'))])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('Value')),
        rhs=Sequence((NamedTerminal('FLOAT', BaseType('Float64')),)),
        action=Lambda(
            [Var('value', BaseType('Float64'))],
            MessageType('Value'),
            Call(Message('Value'), [Call(Message('OneOf'), [Symbol('float_value'), Var('value', BaseType('Float64'))])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('Value')),
        rhs=Sequence((NamedTerminal('UINT128', MessageType('UInt128Value')),)),
        action=Lambda(
            [Var('value', MessageType('UInt128Value'))],
            MessageType('Value'),
            Call(Message('Value'), [Call(Message('OneOf'), [Symbol('uint128_value'), Var('value', MessageType('UInt128Value'))])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('Value')),
        rhs=Sequence((NamedTerminal('INT128', MessageType('Int128Value')),)),
        action=Lambda(
            [Var('value', MessageType('Int128Value'))],
            MessageType('Value'),
            Call(Message('Value'), [Call(Message('OneOf'), [Symbol('int128_value'), Var('value', MessageType('Int128Value'))])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('Value')),
        rhs=Sequence((NamedTerminal('DECIMAL', MessageType('DecimalValue')),)),
        action=Lambda(
            [Var('value', MessageType('DecimalValue'))],
            MessageType('Value'),
            Call(Message('Value'), [Call(Message('OneOf'), [Symbol('decimal_value'), Var('value', MessageType('DecimalValue'))])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('Value')),
        rhs=Sequence((LitTerminal('missing'),)),
        action=Lambda(
            [],
            MessageType('Value'),
            Call(Message('Value'), [Call(Message('OneOf'), [Symbol('missing_value'), Call(Message('MissingValue'), [])])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('Value')),
        rhs=Sequence((LitTerminal('true'),)),
        action=Lambda(
            [],
            MessageType('Value'),
            Call(Message('Value'), [Call(Message('OneOf'), [Symbol('boolean_value'), Lit(True)])])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value', MessageType('Value')),
        rhs=Sequence((LitTerminal('false'),)),
        action=Lambda(
            [],
            MessageType('Value'),
            Call(Message('Value'), [Call(Message('OneOf'), [Symbol('boolean_value'), Lit(False)])])
        )
    ))

    # Date and datetime rules
    add_rule(Rule(
        lhs=Nonterminal('date', MessageType('DateValue')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('date'),
            NamedTerminal('INT', BaseType('Int64')),
            NamedTerminal('INT', BaseType('Int64')),
            NamedTerminal('INT', BaseType('Int64')),
            LitTerminal(')')
        )),
        action=Lambda(
            [Var('year', BaseType('Int64')), Var('month', BaseType('Int64')), Var('day', BaseType('Int64'))],
            MessageType('DateValue'),
            Call(Message('DateValue'), [
                Var('year', BaseType('Int64')),
                Var('month', BaseType('Int64')),
                Var('day', BaseType('Int64'))
            ])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('datetime', MessageType('DateTimeValue')),
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
            MessageType('DateTimeValue'),
            Call(Message('DateTimeValue'), [
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
            Star(Nonterminal('config_key_value', TupleType([BaseType('String'), MessageType('Value')]))),
            LitTerminal('}')
        )),
        action=Lambda(
            [Var('config_key_value', _config_type)],
            return_type=_config_type,
            body=Var('config_key_value', _config_type)
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('config_key_value', TupleType([BaseType('String'), MessageType('Value')])),
        rhs=Sequence((
            LitTerminal(':'),
            NamedTerminal('SYMBOL', BaseType('String')),
            Nonterminal('value', MessageType('Value'))
        )),
        action=Lambda(
            [Var('symbol', BaseType('String')), Var('value', MessageType('Value'))],
            TupleType([BaseType('String'), MessageType('Value')]),
            Call(Builtin('make_tuple'), [Var('symbol', BaseType('String')), Var('value', MessageType('Value'))])
        )
    ))

    # Transaction rule
    add_rule(Rule(
        lhs=Nonterminal('transaction', MessageType('Transaction')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('transaction'),
            Option(Nonterminal('configure', MessageType('Configure'))),
            Option(Nonterminal('sync', MessageType('Sync'))),
            Star(Nonterminal('epoch', MessageType('Epoch'))),
            LitTerminal(')')
        )),
        action=Lambda(
            [
                Var('configure', OptionType(MessageType('Configure'))),
                Var('sync', OptionType(MessageType('Sync'))),
                Var('epochs', ListType(MessageType('Epoch')))
            ],
            MessageType('Transaction'),
            Call(Message('Transaction'), [
                Var('epochs', ListType(MessageType('Epoch'))),
                Var('configure', OptionType(MessageType('Configure'))),
                Var('sync', OptionType(MessageType('Sync')))
            ])
        )
    ))

    # Bindings rules
    add_rule(Rule(
        lhs=Nonterminal('bindings', _bindings_type),
        rhs=Sequence((
            LitTerminal('['),
            Star(Nonterminal('binding', MessageType('Binding'))),
            Option(Nonterminal('value_bindings', ListType(MessageType('Binding')))),
            LitTerminal(']')
        )),
        action=Lambda(
            [
                Var('keys', ListType(MessageType('Binding'))),
                Var('values', OptionType(ListType(MessageType('Binding'))))
            ],
            _bindings_type,
            Call(Builtin('make_tuple'), [
                Var('keys', ListType(MessageType('Binding'))),
                Var('values', OptionType(ListType(MessageType('Binding'))))
            ])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('value_bindings', ListType(MessageType('Binding'))),
        rhs=Sequence((
            LitTerminal('|'),
            Star(Nonterminal('binding', MessageType('Binding')))
        )),
        action=Lambda(
            [Var('values', ListType(MessageType('Binding')))],
            ListType(MessageType('Binding')),
            Var('values', ListType(MessageType('Binding')))
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('binding', MessageType('Binding')),
        rhs=Sequence((
            NamedTerminal('SYMBOL', BaseType('String')),
            LitTerminal('::'),
            Nonterminal('type', MessageType('Type'))
        )),
        action=Lambda(
            [Var('symbol', BaseType('String')), Var('type', MessageType('Type'))],
            MessageType('Binding'),
            Call(Message('Binding'), [
                Call(Message('Var'), [Var('symbol', BaseType('String'))]),
                Var('type', MessageType('Type'))
            ])
        )
    ))

    # Abstraction rules
    add_rule(Rule(
        lhs=Nonterminal('abstraction_with_arity', _abstraction_with_arity_type),
        rhs=Sequence((
            LitTerminal('('),
            Nonterminal('bindings', _bindings_type),
            Nonterminal('formula', MessageType('Formula')),
            LitTerminal(')')
        )),
        action=Lambda(
            params=[Var('bindings', _bindings_type), Var('formula', MessageType('Formula'))],
            return_type=_abstraction_with_arity_type,
            body=Call(Builtin('make_tuple'), [
                Call(Message('Abstraction'), [
                    Call(Builtin('list_concat'), [
                        Call(Builtin('fst'), [Var('bindings', _bindings_type)]),
                        Call(Builtin('snd'), [Var('bindings', _bindings_type)])
                    ]),
                    Var('formula', MessageType('Formula'))
                ]),
                Call(Builtin('length'), [Call(Builtin('snd'), [Var('bindings', _bindings_type)])])
            ])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('abstraction', MessageType('Abstraction')),
        rhs=Sequence((
            LitTerminal('('),
            Nonterminal('bindings', _bindings_type),
            Nonterminal('formula', MessageType('Formula')),
            LitTerminal(')')
        )),
        action=Lambda(
            params=[Var('bindings', _bindings_type), Var('formula', MessageType('Formula'))],
            return_type=MessageType('Abstraction'),
            body=Call(Message('Abstraction'), [
                Call(Builtin('list_concat'), [
                    Call(Builtin('fst'), [Var('bindings', _bindings_type)]),
                    Call(Builtin('snd'), [Var('bindings', _bindings_type)])
                ]),
                Var('formula', MessageType('Formula'))
            ])
        )
    ))

    # Name rule
    add_rule(Rule(
        lhs=Nonterminal('name', BaseType('String')),
        rhs=Sequence((LitTerminal(':'), NamedTerminal('SYMBOL', BaseType('String')))),
        action=Lambda(
            [Var('symbol', BaseType('String'))],
            BaseType('String'),
            Var('symbol', BaseType('String'))
        )
    ))

    # Monoid rules
    add_rule(Rule(
        lhs=Nonterminal('monoid', MessageType('Monoid')),
        rhs=Sequence((
            Nonterminal('type', MessageType('Type')),
            LitTerminal('::'),
            Nonterminal('monoid_op', _monoid_op_type)
        )),
        action=Lambda(
            [Var('type', MessageType('Type')), Var('op', _monoid_op_type)],
            return_type=MessageType('Monoid'),
            body=Call(Var('op', _monoid_op_type), [Var('type', MessageType('Type'))])
        )
    ))

    def _make_monoid_op_rule(lit: str, symbol: str, constructor: str, has_type: bool) -> Rule:
        if has_type:
            body = Call(Message('Monoid'), [
                Call(Message('OneOf'), [
                    Symbol(symbol),
                    Call(Message(constructor), [Var('type', MessageType('Type'))])
                ])
            ])
        else:
            body = Call(Message('Monoid'), [
                Call(Message('OneOf'), [
                    Symbol(symbol),
                    Call(Message(constructor), [])
                ])
            ])
        return Rule(
            lhs=Nonterminal('monoid_op', _monoid_op_type),
            rhs=LitTerminal(lit),
            action=Lambda(
                [],
                return_type=_monoid_op_type,
                body=Lambda([Var('type', MessageType('Type'))], return_type=MessageType('Monoid'), body=body)
            )
        )

    add_rule(_make_monoid_op_rule('OR', 'or_monoid', 'OrMonoid', False))
    add_rule(_make_monoid_op_rule('MIN', 'min_monoid', 'MinMonoid', True))
    add_rule(_make_monoid_op_rule('MAX', 'max_monoid', 'MaxMonoid', True))
    add_rule(_make_monoid_op_rule('SUM', 'sum', 'SumMonoid', True))

    # Configure rule
    add_rule(Rule(
        lhs=Nonterminal('configure', MessageType('Configure')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('configure'),
            Nonterminal('config_dict', _config_type),
            LitTerminal(')')
        )),
        action=Lambda(
            [Var('config_dict', _config_type)],
            return_type=MessageType('Configure'),
            body=Call(Message('Configure'), [Var('config_dict', _config_type)])
        )
    ))

    # True/false formula rules
    add_rule(Rule(
        lhs=Nonterminal('true', MessageType('Conjunction')),
        rhs=Sequence((LitTerminal('('), LitTerminal('true'), LitTerminal(')'))),
        action=Lambda([], MessageType('Conjunction'), Call(Message('Conjunction'), [Call(Builtin('make_list'), [])]))
    ))

    add_rule(Rule(
        lhs=Nonterminal('false', MessageType('Disjunction')),
        rhs=Sequence((LitTerminal('('), LitTerminal('false'), LitTerminal(')'))),
        action=Lambda([], MessageType('Disjunction'), Call(Message('Disjunction'), [Call(Builtin('make_list'), [])]))
    ))

    # Formula rules (not final - auto-generation can add more)
    add_rule(Rule(
        lhs=Nonterminal('formula', MessageType('Formula')),
        rhs=Sequence((Nonterminal('true', MessageType('Conjunction')),)),
        action=Lambda(
            [Var('value', MessageType('Conjunction'))],
            MessageType('Formula'),
            Call(Message('Formula'), [Call(Message('OneOf'), [Symbol('true'), Var('value', MessageType('Conjunction'))])])
        )
    ), is_final=False)

    add_rule(Rule(
        lhs=Nonterminal('formula', MessageType('Formula')),
        rhs=Sequence((Nonterminal('false', MessageType('Disjunction')),)),
        action=Lambda(
            [Var('value', MessageType('Disjunction'))],
            MessageType('Formula'),
            Call(Message('Formula'), [Call(Message('OneOf'), [Symbol('false'), Var('value', MessageType('Disjunction'))])])
        )
    ), is_final=False)

    # Export rules
    add_rule(Rule(
        lhs=Nonterminal('export', MessageType('Export')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('export'),
            Nonterminal('export_csvconfig', MessageType('ExportCsvConfig')),
            LitTerminal(')')
        )),
        action=Lambda(
            [Var('config', MessageType('ExportCsvConfig'))],
            MessageType('Export'),
            Call(Message('Export'), [Var('config', MessageType('ExportCsvConfig'))])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('export_csvconfig', MessageType('ExportCsvConfig')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('export_csvconfig'),
            Nonterminal('export_path', MessageType('ExportPath')),
            Nonterminal('export_csvcolumns', ListType(MessageType('ExportCsvColumn'))),
            Nonterminal('config_dict', _config_type),
            LitTerminal(')')
        )),
        action=Lambda(
            [
                Var('path', MessageType('ExportPath')),
                Var('columns', ListType(MessageType('ExportCsvColumn'))),
                Var('config', _config_type)
            ],
            MessageType('ExportCsvConfig'),
            Call(Builtin('export_csv_config'), [
                Var('path', MessageType('ExportPath')),
                Var('columns', ListType(MessageType('ExportCsvColumn'))),
                Var('config', _config_type)
            ])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('export_csvcolumns', ListType(MessageType('ExportCsvColumn'))),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('columns'),
            Star(Nonterminal('export_csvcolumn', MessageType('ExportCsvColumn'))),
            LitTerminal(')')
        )),
        action=Lambda(
            [Var('columns', ListType(MessageType('ExportCsvColumn')))],
            ListType(MessageType('ExportCsvColumn')),
            Var('columns', ListType(MessageType('ExportCsvColumn')))
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('export_csvcolumn', MessageType('ExportCsvColumn')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('column'),
            NamedTerminal('STRING', BaseType('String')),
            Nonterminal('relation_id', MessageType('RelationId')),
            LitTerminal(')')
        )),
        action=Lambda(
            [Var('name', BaseType('String')), Var('relation_id', MessageType('RelationId'))],
            MessageType('ExportCsvColumn'),
            Call(Message('ExportCsvColumn'), [
                Var('name', BaseType('String')),
                Var('relation_id', MessageType('RelationId'))
            ])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('export_path', MessageType('ExportPath')),
        rhs=Sequence((
            LitTerminal('('), LitTerminal('path'),
            NamedTerminal('STRING', BaseType('String')),
            LitTerminal(')')
        )),
        action=Lambda(
            [Var('path', BaseType('String'))],
            return_type=MessageType('ExportPath'),
            body=Call(Message('ExportPath'), [Var('path', BaseType('String'))])
        )
    ))

    # Var rule
    add_rule(Rule(
        lhs=Nonterminal('var', MessageType('Var')),
        rhs=Sequence((NamedTerminal('SYMBOL', BaseType('String')),)),
        action=Lambda(
            [Var('symbol', BaseType('String'))],
            return_type=MessageType('Var'),
            body=Call(Message('Var'), [Var('symbol', BaseType('String'))])
        )
    ))

    # ID rules
    add_rule(Rule(
        lhs=Nonterminal('fragment_id', MessageType('FragmentId')),
        rhs=Sequence((LitTerminal(':'), NamedTerminal('SYMBOL', BaseType('String')))),
        action=Lambda(
            [Var('symbol', BaseType('String'))],
            return_type=MessageType('FragmentId'),
            body=Call(Builtin('fragment_id_from_string'), [Var('symbol', BaseType('String'))])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('relation_id', MessageType('RelationId')),
        rhs=Sequence((LitTerminal(':'), NamedTerminal('SYMBOL', BaseType('String')))),
        action=Lambda(
            [Var('symbol', BaseType('String'))],
            return_type=MessageType('RelationId'),
            body=Call(Builtin('relation_id_from_string'), [Var('symbol', BaseType('String'))])
        )
    ))

    add_rule(Rule(
        lhs=Nonterminal('relation_id', MessageType('RelationId')),
        rhs=Sequence((NamedTerminal('INT', BaseType('Int64')),)),
        action=Lambda(
            [Var('INT', BaseType('Int64'))],
            return_type=MessageType('RelationId'),
            body=Call(Builtin('relation_id_from_int'), [Var('INT', BaseType('Int64'))])
        )
    ))

    # Specialized value rule
    add_rule(Rule(
        lhs=Nonterminal('specialized_value', MessageType('Value')),
        rhs=Sequence((LitTerminal('#'), Nonterminal('value', MessageType('Value')))),
        action=Lambda(
            [Var('value', MessageType('Value'))],
            MessageType('Value'),
            Var('value', MessageType('Value'))
        )
    ))

    # Type rules
    _type_rules = [
        ('unspecified_type', MessageType('UnspecifiedType'), LitTerminal('UNKNOWN'),
         Lambda([], MessageType('UnspecifiedType'), Call(Message('UnspecifiedType'), []))),
        ('string_type', MessageType('StringType'), LitTerminal('STRING'),
         Lambda([], MessageType('StringType'), Call(Message('StringType'), []))),
        ('int_type', MessageType('IntType'), LitTerminal('INT'),
         Lambda([], MessageType('IntType'), Call(Message('IntType'), []))),
        ('float_type', MessageType('FloatType'), LitTerminal('FLOAT'),
         Lambda([], MessageType('FloatType'), Call(Message('FloatType'), []))),
        ('uint128_type', MessageType('Uint128Type'), LitTerminal('UINT128'),
         Lambda([], MessageType('Uint128Type'), Call(Message('Uint128Type'), []))),
        ('int128_type', MessageType('Int128Type'), LitTerminal('INT128'),
         Lambda([], MessageType('Int128Type'), Call(Message('Int128Type'), []))),
        ('boolean_type', MessageType('BooleanType'), LitTerminal('BOOLEAN'),
         Lambda([], MessageType('BooleanType'), Call(Message('BooleanType'), []))),
        ('date_type', MessageType('DateType'), LitTerminal('DATE'),
         Lambda([], MessageType('DateType'), Call(Message('DateType'), []))),
        ('datetime_type', MessageType('DatetimeType'), LitTerminal('DATETIME'),
         Lambda([], MessageType('DatetimeType'), Call(Message('DatetimeType'), []))),
        ('missing_type', MessageType('MissingType'), LitTerminal('MISSING'),
         Lambda([], MessageType('MissingType'), Call(Message('MissingType'), []))),
        ('decimal_type', MessageType('DecimalType'),
         Sequence((LitTerminal('('), LitTerminal('DECIMAL'), NamedTerminal('INT', BaseType('Int64')), NamedTerminal('INT', BaseType('Int64')), LitTerminal(')'))),
         Lambda(
             [Var('precision', BaseType('Int64')), Var('scale', BaseType('Int64'))],
             MessageType('DecimalType'),
             Call(Message('DecimalType'), [Var('precision', BaseType('Int64')), Var('scale', BaseType('Int64'))])
         )),
    ]
    for lhs_name, lhs_type, rhs, action in _type_rules:
        add_rule(Rule(lhs=Nonterminal(lhs_name, lhs_type), rhs=rhs, action=action))

    # Comparison operator rules
    _comparison_ops = [
        ('eq', '=', 'rel_primitive_eq'),
        ('lt', '<', 'rel_primitive_lt'),
        ('lt_eq', '<=', 'rel_primitive_lt_eq'),
        ('gt', '>', 'rel_primitive_gt'),
        ('gt_eq', '>=', 'rel_primitive_gt_eq'),
    ]
    for name, op, prim in _comparison_ops:
        add_rule(Rule(
            lhs=Nonterminal(name, MessageType('Primitive')),
            rhs=Sequence((
                LitTerminal('('), LitTerminal(op),
                Nonterminal('term', MessageType('Term')),
                Nonterminal('term', MessageType('Term')),
                LitTerminal(')')
            )),
            action=Lambda(
                [Var('left', MessageType('Term')), Var('right', MessageType('Term'))],
                MessageType('Primitive'),
                Call(Message('Primitive'), [Lit(prim), Var('left', MessageType('Term')), Var('right', MessageType('Term'))])
            )
        ))

    # Arithmetic operator rules
    _arithmetic_ops = [
        ('add', '+', 'rel_primitive_add'),
        ('minus', '-', 'rel_primitive_subtract'),
        ('multiply', '*', 'rel_primitive_multiply'),
        ('divide', '/', 'rel_primitive_divide'),
    ]
    for name, op, prim in _arithmetic_ops:
        add_rule(Rule(
            lhs=Nonterminal(name, MessageType('Primitive')),
            rhs=Sequence((
                LitTerminal('('), LitTerminal(op),
                Nonterminal('term', MessageType('Term')),
                Nonterminal('term', MessageType('Term')),
                Nonterminal('term', MessageType('Term')),
                LitTerminal(')')
            )),
            action=Lambda(
                [
                    Var('left', MessageType('Term')),
                    Var('right', MessageType('Term')),
                    Var('result', MessageType('Term'))
                ],
                MessageType('Primitive'),
                Call(Message('Primitive'), [
                    Lit(prim),
                    Var('left', MessageType('Term')),
                    Var('right', MessageType('Term')),
                    Var('result', MessageType('Term'))
                ])
            )
        ))

    # Primitive wrapper rules for operators (not final - auto-generation can add more)
    for name, _op, _prim in _comparison_ops + _arithmetic_ops:
        add_rule(Rule(
            lhs=Nonterminal('primitive', MessageType('Primitive')),
            rhs=Sequence((Nonterminal(name, MessageType('Primitive')),)),
            action=Lambda(
                [Var('op', MessageType('Primitive'))],
                MessageType('Primitive'),
                Var('op', MessageType('Primitive'))
            )
        ), is_final=False)

    return result
