"""Grammar generation from protobuf specifications.

This module provides the GrammarGenerator class which converts protobuf
message definitions into grammar rules with semantic actions.
"""

import re
from typing import Callable, Dict, List, Optional, Set, Tuple

from .grammar import (
    Grammar, Rule, Token, Rhs, LitTerminal, NamedTerminal, Nonterminal,
    Star, Plus, Option, Sequence
)
from .target import (
    Lambda, Call, Var, Symbol, TargetExpr, Lit, IfElse, Builtin, Constructor, BaseType, MessageType
)
from .proto_ast import ProtoMessage, ProtoField, PRIMITIVE_TYPES
from .proto_parser import ProtoParser


def parse_action(action_str: str) -> TargetExpr:
    """Parse a lambda string into an TargetExpr AST."""
    if not action_str.startswith('lambda '):
        raise ValueError(f"Action must start with 'lambda': {action_str}")

    # Extract params and body
    colon_idx = action_str.index(':')
    params_str = action_str[7:colon_idx].strip()
    body_str = action_str[colon_idx+1:].strip()

    params = [p.strip() for p in params_str.split(',')]

    # Remove STATE parameter if present
    if params and params[0] == 'STATE':
        params = params[1:]

    # Parse body - simple f-string parser
    if body_str.startswith('f"') or body_str.startswith("f'"):
        inner = body_str[2:-1]
        # Extract function name and arguments
        paren_idx = inner.index('(')
        func_name = inner[:paren_idx]
        args_str = inner[paren_idx+1:-1]  # Remove parens

        # Parse arguments
        call_args = []
        if args_str:
            for arg in re.findall(r'\{([^}]+)\}', args_str):
                call_args.append(Var(arg))

        body = Call(Var(func_name), call_args)
    elif body_str == 'x' or body_str.isidentifier():
        body = Var(body_str)
    else:
        # Default fallback
        body = Var('x')

    return Lambda(params=params, body=body)


class GrammarGenerator:
    """Generator for grammars from protobuf specifications."""
    def __init__(self, parser: ProtoParser, verbose: bool = False):
        self.parser = parser
        self.generated_rules: Set[str] = set()
        self.final_rules: Set[str] = set()
        self.expected_unreachable: Set[str] = set()
        self.grammar = Grammar()
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

    def _generate_action(self, message_name: str, rhs_elements: List[Rhs], field_names: Optional[List[str]] = None) -> Lambda:
        """Generate semantic action to construct protobuf message from parsed elements."""

        # Create parameters for all RHS elements
        params = []
        field_idx = 0
        for elem in rhs_elements:
            if isinstance(elem, LitTerminal):
                # LitTerminals are skipped.
                pass
            else:
                # Non-literals get named parameters
                if field_names and field_idx < len(field_names):
                    params.append(field_names[field_idx])
                else:
                    params.append(self._next_param_name(len([p for p in params])))
                field_idx += 1

        # Generate message construction
        field_refs = [p for p in params]
        args = [Var(name) for name in field_refs]
        body = Call(Constructor(message_name), args)

        return Lambda(params=params, body=body)

    def _next_param_name(self, idx: int) -> str:
        """Generate parameter name for lambda (a, b, c, ...)."""
        if idx < 26:
            return chr(ord('a') + idx)
        return f"x{idx}"

    def _add_rule(self, rule: Rule) -> None:
        """Add a rule to the grammar and track it in generated_rules."""
        rewrite = self.rule_rewrites.get(rule.lhs.name)
        if rewrite:
            rule = rewrite(rule)
        self.generated_rules.add(rule.lhs.name)
        self.grammar.add_rule(rule)

    def _init_rule_rewrites(self) -> Dict[str, Callable[[Rule], Rule]]:
        """Initialize rule rewrite functions."""

        def rewrite_string_to_name_optional(rule: Rule) -> Rule:
            """Replace STRING with name? in output and abort rules."""
            if isinstance(rule.rhs, Sequence):
                for i, symbol in enumerate(rule.rhs.elements):
                    if symbol == NamedTerminal('STRING'):
                        rule.rhs.elements[i] = Option(Nonterminal('name'))
            return rule

        def rewrite_string_to_name(rule: Rule) -> Rule:
            """Replace STRING with name."""
            if isinstance(rule.rhs, Sequence):
                for i, symbol in enumerate(rule.rhs.elements):
                    if symbol == NamedTerminal('STRING'):
                        rule.rhs.elements[i] = Nonterminal('name')
            return rule

        def rewrite_fragment_remove_debug_info(rule: Rule) -> Rule:
            """Remove debug_info from fragment rules."""
            if isinstance(rule.rhs, Sequence):
                new_elements = []
                for symbol in rule.rhs.elements:
                    if symbol == Option(Nonterminal('debug_info')) or symbol == Nonterminal('debug_info'):
                        continue
                    new_elements.append(symbol)
                rule.rhs.elements = new_elements
                rule.action.params = rule.action.params[:-1]
            return rule

        def rewrite_terms_optional_to_star_term(rule: Rule) -> Rule:
            """Replace terms? with term*."""
            if isinstance(rule.rhs, Sequence):
                for i, symbol in enumerate(rule.rhs.elements):
                    if symbol == Option(Nonterminal('terms')):
                        rule.rhs.elements[i] = Star(Nonterminal('term'))
            return rule

        def rewrite_terms_optional_to_star_relterm(rule: Rule) -> Rule:
            """Replace terms? with relterm* and STRING with name."""
            if isinstance(rule.rhs, Sequence):
                for i, symbol in enumerate(rule.rhs.elements):
                    if symbol == Option(Nonterminal('terms')):
                        rule.rhs.elements[i] = Star(Nonterminal('relterm'))
                    elif symbol == NamedTerminal('STRING'):
                        rule.rhs.elements[i] = Nonterminal('name')
            return rule

        def rewrite_primitive_rule(rule: Rule) -> Rule:
            """Replace STRING with name and term* with relterm* in primitive rules."""
            if isinstance(rule.rhs, Sequence) and len(rule.rhs.elements) >= 2:
                if (rule.rhs.elements[0] == LitTerminal('(') and
                    rule.rhs.elements[1] == LitTerminal('primitive')):
                    for i, symbol in enumerate(rule.rhs.elements):
                        if symbol == NamedTerminal('STRING'):
                            rule.rhs.elements[i] = Nonterminal('name')
                        elif isinstance(symbol, Star):
                            if symbol.rhs == Nonterminal('term'):
                                rule.rhs.elements[i] = Star(Nonterminal('relterm'))
            return rule

        def rewrite_exists(rule: Rule) -> Rule:
            """Rewrite exists rule to use bindings and formula instead of abstraction."""
            if isinstance(rule.rhs, Sequence):
                new_elements = []
                for elem in rule.rhs.elements:
                    if elem == Nonterminal('abstraction'):
                        new_elements.append(Nonterminal('bindings'))
                        new_elements.append(Nonterminal('formula'))
                    else:
                        new_elements.append(elem)
                rule.rhs.elements = new_elements
            return rule

        def rewrite_drop_INT_from_instructions(rule: Rule) -> Rule:
            """Drop INT argument from penultimate position."""
            if isinstance(rule.rhs, Sequence) and len(rule.rhs.elements) >= 2:
                penultimate_idx = len(rule.rhs.elements) - 2
                if penultimate_idx >= 0:
                    elem = rule.rhs.elements[penultimate_idx]
                    if elem == NamedTerminal('INT'):
                        rule.rhs.elements.pop(penultimate_idx)
            return rule

        def rewrite_relatom_rule(rule: Rule) -> Rule:
            """Replace STRING with name and terms? with relterm*."""
            if isinstance(rule.rhs, Sequence):
                for i, symbol in enumerate(rule.rhs.elements):
                    if symbol == NamedTerminal('STRING'):
                        rule.rhs.elements[i] = Nonterminal('name')
                    elif symbol == Option(Nonterminal('terms')):
                        rule.rhs.elements[i] = Star(Nonterminal('relterm'))
            return rule

        def rewrite_attribute_rule(rule: Rule) -> Rule:
            """Replace STRING with name and args? with value*."""
            if isinstance(rule.rhs, Sequence):
                for i, symbol in enumerate(rule.rhs.elements):
                    if symbol == NamedTerminal('STRING'):
                        rule.rhs.elements[i] = Nonterminal('name')
                    elif symbol == Option(Nonterminal('args')):
                        rule.rhs.elements[i] = Star(Nonterminal('value'))
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
            'upsert': rewrite_drop_INT_from_instructions,
            'monoid_def': rewrite_drop_INT_from_instructions,
            'monus_def': rewrite_drop_INT_from_instructions,
            'relatom': rewrite_relatom_rule,
            'attribute': rewrite_attribute_rule,
        }

    def generate(self, start_message: str = "Transaction") -> Grammar:
        """Generate complete grammar with prepopulated and message-derived rules."""
        self._add_all_prepopulated_rules()

        self._generate_message_rule(start_message)

        for message_name in sorted(self.parser.messages.keys()):
            self._generate_message_rule(message_name)

        # Add the tokens to scan for. The order here matters! We go from most specific to least specific.
        # Specifically, we want to be sure to return INT128 before INT and DECIMAL before FLOAT, and SYMBOL last.
        # The semantic action for these is defined in the target-specific lexer code. Here we just define value types.
        self.grammar.tokens.append(Token("STRING", '"(?:[^"\\\\]|\\\\.)*"', BaseType("String")))
        self.grammar.tokens.append(Token("INT128", '[-]?\\d+i128', BaseType("Int128")))
        self.grammar.tokens.append(Token("INT", '[-]?\\d+', BaseType("Int64")))
        self.grammar.tokens.append(Token("UINT128", '0x[0-9a-fA-F]+', BaseType("UInt128")))
        self.grammar.tokens.append(Token("DECIMAL", '[-]?\\d+\\.\\d+d\\d+', BaseType("Decimal")))
        self.grammar.tokens.append(Token("FLOAT", '(?:[-]?\\d+\\.\\d+|inf|nan)', BaseType("Float64")))
        self.grammar.tokens.append(Token("SYMBOL", '[a-zA-Z_][a-zA-Z0-9_.-]*', BaseType("String")))

        self._post_process_grammar()
        return self.grammar

    def _add_all_prepopulated_rules(self) -> None:
        """Add manually-crafted rules that should not be auto-generated."""
        def add_rule(rule: Rule, is_final: bool = True) -> None:
            if is_final:
                self.generated_rules.add(rule.lhs.name)
                self.final_rules.add(rule.lhs.name)
            assert rule.action is not None
            self.grammar.add_rule(rule)


        add_rule(Rule(
            lhs=Nonterminal("start"),
            rhs=Sequence([Nonterminal("transaction")]),
            action=Lambda(params=['transaction'], body=Var('transaction'), return_type=MessageType('Transaction')),
        ))
        add_rule(Rule(
            lhs=Nonterminal("start"),
            rhs=Sequence([Nonterminal("fragment")]),
            action=Lambda(params=['fragment'], body=Var('fragment'), return_type=MessageType('Fragment')),
        ))

        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=Sequence([Nonterminal('date')]),
            action=Lambda(params=['value'], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("date_value"), Var('value')])])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=Sequence([Nonterminal('datetime')]),
            action=Lambda(params=['value'], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("datetime_value"), Var('value')])])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=Sequence([NamedTerminal('STRING')]),
            action=Lambda(params=['value'], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("string_value"), Var('value')])])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=Sequence([NamedTerminal('INT')]),
            action=Lambda(params=['value'], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("int_value"), Var('value')])])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=Sequence([NamedTerminal('FLOAT')]),
            action=Lambda(params=['value'], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("float_value"), Var('value')])])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=Sequence([NamedTerminal('UINT128')]),
            action=Lambda(params=['value'], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("uint128_value"), Var('value')])])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=Sequence([NamedTerminal('INT128')]),
            action=Lambda(params=['value'], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("int128_value"), Var('value')])])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=Sequence([NamedTerminal('DECIMAL')]),
            action=Lambda(params=['value'], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("decimal_value"), Var('value')])])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=Sequence([LitTerminal("missing")]),
            action=Lambda(params=[], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("missing_value"), Call(Constructor("MissingValue"), [])])])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=Sequence([LitTerminal("true")]),
            action=Lambda(params=[], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("boolean_value"), Lit(True)])])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=Sequence([LitTerminal("false")]),
            action=Lambda(params=[], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("boolean_value"), Lit(False)])])),
        ))

        add_rule(Rule(
            lhs=Nonterminal("date"),
            rhs=Sequence([LitTerminal("("), LitTerminal("date"), NamedTerminal("INT"), NamedTerminal("INT"), NamedTerminal("INT"), LitTerminal(")")]),
            action=Lambda(params=['year', 'month', 'day'], body=Call(Constructor("DateValue"), [Var('year'), Var('month'), Var('day')])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("datetime"),
            rhs=Sequence([LitTerminal("("), LitTerminal("datetime"), NamedTerminal("INT"), NamedTerminal("INT"), NamedTerminal("INT"), NamedTerminal("INT"), NamedTerminal("INT"), NamedTerminal("INT"), Option(NamedTerminal("INT")), LitTerminal(")")]),
            action=Lambda(params=['year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond'], body=Call(Constructor("DateTimeValue"), [Var('year'), Var('month'), Var('day'), Var('hour'), Var('minute'), Var('second'), IfElse(Call(Builtin('is_none'),[Var('microsecond')]), Lit(0), Var('microsecond'))])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("config_dict"),
            rhs=Sequence([LitTerminal("{"), Star(Nonterminal("config_key_value")), LitTerminal("}")]),
            action=Lambda(params=['config_key_value'], body=Var('config_key_value')),
        ))
        add_rule(Rule(
            lhs=Nonterminal("config_key_value"),
            rhs=Sequence([LitTerminal(":"), NamedTerminal("SYMBOL"), Nonterminal("value")]),
            action=Lambda(params=['symbol', 'value'], body=Call(Builtin("Tuple"), [Var('symbol'), Var('value')])),
        ))

        add_rule(Rule(
            lhs=Nonterminal("transaction"),
            rhs=Sequence([LitTerminal("("), LitTerminal("transaction"), Option(Nonterminal("configure")), Option(Nonterminal("sync")), Star(Nonterminal("epoch")), LitTerminal(")")]),
            action=Lambda(params=['configure', 'sync', 'epochs'],
                          body=Call(Constructor('Transaction'), [Var('epochs'), Var('configure'), Var('sync')])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("bindings"),
            rhs=Sequence([LitTerminal("["), Star(Nonterminal("binding")), Option(Nonterminal("value_bindings")), LitTerminal("]")]),
            action=Lambda(params=['keys', 'values'], body=Call(Builtin('Tuple'), [Var('keys'), Var('values')])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("value_bindings"),
            rhs=Sequence([LitTerminal("|"), Star(Nonterminal("binding"))]),
            action=Lambda(params=['values'], body=Call(Builtin('Tuple'), [Var('values'), Call(Builtin('length'), [Var('values')])])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("binding"),
            rhs=Sequence([NamedTerminal("SYMBOL"), LitTerminal("::"), Nonterminal("type")]),
            action=Lambda(params=['symbol', 'type'], body=Call(Constructor('Binding'), [Call(Constructor('Var'), [Var('symbol')]), Var('type')])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("abstraction"),
            rhs=Sequence([LitTerminal("("), Nonterminal("bindings"), Nonterminal("formula"), LitTerminal(")")]),
            action=Lambda(params=['bindings', 'formula'], body=Call(Constructor('Abstraction'), [Var('bindings'), Var('formula')])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("name"),
            rhs=Sequence([LitTerminal(":"), NamedTerminal("SYMBOL")]),
            action=Lambda(params=['symbol'], body=Call(Constructor('Name'), [Var('symbol')])),
        ))

        # TODO PR can we just use the naive rules for these?
        # Otherwise, we should at least loop over the monoid messages and add these cases.
        add_rule(Rule(
            lhs=Nonterminal("monoid"),
            rhs=Sequence([Nonterminal("type"), LitTerminal("::"), Nonterminal("monoid_op")]),
            action=Lambda(params=['type', 'op'], body=Call(Var('op'), [Var('type')])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("monoid_op"),
            rhs=LitTerminal("OR"),
            action=Lambda(params=[], body=Lambda(params=['type'], body=Call(Constructor("monoid"), [Call(Constructor("OneOf"), [Symbol("or_monoid"), Call(Constructor('OrMonoid'), [])])]))),
        ))
        add_rule(Rule(
            lhs=Nonterminal("monoid_op"),
            rhs=LitTerminal("MIN"),
            action=Lambda(params=[], body=Lambda(params=['type'], body=Call(Constructor("monoid"), [Call(Constructor("OneOf"), [Symbol("min_monoid"), Call(Constructor('MinMonoid'), [Var('type')])])]))),
        ))
        add_rule(Rule(
            lhs=Nonterminal("monoid_op"),
            rhs=LitTerminal("MAX"),
            action=Lambda(params=[], body=Lambda(params=['type'], body=Call(Constructor("monoid"), [Call(Constructor("OneOf"), [Symbol("max_monoid"), Call(Constructor('MaxMonoid'), [Var('type')])])]))),
        ))
        add_rule(Rule(
            lhs=Nonterminal("monoid_op"),
            rhs=LitTerminal("SUM"),
            action=Lambda(params=[], body=Lambda(params=['type'], body=Call(Constructor("monoid"), [Call(Constructor("OneOf"), [Symbol("sum"), Call(Constructor('SumMonoid'), [Var('type')])])]))),
        ))

        add_rule(Rule(
            lhs=Nonterminal("configure"),
            rhs=Sequence([LitTerminal("("), LitTerminal("configure"), Nonterminal("config_dict"), LitTerminal(")")]),
            action=Lambda(params=['config_dict'], body=Call(Constructor('Configure'), [Var('config_dict')])),
        ))

        add_rule(Rule(
            lhs=Nonterminal("true"),
            rhs=Sequence([LitTerminal("("), LitTerminal("true"), LitTerminal(")")]),
            action = Lambda(params=[], body=Call(Constructor('Conjunction'), [Call(Builtin('make_list'), [])])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("false"),
            rhs=Sequence([LitTerminal("("), LitTerminal("false"), LitTerminal(")")]),
            action = Lambda(params=[], body=Call(Constructor('Disjunction'), [Call(Builtin('make_list'), [])])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("formula"),
            rhs=Sequence([Nonterminal("true")]),
            action=Lambda(params=['value'], body=Call(Constructor('Formula'), [Call(Constructor('OneOf'), [Symbol('true'), Var('value')])])),

        ), is_final=False)
        add_rule(Rule(
            lhs=Nonterminal("formula"),
            rhs=Sequence([Nonterminal("false")]),
            action=Lambda(params=['value'], body=Call(Constructor('Formula'), [Call(Constructor('OneOf'), [Symbol('false'), Var('value')])])),

        ), is_final=False)

        add_rule(Rule(
            lhs=Nonterminal("export"),
            rhs=Sequence([LitTerminal("("), LitTerminal("export"), Nonterminal("export_csvconfig"), LitTerminal(")")]),
            action=Lambda(params=['config'], body=Call(Constructor('Export'), [Var('config')])),
        ))

        add_rule(Rule(
            lhs=Nonterminal("export_csvconfig"),
            rhs=Sequence([LitTerminal("("), LitTerminal("export_csvconfig"), Nonterminal("export_path"), Nonterminal("export_csvcolumns"), Nonterminal("config_dict"), LitTerminal(")")]),
            action=Lambda(params=['path', 'columns', 'config'], body=Call(Constructor('ExportCsvConfig'), [Var('path'), Var('columns'), Var('config')])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("export_csvcolumns"),
            rhs=Sequence([LitTerminal("("), LitTerminal("columns"), Star(Nonterminal("export_csvcolumn")), LitTerminal(")")]),
            action=Lambda(params=['columns'], body=Call(Constructor('ExportCsvColumns'), [Var('columns')])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("export_csvcolumn"),
            rhs=Sequence([LitTerminal("("), LitTerminal("column"), NamedTerminal("STRING"), Nonterminal("relation_id"), LitTerminal(")")]),
            action=Lambda(params=['name', 'relation_id'], body=Call(Constructor('ExportCsvColumn'), [Var('name'), Var('relation_id')])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("export_path"),
            rhs=Sequence([LitTerminal("("), LitTerminal("path"), NamedTerminal("STRING"), LitTerminal(")")]),
            action=Lambda(params=['path'], body=Call(Constructor('ExportPath'), [Var('path')])),
        ))

        add_rule(Rule(
            lhs=Nonterminal("var"),
            rhs=Sequence([NamedTerminal("SYMBOL")]),
            action=Lambda(params=['symbol'], body=Call(Constructor('Var'), [Var('symbol')])),
        ))

        add_rule(Rule(
            lhs=Nonterminal("fragment_id"),
            rhs=Sequence([LitTerminal(":"), NamedTerminal("SYMBOL")]),
            action=Lambda(params=['symbol'], body=Call(Constructor('FragmentId'), [Var('symbol')])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("relation_id"),
            rhs=Sequence([LitTerminal(":"), NamedTerminal("SYMBOL")]),
            action=Lambda(params=['symbol'], body=Call(Constructor('RelationId'), [Var('symbol')])),
        ))
        add_rule(Rule(
            lhs=Nonterminal("relation_id"),
            rhs=Sequence([NamedTerminal("INT")]),
            action=Lambda(params=['INT'], body=Call(Constructor('RelationId'), [Var('INT')])),
        ))

        add_rule(Rule(
            lhs=Nonterminal("specialized_value"),
            rhs=Sequence([LitTerminal("#"), Nonterminal("value")]),
            action=Lambda(params=['value'], body=Call(Constructor('SpecializedValue'), [Var('value')])),

        ), is_final=True)

        type_rules = {
            "unspecified_type": (LitTerminal("UNKNOWN"), Lambda(params=[], body=Call(Constructor('UnspecifiedType'), []))),
            "string_type": (LitTerminal("STRING"), Lambda(params=[], body=Call(Constructor('StringType'), []))),
            "int_type": (LitTerminal("INT"), Lambda(params=[], body=Call(Constructor('IntType'), []))),
            "float_type": (LitTerminal("FLOAT"), Lambda(params=[], body=Call(Constructor('FloatType'), []))),
            "uint128_type": (LitTerminal("UINT128"), Lambda(params=[], body=Call(Constructor('Uint128Type'), []))),
            "int128_type": (LitTerminal("INT128"), Lambda(params=[], body=Call(Constructor('Int128Type'), []))),
            "boolean_type": (LitTerminal("BOOLEAN"), Lambda(params=[], body=Call(Constructor('BooleanType'), []))),
            "date_type": (LitTerminal("DATE"), Lambda(params=[], body=Call(Constructor('DateType'), []))),
            "datetime_type": (LitTerminal("DATETIME"), Lambda(params=[], body=Call(Constructor('DatetimeType'), []))),
            "missing_type": (LitTerminal("MISSING"), Lambda(params=[], body=Call(Constructor('MissingType'), []))),
            "decimal_type": (Sequence([LitTerminal("("), LitTerminal("DECIMAL"), NamedTerminal("INT"), NamedTerminal("INT"), LitTerminal(")")]), Lambda(params=['precision', 'scale'], body=Call(Constructor('DecimalType'), [Var('precision'), Var('scale')]))),
        }
        for lhs_name, (rhs, action) in type_rules.items():
            add_rule(Rule(
                lhs=Nonterminal(lhs_name),
                rhs=rhs,
                action=action,

            ))

        # Comparison operators (binary)
        comparison_ops = [
            ("eq", "=", "rel_primitive_eq"),
            ("lt", "<", "rel_primitive_lt"),
            ("lt_eq", "<=", "rel_primitive_lt_eq"),
            ("gt", ">", "rel_primitive_gt"),
            ("gt_eq", ">=", "rel_primitive_gt_eq"),
        ]
        for name, op, prim in comparison_ops:
            add_rule(Rule(
                lhs=Nonterminal(name),
                rhs=Sequence([LitTerminal("("), LitTerminal(op), Nonterminal("term"), Nonterminal("term"), LitTerminal(")")]),
                action=Lambda(params=['left', 'right'], body=Call(Constructor('Primitive'), [Lit(prim), Var('left'), Var('right')])),

            ))

        # Arithmetic operators (ternary)
        arithmetic_ops = [
            ("add", "+", "rel_primitive_add"),
            ("minus", "-", "rel_primitive_subtract"),
            ("multiply", "*", "rel_primitive_multiply"),
            ("divide", "/", "rel_primitive_divide"),
        ]
        for name, op, prim in arithmetic_ops:
            add_rule(Rule(
                lhs=Nonterminal(name),
                rhs=Sequence([LitTerminal("("), LitTerminal(op), Nonterminal("term"), Nonterminal("term"), Nonterminal("term"), LitTerminal(")")]),
                action=Lambda(params=['left', 'right', 'result'], body=Call(Constructor('Primitive'), [Lit(prim), Var('left'), Var('right'), Var('result')])),

            ))

        for name, _op, _prim in comparison_ops + arithmetic_ops:
            add_rule(Rule(
                lhs=Nonterminal("primitive"),
                rhs=Sequence([Nonterminal(name)]),
                action=Lambda(params=['op'], body=Var('op')),

            ), is_final=False)

    def _post_process_grammar(self) -> None:
        """Apply grammar post-processing."""
        self._combine_identical_rules()

        self.expected_unreachable.add("debug_info")
        self.expected_unreachable.add("debug_info_ids")
        self.expected_unreachable.add("ivmconfig")
        self.expected_unreachable.add("min_monoid")
        self.expected_unreachable.add("sum_monoid")
        self.expected_unreachable.add("max_monoid")
        self.expected_unreachable.add("or_monoid")

    def _combine_identical_rules(self) -> None:
        """Combine rules with identical RHS patterns into a single rule with multiple alternatives."""
        # Build a map from (RHS pattern, source_type) to list of LHS names
        # Only combine rules that came from the same protobuf type
        rhs_source_to_lhs: Dict[Tuple[str, Optional[str]], List[Nonterminal]] = {}
        for lhs in self.grammar.rules.keys():
            rules_list = self.grammar.rules[lhs]
            if len(rules_list) == 1:
                rule = rules_list[0]
                rhs_pattern = str(rule.rhs)
                source_type = rule.source_type
                # Only combine rules with a source_type (i.e., generated from messages)
                if source_type:
                    key = (rhs_pattern, source_type)
                    if key not in rhs_source_to_lhs:
                        rhs_source_to_lhs[key] = []
                    rhs_source_to_lhs[key].append(lhs)

        # Track renaming map
        rename_map: Dict[Nonterminal, Nonterminal] = {}

        # Find groups of rules with identical RHS from the same source type
        for (rhs_pattern, source_type), lhs_names in rhs_source_to_lhs.items():
            if len(lhs_names) > 1:
                # Determine canonical name based on common suffix
                canonical_lhs = self._find_canonical_name(lhs_names)

                # Keep the first rule as the canonical one, delete the rest
                for i, lhs_name in enumerate(lhs_names):
                    if i == 0:
                        # Rename the first rule to canonical name if needed
                        if canonical_lhs != lhs_name:
                            rename_map[lhs_name] = canonical_lhs
                            self.grammar.rules[canonical_lhs] = self.grammar.rules[lhs_name]
                            self.grammar.rules[canonical_lhs][0].lhs = canonical_lhs
                            del self.grammar.rules[lhs_name]
                    else:
                        # Mark this name as renamed to canonical
                        rename_map[lhs_name] = canonical_lhs
                        # Remove from grammar
                        if lhs_name in self.grammar.rules:
                            del self.grammar.rules[lhs_name]

        # Replace all occurrences of renamed rules throughout the grammar
        if rename_map:
            self._apply_renames(rename_map)

    def _find_canonical_name(self, names: List[Nonterminal]) -> Nonterminal:
        """Find canonical name for a group of rules with identical RHS.

        If all names share a common suffix '_foo', use 'foo' as the canonical name.
        Otherwise, use the first name in the list.
        """
        if len(names) < 2:
            return names[0]

        # Find common suffix
        # Split each name by '_' and check if all have the same last part
        parts = [name.name.split('_') for name in names]
        if all(len(p) > 1 for p in parts):
            # Check if all have the same last part
            last_parts = [p[-1] for p in parts]
            if len(set(last_parts)) == 1:
                # All share the same suffix
                return Nonterminal(last_parts[0])

        # No common suffix, use first name
        return names[0]

    def _apply_renames(self, rename_map: Dict[Nonterminal, Nonterminal]) -> None:
        """Replace all occurrences of old names with new names throughout the grammar."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                self._rename_in_rhs(rule.rhs, rename_map)

    def _rename_in_rhs(self, rhs: Rhs, rename_map: Dict[Nonterminal, Nonterminal]) -> None:
        """Recursively rename nonterminals in RHS."""
        if isinstance(rhs, Nonterminal):
            if rhs in rename_map:
                new_nt = rename_map[rhs]
                rhs.name = new_nt.name
        elif isinstance(rhs, Sequence):
            for elem in rhs.elements:
                self._rename_in_rhs(elem, rename_map)
        elif isinstance(rhs, (Star, Plus, Option)):
            self._rename_in_rhs(rhs.rhs, rename_map)

    def _get_rule_name(self, name: str) -> str:
        """Convert message name to rule name."""
        result = self._to_snake_case(name)
        result = re.sub(r'rel_atom', 'relatom', result)
        result = re.sub(r'rel_term', 'relterm', result)
        result = re.sub(r'date_time', 'datetime', result)
        return result

    def _to_snake_case(self, name: str) -> str:
        """Convert CamelCase to snake_case."""
        result = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', name)
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

        if rule_name in self.final_rules:
            if rule_name in self.generated_rules:
                return
            self.generated_rules.add(rule_name)
            message = self.parser.messages[message_name]
            if self._is_oneof_only_message(message):
                for field in message.oneofs[0].fields:
                    self._generate_message_rule(field.type)
            else:
                for field in message.fields:
                    if self._is_message_type(field.type):
                        self._generate_message_rule(field.type)
            return

        if rule_name in self.generated_rules:
            return

        self.generated_rules.add(rule_name)
        message = self.parser.messages[message_name]
        if self._is_oneof_only_message(message):
            oneof = message.oneofs[0]
            for field in oneof.fields:
                field_rule = self._get_rule_name(field.name)
                field_name_snake = self._to_snake_case(field.name)
                # Create action: lambda value: MessageName(OneOf(:field, value))
                oneof_call = Call(Constructor('OneOf'), [Symbol(field_name_snake), Var('value')])
                wrapper_call = Call(Constructor(message_name), [oneof_call])
                action = Lambda(params=['value'], body=wrapper_call)
                alt_rule = Rule(lhs=Nonterminal(rule_name), rhs=Sequence([Nonterminal(field_rule)]), action=action)
                self._add_rule(alt_rule)

                if self._is_primitive_type(field.type):
                    # For primitive types, generate rule mapping to terminal
                    if field_rule not in self.final_rules:
                        terminal_name = self._map_primitive_type(field.type)
                        field_to_type_rule = Rule(lhs=Nonterminal(field_rule), rhs=Sequence([NamedTerminal(terminal_name)]), action=Lambda(params=['x'], body=Var('x')))
                        self._add_rule(field_to_type_rule)
                else:
                    # For message types, generate rule mapping to type nonterminal
                    type_rule = self._get_rule_name(field.type)
                    if field_rule != type_rule and field_rule not in self.final_rules:
                        field_to_type_rule = Rule(lhs=Nonterminal(field_rule), rhs=Sequence([Nonterminal(type_rule)]), action=Lambda(params=['x'], body=Var('x')))
                        self._add_rule(field_to_type_rule)
            for field in oneof.fields:
                if self._is_message_type(field.type):
                    self._generate_message_rule(field.type)
        else:
            tag = self.rule_literal_renames.get(rule_name, rule_name)
            rhs_symbols: List[Rhs] = [LitTerminal('('), LitTerminal(tag)]
            field_names = []
            for field in message.fields:
                field_symbol = self._generate_field_symbol(field, message_name)
                if field_symbol:
                    rhs_symbols.append(field_symbol)
                    field_names.append(field.name)
            rhs_symbols.append(LitTerminal(')'))
            action = self._generate_action(message_name, rhs_symbols, field_names)
            rule = Rule(lhs=Nonterminal(rule_name), rhs=Sequence(rhs_symbols), action=action, source_type=message_name)
            self._add_rule(rule)
            for field in message.fields:
                if self._is_message_type(field.type):
                    self._generate_message_rule(field.type)

    def _to_sexp_tag(self, name: str) -> str:
        """Convert message name to s-expression tag (same as snake_case conversion)."""
        result = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
        result = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', result)
        return result.lower()

    def _is_sexp_tag(self, symbol: str) -> bool:
        """Check if symbol should be treated as s-expression tag (currently unused)."""
        if not symbol or not symbol.isidentifier():
            return False
        return symbol.islower() or '_' in symbol

    def _generate_field_symbol(self, field: ProtoField, message_name: str = "") -> Optional[Rhs]:
        """Generate grammar symbol for a protobuf field, handling repeated/optional modifiers."""
        if self._is_primitive_type(field.type):
            terminal_name = self._map_primitive_type(field.type)
            base_symbol: Rhs = NamedTerminal(terminal_name)
            if field.is_repeated:
                return Star(base_symbol)
            elif field.is_optional:
                return Option(base_symbol)
            else:
                return base_symbol
        elif self._is_message_type(field.type):
            type_rule_name = self._get_rule_name(field.type)
            message_rule_name = self._get_rule_name(message_name)
            field_rule_name = self._to_field_name(field.name)
            wrapper_rule_name = f"{message_rule_name}_{field_rule_name}"

            if field.is_repeated:
                should_inline = (message_name, field.name) in self.inline_fields
                if should_inline:
                    if self.grammar.has_rule(Nonterminal(wrapper_rule_name)):
                        return Nonterminal(wrapper_rule_name)
                    else:
                        return Star(Nonterminal(type_rule_name))
                else:
                    literal_name = self.rule_literal_renames.get(field_rule_name, field_rule_name)
                    if not self.grammar.has_rule(Nonterminal(wrapper_rule_name)):
                        wrapper_rule = Rule(
                            lhs=Nonterminal(wrapper_rule_name),
                            rhs=Sequence([LitTerminal("("), LitTerminal(literal_name), Star(Nonterminal(type_rule_name)), LitTerminal(")")]),
                            action=Lambda(params=['value'], body=Var('value')),
                            source_type=field.type
                        )
                        self._add_rule(wrapper_rule)
                    return Option(Nonterminal(wrapper_rule_name))
            elif field.is_optional:
                if self.grammar.has_rule(Nonterminal(wrapper_rule_name)):
                    return Option(Nonterminal(wrapper_rule_name))
                else:
                    return Option(Nonterminal(type_rule_name))
            else:
                if self.grammar.has_rule(Nonterminal(wrapper_rule_name)):
                    return Nonterminal(wrapper_rule_name)
                else:
                    return Nonterminal(type_rule_name)
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
