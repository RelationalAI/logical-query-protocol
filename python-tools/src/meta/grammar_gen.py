"""Grammar generation from protobuf specifications.

This module provides the GrammarGenerator class which converts protobuf
message definitions into grammar rules with semantic actions.

## Overview

The grammar generator automatically creates parsing rules from protobuf message
definitions. Each protobuf message becomes a nonterminal, and each field becomes
part of the production rule. The generator also creates semantic actions (Lambda
expressions) that construct the protobuf messages from parsed values.

## How Grammar Generation Works

1. **Message to Nonterminal Mapping**: Each protobuf message type becomes a
   nonterminal in the grammar. For example, a `Fragment` message becomes
   a `fragment` nonterminal.

2. **Field to RHS Mapping**: Message fields are converted to grammar symbols:
   - Primitive fields (string, int64, etc.) become terminals (SYMBOL, INT, etc.)
   - Message fields become nonterminals referencing other messages
   - `repeated` fields become Star (*) pseudo-nonterminals
   - `optional` fields become Option (?) pseudo-nonterminals
   - `oneof` fields generate multiple alternative productions

3. **Semantic Actions**: Each production includes a Lambda that constructs the
   protobuf message from parsed values. The Lambda parameters correspond to
   non-literal RHS elements, and the body calls the Message constructor.

4. **S-expression Syntax**: Productions include literal terminals for the
   S-expression syntax: opening paren, message name as a literal, and closing paren.
   For example: `"(" "and" formula* ")"`

## Extension Points

The grammar generator can be extended in two ways:

### 1. Builtin Rules (grammar_gen_builtins.py)

Builtin rules are manually specified productions for constructs that cannot be
auto-generated from protobuf. Use builtins when:

- The syntax doesn't directly correspond to a protobuf message structure
- Multiple protobuf types share the same syntactic form (e.g., Value literals)
- The production requires complex semantic actions with conditionals
- You need to parse special syntax (dates, configuration, operators)

To add builtin rules:
1. Define the Rule with its LHS nonterminal, RHS, and semantic action
2. Call `add_rule(rule, is_final=True)` to mark the nonterminal as complete
3. Set `is_final=False` if auto-generation should add more alternatives

### 2. Rule Rewrites (grammar_gen_rewrites.py)

Rewrites transform auto-generated rules into more suitable forms. Use rewrites when:

- The auto-generated rule is correct but needs adjustment for better parsing
- You need to change token granularity (STRING → name nonterminal)
- You need to flatten nested structures for simpler parsing
- You need to combine multiple grammar elements (abstraction + arity)

To add rewrites:
1. Create a rewrite function: `Callable[[Rule], Rule]`
2. Add it to the dict in `get_rule_rewrites()` with the nonterminal name as key
3. The rewrite will be applied after auto-generation but before finalization

Common rewrite patterns:
- `make_symbol_replacer()`: Replace specific RHS symbols with alternatives
- Field flattening: Transform nested message references into inline parsing
- Type conversions: Adjust semantic action parameter types after RHS changes

## Configuration

The GrammarGenerator constructor accepts several configuration options:

- `inline_fields`: Set of (message_name, field_name) tuples for fields that
  should be inlined (expanded directly) rather than parsed as subnonterminals

- `rule_literal_renames`: Dict mapping rule names to alternative literal names
  used in the S-expression syntax (e.g., "conjunction" → "and")

- `final_rules`: Set of rule names that should not be auto-generated (only
  use builtin rules)

- `expected_unreachable`: Set of rule names that are intentionally not
  reachable from the start symbol
"""
import re
from typing import Callable, Dict, List, Optional, Set, Tuple
from .grammar import Grammar, Rule, Token, Rhs, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence
from .target import Lambda, Call, Var, Symbol, Builtin, Message, OneOf, ListExpr, BaseType, MessageType, OptionType, ListType
from .proto_ast import ProtoMessage, ProtoField
from .proto_parser import ProtoParser
from .grammar_gen_builtins import get_builtin_rules
from .grammar_gen_rewrites import get_rule_rewrites

# Mapping from protobuf primitive types to grammar terminal names
_PRIMITIVE_TO_TERMINAL = {
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
        self.expected_unreachable: Set[str] = set()
        self.grammar = Grammar(start=Nonterminal('transaction', MessageType('transactions', 'Transaction')))
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
        self.rule_rewrites: Dict[str, Callable[[Rule], Rule]] = get_rule_rewrites()

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
            message = self.parser.messages[type_name]
            return MessageType(message.module, type_name)
        else:
            assert False, f'Unknown type: {type_name}'

    def _add_rule(self, rule: Rule) -> None:
        """Add a rule to the grammar."""
        rewrite = self.rule_rewrites.get(rule.lhs.name)
        if rewrite:
            rule = rewrite(rule)
        self.grammar.add_rule(rule)

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
        builtin_rules, final_nonterminals = get_builtin_rules()
        for lhs, rules in builtin_rules.items():
            for rule in rules:
                assert rule.action is not None
                self.grammar.add_rule(rule)
        for nonterminal in final_nonterminals:
            self.final_rules.add(nonterminal.name)

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
            renamed = self._rename_in_rhs(rhs.rhs, rename_map)
            assert isinstance(renamed, (Nonterminal, NamedTerminal)), f"Star child must be Nonterminal or NamedTerminal, got {type(renamed)}"
            return Star(renamed)
        elif isinstance(rhs, Option):
            renamed = self._rename_in_rhs(rhs.rhs, rename_map)
            assert isinstance(renamed, (Nonterminal, NamedTerminal)), f"Option child must be Nonterminal or NamedTerminal, got {type(renamed)}"
            return Option(renamed)
        else:
            return rhs

    @staticmethod
    def _get_rule_name(name: str) -> str:
        """Convert message name to rule name."""
        result = GrammarGenerator._to_snake_case(name)
        result = re.sub('rel_atom', 'relatom', result)
        result = re.sub('rel_term', 'relterm', result)
        result = re.sub('date_time', 'datetime', result)
        result = re.sub('csvconfig', 'csv_config', result)
        return result

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """Convert CamelCase to snake_case."""
        result = re.sub('([a-z\\d])([A-Z])', '\\1_\\2', name)
        return result.lower()

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
                field_name_snake = self._to_snake_case(field.name)
                field_type = self._get_type_for_name(field.type)
                oneof_call = Call(OneOf(Symbol(field_name_snake)), [Var('value', field_type)])
                wrapper_call = Call(Message(message.module, message_name), [oneof_call])
                action = Lambda([Var('value', field_type)], MessageType(message.module, message_name), wrapper_call)
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
            rule = Rule(lhs=Nonterminal(rule_name, message_type), rhs=Sequence(tuple(rhs_symbols)), action=action, source_type=message_name)
            self._add_rule(rule)
            for field in message.fields:
                if self._is_message_type(field.type):
                    self._generate_message_rule(field.type)

    def _generate_field_symbol(self, field: ProtoField, message_name: str='') -> Optional[Rhs]:
        """Generate grammar symbol for a protobuf field, handling repeated/optional modifiers."""
        if self._is_primitive_type(field.type):
            terminal_name = self._map_primitive_type(field.type)
            field_type = self._get_type_for_name(field.type)
            base_symbol: NamedTerminal = NamedTerminal(terminal_name, field_type)
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
        return type_name in _PRIMITIVE_TO_TERMINAL

    def _is_message_type(self, type_name: str) -> bool:
        """Check if type is a protobuf message."""
        return type_name in self.parser.messages

    def _map_primitive_type(self, type_name: str) -> str:
        """Map protobuf primitive to grammar terminal name."""
        if type_name in _PRIMITIVE_TO_TERMINAL:
            return _PRIMITIVE_TO_TERMINAL[type_name]
        else:
            raise ValueError(f"Primitive type {type_name} not found")

def generate_grammar(grammar: Grammar, reachable: Set[str]) -> str:
    """Generate grammar text."""
    return grammar.print_grammar(reachable=reachable)

def generate_semantic_actions(grammar: Grammar, reachable: Set[Nonterminal]) -> str:
    """Generate semantic actions (visitor)."""
    return grammar.print_grammar_with_actions(reachable=reachable)
