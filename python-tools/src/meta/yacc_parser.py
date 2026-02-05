"""Parser for yacc-like grammar files.

This module provides functions to parse grammar files in a yacc-like format
with Python-style semantic actions.

File structure:
    # Comments start with #
    <directives>
    %%
    <rules>
    %%
    <helper functions in Python>

Directive syntax:
    %token NAME Type           -> declare terminal NAME with type Type
    %type name Type            -> declare nonterminal name with type Type
    %validator_ignore_completeness MessageName -> ignore message in completeness checks

Type syntax:
    String, Int64, Float64, Boolean    -> BaseType
    module.MessageName                 -> MessageType
    List[Type]                         -> ListType
    Tuple[Type1, Type2, ...]           -> TupleType
    Optional[Type]                     -> OptionType

Rule syntax:
    name
        : rhs1 { action1 }
        | rhs2 { action2 }
        ...

    Or single-line:
    name : rhs { action }

RHS syntax:
    "literal"           -> LitTerminal
    TERMINAL_NAME       -> NamedTerminal (uppercase)
    nonterminal_name    -> Nonterminal (lowercase)
    element*            -> Star(element)
    element?            -> Option(element)

Action syntax (Python-like):
    $1, $2, ...         -> reference to RHS element (1-indexed, skipping literals)
    $1[0], $1[1]        -> tuple element access
    module.Message(f1=e1, ...)  -> message constructor
    func(args)          -> function call
    [e1, e2, ...]       -> list literal
    "string"            -> string literal
    123                 -> integer literal
    True, False         -> boolean literals
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .grammar import (
    Rhs, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence, Rule,
    GrammarConfig, TerminalDef
)
from .target import TargetType, BaseType, MessageType, ListType, OptionType, TupleType

# Import from action parser
from .yacc_action_parser import (
    YaccGrammarError,
    TypeContext,
    TerminalInfo,
    parse_action,
    parse_helper_functions,
)


def parse_type(text: str) -> TargetType:
    """Parse a type expression.

    Syntax:
        String, Int64, Float64, Boolean    -> BaseType
        module.MessageName                 -> MessageType
        List[Type]                         -> ListType
        Tuple[Type1, Type2, ...]           -> TupleType
        Optional[Type]                     -> OptionType
    """
    text = text.strip()

    # Handle bracket syntax: List[T], Tuple[X, Y], Optional[T]
    bracket_match = re.match(r'^(\w+)\[(.+)\]$', text)
    if bracket_match:
        constructor = bracket_match.group(1)
        args_text = bracket_match.group(2)
        args = _split_bracket_type_args(args_text)

        if constructor == "List":
            if len(args) != 1:
                raise YaccGrammarError(f"List type requires exactly one argument: {text}")
            return ListType(parse_type(args[0]))
        elif constructor == "Optional":
            if len(args) != 1:
                raise YaccGrammarError(f"Optional type requires exactly one argument: {text}")
            return OptionType(parse_type(args[0]))
        elif constructor == "Tuple":
            if len(args) < 1:
                raise YaccGrammarError(f"Tuple type requires at least one argument: {text}")
            return TupleType(tuple(parse_type(a) for a in args))
        else:
            raise YaccGrammarError(f"Unknown type constructor: {constructor}")

    # Handle module.MessageName (any type with a dot is a MessageType)
    if '.' in text:
        parts = text.split('.', 1)
        return MessageType(parts[0], parts[1])

    # Handle base types
    return BaseType(text)


def _split_bracket_type_args(text: str) -> List[str]:
    """Split comma-separated type arguments respecting nested brackets."""
    args = []
    current = []
    depth = 0

    for char in text:
        if char in '([':
            depth += 1
            current.append(char)
        elif char in ')]':
            depth -= 1
            current.append(char)
        elif char == ',' and depth == 0:
            if current:
                args.append(''.join(current).strip())
                current = []
        else:
            current.append(char)

    if current:
        args.append(''.join(current).strip())

    return [a for a in args if a]


def _parse_token_pattern(rest: str, token_name: str) -> Tuple[str, str, bool]:
    """Parse type and required pattern from %token directive.

    Args:
        rest: The part after '%token NAME', e.g. "Type r'pattern'"
        token_name: Name of the token (for error messages)

    Returns:
        (type_str, pattern, is_regex)
        is_regex is True for r'...' patterns, False for '...' literals

    Raises:
        YaccGrammarError: If pattern is missing or invalid
    """
    rest = rest.strip()

    # Find the pattern - look for r'...' or '...' at the end
    # Use regex to find where the string literal starts
    pattern_match = re.search(r"\s+(r?['\"])(.*)$", rest)
    if not pattern_match:
        raise YaccGrammarError(f"%token {token_name} requires a pattern (r'...' or '...')")

    type_str = rest[:pattern_match.start()].strip()
    pattern_literal = pattern_match.group(0).strip()  # e.g., r'pattern' or 'pattern'

    # Use ast.literal_eval to parse and validate the string literal
    try:
        pattern = ast.literal_eval(pattern_literal)
    except (ValueError, SyntaxError) as e:
        raise YaccGrammarError(f"%token {token_name} has invalid pattern {pattern_literal!r}: {e}")

    if not isinstance(pattern, str):
        raise YaccGrammarError(f"%token {token_name} pattern must be a string, got {type(pattern).__name__}")

    # Determine if it's a raw string (regex) or regular string (literal)
    is_regex = pattern_literal.startswith('r')

    return type_str, pattern, is_regex


def parse_directives(lines: List[str]) -> Tuple[TypeContext, List[str], int]:
    """Parse directives section until %%.

    Returns:
        (type_context, ignored_completeness, end_line_index)
    """
    ctx = TypeContext()
    ignored_completeness: List[str] = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        i += 1

        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue

        # Check for section separator
        if line == '%%':
            if ctx.start_symbol is None:
                raise YaccGrammarError("Missing required %start directive", i)
            if ctx.start_symbol not in ctx.nonterminals:
                raise YaccGrammarError(f"Start symbol '{ctx.start_symbol}' is not a declared nonterminal", i)
            return ctx, ignored_completeness, i

        # Parse directive
        if line.startswith('%token'):
            rest = line[6:].strip()
            # Split name from type+pattern
            space_idx = rest.find(' ')
            if space_idx == -1:
                raise YaccGrammarError(f"Invalid %token directive: {line}", i)
            name = rest[:space_idx]
            if name in ctx.terminals:
                raise YaccGrammarError(f"Duplicate token declaration: {name}", i)
            type_and_pattern = rest[space_idx+1:]
            type_str, pattern, is_regex = _parse_token_pattern(type_and_pattern, name)
            ctx.terminals[name] = parse_type(type_str)
            ctx.terminal_info[name] = TerminalInfo(parse_type(type_str), pattern, is_regex)

        elif line.startswith('%nonterm'):
            parts = line[8:].strip().split(None, 1)
            if len(parts) != 2:
                raise YaccGrammarError(f"Invalid %nonterm directive: {line}", i)
            name, type_str = parts
            if name in ctx.nonterminals:
                raise YaccGrammarError(f"Duplicate nonterminal declaration: {name}", i)
            ctx.nonterminals[name] = parse_type(type_str)

        elif line.startswith('%start'):
            name = line[6:].strip()
            if not name:
                raise YaccGrammarError(f"Invalid %start directive: {line}", i)
            if ctx.start_symbol is not None:
                raise YaccGrammarError(f"Duplicate %start directive: {line}", i)
            ctx.start_symbol = name

        elif line.startswith('%validator_ignore_completeness'):
            name = line[30:].strip()
            if not name:
                raise YaccGrammarError(f"Invalid %validator_ignore_completeness directive: {line}", i)
            ignored_completeness.append(name)

        else:
            raise YaccGrammarError(f"Unknown directive: {line}", i)

    raise YaccGrammarError("Unexpected end of file, expected %%")


def parse_rhs_element(text: str, ctx: TypeContext) -> Rhs:
    """Parse a single RHS element.

    Syntax:
        "literal"           -> LitTerminal
        name                -> NamedTerminal (if declared with %token)
        name                -> Nonterminal (if declared with %type)
        element*            -> Star(element)
        element?            -> Option(element)

    Symbol types are determined by their declarations (%token or %type),
    not by naming conventions.
    """
    text = text.strip()

    # Handle star (repetition)
    if text.endswith('*'):
        inner = text[:-1].strip()
        inner_rhs = parse_rhs_element(inner, ctx)
        if not isinstance(inner_rhs, (Nonterminal, NamedTerminal)):
            raise YaccGrammarError(f"Star inner must be nonterminal or terminal: {text}")
        return Star(inner_rhs)

    # Handle option
    if text.endswith('?'):
        inner = text[:-1].strip()
        inner_rhs = parse_rhs_element(inner, ctx)
        if not isinstance(inner_rhs, (Nonterminal, NamedTerminal)):
            raise YaccGrammarError(f"Option inner must be nonterminal or terminal: {text}")
        return Option(inner_rhs)

    # Handle literal
    if text.startswith('"') and text.endswith('"'):
        return LitTerminal(text[1:-1])

    # Look up in context based on declarations
    if text in ctx.terminals:
        return NamedTerminal(text, ctx.terminals[text])
    if text in ctx.nonterminals:
        return Nonterminal(text, ctx.nonterminals[text])

    # Symbol not declared
    raise YaccGrammarError(f"Unknown symbol '{text}': must be declared with %token or %type")


def tokenize_rhs(text: str) -> List[str]:
    """Tokenize an RHS string into elements."""
    tokens = []
    i = 0
    while i < len(text):
        # Skip whitespace
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text):
            break

        # Handle string literal
        if text[i] == '"':
            j = i + 1
            while j < len(text) and text[j] != '"':
                if text[j] == '\\':
                    j += 2
                else:
                    j += 1
            if j >= len(text):
                raise YaccGrammarError(f"Unterminated string literal in RHS: {text}")
            tokens.append(text[i:j+1])
            i = j + 1
        # Handle identifier (possibly with * or ?)
        elif text[i].isalnum() or text[i] == '_':
            j = i
            while j < len(text) and (text[j].isalnum() or text[j] == '_'):
                j += 1
            # Include trailing * or ?
            if j < len(text) and text[j] in '*?':
                j += 1
            tokens.append(text[i:j])
            i = j
        else:
            raise YaccGrammarError(f"Unexpected character in RHS: {text[i]!r} in {text}")

    return tokens


def parse_rhs(text: str, ctx: TypeContext) -> Rhs:
    """Parse a complete RHS string."""
    tokens = tokenize_rhs(text)
    if not tokens:
        raise YaccGrammarError(f"Empty RHS: {text}")

    elements = [parse_rhs_element(t, ctx) for t in tokens]

    if len(elements) == 1:
        return elements[0]
    return Sequence(tuple(elements))


def _get_indent(line: str) -> int:
    """Get the indentation level (number of leading spaces) of a line."""
    return len(line) - len(line.lstrip())


def parse_rules(lines: List[str], start_line: int, ctx: TypeContext) -> Tuple[List[Rule], int]:
    """Parse rules section until %%.

    Rules use 'construct:' to introduce semantic actions:
        rule
            : rhs
            construct: single_line_expression

        rule
            : rhs
            construct:
                multi_line
                action_code

    Returns:
        (rules, end_line_index)
    """
    rules: List[Rule] = []
    i = 0
    current_lhs: Optional[str] = None
    current_lhs_type: Optional[TargetType] = None
    current_rhs_lines: List[str] = []  # Accumulate RHS lines
    current_action_lines: List[str] = []  # Accumulate action lines
    current_alt_start_line: int = 0
    in_action: bool = False
    action_base_indent: int = 0  # Indentation level of the 'construct:' line

    def flush_alternative():
        """Process accumulated alternative."""
        nonlocal current_rhs_lines, current_action_lines, in_action
        if current_rhs_lines and current_lhs is not None and current_lhs_type is not None:
            rhs_text = '\n'.join(current_rhs_lines)
            action_text = '\n'.join(current_action_lines)
            rule = _parse_alternative(current_lhs, current_lhs_type, rhs_text, action_text, ctx, current_alt_start_line)
            rules.append(rule)
        current_rhs_lines = []
        current_action_lines = []
        in_action = False

    while i < len(lines):
        line = lines[i]
        line_num = start_line + i
        stripped = line.strip()
        indent = _get_indent(line)
        i += 1

        # Skip empty lines and comments (but preserve them in action blocks)
        if not stripped or stripped.startswith('#'):
            if in_action and current_action_lines:
                # Preserve empty lines within action blocks
                current_action_lines.append('')
            continue

        # Check for section separator
        if stripped == '%%':
            flush_alternative()
            return rules, i

        # If we're in an action block, check if we should exit
        if in_action:
            if indent <= action_base_indent and not stripped.startswith('construct:'):
                # Indentation decreased - end of action block
                in_action = False
                # Don't consume this line, process it below
            else:
                # Continue action block
                current_action_lines.append(stripped)
                continue

        # Check for new rule (name at start of line, not indented)
        if line and (line[0].isalpha() or line[0] == '_'):
            flush_alternative()

            # New rule definition
            if ':' in stripped:
                # Single-line rule or start of multi-line rule
                parts = stripped.split(':', 1)
                current_lhs = parts[0].strip()
                if current_lhs not in ctx.nonterminals:
                    raise YaccGrammarError(f"Unknown nonterminal: {current_lhs}", line_num)
                current_lhs_type = ctx.nonterminals[current_lhs]

                rest = parts[1].strip()
                if rest:
                    current_rhs_lines = [rest]
                    current_alt_start_line = line_num
            else:
                # Just the name, colon on next line
                current_lhs = stripped
                if current_lhs not in ctx.nonterminals:
                    raise YaccGrammarError(f"Unknown nonterminal: {current_lhs}", line_num)
                current_lhs_type = ctx.nonterminals[current_lhs]

        elif stripped.startswith(':') or stripped.startswith('|'):
            # Start of new alternative
            flush_alternative()

            if current_lhs is None:
                raise YaccGrammarError(f"Rule continuation without rule name", line_num)

            rest = stripped[1:].strip()
            if rest:
                # Check if this line incorrectly contains 'construct:' inline
                if ' construct:' in rest or rest.endswith(' construct'):
                    raise YaccGrammarError(f"'construct:' must be on a separate line from the RHS", line_num)
                current_rhs_lines = [rest]
                current_alt_start_line = line_num

        elif stripped.startswith('construct:'):
            # Start of semantic action
            action_base_indent = indent
            rest = stripped[len('construct:'):].strip()
            if rest:
                # Single-line action
                current_action_lines = [rest]
            else:
                # Multi-line action follows
                in_action = True
                current_action_lines = []

        elif line and line[0].isspace() and current_rhs_lines:
            # Continuation of RHS (indented line, not yet in action)
            current_rhs_lines.append(stripped)

        else:
            raise YaccGrammarError(f"Unexpected line in rules section: {stripped}", line_num)

    raise YaccGrammarError("Unexpected end of file, expected %%")


def _find_non_literal_indices(rhs: Rhs) -> List[int]:
    """Find 1-indexed positions of non-literal elements in an RHS.

    A literal element is a LitTerminal (quoted string like "(" or "transaction").
    Non-literal elements are NamedTerminal, Nonterminal, Star, Option, etc.

    Returns:
        List of 1-indexed positions of non-literal elements.
    """
    indices = []
    if isinstance(rhs, Sequence):
        for i, elem in enumerate(rhs.elements):
            if not isinstance(elem, LitTerminal):
                indices.append(i + 1)  # 1-indexed
    elif not isinstance(rhs, LitTerminal):
        indices.append(1)
    return indices


def _parse_alternative(lhs_name: str, lhs_type: TargetType, rhs_text: str,
                       action_text: str, ctx: TypeContext, line: int) -> Rule:
    """Parse a single rule alternative.

    Args:
        lhs_name: Name of the left-hand side nonterminal
        lhs_type: Type of the left-hand side
        rhs_text: The right-hand side pattern text
        action_text: The semantic action text (from construct: block), or empty for default
        ctx: Type context
        line: Line number for error messages
    """
    # Parse RHS first so we can check for default action
    rhs = parse_rhs(rhs_text, ctx)

    # If no action provided, try to infer default
    if not action_text:
        non_literal_indices = _find_non_literal_indices(rhs)
        if len(non_literal_indices) == 0:
            raise YaccGrammarError(
                f"Missing construct: for rule with no non-literal elements: {rhs_text}",
                line)
        elif len(non_literal_indices) > 1:
            raise YaccGrammarError(
                f"Missing construct: for rule with multiple non-literal elements "
                f"(at positions {non_literal_indices}): {rhs_text}",
                line)
        else:
            # Exactly one non-literal - default to $n
            action_text = f"${non_literal_indices[0]}"

    # Parse action, using LHS type as expected return type
    constructor = parse_action(action_text, rhs, ctx, line, expected_return_type=lhs_type)

    lhs = Nonterminal(lhs_name, lhs_type)
    return Rule(lhs=lhs, rhs=rhs, constructor=constructor)


def load_yacc_grammar(text: str) -> GrammarConfig:
    """Load grammar from yacc-like format.

    Args:
        text: Grammar file content

    Returns:
        GrammarConfig with terminals, rules, and function definitions
    """
    lines = text.split('\n')

    # Check for tabs - they are not allowed
    for line_num, line in enumerate(lines, 1):
        if '\t' in line:
            raise YaccGrammarError(f"Tabs are not allowed in grammar files. Semantic actions are sensitive to indentation.", line_num)

    # Parse directives
    ctx, ignored_completeness, rules_start = parse_directives(lines)

    # Parse rules
    rules_lines = lines[rules_start:]
    rule_list, helpers_start = parse_rules(rules_lines, rules_start + 1, ctx)

    # Parse helper functions
    helpers_lines = rules_lines[helpers_start:]
    functions = parse_helper_functions(helpers_lines, rules_start + helpers_start + 1, ctx)

    # Update context with functions
    ctx.functions.update(functions)

    # Build rules dictionary
    rules_dict: Dict[Nonterminal, List[Rule]] = {}
    for rule in rule_list:
        if rule.lhs not in rules_dict:
            rules_dict[rule.lhs] = []
        rules_dict[rule.lhs].append(rule)

    # Build terminal_patterns from terminal_info
    terminal_patterns = {
        name: TerminalDef(info.type, info.pattern, info.is_regex)
        for name, info in ctx.terminal_info.items()
    }

    # start_symbol should have been set in the header section
    if ctx.start_symbol is None:
        raise YaccGrammarError("Missing %start directive - no start symbol declared", 0)

    return GrammarConfig(
        terminals=ctx.terminals,
        start_symbol=ctx.start_symbol,
        terminal_patterns=terminal_patterns,
        rules=rules_dict,
        ignored_completeness=ignored_completeness,
        function_defs=functions
    )


def load_yacc_grammar_file(path: Path) -> GrammarConfig:
    """Load grammar from a yacc-like format file.

    Args:
        path: Path to the grammar file

    Returns:
        GrammarConfig
    """
    return load_yacc_grammar(path.read_text())


__all__ = [
    'YaccGrammarError',
    'TypeContext',
    'TerminalInfo',
    'parse_type',
    'parse_rhs',
    'parse_action',
    'parse_directives',
    'parse_rules',
    'parse_helper_functions',
    'load_yacc_grammar',
    'load_yacc_grammar_file',
]
