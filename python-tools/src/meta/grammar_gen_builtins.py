"""Builtin grammar rules that are manually specified.

These rules define the grammar for constructs that cannot be auto-generated
from protobuf definitions, such as value literals, date/datetime parsing,
configuration syntax, bindings, abstractions, type literals, and operators.
"""

from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field

from .grammar import Rule, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence
from .target import (
    Lambda, Call, Var, Lit, Seq, Builtin, Message, OneOf, ListExpr,
    OptionType, ListType, TupleType, MessageType, TargetType
)
from .target_utils import (
    STRING_TYPE, INT64_TYPE, FLOAT64_TYPE, BOOLEAN_TYPE,
    create_identity_function,
    make_equal, make_which_oneof, make_get_field, make_some, make_tuple,
    make_fst, make_snd, make_is_empty, make_concat, make_length, make_unwrap_option_or
)

LPAREN = LitTerminal('(')
RPAREN = LitTerminal(')')
LBRACE = LitTerminal('{')
RBRACE = LitTerminal('}')


def _msg(module: str, name: str, *args):
    """Generic message constructor: Call(Message(module, name), [args])."""
    return Call(Message(module, name), list(args))




def _make_identity_rule(lhs_name: str, lhs_type: TargetType, rhs) -> Rule:
    """Create a rule where the value passes through unchanged."""
    return Rule(
        lhs=Nonterminal(lhs_name, lhs_type),
        rhs=rhs,
        constructor=create_identity_function(lhs_type)
    )


def _make_id_from_terminal_rule(
    lhs_name: str,
    msg_type: TargetType,
    terminal_name: str,
    terminal_type: TargetType,
    type_suffix: str
) -> Rule:
    """Create rule: id <- terminal using builtin conversion functions.

    Args:
        lhs_name: Name of LHS nonterminal and builtin prefix (e.g., 'fragment_id')
        msg_type: The message type (e.g., MessageType('fragments', 'FragmentId'))
        terminal_name: Terminal name (e.g., 'COLON_SYMBOL', 'INT')
        terminal_type: Terminal type (e.g., STRING_TYPE, INT64_TYPE)
        type_suffix: Suffix for builtins (e.g., 'string', 'int')
    """
    var_name = 'symbol' if type_suffix == 'string' else terminal_name
    param_var = Var(var_name, terminal_type)
    return Rule(
        lhs=Nonterminal(lhs_name, msg_type),
        rhs=NamedTerminal(terminal_name, terminal_type),
        constructor=Lambda(
            [param_var],
            return_type=msg_type,
            body=Call(Builtin(f'{lhs_name}_from_{type_suffix}'), [param_var])
        )
    )


def _make_simple_message_rule(
    lhs_name: str,
    module: str,
    message_name: str,
    fields: List[Tuple[str, 'TargetType']],
    rhs_inner: tuple = (),
    keyword: str | None = None
) -> Rule:
    """Generate rule with symmetric constructors from field spec.

    Args:
        lhs_name: Name of the LHS nonterminal
        module: Protobuf module name (e.g., 'logic', 'transactions')
        message_name: Protobuf message name
        fields: List of (field_name, field_type) tuples
        rhs_inner: Inner RHS elements (wrapped in '(' keyword ... ')').
                   If empty, RHS is just LitTerminal(keyword).
        keyword: Keyword for the rule (defaults to lhs_name)

    Returns:
        Rule where construct action wraps fields in message.
    """
    if keyword is None:
        keyword = lhs_name
    msg_type = MessageType(module, message_name)
    params = [Var(name, typ) for name, typ in fields]
    msg_var = Var('msg', msg_type)

    if rhs_inner:
        rhs = Sequence((LPAREN, LitTerminal(keyword)) + rhs_inner + (RPAREN,))
    else:
        rhs = LitTerminal(keyword)

    return Rule(
        lhs=Nonterminal(lhs_name, msg_type),
        rhs=rhs,
        constructor=Lambda(
            params,
            msg_type,
            _msg(module, message_name, *params)
        )
    )


def _make_value_oneof_rule(rhs, rhs_type, oneof_field_name):
    """Create a rule for Value -> oneof field."""
    _value_type = MessageType('logic', 'Value')
    _value_nt = Nonterminal('value', _value_type)

    var_value = Var('value', rhs_type)
    msg_var = Var('msg', _value_type)
    return Rule(
        lhs=_value_nt,
        rhs=rhs,
        constructor=Lambda(
            [var_value],
            _value_type,
            _msg('logic', 'Value', Call(OneOf(oneof_field_name), [var_value]))
        )
    )


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

    def _add_rules(self) -> None:
        """Add all builtin rules by calling themed rule methods."""
        self._add_value_rules()
        self._add_transaction_rules()
        self._add_bindings_rules()
        self._add_formula_rules()
        self._add_export_rules()
        self._add_id_rules()
        self._add_type_rules()
        self._add_operator_rules()
        self._add_fragment_rules()
        self._add_epoch_rules()
        self._add_logic_rules()

        # Mark all the non-final rules as non-final
        for lhs in self.nonfinal_nonterminals:
            rules, _ = self.result[lhs]
            self.result[lhs] = (rules, False)

    def _add_value_rules(self) -> None:
        """Add rules for value literals, missing, boolean, date/datetime."""

        # Common types used throughout
        _value_type = MessageType('logic', 'Value')
        _date_value_type = MessageType('logic', 'DateValue')
        _datetime_value_type = MessageType('logic', 'DateTimeValue')
        _uint128_value_type = MessageType('logic', 'UInt128Value')
        _int128_value_type = MessageType('logic', 'Int128Value')
        _decimal_value_type = MessageType('logic', 'DecimalValue')

        # Common nonterminals
        _value_nt = Nonterminal('value', _value_type)
        _date_nt = Nonterminal('date', _date_value_type)
        _datetime_nt = Nonterminal('datetime', _datetime_value_type)
        _boolean_value_nt = Nonterminal('boolean_value', BOOLEAN_TYPE)

        # Common terminals
        _string_terminal = NamedTerminal('STRING', STRING_TYPE)
        _int_terminal = NamedTerminal('INT', INT64_TYPE)
        _float_terminal = NamedTerminal('FLOAT', FLOAT64_TYPE)
        _uint128_terminal = NamedTerminal('UINT128', _uint128_value_type)
        _int128_terminal = NamedTerminal('INT128', _int128_value_type)
        _decimal_terminal = NamedTerminal('DECIMAL', _decimal_value_type)

        # Value literal rules
        self.add_rule(_make_value_oneof_rule(_date_nt, _date_value_type, 'date_value'))
        self.add_rule(_make_value_oneof_rule(_datetime_nt, _datetime_value_type, 'datetime_value'))
        self.add_rule(_make_value_oneof_rule(_string_terminal, STRING_TYPE, 'string_value'))
        self.add_rule(_make_value_oneof_rule(_int_terminal, INT64_TYPE, 'int_value'))
        self.add_rule(_make_value_oneof_rule(_float_terminal, FLOAT64_TYPE, 'float_value'))
        self.add_rule(_make_value_oneof_rule(_uint128_terminal, _uint128_value_type, 'uint128_value'))
        self.add_rule(_make_value_oneof_rule(_int128_terminal, _int128_value_type, 'int128_value'))
        self.add_rule(_make_value_oneof_rule(_decimal_terminal, _decimal_value_type, 'decimal_value'))

        # Special case: missing value
        _msg_value_var = Var('msg', _value_type)
        self.add_rule(Rule(
            lhs=_value_nt,
            rhs=LitTerminal('missing'),
            constructor=Lambda(
                [],
                _value_type,
                _msg('logic', 'Value', Call(OneOf('missing_value'), [_msg('logic', 'MissingValue')]))
            )
        ))

        # Bool value rules
        _var_bool_value = Var('value', BOOLEAN_TYPE)
        for keyword, value in [('true', True), ('false', False)]:
            self.add_rule(Rule(
                lhs=_boolean_value_nt,
                rhs=LitTerminal(keyword),
                constructor=Lambda([], BOOLEAN_TYPE, Lit(value))
            ))

        self.add_rule(_make_value_oneof_rule(_boolean_value_nt, BOOLEAN_TYPE, 'boolean_value'))

        # Date and datetime rules
        self.add_rule(_make_simple_message_rule(
            'date', 'logic', 'DateValue',
            fields=[('year', INT64_TYPE), ('month', INT64_TYPE), ('day', INT64_TYPE)],
            rhs_inner=(_int_terminal, _int_terminal, _int_terminal)
        ))

        _var_year = Var('year', INT64_TYPE)
        _var_month = Var('month', INT64_TYPE)
        _var_day = Var('day', INT64_TYPE)
        _var_hour = Var('hour', INT64_TYPE)
        _var_minute = Var('minute', INT64_TYPE)
        _var_second = Var('second', INT64_TYPE)
        _var_microsecond = Var('microsecond', OptionType(INT64_TYPE))

        _datetime_tuple_type = TupleType([INT64_TYPE, INT64_TYPE, INT64_TYPE, INT64_TYPE, INT64_TYPE, INT64_TYPE, OptionType(INT64_TYPE)])

        self.add_rule(Rule(
            lhs=_datetime_nt,
            rhs=Sequence((
                LPAREN, LitTerminal('datetime'),
                _int_terminal, _int_terminal, _int_terminal,
                _int_terminal, _int_terminal, _int_terminal,
                Option(_int_terminal),
                RPAREN
            )),
            constructor=Lambda(
                [_var_year, _var_month, _var_day, _var_hour, _var_minute, _var_second, _var_microsecond],
                _datetime_value_type,
                _msg('logic', 'DateTimeValue',
                    _var_year, _var_month, _var_day, _var_hour, _var_minute, _var_second,
                    make_unwrap_option_or(_var_microsecond, Lit(0))
                )
            )
        ))

    def _add_transaction_rules(self) -> None:
        """Add rules for transactions, configuration, and exports."""

        # Common types used throughout
        _value_type = MessageType('logic', 'Value')
        _transaction_type = MessageType('transactions', 'Transaction')
        _configure_type = MessageType('transactions', 'Configure')
        _sync_type = MessageType('transactions', 'Sync')
        _epoch_type = MessageType('transactions', 'Epoch')

        _config_key_value_type = TupleType([STRING_TYPE, _value_type])
        _config_type = ListType(_config_key_value_type)

        # Common nonterminals
        _value_nt = Nonterminal('value', _value_type)
        _config_dict_nt = Nonterminal('config_dict', _config_type)
        _config_key_value_nt = Nonterminal('config_key_value', _config_key_value_type)
        _transaction_nt = Nonterminal('transaction', _transaction_type)
        _configure_nt = Nonterminal('configure', _configure_type)
        _sync_nt = Nonterminal('sync', _sync_type)
        _epoch_nt = Nonterminal('epoch', _epoch_type)

        # Common terminals
        _colon_symbol_terminal = NamedTerminal('COLON_SYMBOL', STRING_TYPE)

        # Configuration rules
        _var_tuple = Var('tuple', _config_key_value_type)

        self.add_rule(_make_identity_rule(
            'config_dict', _config_type,
            rhs=Sequence((LBRACE, Star(_config_key_value_nt), RBRACE))
        ))

        self.add_rule(Rule(
            lhs=_config_key_value_nt,
            rhs=Sequence((_colon_symbol_terminal, _value_nt)),
            constructor=Lambda(
                [Var('symbol', STRING_TYPE), Var('value', _value_type)],
                _config_key_value_type,
                make_tuple(Var('symbol', STRING_TYPE), Var('value', _value_type))
            )

        ))

        # Transaction rule
        self.add_rule(Rule(
            lhs=_transaction_nt,
            rhs=Sequence((
                LPAREN, LitTerminal('transaction'),
                Option(_configure_nt),
                Option(_sync_nt),
                Star(_epoch_nt),
                RPAREN
            )),
            constructor=Lambda(
                [
                    Var('configure', OptionType(_configure_type)),
                    Var('sync', OptionType(_sync_type)),
                    Var('epochs', ListType(_epoch_type))
                ],
                _transaction_type,
                _msg('transactions', 'Transaction',
                    Var('epochs', ListType(_epoch_type)),
                    make_unwrap_option_or(
                        Var('configure', OptionType(_configure_type)),
                        Call(Builtin('construct_configure'), [ListExpr([], TupleType([STRING_TYPE, _value_type]))])
                    ),
                    Var('sync', OptionType(_sync_type))
                )
            )

        ))

        # Configure rule
        self.add_rule(Rule(
            lhs=_configure_nt,
            rhs=Sequence((
                LPAREN, LitTerminal('configure'),
                _config_dict_nt,
                RPAREN
            )),
            constructor=Lambda(
                [Var('config_dict', _config_type)],
                return_type=_configure_type,
                body=Call(Builtin('construct_configure'), [Var('config_dict', _config_type)])
            )

        ))

    def _add_bindings_rules(self) -> None:
        """Add rules for bindings and abstractions."""

        # Common types used throughout
        _binding_type = MessageType('logic', 'Binding')
        _formula_type = MessageType('logic', 'Formula')
        _abstraction_type = MessageType('logic', 'Abstraction')
        _type_type = MessageType('logic', 'Type')

        _bindings_type = TupleType([ListType(_binding_type), ListType(_binding_type)])
        _abstraction_with_arity_type = TupleType([_abstraction_type, INT64_TYPE])

        # Common nonterminals
        _binding_nt = Nonterminal('binding', _binding_type)
        _bindings_nt = Nonterminal('bindings', _bindings_type)
        _formula_nt = Nonterminal('formula', _formula_type)
        _abstraction_nt = Nonterminal('abstraction', _abstraction_type)
        _type_nt = Nonterminal('type', _type_type)
        _value_bindings_nt = Nonterminal('value_bindings', ListType(_binding_type))
        _abstraction_with_arity_nt = Nonterminal('abstraction_with_arity', _abstraction_with_arity_type)

        # Common terminals
        _symbol_terminal = NamedTerminal('SYMBOL', STRING_TYPE)

        # Bindings rules
        _var_keys = Var('keys', ListType(_binding_type))
        _var_values = Var('values', OptionType(ListType(_binding_type)))
        _var_bindings_tuple = Var('tuple', _bindings_type)
        _empty_binding_list = ListExpr([], _binding_type)

        self.add_rule(Rule(
            lhs=_bindings_nt,
            rhs=Sequence((LitTerminal('['), Star(_binding_nt), Option(_value_bindings_nt), LitTerminal(']'))),
            constructor=Lambda(
                [_var_keys, _var_values],
                _bindings_type,
                make_tuple(
                    _var_keys,
                    make_unwrap_option_or(_var_values, _empty_binding_list)
                )
            )

        ))

        self.add_rule(_make_identity_rule(
            'value_bindings', ListType(_binding_type),
            rhs=Sequence((LitTerminal('|'), Star(_binding_nt)))
        ))

        _type_var = Var('type', _type_type)
        self.add_rule(Rule(
            lhs=_binding_nt,
            rhs=Sequence((_symbol_terminal, LitTerminal('::'), _type_nt)),
            constructor=Lambda(
                [Var('symbol', STRING_TYPE), _type_var],
                _binding_type,
                _msg('logic', 'Binding', _msg('logic', 'Var', Var('symbol', STRING_TYPE)), _type_var)
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
            rhs=Sequence((LPAREN, _bindings_nt, _formula_nt, RPAREN)),
            constructor=Lambda(
                params=[_var_bindings, _var_formula],
                return_type=_abstraction_with_arity_type,
                body=make_tuple(
                    _msg('logic', 'Abstraction', _concat_bindings(_var_bindings), _var_formula),
                    make_length(make_snd(_var_bindings))
                )
            )

        ))

        self.add_rule(Rule(
            lhs=_abstraction_nt,
            rhs=Sequence((LPAREN, _bindings_nt, _formula_nt, RPAREN)),
            constructor=Lambda(
                params=[_var_bindings, _var_formula],
                return_type=_abstraction_type,
                body=_msg('logic', 'Abstraction', _concat_bindings(_var_bindings), _var_formula)
            )

        ))

    def _add_formula_rules(self) -> None:
        """Add rules for formulas, true/false, and configure."""

        # Common types used throughout
        _formula_type = MessageType('logic', 'Formula')
        _conjunction_type = MessageType('logic', 'Conjunction')
        _disjunction_type = MessageType('logic', 'Disjunction')

        # Common nonterminals
        _formula_nt = Nonterminal('formula', _formula_type)
        _true_nt = Nonterminal('true', _conjunction_type)
        _false_nt = Nonterminal('false', _disjunction_type)

        # True/false formula rules
        _empty_formula_list = ListExpr([], _formula_type)
        _lit_formulas = Lit('formulas')
        _empty_tuple_type = TupleType([])

        self.add_rule(Rule(
            lhs=_true_nt,
            rhs=Sequence((LPAREN, LitTerminal('true'), RPAREN)),
            constructor=Lambda([], _conjunction_type, _msg('logic', 'Conjunction', _empty_formula_list))

        ))

        self.add_rule(Rule(
            lhs=_false_nt,
            rhs=Sequence((LPAREN, LitTerminal('false'), RPAREN)),
            constructor=Lambda([], _disjunction_type, _msg('logic', 'Disjunction', _empty_formula_list))

        ))

        # Formula rules (not final - auto-generation can add more)
        # True formula: checks for empty Conjunction in the 'conjunction' oneof field
        self.mark_nonfinal(_formula_nt)

        _msg_formula_var = Var('msg', _formula_type)
        self.add_rule(Rule(
            lhs=_formula_nt,
            rhs=_true_nt,
            constructor=Lambda(
                [Var('value', _conjunction_type)],
                _formula_type,
                _msg('logic', 'Formula', Call(OneOf('conjunction'), [Var('value', _conjunction_type)]))
            )

        ))

        # False formula: checks for empty Disjunction in the 'disjunction' oneof field
        self.add_rule(Rule(
            lhs=_formula_nt,
            rhs=_false_nt,
            constructor=Lambda(
                [Var('value', _disjunction_type)],
                _formula_type,
                _msg('logic', 'Formula', Call(OneOf('disjunction'), [Var('value', _disjunction_type)]))
            )

        ))

    def _add_export_rules(self) -> None:
        """Add rules for export and export CSV configuration."""

        # Common types used throughout
        _value_type = MessageType('logic', 'Value')
        _relation_id_type = MessageType('logic', 'RelationId')
        _export_type = MessageType('transactions', 'Export')
        _export_csv_config_type = MessageType('transactions', 'ExportCSVConfig')
        _export_csv_column_type = MessageType('transactions', 'ExportCSVColumn')

        _config_key_value_type = TupleType([STRING_TYPE, _value_type])
        _config_type = ListType(_config_key_value_type)

        # Common nonterminals
        _relation_id_nt = Nonterminal('relation_id', _relation_id_type)
        _config_dict_nt = Nonterminal('config_dict', _config_type)
        _export_nt = Nonterminal('export', _export_type)
        _export_csv_config_nt = Nonterminal('export_csvconfig', _export_csv_config_type)
        _export_csv_path_nt = Nonterminal('export_csvpath', STRING_TYPE)
        _export_csv_columns_nt = Nonterminal('export_csvcolumns', ListType(_export_csv_column_type))

        # Export rules
        _msg_export_var = Var('msg', _export_type)
        self.add_rule(Rule(
            lhs=_export_nt,
            rhs=Sequence((
                LPAREN, LitTerminal('export'),
                _export_csv_config_nt,
                RPAREN
            )),
            constructor=Lambda(
                [Var('config', _export_csv_config_type)],
                _export_type,
                _msg('transactions', 'Export', Call(OneOf('csv_config'), [Var('config', _export_csv_config_type)]))
            )

        ))

        # Export CSV path rule
        self.add_rule(_make_identity_rule(
            'export_csv_path', STRING_TYPE,
            rhs=Sequence((LPAREN, LitTerminal('path'), NamedTerminal('STRING', STRING_TYPE), RPAREN))
        ))

        self.add_rule(Rule(
            lhs=_export_csv_config_nt,
            rhs=Sequence((
                LPAREN, LitTerminal('export_csv_config'),
                _export_csv_path_nt,
                _export_csv_columns_nt,
                _config_dict_nt,
                RPAREN
            )),
            constructor=Lambda(
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
            )

        ))

        self.add_rule(_make_identity_rule(
            'export_csv_columns', ListType(_export_csv_column_type),
            rhs=Sequence((
                LPAREN, LitTerminal('columns'),
                Star(Nonterminal('export_csv_column', _export_csv_column_type)),
                RPAREN
            ))
        ))

        self.add_rule(_make_simple_message_rule(
            'export_csv_column', 'transactions', 'ExportCSVColumn',
            fields=[('name', STRING_TYPE), ('relation_id', _relation_id_type)],
            rhs_inner=(NamedTerminal('STRING', STRING_TYPE), _relation_id_nt),
            keyword='column'
        ))

    def _add_id_rules(self) -> None:
        """Add rules for vars, fragment IDs, relation IDs, and specialized values."""

        # Common types used throughout
        _value_type = MessageType('logic', 'Value')
        _relation_id_type = MessageType('logic', 'RelationId')
        _var_type = MessageType('logic', 'Var')
        _fragment_id_type = MessageType('fragments', 'FragmentId')

        # Common nonterminals
        _name_nt = Nonterminal('name', STRING_TYPE)
        _value_nt = Nonterminal('value', _value_type)
        _relation_id_nt = Nonterminal('relation_id', _relation_id_type)
        _var_nt = Nonterminal('var', _var_type)
        _fragment_id_nt = Nonterminal('fragment_id', _fragment_id_type)
        _specialized_value_nt = Nonterminal('specialized_value', _value_type)

        # Common terminals
        _symbol_terminal = NamedTerminal('SYMBOL', STRING_TYPE)
        _colon_symbol_terminal = NamedTerminal('COLON_SYMBOL', STRING_TYPE)

        # Name rule
        self.add_rule(_make_identity_rule('name', STRING_TYPE, rhs=_colon_symbol_terminal))

        # Var rule
        self.add_rule(Rule(
            lhs=_var_nt,
            rhs=_symbol_terminal,
            constructor=Lambda([Var('symbol', STRING_TYPE)], _var_type, _msg('logic', 'Var', Var('symbol', STRING_TYPE)))

        ))

        # ID rules
        self.add_rule(_make_id_from_terminal_rule(
            'fragment_id', _fragment_id_type, 'COLON_SYMBOL', STRING_TYPE, 'string'))
        self.add_rule(_make_id_from_terminal_rule(
            'relation_id', _relation_id_type, 'COLON_SYMBOL', STRING_TYPE, 'string'))
        self.add_rule(_make_id_from_terminal_rule(
            'relation_id', _relation_id_type, 'INT', INT64_TYPE, 'int'))

        # Specialized value rule
        self.add_rule(Rule(
            lhs=_specialized_value_nt,
            rhs=Sequence((LitTerminal('#'), _value_nt)),
            constructor=Lambda(
                [Var('value', _value_type)],
                _value_type,
                Var('value', _value_type)
            )

        ))

    def _add_type_rules(self) -> None:
        """Add rules for type literals."""

        def _make_simple_type_rule(keyword: str, message_name: str) -> Rule:
            """Create a rule for a simple type with no parameters."""
            from .grammar_gen import _get_rule_name
            lhs_name = _get_rule_name(message_name)
            return _make_simple_message_rule(lhs_name, 'logic', message_name, fields=[], keyword=keyword)

        # Simple types: (keyword, message_name)
        _simple_types = [
            ('UNKNOWN', 'UnspecifiedType'),
            ('STRING', 'StringType'),
            ('INT', 'IntType'),
            ('FLOAT', 'FloatType'),
            ('UINT128', 'UInt128Type'),
            ('INT128', 'Int128Type'),
            ('BOOLEAN', 'BooleanType'),
            ('DATE', 'DateType'),
            ('DATETIME', 'DateTimeType'),
            ('MISSING', 'MissingType'),
        ]

        for keyword, message_name in _simple_types:
            self.add_rule(_make_simple_type_rule(keyword, message_name))

        # Decimal type has parameters (precision, scale)
        self.add_rule(_make_simple_message_rule(
            'decimal_type', 'logic', 'DecimalType',
            fields=[('precision', INT64_TYPE), ('scale', INT64_TYPE)],
            rhs_inner=(NamedTerminal('INT', INT64_TYPE), NamedTerminal('INT', INT64_TYPE)),
            keyword='DECIMAL'
        ))

    def _add_operator_rules(self) -> None:
        """Add rules for comparison and arithmetic operators."""

        _term_type = MessageType('logic', 'Term')
        _primitive_type = MessageType('logic', 'Primitive')
        _term_nt = Nonterminal('term', _term_type)
        _primitive_nt = Nonterminal('primitive', _primitive_type)

        _var_names = ['left', 'right', 'result']
        _arg_lits = [Lit('arg0'), Lit('arg1'), Lit('arg2')]
        _lit_op = Lit('op')
        _lit_term = Lit('term')

        def _make_operator_rules(name: str, op: str, prim: str, arity: int) -> Tuple[Rule, Rule]:
            """Create operator rule and its wrapper rule."""
            params = [Var(_var_names[i], _term_type) for i in range(arity)]
            rhs_terms = tuple(_term_nt for _ in range(arity))
            msg_var = Var('msg', _primitive_type)

            wrapped_args = [_msg('logic', 'RelTerm', Call(OneOf('term'), [p])) for p in params]
            extracted_args = [make_get_field(make_get_field(msg_var, _arg_lits[i]), _lit_term)
                              for i in range(arity)]

            op_nt = Nonterminal(name, _primitive_type)

            # The operator rule (e.g., eq -> '(' '=' term term ')')
            op_rule = Rule(
                lhs=op_nt,
                rhs=Sequence((LPAREN, LitTerminal(op)) + rhs_terms + (RPAREN,)),
                constructor=Lambda(
                    params,
                    _primitive_type,
                    _msg('logic', 'Primitive', Lit(prim), *wrapped_args)
                )

            )

            # The wrapper rule (e.g., primitive -> eq)
            wrapper_rule = Rule(
                lhs=_primitive_nt,
                rhs=op_nt,
                constructor=Lambda([Var('op', _primitive_type)], _primitive_type, Var('op', _primitive_type))

            )

            return op_rule, wrapper_rule

        # (name, operator, primitive, arity)
        _operators = [
            ('eq', '=', 'rel_primitive_eq', 2),
            ('lt', '<', 'rel_primitive_lt_monotype', 2),
            ('lt_eq', '<=', 'rel_primitive_lt_eq_monotype', 2),
            ('gt', '>', 'rel_primitive_gt_monotype', 2),
            ('gt_eq', '>=', 'rel_primitive_gt_eq_monotype', 2),
            ('add', '+', 'rel_primitive_add_monotype', 3),
            ('minus', '-', 'rel_primitive_subtract_monotype', 3),
            ('multiply', '*', 'rel_primitive_multiply_monotype', 3),
            ('divide', '/', 'rel_primitive_divide_monotype', 3),
        ]

        self.mark_nonfinal(_primitive_nt)
        for name, op, prim, arity in _operators:
            op_rule, wrapper_rule = _make_operator_rules(name, op, prim, arity)
            self.add_rule(op_rule)
            self.add_rule(wrapper_rule)

    def _add_fragment_rules(self) -> None:
        """Add rules for fragments and new fragment IDs."""

        # Common types used throughout
        _declaration_type = MessageType('logic', 'Declaration')
        _fragment_id_type = MessageType('fragments', 'FragmentId')
        _fragment_type = MessageType('fragments', 'Fragment')

        # Common nonterminals
        _declaration_nt = Nonterminal('declaration', _declaration_type)
        _fragment_id_nt = Nonterminal('fragment_id', _fragment_id_type)
        _new_fragment_id_nt = Nonterminal('new_fragment_id', _fragment_id_type)
        _fragment_nt = Nonterminal('fragment', _fragment_type)

        self.add_rule(Rule(
            lhs=_new_fragment_id_nt,
            rhs=_fragment_id_nt,
            constructor=Lambda(
                [
                    Var('fragment_id', _fragment_id_type),
                ],
                _fragment_id_type,
                Seq([
                    Call(Builtin('start_fragment'), [Var('fragment_id', _fragment_id_type)]),
                    Var('fragment_id', _fragment_id_type),
                ])
            )

        ))

        # Fragment rule with debug_info construction
        self.add_rule(Rule(
            lhs=_fragment_nt,
            rhs=Sequence((
                LPAREN, LitTerminal('fragment'),
                _new_fragment_id_nt,
                Star(_declaration_nt),
                RPAREN
            )),
            constructor=Lambda(
                [
                    Var('fragment_id', _fragment_id_type),
                    Var('declarations', ListType(_declaration_type))
                ],
                _fragment_type,
                Call(Builtin('construct_fragment'), [
                    Var('fragment_id', _fragment_id_type),
                    Var('declarations', ListType(_declaration_type))
                ])
            )

        ))

    def _add_epoch_rules(self) -> None:
        """Add rules for output and abort."""

        _relation_id_type = MessageType('logic', 'RelationId')
        _relation_id_nt = Nonterminal('relation_id', _relation_id_type)
        _name_nt = Nonterminal('name', STRING_TYPE)

        def _make_name_option_relation_rule(keyword: str, message_name: str) -> Rule:
            """Create a rule for (keyword name? relation_id) -> Message(name, relation_id).

            If name is missing, defaults to the keyword.
            """
            msg_type = MessageType('transactions', message_name)
            msg_var = Var('msg', msg_type)
            name_var = Var('name', OptionType(STRING_TYPE))
            return Rule(
                lhs=Nonterminal(keyword, msg_type),
                rhs=Sequence((
                    LPAREN, LitTerminal(keyword),
                    Option(_name_nt),
                    _relation_id_nt,
                    RPAREN
                )),
                constructor=Lambda(
                    [name_var, Var('relation_id', _relation_id_type)],
                    msg_type,
                    _msg('transactions', message_name,
                        make_unwrap_option_or(name_var, Lit(keyword)),
                        Var('relation_id', _relation_id_type))
                )

            )

        self.add_rule(_make_name_option_relation_rule('output', 'Output'))
        self.add_rule(_make_name_option_relation_rule('abort', 'Abort'))

    def _add_logic_rules(self) -> None:
        """Add rules for ffi, rel_atom, primitive, and exists."""

        # Common types used throughout
        _binding_type = MessageType('logic', 'Binding')
        _formula_type = MessageType('logic', 'Formula')
        _term_type = MessageType('logic', 'Term')
        _abstraction_type = MessageType('logic', 'Abstraction')
        _relterm_type = MessageType('logic', 'RelTerm')
        _exists_type = MessageType('logic', 'Exists')
        _bindings_type = TupleType([ListType(_binding_type), ListType(_binding_type)])

        # Common nonterminals
        _bindings_nt = Nonterminal('bindings', _bindings_type)
        _formula_nt = Nonterminal('formula', _formula_type)
        _term_nt = Nonterminal('term', _term_type)
        _relterm_nt = Nonterminal('rel_term', _relterm_type)
        _abstraction_nt = Nonterminal('abstraction', _abstraction_type)
        _name_nt = Nonterminal('name', STRING_TYPE)
        _exists_nt = Nonterminal('exists', _exists_type)

        # ffi: STRING -> name, terms? -> term*
        self.add_rule(_make_simple_message_rule(
            'ffi', 'logic', 'FFI',
            fields=[
                ('name', STRING_TYPE),
                ('args', ListType(_abstraction_type)),
                ('terms', ListType(_term_type))
            ],
            rhs_inner=(_name_nt, Star(_abstraction_nt), Star(_term_nt))
        ))

        # rel_atom: STRING -> name, terms? -> relterm*
        self.add_rule(_make_simple_message_rule(
            'rel_atom', 'logic', 'RelAtom',
            fields=[('name', STRING_TYPE), ('terms', ListType(_relterm_type))],
            rhs_inner=(_name_nt, Star(_relterm_nt))
        ))

        # primitive: STRING -> name, term* -> relterm*
        self.add_rule(_make_simple_message_rule(
            'primitive', 'logic', 'Primitive',
            fields=[('name', STRING_TYPE), ('terms', ListType(_relterm_type))],
            rhs_inner=(_name_nt, Star(_relterm_nt))
        ))

        # exists: abstraction -> (bindings formula)
        self.add_rule(Rule(
            lhs=_exists_nt,
            rhs=Sequence((
                LPAREN, LitTerminal('exists'),
                _bindings_nt,
                _formula_nt,
                RPAREN
            )),
            constructor=Lambda(
                [Var('bindings', _bindings_type), Var('formula', _formula_type)],
                _exists_type,
                _msg('logic', 'Exists',
                    _msg('logic', 'Abstraction',
                        make_concat(
                            make_fst(Var('bindings', _bindings_type)),
                            make_snd(Var('bindings', _bindings_type))
                        ),
                        Var('formula', _formula_type)
                    )
                )
            )

        ))


def get_builtin_rules() -> Dict[Nonterminal, Tuple[List[Rule], bool]]:
    """Return dict mapping nonterminals to (rules, is_final).

    is_final=True means auto-generation should not add more rules for this nonterminal.
    """
    return BuiltinRules().get_builtin_rules()
