"""Builtin grammar rules that are manually specified.

These rules define the grammar for constructs that cannot be auto-generated
from protobuf definitions, such as value literals, date/datetime parsing,
configuration syntax, bindings, abstractions, type literals, and operators.
"""

from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field

from .grammar import Rule, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence
from .target import (
    Lambda, Call, Var, Lit, Seq, IfElse, Builtin, Message, OneOf, ListExpr,
    OptionType, ListType, TupleType, MessageType, FunctionType, TargetType
)
from .target_utils import (
    STRING_TYPE, INT64_TYPE, FLOAT64_TYPE, BOOLEAN_TYPE,
    create_identity_function, create_identity_option_function,
    make_equal, make_which_oneof, make_get_field, make_some, make_tuple,
    make_fst, make_snd, make_is_empty, make_concat, make_length, make_unwrap_option_or
)

_lp = LitTerminal('(')
_rp = LitTerminal(')')
_lc = LitTerminal('{')
_rc = LitTerminal('}')


def _msg(module: str, name: str, *args):
    """Generic message constructor: Call(Message(module, name), [args])."""
    return Call(Message(module, name), list(args))


def _oneof_deconstruct(msg_var, oneof_discriminator: str, oneof_field_name: str, extra_check=None):
    """Create standard oneof deconstruct pattern.

    Args:
        msg_var: Variable for the message being deconstructed
        oneof_discriminator: Name of the oneof field (e.g., 'value_type', 'formula_type')
        oneof_field_name: Name of the specific variant field
        extra_check: Optional additional condition to check after discriminator match

    Returns:
        IfElse expression that returns Some(field_value) if match, None otherwise
    """
    base_check = make_equal(
        make_which_oneof(msg_var, Lit(oneof_discriminator)),
        Lit(oneof_field_name)
    )
    field_value = make_get_field(msg_var, Lit(oneof_field_name))
    if extra_check is None:
        return IfElse(base_check, make_some(field_value), Lit(None))
    return IfElse(
        base_check,
        IfElse(extra_check, make_some(field_value), Lit(None)),
        Lit(None)
    )

def _make_identity_rule(lhs_name: str, lhs_type: TargetType, rhs) -> Rule:
    """Create a rule where the value passes through unchanged."""
    return Rule(
        lhs=Nonterminal(lhs_name, lhs_type),
        rhs=rhs,
        construct_action=create_identity_function(lhs_type),
        deconstruct_action=create_identity_option_function(lhs_type)
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
    msg_var = Var('msg', msg_type)
    return Rule(
        lhs=Nonterminal(lhs_name, msg_type),
        rhs=NamedTerminal(terminal_name, terminal_type),
        construct_action=Lambda(
            [param_var],
            return_type=msg_type,
            body=Call(Builtin(f'{lhs_name}_from_{type_suffix}'), [param_var])
        ),
        deconstruct_action=Lambda(
            [msg_var],
            OptionType(terminal_type),
            Call(Builtin(f'{lhs_name}_to_{type_suffix}'), [msg_var])
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
    """Generate rule with symmetric construct/deconstruct from field spec.

    Args:
        lhs_name: Name of the LHS nonterminal
        module: Protobuf module name (e.g., 'logic', 'transactions')
        message_name: Protobuf message name
        fields: List of (field_name, field_type) tuples
        rhs_inner: Inner RHS elements (wrapped in '(' keyword ... ')').
                   If empty, RHS is just LitTerminal(keyword).
        keyword: Keyword for the rule (defaults to lhs_name)

    Returns:
        Rule where construct wraps fields in message, deconstruct extracts them.
    """
    if keyword is None:
        keyword = lhs_name
    msg_type = MessageType(module, message_name)
    params = [Var(name, typ) for name, typ in fields]
    msg_var = Var('msg', msg_type)

    if rhs_inner:
        rhs = Sequence((_lp, LitTerminal(keyword)) + rhs_inner + (_rp,))
    else:
        rhs = LitTerminal(keyword)

    return Rule(
        lhs=Nonterminal(lhs_name, msg_type),
        rhs=rhs,
        construct_action=Lambda(
            params,
            msg_type,
            _msg(module, message_name, *params)
        ),
        deconstruct_action=Lambda(
            [msg_var],
            OptionType(TupleType([typ for _, typ in fields])),
            make_some(make_tuple(*[
                make_get_field(msg_var, Lit(name)) for name, _ in fields
            ]))
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
        construct_action=Lambda(
            [var_value],
            _value_type,
            _msg('logic', 'Value', Call(OneOf(oneof_field_name), [var_value]))
        ),
        deconstruct_action=Lambda(
            [msg_var],
            OptionType(rhs_type),
            _oneof_deconstruct(msg_var, 'value_type', oneof_field_name)
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
        self._add_monoid_rules()
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
            construct_action=Lambda(
                [],
                _value_type,
                _msg('logic', 'Value', Call(OneOf('missing_value'), [_msg('logic', 'MissingValue')]))
            ),
            deconstruct_action=Lambda(
                [_msg_value_var],
                OptionType(TupleType([])),
                IfElse(
                    make_equal(make_which_oneof(_msg_value_var, Lit('value_type')), Lit('missing_value')),
                    make_some(make_tuple()),
                    Lit(None)
                )
            )
        ))

        # Bool value rules
        _var_bool_value = Var('value', BOOLEAN_TYPE)
        for keyword, value in [('true', True), ('false', False)]:
            self.add_rule(Rule(
                lhs=_boolean_value_nt,
                rhs=LitTerminal(keyword),
                construct_action=Lambda([], BOOLEAN_TYPE, Lit(value)),
                deconstruct_action=Lambda(
                    [_var_bool_value],
                    OptionType(TupleType([])),
                    IfElse(make_equal(_var_bool_value, Lit(value)), make_some(make_tuple()), Lit(None))
                )
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
                _lp, LitTerminal('datetime'),
                _int_terminal, _int_terminal, _int_terminal,
                _int_terminal, _int_terminal, _int_terminal,
                Option(_int_terminal),
                _rp
            )),
            construct_action=Lambda(
                [_var_year, _var_month, _var_day, _var_hour, _var_minute, _var_second, _var_microsecond],
                _datetime_value_type,
                _msg('logic', 'DateTimeValue',
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
            rhs=Sequence((_lc, Star(_config_key_value_nt), _rc))
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
                _msg('transactions', 'Transaction',
                    Var('epochs', ListType(_epoch_type)),
                    make_unwrap_option_or(
                        Var('configure', OptionType(_configure_type)),
                        Call(Builtin('construct_configure'), [ListExpr([], TupleType([STRING_TYPE, _value_type]))])
                    ),
                    Var('sync', OptionType(_sync_type))
                )
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

        self.add_rule(_make_identity_rule(
            'value_bindings', ListType(_binding_type),
            rhs=Sequence((LitTerminal('|'), Star(_binding_nt)))
        ))

        _type_var = Var('type', _type_type)
        self.add_rule(Rule(
            lhs=_binding_nt,
            rhs=Sequence((_symbol_terminal, LitTerminal('::'), _type_nt)),
            construct_action=Lambda(
                [Var('symbol', STRING_TYPE), _type_var],
                _binding_type,
                _msg('logic', 'Binding', _msg('logic', 'Var', Var('symbol', STRING_TYPE)), _type_var)
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
                    _msg('logic', 'Abstraction', _concat_bindings(_var_bindings), _var_formula),
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
                body=_msg('logic', 'Abstraction', _concat_bindings(_var_bindings), _var_formula)
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

    def _add_monoid_rules(self) -> None:
        """Add rules for monoid operators."""

        # Common types used throughout
        _type_type = MessageType('logic', 'Type')
        _monoid_type = MessageType('logic', 'Monoid')
        _monoid_op_type = FunctionType([_type_type], _monoid_type)

        # Common nonterminals
        _type_nt = Nonterminal('type', _type_type)
        _monoid_nt = Nonterminal('monoid', _monoid_type)
        _monoid_op_nt = Nonterminal('monoid_op', _monoid_op_type)

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

        body = _msg('logic', 'Monoid',
            Call(OneOf('or_monoid'), [_msg('logic', 'OrMonoid')])
        )

        _msg_monoid_var = Var('msg', _monoid_type)
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
                [_msg_monoid_var],
                OptionType(TupleType([])),
                IfElse(
                    make_equal(make_which_oneof(_msg_monoid_var, Lit('monoid_type')), Lit('or_monoid')),
                    make_some(make_tuple()),
                    Lit(None)
                )
            )
        ))

        def _make_monoid_op_rule(constructor: str) -> Rule:
            op = constructor.removesuffix('Monoid')
            symbol = f'{op.lower()}_monoid'
            lit = op.upper()
            body = _msg('logic', 'Monoid',
                Call(OneOf(symbol), [_msg('logic', constructor, Var('type', _type_type))])
            )
            rhs = LitTerminal(lit)
            construct_action = Lambda(
                [],
                return_type=_monoid_op_type,
                body=Lambda([Var('type', _type_type)], return_type=_monoid_type, body=body)
            )
            deconstruct_action = Lambda(
                [Var('op', _monoid_op_type)],
                return_type=OptionType(TupleType([])),
                body=Call(Builtin('deconstruct_monoid_op'), [Var('op', _monoid_op_type), Lit(symbol)])
            )
            return Rule(
                lhs=_monoid_op_nt,
                rhs=rhs,
                construct_action=construct_action,
                deconstruct_action=deconstruct_action
            )

        self.add_rule(_make_monoid_op_rule('MinMonoid'))
        self.add_rule(_make_monoid_op_rule('MaxMonoid'))
        self.add_rule(_make_monoid_op_rule('SumMonoid'))

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
            rhs=Sequence((_lp, LitTerminal('true'), _rp)),
            construct_action=Lambda([], _conjunction_type, _msg('logic', 'Conjunction', _empty_formula_list)),
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
            construct_action=Lambda([], _disjunction_type, _msg('logic', 'Disjunction', _empty_formula_list)),
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

        _msg_formula_var = Var('msg', _formula_type)
        self.add_rule(Rule(
            lhs=_formula_nt,
            rhs=_true_nt,
            construct_action=Lambda(
                [Var('value', _conjunction_type)],
                _formula_type,
                _msg('logic', 'Formula', Call(OneOf('conjunction'), [Var('value', _conjunction_type)]))
            ),
            deconstruct_action=Lambda(
                [_msg_formula_var],
                OptionType(_conjunction_type),
                _oneof_deconstruct(
                    _msg_formula_var, 'formula_type', 'conjunction',
                    extra_check=make_is_empty(make_get_field(make_get_field(_msg_formula_var, Lit('conjunction')), _lit_formulas))
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
                _msg('logic', 'Formula', Call(OneOf('disjunction'), [Var('value', _disjunction_type)]))
            ),
            deconstruct_action=Lambda(
                [_msg_formula_var],
                OptionType(_disjunction_type),
                _oneof_deconstruct(
                    _msg_formula_var, 'formula_type', 'disjunction',
                    extra_check=make_is_empty(make_get_field(make_get_field(_msg_formula_var, Lit('disjunction')), _lit_formulas))
                )
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
        _export_csv_config_nt = Nonterminal('export_csv_config', _export_csv_config_type)
        _export_csv_path_nt = Nonterminal('export_csv_path', STRING_TYPE)
        _export_csv_columns_nt = Nonterminal('export_csv_columns', ListType(_export_csv_column_type))

        # Export rules
        _msg_export_var = Var('msg', _export_type)
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
                _msg('transactions', 'Export', Call(OneOf('csv_config'), [Var('config', _export_csv_config_type)]))
            ),
            deconstruct_action=Lambda(
                [_msg_export_var],
                OptionType(_export_csv_config_type),
                _oneof_deconstruct(_msg_export_var, 'export_type', 'csv_config')
            )
        ))

        # Export CSV path rule
        self.add_rule(_make_identity_rule(
            'export_csv_path', STRING_TYPE,
            rhs=Sequence((_lp, LitTerminal('path'), NamedTerminal('STRING', STRING_TYPE), _rp))
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

        self.add_rule(_make_identity_rule(
            'export_csv_columns', ListType(_export_csv_column_type),
            rhs=Sequence((
                _lp, LitTerminal('columns'),
                Star(Nonterminal('export_csv_column', _export_csv_column_type)),
                _rp
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
            construct_action=Lambda([Var('symbol', STRING_TYPE)], _var_type, _msg('logic', 'Var', Var('symbol', STRING_TYPE))),
            deconstruct_action=Lambda(
                [Var('msg', _var_type)],
                OptionType(STRING_TYPE),
                make_some(make_get_field(Var('msg', _var_type), Lit('symbol')))
            )
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

    def _add_type_rules(self) -> None:
        """Add rules for type literals."""

        def _make_simple_type_rule(keyword: str, message_name: str) -> Rule:
            """Create a rule for a simple type with no parameters."""
            lhs_name = message_name[0].lower() + message_name[1:]  # e.g., 'UnspecifiedType' -> 'unspecifiedType'
            lhs_name = lhs_name.replace('Type', '_type')  # e.g., 'unspecifiedType' -> 'unspecified_type'
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
                rhs=Sequence((_lp, LitTerminal(op)) + rhs_terms + (_rp,)),
                construct_action=Lambda(
                    params,
                    _primitive_type,
                    _msg('logic', 'Primitive', Lit(prim), *wrapped_args)
                ),
                deconstruct_action=Lambda(
                    [msg_var],
                    OptionType(TupleType([_term_type] * arity)),
                    IfElse(
                        make_equal(make_get_field(msg_var, _lit_op), Lit(prim)),
                        make_some(make_tuple(*extracted_args)),
                        Lit(None)
                    )
                )
            )

            # The wrapper rule (e.g., primitive -> eq)
            wrapper_rule = Rule(
                lhs=_primitive_nt,
                rhs=op_nt,
                construct_action=Lambda([Var('op', _primitive_type)], _primitive_type, Var('op', _primitive_type)),
                deconstruct_action=Lambda(
                    [msg_var],
                    OptionType(_primitive_type),
                    IfElse(
                        make_equal(make_get_field(msg_var, _lit_op), Lit(prim)),
                        make_some(msg_var),
                        Lit(None)
                    )
                )
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
                    _lp, LitTerminal(keyword),
                    Option(_name_nt),
                    _relation_id_nt,
                    _rp
                )),
                construct_action=Lambda(
                    [name_var, Var('relation_id', _relation_id_type)],
                    msg_type,
                    _msg('transactions', message_name,
                        make_unwrap_option_or(name_var, Lit(keyword)),
                        Var('relation_id', _relation_id_type))
                ),
                deconstruct_action=Lambda(
                    [msg_var],
                    OptionType(TupleType([OptionType(STRING_TYPE), _relation_id_type])),
                    make_some(make_tuple(
                        make_some(make_get_field(msg_var, Lit('name'))),
                        make_get_field(msg_var, Lit('relation_id'))
                    ))
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
                _lp, LitTerminal('exists'),
                _bindings_nt,
                _formula_nt,
                _rp
            )),
            construct_action=Lambda(
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
            ),
            deconstruct_action=Lambda(
                [Var('msg', _exists_type)],
                OptionType(TupleType([_bindings_type, _formula_type])),
                Call(Builtin('deconstruct_exists'), [Var('msg', _exists_type)])
            )
        ))


def get_builtin_rules() -> Dict[Nonterminal, Tuple[List[Rule], bool]]:
    """Return dict mapping nonterminals to (rules, is_final).

    is_final=True means auto-generation should not add more rules for this nonterminal.
    """
    return BuiltinRules().get_builtin_rules()
