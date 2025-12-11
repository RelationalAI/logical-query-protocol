"""Grammar generation from protobuf specifications.

This module provides the GrammarGenerator class which converts protobuf
message definitions into grammar rules with semantic actions.
"""
import re
from typing import Callable, Dict, List, Optional, Set, Tuple
from .grammar import Grammar, Rule, Token, Rhs, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence
from .target import Lambda, Call, Var, Symbol, Let, Lit, IfElse, Builtin, Constructor, BaseType, MessageType, OptionType, ListType, FunctionType, TupleType
from .proto_ast import ProtoMessage, ProtoField, PRIMITIVE_TYPES
from .proto_parser import ProtoParser

_any_type = BaseType("Any")

# Mapping from protobuf primitive types to base type names
_PRIMITIVE_TO_BASE_TYPE = {
    'string': 'String',
    'int32': 'Int64',
    'int64': 'Int64',
    'uint32': 'Int64',
    'uint64': 'Int64',
    'fixed64': 'Int64',
    'bool': 'Boolean',
    'double': 'Float64',
    'float': 'Float64',
    'bytes': 'String',
}

class GrammarGenerator:
    """Generator for grammars from protobuf specifications."""

    def __init__(self, parser: ProtoParser, verbose: bool=False):
        self.parser = parser
        self.final_rules: Set[str] = set()
        self.generated_rules: Set[str] = set()
        self.expected_unreachable: Set[Nonterminal] = set()
        self.grammar = Grammar(start=Nonterminal('transaction', MessageType('Transaction')))
        self.verbose = verbose
        self.inline_fields: Set[Tuple[str, str]] = {
            ("Script", "constructs"),
            ("Conjunction", "args"),
            ("Disjunction", "args"),
            ("Fragment", "declarations"),
            ("Context", "relations"),
            ("Sync", "fragments"),
            ("Algorithm", "global"),
            ("Attribute", "args"),
            ("Atom", "terms"),
            ("Primitive", "terms"),
            ("RelAtom", "terms"),
            ("Pragma", "terms"),
            ("Exists", "body"),
        }
        self.rule_literal_renames: Dict[str, str] = {
            "monoid_def": "monoid",
            "monus_def": "monus",
            "conjunction": "and",
            "disjunction": "or",
        }
        self.rule_rewrites: Dict[str, Callable[[Rule], Rule]] = self._init_rule_rewrites()

    def _generate_action(self, message_name: str, rhs_elements: List[Rhs], field_names: Optional[List[str]]=None, field_types: Optional[List[str]]=None) -> Lambda:
        """Generate semantic action to construct protobuf message from parsed elements."""

        # Create parameters for all RHS elements
        param_names = []
        param_types = []
        field_idx = 0
        for elem in rhs_elements:
            if isinstance(elem, LitTerminal):
                pass
            else:
                if field_names and field_idx < len(field_names):
                    param_names.append(field_names[field_idx])
                else:
                    assert False, f'Too many params for {message_name} semantic action'
                param_types.append(elem.target_type())
                field_idx += 1
        args = []
        for name, param_type in zip(param_names, param_types):
            var = Var(name, param_type)
            if isinstance(param_type, OptionType) and isinstance(param_type.element_type, ListType):
                # Flatten Option[List[T]] to List[T]
                args.append(Call(Builtin('unwrap_option_or'), [var, Call(Builtin('make_list'), [])]))
            else:
                args.append(var)
        body = Call(Constructor(message_name), args)
        params = [Var(name, param_type) for name, param_type in zip(param_names, param_types)]
        return Lambda(params=params, return_type=MessageType(message_name), body=body)

    def _next_param_name(self, idx: int) -> str:
        """Generate parameter name for lambda (a, b, c, ...)."""
        if idx < 26:
            return chr(ord('a') + idx)
        return f'x{idx}'

    def _get_type_for_name(self, type_name: str):
        """Get the appropriate type (BaseType or MessageType) for a given type name."""
        if self._is_primitive_type(type_name):
            base_type_name = _PRIMITIVE_TO_BASE_TYPE[type_name]
            return BaseType(base_type_name)
        elif self._is_message_type(type_name):
            return MessageType(type_name)
        else:
            assert False, f'Unknown type: {type_name}'

    def _add_rule(self, rule: Rule) -> None:
        """Add a rule to the grammar."""
        rewrite = self.rule_rewrites.get(rule.lhs.name)
        if rewrite:
            rule = rewrite(rule)
        self.grammar.add_rule(rule)

    def _init_rule_rewrites(self) -> Dict[str, Callable[[Rule], Rule]]:
        """Initialize rule rewrite functions."""

        def rewrite_string_to_name_optional(rule: Rule) -> Rule:
            """Replace STRING with name? in output and abort rules."""
            if isinstance(rule.rhs, Sequence):
                new_elements = []
                for symbol in rule.rhs.elements:
                    if isinstance(symbol, NamedTerminal) and symbol.name == 'STRING':
                        new_elements.append(Option(Nonterminal('name', symbol.type)))
                    else:
                        new_elements.append(symbol)
                return Rule(lhs=rule.lhs, rhs=Sequence(new_elements), action=rule.action, source_type=rule.source_type)
            return rule

        def rewrite_string_to_name(rule: Rule) -> Rule:
            """Replace STRING with name."""
            if isinstance(rule.rhs, Sequence):
                new_elements = []
                for symbol in rule.rhs.elements:
                    if isinstance(symbol, NamedTerminal) and symbol.name == 'STRING':
                        new_elements.append(Nonterminal('name', symbol.type))
                    else:
                        new_elements.append(symbol)
                return Rule(lhs=rule.lhs, rhs=Sequence(new_elements), action=rule.action, source_type=rule.source_type)
            return rule

        def rewrite_fragment_remove_debug_info(rule: Rule) -> Rule:
            """Remove debug_info from fragment rules."""
            if isinstance(rule.rhs, Sequence):
                new_elements = []
                for symbol in rule.rhs.elements:
                    if isinstance(symbol, Option) and isinstance(symbol.rhs, Nonterminal) and (symbol.rhs.name == 'debug_info') or (isinstance(symbol, Nonterminal) and symbol.name == 'debug_info'):
                        continue
                    new_elements.append(symbol)
                new_params = list(rule.action.params[:-1])
                new_action = Lambda(params=new_params, return_type=rule.action.return_type, body=rule.action.body)
                return Rule(lhs=rule.lhs, rhs=Sequence(new_elements), action=new_action, source_type=rule.source_type)
            return rule

        def rewrite_terms_optional_to_star_term(rule: Rule) -> Rule:
            """Replace terms? with term*."""
            if isinstance(rule.rhs, Sequence):
                new_elements = []
                for symbol in rule.rhs.elements:
                    if isinstance(symbol, Option) and isinstance(symbol.rhs, Nonterminal) and (symbol.rhs.name == 'terms'):
                        new_elements.append(Star(Nonterminal('term', symbol.rhs.type)))
                    else:
                        new_elements.append(symbol)
                return Rule(lhs=rule.lhs, rhs=Sequence(new_elements), action=rule.action, source_type=rule.source_type)
            return rule

        def rewrite_terms_optional_to_star_relterm(rule: Rule) -> Rule:
            """Replace terms? with relterm* and STRING with name."""
            if isinstance(rule.rhs, Sequence):
                new_elements = []
                for symbol in rule.rhs.elements:
                    if isinstance(symbol, Option) and isinstance(symbol.rhs, Nonterminal) and (symbol.rhs.name == 'terms'):
                        new_elements.append(Star(Nonterminal('relterm', symbol.rhs.type)))
                    elif isinstance(symbol, NamedTerminal) and symbol.name == 'STRING':
                        new_elements.append(Nonterminal('name', symbol.type))
                    else:
                        new_elements.append(symbol)
                return Rule(lhs=rule.lhs, rhs=Sequence(new_elements), action=rule.action, source_type=rule.source_type)
            return rule

        def rewrite_primitive_rule(rule: Rule) -> Rule:
            """Replace STRING with name and term* with relterm* in primitive rules."""
            if isinstance(rule.rhs, Sequence) and len(rule.rhs.elements) >= 2:
                if isinstance(rule.rhs.elements[0], LitTerminal) and rule.rhs.elements[0].name == '(' and isinstance(rule.rhs.elements[1], LitTerminal) and (rule.rhs.elements[1].name == 'primitive'):
                    new_elements = []
                    for symbol in rule.rhs.elements:
                        if isinstance(symbol, NamedTerminal) and symbol.name == 'STRING':
                            new_elements.append(Nonterminal('name', symbol.type))
                        elif isinstance(symbol, Star) and isinstance(symbol.rhs, Nonterminal) and (symbol.rhs.name == 'term'):
                            new_elements.append(Star(Nonterminal('relterm', symbol.rhs.type)))
                        else:
                            new_elements.append(symbol)
                    return Rule(lhs=rule.lhs, rhs=Sequence(new_elements), action=rule.action, source_type=rule.source_type)
            return rule

        def rewrite_exists(rule: Rule) -> Rule:
            """Rewrite exists rule to use bindings and formula instead of abstraction."""
            if isinstance(rule.rhs, Sequence):
                new_elements = []
                abstraction_found = False
                for elem in rule.rhs.elements:
                    if isinstance(elem, Nonterminal) and elem.name == 'abstraction':
                        new_elements.append(Nonterminal('bindings', TupleType([ListType(MessageType('Binding')), ListType(MessageType('Binding'))])))
                        new_elements.append(Nonterminal('formula', MessageType('Formula')))
                        abstraction_found = True
                    else:
                        new_elements.append(elem)
                if abstraction_found:
                    # Update action to take bindings and formula instead of abstraction
                    # Original action: lambda body: Constructor('Exists')(body)
                    # New action: lambda bindings, formula: Constructor('Exists')(Constructor('Abstraction')(bindings, formula))
                    new_params = []
                    for i, param in enumerate(rule.action.params):
                        if param.name != 'abstraction' and param.name != 'x' and (param.name != 'body'):
                            new_params.append(param)
                        else:
                            new_params.append(Var('bindings', TupleType([ListType(MessageType('Binding')), ListType(MessageType('Binding'))])))
                            new_params.append(Var('formula', MessageType('Formula')))
                    abstraction_construction = Call(Constructor('Abstraction'), [Call(Builtin('list_concat'), [Call(Builtin('fst'), [Var('bindings', TupleType([ListType(MessageType('Binding')), ListType(MessageType('Binding'))]))]), Call(Builtin('snd'), [Var('bindings', TupleType([ListType(MessageType('Binding')), ListType(MessageType('Binding'))]))])]), Var('formula', MessageType('Formula'))])
                    new_action = Lambda(params=new_params, return_type=rule.action.return_type, body=Call(Constructor('Exists'), [abstraction_construction]))
                    return Rule(lhs=rule.lhs, rhs=Sequence(new_elements), action=new_action, source_type=rule.source_type)
            return rule

        def rewrite_compute_value_arity(rule: Rule) -> Rule:
            """Rewrite `body ... INT` to `body_with_arity ...` where body is an Abstraction field."""
            if isinstance(rule.rhs, Sequence) and len(rule.rhs.elements) >= 2:
                new_elements = list(rule.rhs.elements)
                abstraction_idx = None
                int_idx = None
                for i, elem in enumerate(new_elements):
                    if isinstance(elem, Nonterminal) and (elem.name == 'abstraction' or elem.name == 'body'):
                        abstraction_idx = i
                    elif isinstance(elem, NamedTerminal) and elem.name in ('INT', 'NUMBER'):
                        int_idx = i
                if abstraction_idx is not None and int_idx is not None:
                    elem = new_elements[abstraction_idx]
                    # abstraction_with_arity returns a tuple (Abstraction, Int64)
                    tuple_type = TupleType([elem.type, BaseType('Int64')])
                    new_elements[abstraction_idx] = Nonterminal('abstraction_with_arity', tuple_type)
                    new_elements.pop(int_idx)
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
                        if isinstance(expr, Var):
                            if expr.name == old_abstraction_param.name:
                                return Call(Builtin('fst'), [new_abstraction_param])
                            elif expr.name == rule.action.params[-1].name:
                                return Call(Builtin('snd'), [new_abstraction_param])
                            return expr
                        elif isinstance(expr, Call):
                            return Call(expr.func, [replace_vars(arg) for arg in expr.args])
                        elif isinstance(expr, Let):
                            return Let(expr.var, replace_vars(expr.value), replace_vars(expr.body))
                        return expr

                    new_body = replace_vars(rule.action.body)
                    new_action = Lambda(params=new_params, return_type=rule.action.return_type, body=new_body)
                    return Rule(lhs=rule.lhs, rhs=Sequence(new_elements), action=new_action, source_type=rule.source_type)
            return rule

        def rewrite_relatom_rule(rule: Rule) -> Rule:
            """Replace STRING with name and terms? with relterm*."""
            if isinstance(rule.rhs, Sequence):
                new_elements = []
                for symbol in rule.rhs.elements:
                    if isinstance(symbol, NamedTerminal) and symbol.name == 'STRING':
                        new_elements.append(Nonterminal('name', symbol.type))
                    elif isinstance(symbol, Option) and isinstance(symbol.rhs, Nonterminal) and (symbol.rhs.name == 'terms'):
                        new_elements.append(Star(Nonterminal('relterm', symbol.rhs.type)))
                    else:
                        new_elements.append(symbol)
                return Rule(lhs=rule.lhs, rhs=Sequence(new_elements), action=rule.action, source_type=rule.source_type)
            return rule

        def rewrite_attribute_rule(rule: Rule) -> Rule:
            """Replace STRING with name and args? with value*."""
            if isinstance(rule.rhs, Sequence):
                new_elements = []
                for symbol in rule.rhs.elements:
                    if isinstance(symbol, NamedTerminal) and symbol.name == 'STRING':
                        new_elements.append(Nonterminal('name', symbol.type))
                    elif isinstance(symbol, Option) and isinstance(symbol.rhs, Nonterminal) and (symbol.rhs.name == 'args'):
                        new_elements.append(Star(Nonterminal('value', symbol.rhs.type)))
                    else:
                        new_elements.append(symbol)
                return Rule(lhs=rule.lhs, rhs=Sequence(new_elements), action=rule.action, source_type=rule.source_type)
            return rule

        def compose(*funcs: Callable[[Rule], Rule]) -> Callable[[Rule], Rule]:
            """Compose multiple rewrite functions."""

            def composed(rule: Rule) -> Rule:
                for f in funcs:
                    rule = f(rule)
                return rule
            return composed

        return {
            'output': rewrite_string_to_name_optional,
            'abort': rewrite_string_to_name_optional,
            'ffi': compose(rewrite_string_to_name, rewrite_terms_optional_to_star_term),
            'pragma': compose(rewrite_string_to_name, rewrite_terms_optional_to_star_term),
            'fragment': rewrite_fragment_remove_debug_info,
            'atom': rewrite_terms_optional_to_star_term,
            'rel_atom': rewrite_terms_optional_to_star_relterm,
            'primitive': rewrite_primitive_rule,
            'exists': rewrite_exists,
            'upsert': rewrite_compute_value_arity,
            'monoid_def': rewrite_compute_value_arity,
            'monus_def': rewrite_compute_value_arity,
            'relatom': rewrite_relatom_rule,
            'attribute': rewrite_attribute_rule,
        }

    def generate(self) -> Grammar:
        """Generate complete grammar with prepopulated and message-derived rules."""

        self._add_all_prepopulated_rules()

        for message_name in sorted(self.parser.messages.keys()):
            self._generate_message_rule(message_name)

        # Add the tokens to scan for. The order here matters! We go from most specific to least specific.
        # Specifically, we want to be sure to return INT128 before INT and DECIMAL before FLOAT, and SYMBOL last.
        # The semantic action for these is defined in the target-specific lexer code. Here we just define value types.
        self.grammar.tokens.append(Token("STRING", '"(?:[^"\\\\]|\\\\.)*"', BaseType("String")))
        self.grammar.tokens.append(Token("INT128", '[-]?\\d+i128', MessageType("Int128Value")))
        self.grammar.tokens.append(Token("INT", '[-]?\\d+', BaseType("Int64")))
        self.grammar.tokens.append(Token("UINT128", '0x[0-9a-fA-F]+', MessageType("UInt128Value")))
        self.grammar.tokens.append(Token("DECIMAL", '[-]?\\d+\\.\\d+d\\d+', MessageType("DecimalValue")))
        self.grammar.tokens.append(Token("FLOAT", '(?:[-]?\\d+\\.\\d+|inf|nan)', BaseType("Float64")))
        self.grammar.tokens.append(Token("SYMBOL", '[a-zA-Z_][a-zA-Z0-9_.-]*', BaseType("String")))

        self._post_process_grammar()
        return self.grammar

    def _add_all_prepopulated_rules(self) -> None:
        """Add manually-crafted rules that should not be auto-generated."""

        def add_rule(rule: Rule, is_final: bool=True) -> None:
            if is_final:
                self.final_rules.add(rule.lhs.name)
            assert rule.action is not None
            self.grammar.add_rule(rule)
        add_rule(Rule(lhs=Nonterminal('value', MessageType('Value')), rhs=Sequence((Nonterminal('date', MessageType('DateValue')),)), action=Lambda([Var('value', MessageType('DateValue'))], MessageType('Value'), Call(Constructor('Value'), [Call(Constructor('OneOf'), [Symbol('date_value'), Var('value', MessageType('DateValue'))])]))))
        add_rule(Rule(lhs=Nonterminal('value', MessageType('Value')), rhs=Sequence((Nonterminal('datetime', MessageType('DateTimeValue')),)), action=Lambda([Var('value', MessageType('DateTimeValue'))], MessageType('Value'), Call(Constructor('Value'), [Call(Constructor('OneOf'), [Symbol('datetime_value'), Var('value', MessageType('DateTimeValue'))])]))))
        add_rule(Rule(lhs=Nonterminal('value', MessageType('Value')), rhs=Sequence((NamedTerminal('STRING', BaseType('String')),)), action=Lambda([Var('value', BaseType('String'))], MessageType('Value'), Call(Constructor('Value'), [Call(Constructor('OneOf'), [Symbol('string_value'), Var('value', BaseType('String'))])]))))
        add_rule(Rule(lhs=Nonterminal('value', MessageType('Value')), rhs=Sequence((NamedTerminal('INT', BaseType('Int64')),)), action=Lambda([Var('value', BaseType('Int64'))], MessageType('Value'), Call(Constructor('Value'), [Call(Constructor('OneOf'), [Symbol('int_value'), Var('value', BaseType('Int64'))])]))))
        add_rule(Rule(lhs=Nonterminal('value', MessageType('Value')), rhs=Sequence((NamedTerminal('FLOAT', BaseType('Float64')),)), action=Lambda([Var('value', BaseType('Float64'))], MessageType('Value'), Call(Constructor('Value'), [Call(Constructor('OneOf'), [Symbol('float_value'), Var('value', BaseType('Float64'))])]))))
        add_rule(Rule(lhs=Nonterminal('value', MessageType('Value')), rhs=Sequence((NamedTerminal('UINT128', MessageType('UInt128Value')),)), action=Lambda([Var('value', MessageType('UInt128Value'))], MessageType('Value'), Call(Constructor('Value'), [Call(Constructor('OneOf'), [Symbol('uint128_value'), Var('value', MessageType('UInt128Value'))])]))))
        add_rule(Rule(lhs=Nonterminal('value', MessageType('Value')), rhs=Sequence((NamedTerminal('INT128', MessageType('Int128Value')),)), action=Lambda([Var('value', MessageType('Int128Value'))], MessageType('Value'), Call(Constructor('Value'), [Call(Constructor('OneOf'), [Symbol('int128_value'), Var('value', MessageType('Int128Value'))])]))))
        add_rule(Rule(lhs=Nonterminal('value', MessageType('Value')), rhs=Sequence((NamedTerminal('DECIMAL', MessageType('DecimalValue')),)), action=Lambda([Var('value', MessageType('DecimalValue'))], MessageType('Value'), Call(Constructor('Value'), [Call(Constructor('OneOf'), [Symbol('decimal_value'), Var('value', MessageType('DecimalValue'))])]))))
        add_rule(Rule(lhs=Nonterminal('value', MessageType('Value')), rhs=Sequence((LitTerminal('missing'),)), action=Lambda([], MessageType('Value'), Call(Constructor('Value'), [Call(Constructor('OneOf'), [Symbol('missing_value'), Call(Constructor('MissingValue'), [])])]))))
        add_rule(Rule(lhs=Nonterminal('value', MessageType('Value')), rhs=Sequence((LitTerminal('true'),)), action=Lambda([], MessageType('Value'), Call(Constructor('Value'), [Call(Constructor('OneOf'), [Symbol('boolean_value'), Lit(True)])]))))
        add_rule(Rule(lhs=Nonterminal('value', MessageType('Value')), rhs=Sequence((LitTerminal('false'),)), action=Lambda([], MessageType('Value'), Call(Constructor('Value'), [Call(Constructor('OneOf'), [Symbol('boolean_value'), Lit(False)])]))))
        add_rule(Rule(lhs=Nonterminal('date', MessageType('DateValue')), rhs=Sequence((LitTerminal('('), LitTerminal('date'), NamedTerminal('INT', BaseType('Int64')), NamedTerminal('INT', BaseType('Int64')), NamedTerminal('INT', BaseType('Int64')), LitTerminal(')'))), action=Lambda([Var('year', BaseType('Int64')), Var('month', BaseType('Int64')), Var('day', BaseType('Int64'))], MessageType('DateValue'), Call(Constructor('DateValue'), [Var('year', BaseType('Int64')), Var('month', BaseType('Int64')), Var('day', BaseType('Int64'))]))))
        add_rule(Rule(lhs=Nonterminal('datetime', MessageType('DateTimeValue')), rhs=Sequence((LitTerminal('('), LitTerminal('datetime'), NamedTerminal('INT', BaseType('Int64')), NamedTerminal('INT', BaseType('Int64')), NamedTerminal('INT', BaseType('Int64')), NamedTerminal('INT', BaseType('Int64')), NamedTerminal('INT', BaseType('Int64')), NamedTerminal('INT', BaseType('Int64')), Option(NamedTerminal('INT', BaseType('Int64'))), LitTerminal(')'))), action=Lambda([Var('year', BaseType('Int64')), Var('month', BaseType('Int64')), Var('day', BaseType('Int64')), Var('hour', BaseType('Int64')), Var('minute', BaseType('Int64')), Var('second', BaseType('Int64')), Var('microsecond', OptionType(BaseType('Int64')))], MessageType('DateTimeValue'), Call(Constructor('DateTimeValue'), [Var('year', BaseType('Int64')), Var('month', BaseType('Int64')), Var('day', BaseType('Int64')), Var('hour', BaseType('Int64')), Var('minute', BaseType('Int64')), Var('second', BaseType('Int64')), IfElse(Call(Builtin('is_none'), [Var('microsecond', OptionType(BaseType('Int64')))]), Lit(0), Call(Builtin('some'), [Var('microsecond', OptionType(BaseType('Int64')))]))]))))
        add_rule(Rule(lhs=Nonterminal('config_dict', ListType(TupleType([BaseType('String'), MessageType('Value')]))), rhs=Sequence((LitTerminal('{'), Star(Nonterminal('config_key_value', TupleType([BaseType('String'), MessageType('Value')]))), LitTerminal('}'))), action=Lambda([Var('config_key_value', ListType(TupleType([BaseType('String'), MessageType('Value')])))], return_type=ListType(TupleType([BaseType('String'), MessageType('Value')])), body=Var('config_key_value', ListType(TupleType([BaseType('String'), MessageType('Value')]))))))
        add_rule(Rule(lhs=Nonterminal('config_key_value', TupleType([BaseType('String'), MessageType('Value')])), rhs=Sequence((LitTerminal(':'), NamedTerminal('SYMBOL', BaseType('String')), Nonterminal('value', MessageType('Value')))), action=Lambda([Var('symbol', BaseType('String')), Var('value', MessageType('Value'))], TupleType([BaseType('String'), MessageType('Value')]), Call(Builtin('Tuple'), [Var('symbol', BaseType('String')), Var('value', MessageType('Value'))]))))
        add_rule(Rule(lhs=Nonterminal('transaction', MessageType('Transaction')), rhs=Sequence((LitTerminal('('), LitTerminal('transaction'), Option(Nonterminal('configure', MessageType('Configure'))), Option(Nonterminal('sync', MessageType('Sync'))), Star(Nonterminal('epoch', MessageType('Epoch'))), LitTerminal(')'))), action=Lambda([Var('configure', OptionType(MessageType('Configure'))), Var('sync', OptionType(MessageType('Sync'))), Var('epochs', ListType(MessageType('Epoch')))], MessageType('Transaction'), Call(Constructor('Transaction'), [Var('epochs', ListType(MessageType('Epoch'))), Var('configure', OptionType(MessageType('Configure'))), Var('sync', OptionType(MessageType('Sync')))]))))
        add_rule(Rule(lhs=Nonterminal('bindings', TupleType([ListType(MessageType('Binding')), ListType(MessageType('Binding'))])), rhs=Sequence((LitTerminal('['), Star(Nonterminal('binding', MessageType('Binding'))), Option(Nonterminal('value_bindings', ListType(MessageType('Binding')))), LitTerminal(']'))), action=Lambda([Var('keys', ListType(MessageType('Binding'))), Var('values', OptionType(ListType(MessageType('Binding'))))], TupleType([ListType(MessageType('Binding')), ListType(MessageType('Binding'))]), Call(Builtin('Tuple'), [Var('keys', ListType(MessageType('Binding'))), Var('values', OptionType(ListType(MessageType('Binding'))))]))))
        add_rule(Rule(lhs=Nonterminal('value_bindings', ListType(MessageType('Binding'))), rhs=Sequence((LitTerminal('|'), Star(Nonterminal('binding', MessageType('Binding'))))), action=Lambda([Var('values', ListType(MessageType('Binding')))], ListType(MessageType('Binding')), Var('values', ListType(MessageType('Binding'))))))
        add_rule(Rule(lhs=Nonterminal('binding', MessageType('Binding')), rhs=Sequence((NamedTerminal('SYMBOL', BaseType('String')), LitTerminal('::'), Nonterminal('type', MessageType('Type')))), action=Lambda([Var('symbol', BaseType('String')), Var('type', MessageType('Type'))], MessageType('Binding'), Call(Constructor('Binding'), [Call(Constructor('Var'), [Var('symbol', BaseType('String'))]), Var('type', MessageType('Type'))]))))
        add_rule(Rule(lhs=Nonterminal('abstraction_with_arity', TupleType([MessageType('Abstraction'), BaseType('Int64')])), rhs=Sequence((LitTerminal('('), Nonterminal('bindings', TupleType([ListType(MessageType('Binding')), ListType(MessageType('Binding'))])), Nonterminal('formula', MessageType('Formula')), LitTerminal(')'))), action=Lambda(params=[Var('bindings', TupleType([ListType(MessageType('Binding')), ListType(MessageType('Binding'))])), Var('formula', MessageType('Formula'))], return_type=TupleType([MessageType('Abstraction'), BaseType('Int64')]), body=Call(Builtin('Tuple'), [Call(Constructor('Abstraction'), [Call(Builtin('list_concat'), [Call(Builtin('fst'), [Var('bindings', TupleType([ListType(MessageType('Binding')), ListType(MessageType('Binding'))]))]), Call(Builtin('snd'), [Var('bindings', TupleType([ListType(MessageType('Binding')), ListType(MessageType('Binding'))]))])]), Var('formula', MessageType('Formula'))]), Call(Builtin('length'), [Call(Builtin('snd'), [Var('bindings', TupleType([ListType(MessageType('Binding')), ListType(MessageType('Binding'))]))])])]))))
        add_rule(Rule(lhs=Nonterminal('abstraction', MessageType('Abstraction')), rhs=Sequence((LitTerminal('('), Nonterminal('bindings', TupleType([ListType(MessageType('Binding')), ListType(MessageType('Binding'))])), Nonterminal('formula', MessageType('Formula')), LitTerminal(')'))), action=Lambda(params=[Var('bindings', TupleType([ListType(MessageType('Binding')), ListType(MessageType('Binding'))])), Var('formula', MessageType('Formula'))], return_type=MessageType('Abstraction'), body=Call(Constructor('Abstraction'), [Call(Builtin('list_concat'), [Call(Builtin('fst'), [Var('bindings', TupleType([ListType(MessageType('Binding')), ListType(MessageType('Binding'))]))]), Call(Builtin('snd'), [Var('bindings', TupleType([ListType(MessageType('Binding')), ListType(MessageType('Binding'))]))])]), Var('formula', MessageType('Formula'))]))))
        add_rule(Rule(lhs=Nonterminal('name', BaseType('String')), rhs=Sequence((LitTerminal(':'), NamedTerminal('SYMBOL', BaseType('String')))), action=Lambda([Var('symbol', BaseType('String'))], BaseType('String'), Var('symbol', BaseType('String')))))
        add_rule(Rule(lhs=Nonterminal('monoid', MessageType('Monoid')), rhs=Sequence((Nonterminal('type', MessageType('Type')), LitTerminal('::'), Nonterminal('monoid_op', FunctionType([MessageType('Type')], MessageType('Monoid'))))), action=Lambda([Var('type', MessageType('Type')), Var('op', FunctionType([MessageType('Type')], MessageType('Monoid')))], return_type=MessageType('Monoid'), body=Call(Var('op', FunctionType([MessageType('Type')], MessageType('Monoid'))), [Var('type', MessageType('Type'))]))))
        add_rule(Rule(lhs=Nonterminal('monoid_op', FunctionType([MessageType('Type')], MessageType('Monoid'))), rhs=LitTerminal('OR'), action=Lambda([], return_type=FunctionType([MessageType('Type')], MessageType('Monoid')), body=Lambda([Var('type', MessageType('Type'))], return_type=MessageType('Monoid'), body=Call(Constructor('Monoid'), [Call(Constructor('OneOf'), [Symbol('or_monoid'), Call(Constructor('OrMonoid'), [])])])))))
        add_rule(Rule(lhs=Nonterminal('monoid_op', FunctionType([MessageType('Type')], MessageType('Monoid'))), rhs=LitTerminal('MIN'), action=Lambda([], return_type=FunctionType([MessageType('Type')], MessageType('Monoid')), body=Lambda([Var('type', MessageType('Type'))], return_type=MessageType('Monoid'), body=Call(Constructor('Monoid'), [Call(Constructor('OneOf'), [Symbol('min_monoid'), Call(Constructor('MinMonoid'), [Var('type', MessageType('Type'))])])])))))
        add_rule(Rule(lhs=Nonterminal('monoid_op', FunctionType([MessageType('Type')], MessageType('Monoid'))), rhs=LitTerminal('MAX'), action=Lambda([], return_type=FunctionType([MessageType('Type')], MessageType('Monoid')), body=Lambda([Var('type', MessageType('Type'))], return_type=MessageType('Monoid'), body=Call(Constructor('Monoid'), [Call(Constructor('OneOf'), [Symbol('max_monoid'), Call(Constructor('MaxMonoid'), [Var('type', MessageType('Type'))])])])))))
        add_rule(Rule(lhs=Nonterminal('monoid_op', FunctionType([MessageType('Type')], MessageType('Monoid'))), rhs=LitTerminal('SUM'), action=Lambda([], return_type=FunctionType([MessageType('Type')], MessageType('Monoid')), body=Lambda([Var('type', MessageType('Type'))], return_type=MessageType('Monoid'), body=Call(Constructor('Monoid'), [Call(Constructor('OneOf'), [Symbol('sum'), Call(Constructor('SumMonoid'), [Var('type', MessageType('Type'))])])])))))
        add_rule(Rule(lhs=Nonterminal('configure', MessageType('Configure')), rhs=Sequence((LitTerminal('('), LitTerminal('configure'), Nonterminal('config_dict', ListType(TupleType([BaseType('String'), MessageType('Value')]))), LitTerminal(')'))), action=Lambda([Var('config_dict', ListType(TupleType([BaseType('String'), MessageType('Value')])))], return_type=MessageType('Configure'), body=Call(Constructor('Configure'), [Var('config_dict', ListType(TupleType([BaseType('String'), MessageType('Value')])))]))))
        add_rule(Rule(lhs=Nonterminal('true', MessageType('Conjunction')), rhs=Sequence((LitTerminal('('), LitTerminal('true'), LitTerminal(')'))), action=Lambda([], MessageType('Conjunction'), Call(Constructor('Conjunction'), [Call(Builtin('make_list'), [])]))))
        add_rule(Rule(lhs=Nonterminal('false', MessageType('Disjunction')), rhs=Sequence((LitTerminal('('), LitTerminal('false'), LitTerminal(')'))), action=Lambda([], MessageType('Disjunction'), Call(Constructor('Disjunction'), [Call(Builtin('make_list'), [])]))))
        add_rule(Rule(lhs=Nonterminal('formula', MessageType('Formula')), rhs=Sequence((Nonterminal('true', MessageType('Conjunction')),)), action=Lambda([Var('value', MessageType('Conjunction'))], MessageType('Formula'), Call(Constructor('Formula'), [Call(Constructor('OneOf'), [Symbol('true'), Var('value', MessageType('Conjunction'))])]))), is_final=False)
        add_rule(Rule(lhs=Nonterminal('formula', MessageType('Formula')), rhs=Sequence((Nonterminal('false', MessageType('Disjunction')),)), action=Lambda([Var('value', MessageType('Disjunction'))], MessageType('Formula'), Call(Constructor('Formula'), [Call(Constructor('OneOf'), [Symbol('false'), Var('value', MessageType('Disjunction'))])]))), is_final=False)
        add_rule(Rule(lhs=Nonterminal('export', MessageType('Export')), rhs=Sequence((LitTerminal('('), LitTerminal('export'), Nonterminal('export_csvconfig', MessageType('ExportCsvConfig')), LitTerminal(')'))), action=Lambda([Var('config', MessageType('ExportCsvConfig'))], MessageType('Export'), Call(Constructor('Export'), [Var('config', MessageType('ExportCsvConfig'))]))))
        add_rule(Rule(lhs=Nonterminal('export_csvconfig', MessageType('ExportCsvConfig')), rhs=Sequence((LitTerminal('('), LitTerminal('export_csvconfig'), Nonterminal('export_path', MessageType('ExportPath')), Nonterminal('export_csvcolumns', ListType(MessageType('ExportCsvColumn'))), Nonterminal('config_dict', ListType(TupleType([BaseType('String'), MessageType('Value')]))), LitTerminal(')'))), action=Lambda([Var('path', MessageType('ExportPath')), Var('columns', ListType(MessageType('ExportCsvColumn'))), Var('config', ListType(TupleType([BaseType('String'), MessageType('Value')])))], MessageType('ExportCsvConfig'), Call(Builtin('export_csv_config'), [Var('path', MessageType('ExportPath')), Var('columns', ListType(MessageType('ExportCsvColumn'))), Var('config', ListType(TupleType([BaseType('String'), MessageType('Value')])))]))))
        add_rule(Rule(lhs=Nonterminal('export_csvcolumns', ListType(MessageType('ExportCsvColumn'))), rhs=Sequence((LitTerminal('('), LitTerminal('columns'), Star(Nonterminal('export_csvcolumn', MessageType('ExportCsvColumn'))), LitTerminal(')'))), action=Lambda([Var('columns', ListType(MessageType('ExportCsvColumn')))], ListType(MessageType('ExportCsvColumn')), Var('columns', ListType(MessageType('ExportCsvColumn'))))))
        add_rule(Rule(lhs=Nonterminal('export_csvcolumn', MessageType('ExportCsvColumn')), rhs=Sequence((LitTerminal('('), LitTerminal('column'), NamedTerminal('STRING', BaseType('String')), Nonterminal('relation_id', MessageType('RelationId')), LitTerminal(')'))), action=Lambda([Var('name', BaseType('String')), Var('relation_id', MessageType('RelationId'))], MessageType('ExportCsvColumn'), Call(Constructor('ExportCsvColumn'), [Var('name', BaseType('String')), Var('relation_id', MessageType('RelationId'))]))))
        add_rule(Rule(lhs=Nonterminal('export_path', MessageType('ExportPath')), rhs=Sequence((LitTerminal('('), LitTerminal('path'), NamedTerminal('STRING', BaseType('String')), LitTerminal(')'))), action=Lambda([Var('path', BaseType('String'))], return_type=MessageType('ExportPath'), body=Call(Constructor('ExportPath'), [Var('path', BaseType('String'))]))))
        add_rule(Rule(lhs=Nonterminal('var', MessageType('Var')), rhs=Sequence((NamedTerminal('SYMBOL', BaseType('String')),)), action=Lambda([Var('symbol', BaseType('String'))], return_type=MessageType('Var'), body=Call(Constructor('Var'), [Var('symbol', BaseType('String'))]))))
        add_rule(Rule(lhs=Nonterminal('fragment_id', MessageType('FragmentId')), rhs=Sequence((LitTerminal(':'), NamedTerminal('SYMBOL', BaseType('String')))), action=Lambda([Var('symbol', BaseType('String'))], return_type=MessageType('FragmentId'), body=Call(Builtin('fragment_id_from_string'), [Var('symbol', BaseType('String'))]))))
        add_rule(Rule(lhs=Nonterminal('relation_id', MessageType('RelationId')), rhs=Sequence((LitTerminal(':'), NamedTerminal('SYMBOL', BaseType('String')))), action=Lambda([Var('symbol', BaseType('String'))], return_type=MessageType('RelationId'), body=Call(Builtin('relation_id_from_string'), [Var('symbol', BaseType('String'))]))))
        add_rule(Rule(lhs=Nonterminal('relation_id', MessageType('RelationId')), rhs=Sequence((NamedTerminal('INT', BaseType('Int64')),)), action=Lambda([Var('INT', BaseType('Int64'))], return_type=MessageType('RelationId'), body=Call(Builtin('relation_id_from_int'), [Var('INT', BaseType('Int64'))]))))
        add_rule(Rule(lhs=Nonterminal('specialized_value', MessageType('Value')), rhs=Sequence((LitTerminal('#'), Nonterminal('value', MessageType('Value')))), action=Lambda([Var('value', MessageType('Value'))], MessageType('Value'), Var('value', MessageType('Value')))), is_final=True)
        type_rules = {'unspecified_type': (MessageType('UnspecifiedType'), LitTerminal('UNKNOWN'), Lambda([], MessageType('UnspecifiedType'), Call(Constructor('UnspecifiedType'), []))), 'string_type': (MessageType('StringType'), LitTerminal('STRING'), Lambda([], MessageType('StringType'), Call(Constructor('StringType'), []))), 'int_type': (MessageType('IntType'), LitTerminal('INT'), Lambda([], MessageType('IntType'), Call(Constructor('IntType'), []))), 'float_type': (MessageType('FloatType'), LitTerminal('FLOAT'), Lambda([], MessageType('FloatType'), Call(Constructor('FloatType'), []))), 'uint128_type': (MessageType('Uint128Type'), LitTerminal('UINT128'), Lambda([], MessageType('Uint128Type'), Call(Constructor('Uint128Type'), []))), 'int128_type': (MessageType('Int128Type'), LitTerminal('INT128'), Lambda([], MessageType('Int128Type'), Call(Constructor('Int128Type'), []))), 'boolean_type': (MessageType('BooleanType'), LitTerminal('BOOLEAN'), Lambda([], MessageType('BooleanType'), Call(Constructor('BooleanType'), []))), 'date_type': (MessageType('DateType'), LitTerminal('DATE'), Lambda([], MessageType('DateType'), Call(Constructor('DateType'), []))), 'datetime_type': (MessageType('DatetimeType'), LitTerminal('DATETIME'), Lambda([], MessageType('DatetimeType'), Call(Constructor('DatetimeType'), []))), 'missing_type': (MessageType('MissingType'), LitTerminal('MISSING'), Lambda([], MessageType('MissingType'), Call(Constructor('MissingType'), []))), 'decimal_type': (MessageType('DecimalType'), Sequence((LitTerminal('('), LitTerminal('DECIMAL'), NamedTerminal('INT', BaseType('Int64')), NamedTerminal('INT', BaseType('Int64')), LitTerminal(')'))), Lambda([Var('precision', BaseType('Int64')), Var('scale', BaseType('Int64'))], MessageType('DecimalType'), Call(Constructor('DecimalType'), [Var('precision', BaseType('Int64')), Var('scale', BaseType('Int64'))])))}
        for lhs_name, (lhs_type, rhs, action) in type_rules.items():
            add_rule(Rule(lhs=Nonterminal(lhs_name, lhs_type), rhs=rhs, action=action))
        comparison_ops = [('eq', '=', 'rel_primitive_eq'), ('lt', '<', 'rel_primitive_lt'), ('lt_eq', '<=', 'rel_primitive_lt_eq'), ('gt', '>', 'rel_primitive_gt'), ('gt_eq', '>=', 'rel_primitive_gt_eq')]
        for name, op, prim in comparison_ops:
            add_rule(Rule(lhs=Nonterminal(name, MessageType('Primitive')), rhs=Sequence((LitTerminal('('), LitTerminal(op), Nonterminal('term', MessageType('Term')), Nonterminal('term', MessageType('Term')), LitTerminal(')'))), action=Lambda([Var('left', MessageType('Term')), Var('right', MessageType('Term'))], MessageType('Primitive'), Call(Constructor('Primitive'), [Lit(prim), Var('left', MessageType('Term')), Var('right', MessageType('Term'))]))))
        arithmetic_ops = [('add', '+', 'rel_primitive_add'), ('minus', '-', 'rel_primitive_subtract'), ('multiply', '*', 'rel_primitive_multiply'), ('divide', '/', 'rel_primitive_divide')]
        for name, op, prim in arithmetic_ops:
            add_rule(Rule(lhs=Nonterminal(name, MessageType('Primitive')), rhs=Sequence((LitTerminal('('), LitTerminal(op), Nonterminal('term', MessageType('Term')), Nonterminal('term', MessageType('Term')), Nonterminal('term', MessageType('Term')), LitTerminal(')'))), action=Lambda([Var('left', MessageType('Term')), Var('right', MessageType('Term')), Var('result', MessageType('Term'))], MessageType('Primitive'), Call(Constructor('Primitive'), [Lit(prim), Var('left', MessageType('Term')), Var('right', MessageType('Term')), Var('result', MessageType('Term'))]))))
        for name, _op, _prim in comparison_ops + arithmetic_ops:
            add_rule(Rule(lhs=Nonterminal('primitive', MessageType('Primitive')), rhs=Sequence((Nonterminal(name, MessageType('Primitive')),)), action=Lambda([Var('op', MessageType('Primitive'))], MessageType('Primitive'), Var('op', MessageType('Primitive')))), is_final=False)

    def _post_process_grammar(self) -> None:
        """Apply grammar post-processing."""
        self._combine_identical_rules()
        self.expected_unreachable.add(Nonterminal('debug_info', MessageType('DebugInfo')))
        self.expected_unreachable.add(Nonterminal('debug_info_ids', ListType(BaseType('Int64'))))
        self.expected_unreachable.add(Nonterminal('ivmconfig', MessageType('IvmConfig')))
        self.expected_unreachable.add(Nonterminal('min_monoid', MessageType('MinMonoid')))
        self.expected_unreachable.add(Nonterminal('sum_monoid', MessageType('SumMonoid')))
        self.expected_unreachable.add(Nonterminal('max_monoid', MessageType('MaxMonoid')))
        self.expected_unreachable.add(Nonterminal('or_monoid', MessageType('OrMonoid')))
        self.expected_unreachable.add(Nonterminal('date_value', MessageType('DateValue')))
        self.expected_unreachable.add(Nonterminal('datetime_value', MessageType('DateTimeValue')))
        self.expected_unreachable.add(Nonterminal('decimal_value', MessageType('DecimalValue')))
        self.expected_unreachable.add(Nonterminal('int128_value', MessageType('Int128Value')))
        self.expected_unreachable.add(Nonterminal('missing_value', MessageType('MissingValue')))
        self.expected_unreachable.add(Nonterminal('uint128_value', MessageType('UInt128Value')))

    def _combine_identical_rules(self) -> None:
        """Combine rules with identical RHS patterns into a single rule with multiple alternatives."""
        rhs_source_to_lhs: Dict[Tuple[str, Optional[str]], List[Nonterminal]] = {}
        for lhs in self.grammar.rules.keys():
            rules_list = self.grammar.rules[lhs]
            if len(rules_list) == 1:
                rule = rules_list[0]
                rhs_pattern = str(rule.rhs)
                source_type = rule.source_type
                if source_type:
                    key = (rhs_pattern, source_type)
                    if key not in rhs_source_to_lhs:
                        rhs_source_to_lhs[key] = []
                    rhs_source_to_lhs[key].append(lhs)
        rename_map: Dict[Nonterminal, Nonterminal] = {}
        for (rhs_pattern, source_type), lhs_names in rhs_source_to_lhs.items():
            if len(lhs_names) > 1:
                canonical_lhs = self._find_canonical_name(lhs_names)
                for i, lhs_name in enumerate(lhs_names):
                    if i == 0:
                        if canonical_lhs != lhs_name:
                            rename_map[lhs_name] = canonical_lhs
                            old_rules = self.grammar.rules[lhs_name]
                            new_rules = [Rule(lhs=canonical_lhs, rhs=rule.rhs, action=rule.action, source_type=rule.source_type) for rule in old_rules]
                            self.grammar.rules[canonical_lhs] = new_rules
                            del self.grammar.rules[lhs_name]
                    else:
                        rename_map[lhs_name] = canonical_lhs
                        if lhs_name in self.grammar.rules:
                            del self.grammar.rules[lhs_name]
        if rename_map:
            self._apply_renames(rename_map)

    def _find_canonical_name(self, names: List[Nonterminal]) -> Nonterminal:
        """Find canonical name for a group of rules with identical RHS.

        If all names share a common suffix '_foo', use 'foo' as the canonical name.
        Otherwise, use the first name in the list.
        """
        if len(names) < 2:
            return names[0]
        parts = [name.name.split('_') for name in names]
        if all((len(p) > 1 for p in parts)):
            last_parts = [p[-1] for p in parts]
            if len(set(last_parts)) == 1:
                return Nonterminal(last_parts[0], names[0].type)
        return names[0]

    def _apply_renames(self, rename_map: Dict[Nonterminal, Nonterminal]) -> None:
        """Replace all occurrences of old names with new names throughout the grammar."""
        new_rules = {}
        for lhs, rules_list in self.grammar.rules.items():
            new_rules[lhs] = [Rule(lhs=rule.lhs, rhs=self._rename_in_rhs(rule.rhs, rename_map), action=rule.action, source_type=rule.source_type) for rule in rules_list]
        self.grammar.rules = new_rules

    def _rename_in_rhs(self, rhs: Rhs, rename_map: Dict[Nonterminal, Nonterminal]) -> Rhs:
        """Recursively rename nonterminals in RHS, returning new Rhs."""
        if isinstance(rhs, Nonterminal):
            if rhs in rename_map:
                return rename_map[rhs]
            return rhs
        elif isinstance(rhs, Sequence):
            new_elements = tuple(self._rename_in_rhs(elem, rename_map) for elem in rhs.elements)
            return Sequence(new_elements)
        elif isinstance(rhs, Star):
            return Star(self._rename_in_rhs(rhs.rhs, rename_map))
        elif isinstance(rhs, Option):
            return Option(self._rename_in_rhs(rhs.rhs, rename_map))
        else:
            return rhs

    def _get_rule_name(self, name: str) -> str:
        """Convert message name to rule name."""
        result = self._to_snake_case(name)
        result = re.sub('rel_atom', 'relatom', result)
        result = re.sub('rel_term', 'relterm', result)
        result = re.sub('date_time', 'datetime', result)
        return result

    def _to_snake_case(self, name: str) -> str:
        """Convert CamelCase to snake_case."""
        result = re.sub('([a-z\\d])([A-Z])', '\\1_\\2', name)
        return result.lower()

    def _to_field_name(self, name: str) -> str:
        """Normalize field name to valid identifier."""
        return name.replace('-', '_').replace('.', '_')

    def _is_oneof_only_message(self, message: ProtoMessage) -> bool:
        """Check if a message contains only a single oneof and no other fields."""
        return len(message.oneofs) > 0 and len(message.fields) == 0

    def _generate_message_rule(self, message_name: str) -> None:
        """Generate grammar rules for a protobuf message and recursively for its fields."""
        if message_name not in self.parser.messages:
            return
        rule_name = self._get_rule_name(message_name)
        message_type = MessageType(message_name)
        rule_lhs = Nonterminal(rule_name, message_type)
        if rule_name in self.final_rules:
            return
        if rule_name in self.generated_rules:
            return
        self.generated_rules.add(rule_name)
        if rule_lhs not in self.grammar.rules:
            self.grammar.rules[rule_lhs] = []
        message = self.parser.messages[message_name]
        if self._is_oneof_only_message(message):
            oneof = message.oneofs[0]
            for field in oneof.fields:
                field_rule = self._get_rule_name(field.name)
                field_name_snake = self._to_snake_case(field.name)
                field_type = self._get_type_for_name(field.type)
                oneof_call = Call(Constructor('OneOf'), [Symbol(field_name_snake), Var('value', field_type)])
                wrapper_call = Call(Constructor(message_name), [oneof_call])
                action = Lambda([Var('value', field_type)], MessageType(message_name), wrapper_call)
                alt_rule = Rule(lhs=Nonterminal(rule_name, message_type), rhs=Sequence((Nonterminal(field_rule, field_type),)), action=action)
                self._add_rule(alt_rule)
                if self._is_primitive_type(field.type):
                    if field_rule not in self.final_rules:
                        terminal_name = self._map_primitive_type(field.type)
                        field_type = self._get_type_for_name(field.type)
                        field_to_type_rule = Rule(lhs=Nonterminal(field_rule, field_type), rhs=Sequence((NamedTerminal(terminal_name, field_type),)), action=Lambda([Var('x', field_type)], field_type, Var('x', field_type)))
                        self._add_rule(field_to_type_rule)
                else:
                    type_rule = self._get_rule_name(field.type)
                    if field_rule != type_rule and field_rule not in self.final_rules:
                        field_type = self._get_type_for_name(field.type)
                        field_to_type_rule = Rule(lhs=Nonterminal(field_rule, field_type), rhs=Sequence((Nonterminal(type_rule, field_type),)), action=Lambda([Var('x', field_type)], field_type, Var('x', field_type)))
                        self._add_rule(field_to_type_rule)
            for field in oneof.fields:
                if self._is_message_type(field.type):
                    self._generate_message_rule(field.type)
        else:
            tag = self.rule_literal_renames.get(rule_name, rule_name)
            rhs_symbols: List[Rhs] = [LitTerminal('('), LitTerminal(tag)]
            field_names = []
            field_types = []
            for field in message.fields:
                field_symbol = self._generate_field_symbol(field, message_name)
                if field_symbol:
                    rhs_symbols.append(field_symbol)
                    field_names.append(field.name)
                    field_types.append(field.type)
            rhs_symbols.append(LitTerminal(')'))
            action = self._generate_action(message_name, rhs_symbols, field_names, field_types)
            rule = Rule(lhs=Nonterminal(rule_name, message_type), rhs=Sequence(rhs_symbols), action=action, source_type=message_name)
            self._add_rule(rule)
            for field in message.fields:
                if self._is_message_type(field.type):
                    self._generate_message_rule(field.type)

    def _to_sexp_tag(self, name: str) -> str:
        """Convert message name to s-expression tag (same as snake_case conversion)."""
        result = re.sub('([A-Z]+)([A-Z][a-z])', '\\1_\\2', name)
        result = re.sub('([a-z\\d])([A-Z])', '\\1_\\2', result)
        return result.lower()

    def _is_sexp_tag(self, symbol: str) -> bool:
        """Check if symbol should be treated as s-expression tag (currently unused)."""
        if not symbol or not symbol.isidentifier():
            return False
        return symbol.islower() or '_' in symbol

    def _generate_field_symbol(self, field: ProtoField, message_name: str='') -> Optional[Rhs]:
        """Generate grammar symbol for a protobuf field, handling repeated/optional modifiers."""
        if self._is_primitive_type(field.type):
            terminal_name = self._map_primitive_type(field.type)
            field_type = self._get_type_for_name(field.type)
            base_symbol: Rhs = NamedTerminal(terminal_name, field_type)
            if field.is_repeated:
                return Star(base_symbol)
            elif field.is_optional:
                return Option(base_symbol)
            else:
                return base_symbol
        elif self._is_message_type(field.type):
            type_rule_name = self._get_rule_name(field.type)
            field_type = self._get_type_for_name(field.type)
            message_rule_name = self._get_rule_name(message_name)
            field_rule_name = self._to_field_name(field.name)
            wrapper_rule_name = f'{message_rule_name}_{field_rule_name}'
            wrapper_type = ListType(field_type)
            if field.is_repeated:
                should_inline = (message_name, field.name) in self.inline_fields
                if should_inline:
                    if self.grammar.has_rule(Nonterminal(wrapper_rule_name, wrapper_type)):
                        return Nonterminal(wrapper_rule_name, wrapper_type)
                    else:
                        return Star(Nonterminal(type_rule_name, field_type))
                else:
                    literal_name = self.rule_literal_renames.get(field_rule_name, field_rule_name)
                    if not self.grammar.has_rule(Nonterminal(wrapper_rule_name, wrapper_type)):
                        wrapper_rule = Rule(lhs=Nonterminal(wrapper_rule_name, wrapper_type), rhs=Sequence((LitTerminal('('), LitTerminal(literal_name), Star(Nonterminal(type_rule_name, field_type)), LitTerminal(')'))), action=Lambda([Var('value', wrapper_type)], wrapper_type, Var('value', wrapper_type)), source_type=field.type)
                        self._add_rule(wrapper_rule)
                    return Option(Nonterminal(wrapper_rule_name, wrapper_type))
            elif field.is_optional:
                if self.grammar.has_rule(Nonterminal(wrapper_rule_name, field_type)):
                    return Option(Nonterminal(wrapper_rule_name, field_type))
                else:
                    return Option(Nonterminal(type_rule_name, field_type))
            elif self.grammar.has_rule(Nonterminal(wrapper_rule_name, field_type)):
                return Nonterminal(wrapper_rule_name, field_type)
            else:
                return Nonterminal(type_rule_name, field_type)
        else:
            return None

    def _is_primitive_type(self, type_name: str) -> bool:
        """Check if type is a protobuf primitive."""
        return type_name in PRIMITIVE_TYPES

    def _is_message_type(self, type_name: str) -> bool:
        """Check if type is a protobuf message."""
        return type_name in self.parser.messages

    def _map_primitive_type(self, type_name: str) -> str:
        """Map protobuf primitive to grammar terminal name."""
        return PRIMITIVE_TYPES.get(type_name, 'SYMBOL')

def generate_grammar(grammar: Grammar, reachable: Set[str]) -> str:
    """Generate grammar text."""
    return grammar.print_grammar(reachable=reachable)

def generate_semantic_actions(grammar: Grammar, reachable: Set[Nonterminal]) -> str:
    """Generate semantic actions (visitor)."""
    return grammar.print_grammar_with_actions(reachable=reachable)
