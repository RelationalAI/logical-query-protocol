#!/usr/bin/env python3
"""
Tool to generate a Lark grammar from protobuf specifications.

This tool reads protobuf specifications and generates a Lark grammar for parsing
s-expression representations of the same structured data.

The mapping works as follows:
- protobuf message types become grammar rules
- oneof fields become alternatives (|)
- repeated fields become zero-or-more (*)
- message fields become nested s-expressions
- primitive types map to terminal tokens

Special handling:
- Messages with only a oneof become unwrapped alternatives
- Certain primitives like RelationId become tokens
- Some wrapper types are flattened
"""

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


SPECIAL_MAPPINGS = {
    'RelationId': 'relation_id',
    'FragmentId': 'fragment_id',
    'Var': 'var',
    'Value': 'value',
    'Type': 'type_',
}




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
    """Base class for right-hand side of grammar rules."""
    pass


@dataclass
class Terminal(Rhs):
    """Represents a terminal symbol (literal string)."""
    name: str

    def __str__(self) -> str:
        return f'"{self.name}"'


@dataclass
class Nonterminal(Rhs):
    """Represents a nonterminal symbol."""
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass
class Sequence(Rhs):
    """Represents a sequence of RHS elements."""
    elements: List['Rhs'] = field(default_factory=list)

    def __str__(self) -> str:
        return " ".join(str(e) for e in self.elements)


@dataclass
class Union(Rhs):
    """Represents alternatives (|)."""
    alternatives: List['Rhs'] = field(default_factory=list)

    def __str__(self) -> str:
        # Union formatting is handled by Rule.to_pattern
        return " | ".join(str(a) for a in self.alternatives)


@dataclass
class Star(Rhs):
    """Represents zero or more repetitions (*)."""
    rhs: 'Rhs'

    def __str__(self) -> str:
        # Add parentheses if the inner RHS is complex
        if isinstance(self.rhs, (Sequence, Union)):
            return f"({self.rhs})*"
        return f"{self.rhs}*"


@dataclass
class Plus(Rhs):
    """Represents one or more repetitions (+)."""
    rhs: 'Rhs'

    def __str__(self) -> str:
        # Add parentheses if the inner RHS is complex
        if isinstance(self.rhs, (Sequence, Union)):
            return f"({self.rhs})+"
        return f"{self.rhs}+"


@dataclass
class Option(Rhs):
    """Represents optional (?)."""
    rhs: 'Rhs'

    def __str__(self) -> str:
        # Add parentheses if the inner RHS is complex
        if isinstance(self.rhs, (Sequence, Union)):
            return f"({self.rhs})?"
        return f"{self.rhs}?"


@dataclass
class ProtoField:
    """Represents a field in a protobuf message."""
    name: str
    type: str
    number: int
    is_repeated: bool = False
    is_optional: bool = False


@dataclass
class ProtoOneof:
    """Represents a oneof group in a protobuf message."""
    name: str
    fields: List[ProtoField] = field(default_factory=list)


@dataclass
class ProtoEnum:
    """Represents an enum in a protobuf message."""
    name: str
    values: List[Tuple[str, int]] = field(default_factory=list)


@dataclass
class ProtoMessage:
    """Represents a protobuf message."""
    name: str
    fields: List[ProtoField] = field(default_factory=list)
    oneofs: List[ProtoOneof] = field(default_factory=list)
    enums: List[ProtoEnum] = field(default_factory=list)


@dataclass
class Rule:
    """Represents a grammar rule."""
    lhs: Nonterminal
    rhs: Rhs
    action: Optional[str] = None
    grammar: Optional['Grammar'] = field(default=None, repr=False, compare=False)

    def to_pattern(self, grammar: Optional['Grammar'] = None) -> str:
        """Convert RHS to pattern string."""
        return str(self.rhs)


@dataclass
class Token:
    """Represents a token definition."""
    name: str
    pattern: str
    priority: Optional[int] = None


@dataclass
class Grammar:
    """Represents a complete grammar."""
    rules: List[Rule] = field(default_factory=list)
    tokens: List[Token] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    ignores: List[str] = field(default_factory=list)

    def get_rule(self, name: str) -> Optional[Rule]:
        """Get a rule by name."""
        for rule in self.rules:
            if rule.lhs.name == name:
                return rule
        return None

    def has_rule(self, name: str) -> bool:
        """Check if a rule exists."""
        return self.get_rule(name) is not None

    def has_token(self, name: str) -> bool:
        """Check if a token exists."""
        for token in self.tokens:
            if token.name == name:
                return True
        return False

    def to_lark(self) -> str:
        """Convert grammar to Lark format."""
        lines = []
        lines.append("// Auto-generated grammar from protobuf specifications")
        lines.append("")

        rules_by_lhs: Dict[str, List[Rule]] = {}
        for rule in self.rules:
            lhs_name = rule.lhs.name
            if lhs_name not in rules_by_lhs:
                rules_by_lhs[lhs_name] = []
            rules_by_lhs[lhs_name].append(rule)

        for lhs, rules_list in rules_by_lhs.items():
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
    """Parse protobuf files into an internal representation."""

    def __init__(self):
        self.messages: Dict[str, ProtoMessage] = {}
        self.enums: Dict[str, ProtoEnum] = {}

    def parse_file(self, filepath: Path) -> None:
        """Parse a single protobuf file."""
        content = filepath.read_text()
        content = self._remove_comments(content)
        self._parse_content(content)

    def _remove_comments(self, content: str) -> str:
        """Remove C-style comments from protobuf content."""
        content = re.sub(r'//.*?\n', '\n', content)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        return content

    def _parse_content(self, content: str) -> None:
        """Parse protobuf content."""
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
        """Extract content within braces, handling nesting."""
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
        """Parse a message definition."""
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
        """Parse an enum definition."""
        enum_obj = ProtoEnum(name=name)
        for match in re.finditer(r'(\w+)\s*=\s*(\d+);', body):
            value_name = match.group(1)
            value_number = int(match.group(2))
            enum_obj.values.append((value_name, value_number))
        return enum_obj


class GrammarGenerator:
    """Generate a Lark grammar from parsed protobuf messages."""

    def __init__(self, parser: ProtoParser, verbose: bool = False):
        self.parser = parser
        self.generated_rules: Set[str] = set()
        self.grammar = Grammar()
        self.verbose = verbose
        self.auto_generated_rules: Dict[str, List[Rule]] = {}
        self._warned_rules: Set[str] = set()

    def generate(self, start_message: str = "Transaction") -> Grammar:
        """Generate a complete grammar."""
        # Add prepopulated rules first
        self._add_all_prepopulated_rules()

        start_rule = self._get_rule_name(start_message)
        self.grammar.rules.append(Rule(
            lhs=Nonterminal("start"),
            rhs=[Nonterminal(start_rule)],
            grammar=self.grammar
        ))
        self.grammar.rules.append(Rule(
            lhs=Nonterminal("start"),
            rhs=[Nonterminal("fragment")],
            grammar=self.grammar
        ))

        self._generate_message_rule(start_message)

        for message_name in sorted(self.parser.messages.keys()):
            if message_name not in self.generated_rules:
                self._generate_message_rule(message_name)

        # Add terminal mapping rules
        if 'relation_id' not in self.generated_rules:
            self.grammar.rules.append(Rule(
                lhs=Nonterminal("relation_id"),
                rhs=[Terminal("("), Terminal(":"), Nonterminal("SYMBOL"), Terminal(")")],
                grammar=self.grammar
            ))
            self.grammar.rules.append(Rule(
                lhs=Nonterminal("relation_id"),
                rhs=[Nonterminal("NUMBER")],
                grammar=self.grammar
            ))

        if 'fragment_id' not in self.generated_rules:
            self.grammar.rules.append(Rule(
                lhs=Nonterminal("fragment_id"),
                rhs=[Terminal(":"), Nonterminal("SYMBOL")],
                grammar=self.grammar
            ))

        if 'var' not in self.generated_rules:
            self.grammar.rules.append(Rule(
                lhs=Nonterminal("var"),
                rhs=[Nonterminal("SYMBOL")],
                grammar=self.grammar
            ))

        if 'value' not in self.generated_rules:
            for val_type in ['STRING', 'NUMBER', 'FLOAT', 'UINT128', 'INT128', 'date', 'datetime', 'MISSING', 'DECIMAL', 'BOOLEAN']:
                self.grammar.rules.append(Rule(
                    lhs=Nonterminal("value"),
                    rhs=[Nonterminal(val_type)],
                    grammar=self.grammar
                ))

        if 'type_' not in self.generated_rules:
            self.grammar.rules.append(Rule(
                lhs=Nonterminal("type_"),
                rhs=[Nonterminal("TYPE_NAME")],
                grammar=self.grammar
            ))
            self.grammar.rules.append(Rule(
                lhs=Nonterminal("type_"),
                rhs=[Terminal("("), Nonterminal("TYPE_NAME"), Star(Nonterminal("value")), Terminal(")")],
                grammar=self.grammar
            ))


        self.grammar.rules.append(Rule(
            lhs=Nonterminal("date"),
            rhs=[Terminal("("), Terminal("date"), Nonterminal("NUMBER"), Nonterminal("NUMBER"), Nonterminal("NUMBER"), Terminal(")")],
            grammar=self.grammar
        ))
        self.grammar.rules.append(Rule(
            lhs=Nonterminal("datetime"),
            rhs=[Terminal("("), Terminal("datetime"), Nonterminal("NUMBER"), Nonterminal("NUMBER"), Nonterminal("NUMBER"), Nonterminal("NUMBER"), Nonterminal("NUMBER"), Nonterminal("NUMBER"), Option(Nonterminal("NUMBER")), Terminal(")")],
            grammar=self.grammar
        ))
        self.grammar.rules.append(Rule(
            lhs=Nonterminal("config_dict"),
            rhs=[Terminal("{"), Star(Nonterminal("config_key_value")), Terminal("}")],
            grammar=self.grammar
        ))
        self.grammar.rules.append(Rule(
            lhs=Nonterminal("config_key_value"),
            rhs=[Terminal(":"), Nonterminal("SYMBOL"), Nonterminal("value")],
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
        self.grammar.tokens.append(Token("COMMENT", '/;;.*/'))

        self.grammar.ignores.append('/\\s+/')
        self.grammar.ignores.append('COMMENT')

        self.grammar.imports.append('%import common.ESCAPED_STRING -> ESCAPED_STRING')

        self._post_process_grammar()

        return self.grammar

    def _add_all_prepopulated_rules(self) -> None:
        """Add all prepopulated rules that override auto-generated ones."""
        self._add_prepopulated_rule(Rule(
            lhs=Nonterminal("transaction"),
            rhs=[Terminal("("), Terminal("transaction"), Option(Nonterminal("configure")), Star(Nonterminal("epoch")), Terminal(")")],
            grammar=self.grammar
        ))
        # TODO: bindings rule needs Group support for ("|" right_bindings)?
        # For now, create a simplified version
        self._add_prepopulated_rule(Rule(
            lhs=Nonterminal("bindings"),
            rhs=[Terminal("["), Nonterminal("left_bindings"), Option(Terminal("|")), Option(Nonterminal("right_bindings")), Terminal("]")],
            grammar=self.grammar
        ))
        self._add_prepopulated_rule(Rule(
            lhs=Nonterminal("left_bindings"),
            rhs=[Star(Nonterminal("binding"))],
            grammar=self.grammar
        ))
        self._add_prepopulated_rule(Rule(
            lhs=Nonterminal("right_bindings"),
            rhs=[Star(Nonterminal("binding"))],
            grammar=self.grammar
        ))
        self._add_prepopulated_rule(Rule(
            lhs=Nonterminal("binding"),
            rhs=[Nonterminal("SYMBOL"), Terminal("::"), Nonterminal("type_")],
            grammar=self.grammar
        ))
        self._add_prepopulated_rule(Rule(
            lhs=Nonterminal("abstraction"),
            rhs=[Terminal("("), Nonterminal("bindings"), Nonterminal("formula"), Terminal(")")],
            grammar=self.grammar
        ))
        self._add_prepopulated_rule(Rule(
            lhs=Nonterminal("name"),
            rhs=[Terminal(":"), Nonterminal("SYMBOL")],
            grammar=self.grammar
        ))

        self._add_prepopulated_rule(Rule(
            lhs=Nonterminal("eq"),
            rhs=[Terminal("("), Terminal("="), Nonterminal("term"), Nonterminal("term"), Terminal(")")],
            grammar=self.grammar
        ))
        self._add_prepopulated_rule(Rule(
            lhs=Nonterminal("lt"),
            rhs=[Terminal("("), Terminal("<"), Nonterminal("term"), Nonterminal("term"), Terminal(")")],
            grammar=self.grammar
        ))
        self._add_prepopulated_rule(Rule(
            lhs=Nonterminal("lt_eq"),
            rhs=[Terminal("("), Terminal("<="), Nonterminal("term"), Nonterminal("term"), Terminal(")")],
            grammar=self.grammar
        ))
        self._add_prepopulated_rule(Rule(
            lhs=Nonterminal("gt"),
            rhs=[Terminal("("), Terminal(">"), Nonterminal("term"), Nonterminal("term"), Terminal(")")],
            grammar=self.grammar
        ))
        self._add_prepopulated_rule(Rule(
            lhs=Nonterminal("gt_eq"),
            rhs=[Terminal("("), Terminal(">="), Nonterminal("term"), Nonterminal("term"), Terminal(")")],
            grammar=self.grammar
        ))

        self._add_prepopulated_rule(Rule(
            lhs=Nonterminal("add"),
            rhs=[Terminal("("), Terminal("+"), Nonterminal("term"), Nonterminal("term"), Nonterminal("term"), Terminal(")")],
            grammar=self.grammar
        ))
        self._add_prepopulated_rule(Rule(
            lhs=Nonterminal("minus"),
            rhs=[Terminal("("), Terminal("-"), Nonterminal("term"), Nonterminal("term"), Nonterminal("term"), Terminal(")")],
            grammar=self.grammar
        ))
        self._add_prepopulated_rule(Rule(
            lhs=Nonterminal("multiply"),
            rhs=[Terminal("("), Terminal("*"), Nonterminal("term"), Nonterminal("term"), Nonterminal("term"), Terminal(")")],
            grammar=self.grammar
        ))
        self._add_prepopulated_rule(Rule(
            lhs=Nonterminal("divide"),
            rhs=[Terminal("("), Terminal("/"), Nonterminal("term"), Nonterminal("term"), Nonterminal("term"), Terminal(")")],
            grammar=self.grammar
        ))

        for prim in ["raw_primitive", "eq", "lt", "lt_eq", "gt", "gt_eq", "add", "minus", "multiply", "divide"]:
            self._add_prepopulated_rule(Rule(
                lhs=Nonterminal("primitive"),
                rhs=[Nonterminal(prim)],
                grammar=self.grammar
            ))
        self._add_prepopulated_rule(Rule(
            lhs=Nonterminal("raw_primitive"),
            rhs=[Terminal("("), Terminal("primitive"), Nonterminal("name"), Star(Nonterminal("rel_term")), Terminal(")")],
            grammar=self.grammar
        ))

    def _post_process_grammar(self) -> None:
        """Apply rewrite rules to the grammar."""
        self._rewrite_monoid_rules()
        self._rewrite_monoid_monus_def_tags()
        self._rewrite_string_to_name_optional()
        self._rewrite_string_to_name_in_ffi_and_pragma()

    def _rewrite_monoid_rules(self) -> None:
        """Rewrite monoid rules to use type_ "::" "OPERATION" format."""
        import re as regex

        monoid_pattern = regex.compile(r'^(\w+)_monoid$')

        for rule in self.grammar.rules:
            match = monoid_pattern.match(rule.lhs.name)
            if match:
                operation = match.group(1).upper()
                if operation == 'OR':
                    rule.rhs = [Nonterminal('BOOL'), Terminal('::'), Terminal(operation)]
                else:
                    rule.rhs = [Nonterminal('type_'), Terminal('::'), Terminal(operation)]

    def _rewrite_monoid_monus_def_tags(self) -> None:
        """Rewrite 'monoid_def' tag to 'monoid' and 'monus_def' tag to 'monus'."""
        for rule in self.grammar.rules:
            if rule.lhs.name in ['monoid_def', 'monus_def']:
                for i, symbol in enumerate(rule.rhs):
                    if isinstance(symbol, Terminal):
                        if symbol.name == 'monoid_def':
                            rule.rhs[i] = Terminal('monoid')
                        elif symbol.name == 'monus_def':
                            rule.rhs[i] = Terminal('monus')

    def _rewrite_string_to_name_optional(self) -> None:
        """Replace STRING with name? in output and abort rules."""
        for rule in self.grammar.rules:
            if rule.lhs.name in ['output', 'abort']:
                for i, symbol in enumerate(rule.rhs):
                    if isinstance(symbol, Nonterminal) and symbol.name == 'STRING':
                        rule.rhs[i] = Option(Nonterminal('name'))

    def _rewrite_string_to_name_in_ffi_and_pragma(self) -> None:
        """Replace STRING with name in ffi and pragma rules."""
        for rule in self.grammar.rules:
            if rule.lhs.name in ['ffi', 'pragma']:
                for i, symbol in enumerate(rule.rhs):
                    if isinstance(symbol, Nonterminal) and symbol.name == 'STRING':
                        rule.rhs[i] = Nonterminal('name')

    def _add_prepopulated_rule(self, rule: Rule) -> None:
        """Add a pre-populated rule and mark it to prevent auto-generation."""
        name = rule.lhs.name
        # Mark this rule as generated so it won't be auto-generated
        self.generated_rules.add(name)
        self.grammar.rules.append(rule)

    def _get_rule_name(self, name: str) -> str:
        """Get the grammar rule name for a message."""
        if name in SPECIAL_MAPPINGS:
            return SPECIAL_MAPPINGS[name]
        return self._to_rule_name(name)

    def _to_rule_name(self, name: str) -> str:
        """Convert a message name to a grammar rule name."""
        result = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
        result = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', result)
        return result.lower()

    def _to_field_name(self, name: str) -> str:
        """Convert a field name to snake_case."""
        return name.replace('-', '_').replace('.', '_')

    def _is_oneof_only_message(self, message: ProtoMessage) -> bool:
        """Check if a message contains only a single oneof and no other fields."""
        return len(message.oneofs) > 0 and len(message.fields) == 0

    def _generate_message_rule(self, message_name: str) -> None:
        """Generate a grammar rule for a message."""
        if message_name in self.generated_rules:
            return

        if message_name not in self.parser.messages:
            return

        if message_name in SPECIAL_MAPPINGS:
            self.generated_rules.add(message_name)
            return

        self.generated_rules.add(message_name)
        message = self.parser.messages[message_name]
        rule_name = self._to_rule_name(message_name)

        # Skip if a prepopulated rule already exists for this rule name
        if rule_name in self.generated_rules:
            return

        if self._is_oneof_only_message(message):
            oneof = message.oneofs[0]
            alternatives = []
            rules_for_nonterm = []
            for field in oneof.fields:
                field_rule = self._get_rule_name(field.type)
                alternatives.append(field_rule)

            for alt in alternatives:
                alt_rule = Rule(lhs=Nonterminal(rule_name), rhs=[Nonterminal(alt)], grammar=self.grammar)
                self.grammar.rules.append(alt_rule)
                rules_for_nonterm.append(alt_rule)

            self.auto_generated_rules[rule_name] = rules_for_nonterm

            for field in oneof.fields:
                self._generate_message_rule(field.type)
        else:
            tag = self._to_sexp_tag(message_name)

            rhs_symbols: List[GrammarSymbol] = [Terminal('('), Terminal(tag)]
            for field in message.fields:
                field_symbol = self._generate_field_symbol(field)
                if field_symbol:
                    rhs_symbols.append(field_symbol)
            rhs_symbols.append(Terminal(')'))

            rule = Rule(lhs=Nonterminal(rule_name), rhs=rhs_symbols, grammar=self.grammar)
            self.grammar.rules.append(rule)
            self.auto_generated_rules[rule_name] = [rule]

            for field in message.fields:
                if self._is_message_type(field.type):
                    self._generate_message_rule(field.type)

    def _to_sexp_tag(self, name: str) -> str:
        """Convert a message name to an s-expression tag."""
        result = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
        result = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', result)
        return result.lower()

    def _is_sexp_tag(self, symbol: str) -> bool:
        """Check if a symbol is an s-expression tag (should be quoted as literal)."""
        if not symbol or not symbol.isidentifier():
            return False
        return symbol.islower() or '_' in symbol

    def _generate_field_symbol(self, field: ProtoField) -> Optional[GrammarSymbol]:
        """Generate a symbol for a field."""
        if self._is_primitive_type(field.type):
            terminal_name = self._map_primitive_type(field.type)
            base_symbol: GrammarSymbol = Nonterminal(terminal_name)
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
                # Check if field name differs from type name - if so, create wrapper rule
                if field_rule_name != rule_name:
                    # Only add wrapper rule if it doesn't already exist
                    if not self.grammar.has_rule(field_rule_name):
                        # Create wrapper rule: field_name: "(" "field_name" type* ")"
                        wrapper_rule = Rule(
                            lhs=Nonterminal(field_rule_name),
                            rhs=[Terminal("("), Terminal(field_rule_name), Star(Nonterminal(rule_name)), Terminal(")")],
                            grammar=self.grammar
                        )
                        self.grammar.rules.append(wrapper_rule)
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
        """Check if a type is a protobuf primitive."""
        return type_name in PRIMITIVE_TYPES

    def _is_message_type(self, type_name: str) -> bool:
        """Check if a type is a message type."""
        return type_name in self.parser.messages

    def _map_primitive_type(self, type_name: str) -> str:
        """Map protobuf primitive types to grammar terminals."""
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
    grammar_text = grammar_obj.to_lark()

    if args.output:
        args.output.write_text(grammar_text)
        print(f"Generated grammar written to {args.output}")
    else:
        print(grammar_text)

    return 0


if __name__ == "__main__":
    exit(main())
