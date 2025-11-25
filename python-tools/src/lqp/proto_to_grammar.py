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

    def to_lark(self) -> str:
        """Convert to Lark grammar format."""
        lines = []
        lines.append("// Auto-generated grammar from protobuf specifications")
        lines.append("")

        for lhs in self.rule_order:
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
        self.grammar = Grammar()
        self.verbose = verbose

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

        if 'type_' not in self.generated_rules:
            self._add_rule(Rule(
                lhs=Nonterminal("type"),
                rhs=Terminal("TYPE_NAME"),
                grammar=self.grammar
            ))
            self._add_rule(Rule(
                lhs=Nonterminal("type"),
                rhs=Sequence([Literal("("), Terminal("TYPE_NAME"), Star(Nonterminal("value")), Literal(")")]),
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

        self.grammar.tokens.append(Token("TYPE_NAME", '"STRING" | "INT" | "FLOAT" | "UINT128" | "INT128"\n         | "DATE" | "DATETIME" | "MISSING" | "DECIMAL" | "BOOLEAN"'))
        self.grammar.tokens.append(Token("SYMBOL", '/[a-zA-Z_][a-zA-Z0-9_.-]*/'))
        self.grammar.tokens.append(Token("MISSING", '"missing"', 1))
        self.grammar.tokens.append(Token("STRING", 'ESCAPED_STRING'))
        self.grammar.tokens.append(Token("NUMBER", '/[-]?\\d+/'))
        self.grammar.tokens.append(Token("INT128", '/[-]?\\d+i128/'))
        self.grammar.tokens.append(Token("UINT128", '/0x[0-9a-fA-F]+/'))
        self.grammar.tokens.append(Token("FLOAT", '/[-]?\\d+\\.\\d+/ | "inf" | "nan"', 1))
        self.grammar.tokens.append(Token("DECIMAL", '/[-]?\\d+\\.\\d+d\\d+/', 2))
        self.grammar.tokens.append(Token("BOOLEAN", '"true" | "false"', 1))
        self.grammar.tokens.append(Token("COMMENT", '/;.*/'))

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
            lhs=Nonterminal("relation_id"),
            rhs=Sequence([Literal("("), Literal(":"), Terminal("SYMBOL"), Literal(")")]),
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
        add_rule(Rule(
            lhs=Nonterminal("relterm"),
            rhs=Nonterminal("specialized_value"),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("relterm"),
            rhs=Nonterminal("term"),
            grammar=self.grammar
        ))

        add_rule(Rule(
            lhs=Nonterminal("string_type"),
            rhs=Literal("STRING"),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("int_type"),
            rhs=Literal("INT"),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("float_type"),
            rhs=Literal("FLOAT"),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("uint128_type"),
            rhs=Literal("UINT128"),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("int128_type"),
            rhs=Literal("INT128"),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("boolean_type"),
            rhs=Literal("BOOLEAN"),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("date_type"),
            rhs=Literal("DATE"),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("datetime_type"),
            rhs=Literal("DATETIME"),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("missing_type"),
            rhs=Literal("MISSING"),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("decimal_type"),
            rhs=Sequence([Literal("("), Literal("DECIMAL"), Terminal("NUMBER"), Terminal("NUMBER"), Literal(")")]),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("unspecified_type"),
            rhs=Literal("UNKNOWN"),
            grammar=self.grammar
        ))

        add_rule(Rule(
            lhs=Nonterminal("missing_value"),
            rhs=Terminal("MISSING"),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("datetime_value"),
            rhs=Nonterminal("datetime"),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("date_value"),
            rhs=Nonterminal("date"),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("int128_value"),
            rhs=Terminal("INT128"),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("uint128_value"),
            rhs=Terminal("UINT128"),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("decimal_value"),
            rhs=Terminal("DECIMAL"),
            grammar=self.grammar
        ))

        add_rule(Rule(
            lhs=Nonterminal("eq"),
            rhs=Sequence([Literal("("), Literal("="), Nonterminal("term"), Nonterminal("term"), Literal(")")]),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("lt"),
            rhs=Sequence([Literal("("), Literal("<"), Nonterminal("term"), Nonterminal("term"), Literal(")")]),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("lt_eq"),
            rhs=Sequence([Literal("("), Literal("<="), Nonterminal("term"), Nonterminal("term"), Literal(")")]),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("gt"),
            rhs=Sequence([Literal("("), Literal(">"), Nonterminal("term"), Nonterminal("term"), Literal(")")]),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("gt_eq"),
            rhs=Sequence([Literal("("), Literal(">="), Nonterminal("term"), Nonterminal("term"), Literal(")")]),
            grammar=self.grammar
        ))

        add_rule(Rule(
            lhs=Nonterminal("add"),
            rhs=Sequence([Literal("("), Literal("+"), Nonterminal("term"), Nonterminal("term"), Nonterminal("term"), Literal(")")]),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("minus"),
            rhs=Sequence([Literal("("), Literal("-"), Nonterminal("term"), Nonterminal("term"), Nonterminal("term"), Literal(")")]),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("multiply"),
            rhs=Sequence([Literal("("), Literal("*"), Nonterminal("term"), Nonterminal("term"), Nonterminal("term"), Literal(")")]),
            grammar=self.grammar
        ))
        add_rule(Rule(
            lhs=Nonterminal("divide"),
            rhs=Sequence([Literal("("), Literal("/"), Nonterminal("term"), Nonterminal("term"), Nonterminal("term"), Literal(")")]),
            grammar=self.grammar
        ))

        for prim in ["eq", "lt", "lt_eq", "gt", "gt_eq", "add", "minus", "multiply", "divide"]:
            add_rule(Rule(
                lhs=Nonterminal("primitive"),
                rhs=Nonterminal(prim),
                grammar=self.grammar
            ), is_final=False)

    def _post_process_grammar(self) -> None:
        """Apply grammar rewrite rules."""
        self._rewrite_monoid_rules()
        self._rewrite_monoid_monus_def_tags()
        self._rewrite_string_to_name_optional()
        self._rewrite_string_to_name_in_ffi_and_pragma()
        self._rewrite_fragment_declarations()
        self._rewrite_fragment_remove_debug_info()
        self._rewrite_terms_optional_to_star()
        self._rewrite_primitive_rule()

    def _rewrite_monoid_rules(self) -> None:
        """Rewrite *_monoid rules to type_ "::" OPERATION format."""
        import re as regex
        monoid_pattern = regex.compile(r'^(\w+)_monoid$')
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                match = monoid_pattern.match(rule.lhs.name)
                if match:
                    operation = match.group(1).upper()
                    if operation == 'OR':
                        rule.rhs = Sequence([Literal('BOOL'), Literal('::'), Literal(operation)])
                    else:
                        rule.rhs = Sequence([Nonterminal('type_'), Literal('::'), Literal(operation)])

    def _rewrite_monoid_monus_def_tags(self) -> None:
        """Rewrite monoid_def → monoid and monus_def → monus in terminal strings."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name in ['monoid_def', 'monus_def']:
                    if isinstance(rule.rhs, Sequence):
                        for i, symbol in enumerate(rule.rhs.elements):
                            if isinstance(symbol, Literal):
                                if symbol.name == 'monoid_def':
                                    rule.rhs.elements[i] = Literal('monoid')
                                elif symbol.name == 'monus_def':
                                    rule.rhs.elements[i] = Literal('monus')

    def _rewrite_string_to_name_optional(self) -> None:
        """Replace STRING with name? in output and abort rules."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name in ['output', 'abort']:
                    if isinstance(rule.rhs, Sequence):
                        for i, symbol in enumerate(rule.rhs.elements):
                            if isinstance(symbol, Terminal) and symbol.name == 'STRING':
                                rule.rhs.elements[i] = Option(Nonterminal('name'))

    def _rewrite_string_to_name_in_ffi_and_pragma(self) -> None:
        """Replace STRING with name in ffi and pragma rules."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name in ['ffi', 'pragma']:
                    if isinstance(rule.rhs, Sequence):
                        for i, symbol in enumerate(rule.rhs.elements):
                            if isinstance(symbol, Terminal) and symbol.name == 'STRING':
                                rule.rhs.elements[i] = Nonterminal('name')

    def _rewrite_fragment_declarations(self) -> None:
        """Replace declarations? with declaration* in fragment rules."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name == 'fragment':
                    if isinstance(rule.rhs, Sequence):
                        for i, symbol in enumerate(rule.rhs.elements):
                            if isinstance(symbol, Option):
                                if isinstance(symbol.rhs, Nonterminal) and symbol.rhs.name == 'declarations':
                                    rule.rhs.elements[i] = Star(Nonterminal('declaration'))

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
        """Replace STRING with name and terms? with relterm* in primitive rules."""
        for rules_list in self.grammar.rules.values():
            for rule in rules_list:
                if rule.lhs.name == 'primitive':
                    if isinstance(rule.rhs, Sequence) and len(rule.rhs.elements) >= 2:
                        if (isinstance(rule.rhs.elements[0], Literal) and rule.rhs.elements[0].name == '(' and
                            isinstance(rule.rhs.elements[1], Literal) and rule.rhs.elements[1].name == 'primitive'):
                            for i, symbol in enumerate(rule.rhs.elements):
                                if isinstance(symbol, Terminal) and symbol.name == 'STRING':
                                    rule.rhs.elements[i] = Nonterminal('name')
                                elif isinstance(symbol, Option):
                                    if isinstance(symbol.rhs, Nonterminal) and symbol.rhs.name == 'terms':
                                        rule.rhs.elements[i] = Star(Nonterminal('relterm'))

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
                field_rule = self._get_rule_name(field.type)
                alt_rule = Rule(lhs=Nonterminal(rule_name), rhs=Nonterminal(field_rule), grammar=self.grammar)
                self._add_rule(alt_rule)
            for field in oneof.fields:
                self._generate_message_rule(field.type)
        else:
            tag = rule_name
            rhs_symbols: List[Rhs] = [Literal('('), Literal(tag)]
            for field in message.fields:
                field_symbol = self._generate_field_symbol(field)
                if field_symbol:
                    rhs_symbols.append(field_symbol)
            rhs_symbols.append(Literal(')'))
            rule = Rule(lhs=Nonterminal(rule_name), rhs=Sequence(rhs_symbols), grammar=self.grammar)
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

    def _generate_field_symbol(self, field: ProtoField) -> Optional[Rhs]:
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
            rule_name = self._get_rule_name(field.type)
            field_rule_name = self._to_field_name(field.name)

            if field.is_repeated:
                if field_rule_name != rule_name:
                    if not self.grammar.has_rule(field_rule_name):
                        wrapper_rule = Rule(
                            lhs=Nonterminal(field_rule_name),
                            rhs=Sequence([Literal("("), Literal(field_rule_name), Star(Nonterminal(rule_name)), Literal(")")]),
                            grammar=self.grammar
                        )
                        self._add_rule(wrapper_rule)
                    return Option(Nonterminal(field_rule_name))
                else:
                    return Star(Nonterminal(rule_name))
            elif field.is_optional:
                return Option(Nonterminal(rule_name))
            else:
                return Nonterminal(rule_name)
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

    unreachable = grammar_obj.get_unreachable_rules()
    if unreachable:
        print("Warning: Unreachable rules detected:")
        for rule_name in unreachable:
            print(f"  {rule_name}")
        print()

    grammar_text = grammar_obj.to_lark()

    if args.output:
        args.output.write_text(grammar_text)
        print(f"Generated grammar written to {args.output}")
    else:
        print(grammar_text)

    return 0


if __name__ == "__main__":
    exit(main())
