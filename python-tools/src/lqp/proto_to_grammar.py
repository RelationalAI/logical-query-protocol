#!/usr/bin/env python3
"""
Generate a Lark grammar from protobuf specifications.

Reads protobuf files and generates a Lark grammar for parsing s-expression
representations of the protobuf messages.

Mapping:
- Message types → grammar rules
- oneof fields → alternatives (|)
- repeated fields → zero-or-more (*)
- optional fields → optional (?)
- Message fields → nested s-expressions
- Primitive types → terminal tokens

Special cases:
- Messages containing only a single oneof and no other fields generate multiple
  rules with the same LHS, one per oneof field type
- Repeated message fields where the field name differs from the type name
  generate wrapper rules
- Certain rules (transaction, bindings, primitive operators) are prepopulated
  rather than auto-generated
"""

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

PRIMITIVE_TYPES = {
    'string': 'STRING',
    'int32': 'NUMBER',
    'int64': 'NUMBER',
    'uint32': 'NUMBER',
    'uint64': 'NUMBER',
    'fixed64': 'NUMBER',
    'bool': 'BOOLEAN',
    'double': 'FLOAT',
    'float': 'FLOAT',
    'bytes': 'STRING',
}


@dataclass
class Rhs:
    """Base class for right-hand sides of grammar rules."""
    pass


@dataclass
class Literal(Rhs):
    """Literal terminal (quoted string in grammar)."""
    name: str

    def __str__(self) -> str:
        return f'"{self.name}"'


@dataclass
class Terminal(Rhs):
    """Token terminal (unquoted uppercase name like SYMBOL, NUMBER)."""
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass
class Nonterminal(Rhs):
    """Nonterminal (rule name)."""
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass
class Sequence(Rhs):
    """Sequence of grammar symbols (concatenation)."""
    elements: List['Rhs'] = field(default_factory=list)

    def __str__(self) -> str:
        return " ".join(str(e) for e in self.elements)


@dataclass
class Union(Rhs):
    """Alternatives (|). Not currently used in generated grammar."""
    alternatives: List['Rhs'] = field(default_factory=list)

    def __str__(self) -> str:
        return " | ".join(str(a) for a in self.alternatives)


@dataclass
class Star(Rhs):
    """Zero or more repetitions (*)."""
    rhs: 'Rhs'

    def __str__(self) -> str:
        if isinstance(self.rhs, (Sequence, Union)):
            return f"({self.rhs})*"
        return f"{self.rhs}*"


@dataclass
class Plus(Rhs):
    """One or more repetitions (+). Not currently used in generated grammar."""
    rhs: 'Rhs'

    def __str__(self) -> str:
        if isinstance(self.rhs, (Sequence, Union)):
            return f"({self.rhs})+"
        return f"{self.rhs}+"


@dataclass
class Option(Rhs):
    """Optional element (?)."""
    rhs: 'Rhs'

    def __str__(self) -> str:
        if isinstance(self.rhs, (Sequence, Union)):
            return f"({self.rhs})?"
        return f"{self.rhs}?"


@dataclass
class ProtoField:
    """Field in a protobuf message."""
    name: str
    type: str
    number: int
    is_repeated: bool = False
    is_optional: bool = False


@dataclass
class ProtoOneof:
    """Oneof group in a protobuf message."""
    name: str
    fields: List[ProtoField] = field(default_factory=list)


@dataclass
class ProtoEnum:
    """Enum definition in a protobuf message."""
    name: str
    values: List[Tuple[str, int]] = field(default_factory=list)


@dataclass
class ProtoMessage:
    """Protobuf message definition."""
    name: str
    fields: List[ProtoField] = field(default_factory=list)
    oneofs: List[ProtoOneof] = field(default_factory=list)
    enums: List[ProtoEnum] = field(default_factory=list)


@dataclass
class Rule:
    """Grammar rule (production)."""
    lhs: Nonterminal
    rhs: Rhs
    action: Optional[str] = None
    grammar: Optional['Grammar'] = field(default=None, repr=False, compare=False)
    source_type: Optional[str] = None  # Track the protobuf type this rule came from

    def to_pattern(self, grammar: Optional['Grammar'] = None) -> str:
        """Convert RHS to pattern string."""
        return str(self.rhs)


@dataclass
class Token:
    """Token definition (terminal with regex pattern)."""
    name: str
    pattern: str
    priority: Optional[int] = None


@dataclass
class Grammar:
    """Complete grammar specification."""
    rules: Dict[str, List[Rule]] = field(default_factory=dict)
    rule_order: List[str] = field(default_factory=list)
    tokens: List[Token] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    ignores: List[str] = field(default_factory=list)

    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the grammar."""
        lhs_name = rule.lhs.name
        if lhs_name not in self.rules:
            self.rules[lhs_name] = []
            self.rule_order.append(lhs_name)
        self.rules[lhs_name].append(rule)

    def get_rules(self, name: str) -> List[Rule]:
        """Get all rules with the given LHS name."""
        return self.rules.get(name, [])

    def has_rule(self, name: str) -> bool:
        """Check if any rule has the given LHS name."""
        return name in self.rules

    def has_token(self, name: str) -> bool:
        """Check if a token with the given name exists."""
        for token in self.tokens:
            if token.name == name:
                return True
        return False

    def check_reachability(self) -> Set[str]:
        """
        Compute set of reachable nonterminals from start symbol.

        Returns set of rule names that can be reached.
        """
        if 'start' not in self.rules:
            return set()

        reachable: Set[str] = set(['start'])
        worklist = ['start']

        def extract_nonterminals(rhs: Rhs) -> List[str]:
            """Extract all nonterminal names from an RHS."""
            if isinstance(rhs, Nonterminal):
                return [rhs.name]
            elif isinstance(rhs, Sequence):
                result = []
                for elem in rhs.elements:
                    result.extend(extract_nonterminals(elem))
                return result
            elif isinstance(rhs, Union):
                result = []
                for alt in rhs.alternatives:
                    result.extend(extract_nonterminals(alt))
                return result
            elif isinstance(rhs, (Star, Plus, Option)):
                return extract_nonterminals(rhs.rhs)
            else:
                return []

        while worklist:
            current = worklist.pop()
            if current in self.rules:
                for rule in self.rules[current]:
                    nonterminals = extract_nonterminals(rule.rhs)
                    for nt in nonterminals:
                        if nt not in reachable:
                            reachable.add(nt)
                            worklist.append(nt)

        return reachable

    def get_unreachable_rules(self) -> List[str]:
        """
        Find all rules that are unreachable from start symbol.

        Returns list of rule names that cannot be reached.
        """
        reachable = self.check_reachability()
        unreachable = []
        for rule_name in self.rule_order:
            if rule_name not in reachable:
                unreachable.append(rule_name)
        return unreachable

    def to_lark(self, reachable: Optional[Set[str]] = None) -> str:
        """Convert to Lark grammar format."""
        lines = []
        lines.append("// Auto-generated grammar from protobuf specifications")
        lines.append("")

        for lhs in self.rule_order:
            if reachable is not None and lhs not in reachable:
                continue
            rules_list = self.rules[lhs]
            if len(rules_list) == 1:
                lines.append(f"{lhs}: {rules_list[0].to_pattern(self)}")
            else:
                alternatives = [rule.to_pattern(self) for rule in rules_list]
                lines.append(f"{lhs}: {alternatives[0]}")
                for alt in alternatives[1:]:
                    lines.append(f"    | {alt}")

        if self.rules and self.tokens:
            lines.append("")

        for token in self.tokens:
            if token.priority is not None:
                lines.append(f"{token.name}.{token.priority}: {token.pattern}")
            else:
                lines.append(f"{token.name}: {token.pattern}")

        if self.ignores:
            lines.append("")
            for ignore in self.ignores:
                lines.append(f"%ignore {ignore}")

        if self.imports:
            lines.append("")
            for imp in self.imports:
                lines.append(imp)

        return "\n".join(lines)


class ProtoParser:
    """Parser for protobuf files."""
    def __init__(self):
        self.messages: Dict[str, ProtoMessage] = {}
        self.enums: Dict[str, ProtoEnum] = {}

    def parse_file(self, filepath: Path) -> None:
        """Parse protobuf file and add messages/enums to internal state."""
        content = filepath.read_text()
        content = self._remove_comments(content)
        self._parse_content(content)

    def _remove_comments(self, content: str) -> str:
        """Remove C-style comments."""
        content = re.sub(r'//.*?\n', '\n', content)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        return content

    def _parse_content(self, content: str) -> None:
        """Parse message and enum definitions."""
        i = 0
        while i < len(content):
            message_match = re.match(r'message\s+(\w+)\s*\{', content[i:])
            if message_match:
                message_name = message_match.group(1)
                start = i + message_match.end()
                body, end = self._extract_braced_content(content, start)
                message = self._parse_message(message_name, body)
                self.messages[message_name] = message
                i = end
            else:
                enum_match = re.match(r'enum\s+(\w+)\s*\{', content[i:])
                if enum_match:
                    enum_name = enum_match.group(1)
                    start = i + enum_match.end()
                    body, end = self._extract_braced_content(content, start)
                    enum_obj = self._parse_enum(enum_name, body)
                    self.enums[enum_name] = enum_obj
                    i = end
                else:
                    i += 1

    def _extract_braced_content(self, content: str, start: int) -> tuple[str, int]:
        """Extract content within matching braces, handling nested braces."""
        depth = 1
        i = start
        while i < len(content) and depth > 0:
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
            i += 1
        return content[start:i-1], i

    def _parse_message(self, name: str, body: str) -> ProtoMessage:
        """Parse message definition body into fields, oneofs, and nested enums."""
        message = ProtoMessage(name=name)

        oneof_pattern = r'oneof\s+(\w+)\s*\{((?:[^{}]|\{[^}]*\})*)\}'
        oneofs = {}
        for match in re.finditer(oneof_pattern, body):
            oneof_name = match.group(1)
            oneof_body = match.group(2)
            oneof = ProtoOneof(name=oneof_name)
            oneofs[oneof_name] = oneof
            message.oneofs.append(oneof)

            for field_match in re.finditer(r'(\w+)\s+(\w+)\s*=\s*(\d+);', oneof_body):
                field_type = field_match.group(1)
                field_name = field_match.group(2)
                field_number = int(field_match.group(3))
                proto_field = ProtoField(
                    name=field_name,
                    type=field_type,
                    number=field_number
                )
                oneof.fields.append(proto_field)

        field_pattern = r'(repeated|optional)?\s*(\w+)\s+(\w+)\s*=\s*(\d+);'
        for match in re.finditer(field_pattern, body):
            if any(match.start() >= m.start() and match.end() <= m.end()
                   for m in re.finditer(oneof_pattern, body)):
                continue

            modifier = match.group(1)
            field_type = match.group(2)
            field_name = match.group(3)
            field_number = int(match.group(4))

            if field_type == 'reserved':
                continue

            proto_field = ProtoField(
                name=field_name,
                type=field_type,
                number=field_number,
                is_repeated=modifier == 'repeated',
                is_optional=modifier == 'optional'
            )
            message.fields.append(proto_field)

        enum_pattern = r'enum\s+(\w+)\s*\{([^}]+)\}'
        for match in re.finditer(enum_pattern, body):
            enum_name = match.group(1)
            enum_body = match.group(2)
            enum_obj = self._parse_enum(enum_name, enum_body)
            message.enums.append(enum_obj)

        return message

    def _parse_enum(self, name: str, body: str) -> ProtoEnum:
        """Parse enum definition body into values."""
        enum_obj = ProtoEnum(name=name)
        for match in re.finditer(r'(\w+)\s*=\s*(\d+);', body):
            value_name = match.group(1)
            value_number = int(match.group(2))
            enum_obj.values.append((value_name, value_number))
        return enum_obj


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
            for val_type in ['STRING', 'NUMBER', 'FLOAT', 'UINT128', 'INT128', 'date', 'datetime', 'MISSING', 'DECIMAL', 'BOOLEAN']:
                self._add_rule(Rule(
                    lhs=Nonterminal("value"),
                    rhs=Nonterminal(val_type),
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
        self.grammar.tokens.append(Token("BOOLEAN", '"true" | "false"', 1))
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
            rhs=Sequence([Literal("("), Literal("transaction"), Option(Nonterminal("configure")), Star(Nonterminal("epoch")), Literal(")")]),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("bindings"),
            rhs=Sequence([Literal("["), Star(Nonterminal("binding")), Option(Sequence([Literal("|"), Star(Nonterminal("binding"))])), Literal("]")]),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("binding"),
            rhs=Sequence([Terminal("SYMBOL"), Literal("::"), Nonterminal("type")]),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("abstraction"),
            rhs=Sequence([Literal("("), Nonterminal("bindings"), Nonterminal("formula"), Literal(")")]),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("name"),
            rhs=Sequence([Literal(":"), Terminal("SYMBOL")]),
            grammar=self.grammar
        ))

        add_rule(Rule(
            lhs=Nonterminal("configure"),
            rhs=Sequence([Literal("("), Literal("configure"), Nonterminal("config_dict"), Literal(")")]),
            grammar=self.grammar
        ))

        add_rule(Rule(
            lhs=Nonterminal("true"),
            rhs=Sequence([Literal("("), Literal("true"), Literal(")")]),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("false"),
            rhs=Sequence([Literal("("), Literal("false"), Literal(")")]),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("formula"),
            rhs=Nonterminal("true"),
            grammar=self.grammar
        ), is_final=False)
        add_rule(Rule(
            lhs=Nonterminal("formula"),
            rhs=Nonterminal("false"),
            grammar=self.grammar
        ), is_final=False)

        add_rule(Rule(
            lhs=Nonterminal("export"),
            rhs=Sequence([Literal("("), Literal("export"), Nonterminal("export_csvconfig"), Literal(")")]),
            grammar=self.grammar
        ))

        add_rule(Rule(
            lhs=Nonterminal("export_csvconfig"),
            rhs=Sequence([Literal("("), Literal("export_csvconfig"), Nonterminal("export_path"), Nonterminal("export_csvcolumns"), Nonterminal("config_dict"), Literal(")")]),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("export_csvcolumns"),
            rhs=Sequence([Literal("("), Literal("columns"), Star(Nonterminal("export_csvcolumn")), Literal(")")]),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("export_csvcolumn"),
            rhs=Sequence([Literal("("), Literal("column"), Terminal("STRING"), Nonterminal("relation_id"), Literal(")")]),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("export_path"),
            rhs=Sequence([Literal("("), Literal("path"), Terminal("STRING"), Literal(")")]),
            grammar=self.grammar
        ))

        add_rule(Rule(
            lhs=Nonterminal("var"),
            rhs=Sequence([Terminal("SYMBOL")]),
            grammar=self.grammar
        ))

        add_rule(Rule(
            lhs=Nonterminal("fragment_id"),
            rhs=Sequence([Literal(":"), Terminal("SYMBOL")]),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("relation_id"),
            rhs=Sequence([Literal(":"), Terminal("SYMBOL")]),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("relation_id"),
            rhs=Terminal("NUMBER"),
            grammar=self.grammar
        ))

        add_rule(Rule(
            lhs=Nonterminal("specialized_value"),
            rhs=Sequence([Literal("#"), Nonterminal("value")]),
            grammar=self.grammar
        ))

        type_rules = {
            "unspecified_type": Literal("UNKNOWN"),
            "string_type": Literal("STRING"),
            "int_type": Literal("INT"),
            "float_type": Literal("FLOAT"),
            "uint128_type": Literal("UINT128"),
            "int128_type": Literal("INT128"),
            "boolean_type": Literal("BOOLEAN"),
            "date_type": Literal("DATE"),
            "datetime_type": Literal("DATETIME"),
            "missing_type": Literal("MISSING"),
            "decimal_type": Sequence([Literal("("), Literal("DECIMAL"), Terminal("NUMBER"), Terminal("NUMBER"), Literal(")")]),
        }
        for lhs_name, rhs_value in type_rules.items():
            add_rule(Rule(
                lhs=Nonterminal(lhs_name),
                rhs=rhs_value,
                grammar=self.grammar
            ))

        value_rules = {
            "missing_value": Terminal("MISSING"),
            "datetime_value": Nonterminal("datetime"),
            "date_value": Nonterminal("date"),
            "int128_value": Terminal("INT128"),
            "uint128_value": Terminal("UINT128"),
            "decimal_value": Terminal("DECIMAL"),
        }
        for lhs_name, rhs_value in value_rules.items():
            add_rule(Rule(
                lhs=Nonterminal(lhs_name),
                rhs=rhs_value,
                grammar=self.grammar
            ))

        # Comparison operators (binary)
        comparison_ops = {
            "eq": "=",
            "lt": "<",
            "lt_eq": "<=",
            "gt": ">",
            "gt_eq": ">=",
        }
        for name, op in comparison_ops.items():
            add_rule(Rule(
                lhs=Nonterminal(name),
                rhs=Sequence([Literal("("), Literal(op), Nonterminal("term"), Nonterminal("term"), Literal(")")]),
                grammar=self.grammar
            ))

        # Arithmetic operators (ternary)
        arithmetic_ops = {
            "add": "+",
            "minus": "-",
            "multiply": "*",
            "divide": "/",
        }
        for name, op in arithmetic_ops.items():
            add_rule(Rule(
                lhs=Nonterminal(name),
                rhs=Sequence([Literal("("), Literal(op), Nonterminal("term"), Nonterminal("term"), Nonterminal("term"), Literal(")")]),
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
        import re as regex
        monoid_pattern = regex.compile(r'^(\w+)_monoid$')
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                match = monoid_pattern.match(rule.lhs.name)
                if match:
                    operation = match.group(1).upper()
                    if operation == 'OR':
                        rule.rhs = Sequence([Literal('BOOL'), Literal('::'), Literal(operation)])
                    elif (isinstance(rule.rhs, Sequence) and len(rule.rhs.elements) == 4 and
                        isinstance(rule.rhs.elements[0], Literal) and rule.rhs.elements[0].name == '(' and
                        isinstance(rule.rhs.elements[1], Literal) and rule.rhs.elements[1].name == rule.lhs.name and
                        isinstance(rule.rhs.elements[2], Nonterminal) and rule.rhs.elements[2].name == 'type' and
                        isinstance(rule.rhs.elements[3], Literal) and rule.rhs.elements[3].name == ')'):

                        # Only rewrite if RHS is "(" <rule_name> type ")"
                        rule.rhs = Sequence([Nonterminal('type'), Literal('::'), Literal(operation)])

    def _rewrite_string_to_name_optional(self) -> None:
        """Replace STRING with name? in output and abort rules."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name in ['output', 'abort']:
                    if isinstance(rule.rhs, Sequence):
                        for i, symbol in enumerate(rule.rhs.elements):
                            if isinstance(symbol, Terminal) and symbol.name == 'STRING':
                                rule.rhs.elements[i] = Option(Nonterminal('name'))

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

                # If canonical name differs from first name, need to rename
                if canonical_lhs != lhs_names[0]:
                    rename_map[lhs_names[0]] = canonical_lhs
                    # Move the rule to the new name
                    self.grammar.rules[canonical_lhs] = self.grammar.rules[lhs_names[0]]
                    self.grammar.rules[canonical_lhs][0].lhs = Nonterminal(canonical_lhs)
                    # Update rule_order
                    try:
                        idx = self.grammar.rule_order.index(lhs_names[0])
                        del self.grammar.rule_order[idx]
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
        elif isinstance(rhs, Union):
            for alt in rhs.alternatives:
                self._rename_in_rhs(alt, rename_map)
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
                alt_rule = Rule(lhs=Nonterminal(rule_name), rhs=Nonterminal(field_rule), grammar=self.grammar)
                self._add_rule(alt_rule)

                if self._is_primitive_type(field.type):
                    # For primitive types, generate rule mapping to terminal
                    terminal_name = self._map_primitive_type(field.type)
                    field_to_type_rule = Rule(lhs=Nonterminal(field_rule), rhs=Terminal(terminal_name), grammar=self.grammar)
                    self._add_rule(field_to_type_rule)
                else:
                    # For message types, generate rule mapping to type nonterminal
                    type_rule = self._get_rule_name(field.type)
                    if field_rule != type_rule:
                        field_to_type_rule = Rule(lhs=Nonterminal(field_rule), rhs=Nonterminal(type_rule), grammar=self.grammar)
                        self._add_rule(field_to_type_rule)
            for field in oneof.fields:
                if self._is_message_type(field.type):
                    self._generate_message_rule(field.type)
        else:
            tag = self.rule_literal_renames.get(rule_name, rule_name)
            rhs_symbols: List[Rhs] = [Literal('('), Literal(tag)]
            for field in message.fields:
                field_symbol = self._generate_field_symbol(field, message_name)
                if field_symbol:
                    rhs_symbols.append(field_symbol)
            rhs_symbols.append(Literal(')'))
            rule = Rule(lhs=Nonterminal(rule_name), rhs=Sequence(rhs_symbols), grammar=self.grammar, source_type=message_name)
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


def main():
    parser = argparse.ArgumentParser(
        description="Generate Lark grammar from protobuf specifications"
    )
    parser.add_argument(
        "proto_files",
        nargs="+",
        type=Path,
        help="Protobuf files to parse"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file for generated grammar"
    )
    parser.add_argument(
        "-s", "--start",
        default="Transaction",
        help="Start message for the grammar"
    )

    args = parser.parse_args()

    proto_parser = ProtoParser()
    for proto_file in args.proto_files:
        if not proto_file.exists():
            print(f"Error: File not found: {proto_file}")
            return 1
        proto_parser.parse_file(proto_file)

    generator = GrammarGenerator(proto_parser, verbose=True)
    grammar_obj = generator.generate(args.start)

    reachable = grammar_obj.check_reachability()
    unreachable = grammar_obj.get_unreachable_rules()
    unexpected_unreachable = [r for r in unreachable if r not in generator.expected_unreachable]
    if unexpected_unreachable:
        print("Warning: Unreachable rules detected:")
        for rule_name in unexpected_unreachable:
            print(f"  {rule_name}")
        print()

    grammar_text = grammar_obj.to_lark(reachable=reachable)

    if args.output:
        args.output.write_text(grammar_text)
        print(f"Generated grammar written to {args.output}")
    else:
        print(grammar_text)

    return 0


if __name__ == "__main__":
    exit(main())
