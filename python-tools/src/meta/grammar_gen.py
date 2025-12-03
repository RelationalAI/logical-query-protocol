"""Grammar generation from protobuf specifications.

This module provides the GrammarGenerator class which converts protobuf
message definitions into grammar rules with semantic actions.
"""

import re
from types import BuiltinMethodType
from typing import Dict, List, Optional, Set, Tuple

from .grammar import (
    Grammar, Rule, Token, Rhs, Literal, Terminal, Nonterminal,
    Star, Plus, Option
)
from .target import (
    Lambda, Call, Var, Symbol, TargetExpr, Lit, IfElse, Builtin, Constructor
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

    def _generate_action(self, message_name: str, rhs: List[Rhs], field_names: Optional[List[str]] = None) -> TargetExpr:
        """Generate semantic action to construct protobuf message from parsed elements."""

        elements = rhs

        # Create parameters for all RHS elements
        params = []
        field_idx = 0
        for elem in elements:
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
        body = Call(Constructor(message_name), call_args)

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

        self._generate_message_rule(start_message)

        for message_name in sorted(self.parser.messages.keys()):
            self._generate_message_rule(message_name)

        self.grammar.tokens.append(Token("SYMBOL", '/[a-zA-Z_][a-zA-Z0-9_.-]*/'))
        self.grammar.tokens.append(Token("MISSING", '"missing"', 1))
        self.grammar.tokens.append(Token("STRING", '/"(?:[^"\\\\]|\\\\.)*"/'))
        self.grammar.tokens.append(Token("INT", '/[-]?\\d+/'))
        self.grammar.tokens.append(Token("INT128", '/[-]?\\d+i128/'))
        self.grammar.tokens.append(Token("UINT128", '/0x[0-9a-fA-F]+/'))
        self.grammar.tokens.append(Token("FLOAT", '/[-]?\\d+\\.\\d+/ | "inf" | "nan"', 1))
        self.grammar.tokens.append(Token("DECIMAL", '/[-]?\\d+\\.\\d+d\\d+/', 2))

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
            rhs=[Nonterminal("transaction")],
            action=Lambda(params=['transaction'], body=Var('transaction')),

        ))
        add_rule(Rule(
            lhs=Nonterminal("start"),
            rhs=[Nonterminal("fragment")],
            action=Lambda(params=['fragment'], body=Var('fragment')),

        ))

        # add_rule(Rule(
        #     lhs=Nonterminal("monoid"),
        #     rhs=[Nonterminal("type"), Literal("::"), Nonterminal("monoid_name")],
        #     action=Lambda(['type', 'name'], Call(Var('name'), [Var('type')])),
        #
        # ))
        # add_rule(Rule(
        #     lhs=Nonterminal("monoid"),
        #     rhs=[Literal("BOOL"), Literal("::"), Literal("OR")],
        #     action=Lambda([], Call(Constructor('OrMonoid'), [])),
        #
        # ))

        # add_rule(Rule(
        #     lhs=Nonterminal("monoid_name"),
        #     rhs=[Literal("SUM")],
        #     action=Lambda([], Lambda(['type'], Call(Constructor('SumMonoid'), [Var('type')])))
        # ))
        # add_rule(Rule(
        #     lhs=Nonterminal("monoid_name"),
        #     rhs=[Literal("MIN")],
        #     action=Lambda([], Lambda(['type'], Call(Constructor('MinMonoid'), [Var('type')])))
        # ))
        # add_rule(Rule(
        #     lhs=Nonterminal("monoid_name"),
        #     rhs=[Literal("MAX")],
        #     action=Lambda([], Lambda(['type'], Call(Constructor('MaxMonoid'), [Var('type')])))
        # ))

        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=[Nonterminal('date')],
            action=Lambda(params=['value'], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("date_value"), Var('value')])])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=[Nonterminal('datetime')],
            action=Lambda(params=['value'], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("datetime_value"), Var('value')])])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=[Terminal('STRING')],
            action=Lambda(params=['value'], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("string_value"), Var('value')])])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=[Terminal('INT')],
            action=Lambda(params=['value'], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("int_value"), Var('value')])])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=[Terminal('FLOAT')],
            action=Lambda(params=['value'], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("float_value"), Var('value')])])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=[Terminal('UINT128')],
            action=Lambda(params=['value'], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("uint128_value"), Var('value')])])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=[Terminal('INT128')],
            action=Lambda(params=['value'], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("int128_value"), Var('value')])])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=[Terminal('DECIMAL')],
            action=Lambda(params=['value'], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("decimal_value"), Var('value')])])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=[Literal("missing")],
            action=Lambda(params=[], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("missing_value"), Call(Constructor("MissingValue"), [])])])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=[Literal("true")],
            action=Lambda(params=[], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("boolean_value"), Lit(True)])])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("value"),
            rhs=[Literal("false")],
            action=Lambda(params=[], body=Call(Constructor("Value"), [Call(Constructor("OneOf"), [Symbol("boolean_value"), Lit(False)])])),

        ))

        add_rule(Rule(
            lhs=Nonterminal("date"),
            rhs=[Literal("("), Literal("date"), Terminal("INT"), Terminal("INT"), Terminal("INT"), Literal(")")],
            action=Lambda(params=['year', 'month', 'day'], body=Call(Constructor("DateValue"), [Var('year'), Var('month'), Var('day')])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("datetime"),
            rhs=[Literal("("), Literal("datetime"), Terminal("INT"), Terminal("INT"), Terminal("INT"), Terminal("INT"), Terminal("INT"), Terminal("INT"), Option(Terminal("INT")), Literal(")")],
            action=Lambda(params=['year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond'], body=Call(Constructor("DateTimeValue"), [Var('year'), Var('month'), Var('day'), Var('hour'), Var('minute'), Var('second'), IfElse(Call(Builtin('is_none'),[Var('microsecond')]), Lit(0), Var('microsecond'))])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("config_dict"),
            rhs=[Literal("{"), Star(Nonterminal("config_key_value")), Literal("}")],
            action=Lambda(params=['config_key_value'], body=Var('config_key_value')),

        ))
        add_rule(Rule(
            lhs=Nonterminal("config_key_value"),
            rhs=[Literal(":"), Terminal("SYMBOL"), Nonterminal("value")],
            action=Lambda(params=['symbol', 'value'], body=Call(Builtin("Tuple"), [Var('symbol'), Var('value')])),

        ))

        add_rule(Rule(
            lhs=Nonterminal("transaction"),
            rhs=[Literal("("), Literal("transaction"), Option(Nonterminal("configure")), Option(Nonterminal("sync")), Star(Nonterminal("epoch")), Literal(")")],
            action=Lambda(params=['configure', 'sync', 'epochs'],
                          body=Call(Constructor('Transaction'), [Var('epochs'), Var('configure'), Var('sync')])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("bindings"),
            rhs=[Literal("["), Star(Nonterminal("binding")), Literal("]")],
            action=Lambda(params=['keys'], body=Call(Builtin('Tuple'), [Var('keys'), Lit(0)])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("bindings"),
            rhs=[Literal("["), Star(Nonterminal("binding")), Literal("|"), Star(Nonterminal("binding")), Literal("]")],
            action=Lambda(params=['keys', 'values'], body=Call(Builtin('Tuple'), [Call(Builtin('Concat'), [Var('keys'), Var('values')]), Call(Builtin('length'), [Var('values')])])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("binding"),
            rhs=[Terminal("SYMBOL"), Literal("::"), Nonterminal("type")],
            action=Lambda(params=['symbol', 'type'], body=Call(Constructor('Binding'), [Call(Constructor('Var'), [Var('symbol')]), Var('type')])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("abstraction"),
            rhs=[Literal("("), Nonterminal("bindings"), Nonterminal("formula"), Literal(")")],
            action=Lambda(params=['bindings', 'formula'], body=Call(Constructor('Abstraction'), [Var('bindings'), Var('formula')])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("name"),
            rhs=[Literal(":"), Terminal("SYMBOL")],
            action=Lambda(params=['symbol'], body=Call(Constructor('Name'), [Var('symbol')])),

        ))

        add_rule(Rule(
            lhs=Nonterminal("configure"),
            rhs=[Literal("("), Literal("configure"), Nonterminal("config_dict"), Literal(")")],
            action=Lambda(params=['config_dict'], body=Call(Constructor('Configure'), [Var('config_dict')])),

        ))

        add_rule(Rule(
            lhs=Nonterminal("true"),
            rhs=[Literal("("), Literal("true"), Literal(")")],
            action = Lambda(params=[], body=Call(Constructor('Conjunction'), [Call(Builtin('List'), [])])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("false"),
            rhs=[Literal("("), Literal("false"), Literal(")")],
            action = Lambda(params=[], body=Call(Constructor('Disjunction'), [Call(Builtin('List'), [])])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("formula"),
            rhs=[Nonterminal("true")],
            action=Lambda(params=['value'], body=Call(Constructor('Formula'), [Call(Constructor('OneOf'), [Symbol('true'), Var('value')])])),

        ), is_final=False)
        add_rule(Rule(
            lhs=Nonterminal("formula"),
            rhs=[Nonterminal("false")],
            action=Lambda(params=['value'], body=Call(Constructor('Formula'), [Call(Constructor('OneOf'), [Symbol('false'), Var('value')])])),

        ), is_final=False)

        add_rule(Rule(
            lhs=Nonterminal("export"),
            rhs=[Literal("("), Literal("export"), Nonterminal("export_csvconfig"), Literal(")")],
            action=Lambda(params=['config'], body=Call(Constructor('Export'), [Var('config')])),

        ))

        add_rule(Rule(
            lhs=Nonterminal("export_csvconfig"),
            rhs=[Literal("("), Literal("export_csvconfig"), Nonterminal("export_path"), Nonterminal("export_csvcolumns"), Nonterminal("config_dict"), Literal(")")],
            action=Lambda(params=['path', 'columns', 'config'], body=Call(Constructor('ExportCsvConfig'), [Var('path'), Var('columns'), Var('config')])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("export_csvcolumns"),
            rhs=[Literal("("), Literal("columns"), Star(Nonterminal("export_csvcolumn")), Literal(")")],
            action=Lambda(params=['columns'], body=Call(Constructor('ExportCsvColumns'), [Var('columns')])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("export_csvcolumn"),
            rhs=[Literal("("), Literal("column"), Terminal("STRING"), Nonterminal("relation_id"), Literal(")")],
            action=Lambda(params=['name', 'relation_id'], body=Call(Constructor('ExportCsvColumn'), [Var('name'), Var('relation_id')])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("export_path"),
            rhs=[Literal("("), Literal("path"), Terminal("STRING"), Literal(")")],
            action=Lambda(params=['path'], body=Call(Constructor('ExportPath'), [Var('path')])),

        ))

        add_rule(Rule(
            lhs=Nonterminal("var"),
            rhs=[Terminal("SYMBOL")],
            action=Lambda(params=['symbol'], body=Call(Constructor('Var'), [Var('symbol')])),

        ))

        add_rule(Rule(
            lhs=Nonterminal("fragment_id"),
            rhs=[Literal(":"), Terminal("SYMBOL")],
            action=Lambda(params=['symbol'], body=Call(Constructor('FragmentId'), [Var('symbol')])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("relation_id"),
            rhs=[Literal(":"), Terminal("SYMBOL")],
            action=Lambda(params=['symbol'], body=Call(Constructor('RelationId'), [Var('symbol')])),

        ))
        add_rule(Rule(
            lhs=Nonterminal("relation_id"),
            rhs=[Terminal("INT")],
            action=Lambda(params=['INT'], body=Call(Constructor('RelationId'), [Var('INT')])),

        ))

        add_rule(Rule(
            lhs=Nonterminal("specialized_value"),
            rhs=[Literal("#"), Nonterminal("value")],
            action=Lambda(params=['value'], body=Call(Constructor('SpecializedValue'), [Var('value')])),

        ), is_final=True)

        type_rules = {
            "unspecified_type": ([Literal("UNKNOWN")], Lambda(params=[], body=Call(Constructor('UnspecifiedType'), []))),
            "string_type": ([Literal("STRING")], Lambda(params=[], body=Call(Constructor('StringType'), []))),
            "int_type": ([Literal("INT")], Lambda(params=[], body=Call(Constructor('IntType'), []))),
            "float_type": ([Literal("FLOAT")], Lambda(params=[], body=Call(Constructor('FloatType'), []))),
            "uint128_type": ([Literal("UINT128")], Lambda(params=[], body=Call(Constructor('Uint128Type'), []))),
            "int128_type": ([Literal("INT128")], Lambda(params=[], body=Call(Constructor('Int128Type'), []))),
            "boolean_type": ([Literal("BOOLEAN")], Lambda(params=[], body=Call(Constructor('BooleanType'), []))),
            "date_type": ([Literal("DATE")], Lambda(params=[], body=Call(Constructor('DateType'), []))),
            "datetime_type": ([Literal("DATETIME")], Lambda(params=[], body=Call(Constructor('DatetimeType'), []))),
            "missing_type": ([Literal("MISSING")], Lambda(params=[], body=Call(Constructor('MissingType'), []))),
            "decimal_type": ([Literal("("), Literal("DECIMAL"), Terminal("INT"), Terminal("INT"), Literal(")")], Lambda(params=['precision', 'scale'], body=Call(Constructor('DecimalType'), [Var('precision'), Var('scale')]))),
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
                rhs=[Literal("("), Literal(op), Nonterminal("term"), Nonterminal("term"), Literal(")")],
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
                rhs=[Literal("("), Literal(op), Nonterminal("term"), Nonterminal("term"), Nonterminal("term"), Literal(")")],
                action=Lambda(params=['left', 'right', 'result'], body=Call(Constructor('Primitive'), [Lit(prim), Var('left'), Var('right'), Var('result')])),

            ))

        for name, _op, _prim in comparison_ops + arithmetic_ops:
            add_rule(Rule(
                lhs=Nonterminal("primitive"),
                rhs=[Nonterminal(name)],
                action=Lambda(params=['op'], body=Var('op')),

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
        self._rewrite_drop_INT_from_instructions()
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
                    if (len(rule.rhs) == 3 and
                        isinstance(rule.rhs[0], Literal) and rule.rhs[0].name == '(' and
                        isinstance(rule.rhs[1], Literal) and rule.rhs[1].name == rule.lhs.name and
                        isinstance(rule.rhs[2], Literal) and rule.rhs[2].name == ')'):

                        # Rewrite to `BOOL :: <OP>` if RHS is `"(" <rule_name> ")"`
                        rule.rhs = [Literal('BOOL'), Literal('::'), Literal(operation)]
                        rule.action = Lambda(params=[], body=Call(Var(f'{operation_name}Monoid'), []))
                    elif (len(rule.rhs) == 4 and
                        isinstance(rule.rhs[0], Literal) and rule.rhs[0].name == '(' and
                        isinstance(rule.rhs[1], Literal) and rule.rhs[1].name == rule.lhs.name and
                        isinstance(rule.rhs[2], Nonterminal) and rule.rhs[2].name == 'type' and
                        isinstance(rule.rhs[3], Literal) and rule.rhs[3].name == ')'):

                        # Rewrite to `type :: <OP>` if RHS is `"(" <rule_name> type ")"`
                        rule.rhs = [Nonterminal('type'), Literal('::'), Literal(operation)]
                        rule.action = Lambda(params=['type'], body=Call(Var(f'{operation_name}Monoid'), [Var('type')]))

    def _rewrite_string_to_name_optional(self) -> None:
        """Replace STRING with name? in output and abort rules."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name in ['output', 'abort']:
                    if True:
                        # Track which positions we're replacing
                        replaced_positions = []
                        for i, symbol in enumerate(rule.rhs):
                            if isinstance(symbol, Terminal) and symbol.name == 'STRING':
                                rule.rhs[i] = Option(Nonterminal('name'))
                                replaced_positions.append(i)

                        # Update action if needed - Option doesn't change parameter count
                        # The parameter is still there, it just becomes optional

    def _rewrite_string_to_name(self) -> None:
        """Replace STRING with name in ffi and pragma rules."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name in ['ffi', 'pragma']:
                    if True:
                        for i, symbol in enumerate(rule.rhs):
                            if isinstance(symbol, Terminal) and symbol.name == 'STRING':
                                rule.rhs[i] = Nonterminal('name')

    def _rewrite_fragment_remove_debug_info(self) -> None:
        """Remove debug_info from fragment rules."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name == 'fragment':
                    if True:
                        new_elements = []
                        for symbol in rule.rhs:
                            if isinstance(symbol, Option):
                                if isinstance(symbol.rhs, Nonterminal) and symbol.rhs.name == 'debug_info':
                                    continue
                            elif isinstance(symbol, Nonterminal) and symbol.name == 'debug_info':
                                continue
                            new_elements.append(symbol)
                        rule.rhs = new_elements

    def _rewrite_terms_optional_to_star(self) -> None:
        """Replace terms? with term* in pragma, atom, ffi, and reduce rules, and with relterm* in rel_atom."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name in ['pragma', 'atom', 'ffi']:
                    if True:
                        for i, symbol in enumerate(rule.rhs):
                            if isinstance(symbol, Option):
                                if isinstance(symbol.rhs, Nonterminal) and symbol.rhs.name == 'terms':
                                    rule.rhs[i] = Star(Nonterminal('term'))
                elif rule.lhs.name == 'rel_atom':
                    if True:
                        for i, symbol in enumerate(rule.rhs):
                            if isinstance(symbol, Option):
                                if isinstance(symbol.rhs, Nonterminal) and symbol.rhs.name == 'terms':
                                    rule.rhs[i] = Star(Nonterminal('relterm'))
                            elif isinstance(symbol, Terminal) and symbol.name == 'STRING':
                                rule.rhs[i] = Nonterminal('name')

    def _rewrite_primitive_rule(self) -> None:
        """Replace STRING with name and term* with relterm* in primitive rules."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name == 'primitive':
                    if len(rule.rhs) >= 2:
                        if (isinstance(rule.rhs[0], Literal) and rule.rhs[0].name == '(' and
                            isinstance(rule.rhs[1], Literal) and rule.rhs[1].name == 'primitive'):
                            for i, symbol in enumerate(rule.rhs):
                                if isinstance(symbol, Terminal) and symbol.name == 'STRING':
                                    rule.rhs[i] = Nonterminal('name')
                                elif isinstance(symbol, Star):
                                    if isinstance(symbol.rhs, Nonterminal) and symbol.rhs.name == 'term':
                                        rule.rhs[i] = Star(Nonterminal('relterm'))

    def _rewrite_exists(self) -> None:
        """Rewrite exists rule to use bindings and formula instead of abstraction."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name == 'exists':
                    if True:
                        new_elements = []
                        for elem in rule.rhs:
                            if isinstance(elem, Nonterminal) and elem.name == 'abstraction':
                                new_elements.append(Nonterminal('bindings'))
                                new_elements.append(Nonterminal('formula'))
                            else:
                                new_elements.append(elem)
                        rule.rhs = new_elements

    def _rewrite_drop_INT_from_instructions(self) -> None:
        """Drop INT argument from penultimate position in upsert, monoid_def, and monus_def rules."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name in ['upsert', 'monoid_def', 'monus_def']:
                    if len(rule.rhs) >= 2:
                        penultimate_idx = len(rule.rhs) - 2
                        if penultimate_idx >= 0:
                            elem = rule.rhs[penultimate_idx]
                            if isinstance(elem, Terminal) and elem.name == 'INT':
                                rule.rhs.pop(penultimate_idx)

    def _rewrite_relatom_rule(self) -> None:
        """Replace STRING with name and terms? with relterm* in relatom rules."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name == 'relatom':
                    if True:
                        for i, symbol in enumerate(rule.rhs):
                            if isinstance(symbol, Terminal) and symbol.name == 'STRING':
                                rule.rhs[i] = Nonterminal('name')
                            elif isinstance(symbol, Option):
                                if isinstance(symbol.rhs, Nonterminal) and symbol.rhs.name == 'terms':
                                    rule.rhs[i] = Star(Nonterminal('relterm'))

    def _rewrite_attribute_rule(self) -> None:
        """Replace STRING with name and args? with value* in attribute rules."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name == 'attribute':
                    if True:
                        for i, symbol in enumerate(rule.rhs):
                            if isinstance(symbol, Terminal) and symbol.name == 'STRING':
                                rule.rhs[i] = Nonterminal('name')
                            elif isinstance(symbol, Option):
                                if isinstance(symbol.rhs, Nonterminal) and symbol.rhs.name == 'args':
                                    rule.rhs[i] = Star(Nonterminal('value'))

    def _combine_identical_rules(self) -> None:
        """Combine rules with identical RHS patterns into a single rule with multiple alternatives."""
        # Build a map from (RHS pattern, source_type) to list of LHS names
        # Only combine rules that came from the same protobuf type
        rhs_source_to_lhs: Dict[Tuple[str, Optional[str]], List[str]] = {}
        for lhs_name in self.grammar.rules.keys():
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
                    else:
                        # Mark this name as renamed to canonical
                        rename_map[lhs_name] = canonical_lhs
                        # Remove from grammar
                        if lhs_name in self.grammar.rules:
                            del self.grammar.rules[lhs_name]

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

    def _rename_in_rhs(self, rhs: List[Rhs], rename_map: Dict[str, str]) -> None:
        """Recursively rename nonterminals in RHS."""
        for elem in rhs:
            self._rename_in_rhs_elem(elem, rename_map)

    def _rename_in_rhs_elem(self, rhs: Rhs, rename_map: Dict[str, str]) -> None:
        """Recursively rename nonterminals in RHS."""
        if isinstance(rhs, Nonterminal):
            if rhs.name in rename_map:
                rhs.name = rename_map[rhs.name]
        elif isinstance(rhs, (Star, Plus, Option)):
            self._rename_in_rhs_elem(rhs.rhs, rename_map)

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
                alt_rule = Rule(lhs=Nonterminal(rule_name), rhs=[Nonterminal(field_rule)], action=action)
                self._add_rule(alt_rule)

                if self._is_primitive_type(field.type):
                    # For primitive types, generate rule mapping to terminal
                    if field_rule not in self.final_rules:
                        terminal_name = self._map_primitive_type(field.type)
                        field_to_type_rule = Rule(lhs=Nonterminal(field_rule), rhs=[Terminal(terminal_name)], action=Lambda(params=['x'], body=Var('x')))
                        self._add_rule(field_to_type_rule)
                else:
                    # For message types, generate rule mapping to type nonterminal
                    type_rule = self._get_rule_name(field.type)
                    if field_rule != type_rule and field_rule not in self.final_rules:
                        field_to_type_rule = Rule(lhs=Nonterminal(field_rule), rhs=[Nonterminal(type_rule)], action=Lambda(params=['x'], body=Var('x')))
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
            action = self._generate_action(message_name, rhs_symbols, field_names)
            rule = Rule(lhs=Nonterminal(rule_name), rhs=rhs_symbols, action=action, source_type=message_name)
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
                            rhs=[Literal("("), Literal(literal_name), Star(Nonterminal(type_rule_name)), Literal(")")],
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
