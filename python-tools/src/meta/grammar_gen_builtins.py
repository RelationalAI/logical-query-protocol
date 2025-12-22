"""Builtin grammar rules that are manually specified.

These rules define the grammar for constructs that cannot be auto-generated
from protobuf definitions, such as value literals, date/datetime parsing,
configuration syntax, bindings, abstractions, type literals, and operators.
"""

from types import NoneType
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
    nonfinal_nonterminals: Set[Nonterminal] = set()

    def add_rule(rule: Rule) -> None:
        lhs = rule.lhs
        if lhs not in result:
            result[lhs] = ([], True)
        rules_list, existing_final = result[lhs]
        rules_list.append(rule)
        result[lhs] = (rules_list, existing_final)

    def mark_nonfinal(lhs: Nonterminal) -> None:
        nonfinal_nonterminals.add(lhs)

    # Common types used throughout
    _string_type = BaseType('String')
    _int64_type = BaseType('Int64')
    _float64_type = BaseType('Float64')
    _bool_type = BaseType('Bool')
    _value_type = MessageType('logic', 'Value')
    _binding_type = MessageType('logic', 'Binding')
    _formula_type = MessageType('logic', 'Formula')
    _term_type = MessageType('logic', 'Term')
    _abstraction_type = MessageType('logic', 'Abstraction')
    _primitive_type = MessageType('logic', 'Primitive')
    _relation_id_type = MessageType('logic', 'RelationId')
    _relterm_type = MessageType('logic', 'RelTerm')
    _attribute_type = MessageType('logic', 'Attribute')
    _date_value_type = MessageType('logic', 'DateValue')
    _datetime_value_type = MessageType('logic', 'DateTimeValue')
    _uint128_value_type = MessageType('logic', 'UInt128Value')
    _int128_value_type = MessageType('logic', 'Int128Value')
    _decimal_value_type = MessageType('logic', 'DecimalValue')
    _var_type = MessageType('logic', 'Var')
    _type_type = MessageType('logic', 'Type')
    _monoid_type = MessageType('logic', 'Monoid')
    _conjunction_type = MessageType('logic', 'Conjunction')
    _disjunction_type = MessageType('logic', 'Disjunction')
    _declaration_type = MessageType('logic', 'Declaration')
    _fragment_id_type = MessageType('fragments', 'FragmentId')
    _fragment_type = MessageType('fragments', 'Fragment')
    _transaction_type = MessageType('transactions', 'Transaction')
    _configure_type = MessageType('transactions', 'Configure')
    _sync_type = MessageType('transactions', 'Sync')
    _epoch_type = MessageType('transactions', 'Epoch')
    _output_type = MessageType('transactions', 'Output')
    _abort_type = MessageType('transactions', 'Abort')
    _export_type = MessageType('transactions', 'Export')
    _export_csv_config_type = MessageType('transactions', 'ExportCSVConfig')
    _export_csv_column_type = MessageType('transactions', 'ExportCSVColumn')

    _config_type = ListType(TupleType([_string_type, _value_type]))
    _bindings_type = TupleType([ListType(_binding_type), ListType(_binding_type)])
    _abstraction_with_arity_type = TupleType([_abstraction_type, _int64_type])
    _monoid_op_type = FunctionType([_type_type], _monoid_type)





    # Common nonterminals
    _value_nt = Nonterminal('value', _value_type)
    _binding_nt = Nonterminal('binding', _binding_type)
    _bindings_nt = Nonterminal('bindings', _bindings_type)
    _formula_nt = Nonterminal('formula', _formula_type)
    _term_nt = Nonterminal('term', _term_type)
    _relterm_nt = Nonterminal('relterm', _relterm_type)
    _abstraction_nt = Nonterminal('abstraction', _abstraction_type)
    _primitive_nt = Nonterminal('primitive', _primitive_type)
    _relation_id_nt = Nonterminal('relation_id', _relation_id_type)
    _attribute_nt = Nonterminal('attribute', _attribute_type)
    _type_nt = Nonterminal('type', _type_type)
    _monoid_nt = Nonterminal('monoid', _monoid_type)
    _declaration_nt = Nonterminal('declaration', _declaration_type)
    _name_nt = Nonterminal('name', _string_type)
    _config_dict_nt = Nonterminal('config_dict', _config_type)
    _date_nt = Nonterminal('date', _date_value_type)
    _datetime_nt = Nonterminal('datetime', _datetime_value_type)

    # Common terminals
    _string_terminal = NamedTerminal('STRING', _string_type)
    _int_terminal = NamedTerminal('INT', _int64_type)
    _float_terminal = NamedTerminal('FLOAT', _float64_type)
    _symbol_terminal = NamedTerminal('SYMBOL', _string_type)
    _colon_symbol_terminal = NamedTerminal('COLON_SYMBOL', _string_type)
    _lparen = LitTerminal('(')
    _rparen = LitTerminal(')')



    # Common Var expressions
    def _var_value(typ=_value_type):
        return Var('value', typ)

    def _var_msg(typ):
        return Var('msg', typ)

    def _var_symbol(typ=_string_type):
        return Var('symbol', typ)

    def _var_name(typ=_string_type):
        return Var('name', typ)

    # Common Builtin functions that return Call instances
    def _builtin_equal(*args):
        return Call(Builtin('equal'), list(args))

    def _builtin_which_oneof(*args):
        return Call(Builtin('WhichOneof'), list(args))

    def _builtin_get_field(*args):
        return Call(Builtin('get_field'), list(args))

    def _builtin_some(*args):
        return Call(Builtin('Some'), list(args))

    def _builtin_make_tuple(*args):
        return Call(Builtin('make_tuple'), list(args))

    def _builtin_fst(*args):
        return Call(Builtin('fst'), list(args))

    def _builtin_snd(*args):
        return Call(Builtin('snd'), list(args))

    def _builtin_is_none(*args):
        return Call(Builtin('is_none'), list(args))

    def _builtin_is_empty(*args):
        return Call(Builtin('is_empty'), list(args))

    def _builtin_list_concat(*args):
        return Call(Builtin('list_concat'), list(args))

    def _builtin_length(*args):
        return Call(Builtin('length'), list(args))

    def _builtin_unwrap_option_or(*args):
        return Call(Builtin('unwrap_option_or'), list(args))

    # Common Message constructor functions that return Call instances
    def _message_value(*args):
        return Call(Message('logic', 'Value'), list(args))

    def _message_binding(*args):
        return Call(Message('logic', 'Binding'), list(args))

    def _message_var(*args):
        return Call(Message('logic', 'Var'), list(args))

    def _message_abstraction(*args):
        return Call(Message('logic', 'Abstraction'), list(args))

    def _message_primitive(*args):
        return Call(Message('logic', 'Primitive'), list(args))

    def _message_relterm(*args):
        return Call(Message('logic', 'RelTerm'), list(args))

    def _message_date_value(*args):
        return Call(Message('logic', 'DateValue'), list(args))

    def _message_datetime_value(*args):
        return Call(Message('logic', 'DateTimeValue'), list(args))

    def _message_conjunction(*args):
        return Call(Message('logic', 'Conjunction'), list(args))

    def _message_disjunction(*args):
        return Call(Message('logic', 'Disjunction'), list(args))

    def _message_formula(*args):
        return Call(Message('logic', 'Formula'), list(args))

    # Helper functions for common patterns (these remain as they provide additional convenience)
    def _which_oneof_call(msg_var, field_lit):
        """Create Call(Builtin('WhichOneof'), [msg_var, field_lit])."""
        return _builtin_which_oneof(msg_var, field_lit)

    def _get_field_call(msg_var, field_lit):
        """Create Call(Builtin('get_field'), [msg_var, field_lit])."""
        return _builtin_get_field(msg_var, field_lit)

    def _equal_call(left, right):
        """Create Call(Builtin('equal'), [left, right])."""
        return _builtin_equal(left, right)

    def _some_call(arg):
        """Create Call(Builtin('Some'), [arg])."""
        return _builtin_some(arg)

    def _make_tuple_call(args):
        """Create Call(Builtin('make_tuple'), args)."""
        return _builtin_make_tuple(*args)

    def _value_oneof_deconstruct(msg_var, oneof_field_name, result_type):
        """Create standard Value oneof deconstruct pattern."""
        return IfElse(
            _equal_call(
                _which_oneof_call(msg_var, Lit('value_type')),
                Lit(oneof_field_name)
            ),
            _some_call(_get_field_call(msg_var, Lit(oneof_field_name))),
            Lit(None)
        )

    def _formula_oneof_deconstruct(msg_var, oneof_field_name, result_type, extra_check=None):
        """Create standard Formula oneof deconstruct pattern."""
        base_check = _equal_call(
            _which_oneof_call(msg_var, Lit('formula_type')),
            Lit(oneof_field_name)
        )
        if extra_check:
            return IfElse(
                base_check,
                IfElse(extra_check, _some_call(_get_field_call(msg_var, Lit(oneof_field_name))), Lit(None)),
                Lit(None)
            )
        return IfElse(
            base_check,
            _some_call(_get_field_call(msg_var, Lit(oneof_field_name))),
            Lit(None)
        )

    # Helper function to generate Value oneof rules
    def _make_value_oneof_rule(rhs, value_type, oneof_field_name):
        """Create a rule for Value -> oneof field."""
        var_value = Var('value', value_type)
        msg_var = _var_msg(_value_type)
        return Rule(
            lhs=_value_nt,
            rhs=rhs,
            construct_action=Lambda(
                [var_value],
                _value_type,
                _message_value(Call(OneOf(oneof_field_name), [var_value]))
            ),
            deconstruct_action=Lambda(
                [msg_var],
                OptionType(value_type),
                _value_oneof_deconstruct(msg_var, oneof_field_name, value_type)
            )
        )

    # Value literal rules
    add_rule(_make_value_oneof_rule(_date_nt, _date_value_type, 'date_value'))
    add_rule(_make_value_oneof_rule(_datetime_nt, _datetime_value_type, 'datetime_value'))
    add_rule(_make_value_oneof_rule(_string_terminal, _string_type, 'string_value'))
    add_rule(_make_value_oneof_rule(_int_terminal, _int64_type, 'int_value'))
    add_rule(_make_value_oneof_rule(_float_terminal, _float64_type, 'float_value'))
    add_rule(_make_value_oneof_rule(NamedTerminal('UINT128', _uint128_value_type), _uint128_value_type, 'uint128_value'))
    add_rule(_make_value_oneof_rule(NamedTerminal('INT128', _int128_value_type), _int128_value_type, 'int128_value'))
    add_rule(_make_value_oneof_rule(NamedTerminal('DECIMAL', _decimal_value_type), _decimal_value_type, 'decimal_value'))

    # Special case: missing value
    add_rule(Rule(
        lhs=_value_nt,
        rhs=LitTerminal('missing'),
        construct_action=Lambda(
            [],
            _value_type,
            _message_value(Call(OneOf('missing_value'), [Call(Message('logic', 'MissingValue'), [])]))
        ),
        deconstruct_action=Lambda(
            [_var_msg(_value_type)],
            OptionType(TupleType([])),
            IfElse(
                _equal_call(_which_oneof_call(_var_msg(_value_type), Lit('value_type')), Lit('missing_value')),
                _some_call(_make_tuple_call([])),
                Lit(None)
            )
        )
    ))

    # Bool value rules
    _bool_value_nt = Nonterminal('bool_value', _bool_type)
    _var_bool_value = Var('value', _bool_type)

    add_rule(Rule(
        lhs=_bool_value_nt,
        rhs=LitTerminal('true'),
        construct_action=Lambda([], _bool_type, Lit(True)),
        deconstruct_action=Lambda(
            [_var_bool_value],
            OptionType(TupleType([])),
            IfElse(_equal_call(_var_bool_value, Lit(True)), _some_call(_make_tuple_call([])), Lit(None))
        )
    ))

    add_rule(Rule(
        lhs=_bool_value_nt,
        rhs=LitTerminal('false'),
        construct_action=Lambda([], _bool_type, Lit(False)),
        deconstruct_action=Lambda(
            [_var_bool_value],
            OptionType(TupleType([])),
            IfElse(_equal_call(_var_bool_value, Lit(False)), _some_call(_make_tuple_call([])), Lit(None))
        )
    ))

    add_rule(_make_value_oneof_rule(_bool_value_nt, _bool_type, 'boolean_value'))

    # Date and datetime rules
    _var_year = Var('year', _int64_type)
    _var_month = Var('month', _int64_type)
    _var_day = Var('day', _int64_type)
    _var_hour = Var('hour', _int64_type)
    _var_minute = Var('minute', _int64_type)
    _var_second = Var('second', _int64_type)
    _var_microsecond = Var('microsecond', OptionType(_int64_type))

    add_rule(Rule(
        lhs=_date_nt,
        rhs=Sequence((_lparen, LitTerminal('date'), _int_terminal, _int_terminal, _int_terminal, _rparen)),
        construct_action=Lambda(
            [_var_year, _var_month, _var_day],
            _date_value_type,
            _message_date_value(_var_year, _var_month, _var_day)
        ),
        deconstruct_action=Lambda(
            [_var_msg(_date_value_type)],
            OptionType(TupleType([_int64_type, _int64_type, _int64_type])),
            _some_call(_make_tuple_call([
                _get_field_call(_var_msg(_date_value_type), Lit('year')),
                _get_field_call(_var_msg(_date_value_type), Lit('month')),
                _get_field_call(_var_msg(_date_value_type), Lit('day'))
            ]))
        )
    ))

    _datetime_tuple_type = TupleType([_int64_type, _int64_type, _int64_type, _int64_type, _int64_type, _int64_type, OptionType(_int64_type)])

    add_rule(Rule(
        lhs=_datetime_nt,
        rhs=Sequence((
            _lparen, LitTerminal('datetime'),
            _int_terminal, _int_terminal, _int_terminal,
            _int_terminal, _int_terminal, _int_terminal,
            Option(_int_terminal),
            _rparen
        )),
        construct_action=Lambda(
            [_var_year, _var_month, _var_day, _var_hour, _var_minute, _var_second, _var_microsecond],
            _datetime_value_type,
            _message_datetime_value(
                _var_year, _var_month, _var_day, _var_hour, _var_minute, _var_second,
                IfElse(
                    _builtin_is_none(_var_microsecond),
                    Lit(0),
                    _builtin_some(_var_microsecond)
                )
            )
        ),
        deconstruct_action=Lambda(
            [_var_msg(_datetime_value_type)],
            OptionType(_datetime_tuple_type),
            _some_call(_make_tuple_call([
                _get_field_call(_var_msg(_datetime_value_type), Lit('year')),
                _get_field_call(_var_msg(_datetime_value_type), Lit('month')),
                _get_field_call(_var_msg(_datetime_value_type), Lit('day')),
                _get_field_call(_var_msg(_datetime_value_type), Lit('hour')),
                _get_field_call(_var_msg(_datetime_value_type), Lit('minute')),
                _get_field_call(_var_msg(_datetime_value_type), Lit('second')),
                IfElse(
                    _equal_call(_get_field_call(_var_msg(_datetime_value_type), Lit('microsecond')), Lit(0)),
                    Lit(None),
                    _some_call(_get_field_call(_var_msg(_datetime_value_type), Lit('microsecond')))
                )
            ]))
        )
    ))

    # Configuration rules
    _config_key_value_type = TupleType([_string_type, _value_type])
    _config_key_value_nt = Nonterminal('config_key_value', _config_key_value_type)
    _var_config = Var('config', _config_type)
    _var_config_key_value = Var('config_key_value', _config_type)
    _var_tuple = Var('tuple', _config_key_value_type)

    add_rule(Rule(
        lhs=_config_dict_nt,
        rhs=Sequence((LitTerminal('{'), Star(_config_key_value_nt), LitTerminal('}'))),
        construct_action=Lambda([_var_config_key_value], return_type=_config_type, body=_var_config_key_value),
        deconstruct_action=Lambda([_var_config], OptionType(_config_type), _some_call(_var_config))
    ))

    add_rule(Rule(
        lhs=_config_key_value_nt,
        rhs=Sequence((_colon_symbol_terminal, _value_nt)),
        construct_action=Lambda(
            [_var_symbol(), _var_value()],
            _config_key_value_type,
            _make_tuple_call([_var_symbol(), _var_value()])
        ),
        deconstruct_action=Lambda(
            [_var_tuple],
            OptionType(_config_key_value_type),
            _some_call(_make_tuple_call([
                _builtin_fst(_var_tuple),
                _builtin_snd(_var_tuple)
            ]))
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
                _builtin_unwrap_option_or(
                    Var('configure', OptionType(MessageType('transactions', 'Configure'))),
                    Call(Builtin('construct_configure'), [ListExpr([], TupleType([BaseType('String'), MessageType('logic', 'Value')]))])
                ),
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
            _builtin_some(_builtin_make_tuple(
                Call(Builtin('deconstruct_configure'), [_builtin_get_field(Var('msg', MessageType('transactions', 'Transaction')), Lit('configure'))]),
                _builtin_get_field(Var('msg', MessageType('transactions', 'Transaction')), Lit('sync')),
                _builtin_get_field(Var('msg', MessageType('transactions', 'Transaction')), Lit('epochs'))
            ))
        )
    ))

    # Bindings rules
    _value_bindings_nt = Nonterminal('value_bindings', ListType(_binding_type))
    _var_keys = Var('keys', ListType(_binding_type))
    _var_values = Var('values', OptionType(ListType(_binding_type)))
    _var_bindings_tuple = Var('tuple', _bindings_type)
    _empty_binding_list = ListExpr([], _binding_type)

    add_rule(Rule(
        lhs=_bindings_nt,
        rhs=Sequence((LitTerminal('['), Star(_binding_nt), Option(_value_bindings_nt), LitTerminal(']'))),
        construct_action=Lambda(
            [_var_keys, _var_values],
            _bindings_type,
            _make_tuple_call([
                _var_keys,
                _builtin_unwrap_option_or(_var_values, _empty_binding_list)
            ])
        ),
        deconstruct_action=Lambda(
            [_var_bindings_tuple],
            OptionType(TupleType([ListType(_binding_type), OptionType(ListType(_binding_type))])),
            _some_call(_make_tuple_call([
                _builtin_fst(_var_bindings_tuple),
                IfElse(
                    _builtin_is_empty(_builtin_snd(_var_bindings_tuple)),
                    Lit(None),
                    _some_call(_builtin_snd(_var_bindings_tuple))
                )
            ]))
        )
    ))

    add_rule(Rule(
        lhs=_value_bindings_nt,
        rhs=Sequence((LitTerminal('|'), Star(_binding_nt))),
        construct_action=Lambda([_var_values], ListType(_binding_type), _var_values),
        deconstruct_action=Lambda([Var('values', ListType(_binding_type))], OptionType(ListType(_binding_type)), _some_call(Var('values', ListType(_binding_type))))
    ))

    _type_var = Var('type', _type_type)
    add_rule(Rule(
        lhs=_binding_nt,
        rhs=Sequence((_symbol_terminal, LitTerminal('::'), _type_nt)),
        construct_action=Lambda(
            [_var_symbol(_string_type), _type_var],
            _binding_type,
            _message_binding(_message_var(_var_symbol(_string_type)), _type_var)
        ),
        deconstruct_action=Lambda(
            [_var_msg(_binding_type)],
            OptionType(TupleType([_string_type, _type_type])),
            _some_call(_make_tuple_call([
                _get_field_call(_get_field_call(_var_msg(_binding_type), Lit('var')), Lit('symbol')),
                _get_field_call(_var_msg(_binding_type), Lit('type'))
            ]))
        )
    ))

    # Abstraction rules
    _abstraction_with_arity_nt = Nonterminal('abstraction_with_arity', _abstraction_with_arity_type)
    _var_bindings = Var('bindings', _bindings_type)
    _var_formula = Var('formula', _formula_type)
    _var_abstraction_tuple = Var('tuple', _abstraction_with_arity_type)

    # Helper to concat bindings
    def _concat_bindings(bindings_var):
        return _builtin_list_concat(
            _builtin_fst(bindings_var),
            _builtin_snd(bindings_var)
        )

    add_rule(Rule(
        lhs=_abstraction_with_arity_nt,
        rhs=Sequence((_lparen, _bindings_nt, _formula_nt, _rparen)),
        construct_action=Lambda(
            params=[_var_bindings, _var_formula],
            return_type=_abstraction_with_arity_type,
            body=_make_tuple_call([
                _message_abstraction(_concat_bindings(_var_bindings), _var_formula),
                _builtin_length(_builtin_snd(_var_bindings))
            ])
        ),
        deconstruct_action=Lambda(
            [_var_abstraction_tuple],
            OptionType(TupleType([_bindings_type, _formula_type])),
            _some_call(_make_tuple_call([
                Call(Builtin('split_bindings'), [
                    _builtin_fst(_var_abstraction_tuple),
                    _builtin_snd(_var_abstraction_tuple)
                ]),
                _get_field_call(_builtin_fst(_var_abstraction_tuple), Lit('formula'))
            ]))
        )
    ))

    add_rule(Rule(
        lhs=_abstraction_nt,
        rhs=Sequence((_lparen, _bindings_nt, _formula_nt, _rparen)),
        construct_action=Lambda(
            params=[_var_bindings, _var_formula],
            return_type=_abstraction_type,
            body=_message_abstraction(_concat_bindings(_var_bindings), _var_formula)
        ),
        deconstruct_action=Lambda(
            [_var_msg(_abstraction_type)],
            OptionType(TupleType([_bindings_type, _formula_type])),
            _some_call(_make_tuple_call([
                Call(Builtin('split_all_bindings'), [_get_field_call(_var_msg(_abstraction_type), Lit('bindings'))]),
                _get_field_call(_var_msg(_abstraction_type), Lit('formula'))
            ]))
        )
    ))

    # Name rule
    add_rule(Rule(
        lhs=_name_nt,
        rhs=_colon_symbol_terminal,
        construct_action=Lambda([_var_symbol(_string_type)], _string_type, _var_symbol(_string_type)),
        deconstruct_action=Lambda([_var_symbol(_string_type)], OptionType(_string_type), _some_call(_var_symbol(_string_type)))
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
    _true_nt = Nonterminal('true', _conjunction_type)
    _false_nt = Nonterminal('false', _disjunction_type)
    _empty_formula_list = ListExpr([], _formula_type)
    _lit_formulas = Lit('formulas')
    _empty_tuple_type = TupleType([])

    add_rule(Rule(
        lhs=_true_nt,
        rhs=Sequence((_lparen, LitTerminal('true'), _rparen)),
        construct_action=Lambda([], _conjunction_type, _message_conjunction(_empty_formula_list)),
        deconstruct_action=Lambda(
            [_var_msg(_conjunction_type)],
            OptionType(_empty_tuple_type),
            IfElse(
                _builtin_is_empty(_get_field_call(_var_msg(_conjunction_type), _lit_formulas)),
                _some_call(_make_tuple_call([])),
                Lit(None)
            )
        )
    ))

    add_rule(Rule(
        lhs=_false_nt,
        rhs=Sequence((_lparen, LitTerminal('false'), _rparen)),
        construct_action=Lambda([], _disjunction_type, _message_disjunction(_empty_formula_list)),
        deconstruct_action=Lambda(
            [_var_msg(_disjunction_type)],
            OptionType(_empty_tuple_type),
            IfElse(
                _builtin_is_empty(_get_field_call(_var_msg(_disjunction_type), _lit_formulas)),
                _some_call(_make_tuple_call([])),
                Lit(None)
            )
        )
    ))

    # Formula rules (not final - auto-generation can add more)
    # True formula: checks for empty Conjunction in the 'conjunction' oneof field
    mark_nonfinal(_formula_nt)
    _lit_conjunction = Lit('conjunction')
    _lit_disjunction = Lit('disjunction')

    add_rule(Rule(
        lhs=_formula_nt,
        rhs=_true_nt,
        construct_action=Lambda(
            [_var_value(_conjunction_type)],
            _formula_type,
            _message_formula(Call(OneOf('true'), [_var_value(_conjunction_type)]))
        ),
        deconstruct_action=Lambda(
            [_var_msg(_formula_type)],
            OptionType(_conjunction_type),
            _formula_oneof_deconstruct(
                _var_msg(_formula_type),
                'conjunction',
                _conjunction_type,
                extra_check=_builtin_is_empty(_get_field_call(_get_field_call(_var_msg(_formula_type), _lit_conjunction), _lit_formulas))
            )
        )
    ))

    # False formula: checks for empty Disjunction in the 'disjunction' oneof field
    add_rule(Rule(
        lhs=_formula_nt,
        rhs=_false_nt,
        construct_action=Lambda(
            [_var_value(_disjunction_type)],
            _formula_type,
            _message_formula(Call(OneOf('false'), [_var_value(_disjunction_type)]))
        ),
        deconstruct_action=Lambda(
            [_var_msg(_formula_type)],
            OptionType(_disjunction_type),
            _formula_oneof_deconstruct(
                _var_msg(_formula_type),
                'disjunction',
                _disjunction_type,
                extra_check=_builtin_is_empty(_get_field_call(_get_field_call(_var_msg(_formula_type), _lit_disjunction), _lit_formulas))
            )
        )
    ))

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
                _builtin_equal(
                    _builtin_which_oneof(Var('msg', MessageType('transactions', 'Export')), Lit('export_type')),
                    Lit('csv_config')
                ),
                _builtin_some(_builtin_get_field(Var('msg', MessageType('transactions', 'Export')), Lit('csv_config'))),
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
            _builtin_some(Var('columns', ListType(MessageType('transactions', 'ExportCSVColumn'))))
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
            _builtin_some(_builtin_make_tuple(
                _builtin_get_field(Var('msg', MessageType('transactions', 'ExportCSVColumn')), Lit('name')),
                _builtin_get_field(Var('msg', MessageType('transactions', 'ExportCSVColumn')), Lit('relation_id'))
            ))
        )
    ))

    # Var rule
    _var_nt = Nonterminal('var', _var_type)
    add_rule(Rule(
        lhs=_var_nt,
        rhs=_symbol_terminal,
        construct_action=Lambda([_var_symbol(_string_type)], _var_type, _message_var(_var_symbol(_string_type))),
        deconstruct_action=Lambda(
            [_var_msg(_var_type)],
            OptionType(_string_type),
            _some_call(_get_field_call(_var_msg(_var_type), Lit('symbol')))
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
            _builtin_some(Var('value', MessageType('logic', 'Value')))
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
                    _builtin_some(_builtin_make_tuple(
                        _builtin_get_field(Var('msg', lhs_type), Lit('precision')),
                        _builtin_get_field(Var('msg', lhs_type), Lit('scale'))
                    ))
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
                    _builtin_some(_builtin_make_tuple())
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

    # Common vars for operators
    _var_left = Var('left', _term_type)
    _var_right = Var('right', _term_type)
    _var_result = Var('result', _term_type)
    _lit_op = Lit('op')
    _lit_arg0 = Lit('arg0')
    _lit_arg1 = Lit('arg1')
    _lit_arg2 = Lit('arg2')
    _lit_term = Lit('term')

    # Helper to wrap term in RelTerm
    def _wrap_relterm(term_var):
        return _message_relterm(Call(OneOf('term'), [term_var]))

    # Helper to extract term from arg
    def _extract_term_from_arg(msg_var, arg_lit):
        return _get_field_call(_get_field_call(msg_var, arg_lit), _lit_term)

    for name, op, prim in _comparison_ops:
        add_rule(Rule(
            lhs=Nonterminal(name, _primitive_type),
            rhs=Sequence((_lparen, LitTerminal(op), _term_nt, _term_nt, _rparen)),
            construct_action=Lambda(
                [_var_left, _var_right],
                _primitive_type,
                _message_primitive(Lit(prim), _wrap_relterm(_var_left), _wrap_relterm(_var_right))
            ),
            deconstruct_action=Lambda(
                [_var_msg(_primitive_type)],
                OptionType(TupleType([_term_type, _term_type])),
                IfElse(
                    _equal_call(_get_field_call(_var_msg(_primitive_type), _lit_op), Lit(prim)),
                    _some_call(_make_tuple_call([
                        _extract_term_from_arg(_var_msg(_primitive_type), _lit_arg0),
                        _extract_term_from_arg(_var_msg(_primitive_type), _lit_arg1)
                    ])),
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
            lhs=Nonterminal(name, _primitive_type),
            rhs=Sequence((_lparen, LitTerminal(op), _term_nt, _term_nt, _term_nt, _rparen)),
            construct_action=Lambda(
                [_var_left, _var_right, _var_result],
                _primitive_type,
                _message_primitive(
                    Lit(prim),
                    _wrap_relterm(_var_left),
                    _wrap_relterm(_var_right),
                    _wrap_relterm(_var_result)
                )
            ),
            deconstruct_action=Lambda(
                [_var_msg(_primitive_type)],
                OptionType(TupleType([_term_type, _term_type, _term_type])),
                IfElse(
                    _equal_call(_get_field_call(_var_msg(_primitive_type), _lit_op), Lit(prim)),
                    _some_call(_make_tuple_call([
                        _extract_term_from_arg(_var_msg(_primitive_type), _lit_arg0),
                        _extract_term_from_arg(_var_msg(_primitive_type), _lit_arg1),
                        _extract_term_from_arg(_var_msg(_primitive_type), _lit_arg2)
                    ])),
                    Lit(None)
                )
            )
        ))

    # Primitive wrapper rules for operators (not final - auto-generation can add more)
    mark_nonfinal(_primitive_nt)
    _var_op = Var('op', _primitive_type)
    for name, _op, prim in _comparison_ops + _arithmetic_ops:
        add_rule(Rule(
            lhs=_primitive_nt,
            rhs=Nonterminal(name, _primitive_type),
            construct_action=Lambda([_var_op], _primitive_type, _var_op),
            deconstruct_action=Lambda(
                [_var_msg(_primitive_type)],
                OptionType(_primitive_type),
                IfElse(
                    _equal_call(_get_field_call(_var_msg(_primitive_type), _lit_op), Lit(prim)),
                    _some_call(_var_msg(_primitive_type)),
                    Lit(None)
                )
            )
        ))

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
            _builtin_some(Var('fragment_id', MessageType('fragments', 'FragmentId')))
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
            _builtin_some(_builtin_make_tuple(
                _builtin_get_field(Var('msg', MessageType('transactions', 'Output')), Lit('name')),
                _builtin_get_field(Var('msg', MessageType('transactions', 'Output')), Lit('relation_id'))
            ))
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
            _builtin_some(_builtin_make_tuple(
                _builtin_get_field(Var('msg', MessageType('transactions', 'Abort')), Lit('name')),
                _builtin_get_field(Var('msg', MessageType('transactions', 'Abort')), Lit('relation_id'))
            ))
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
            _builtin_some(_builtin_make_tuple(
                _builtin_get_field(Var('msg', MessageType('logic', 'FFI')), Lit('name')),
                _builtin_get_field(Var('msg', MessageType('logic', 'FFI')), Lit('args')),
                _builtin_get_field(Var('msg', MessageType('logic', 'FFI')), Lit('terms'))
            ))
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
            _builtin_some(_builtin_make_tuple(
                _builtin_get_field(Var('msg', MessageType('logic', 'Pragma')), Lit('name')),
                _builtin_get_field(Var('msg', MessageType('logic', 'Pragma')), Lit('terms'))
            ))
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
            _builtin_some(_builtin_make_tuple(
                _builtin_get_field(Var('msg', MessageType('logic', 'Atom')), Lit('name')),
                _builtin_get_field(Var('msg', MessageType('logic', 'Atom')), Lit('terms'))
            ))
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
            _builtin_some(_builtin_make_tuple(
                _builtin_get_field(Var('msg', MessageType('logic', 'RelAtom')), Lit('name')),
                _builtin_get_field(Var('msg', MessageType('logic', 'RelAtom')), Lit('terms'))
            ))
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
            _message_primitive(Var('name', BaseType('String')), Var('terms', ListType(MessageType('logic', 'RelTerm'))))
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Primitive'))],
            OptionType(TupleType([BaseType('String'), ListType(MessageType('logic', 'RelTerm'))])),
            _builtin_some(_builtin_make_tuple(
                _builtin_get_field(Var('msg', MessageType('logic', 'Primitive')), Lit('name')),
                _builtin_get_field(Var('msg', MessageType('logic', 'Primitive')), Lit('terms'))
            ))
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
            _builtin_some(_builtin_make_tuple(
                _builtin_get_field(Var('msg', MessageType('logic', 'Attribute')), Lit('name')),
                _builtin_get_field(Var('msg', MessageType('logic', 'Attribute')), Lit('args'))
            ))
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
                _message_abstraction(
                    _builtin_list_concat(
                        _builtin_fst(Var('bindings', _bindings_type)),
                        _builtin_snd(Var('bindings', _bindings_type))
                    ),
                    Var('formula', MessageType('logic', 'Formula'))
                )
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
                _builtin_fst(Var('body_with_arity', _abstraction_with_arity_type)),
                Var('attrs', ListType(MessageType('logic', 'Attribute'))),
                _builtin_snd(Var('body_with_arity', _abstraction_with_arity_type))
            ])
        ),
        deconstruct_action=Lambda(
            [Var('msg', MessageType('logic', 'Upsert'))],
            OptionType(TupleType([
                MessageType('logic', 'RelationId'),
                _abstraction_with_arity_type,
                ListType(MessageType('logic', 'Attribute'))
            ])),
            _builtin_some(_builtin_make_tuple(
                _builtin_get_field(Var('msg', MessageType('logic', 'Upsert')), Lit('name')),
                _builtin_make_tuple(
                    _builtin_get_field(Var('msg', MessageType('logic', 'Upsert')), Lit('body')),
                    _builtin_get_field(Var('msg', MessageType('logic', 'Upsert')), Lit('value_arity'))
                ),
                _builtin_get_field(Var('msg', MessageType('logic', 'Upsert')), Lit('attrs'))
            ))
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
                _builtin_fst(Var('body_with_arity', _abstraction_with_arity_type)),
                Var('attrs', ListType(MessageType('logic', 'Attribute'))),
                _builtin_snd(Var('body_with_arity', _abstraction_with_arity_type))
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
            _builtin_some(_builtin_make_tuple(
                _builtin_get_field(Var('msg', MessageType('logic', 'MonoidDef')), Lit('monoid')),
                _builtin_get_field(Var('msg', MessageType('logic', 'MonoidDef')), Lit('name')),
                _builtin_make_tuple(
                    _builtin_get_field(Var('msg', MessageType('logic', 'MonoidDef')), Lit('body')),
                    _builtin_get_field(Var('msg', MessageType('logic', 'MonoidDef')), Lit('value_arity'))
                ),
                _builtin_get_field(Var('msg', MessageType('logic', 'MonoidDef')), Lit('attrs'))
            ))
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
                _builtin_fst(Var('body_with_arity', _abstraction_with_arity_type)),
                Var('attrs', ListType(MessageType('logic', 'Attribute'))),
                _builtin_snd(Var('body_with_arity', _abstraction_with_arity_type))
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
            _builtin_some(_builtin_make_tuple(
                _builtin_get_field(Var('msg', MessageType('logic', 'MonusDef')), Lit('monoid')),
                _builtin_get_field(Var('msg', MessageType('logic', 'MonusDef')), Lit('name')),
                _builtin_make_tuple(
                    _builtin_get_field(Var('msg', MessageType('logic', 'MonusDef')), Lit('body')),
                    _builtin_get_field(Var('msg', MessageType('logic', 'MonusDef')), Lit('value_arity'))
                ),
                _builtin_get_field(Var('msg', MessageType('logic', 'MonusDef')), Lit('attrs'))
            ))
        )
    ))

    # Mark all the non-final rules as non-final
    for lhs in nonfinal_nonterminals:
        rules, _ = result[lhs]
        result[lhs] = (rules, False)

    return result
