"""Builtin grammar rules that are manually specified.

These rules define the grammar for constructs that cannot be auto-generated
from protobuf definitions, such as value literals, date/datetime parsing,
configuration syntax, bindings, abstractions, type literals, and operators.
"""

from types import NoneType
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field

from .grammar import Rule, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence
from .target import (
    Lambda, Call, Var, Symbol, Lit, Seq, IfElse, Builtin, Message, OneOf, ListExpr,
    OptionType, ListType, TupleType, MessageType, FunctionType
)
from .target_utils import (
    STRING_TYPE, INT64_TYPE, FLOAT64_TYPE, BOOLEAN_TYPE,
    create_identity_function, create_identity_option_function,
    make_equal, make_which_oneof, make_get_field, make_some, make_tuple,
    make_fst, make_snd, make_is_empty, make_concat, make_length, make_unwrap_option_or
)

# Common types used throughout
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
_ffi_type = MessageType('logic', 'FFI')
_rel_atom_type = MessageType('logic', 'RelAtom')
_exists_type = MessageType('logic', 'Exists')

_config_key_value_type = TupleType([STRING_TYPE, _value_type])
_config_type = ListType(_config_key_value_type)
_bindings_type = TupleType([ListType(_binding_type), ListType(_binding_type)])
_abstraction_with_arity_type = TupleType([_abstraction_type, INT64_TYPE])
_monoid_op_type = FunctionType([_type_type], _monoid_type)


# Common nonterminals
_value_nt = Nonterminal('value', _value_type)
_binding_nt = Nonterminal('binding', _binding_type)
_bindings_nt = Nonterminal('bindings', _bindings_type)
_formula_nt = Nonterminal('formula', _formula_type)
_term_nt = Nonterminal('term', _term_type)
_relterm_nt = Nonterminal('rel_term', _relterm_type)
_abstraction_nt = Nonterminal('abstraction', _abstraction_type)
_primitive_nt = Nonterminal('primitive', _primitive_type)
_relation_id_nt = Nonterminal('relation_id', _relation_id_type)
_type_nt = Nonterminal('type', _type_type)
_monoid_nt = Nonterminal('monoid', _monoid_type)
_declaration_nt = Nonterminal('declaration', _declaration_type)
_name_nt = Nonterminal('name', STRING_TYPE)
_config_dict_nt = Nonterminal('config_dict', _config_type)
_date_nt = Nonterminal('date', _date_value_type)
_datetime_nt = Nonterminal('datetime', _datetime_value_type)
_var_nt = Nonterminal('var', _var_type)
_boolean_value_nt = Nonterminal('boolean_value', BOOLEAN_TYPE)
_config_key_value_nt = Nonterminal('config_key_value', _config_key_value_type)
_value_bindings_nt = Nonterminal('value_bindings', ListType(_binding_type))
_abstraction_with_arity_nt = Nonterminal('abstraction_with_arity', _abstraction_with_arity_type)
_true_nt = Nonterminal('true', _conjunction_type)
_false_nt = Nonterminal('false', _disjunction_type)
_transaction_nt = Nonterminal('transaction', _transaction_type)
_configure_nt = Nonterminal('configure', _configure_type)
_sync_nt = Nonterminal('sync', _sync_type)
_epoch_nt = Nonterminal('epoch', _epoch_type)
_export_nt = Nonterminal('export', _export_type)
_export_csv_config_nt = Nonterminal('export_csv_config', _export_csv_config_type)
_export_csv_path_nt = Nonterminal('export_csv_path', STRING_TYPE)
_export_csv_columns_nt = Nonterminal('export_csv_columns', ListType(_export_csv_column_type))
_export_csv_column_nt = Nonterminal('export_csv_column', _export_csv_column_type)
_output_nt = Nonterminal('output', _output_type)
_abort_nt = Nonterminal('abort', _abort_type)
_ffi_nt = Nonterminal('ffi', _ffi_type)
_rel_atom_nt = Nonterminal('rel_atom', _rel_atom_type)
_exists_nt = Nonterminal('exists', _exists_type)
_monoid_op_nt = Nonterminal('monoid_op', _monoid_op_type)
_fragment_id_nt = Nonterminal('fragment_id', _fragment_id_type)
_new_fragment_id_nt = Nonterminal('new_fragment_id', _fragment_id_type)
_fragment_nt = Nonterminal('fragment', _fragment_type)
_specialized_value_nt = Nonterminal('specialized_value', _value_type)

# Common terminals
_string_terminal = NamedTerminal('STRING', STRING_TYPE)
_int_terminal = NamedTerminal('INT', INT64_TYPE)
_float_terminal = NamedTerminal('FLOAT', FLOAT64_TYPE)
_symbol_terminal = NamedTerminal('SYMBOL', STRING_TYPE)
_colon_symbol_terminal = NamedTerminal('COLON_SYMBOL', STRING_TYPE)
_uint128_terminal = NamedTerminal('UINT128', _uint128_value_type)
_int128_terminal = NamedTerminal('INT128', _int128_value_type)
_decimal_terminal = NamedTerminal('DECIMAL', _decimal_value_type)

_lp = LitTerminal('(')
_rp = LitTerminal(')')
_lc = LitTerminal('{')
_rc = LitTerminal('}')


@dataclass
class BuiltinRules:
    forced: bool = False
    result: Dict[Nonterminal, Tuple[List[Rule], bool]] = field(default_factory=dict)
    nonfinal_nonterminals: Set[Nonterminal] = field(default_factory=set)

    def get_builtin_rules(self) -> Dict[Nonterminal, Tuple[List[Rule], bool]]:
        """Return dict mapping nonterminals to (rules, is_final).

        is_final=True means auto-generation should not add more rules for this nonterminal.
        """

        if not self.forced:
            self._add_rules()
        return self.result

    def add_rule(self, rule: Rule) -> None:
        lhs = rule.lhs
        if lhs not in self.result:
            self.result[lhs] = ([], True)
        rules_list, existing_final = self.result[lhs]
        rules_list.append(rule)
        self.result[lhs] = (rules_list, existing_final)

    def mark_nonfinal(self, lhs: Nonterminal) -> None:
        self.nonfinal_nonterminals.add(lhs)

    # Common Message constructor functions that return Call instances
    @staticmethod
    def _message_value(*args):
        return Call(Message('logic', 'Value'), list(args))

    @staticmethod
    def _message_binding(*args):
        return Call(Message('logic', 'Binding'), list(args))

    @staticmethod
    def _message_var(*args):
        return Call(Message('logic', 'Var'), list(args))

    @staticmethod
    def _message_abstraction(*args):
        return Call(Message('logic', 'Abstraction'), list(args))

    @staticmethod
    def _message_primitive(*args):
        return Call(Message('logic', 'Primitive'), list(args))

    @staticmethod
    def _message_relterm(*args):
        return Call(Message('logic', 'RelTerm'), list(args))

    @staticmethod
    def _message_date_value(*args):
        return Call(Message('logic', 'DateValue'), list(args))

    @staticmethod
    def _message_datetime_value(*args):
        return Call(Message('logic', 'DateTimeValue'), list(args))

    @staticmethod
    def _message_conjunction(*args):
        return Call(Message('logic', 'Conjunction'), list(args))

    @staticmethod
    def _message_disjunction(*args):
        return Call(Message('logic', 'Disjunction'), list(args))

    @staticmethod
    def _message_formula(*args):
        return Call(Message('logic', 'Formula'), list(args))



    @staticmethod
    def _value_oneof_deconstruct(msg_var, oneof_field_name, result_type):
        """Create standard Value oneof deconstruct pattern."""
        return IfElse(
            make_equal(
                make_which_oneof(msg_var, Lit('value_type')),
                Lit(oneof_field_name)
            ),
            make_some(make_get_field(msg_var, Lit(oneof_field_name))),
            Lit(None)
        )

    @staticmethod
    def _formula_oneof_deconstruct(msg_var, oneof_field_name, result_type, extra_check):
        """Create standard Formula oneof deconstruct pattern."""
        base_check = make_equal(
            make_which_oneof(msg_var, Lit('formula_type')),
            Lit(oneof_field_name)
        )
        return IfElse(
            base_check,
            IfElse(extra_check, make_some(make_get_field(msg_var, Lit(oneof_field_name))), Lit(None)),
            Lit(None)
        )

    # Helper function to generate Value oneof rules
    @staticmethod
    def _make_value_oneof_rule(rhs, value_type, oneof_field_name):
        """Create a rule for Value -> oneof field."""
        var_value = Var('value', value_type)
        msg_var = Var('msg', _value_type)
        return Rule(
            lhs=_value_nt,
            rhs=rhs,
            construct_action=Lambda(
                [var_value],
                _value_type,
                BuiltinRules._message_value(Call(OneOf(oneof_field_name), [var_value]))
            ),
            deconstruct_action=Lambda(
                [msg_var],
                OptionType(value_type),
                BuiltinRules._value_oneof_deconstruct(msg_var, oneof_field_name, value_type)
            )
        )

    def _add_rules(self) -> None:
        # Value literal rules
        self.add_rule(self._make_value_oneof_rule(_date_nt, _date_value_type, 'date_value'))
        self.add_rule(self._make_value_oneof_rule(_datetime_nt, _datetime_value_type, 'datetime_value'))
        self.add_rule(self._make_value_oneof_rule(_string_terminal, STRING_TYPE, 'string_value'))
        self.add_rule(self._make_value_oneof_rule(_int_terminal, INT64_TYPE, 'int_value'))
        self.add_rule(self._make_value_oneof_rule(_float_terminal, FLOAT64_TYPE, 'float_value'))
        self.add_rule(self._make_value_oneof_rule(_uint128_terminal, _uint128_value_type, 'uint128_value'))
        self.add_rule(self._make_value_oneof_rule(_int128_terminal, _int128_value_type, 'int128_value'))
        self.add_rule(self._make_value_oneof_rule(_decimal_terminal, _decimal_value_type, 'decimal_value'))

        # Special case: missing value
        self.add_rule(Rule(
            lhs=_value_nt,
            rhs=LitTerminal('missing'),
            construct_action=Lambda(
                [],
                _value_type,
                self._message_value(Call(OneOf('missing_value'), [Call(Message('logic', 'MissingValue'), [])]))
            ),
            deconstruct_action=Lambda(
                [Var('msg', _value_type)],
                OptionType(TupleType([])),
                IfElse(
                    make_equal(make_which_oneof(Var('msg', _value_type), Lit('value_type')), Lit('missing_value')),
                    make_some(make_tuple()),
                    Lit(None)
                )
            )
        ))

        # Bool value rules
        _var_bool_value = Var('value', BOOLEAN_TYPE)

        self.add_rule(Rule(
            lhs=_boolean_value_nt,
            rhs=LitTerminal('true'),
            construct_action=Lambda([], BOOLEAN_TYPE, Lit(True)),
            deconstruct_action=Lambda(
                [_var_bool_value],
                OptionType(TupleType([])),
                IfElse(make_equal(_var_bool_value, Lit(True)), make_some(make_tuple()), Lit(None))
            )
        ))

        self.add_rule(Rule(
            lhs=_boolean_value_nt,
            rhs=LitTerminal('false'),
            construct_action=Lambda([], BOOLEAN_TYPE, Lit(False)),
            deconstruct_action=Lambda(
                [_var_bool_value],
                OptionType(TupleType([])),
                IfElse(make_equal(_var_bool_value, Lit(False)), make_some(make_tuple()), Lit(None))
            )
        ))

        self.add_rule(self._make_value_oneof_rule(_boolean_value_nt, BOOLEAN_TYPE, 'boolean_value'))

        # Date and datetime rules
        _var_year = Var('year', INT64_TYPE)
        _var_month = Var('month', INT64_TYPE)
        _var_day = Var('day', INT64_TYPE)
        _var_hour = Var('hour', INT64_TYPE)
        _var_minute = Var('minute', INT64_TYPE)
        _var_second = Var('second', INT64_TYPE)
        _var_microsecond = Var('microsecond', OptionType(INT64_TYPE))

        self.add_rule(Rule(
            lhs=_date_nt,
            rhs=Sequence((_lp, LitTerminal('date'), _int_terminal, _int_terminal, _int_terminal, _rp)),
            construct_action=Lambda(
                [_var_year, _var_month, _var_day],
                _date_value_type,
                self._message_date_value(_var_year, _var_month, _var_day)
            ),
            deconstruct_action=Lambda(
                [Var('msg', _date_value_type)],
                OptionType(TupleType([INT64_TYPE, INT64_TYPE, INT64_TYPE])),
                make_some(make_tuple(
                    make_get_field(Var('msg', _date_value_type), Lit('year')),
                    make_get_field(Var('msg', _date_value_type), Lit('month')),
                    make_get_field(Var('msg', _date_value_type), Lit('day'))
                ))
            )
        ))

        _datetime_tuple_type = TupleType([INT64_TYPE, INT64_TYPE, INT64_TYPE, INT64_TYPE, INT64_TYPE, INT64_TYPE, OptionType(INT64_TYPE)])

        self.add_rule(Rule(
            lhs=_datetime_nt,
            rhs=Sequence((
                _lp, LitTerminal('datetime'),
                _int_terminal, _int_terminal, _int_terminal,
                _int_terminal, _int_terminal, _int_terminal,
                Option(_int_terminal),
                _rp
            )),
            construct_action=Lambda(
                [_var_year, _var_month, _var_day, _var_hour, _var_minute, _var_second, _var_microsecond],
                _datetime_value_type,
                self._message_datetime_value(
                    _var_year, _var_month, _var_day, _var_hour, _var_minute, _var_second,
                    make_unwrap_option_or(_var_microsecond, Lit(0))
                )
            ),
            deconstruct_action=Lambda(
                [Var('msg', _datetime_value_type)],
                OptionType(_datetime_tuple_type),
                make_some(make_tuple(
                    make_get_field(Var('msg', _datetime_value_type), Lit('year')),
                    make_get_field(Var('msg', _datetime_value_type), Lit('month')),
                    make_get_field(Var('msg', _datetime_value_type), Lit('day')),
                    make_get_field(Var('msg', _datetime_value_type), Lit('hour')),
                    make_get_field(Var('msg', _datetime_value_type), Lit('minute')),
                    make_get_field(Var('msg', _datetime_value_type), Lit('second')),
                    IfElse(
                        make_equal(make_get_field(Var('msg', _datetime_value_type), Lit('microsecond')), Lit(0)),
                        Lit(None),
                        make_some(make_get_field(Var('msg', _datetime_value_type), Lit('microsecond')))
                    )
                ))
            )
        ))

        # Configuration rules
        _var_tuple = Var('tuple', _config_key_value_type)

        self.add_rule(Rule(
            lhs=_config_dict_nt,
            rhs=Sequence((_lc, Star(_config_key_value_nt), _rc)),
            construct_action=create_identity_function(_config_type),
            deconstruct_action=create_identity_option_function(_config_type)
        ))

        self.add_rule(Rule(
            lhs=_config_key_value_nt,
            rhs=Sequence((_colon_symbol_terminal, _value_nt)),
            construct_action=Lambda(
                [Var('symbol', STRING_TYPE), Var('value', _value_type)],
                _config_key_value_type,
                make_tuple(Var('symbol', STRING_TYPE), Var('value', _value_type))
            ),
            deconstruct_action=Lambda(
                [_var_tuple],
                OptionType(_config_key_value_type),
                make_some(make_tuple(
                    make_fst(_var_tuple),
                    make_snd(_var_tuple)
                ))
            )
        ))

        # Transaction rule
        self.add_rule(Rule(
            lhs=_transaction_nt,
            rhs=Sequence((
                _lp, LitTerminal('transaction'),
                Option(_configure_nt),
                Option(_sync_nt),
                Star(_epoch_nt),
                _rp
            )),
            construct_action=Lambda(
                [
                    Var('configure', OptionType(_configure_type)),
                    Var('sync', OptionType(_sync_type)),
                    Var('epochs', ListType(_epoch_type))
                ],
                _transaction_type,
                Call(Message('transactions', 'Transaction'), [
                    Var('epochs', ListType(_epoch_type)),
                    make_unwrap_option_or(
                        Var('configure', OptionType(_configure_type)),
                        Call(Builtin('construct_configure'), [ListExpr([], TupleType([STRING_TYPE, _value_type]))])
                    ),
                    Var('sync', OptionType(_sync_type))
                ])
            ),
            deconstruct_action=Lambda(
                [Var('msg', _transaction_type)],
                OptionType(TupleType([
                    OptionType(_configure_type),
                    OptionType(_sync_type),
                    ListType(_epoch_type)
                ])),
                make_some(make_tuple(
                    Call(Builtin('deconstruct_configure'), [make_get_field(Var('msg', _transaction_type), Lit('configure'))]),
                    make_get_field(Var('msg', _transaction_type), Lit('sync')),
                    make_get_field(Var('msg', _transaction_type), Lit('epochs'))
                ))
            )
        ))

        # Bindings rules
        _var_keys = Var('keys', ListType(_binding_type))
        _var_values = Var('values', OptionType(ListType(_binding_type)))
        _var_bindings_tuple = Var('tuple', _bindings_type)
        _empty_binding_list = ListExpr([], _binding_type)

        self.add_rule(Rule(
            lhs=_bindings_nt,
            rhs=Sequence((LitTerminal('['), Star(_binding_nt), Option(_value_bindings_nt), LitTerminal(']'))),
            construct_action=Lambda(
                [_var_keys, _var_values],
                _bindings_type,
                make_tuple(
                    _var_keys,
                    make_unwrap_option_or(_var_values, _empty_binding_list)
                )
            ),
            deconstruct_action=Lambda(
                [_var_bindings_tuple],
                OptionType(TupleType([ListType(_binding_type), OptionType(ListType(_binding_type))])),
                make_some(make_tuple(
                    make_fst(_var_bindings_tuple),
                    IfElse(
                        make_is_empty(make_snd(_var_bindings_tuple)),
                        Lit(None),
                        make_some(make_snd(_var_bindings_tuple))
                    )
                ))
            )
        ))

        self.add_rule(Rule(
            lhs=_value_bindings_nt,
            rhs=Sequence((LitTerminal('|'), Star(_binding_nt))),
            construct_action=create_identity_function(ListType(_binding_type)),
            deconstruct_action=create_identity_option_function(ListType(_binding_type))
        ))

        _type_var = Var('type', _type_type)
        self.add_rule(Rule(
            lhs=_binding_nt,
            rhs=Sequence((_symbol_terminal, LitTerminal('::'), _type_nt)),
            construct_action=Lambda(
                [Var('symbol', STRING_TYPE), _type_var],
                _binding_type,
                self._message_binding(self._message_var(Var('symbol', STRING_TYPE)), _type_var)
            ),
            deconstruct_action=Lambda(
                [Var('msg', _binding_type)],
                OptionType(TupleType([STRING_TYPE, _type_type])),
                make_some(make_tuple(
                    make_get_field(make_get_field(Var('msg', _binding_type), Lit('var')), Lit('symbol')),
                    make_get_field(Var('msg', _binding_type), Lit('type'))
                ))
            )
        ))

        # Abstraction rules
        _var_bindings = Var('bindings', _bindings_type)
        _var_formula = Var('formula', _formula_type)
        _var_abstraction_tuple = Var('tuple', _abstraction_with_arity_type)

        # Helper to concat bindings
        def _concat_bindings(bindings_var):
            return make_concat(
                make_fst(bindings_var),
                make_snd(bindings_var)
            )

        self.add_rule(Rule(
            lhs=_abstraction_with_arity_nt,
            rhs=Sequence((_lp, _bindings_nt, _formula_nt, _rp)),
            construct_action=Lambda(
                params=[_var_bindings, _var_formula],
                return_type=_abstraction_with_arity_type,
                body=make_tuple(
                    self._message_abstraction(_concat_bindings(_var_bindings), _var_formula),
                    make_length(make_snd(_var_bindings))
                )
            ),
            deconstruct_action=Lambda(
                [_var_abstraction_tuple],
                OptionType(TupleType([_bindings_type, _formula_type])),
                make_some(make_tuple(
                    Call(Builtin('split_bindings'), [
                        make_fst(_var_abstraction_tuple),
                        make_snd(_var_abstraction_tuple)
                    ]),
                    make_get_field(make_fst(_var_abstraction_tuple), Lit('formula'))
                ))
            )
        ))

        self.add_rule(Rule(
            lhs=_abstraction_nt,
            rhs=Sequence((_lp, _bindings_nt, _formula_nt, _rp)),
            construct_action=Lambda(
                params=[_var_bindings, _var_formula],
                return_type=_abstraction_type,
                body=self._message_abstraction(_concat_bindings(_var_bindings), _var_formula)
            ),
            deconstruct_action=Lambda(
                [Var('msg', _abstraction_type)],
                OptionType(TupleType([_bindings_type, _formula_type])),
                make_some(make_tuple(
                    Call(Builtin('split_all_bindings'), [make_get_field(Var('msg', _abstraction_type), Lit('bindings'))]),
                    make_get_field(Var('msg', _abstraction_type), Lit('formula'))
                ))
            )
        ))

        # Name rule
        self.add_rule(Rule(
            lhs=_name_nt,
            rhs=_colon_symbol_terminal,
            construct_action=create_identity_function(STRING_TYPE),
            deconstruct_action=create_identity_option_function(STRING_TYPE)
        ))

        # Monoid rules
        self.add_rule(Rule(
            lhs=_monoid_nt,
            rhs=Sequence((
                _type_nt,
                LitTerminal('::'),
                _monoid_op_nt
            )),
            construct_action=Lambda(
                [Var('type', _type_type), Var('op', _monoid_op_type)],
                return_type=_monoid_type,
                body=Call(Var('op', _monoid_op_type), [Var('type', _type_type)])
            ),
            deconstruct_action=Lambda(
                [Var('msg', _monoid_type)],
                OptionType(TupleType([_type_type, _monoid_op_type])),
                Call(Builtin('deconstruct_monoid'), [Var('msg', _monoid_type)])
            )
        ))

        body = Call(Message('logic', 'Monoid'), [
            Call(OneOf('or_monoid'), [
                Call(Message('logic', 'OrMonoid'), [])
            ])
        ])

        self.add_rule(Rule(
            lhs=_monoid_nt,
            rhs=Sequence((
                LitTerminal('BOOL'),
                LitTerminal('::'),
                LitTerminal('OR')
            )),
            construct_action = Lambda(
                [],
                return_type=_monoid_type,
                body=Lambda([], return_type=_monoid_type, body=body)
            ),
            deconstruct_action=Lambda(
                [Var('msg', _monoid_type)],
                OptionType(TupleType([])),
                IfElse(
                    make_equal(make_which_oneof('monoid_type'), Lit('or_monoid')),
                    make_some(make_tuple()),
                    Lit(None)
                )
            )
        ))

        def _make_monoid_op_rule(constructor: str) -> Rule:
            op = constructor.removesuffix('Monoid')
            symbol = f'{op.lower()}_monoid'
            lit = op.upper()
            body = Call(Message('logic', 'Monoid'), [
                Call(OneOf(symbol), [
                    Call(Message('logic', constructor), [Var('type', _type_type)])
                ])
            ])
            rhs = LitTerminal(lit)
            construct_action = Lambda(
                [],
                return_type=_monoid_op_type,
                body=Lambda([Var('type', _type_type)], return_type=_monoid_type, body=body)
            )
            from .grammar import generate_deconstruct_action
            deconstruct_action = generate_deconstruct_action(construct_action, rhs)
            return Rule(
                lhs=_monoid_op_nt,
                rhs=rhs,
                construct_action=construct_action,
                deconstruct_action=deconstruct_action
            )

        self.add_rule(_make_monoid_op_rule('MinMonoid'))
        self.add_rule(_make_monoid_op_rule('MaxMonoid'))
        self.add_rule(_make_monoid_op_rule('SumMonoid'))

        # Configure rule
        self.add_rule(Rule(
            lhs=_configure_nt,
            rhs=Sequence((
                _lp, LitTerminal('configure'),
                _config_dict_nt,
                _rp
            )),
            construct_action=Lambda(
                [Var('config_dict', _config_type)],
                return_type=_configure_type,
                body=Call(Builtin('construct_configure'), [Var('config_dict', _config_type)])
            ),
            deconstruct_action=Lambda(
                [Var('msg', _configure_type)],
                OptionType(_config_type),
                Call(Builtin('deconstruct_configure_to_dict'), [Var('msg', _configure_type)])
            )
        ))

        # True/false formula rules
        _empty_formula_list = ListExpr([], _formula_type)
        _lit_formulas = Lit('formulas')
        _empty_tuple_type = TupleType([])

        self.add_rule(Rule(
            lhs=_true_nt,
            rhs=Sequence((_lp, LitTerminal('true'), _rp)),
            construct_action=Lambda([], _conjunction_type, self._message_conjunction(_empty_formula_list)),
            deconstruct_action=Lambda(
                [Var('msg', _conjunction_type)],
                OptionType(_empty_tuple_type),
                IfElse(
                    make_is_empty(make_get_field(Var('msg', _conjunction_type), _lit_formulas)),
                    make_some(make_tuple()),
                    Lit(None)
                )
            )
        ))

        self.add_rule(Rule(
            lhs=_false_nt,
            rhs=Sequence((_lp, LitTerminal('false'), _rp)),
            construct_action=Lambda([], _disjunction_type, self._message_disjunction(_empty_formula_list)),
            deconstruct_action=Lambda(
                [Var('msg', _disjunction_type)],
                OptionType(_empty_tuple_type),
                IfElse(
                    make_is_empty(make_get_field(Var('msg', _disjunction_type), _lit_formulas)),
                    make_some(make_tuple()),
                    Lit(None)
                )
            )
        ))

        # Formula rules (not final - auto-generation can add more)
        # True formula: checks for empty Conjunction in the 'conjunction' oneof field
        self.mark_nonfinal(_formula_nt)

        self.add_rule(Rule(
            lhs=_formula_nt,
            rhs=_true_nt,
            construct_action=Lambda(
                [Var('value', _conjunction_type)],
                _formula_type,
                self._message_formula(Call(OneOf('conjunction'), [Var('value', _conjunction_type)]))
            ),
            deconstruct_action=Lambda(
                [Var('msg', _formula_type)],
                OptionType(_conjunction_type),
                self._formula_oneof_deconstruct(
                    Var('msg', _formula_type),
                    'conjunction',
                    _conjunction_type,
                    extra_check=make_is_empty(make_get_field(make_get_field(Var('msg', _formula_type), Lit('conjunction')), _lit_formulas))
                )
            )
        ))

        # False formula: checks for empty Disjunction in the 'disjunction' oneof field
        self.add_rule(Rule(
            lhs=_formula_nt,
            rhs=_false_nt,
            construct_action=Lambda(
                [Var('value', _disjunction_type)],
                _formula_type,
                self._message_formula(Call(OneOf('disjunction'), [Var('value', _disjunction_type)]))
            ),
            deconstruct_action=Lambda(
                [Var('msg', _formula_type)],
                OptionType(_disjunction_type),
                self._formula_oneof_deconstruct(
                    Var('msg', _formula_type),
                    'disjunction',
                    _disjunction_type,
                    extra_check=make_is_empty(make_get_field(make_get_field(Var('msg', _formula_type), Lit('disjunction')), _lit_formulas))
                )
            )
        ))

        # Export rules
        self.add_rule(Rule(
            lhs=_export_nt,
            rhs=Sequence((
                _lp, LitTerminal('export'),
                _export_csv_config_nt,
                _rp
            )),
            construct_action=Lambda(
                [Var('config', _export_csv_config_type)],
                _export_type,
                Call(Message('transactions', 'Export'), [Call(OneOf('csv_config'), [Var('config', _export_csv_config_type)])])
            ),
            deconstruct_action=Lambda(
                [Var('msg', _export_type)],
                OptionType(_export_csv_config_type),
                IfElse(
                    make_equal(
                        make_which_oneof(Var('msg', _export_type), Lit('export_type')),
                        Lit('csv_config')
                    ),
                    make_some(make_get_field(Var('msg', _export_type), Lit('csv_config'))),
                    Lit(None)
                )
            )
        ))

        # Export CSV path rule
        self.add_rule(Rule(
            lhs=_export_csv_path_nt,
            rhs=Sequence((
                _lp, LitTerminal('path'), NamedTerminal('STRING', STRING_TYPE), _rp
            )),
            construct_action=create_identity_function(STRING_TYPE),
            deconstruct_action=create_identity_option_function(STRING_TYPE)
        ))

        self.add_rule(Rule(
            lhs=_export_csv_config_nt,
            rhs=Sequence((
                _lp, LitTerminal('export_csv_config'),
                _export_csv_path_nt,
                _export_csv_columns_nt,
                _config_dict_nt,
                _rp
            )),
            construct_action=Lambda(
                [
                    Var('path', STRING_TYPE),
                    Var('columns', ListType(_export_csv_column_type)),
                    Var('config', _config_type)
                ],
                _export_csv_config_type,
                Call(Builtin('export_csv_config'), [
                    Var('path', STRING_TYPE),
                    Var('columns', ListType(_export_csv_column_type)),
                    Var('config', _config_type)
                ])
            ),
            deconstruct_action=Lambda(
                [Var('msg', _export_csv_config_type)],
                OptionType(TupleType([
                    STRING_TYPE,
                    ListType(_export_csv_column_type),
                    _config_type
                ])),
                Call(Builtin('deconstruct_export_csv_config'), [Var('msg', _export_csv_config_type)])
            )
        ))

        self.add_rule(Rule(
            lhs=_export_csv_columns_nt,
            rhs=Sequence((
                _lp, LitTerminal('columns'),
                Star(_export_csv_column_nt),
                _rp
            )),
            construct_action=create_identity_function(ListType(_export_csv_column_type)),
            deconstruct_action=create_identity_option_function(ListType(_export_csv_column_type))
        ))

        self.add_rule(Rule(
            lhs=_export_csv_column_nt,
            rhs=Sequence((
                _lp, LitTerminal('column'),
                NamedTerminal('STRING', STRING_TYPE),
                _relation_id_nt,
                _rp
            )),
            construct_action=Lambda(
                [Var('name', STRING_TYPE), Var('relation_id', _relation_id_type)],
                _export_csv_column_type,
                Call(Message('transactions', 'ExportCSVColumn'), [
                    Var('name', STRING_TYPE),
                    Var('relation_id', _relation_id_type)
                ])
            ),
            deconstruct_action=Lambda(
                [Var('msg', _export_csv_column_type)],
                OptionType(TupleType([STRING_TYPE, _relation_id_type])),
                make_some(make_tuple(
                    make_get_field(Var('msg', _export_csv_column_type), Lit('name')),
                    make_get_field(Var('msg', _export_csv_column_type), Lit('relation_id'))
                ))
            )
        ))

        # Var rule
        self.add_rule(Rule(
            lhs=_var_nt,
            rhs=_symbol_terminal,
            construct_action=Lambda([Var('symbol', STRING_TYPE)], _var_type, self._message_var(Var('symbol', STRING_TYPE))),
            deconstruct_action=Lambda(
                [Var('msg', _var_type)],
                OptionType(STRING_TYPE),
                make_some(make_get_field(Var('msg', _var_type), Lit('symbol')))
            )
        ))

        # ID rules
        self.add_rule(Rule(
            lhs=_fragment_id_nt,
            rhs=NamedTerminal('COLON_SYMBOL', STRING_TYPE),
            construct_action=Lambda(
                [Var('symbol', STRING_TYPE)],
                return_type=_fragment_id_type,
                body=Call(Builtin('fragment_id_from_string'), [Var('symbol', STRING_TYPE)])
            ),
            deconstruct_action=Lambda(
                [Var('msg', _fragment_id_type)],
                OptionType(STRING_TYPE),
                Call(Builtin('fragment_id_to_string'), [Var('msg', _fragment_id_type)])
            )
        ))

        self.add_rule(Rule(
            lhs=_relation_id_nt,
            rhs=NamedTerminal('COLON_SYMBOL', STRING_TYPE),
            construct_action=Lambda(
                [Var('symbol', STRING_TYPE)],
                return_type=_relation_id_type,
                body=Call(Builtin('relation_id_from_string'), [Var('symbol', STRING_TYPE)])
            ),
            deconstruct_action=Lambda(
                [Var('msg', _relation_id_type)],
                OptionType(STRING_TYPE),
                Call(Builtin('relation_id_to_string'), [Var('msg', _relation_id_type)])
            )
        ))

        self.add_rule(Rule(
            lhs=_relation_id_nt,
            rhs=NamedTerminal('INT', INT64_TYPE),
            construct_action=Lambda(
                [Var('INT', INT64_TYPE)],
                return_type=_relation_id_type,
                body=Call(Builtin('relation_id_from_int'), [Var('INT', INT64_TYPE)])
            ),
            deconstruct_action=Lambda(
                [Var('msg', _relation_id_type)],
                OptionType(INT64_TYPE),
                Call(Builtin('relation_id_to_int'), [Var('msg', _relation_id_type)])
            )
        ))

        # Specialized value rule
        self.add_rule(Rule(
            lhs=_specialized_value_nt,
            rhs=Sequence((LitTerminal('#'), _value_nt)),
            construct_action=Lambda(
                [Var('value', _value_type)],
                _value_type,
                Var('value', _value_type)
            ),
            deconstruct_action=Lambda(
                [Var('value', _value_type)],
                OptionType(_value_type),
                make_some(Var('value', _value_type))
            )
        ))

        # Type rules
        _unspecified_type_type = MessageType('logic', 'UnspecifiedType')
        STRING_TYPE_type = MessageType('logic', 'StringType')
        _int_type_type = MessageType('logic', 'IntType')
        _float_type_type = MessageType('logic', 'FloatType')
        _uint128_type_type = MessageType('logic', 'UInt128Type')
        _int128_type_type = MessageType('logic', 'Int128Type')
        _boolean_type_type = MessageType('logic', 'BooleanType')
        _date_type_type = MessageType('logic', 'DateType')
        _datetime_type_type = MessageType('logic', 'DateTimeType')
        _missing_type_type = MessageType('logic', 'MissingType')
        _decimal_type_type = MessageType('logic', 'DecimalType')

        _type_rules = [
            ('unspecified_type', _unspecified_type_type, LitTerminal('UNKNOWN'),
             Lambda([], _unspecified_type_type, Call(Message('logic', 'UnspecifiedType'), []))),
            ('string_type', STRING_TYPE_type, LitTerminal('STRING'),
             Lambda([], STRING_TYPE_type, Call(Message('logic', 'StringType'), []))),
            ('int_type', _int_type_type, LitTerminal('INT'),
             Lambda([], _int_type_type, Call(Message('logic', 'IntType'), []))),
            ('float_type', _float_type_type, LitTerminal('FLOAT'),
             Lambda([], _float_type_type, Call(Message('logic', 'FloatType'), []))),
            ('uint128_type', _uint128_type_type, LitTerminal('UINT128'),
             Lambda([], _uint128_type_type, Call(Message('logic', 'UInt128Type'), []))),
            ('int128_type', _int128_type_type, LitTerminal('INT128'),
             Lambda([], _int128_type_type, Call(Message('logic', 'Int128Type'), []))),
            ('boolean_type', _boolean_type_type, LitTerminal('BOOLEAN'),
             Lambda([], _boolean_type_type, Call(Message('logic', 'BooleanType'), []))),
            ('date_type', _date_type_type, LitTerminal('DATE'),
             Lambda([], _date_type_type, Call(Message('logic', 'DateType'), []))),
            ('datetime_type', _datetime_type_type, LitTerminal('DATETIME'),
             Lambda([], _datetime_type_type, Call(Message('logic', 'DateTimeType'), []))),
            ('missing_type', _missing_type_type, LitTerminal('MISSING'),
             Lambda([], _missing_type_type, Call(Message('logic', 'MissingType'), []))),
            ('decimal_type', _decimal_type_type,
             Sequence((_lp, LitTerminal('DECIMAL'), NamedTerminal('INT', INT64_TYPE), NamedTerminal('INT', INT64_TYPE), _rp)),
             Lambda(
                 [Var('precision', INT64_TYPE), Var('scale', INT64_TYPE)],
                 _decimal_type_type,
                 Call(Message('logic', 'DecimalType'), [Var('precision', INT64_TYPE), Var('scale', INT64_TYPE)])
             )),
        ]
        for lhs_name, lhs_type, rhs, action in _type_rules:
            if lhs_name == 'decimal_type':
                # Decimal type has parameters
                self.add_rule(Rule(
                    lhs=Nonterminal(lhs_name, lhs_type),
                    rhs=rhs,
                    construct_action=action,
                    deconstruct_action=Lambda(
                        [Var('msg', lhs_type)],
                        OptionType(TupleType([INT64_TYPE, INT64_TYPE])),
                        make_some(make_tuple(
                            make_get_field(Var('msg', lhs_type), Lit('precision')),
                            make_get_field(Var('msg', lhs_type), Lit('scale'))
                        ))
                    )
                ))
            else:
                # Other type rules have no parameters
                self.add_rule(Rule(
                    lhs=Nonterminal(lhs_name, lhs_type),
                    rhs=rhs,
                    construct_action=action,
                    deconstruct_action=Lambda(
                        [Var('msg', lhs_type)],
                        OptionType(TupleType([])),
                        make_some(make_tuple())
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
            return self._message_relterm(Call(OneOf('term'), [term_var]))

        # Helper to extract term from arg
        def _extract_term_from_arg(msg_var, arg_lit):
            return make_get_field(make_get_field(msg_var, arg_lit), _lit_term)

        for name, op, prim in _comparison_ops:
            self.add_rule(Rule(
                lhs=Nonterminal(name, _primitive_type),
                rhs=Sequence((_lp, LitTerminal(op), _term_nt, _term_nt, _rp)),
                construct_action=Lambda(
                    [_var_left, _var_right],
                    _primitive_type,
                    self._message_primitive(Lit(prim), _wrap_relterm(_var_left), _wrap_relterm(_var_right))
                ),
                deconstruct_action=Lambda(
                    [Var('msg', _primitive_type)],
                    OptionType(TupleType([_term_type, _term_type])),
                    IfElse(
                        make_equal(make_get_field(Var('msg', _primitive_type), _lit_op), Lit(prim)),
                        make_some(make_tuple(
                            _extract_term_from_arg(Var('msg', _primitive_type), _lit_arg0),
                            _extract_term_from_arg(Var('msg', _primitive_type), _lit_arg1)
                        )),
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
            self.add_rule(Rule(
                lhs=Nonterminal(name, _primitive_type),
                rhs=Sequence((_lp, LitTerminal(op), _term_nt, _term_nt, _term_nt, _rp)),
                construct_action=Lambda(
                    [_var_left, _var_right, _var_result],
                    _primitive_type,
                    self._message_primitive(
                        Lit(prim),
                        _wrap_relterm(_var_left),
                        _wrap_relterm(_var_right),
                        _wrap_relterm(_var_result)
                    )
                ),
                deconstruct_action=Lambda(
                    [Var('msg', _primitive_type)],
                    OptionType(TupleType([_term_type, _term_type, _term_type])),
                    IfElse(
                        make_equal(make_get_field(Var('msg', _primitive_type), _lit_op), Lit(prim)),
                        make_some(make_tuple(
                            _extract_term_from_arg(Var('msg', _primitive_type), _lit_arg0),
                            _extract_term_from_arg(Var('msg', _primitive_type), _lit_arg1),
                            _extract_term_from_arg(Var('msg', _primitive_type), _lit_arg2)
                        )),
                        Lit(None)
                    )
                )
            ))

        # Primitive wrapper rules for operators (not final - auto-generation can add more)
        self.mark_nonfinal(_primitive_nt)
        _var_op = Var('op', _primitive_type)
        for name, _op, prim in _comparison_ops + _arithmetic_ops:
            self.add_rule(Rule(
                lhs=_primitive_nt,
                rhs=Nonterminal(name, _primitive_type),
                construct_action=Lambda([_var_op], _primitive_type, _var_op),
                deconstruct_action=Lambda(
                    [Var('msg', _primitive_type)],
                    OptionType(_primitive_type),
                    IfElse(
                        make_equal(make_get_field(Var('msg', _primitive_type), _lit_op), Lit(prim)),
                        make_some(Var('msg', _primitive_type)),
                        Lit(None)
                    )
                )
            ))

        self.add_rule(Rule(
            lhs=_new_fragment_id_nt,
            rhs=_fragment_id_nt,
            construct_action=Lambda(
                [
                    Var('fragment_id', _fragment_id_type),
                ],
                _fragment_id_type,
                Seq([
                    Call(Builtin('start_fragment'), [Var('fragment_id', _fragment_id_type)]),
                    Var('fragment_id', _fragment_id_type),
                ])
            ),
            deconstruct_action=Lambda(
                [Var('fragment_id', _fragment_id_type)],
                OptionType(_fragment_id_type),
                make_some(Var('fragment_id', _fragment_id_type))
            )
        ))

        # Fragment rule with debug_info construction
        self.add_rule(Rule(
            lhs=_fragment_nt,
            rhs=Sequence((
                _lp, LitTerminal('fragment'),
                _new_fragment_id_nt,
                Star(_declaration_nt),
                _rp
            )),
            construct_action=Lambda(
                [
                    Var('fragment_id', _fragment_id_type),
                    Var('declarations', ListType(_declaration_type))
                ],
                _fragment_type,
                Call(Builtin('construct_fragment'), [
                    Var('fragment_id', _fragment_id_type),
                    Var('declarations', ListType(_declaration_type))
                ])
            ),
            deconstruct_action=Lambda(
                [Var('msg', _fragment_type)],
                OptionType(TupleType([
                    _fragment_id_type,
                    ListType(_declaration_type)
                ])),
                Call(Builtin('deconstruct_fragment'), [Var('msg', _fragment_type)])
            )
        ))

        # output: STRING -> name?
        self.add_rule(Rule(
            lhs=_output_nt,
            rhs=Sequence((
                _lp, LitTerminal('output'),
                Option(_name_nt),
                _relation_id_nt,
                _rp
            )),
            construct_action=Lambda(
                [Var('name', STRING_TYPE), Var('relation_id', _relation_id_type)],
                _output_type,
                Call(Message('transactions', 'Output'), [Var('name', STRING_TYPE), Var('relation_id', _relation_id_type)])
            ),
            deconstruct_action=Lambda(
                [Var('msg', _output_type)],
                OptionType(TupleType([STRING_TYPE, _relation_id_type])),
                make_some(make_tuple(
                    make_get_field(Var('msg', _output_type), Lit('name')),
                    make_get_field(Var('msg', _output_type), Lit('relation_id'))
                ))
            )
        ))

        # abort: STRING -> name?
        self.add_rule(Rule(
            lhs=_abort_nt,
            rhs=Sequence((
                _lp, LitTerminal('abort'),
                Option(_name_nt),
                _relation_id_nt,
                _rp
            )),
            construct_action=Lambda(
                [Var('name', STRING_TYPE), Var('relation_id', _relation_id_type)],
                _abort_type,
                Call(Message('transactions', 'Abort'), [Var('name', STRING_TYPE), Var('relation_id', _relation_id_type)])
            ),
            deconstruct_action=Lambda(
                [Var('msg', _abort_type)],
                OptionType(TupleType([STRING_TYPE, _relation_id_type])),
                make_some(make_tuple(
                    make_get_field(Var('msg', _abort_type), Lit('name')),
                    make_get_field(Var('msg', _abort_type), Lit('relation_id'))
                ))
            )
        ))

        # ffi: STRING -> name, terms? -> term*
        self.add_rule(Rule(
            lhs=_ffi_nt,
            rhs=Sequence((
                _lp, LitTerminal('ffi'),
                _name_nt,
                Star(_abstraction_nt),
                Star(_term_nt),
                _rp
            )),
            construct_action=Lambda(
                [
                    Var('name', STRING_TYPE),
                    Var('args', ListType(_abstraction_type)),
                    Var('terms', ListType(_term_type))
                ],
                _ffi_type,
                Call(Message('logic', 'FFI'), [Var('name', STRING_TYPE), Var('args', ListType(_abstraction_type)), Var('terms', ListType(_term_type))])
            ),
            deconstruct_action=Lambda(
                [Var('msg', _ffi_type)],
                OptionType(TupleType([STRING_TYPE, ListType(_abstraction_type), ListType(_term_type)])),
                make_some(make_tuple(
                    make_get_field(Var('msg', _ffi_type), Lit('name')),
                    make_get_field(Var('msg', _ffi_type), Lit('args')),
                    make_get_field(Var('msg', _ffi_type), Lit('terms'))
                ))
            )
        ))

        # rel_atom: STRING -> name, terms? -> relterm*
        self.add_rule(Rule(
            lhs=_rel_atom_nt,
            rhs=Sequence((
                _lp, LitTerminal('rel_atom'),
                _name_nt,
                Star(_relterm_nt),
                _rp
            )),
            construct_action=Lambda(
                [Var('name', STRING_TYPE), Var('terms', ListType(_relterm_type))],
                _rel_atom_type,
                Call(Message('logic', 'RelAtom'), [Var('name', STRING_TYPE), Var('terms', ListType(_relterm_type))])
            ),
            deconstruct_action=Lambda(
                [Var('msg', _rel_atom_type)],
                OptionType(TupleType([STRING_TYPE, ListType(_relterm_type)])),
                make_some(make_tuple(
                    make_get_field(Var('msg', _rel_atom_type), Lit('name')),
                    make_get_field(Var('msg', _rel_atom_type), Lit('terms'))
                ))
            )
        ))

        # primitive: STRING -> name, term* -> relterm*
        self.add_rule(Rule(
            lhs=_primitive_nt,
            rhs=Sequence((
                LitTerminal('('), LitTerminal('primitive'),
                _name_nt,
                Star(_relterm_nt),
                LitTerminal(')')
            )),
            construct_action=Lambda(
                [Var('name', STRING_TYPE), Var('terms', ListType(_relterm_type))],
                _primitive_type,
                self._message_primitive(Var('name', STRING_TYPE), Var('terms', ListType(_relterm_type)))
            ),
            deconstruct_action=Lambda(
                [Var('msg', _primitive_type)],
                OptionType(TupleType([STRING_TYPE, ListType(_relterm_type)])),
                make_some(make_tuple(
                    make_get_field(Var('msg', _primitive_type), Lit('name')),
                    make_get_field(Var('msg', _primitive_type), Lit('terms'))
                ))
            )
        ))


        # exists: abstraction -> (bindings formula)
        self.add_rule(Rule(
            lhs=_exists_nt,
            rhs=Sequence((
                LitTerminal('('), LitTerminal('exists'),
                _bindings_nt,
                _formula_nt,
                LitTerminal(')')
            )),
            construct_action=Lambda(
                [Var('bindings', _bindings_type), Var('formula', _formula_type)],
                _exists_type,
                Call(Message('logic', 'Exists'), [
                    self._message_abstraction(
                        make_concat(
                            make_fst(Var('bindings', _bindings_type)),
                            make_snd(Var('bindings', _bindings_type))
                        ),
                        Var('formula', _formula_type)
                    )
                ])
            ),
            deconstruct_action=Lambda(
                [Var('msg', _exists_type)],
                OptionType(TupleType([_bindings_type, _formula_type])),
                Call(Builtin('deconstruct_exists'), [Var('msg', _exists_type)])
            )
        ))

        # Mark all the non-final rules as non-final
        for lhs in self.nonfinal_nonterminals:
            rules, _ = self.result[lhs]
            self.result[lhs] = (rules, False)


def get_builtin_rules() -> Dict[Nonterminal, Tuple[List[Rule], bool]]:
    """Return dict mapping nonterminals to (rules, is_final).

    is_final=True means auto-generation should not add more rules for this nonterminal.
    """
    return BuiltinRules().get_builtin_rules()
