"""Grammar generation from protobuf specifications.

This module provides the GrammarGenerator class which converts protobuf
message definitions into grammar rules with semantic actions.
"""
import re
from typing import Callable, Dict, List, Optional, Set, Tuple, cast
from .grammar import Grammar, Rule, Token, Rhs, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence
from .target import Lambda, Call, Var, Lit, IfElse, Symbol, Builtin, Message, OneOf, ListExpr, BaseType, MessageType, OptionType, ListType, TargetType, TargetExpr, TupleType
from .target_utils import create_identity_function
from .grammar_utils import rewrite_rule
from .proto_ast import ProtoMessage, ProtoField
from .proto_parser import ProtoParser
from .grammar_gen_builtins import BuiltinRules
from .grammar_gen_rewrites import get_rule_rewrites

_PRIMITIVE_TO_GRAMMAR_SYMBOL = {
    'string': 'STRING',
    'int32': 'INT',
    'int64': 'INT',
    'uint32': 'INT',
    'uint64': 'INT',
    'fixed64': 'INT',
    'bool': 'BOOLEAN',
    'double': 'FLOAT',
    'float': 'FLOAT',
    'bytes': 'STRING',
}

# Mapping from protobuf primitive types to base type names
_PRIMITIVE_TO_BASE_TYPE = {
    'string': 'String',
    'int32': 'Int32',
    'int64': 'Int64',
    'uint32': 'UInt32',
    'uint64': 'UInt64',
    'fixed64': 'Int64',
    'bool': 'Boolean',
    'double': 'Float64',
    'float': 'Float32',
    'bytes': 'String',
}

class GrammarGenerator:
    """Generator for grammars from protobuf specifications."""

    def __init__(self, parser: ProtoParser, verbose: bool=False):
        self.parser = parser
        self.final_rules: Set[str] = set()
        self.generated_rules: Set[str] = set()
        self.expected_unreachable: Set[str] = set()
        self.grammar = Grammar(start=Nonterminal('transaction', MessageType('transactions', 'Transaction')))
        self.verbose = verbose
        self.never_inline_fields: Set[Tuple[str, str]] = {
            ("Attribute", "attrs"),
        }
        self.rule_literal_renames: Dict[str, str] = {
            "monoid_def": "monoid",
            "monus_def": "monus",
            "conjunction": "and",
            "disjunction": "or",
        }
        self.builtin_rules = BuiltinRules().get_builtin_rules()
        self.rewrite_rules: List[Callable[[Rule], Optional[Rule]]] = get_rule_rewrites()

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
                args.append(Call(Builtin('unwrap_option_or'), [var, ListExpr([], param_type.element_type.element_type)]))
            else:
                args.append(var)
        message = self.parser.messages[message_name]
        body = Call(Message(message.module, message_name), args)
        params = [Var(name, param_type) for name, param_type in zip(param_names, param_types)]
        return Lambda(params=params, return_type=MessageType(message.module, message_name), body=body)

    def _get_type_for_name(self, type_name: str) -> TargetType:
        """Get the appropriate type (BaseType or MessageType) for a given type name."""
        if self._is_primitive_type(type_name):
            base_type_name = _PRIMITIVE_TO_BASE_TYPE[type_name]
            return BaseType(base_type_name)
        elif self._is_message_type(type_name):
            message = self.parser.messages[type_name]
            return MessageType(message.module, type_name)
        else:
            assert False, f'Unknown type: {type_name}'

    def _add_rule(self, rule: Rule, is_builtin: bool = False) -> None:
        """Add a rule to the grammar.

        If there are builtin rules for this nonterminal and it's marked as final,
        assert that the generated rule is different from all builtin rules.

        Applies rewrite rules to generated rules only, not builtin rules.
        """
        # Apply rewrite rules only to generated rules
        rewritten_rule = rule
        if not is_builtin:
            for rewrite in self.rewrite_rules:
                result = rewrite(rewritten_rule)
                if result is not None:
                    rewritten_rule = result

        self.grammar.add_rule(rewritten_rule)

    def generate(self) -> Grammar:
        """Generate complete grammar with prepopulated and message-derived rules."""

        self._add_all_prepopulated_rules()

        for message_name in sorted(self.parser.messages.keys()):
            self._generate_message_rule(message_name)

        # Add the tokens to scan for. The order here matters! We go from most specific to least specific.
        # Specifically, we want to be sure to return INT128 before INT and DECIMAL before FLOAT before INT, and SYMBOL last.
        # The semantic action for these is defined in the target-specific lexer code. Here we just define value types.
        self.grammar.tokens.append(Token("STRING", '"(?:[^"\\\\]|\\\\.)*"', BaseType("String")))
        self.grammar.tokens.append(Token("DECIMAL", '[-]?\\d+\\.\\d+d\\d+', MessageType("logic", "DecimalValue")))
        self.grammar.tokens.append(Token("FLOAT", '(?:[-]?\\d+\\.\\d+|inf|nan)', BaseType("Float64")))
        self.grammar.tokens.append(Token("INT128", '[-]?\\d+i128', MessageType("logic", "Int128Value")))
        self.grammar.tokens.append(Token("UINT128", '0x[0-9a-fA-F]+', MessageType("logic", "UInt128Value")))
        self.grammar.tokens.append(Token("INT", '[-]?\\d+', BaseType("Int64")))
        self.grammar.tokens.append(Token("SYMBOL", '[a-zA-Z_][a-zA-Z0-9_.-]*', BaseType("String")))
        self.grammar.tokens.append(Token("COLON_SYMBOL", ':[a-zA-Z_][a-zA-Z0-9_.-]*', BaseType("String")))

        self._post_process_grammar()
        return self.grammar

    def _add_all_prepopulated_rules(self) -> None:
        """Add manually-crafted rules that should not be auto-generated."""
        for lhs, (rules, is_final) in self.builtin_rules.items():
            if is_final:
                self.final_rules.add(lhs.name)
            for rule in rules:
                assert rule.construct_action is not None
                self._add_rule(rule, is_builtin=True)

    def _post_process_grammar(self) -> None:
        """Apply grammar post-processing."""
        self._combine_identical_rules()
        self.expected_unreachable.update([
            'debug_info',
            'debug_info_ids',
            'ivmconfig',
            'min_monoid',
            'sum_monoid',
            'max_monoid',
            'or_monoid',
            'date_value',
            'datetime_value',
            'decimal_value',
            'int128_value',
            'missing_value',
            'uint128_value',
            'uint128_type',
            'datetime_type',
        ])

    # TODO Check that the actions are also equal (up to alpha equivalence).
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
        rename_map: Dict[Rhs, Rhs] = {}
        for (rhs_pattern, source_type), lhs_names in rhs_source_to_lhs.items():
            if len(lhs_names) > 1:
                canonical_lhs = self._find_canonical_name(lhs_names)
                for i, lhs_name in enumerate(lhs_names):
                    if i == 0:
                        if canonical_lhs != lhs_name:
                            rename_map[lhs_name] = canonical_lhs
                            old_rules = self.grammar.rules[lhs_name]
                            new_rules = [
                                Rule(
                                    lhs=canonical_lhs,
                                    rhs=rule.rhs,
                                    construct_action=rule.construct_action,
                                    source_type=rule.source_type
                                ) for rule in old_rules
                            ]
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

    def _apply_renames(self, rename_map: Dict[Rhs, Rhs]) -> None:
        """Replace all occurrences of old names with new names throughout the grammar."""
        new_rules = {}
        for lhs, rules_list in self.grammar.rules.items():
            new_rules[lhs] = [
                rewrite_rule(rule, rename_map)
                for rule in rules_list
            ]
        self.grammar.rules = new_rules

    @staticmethod
    def _get_rule_name(name: str) -> str:
        """Convert message name to rule name."""
        result = GrammarGenerator._to_snake_case(name)
        return result

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """Convert CamelCase to snake_case."""
        result = re.sub('([a-z\\d])([A-Z])', '\\1_\\2', name)
        result = result.lower()
        result = re.sub('date_time', 'datetime', result)
        result = re.sub('csvconfig', 'csv_config', result)
        result = re.sub('csvcolumn', 'csv_column', result)
        return result

    @staticmethod
    def _to_field_name(name: str) -> str:
        """Normalize field name to valid identifier."""
        return name.replace('-', '_').replace('.', '_')

    @staticmethod
    def _is_oneof_only_message(message: ProtoMessage) -> bool:
        """Check if a message contains only a single oneof and no other fields."""
        return len(message.oneofs) > 0 and len(message.fields) == 0

    def _generate_message_rule(self, message_name: str) -> None:
        """Generate grammar rules for a protobuf message and recursively for its fields."""
        if message_name not in self.parser.messages:
            return
        rule_name = self._get_rule_name(message_name)
        message = self.parser.messages[message_name]
        message_type = MessageType(message.module, message_name)
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
                field_type = self._get_type_for_name(field.type)

                # Create oneof wrapper action
                oneof_call = Call(OneOf(field.name), [Var('value', field_type)])
                wrapper_call = Call(Message(message.module, message_name), [oneof_call])
                construct_action = Lambda(
                    [Var('value', field_type)],
                    MessageType(message.module, message_name),
                    wrapper_call
                )

                # Create rule
                rhs = Nonterminal(field_rule, field_type)
                alt_rule = Rule(
                    lhs=Nonterminal(rule_name, message_type),
                    rhs=rhs,
                    construct_action=construct_action
                )
                self._add_rule(alt_rule)

                # Add field-to-type mapping rule if needed
                if self._is_primitive_type(field.type):
                    if field_rule not in self.final_rules:
                        terminal_name = self._map_primitive_type(field.type)
                        field_type = self._get_type_for_name(field.type)
                        rhs = NamedTerminal(terminal_name, field_type)
                        construct_action = create_identity_function(field_type)
                        field_to_type_rule = Rule(
                            lhs=Nonterminal(field_rule, field_type),
                            rhs=rhs,
                            construct_action=construct_action
                        )
                        self._add_rule(field_to_type_rule)
                else:
                    type_rule = self._get_rule_name(field.type)
                    if field_rule != type_rule and field_rule not in self.final_rules:
                        field_type = self._get_type_for_name(field.type)
                        construct_action = create_identity_function(field_type)
                        rhs = Nonterminal(type_rule, field_type)
                        field_to_type_rule = Rule(
                            lhs=Nonterminal(field_rule, field_type),
                            rhs=rhs,
                            construct_action=construct_action
                        )
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
            rhs = Sequence(tuple(rhs_symbols))

            # Generate construct action
            construct_action = self._generate_action(message_name, rhs_symbols, field_names, field_types)

            # Create rule
            rule = Rule(
                lhs=Nonterminal(rule_name, message_type),
                rhs=rhs,
                construct_action=construct_action,
                source_type=message_name
            )
            self._add_rule(rule)

            for field in message.fields:
                if self._is_message_type(field.type):
                    self._generate_message_rule(field.type)

    def _generate_field_symbol(self, field: ProtoField, message_name: str='') -> Optional[Rhs]:
        """Generate grammar symbol for a protobuf field, handling repeated/optional modifiers."""
        if self._is_primitive_type(field.type):
            field_type = self._get_type_for_name(field.type)
            terminal_name = self._map_primitive_type(field.type)
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
                if self._should_inline_repeated_field(message_name, field):
                    if self.grammar.has_rule(Nonterminal(wrapper_rule_name, wrapper_type)):
                        return Nonterminal(wrapper_rule_name, wrapper_type)
                    else:
                        return Star(Nonterminal(type_rule_name, field_type))
                else:
                    literal_name = self.rule_literal_renames.get(field_rule_name, field_rule_name)
                    if not self.grammar.has_rule(Nonterminal(wrapper_rule_name, wrapper_type)):
                        construct_action = create_identity_function(wrapper_type)
                        rhs = Sequence((LitTerminal('('), LitTerminal(literal_name), Star(Nonterminal(type_rule_name, field_type)), LitTerminal(')')))
                        wrapper_rule = Rule(
                            lhs=Nonterminal(wrapper_rule_name, wrapper_type),
                            rhs=rhs,
                            construct_action=construct_action,
                            source_type=field.type
                        )
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

    def _should_inline_repeated_field(self, message_name: str, field: ProtoField) -> bool:
        """Determine if a repeated field should be inlined.

        A repeated field is inlined if it's the only repeated field in the message
        and not in never_inline.
        """
        if message_name in self.parser.messages:
            message = self.parser.messages[message_name]
            repeated_fields = [f for f in message.fields if f.is_repeated]
            if len(repeated_fields) == 1 and (field.type, field.name) not in self.never_inline_fields:
                return True

        return False

    def _is_primitive_type(self, type_name: str) -> bool:
        """Check if type is a protobuf primitive."""
        return type_name in _PRIMITIVE_TO_GRAMMAR_SYMBOL

    def _is_message_type(self, type_name: str) -> bool:
        """Check if type is a protobuf message."""
        return type_name in self.parser.messages

    def _map_primitive_type(self, type_name: str) -> str:
        """Map protobuf primitive to grammar terminal name."""
        return _PRIMITIVE_TO_GRAMMAR_SYMBOL.get(type_name, 'SYMBOL')



def generate_grammar(grammar: Grammar) -> str:
    """Generate grammar text."""
    return grammar.print_grammar()

def generate_semantic_actions(grammar: Grammar) -> str:
    """Generate semantic actions (visitor)."""
    return grammar.print_grammar_with_actions()
