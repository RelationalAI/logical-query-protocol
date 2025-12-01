"""Grammar generation from protobuf specifications.

This module provides the GrammarGenerator class which converts protobuf
message definitions into Lark grammar rules with semantic actions.
"""

import re
from typing import Dict, List, Optional, Set, Tuple

from .grammar import (
    Grammar, Rule, Token, Rhs, Literal, Terminal, Nonterminal, Sequence,
    Star, Plus, Option, Lambda, Call, Var, Symbol, TargetExpr
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

        body = Call(func_name, call_args)
    elif body_str == 'x' or body_str.isidentifier():
        body = Var(body_str)
    else:
        # Default fallback
        body = Var('x')

    return Lambda(params=params, body=body)


class GrammarGenerator:
    """Generator for Lark grammars from protobuf specifications."""
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
        }
        self.rule_literal_renames: Dict[str, str] = {
            "monoid_def": "monoid",
            "monus_def": "monus",
            "conjunction": "and",
            "disjunction": "or",
        }

    def _generate_action(self, message_name: str, rhs: Rhs, field_names: Optional[List[str]] = None) -> TargetExpr:
        """Generate semantic action to construct protobuf message from parsed elements."""
        if isinstance(rhs, Nonterminal):
            return Lambda(params=['x'], body=Var('x'))

        if not isinstance(rhs, Sequence):
            return Lambda(params=['x'], body=Call('str', [Var('x')]))

        # Create parameters for all RHS elements
        params = []
        field_idx = 0
        for elem in rhs.elements:
            if isinstance(elem, Literal):
                # Literals are skipped.
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
        call_args = [Var(name) for name in field_refs]
        body = Call(message_name, call_args)

        return Lambda(params=params, body=body)

    def _next_param_name(self, idx: int) -> str:
        """Generate parameter name for lambda (a, b, c, ...)."""
        if idx < 26:
            return chr(ord('a') + idx)
        return f"x{idx}"

    def _add_rule(self, rule: Rule) -> None:
        """Add a rule to the grammar and track it in generated_rules."""
        self.generated_rules.add(rule.lhs.name)
        self.grammar.add_rule(rule)

    def generate(self, start_message: str = "Transaction") -> Grammar:
        """Generate complete grammar with prepopulated and message-derived rules."""
        self._add_all_prepopulated_rules()

        start_rule = self._get_rule_name(start_message)
        self.grammar.add_rule(Rule(
            lhs=Nonterminal("start"),
            rhs=Nonterminal(start_rule),
            grammar=self.grammar
        ))
        self.grammar.add_rule(Rule(
            lhs=Nonterminal("start"),
            rhs=Nonterminal("fragment"),
            grammar=self.grammar
        ))

        self._generate_message_rule(start_message)

        for message_name in sorted(self.parser.messages.keys()):
            self._generate_message_rule(message_name)

        if 'fragment_id' not in self.generated_rules:
            self._add_rule(Rule(
                lhs=Nonterminal("fragment_id"),
                rhs=Sequence([Literal(":"), Terminal("SYMBOL")]),
                grammar=self.grammar
            ))

        if 'var' not in self.generated_rules:
            self._add_rule(Rule(
                lhs=Nonterminal("var"),
                rhs=Terminal("SYMBOL"),
                grammar=self.grammar
            ))

        if 'value' not in self.generated_rules:
            for val_type in ['STRING', 'NUMBER', 'FLOAT', 'UINT128', 'INT128', 'date', 'datetime', 'MISSING', 'DECIMAL']:
                self._add_rule(Rule(
                    lhs=Nonterminal("value"),
                    rhs=Nonterminal(val_type),
                    grammar=self.grammar
                ))
            self._add_rule(Rule(
                lhs=Nonterminal("value"),
                rhs=Literal("true"),
                grammar=self.grammar
            ))
            self._add_rule(Rule(
                lhs=Nonterminal("value"),
                rhs=Literal("false"),
                grammar=self.grammar
            ))

        self._add_rule(Rule(
            lhs=Nonterminal("date"),
            rhs=Sequence([Literal("("), Literal("date"), Terminal("NUMBER"), Terminal("NUMBER"), Terminal("NUMBER"), Literal(")")]),
            grammar=self.grammar
        ))
        self._add_rule(Rule(
            lhs=Nonterminal("datetime"),
            rhs=Sequence([Literal("("), Literal("datetime"), Terminal("NUMBER"), Terminal("NUMBER"), Terminal("NUMBER"), Terminal("NUMBER"), Terminal("NUMBER"), Terminal("NUMBER"), Option(Terminal("NUMBER")), Literal(")")]),
            grammar=self.grammar
        ))
        self._add_rule(Rule(
            lhs=Nonterminal("config_dict"),
            rhs=Sequence([Literal("{"), Star(Nonterminal("config_key_value")), Literal("}")]),
            grammar=self.grammar
        ))
        self._add_rule(Rule(
            lhs=Nonterminal("config_key_value"),
            rhs=Sequence([Literal(":"), Terminal("SYMBOL"), Nonterminal("value")]),
            grammar=self.grammar
        ))

        self.grammar.tokens.append(Token("SYMBOL", '/[a-zA-Z_][a-zA-Z0-9_.-]*/'))
        self.grammar.tokens.append(Token("MISSING", '"missing"', 1))
        self.grammar.tokens.append(Token("STRING", 'ESCAPED_STRING'))
        self.grammar.tokens.append(Token("NUMBER", '/[-]?\\d+/'))
        self.grammar.tokens.append(Token("INT128", '/[-]?\\d+i128/'))
        self.grammar.tokens.append(Token("UINT128", '/0x[0-9a-fA-F]+/'))
        self.grammar.tokens.append(Token("FLOAT", '/[-]?\\d+\\.\\d+/ | "inf" | "nan"', 1))
        self.grammar.tokens.append(Token("DECIMAL", '/[-]?\\d+\\.\\d+d\\d+/', 2))
        self.grammar.tokens.append(Token("COMMENT", '/;;.*/'))

        self.grammar.ignores.append('/\\s+/')
        self.grammar.ignores.append('COMMENT')

        self.grammar.imports.append('%import common.ESCAPED_STRING -> ESCAPED_STRING')
        self._post_process_grammar()
        return self.grammar

    def _add_all_prepopulated_rules(self) -> None:
        """Add manually-crafted rules that should not be auto-generated."""
        def add_rule(rule: Rule, is_final: bool = True) -> None:
            if is_final:
                self.generated_rules.add(rule.lhs.name)
                self.final_rules.add(rule.lhs.name)
            self.grammar.add_rule(rule)

        add_rule(Rule(
            lhs=Nonterminal("transaction"),
            rhs=Sequence([Literal("("), Literal("transaction"), Option(Nonterminal("configure")), Option(Nonterminal("sync")), Star(Nonterminal("epoch")), Literal(")")]),
            action=Lambda(params=['configure', 'sync', 'epochs'],
                          body=Call('Transaction', [Var('epochs'), Var('configure'), Var('sync')])),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("bindings"),
            rhs=Sequence([Literal("["), Star(Nonterminal("binding")), Option(Sequence([Literal("|"), Star(Nonterminal("binding"))])), Literal("]")]),
            action=Lambda(params=['bindings', 'rest'], body=Call('Bindings', [Var('bindings'), Var('rest')])),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("binding"),
            rhs=Sequence([Terminal("SYMBOL"), Literal("::"), Nonterminal("type")]),
            action=Lambda(params=['symbol', 'type'], body=Call('Binding', [Call('Var', [Var('symbol')]), Var('type')])),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("abstraction"),
            rhs=Sequence([Literal("("), Nonterminal("bindings"), Nonterminal("formula"), Literal(")")]),
            action=Lambda(params=['bindings', 'formula'], body=Call('Abstraction', [Var('bindings'), Var('formula')])),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("name"),
            rhs=Sequence([Literal(":"), Terminal("SYMBOL")]),
            action=Lambda(params=['symbol'], body=Call('Name', [Var('symbol')])),
            grammar=self.grammar
        ))

        add_rule(Rule(
            lhs=Nonterminal("configure"),
            rhs=Sequence([Literal("("), Literal("configure"), Nonterminal("config_dict"), Literal(")")]),
            action=Lambda(params=['config_dict'], body=Call('Configure', [Var('config_dict')])),
            grammar=self.grammar
        ))

        add_rule(Rule(
            lhs=Nonterminal("true"),
            rhs=Sequence([Literal("("), Literal("true"), Literal(")")]),
            action = Lambda(params=[], body=Call('Conjunction', [Call('List', [])])),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("false"),
            rhs=Sequence([Literal("("), Literal("false"), Literal(")")]),
            action = Lambda(params=[], body=Call('Disjunction', [Call('List', [])])),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("formula"),
            rhs=Nonterminal("true"),
            action=Lambda(params=['value'], body=Call('Formula', [Call('OneOf', [Symbol('true'), Var('value')])])),
            grammar=self.grammar
        ), is_final=False)
        add_rule(Rule(
            lhs=Nonterminal("formula"),
            rhs=Nonterminal("false"),
            action=Lambda(params=['value'], body=Call('Formula', [Call('OneOf', [Symbol('false'), Var('value')])])),
            grammar=self.grammar
        ), is_final=False)

        add_rule(Rule(
            lhs=Nonterminal("export"),
            rhs=Sequence([Literal("("), Literal("export"), Nonterminal("export_csvconfig"), Literal(")")]),
            action=Lambda(params=['config'], body=Call('Export', [Var('config')])),
            grammar=self.grammar
        ))

        add_rule(Rule(
            lhs=Nonterminal("export_csvconfig"),
            rhs=Sequence([Literal("("), Literal("export_csvconfig"), Nonterminal("export_path"), Nonterminal("export_csvcolumns"), Nonterminal("config_dict"), Literal(")")]),
            action=Lambda(params=['path', 'columns', 'config'], body=Call('ExportCsvConfig', [Var('path'), Var('columns'), Var('config')])),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("export_csvcolumns"),
            rhs=Sequence([Literal("("), Literal("columns"), Star(Nonterminal("export_csvcolumn")), Literal(")")]),
            action=Lambda(params=['columns'], body=Call('ExportCsvColumns', [Var('columns')])),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("export_csvcolumn"),
            rhs=Sequence([Literal("("), Literal("column"), Terminal("STRING"), Nonterminal("relation_id"), Literal(")")]),
            action=Lambda(params=['name', 'relation_id'], body=Call('ExportCsvColumn', [Var('name'), Var('relation_id')])),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("export_path"),
            rhs=Sequence([Literal("("), Literal("path"), Terminal("STRING"), Literal(")")]),
            action=Lambda(params=['path'], body=Call('ExportPath', [Var('path')])),
            grammar=self.grammar
        ))

        add_rule(Rule(
            lhs=Nonterminal("var"),
            rhs=Sequence([Terminal("SYMBOL")]),
            action=Lambda(params=['symbol'], body=Call('Var', [Var('symbol')])),
            grammar=self.grammar
        ))

        add_rule(Rule(
            lhs=Nonterminal("fragment_id"),
            rhs=Sequence([Literal(":"), Terminal("SYMBOL")]),
            action=Lambda(params=['symbol'], body=Call('FragmentId', [Var('symbol')])),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("relation_id"),
            rhs=Sequence([Literal(":"), Terminal("SYMBOL")]),
            action=Lambda(params=['symbol'], body=Call('RelationId', [Var('symbol')])),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("relation_id"),
            rhs=Terminal("NUMBER"),
            action=Lambda(params=['number'], body=Call('RelationId', [Var('number')])),
            grammar=self.grammar
        ))

        add_rule(Rule(
            lhs=Nonterminal("specialized_value"),
            rhs=Sequence([Literal("#"), Nonterminal("value")]),
            action=Lambda(params=['value'], body=Call('SpecializedValue', [Var('value')])),
            grammar=self.grammar
        ), is_final=True)

        type_rules = {
            "unspecified_type": (Literal("UNKNOWN"), Lambda(params=[], body=Call('UnspecifiedType', []))),
            "string_type": (Literal("STRING"), Lambda(params=[], body=Call('StringType', []))),
            "int_type": (Literal("INT"), Lambda(params=[], body=Call('IntType', []))),
            "float_type": (Literal("FLOAT"), Lambda(params=[], body=Call('FloatType', []))),
            "uint128_type": (Literal("UINT128"), Lambda(params=[], body=Call('Uint128Type', []))),
            "int128_type": (Literal("INT128"), Lambda(params=[], body=Call('Int128Type', []))),
            "boolean_type": (Literal("BOOLEAN"), Lambda(params=[], body=Call('BooleanType', []))),
            "date_type": (Literal("DATE"), Lambda(params=[], body=Call('DateType', []))),
            "datetime_type": (Literal("DATETIME"), Lambda(params=[], body=Call('DatetimeType', []))),
            "missing_type": (Literal("MISSING"), Lambda(params=[], body=Call('MissingType', []))),
            "decimal_type": (Sequence([Literal("("), Literal("DECIMAL"), Terminal("NUMBER"), Terminal("NUMBER"), Literal(")")]), Lambda(params=['precision', 'scale'], body=Call('DecimalType', [Var('precision'), Var('scale')]))),
        }
        for lhs_name, (rhs_value, action) in type_rules.items():
            add_rule(Rule(
                lhs=Nonterminal(lhs_name),
                rhs=rhs_value,
                action=action,
                grammar=self.grammar
            ))

        value_rules = {
            "missing_value": (Terminal("MISSING"), Lambda(params=['value'], body=Call('MissingValue', [Var('value')]))),
            "datetime_value": (Nonterminal("datetime"), Lambda(params=['value'], body=Call('DatetimeValue', [Var('value')]))),
            "date_value": (Nonterminal("date"), Lambda(params=['value'], body=Call('DateValue', [Var('value')]))),
            "int128_value": (Terminal("INT128"), Lambda(params=['value'], body=Call('Int128Value', [Var('value')]))),
            "uint128_value": (Terminal("UINT128"), Lambda(params=['value'], body=Call('Uint128Value', [Var('value')]))),
            "decimal_value": (Terminal("DECIMAL"), Lambda(params=['value'], body=Call('DecimalValue', [Var('value')]))),
        }
        for lhs_name, (rhs_value, action) in value_rules.items():
            add_rule(Rule(
                lhs=Nonterminal(lhs_name),
                rhs=rhs_value,
                action=action,
                grammar=self.grammar
            ))

        # Comparison operators (binary)
        comparison_ops = {
            "eq": ("=", "Eq"),
            "lt": ("<", "Lt"),
            "lt_eq": ("<=", "LtEq"),
            "gt": (">", "Gt"),
            "gt_eq": (">=", "GtEq"),
        }
        for name, (op, class_name) in comparison_ops.items():
            add_rule(Rule(
                lhs=Nonterminal(name),
                rhs=Sequence([Literal("("), Literal(op), Nonterminal("term"), Nonterminal("term"), Literal(")")]),
                action=Lambda(params=['left', 'right'], body=Call(class_name, [Var('left'), Var('right')])),
                grammar=self.grammar
            ))

        # Arithmetic operators (ternary)
        arithmetic_ops = {
            "add": ("+", "Add"),
            "minus": ("-", "Minus"),
            "multiply": ("*", "Multiply"),
            "divide": ("/", "Divide"),
        }
        for name, (op, class_name) in arithmetic_ops.items():
            add_rule(Rule(
                lhs=Nonterminal(name),
                rhs=Sequence([Literal("("), Literal(op), Nonterminal("term"), Nonterminal("term"), Nonterminal("term"), Literal(")")]),
                action=Lambda(params=['left', 'right', 'result'], body=Call(class_name, [Var('left'), Var('right'), Var('result')])),
                grammar=self.grammar
            ))

        for prim in list(comparison_ops.keys()) + list(arithmetic_ops.keys()):
            add_rule(Rule(
                lhs=Nonterminal("primitive"),
                rhs=Nonterminal(prim),
                grammar=self.grammar
            ), is_final=False)

    def _post_process_grammar(self) -> None:
        """Apply grammar rewrite rules."""
        self._rewrite_monoid_rules()
        self._rewrite_string_to_name_optional()
        self._rewrite_string_to_name()
        self._rewrite_fragment_remove_debug_info()
        self._rewrite_terms_optional_to_star()
        self._rewrite_primitive_rule()
        self._rewrite_exists()
        self._rewrite_drop_number_from_instructions()
        self._rewrite_relatom_rule()
        self._rewrite_attribute_rule()
        self._combine_identical_rules()

        self.expected_unreachable.add("debug_info")
        self.expected_unreachable.add("debug_info_ids")
        self.expected_unreachable.add("ivmconfig")

    def _rewrite_monoid_rules(self) -> None:
        """Rewrite *_monoid rules to type "::" OPERATION format."""
        monoid_pattern = re.compile(r'^(\w+)_monoid$')
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                match = monoid_pattern.match(rule.lhs.name)
                if match:
                    operation = match.group(1).upper()
                    operation_name = match.group(1).capitalize()
                    if operation == 'OR':
                        rule.rhs = Sequence([Literal('BOOL'), Literal('::'), Literal(operation)])
                        rule.action = Lambda(params=[], body=Call(f'{operation_name}Monoid', []))
                    elif (isinstance(rule.rhs, Sequence) and len(rule.rhs.elements) == 4 and
                        isinstance(rule.rhs.elements[0], Literal) and rule.rhs.elements[0].name == '(' and
                        isinstance(rule.rhs.elements[1], Literal) and rule.rhs.elements[1].name == rule.lhs.name and
                        isinstance(rule.rhs.elements[2], Nonterminal) and rule.rhs.elements[2].name == 'type' and
                        isinstance(rule.rhs.elements[3], Literal) and rule.rhs.elements[3].name == ')'):

                        # Only rewrite if RHS is "(" <rule_name> type ")"
                        rule.rhs = Sequence([Nonterminal('type'), Literal('::'), Literal(operation)])
                        rule.action = Lambda(params=['type'], body=Call(f'{operation_name}Monoid', [Var('type')]))

    def _rewrite_string_to_name_optional(self) -> None:
        """Replace STRING with name? in output and abort rules."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name in ['output', 'abort']:
                    if isinstance(rule.rhs, Sequence):
                        # Track which positions we're replacing
                        replaced_positions = []
                        for i, symbol in enumerate(rule.rhs.elements):
                            if isinstance(symbol, Terminal) and symbol.name == 'STRING':
                                rule.rhs.elements[i] = Option(Nonterminal('name'))
                                replaced_positions.append(i)

                        # Update action if needed - Option doesn't change parameter count
                        # The parameter is still there, it just becomes optional

    def _rewrite_string_to_name(self) -> None:
        """Replace STRING with name in ffi and pragma rules."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name in ['ffi', 'pragma']:
                    if isinstance(rule.rhs, Sequence):
                        for i, symbol in enumerate(rule.rhs.elements):
                            if isinstance(symbol, Terminal) and symbol.name == 'STRING':
                                rule.rhs.elements[i] = Nonterminal('name')

    def _rewrite_fragment_remove_debug_info(self) -> None:
        """Remove debug_info from fragment rules."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name == 'fragment':
                    if isinstance(rule.rhs, Sequence):
                        new_elements = []
                        for symbol in rule.rhs.elements:
                            if isinstance(symbol, Option):
                                if isinstance(symbol.rhs, Nonterminal) and symbol.rhs.name == 'debug_info':
                                    continue
                            elif isinstance(symbol, Nonterminal) and symbol.name == 'debug_info':
                                continue
                            new_elements.append(symbol)
                        rule.rhs.elements = new_elements

    def _rewrite_terms_optional_to_star(self) -> None:
        """Replace terms? with term* in pragma, atom, ffi, and reduce rules, and with relterm* in rel_atom."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name in ['pragma', 'atom', 'ffi']:
                    if isinstance(rule.rhs, Sequence):
                        for i, symbol in enumerate(rule.rhs.elements):
                            if isinstance(symbol, Option):
                                if isinstance(symbol.rhs, Nonterminal) and symbol.rhs.name == 'terms':
                                    rule.rhs.elements[i] = Star(Nonterminal('term'))
                elif rule.lhs.name == 'rel_atom':
                    if isinstance(rule.rhs, Sequence):
                        for i, symbol in enumerate(rule.rhs.elements):
                            if isinstance(symbol, Option):
                                if isinstance(symbol.rhs, Nonterminal) and symbol.rhs.name == 'terms':
                                    rule.rhs.elements[i] = Star(Nonterminal('relterm'))
                            elif isinstance(symbol, Terminal) and symbol.name == 'STRING':
                                rule.rhs.elements[i] = Nonterminal('name')

    def _rewrite_primitive_rule(self) -> None:
        """Replace STRING with name and term* with relterm* in primitive rules."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name == 'primitive':
                    if isinstance(rule.rhs, Sequence) and len(rule.rhs.elements) >= 2:
                        if (isinstance(rule.rhs.elements[0], Literal) and rule.rhs.elements[0].name == '(' and
                            isinstance(rule.rhs.elements[1], Literal) and rule.rhs.elements[1].name == 'primitive'):
                            for i, symbol in enumerate(rule.rhs.elements):
                                if isinstance(symbol, Terminal) and symbol.name == 'STRING':
                                    rule.rhs.elements[i] = Nonterminal('name')
                                elif isinstance(symbol, Star):
                                    if isinstance(symbol.rhs, Nonterminal) and symbol.rhs.name == 'term':
                                        rule.rhs.elements[i] = Star(Nonterminal('relterm'))

    def _rewrite_exists(self) -> None:
        """Rewrite exists rule to use bindings and formula instead of abstraction."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name == 'exists':
                    if isinstance(rule.rhs, Sequence):
                        new_elements = []
                        for elem in rule.rhs.elements:
                            if isinstance(elem, Nonterminal) and elem.name == 'abstraction':
                                new_elements.append(Nonterminal('bindings'))
                                new_elements.append(Nonterminal('formula'))
                            else:
                                new_elements.append(elem)
                        rule.rhs.elements = new_elements

    def _rewrite_drop_number_from_instructions(self) -> None:
        """Drop NUMBER argument from penultimate position in upsert, monoid_def, and monus_def rules."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name in ['upsert', 'monoid_def', 'monus_def']:
                    if isinstance(rule.rhs, Sequence) and len(rule.rhs.elements) >= 2:
                        penultimate_idx = len(rule.rhs.elements) - 2
                        if penultimate_idx >= 0:
                            elem = rule.rhs.elements[penultimate_idx]
                            if isinstance(elem, Terminal) and elem.name == 'NUMBER':
                                rule.rhs.elements.pop(penultimate_idx)

    def _rewrite_relatom_rule(self) -> None:
        """Replace STRING with name and terms? with relterm* in relatom rules."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name == 'relatom':
                    if isinstance(rule.rhs, Sequence):
                        for i, symbol in enumerate(rule.rhs.elements):
                            if isinstance(symbol, Terminal) and symbol.name == 'STRING':
                                rule.rhs.elements[i] = Nonterminal('name')
                            elif isinstance(symbol, Option):
                                if isinstance(symbol.rhs, Nonterminal) and symbol.rhs.name == 'terms':
                                    rule.rhs.elements[i] = Star(Nonterminal('relterm'))

    def _rewrite_attribute_rule(self) -> None:
        """Replace STRING with name and args? with value* in attribute rules."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name == 'attribute':
                    if isinstance(rule.rhs, Sequence):
                        for i, symbol in enumerate(rule.rhs.elements):
                            if isinstance(symbol, Terminal) and symbol.name == 'STRING':
                                rule.rhs.elements[i] = Nonterminal('name')
                            elif isinstance(symbol, Option):
                                if isinstance(symbol.rhs, Nonterminal) and symbol.rhs.name == 'args':
                                    rule.rhs.elements[i] = Star(Nonterminal('value'))

    def _combine_identical_rules(self) -> None:
        """Combine rules with identical RHS patterns into a single rule with multiple alternatives."""
        # Build a map from (RHS pattern, source_type) to list of LHS names
        # Only combine rules that came from the same protobuf type
        rhs_source_to_lhs: Dict[Tuple[str, Optional[str]], List[str]] = {}
        for lhs_name in self.grammar.rule_order:
            rules_list = self.grammar.rules[lhs_name]
            if len(rules_list) == 1:
                rule = rules_list[0]
                rhs_pattern = str(rule.rhs)
                source_type = rule.source_type
                # Only combine rules with a source_type (i.e., generated from messages)
                if source_type:
                    key = (rhs_pattern, source_type)
                    if key not in rhs_source_to_lhs:
                        rhs_source_to_lhs[key] = []
                    rhs_source_to_lhs[key].append(lhs_name)

        # Track renaming map
        rename_map: Dict[str, str] = {}

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
                            self.grammar.rules[canonical_lhs][0].lhs = Nonterminal(canonical_lhs)
                            del self.grammar.rules[lhs_name]
                            try:
                                idx = self.grammar.rule_order.index(lhs_name)
                                self.grammar.rule_order[idx] = canonical_lhs
                            except ValueError:
                                pass
                    else:
                        # Mark this name as renamed to canonical
                        rename_map[lhs_name] = canonical_lhs
                        # Remove from grammar
                        if lhs_name in self.grammar.rules:
                            del self.grammar.rules[lhs_name]
                        try:
                            self.grammar.rule_order.remove(lhs_name)
                        except ValueError:
                            pass

        # Replace all occurrences of renamed rules throughout the grammar
        if rename_map:
            self._apply_renames(rename_map)

    def _find_canonical_name(self, names: List[str]) -> str:
        """Find canonical name for a group of rules with identical RHS.

        If all names share a common suffix '_foo', use 'foo' as the canonical name.
        Otherwise, use the first name in the list.
        """
        if len(names) < 2:
            return names[0]

        # Find common suffix
        # Split each name by '_' and check if all have the same last part
        parts = [name.split('_') for name in names]
        if all(len(p) > 1 for p in parts):
            # Check if all have the same last part
            last_parts = [p[-1] for p in parts]
            if len(set(last_parts)) == 1:
                # All share the same suffix
                return last_parts[0]

        # No common suffix, use first name
        return names[0]

    def _apply_renames(self, rename_map: Dict[str, str]) -> None:
        """Replace all occurrences of old names with new names throughout the grammar."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                self._rename_in_rhs(rule.rhs, rename_map)

    def _rename_in_rhs(self, rhs: Rhs, rename_map: Dict[str, str]) -> None:
        """Recursively rename nonterminals in RHS."""
        if isinstance(rhs, Nonterminal):
            if rhs.name in rename_map:
                rhs.name = rename_map[rhs.name]
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
                oneof_call = Call('OneOf', [Symbol(field_name_snake), Var('value')])
                wrapper_call = Call(message_name, [oneof_call])
                action = Lambda(params=['value'], body=wrapper_call)
                alt_rule = Rule(lhs=Nonterminal(rule_name), rhs=Nonterminal(field_rule), action=action, grammar=self.grammar)
                self._add_rule(alt_rule)

                if self._is_primitive_type(field.type):
                    # For primitive types, generate rule mapping to terminal
                    if field_rule not in self.final_rules:
                        terminal_name = self._map_primitive_type(field.type)
                        field_to_type_rule = Rule(lhs=Nonterminal(field_rule), rhs=Terminal(terminal_name), action=Lambda(params=['x'], body=Var('x')), grammar=self.grammar)
                        self._add_rule(field_to_type_rule)
                else:
                    # For message types, generate rule mapping to type nonterminal
                    type_rule = self._get_rule_name(field.type)
                    if field_rule != type_rule and field_rule not in self.final_rules:
                        field_to_type_rule = Rule(lhs=Nonterminal(field_rule), rhs=Nonterminal(type_rule), action=Lambda(params=['x'], body=Var('x')), grammar=self.grammar)
                        self._add_rule(field_to_type_rule)
            for field in oneof.fields:
                if self._is_message_type(field.type):
                    self._generate_message_rule(field.type)
        else:
            tag = self.rule_literal_renames.get(rule_name, rule_name)
            rhs_symbols: List[Rhs] = [Literal('('), Literal(tag)]
            field_names = []
            for field in message.fields:
                field_symbol = self._generate_field_symbol(field, message_name)
                if field_symbol:
                    rhs_symbols.append(field_symbol)
                    field_names.append(field.name)
            rhs_symbols.append(Literal(')'))
            rhs_seq = Sequence(rhs_symbols)
            action = self._generate_action(message_name, rhs_seq, field_names)
            rule = Rule(lhs=Nonterminal(rule_name), rhs=rhs_seq, action=action, grammar=self.grammar, source_type=message_name)
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
            base_symbol: Rhs = Terminal(terminal_name)
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
                    if self.grammar.has_rule(wrapper_rule_name):
                        return Nonterminal(wrapper_rule_name)
                    else:
                        return Star(Nonterminal(type_rule_name))
                else:
                    literal_name = self.rule_literal_renames.get(field_rule_name, field_rule_name)
                    if not self.grammar.has_rule(wrapper_rule_name):
                        wrapper_rule = Rule(
                            lhs=Nonterminal(wrapper_rule_name),
                            rhs=Sequence([Literal("("), Literal(literal_name), Star(Nonterminal(type_rule_name)), Literal(")")]),
                            grammar=self.grammar,
                            source_type=field.type
                        )
                        self._add_rule(wrapper_rule)
                    return Option(Nonterminal(wrapper_rule_name))
            elif field.is_optional:
                if self.grammar.has_rule(wrapper_rule_name):
                    return Option(Nonterminal(wrapper_rule_name))
                else:
                    return Option(Nonterminal(type_rule_name))
            else:
                if self.grammar.has_rule(wrapper_rule_name):
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


def generate_grammar(grammar_obj: Grammar, reachable: Set[str]) -> str:
    """Generate grammar text."""
    return grammar_obj.print_grammar(reachable=reachable)


def generate_semantic_actions(grammar_obj: Grammar, reachable: Set[str]) -> str:
    """Generate semantic actions (visitor)."""
    return grammar_obj.print_grammar_with_actions(reachable=reachable)
