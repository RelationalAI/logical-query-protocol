"""Python parser code generation.

This module generates LL(k) recursive-descent parsers in Python from grammars.
The generated parsers support:
- LL(k) parsing with configurable lookahead depth
- Decision tree generation for efficient alternative selection
- Backtracking for ambiguous cases beyond k tokens
- Left-factored continuation methods
- Lexer generation with token patterns and literal matching
"""

from typing import Dict, List, Optional, Set, Tuple

from .grammar import Grammar, Rule, Rhs, Literal, Terminal, Nonterminal, Sequence, Star, Plus, Option
from .analysis import _compute_rhs_first_k


def generate_parser_python(grammar_obj: Grammar, reachable: Set[str]) -> str:
    """Generate LL(k) recursive-descent parser in Python."""
    lines = []
    lines.append('"""')
    lines.append("Auto-generated LL(k) recursive-descent parser.")
    lines.append("")
    lines.append("Generated from protobuf specifications.")
    lines.append('"""')
    lines.append("")
    lines.append("import re")
    lines.append("from typing import List, Optional, Any, Tuple")
    lines.append("")
    lines.append("")

    # First normalize to eliminate *, +, ?
    normalized = grammar_obj.normalize()

    # Then apply left-factoring to eliminate common prefixes
    factored = normalized.left_factor()

    # Recompute reachability after normalization and factoring
    reachable = factored.check_reachability()

    # Check if grammar is LL(2)
    is_ll2, conflicts = factored.check_ll_k(k=2)
    if not is_ll2:
        lines.append("# WARNING: Grammar is not LL(2). Conflicts detected:")
        for conflict in conflicts:
            # Add # to each line of the conflict message
            for line in conflict.split('\n'):
                lines.append(f"# {line}")
        lines.append("")

    nullable = factored.compute_nullable()
    first = factored.compute_first(nullable)
    first_2 = factored.compute_first_k(k=2, nullable=nullable)
    follow = factored.compute_follow(nullable, first)

    lines.append("class ParseError(Exception):")
    lines.append('    """Parse error exception."""')
    lines.append("    pass")
    lines.append("")
    lines.append("")
    lines.append("class Token:")
    lines.append('    """Token representation."""')
    lines.append("    def __init__(self, type: str, value: str, pos: int):")
    lines.append("        self.type = type")
    lines.append("        self.value = value")
    lines.append("        self.pos = pos")
    lines.append("")
    lines.append("    def __repr__(self) -> str:")
    lines.append('        return f"Token({self.type}, {self.value!r}, {self.pos})"')
    lines.append("")
    lines.append("")
    lines.append("class Lexer:")
    lines.append('    """Tokenizer for the input."""')
    lines.append("    def __init__(self, input_str: str):")
    lines.append("        self.input = input_str")
    lines.append("        self.pos = 0")
    lines.append("        self.tokens: List[Token] = []")
    lines.append("        self._tokenize()")
    lines.append("")
    lines.append("    def _tokenize(self) -> None:")
    lines.append('        """Tokenize the input string."""')

    token_patterns = []
    for token in factored.tokens:
        pattern = token.pattern
        if pattern.startswith('/') and pattern.endswith('/'):
            pattern = pattern[1:-1]
        elif pattern == 'ESCAPED_STRING':
            pattern = r'"(?:[^"\\\\]|\\\\.)*"'
        token_patterns.append((token.name, pattern))

    lines.append("        token_specs = [")
    for name, pattern in token_patterns:
        lines.append(f"            ('{name}', r'{pattern}'),")
    lines.append("        ]")
    lines.append("")
    lines.append("        whitespace_re = re.compile(r'\\s+')")
    lines.append("        comment_re = re.compile(r';;.*')")
    lines.append("")
    lines.append("        while self.pos < len(self.input):")
    lines.append("            if whitespace_re.match(self.input, self.pos):")
    lines.append("                match = whitespace_re.match(self.input, self.pos)")
    lines.append("                self.pos = match.end()")
    lines.append("                continue")
    lines.append("")
    lines.append("            if comment_re.match(self.input, self.pos):")
    lines.append("                match = comment_re.match(self.input, self.pos)")
    lines.append("                self.pos = match.end()")
    lines.append("                continue")
    lines.append("")
    lines.append("            matched = False")
    lines.append("            for token_type, pattern in token_specs:")
    lines.append("                regex = re.compile(pattern)")
    lines.append("                match = regex.match(self.input, self.pos)")
    lines.append("                if match:")
    lines.append("                    value = match.group(0)")
    lines.append("                    self.tokens.append(Token(token_type, value, self.pos))")
    lines.append("                    self.pos = match.end()")
    lines.append("                    matched = True")
    lines.append("                    break")
    lines.append("")
    lines.append("            if not matched:")
    lines.append("                for literal in self._get_literals():")
    lines.append("                    if self.input[self.pos:].startswith(literal):")
    lines.append("                        self.tokens.append(Token('LITERAL', literal, self.pos))")
    lines.append("                        self.pos += len(literal)")
    lines.append("                        matched = True")
    lines.append("                        break")
    lines.append("")
    lines.append("            if not matched:")
    lines.append(f"                raise ParseError(f'Unexpected character at position {{self.pos}}: {{self.input[self.pos]!r}}')")
    lines.append("")
    lines.append("        self.tokens.append(Token('$', '', self.pos))")
    lines.append("")
    lines.append("    def _get_literals(self) -> List[str]:")
    lines.append('        """Get all literal strings from the grammar."""')

    literals = set()
    def extract_literals(rhs: Rhs) -> None:
        if isinstance(rhs, Literal):
            literals.add(rhs.name)
        elif isinstance(rhs, Sequence):
            for elem in rhs.elements:
                extract_literals(elem)
        elif isinstance(rhs, (Star, Plus, Option)):
            extract_literals(rhs.rhs)

    for rules_list in factored.rules.values():
        for rule in rules_list:
            extract_literals(rule.rhs)

    sorted_literals = sorted(literals, key=len, reverse=True)
    lines.append("        return [")
    for lit in sorted_literals:
        lines.append(f"            '{lit}',")
    lines.append("        ]")
    lines.append("")
    lines.append("")
    lines.append("class Parser:")
    lines.append('    """LL(k) recursive-descent parser with backtracking."""')
    lines.append("    def __init__(self, tokens: List[Token]):")
    lines.append("        self.tokens = tokens")
    lines.append("        self.pos = 0")
    lines.append("")
    lines.append("    def current(self) -> Token:")
    lines.append('        """Get current token."""')
    lines.append("        return self.tokens[self.pos] if self.pos < len(self.tokens) else Token('$', '', -1)")
    lines.append("")
    lines.append("    def lookahead(self, k: int = 0) -> Token:")
    lines.append('        """Get lookahead token at offset k."""')
    lines.append("        idx = self.pos + k")
    lines.append("        return self.tokens[idx] if idx < len(self.tokens) else Token('$', '', -1)")
    lines.append("")
    lines.append("    def save_position(self) -> int:")
    lines.append('        """Save current position for backtracking."""')
    lines.append("        return self.pos")
    lines.append("")
    lines.append("    def restore_position(self, pos: int) -> None:")
    lines.append('        """Restore position for backtracking."""')
    lines.append("        self.pos = pos")
    lines.append("")
    lines.append("    def consume(self, expected: str) -> None:")
    lines.append('        """Consume a literal token."""')
    lines.append("        token = self.current()")
    lines.append("        if token.type != 'LITERAL' or token.value != expected:")
    lines.append(f"            raise ParseError(f'Expected literal {{expected!r}} but got {{token.type}}={{token.value!r}} at position {{token.pos}}')")
    lines.append("        self.pos += 1")
    lines.append("")
    lines.append("    def consume_terminal(self, expected: str) -> str:")
    lines.append('        """Consume a terminal token and return its value."""')
    lines.append("        token = self.current()")
    lines.append("        if token.type != expected:")
    lines.append(f"            raise ParseError(f'Expected terminal {{expected}} but got {{token.type}} at position {{token.pos}}')")
    lines.append("        self.pos += 1")
    lines.append("        return token.value")
    lines.append("")
    lines.append("    def match_literal(self, literal: str) -> bool:")
    lines.append('        """Check if current token matches literal."""')
    lines.append("        token = self.current()")
    lines.append("        return token.type == 'LITERAL' and token.value == literal")
    lines.append("")
    lines.append("    def match_terminal(self, terminal: str) -> bool:")
    lines.append('        """Check if current token matches terminal."""')
    lines.append("        token = self.current()")
    lines.append("        return token.type == terminal")
    lines.append("")
    lines.append("    def match_lookahead_literal(self, k: int, literal: str) -> bool:")
    lines.append('        """Check if lookahead token at position k matches literal."""')
    lines.append("        token = self.lookahead(k)")
    lines.append("        return token.type == 'LITERAL' and token.value == literal")
    lines.append("")
    lines.append("    def match_lookahead_terminal(self, k: int, terminal: str) -> bool:")
    lines.append('        """Check if lookahead token at position k matches terminal."""')
    lines.append("        token = self.lookahead(k)")
    lines.append("        return token.type == terminal")
    lines.append("")

    for nt_name in factored.rule_order:
        if reachable is not None and nt_name not in reachable:
            continue
        rules_list = factored.rules[nt_name]

        # Check if this is a continuation nonterminal
        is_continuation = nt_name.endswith('_cont_0') or '_cont_' in nt_name

        if is_continuation:
            lines.append(f"    def parse_{nt_name}(self, prefix_results: List[Any]) -> Any:")
            lines.append(f'        """Parse {nt_name} continuation with prefix context."""')
        else:
            lines.append(f"    def parse_{nt_name}(self) -> Any:")
            lines.append(f'        """Parse {nt_name}."""')

        if len(rules_list) == 1:
            rule = rules_list[0]
            if is_continuation and hasattr(rule, 'original_action'):
                # Generate code to combine prefix and suffix using original action
                lines.extend(_generate_continuation_parse(rule, "        "))
            else:
                lines.extend(_generate_parse_rhs(rule.rhs, "        ", rule))
        else:
            # Use fixed k=7 lookahead
            # Why 7? ( decimal 38 18 ) :: MIN
            #        1 2       3  4  5 6  7
            min_k = 2
            first_k_final = factored.compute_first_k(min_k, nullable)

            # Collect sequences and group by tokens progressively
            first_token_to_rules = {}

            for rule_idx, rule in enumerate(rules_list):
                sequences = _compute_rhs_first_k(rule.rhs, first_k_final, nullable, min_k)

                for seq in sequences:
                    if len(seq) == 0:
                        continue
                    first_token = seq[0]

                    if first_token not in first_token_to_rules:
                        first_token_to_rules[first_token] = []
                    first_token_to_rules[first_token].append((seq, rule_idx))

            # Build decision tree recursively by token position
            _generate_decision_tree(lines, first_token_to_rules, rules_list, nt_name, 0, "        ", min_k, is_continuation)

            # Check if any rule is epsilon (empty sequence)
            has_epsilon = any(isinstance(rule.rhs, Sequence) and len(rule.rhs.elements) == 0
                             for rule in rules_list)

            lines.append("        else:")
            if has_epsilon:
                lines.append(f"            return None")
            else:
                lines.append(f"            raise ParseError(f'Unexpected token in {nt_name}: {{self.current()}}')")

        lines.append("")

    lines.append("")
    lines.append("def parse(input_str: str) -> Any:")
    lines.append('    """Parse input string and return parse tree."""')
    lines.append("    lexer = Lexer(input_str)")
    lines.append("    parser = Parser(lexer.tokens)")
    lines.append("    return parser.parse_start()")
    lines.append("")

    return "\n".join(lines)


def _generate_decision_tree(lines: List[str], token_map: Dict, rules_list: List, nt_name: str,
                            depth: int, indent: str, max_depth: int, is_continuation: bool = False) -> None:
    """Generate decision tree for k-token lookahead."""
    if depth >= max_depth:
        # Shouldn't happen but handle gracefully
        return

    # Group alternatives by token at current depth
    next_level = {}
    for seq_or_token, alternatives in token_map.items():
        if isinstance(alternatives, list) and len(alternatives) > 0 and isinstance(alternatives[0], tuple):
            # This is from the initial call: alternatives = [(seq, rule_idx), ...]
            for seq, rule_idx in alternatives:
                if len(seq) > depth:
                    token_at_depth = seq[depth]
                    if token_at_depth not in next_level:
                        next_level[token_at_depth] = []
                    next_level[token_at_depth].append((seq, rule_idx))
        else:
            # Recursively grouped
            next_level[seq_or_token] = alternatives

    for idx, (token, items) in enumerate(next_level.items()):
        # Generate check for this token
        if token.startswith('"'):
            lit = token[1:-1]
            if depth == 0:
                check = f"self.match_literal('{lit}')"
            else:
                check = f"self.match_lookahead_literal({depth}, '{lit}')"
        else:
            if depth == 0:
                check = f"self.match_terminal('{token}')"
            else:
                check = f"self.match_lookahead_terminal({depth}, '{token}')"

        if_keyword = "if" if idx == 0 else "elif"
        lines.append(f"{indent}{if_keyword} {check}:")

        # Check if all items lead to the same rule
        rule_indices = set()
        for seq, rule_idx in items:
            rule_indices.add(rule_idx)

        if len(rule_indices) == 1:
            # All lead to same rule - generate parse code
            rule_idx = rule_indices.pop()
            rule = rules_list[rule_idx]
            if is_continuation and hasattr(rule, 'original_action'):
                lines.extend(_generate_continuation_parse(rule, indent + "    "))
            else:
                lines.extend(_generate_parse_rhs(rule.rhs, indent + "    ", rule))
        elif depth >= 2:
            # Beyond 2 tokens, use backtracking
            lines.append(f"{indent}    # Ambiguous beyond {depth} tokens - use backtracking")
            for bt_idx, rule_idx in enumerate(sorted(rule_indices)):
                rule = rules_list[rule_idx]
                if bt_idx == 0:
                    lines.append(f"{indent}    saved_pos = self.save_position()")
                    lines.append(f"{indent}    try:")
                    if is_continuation and hasattr(rule, 'original_action'):
                        lines.extend(_generate_continuation_parse(rule, indent + "        "))
                    else:
                        lines.extend(_generate_parse_rhs(rule.rhs, indent + "        ", rule))
                elif bt_idx < len(rule_indices) - 1:
                    lines.append(f"{indent}    except ParseError:")
                    lines.append(f"{indent}        self.restore_position(saved_pos)")
                    lines.append(f"{indent}        try:")
                    if is_continuation and hasattr(rule, 'original_action'):
                        lines.extend(_generate_continuation_parse(rule, indent + "            "))
                    else:
                        lines.extend(_generate_parse_rhs(rule.rhs, indent + "            ", rule))
                else:
                    # Last alternative - don't catch error
                    lines.append(f"{indent}    except ParseError:")
                    lines.append(f"{indent}        self.restore_position(saved_pos)")
                    if is_continuation and hasattr(rule, 'original_action'):
                        lines.extend(_generate_continuation_parse(rule, indent + "        "))
                    else:
                        lines.extend(_generate_parse_rhs(rule.rhs, indent + "        ", rule))
        elif depth + 1 < max_depth:
            # Need to check next token
            sub_map = {}
            for seq, rule_idx in items:
                if len(seq) > depth + 1:
                    next_token = seq[depth + 1]
                    if next_token not in sub_map:
                        sub_map[next_token] = []
                    sub_map[next_token].append((seq, rule_idx))

            if sub_map:
                _generate_decision_tree(lines, sub_map, rules_list, nt_name, depth + 1, indent + "    ", max_depth, is_continuation)
            else:
                # All sequences end here - pick first rule
                rule_idx = items[0][1]
                rule = rules_list[rule_idx]
                if is_continuation and hasattr(rule, 'original_action'):
                    lines.extend(_generate_continuation_parse(rule, indent + "    "))
                else:
                    lines.extend(_generate_parse_rhs(rule.rhs, indent + "    ", rule))
        else:
            # Reached max depth - pick first rule
            rule_idx = items[0][1]
            rule = rules_list[rule_idx]
            if is_continuation and hasattr(rule, 'original_action'):
                lines.extend(_generate_continuation_parse(rule, indent + "    "))
            else:
                lines.extend(_generate_parse_rhs(rule.rhs, indent + "    ", rule))


def _generate_continuation_parse(rule: Rule, indent: str) -> List[str]:
    """Generate parsing code for a continuation rule.

    Combines prefix_results with parsed suffix using original semantic action.
    """
    lines = []

    # Parse the suffix
    if isinstance(rule.rhs, Sequence) and rule.rhs.elements:
        lines.append(f"{indent}suffix_results = []")
        for elem in rule.rhs.elements:
            elem_lines = _generate_parse_rhs(elem, indent)
            if isinstance(elem, Literal):
                # Literal: just execute the consume, don't collect result
                for line in elem_lines:
                    lines.append(line)
            else:
                # Terminal/Nonterminal: execute code and collect result
                for line in elem_lines[:-1]:
                    lines.append(line)
                # Last line is the return statement
                result_line = elem_lines[-1]
                result_expr = result_line.strip()[len("return "):]
                lines.append(f"{indent}suffix_results.append({result_expr})")
        lines.append(f"{indent}# Combine prefix and suffix for semantic action")
        lines.append(f"{indent}all_results = prefix_results + suffix_results")
    elif isinstance(rule.rhs, Sequence) and not rule.rhs.elements:
        # Empty suffix
        lines.append(f"{indent}all_results = prefix_results")
    else:
        # Single element suffix
        elem_lines = _generate_parse_rhs(rule.rhs, indent)
        if isinstance(rule.rhs, Literal):
            # Literal: just execute the consume, don't collect result
            for line in elem_lines:
                lines.append(line)
            lines.append(f"{indent}all_results = prefix_results")
        else:
            # Terminal/Nonterminal: execute code and collect result
            for line in elem_lines[:-1]:
                lines.append(line)
            result_line = elem_lines[-1]
            result_expr = result_line.strip()[len("return "):]
            lines.append(f"{indent}all_results = prefix_results + [{result_expr}]")

    lines.append(f"{indent}return all_results")
    return lines


def _generate_parse_rhs(rhs: Rhs, indent: str, rule: Optional[Rule] = None) -> List[str]:
    """Generate parsing code for an RHS.

    If rule has left-factoring metadata, generates code to thread prefix through continuation.
    Returns empty list for Literal (side effect only), single return statement for others.
    """
    lines = []
    if isinstance(rhs, Literal):
        lines.append(f"{indent}self.consume('{rhs.name}')")
        return lines  # No return statement for literals
    elif isinstance(rhs, Terminal):
        lines.append(f"{indent}return self.consume_terminal('{rhs.name}')")
        return lines
    elif isinstance(rhs, Nonterminal):
        lines.append(f"{indent}return self.parse_{rhs.name}()")
        return lines
    elif isinstance(rhs, Sequence):
        if not rhs.elements:
            lines.append(f"{indent}return None")
        else:
            # Check if this is a left-factored rule
            is_factored = rule and hasattr(rule, 'prefix_length') and hasattr(rule, 'original_rules')

            if is_factored:
                # Generate code to parse prefix, call continuation, then combine results
                prefix_len = rule.prefix_length
                cont_nt_name = rhs.elements[-1].name  # Last element is continuation nonterminal

                lines.append(f"{indent}# Parse common prefix")
                lines.append(f"{indent}prefix_results = []")
                for i, elem in enumerate(rhs.elements[:-1]):  # All but continuation
                    elem_lines = _generate_parse_rhs(elem, indent)
                    if isinstance(elem, Literal):
                        # Literal: just execute the consume, don't collect result
                        for line in elem_lines:
                            lines.append(line)
                    else:
                        # Terminal/Nonterminal: execute code and collect result
                        for line in elem_lines[:-1]:
                            lines.append(line)
                        # Last line is the return statement
                        result_line = elem_lines[-1]
                        result_expr = result_line.strip()[len("return "):]
                        lines.append(f"{indent}prefix_results.append({result_expr})")

                lines.append(f"{indent}# Parse continuation with prefix context")
                lines.append(f"{indent}suffix_result = self.parse_{cont_nt_name}(prefix_results)")
                lines.append(f"{indent}return suffix_result")
            else:
                # Normal sequence parsing
                lines.append(f"{indent}results = []")
                for elem in rhs.elements:
                    elem_lines = _generate_parse_rhs(elem, indent)
                    if isinstance(elem, Literal):
                        # Literal: just execute the consume, don't collect result
                        for line in elem_lines:
                            lines.append(line)
                    else:
                        # Terminal/Nonterminal: execute code and collect result
                        for line in elem_lines[:-1]:
                            lines.append(line)
                        # Last line is the return statement
                        result_line = elem_lines[-1]
                        result_expr = result_line.strip()[len("return "):]
                        lines.append(f"{indent}results.append({result_expr})")
                lines.append(f"{indent}return results")
    elif isinstance(rhs, Star):
        lines.append(f"{indent}results = []")
        lines.append(f"{indent}while True:")
        lines.append(f"{indent}    try:")
        inner_lines = _generate_parse_rhs(rhs.rhs, f"{indent}        ")
        for line in inner_lines[:-1]:
            lines.append(line)
        result_line = inner_lines[-1]
        result_expr = result_line.strip()[len("return "):]
        lines.append(f"{indent}        results.append({result_expr})")
        lines.append(f"{indent}    except ParseError:")
        lines.append(f"{indent}        break")
        lines.append(f"{indent}return results")
    elif isinstance(rhs, Plus):
        lines.append(f"{indent}results = []")
        inner_lines = _generate_parse_rhs(rhs.rhs, indent)
        for line in inner_lines[:-1]:
            lines.append(line)
        result_line = inner_lines[-1]
        result_expr = result_line.strip()[len("return "):]
        lines.append(f"{indent}results.append({result_expr})")
        lines.append(f"{indent}while True:")
        lines.append(f"{indent}    try:")
        inner_lines2 = _generate_parse_rhs(rhs.rhs, f"{indent}        ")
        for line in inner_lines2[:-1]:
            lines.append(line)
        result_line2 = inner_lines2[-1]
        result_expr2 = result_line2.strip()[len("return "):]
        lines.append(f"{indent}        results.append({result_expr2})")
        lines.append(f"{indent}    except ParseError:")
        lines.append(f"{indent}        break")
        lines.append(f"{indent}return results")
    elif isinstance(rhs, Option):
        lines.append(f"{indent}try:")
        inner_lines = _generate_parse_rhs(rhs.rhs, f"{indent}    ")
        for line in inner_lines:
            lines.append(line)
        lines.append(f"{indent}except ParseError:")
        lines.append(f"{indent}    return None")
    return lines
